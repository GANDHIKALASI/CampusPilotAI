"""
Embedding service for CampusPilot AI.

Provides isolated text embedding generation for academic document RAG retrieval
using Google's official Gemini Embedding API (`google-genai` SDK).
Supports configurable Matryoshka Representation Learning (MRL) output dimensionality
(default: 768 dimensions), task-type specifications (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY),
robust batch/bulk embedding with bounded exponential backoff, content hashing,
and strict idempotency controls.
"""

import hashlib
import logging
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import Settings, get_settings
from app.schemas.chunk import DocumentChunk
from app.schemas.embedding import (
    BulkEmbeddingResult,
    EmbeddedChunk,
    FailedChunk,
    SkippedChunk,
)

logger = logging.getLogger(__name__)

# HTTP status codes eligible for retry with exponential backoff
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def compute_chunk_hash(content: str, title: Optional[str] = None) -> str:
    """Generate a deterministic SHA-256 hash of chunk content and contextual title."""
    raw = f"title:{title or ''}::content:{content.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_config_signature(
    model: str,
    dimension: int,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> str:
    """Generate a unique signature of model configuration for idempotency check."""
    return f"{model}:{dimension}:{task_type}"


def estimate_embedding_cost(character_count: int) -> float:
    """
    Estimate Google Gemini embedding API cost based on official published pricing.
    gemini-embedding-2 is priced at ~$0.00002 per 1,000 characters ($0.02 / 1M chars).
    """
    return (character_count / 1000.0) * 0.00002


def validate_vector(vector: Any, expected_dim: int) -> None:
    """Validate that vector is a non-empty list of finite floating point numbers with expected dimensionality."""
    if not isinstance(vector, (list, tuple)):
        raise ValueError(f"Vector must be a list of floats, got {type(vector).__name__}")
    if len(vector) != expected_dim:
        raise ValueError(f"Expected vector dimension {expected_dim}, but got {len(vector)}")
    for val in vector:
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            raise ValueError("Embedding contains NaN or non-finite floating point value.")


def is_retryable_error(exc: Exception) -> bool:
    """Determine whether an exception is transient and eligible for backoff retry."""
    if isinstance(exc, APIError):
        return exc.code in RETRYABLE_STATUS_CODES
    exc_name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if any(k in exc_name for k in ("connect", "timeout", "protocol", "reset", "ssl")):
        return True
    if any(k in msg for k in ("eof occurred", "connection reset", "timed out", "temporary failure", "too many requests")):
        return True
    return False


class EmbeddingService:
    """Service responsible for generating semantic embeddings from document chunks and search queries."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client: Optional[genai.Client] = None
        self._query_cache: Dict[str, List[float]] = {}

    @property
    def client(self) -> genai.Client:
        """Lazily initialize Google GenAI client using backend environment configuration."""
        if self._client is None:
            api_key = self.settings.gemini_api_key
            if not api_key or not api_key.strip():
                raise ValueError("GEMINI_API_KEY is not configured in backend environment variables.")
            self._client = genai.Client(api_key=api_key.strip())
        return self._client

    def is_configured(self) -> bool:
        """Check if Gemini API credentials are validly populated."""
        return bool(self.settings.gemini_api_key and self.settings.gemini_api_key.strip())

    def embed_text(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT",
        title: Optional[str] = None,
        output_dimensionality: Optional[int] = None,
    ) -> List[float]:
        """Generate a single embedding vector with designated task type and target dimensionality."""
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty or whitespace-only text.")

        target_dim = output_dimensionality or self.settings.embedding_dimension
        model_name = self.settings.gemini_embedding_model

        config = types.EmbedContentConfig(
            output_dimensionality=target_dim,
            task_type=task_type,
            title=title if task_type == "RETRIEVAL_DOCUMENT" and title else None,
        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.client.models.embed_content(
                    model=model_name,
                    contents=text.strip(),
                    config=config,
                )
                if not response.embeddings:
                    raise RuntimeError(f"Embedding API returned empty embedding list for input of length {len(text)}")

                embedding_values = list(response.embeddings[0].values)
                validate_vector(embedding_values, target_dim)
                return embedding_values

            except APIError as api_err:
                if api_err.code in (429, 500, 502, 503, 504) and attempt < max_attempts:
                    sleep_time = (2 ** (attempt - 1)) + 0.1
                    logger.warning("Gemini Embedding API attempt %d transient error (%s). Retrying in %.2fs...", attempt, api_err.code, sleep_time)
                    time.sleep(sleep_time)
                    continue
                logger.error("Google Gemini Embedding API error (%s): %s", api_err.code, api_err.message)
                raise RuntimeError(f"Gemini Embedding API call failed: {api_err.message}") from api_err
            except Exception as exc:
                if attempt < max_attempts and is_retryable_error(exc):
                    sleep_time = (2 ** (attempt - 1)) + 0.25
                    logger.warning("Gemini Embedding network attempt %d transient error (%s: %s). Retrying in %.2fs...", attempt, type(exc).__name__, exc, sleep_time)
                    time.sleep(sleep_time)
                    continue
                logger.error("Unexpected error generating embedding: %s", exc)
                raise

    def embed_document_chunk(
        self,
        chunk_content: str,
        document_title: Optional[str] = None,
        output_dimensionality: Optional[int] = None,
    ) -> List[float]:
        """Convenience method to embed an academic document chunk using the RETRIEVAL_DOCUMENT task."""
        return self.embed_text(
            text=chunk_content,
            task_type="RETRIEVAL_DOCUMENT",
            title=document_title,
            output_dimensionality=output_dimensionality,
        )

    def embed_query(
        self,
        query: str,
        output_dimensionality: Optional[int] = None,
    ) -> List[float]:
        """Convenience method to embed a student search query using the RETRIEVAL_QUERY task with in-memory caching."""
        cache_key = f"{query.strip()}:{output_dimensionality or self.settings.embedding_dimension}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]
        vec = self.embed_text(
            text=query,
            task_type="RETRIEVAL_QUERY",
            title=None,
            output_dimensionality=output_dimensionality,
        )
        self._query_cache[cache_key] = vec
        return vec

    def _execute_with_retry(
        self,
        call_fn,
        max_retries: int,
        initial_delay: float,
        max_delay: float,
        backoff_factor: float,
    ) -> Tuple[Any, int, float]:
        """
        Execute API call with bounded exponential backoff on retryable errors.
        Returns: (result, attempts_made, call_latency_seconds)
        """
        last_error = None
        for attempt in range(max_retries + 1):
            start_t = time.perf_counter()
            try:
                result = call_fn()
                latency = time.perf_counter() - start_t
                return result, attempt + 1, latency
            except Exception as exc:
                latency = time.perf_counter() - start_t
                last_error = exc
                if attempt < max_retries and is_retryable_error(exc):
                    delay = min(max_delay, initial_delay * (backoff_factor ** attempt))
                    jitter = random.uniform(0.05, 0.25)
                    total_delay = delay + jitter
                    logger.warning(
                        "Embedding API attempt %d failed (%s: %s). Retrying in %.2fs...",
                        attempt + 1,
                        type(exc).__name__,
                        exc,
                        total_delay,
                    )
                    time.sleep(total_delay)
                else:
                    break

        raise last_error

    def embed_chunks_bulk(
        self,
        chunks: List[Union[DocumentChunk, Dict[str, Any]]],
        document_title: Optional[str] = None,
        existing_embeddings: Optional[Dict[str, Dict[str, Any]]] = None,
        batch_size: Optional[int] = None,
        output_dimensionality: Optional[int] = None,
        max_retries: Optional[int] = None,
        force_reembed: bool = False,
    ) -> BulkEmbeddingResult:
        """
        Reliably and idempotently generate embeddings for document chunks.

        - Respects API batching limits.
        - Preserves original chunk IDs and metadata.
        - Validates all output vectors (768 dimensions, finite floats, non-empty).
        - Traps empty chunks without sending them to API.
        - Checks content hash and config signature for idempotency.
        - Retries retryable errors with bounded exponential backoff.
        - Falls back to chunk-by-chunk processing on batch failure to isolate errors.
        - Separately reports successful, failed, and skipped chunks.
        """
        start_wall_time = time.perf_counter()

        target_dim = output_dimensionality or self.settings.embedding_dimension
        model_name = self.settings.gemini_embedding_model
        effective_batch_size = max(1, batch_size or self.settings.embedding_batch_size)
        effective_retries = max_retries if max_retries is not None else self.settings.embedding_max_retries
        initial_delay = self.settings.embedding_retry_initial_delay
        max_delay = self.settings.embedding_retry_max_delay
        backoff_factor = self.settings.embedding_retry_backoff_factor

        current_config_sig = compute_config_signature(
            model=model_name,
            dimension=target_dim,
            task_type="RETRIEVAL_DOCUMENT",
        )

        successful_chunks: List[EmbeddedChunk] = []
        failed_chunks: List[FailedChunk] = []
        skipped_chunks: List[SkippedChunk] = []

        api_calls_count = 0
        total_api_latency_ms = 0.0
        total_chars_embedded = 0

        # Step 1: Normalize input chunks and sanitize
        normalized_chunks: List[Dict[str, Any]] = []
        for idx, item in enumerate(chunks):
            if isinstance(item, DocumentChunk):
                c_dict = item.model_dump()
            elif isinstance(item, dict):
                c_dict = dict(item)
            else:
                c_dict = {
                    "chunk_index": idx,
                    "content": str(item),
                    "page_number": 1,
                }

            # Ensure required identifiers exist
            chunk_id = c_dict.get("id") or c_dict.get("chunk_id") or f"chunk_{c_dict.get('chunk_index', idx)}"
            c_dict["resolved_chunk_id"] = str(chunk_id)
            if "chunk_index" not in c_dict:
                c_dict["chunk_index"] = idx
            if "page_number" not in c_dict:
                c_dict["page_number"] = 1
            if "character_count" not in c_dict:
                c_dict["character_count"] = len(c_dict.get("content", ""))
            if "token_count" not in c_dict:
                c_dict["token_count"] = 0

            normalized_chunks.append(c_dict)

        # Step 2: Separate empty chunks and check idempotency against existing embeddings
        chunks_to_process: List[Dict[str, Any]] = []

        for c_dict in normalized_chunks:
            chunk_id = c_dict["resolved_chunk_id"]
            chunk_idx = c_dict["chunk_index"]
            page_num = c_dict["page_number"]
            content = c_dict.get("content", "")

            # Check 2a: Empty content check (Do not send empty chunks to API)
            if not content or not content.strip():
                failed_chunks.append(
                    FailedChunk(
                        chunk_id=chunk_id,
                        chunk_index=chunk_idx,
                        page_number=page_num,
                        error="Empty or whitespace-only chunk content cannot be embedded.",
                        retry_count=0,
                        retryable=False,
                    )
                )
                continue

            # Check 2b: Compute deterministic content hash
            content_hash = compute_chunk_hash(content, document_title)
            c_dict["computed_content_hash"] = content_hash

            # Check 2c: Idempotency check
            if not force_reembed and existing_embeddings:
                existing = existing_embeddings.get(str(chunk_id)) or existing_embeddings.get(chunk_idx)
                if existing:
                    existing_hash = existing.get("content_hash")
                    existing_sig = existing.get("config_signature")
                    existing_vec = existing.get("vector")

                    # If content and configuration match, and vector is valid -> SKIP
                    if existing_hash == content_hash and existing_sig == current_config_sig:
                        if isinstance(existing_vec, (list, tuple)) and len(existing_vec) == target_dim:
                            skipped_chunks.append(
                                SkippedChunk(
                                    chunk_id=chunk_id,
                                    chunk_index=chunk_idx,
                                    page_number=page_num,
                                    reason="unchanged_content_and_config",
                                    content_hash=content_hash,
                                )
                            )
                            # Also retain in successful results so downstream caller has the full set
                            successful_chunks.append(
                                EmbeddedChunk(
                                    chunk_id=chunk_id,
                                    chunk_index=chunk_idx,
                                    page_number=page_num,
                                    document_id=c_dict.get("document_id"),
                                    filename=c_dict.get("filename"),
                                    content_hash=content_hash,
                                    config_signature=current_config_sig,
                                    vector=list(existing_vec),
                                    token_count=c_dict.get("token_count", 0),
                                    character_count=c_dict.get("character_count", len(content)),
                                    metadata=c_dict.get("metadata", {}),
                                )
                            )
                            continue
                        else:
                            logger.info(
                                "Chunk %s existing vector is invalid/corrupted; scheduling re-embedding.",
                                chunk_id,
                            )
                    else:
                        logger.info(
                            "Chunk %s changed (hash match: %s, sig match: %s); scheduling re-embedding.",
                            chunk_id,
                            existing_hash == content_hash,
                            existing_sig == current_config_sig,
                        )

            chunks_to_process.append(c_dict)

        # Step 3: Batch generation with fallback resilience
        config = types.EmbedContentConfig(
            output_dimensionality=target_dim,
            task_type="RETRIEVAL_DOCUMENT",
            title=document_title if document_title else None,
        )

        for batch_start in range(0, len(chunks_to_process), effective_batch_size):
            batch = chunks_to_process[batch_start : batch_start + effective_batch_size]

            # Convert batch to google.genai Content list
            contents = [
                types.Content(parts=[types.Part.from_text(text=item["content"].strip())])
                for item in batch
            ]

            def _call_api():
                return self.client.models.embed_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )

            try:
                response, attempts, latency = self._execute_with_retry(
                    call_fn=_call_api,
                    max_retries=effective_retries,
                    initial_delay=initial_delay,
                    max_delay=max_delay,
                    backoff_factor=backoff_factor,
                )
                api_calls_count += 1
                total_api_latency_ms += latency * 1000.0

                embeddings = list(response.embeddings or [])
                if len(embeddings) != len(batch):
                    raise ValueError(
                        f"API returned {len(embeddings)} embeddings for batch of {len(batch)} chunks"
                    )

                for item, emb in zip(batch, embeddings):
                    raw_vec = list(emb.values)
                    try:
                        validate_vector(raw_vec, target_dim)
                        char_count = item["character_count"]
                        total_chars_embedded += char_count

                        successful_chunks.append(
                            EmbeddedChunk(
                                chunk_id=item["resolved_chunk_id"],
                                chunk_index=item["chunk_index"],
                                page_number=item["page_number"],
                                document_id=item.get("document_id"),
                                filename=item.get("filename"),
                                content_hash=item["computed_content_hash"],
                                config_signature=current_config_sig,
                                vector=raw_vec,
                                token_count=item.get("token_count", 0),
                                character_count=char_count,
                                metadata=item.get("metadata", {}),
                            )
                        )
                    except Exception as val_err:
                        failed_chunks.append(
                            FailedChunk(
                                chunk_id=item["resolved_chunk_id"],
                                chunk_index=item["chunk_index"],
                                page_number=item["page_number"],
                                error=f"Validation error: {val_err}",
                                retry_count=attempts,
                                retryable=False,
                            )
                        )

            except Exception as batch_err:
                logger.warning(
                    "Batch embedding of %d chunks failed (%s: %s). Initiating granular chunk fallback...",
                    len(batch),
                    type(batch_err).__name__,
                    batch_err,
                )
                # Granular fallback: attempt each chunk individually to isolate errors
                for single_item in batch:
                    single_content = single_item["content"].strip()

                    def _single_call():
                        return self.client.models.embed_content(
                            model=model_name,
                            contents=single_content,
                            config=config,
                        )

                    try:
                        single_resp, attempts, latency = self._execute_with_retry(
                            call_fn=_single_call,
                            max_retries=effective_retries,
                            initial_delay=initial_delay,
                            max_delay=max_delay,
                            backoff_factor=backoff_factor,
                        )
                        api_calls_count += 1
                        total_api_latency_ms += latency * 1000.0

                        if not single_resp.embeddings:
                            raise RuntimeError("Empty embeddings returned for single chunk")

                        single_vec = list(single_resp.embeddings[0].values)
                        validate_vector(single_vec, target_dim)
                        char_count = single_item["character_count"]
                        total_chars_embedded += char_count

                        successful_chunks.append(
                            EmbeddedChunk(
                                chunk_id=single_item["resolved_chunk_id"],
                                chunk_index=single_item["chunk_index"],
                                page_number=single_item["page_number"],
                                document_id=single_item.get("document_id"),
                                filename=single_item.get("filename"),
                                content_hash=single_item["computed_content_hash"],
                                config_signature=current_config_sig,
                                vector=single_vec,
                                token_count=single_item.get("token_count", 0),
                                character_count=char_count,
                                metadata=single_item.get("metadata", {}),
                            )
                        )
                    except Exception as single_err:
                        failed_chunks.append(
                            FailedChunk(
                                chunk_id=single_item["resolved_chunk_id"],
                                chunk_index=single_item["chunk_index"],
                                page_number=single_item["page_number"],
                                error=str(single_err),
                                retry_count=effective_retries,
                                retryable=is_retryable_error(single_err),
                            )
                        )

        # Step 4: Sort successful chunks back into original chunk_index order
        successful_chunks.sort(key=lambda x: x.chunk_index)

        elapsed_wall_time = time.perf_counter() - start_wall_time
        avg_latency_ms = (total_api_latency_ms / api_calls_count) if api_calls_count > 0 else 0.0
        cost_usd = estimate_embedding_cost(total_chars_embedded)

        # Status calculation
        if len(failed_chunks) == 0:
            status = "success"
        elif len(successful_chunks) > 0:
            status = "partial_success"
        else:
            status = "failed"

        return BulkEmbeddingResult(
            status=status,
            model=model_name,
            dimension=target_dim,
            total_chunks=len(normalized_chunks),
            successful_count=len(successful_chunks),
            failed_count=len(failed_chunks),
            skipped_count=len(skipped_chunks),
            api_calls_made=api_calls_count,
            total_latency_seconds=round(elapsed_wall_time, 4),
            average_latency_per_call_ms=round(avg_latency_ms, 2),
            total_characters_embedded=total_chars_embedded,
            estimated_cost_usd=round(cost_usd, 6),
            successful_chunks=successful_chunks,
            failed_chunks=failed_chunks,
            skipped_chunks=skipped_chunks,
        )

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute the cosine similarity between two float vectors without external dependencies."""
        if not vec_a or not vec_b:
            return 0.0
        if len(vec_a) != len(vec_b):
            raise ValueError(f"Vector dimensions must match for cosine similarity ({len(vec_a)} != {len(vec_b)})")

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot_product / (norm_a * norm_b)


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Singleton provider for EmbeddingService."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
