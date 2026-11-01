"""
Semantic similarity search service for CampusPilot AI.

Generates query embeddings using Google Gemini API (`gemini-embedding-2` with RETRIEVAL_QUERY task),
searches stored document chunks in PostgreSQL pgvector via cosine distance (`<=>`),
strictly enforces personal document ownership and shared academic document visibility,
and ranks relevant chunks by descending cosine similarity.
"""

import logging
import math
import time
from typing import Any, Dict, List, Optional

import asyncpg

from app.core.config import Settings, get_settings
from app.schemas.search import (
    SearchResultChunk,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.embedding_persistence import (
    pg_string_to_vector,
    validate_embedding_vector,
    vector_to_pg_string,
)
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Service providing semantic document retrieval using pgvector cosine similarity."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        embedding_service: Optional[EmbeddingService] = None,
        supabase_service: Optional[SupabaseService] = None,
        database_url: Optional[str] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_service = embedding_service or get_embedding_service()
        self.supabase_service = supabase_service or get_supabase_service()
        self.database_url = database_url or self.settings.database_url

    async def _get_pg_connection(self) -> Optional[asyncpg.Connection]:
        """Establish direct asyncpg connection if database_url is provided."""
        if not self.database_url:
            return None
        try:
            return await asyncpg.connect(self.database_url)
        except Exception as exc:
            logger.warning("Direct PostgreSQL connection to %s failed: %s", self.database_url, exc)
            return None

    async def search(
        self,
        user_id: str,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        document_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> SemanticSearchResponse:
        """
        Execute an authenticated semantic similarity search.

        - Enforces student ownership & shared document visibility.
        - Embeds student question via Gemini embedding service with RETRIEVAL_QUERY task.
        - Calculates cosine similarity (1 - cosine distance) via pgvector `<=>`.
        - Filters by similarity threshold and limits by top_k.
        - Applies optional academic filters (subject_id, semester_id, unit_id) at database level.
        - Excludes null embeddings.
        - Returns ranked chunk results without raw vectors.
        """
        start_time = time.perf_counter()

        # 1. Validate query input
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty or whitespace-only.")

        clean_query = query.strip()

        # 2. Configure parameters
        effective_top_k = min(
            max(1, top_k or self.settings.search_default_top_k),
            self.settings.search_max_top_k,
        )
        effective_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.settings.search_default_threshold
        )
        effective_threshold = max(0.0, min(1.0, effective_threshold))

        # 3. Check document-level access if specific document_id is provided
        if document_id:
            doc = await self.supabase_service.get_user_document(user_id=user_id, document_id=document_id)
            if not doc:
                raise PermissionError(f"Access denied: document {document_id} not accessible by user {user_id}")

        # 4. Generate query embedding with RETRIEVAL_QUERY task type
        expected_dim = self.settings.embedding_dimension
        query_vector = self.embedding_service.embed_query(
            query=clean_query,
            output_dimensionality=expected_dim,
        )
        validated_query_vector = validate_embedding_vector(query_vector, expected_dim=expected_dim)
        pg_query_vector_str = vector_to_pg_string(validated_query_vector)

        ranked_results: List[SearchResultChunk] = []

        # 5. Path A: Direct PostgreSQL query using native pgvector `<=>` operator
        pg_conn = await self._get_pg_connection()
        if pg_conn:
            try:
                import uuid
                doc_uuid = uuid.UUID(document_id) if document_id else None
                user_uuid = uuid.UUID(user_id) if user_id and len(user_id) == 36 else None
                subject_uuid = uuid.UUID(subject_id) if subject_id and len(subject_id) == 36 else None
                semester_uuid = uuid.UUID(semester_id) if semester_id and len(semester_id) == 36 else None
                unit_uuid = uuid.UUID(unit_id) if unit_id and len(unit_id) == 36 else None

                rows = await pg_conn.fetch(
                    """
                    SELECT
                        dc.id::text as chunk_id,
                        dc.document_id::text as document_id,
                        d.filename,
                        dc.chunk_index,
                        dc.page_number,
                        dc.content,
                        dc.token_count,
                        dc.character_count,
                        dc.scope,
                        (1 - (dc.embedding <=> $1::vector))::float as similarity_score
                    FROM public.document_chunks dc
                    JOIN public.documents d ON dc.document_id = d.id
                    WHERE dc.embedding IS NOT NULL
                      AND (
                          ($2::uuid IS NOT NULL AND dc.user_id = $2::uuid)
                          OR dc.scope = 'shared'
                      )
                      AND ($3::uuid IS NULL OR dc.document_id = $3::uuid)
                      AND ($6::uuid IS NULL OR dc.subject_id = $6::uuid)
                      AND ($7::uuid IS NULL OR dc.semester_id = $7::uuid)
                      AND ($8::uuid IS NULL OR dc.unit_id = $8::uuid)
                      AND (1 - (dc.embedding <=> $1::vector)) >= $4
                    ORDER BY dc.embedding <=> $1::vector ASC
                    LIMIT $5;
                    """,
                    pg_query_vector_str,
                    user_uuid,
                    doc_uuid,
                    effective_threshold,
                    effective_top_k,
                    subject_uuid,
                    semester_uuid,
                    unit_uuid,
                )
                await pg_conn.close()

                for r in rows:
                    ranked_results.append(
                        SearchResultChunk(
                            chunk_id=r["chunk_id"],
                            document_id=r["document_id"],
                            filename=r["filename"],
                            chunk_index=r["chunk_index"],
                            page_number=r["page_number"],
                            content=r["content"],
                            similarity_score=round(r["similarity_score"], 4),
                            scope=r["scope"],
                            token_count=r["token_count"] or 0,
                            character_count=r["character_count"] or len(r["content"]),
                        )
                    )

                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return SemanticSearchResponse(
                    query=clean_query,
                    total_results=len(ranked_results),
                    results=ranked_results,
                    execution_time_ms=round(elapsed_ms, 2),
                    status="success",
                )
            except Exception as pg_err:
                logger.error("Direct PostgreSQL semantic search failed: %s", pg_err)
                await pg_conn.close()

        # 6. Path B: Supabase PostgREST client with match_document_chunks RPC or chunk query
        if self.supabase_service.is_configured() and self.supabase_service._client:
            client = self.supabase_service._client
            try:
                # Attempt 1: Call match_document_chunks RPC
                rpc_params = {
                    "query_embedding": validated_query_vector,
                    "match_threshold": effective_threshold,
                    "match_count": effective_top_k,
                    "filter_user_id": user_id,
                    "filter_document_id": document_id,
                }
                res = client.rpc("match_document_chunks", rpc_params).execute()
                if res.data is not None:
                    for row in res.data:
                        ranked_results.append(
                            SearchResultChunk(
                                chunk_id=str(row["chunk_id"]),
                                document_id=str(row["document_id"]),
                                filename=row.get("filename", "academic_document.pdf"),
                                chunk_index=row["chunk_index"],
                                page_number=row["page_number"],
                                content=row["content"],
                                similarity_score=round(float(row["similarity_score"]), 4),
                                scope=row.get("scope", "personal"),
                                token_count=row.get("token_count", 0),
                                character_count=row.get("character_count", len(row["content"])),
                            )
                        )
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    return SemanticSearchResponse(
                        query=clean_query,
                        total_results=len(ranked_results),
                        results=ranked_results,
                        execution_time_ms=round(elapsed_ms, 2),
                        status="success",
                    )
            except Exception as rpc_err:
                logger.debug("Supabase RPC match_document_chunks not available (%s); executing authorized chunk retrieval...", rpc_err)

            # Attempt 2: Retrieve authorized chunks with non-null embeddings from Supabase
            try:
                docs = await self.supabase_service.list_user_documents(user_id=user_id)
                doc_map = {d["id"]: d for d in docs}
                if document_id:
                    doc_map = {k: v for k, v in doc_map.items() if k == document_id}

                if doc_map:
                    candidate_chunks = []
                    for d_id, d_meta in doc_map.items():
                        c_res = (
                            client.table("document_chunks")
                            .select("*")
                            .eq("document_id", d_id)
                            .not_.is_("embedding", "null")
                            .execute()
                        )
                        for c in (c_res.data or []):
                            c["filename"] = d_meta.get("filename", "document.pdf")
                            candidate_chunks.append(c)

                    # Compute cosine similarity and rank
                    scored = []
                    for c in candidate_chunks:
                        if not c.get("embedding"):
                            continue
                        chunk_vec = pg_string_to_vector(c["embedding"])
                        sim = EmbeddingService.cosine_similarity(chunk_vec, validated_query_vector)
                        if sim >= effective_threshold:
                            scored.append((sim, c))

                    scored.sort(key=lambda x: x[0], reverse=True)
                    for sim, c in scored[:effective_top_k]:
                        ranked_results.append(
                            SearchResultChunk(
                                chunk_id=str(c["id"]),
                                document_id=str(c["document_id"]),
                                filename=c.get("filename", "document.pdf"),
                                chunk_index=c["chunk_index"],
                                page_number=c["page_number"],
                                content=c["content"],
                                similarity_score=round(sim, 4),
                                scope=c.get("scope", "personal"),
                                token_count=c.get("token_count", 0),
                                character_count=c.get("character_count", len(c["content"])),
                            )
                        )

                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    return SemanticSearchResponse(
                        query=clean_query,
                        total_results=len(ranked_results),
                        results=ranked_results,
                        execution_time_ms=round(elapsed_ms, 2),
                        status="success",
                    )
            except Exception as sb_err:
                logger.error("Supabase chunk similarity search error: %s", sb_err)

        # 7. Path C: Development in-memory fallback
        dev_docs = self.supabase_service._dev_documents
        candidate_dev_chunks = []
        for d_id, d_meta in dev_docs.items():
            if document_id and d_id != document_id:
                continue
            is_owner = (d_meta.get("user_id") == user_id)
            is_shared = (d_meta.get("scope") == "shared")
            if is_owner or is_shared:
                chunks = self.supabase_service._dev_chunks.get(d_id, [])
                for c in chunks:
                    c_copy = dict(c)
                    c_copy["filename"] = d_meta.get("filename", "document.pdf")
                    candidate_dev_chunks.append(c_copy)

        scored_dev = []
        for c in candidate_dev_chunks:
            if not c.get("embedding"):
                continue
            chunk_vec = pg_string_to_vector(c["embedding"])
            sim = EmbeddingService.cosine_similarity(chunk_vec, validated_query_vector)
            if sim >= effective_threshold:
                scored_dev.append((sim, c))

        scored_dev.sort(key=lambda x: x[0], reverse=True)
        for sim, c in scored_dev[:effective_top_k]:
            ranked_results.append(
                SearchResultChunk(
                    chunk_id=str(c.get("id", f"{c.get('document_id')}_{c.get('chunk_index')}")),
                    document_id=str(c["document_id"]),
                    filename=c.get("filename", "document.pdf"),
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    content=c["content"],
                    similarity_score=round(sim, 4),
                    scope=c.get("scope", "personal"),
                    token_count=c.get("token_count", 0),
                    character_count=c.get("character_count", len(c["content"])),
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return SemanticSearchResponse(
            query=clean_query,
            total_results=len(ranked_results),
            results=ranked_results,
            execution_time_ms=round(elapsed_ms, 2),
            status="success",
        )


_semantic_search_service: Optional[SemanticSearchService] = None


def get_semantic_search_service() -> SemanticSearchService:
    """Singleton provider for SemanticSearchService."""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service
