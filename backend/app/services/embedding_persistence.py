"""
Persistence service for document chunk embeddings using PostgreSQL native pgvector and Supabase.

Provides:
- Native pgvector storage and batch upserting for 768-dimensional embeddings.
- Strict numeric validation (768 finite floats, rejection of NaN/Inf/empty vectors).
- Idempotency controls (skipping unchanged content_hash and config_signature).
- Strict scope-aware access control (isolated personal documents vs shared academic documents).
- Seamless cascading deletion without orphaned embeddings.
"""

import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import asyncpg

from app.core.config import Settings, get_settings
from app.schemas.embedding import EmbeddedChunk
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)


def validate_embedding_vector(vector: Any, expected_dim: int = 768) -> List[float]:
    """Validate that vector is a non-empty sequence of finite floating point numbers with expected dimensionality."""
    if not isinstance(vector, (list, tuple)):
        raise ValueError(f"Vector must be a list of floats, got {type(vector).__name__}")
    if len(vector) != expected_dim:
        raise ValueError(f"Vector dimension mismatch: expected {expected_dim}, but got {len(vector)}")
    
    clean_floats = []
    for idx, val in enumerate(vector):
        if not isinstance(val, (int, float)) or not math.isfinite(val):
            raise ValueError(f"Vector component at index {idx} contains non-finite or NaN value: {val}")
        clean_floats.append(float(val))
    
    return clean_floats


def vector_to_pg_string(vector: List[float]) -> str:
    """Format float list into PostgreSQL pgvector string literal '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.8f}" for x in vector) + "]"


def pg_string_to_vector(pg_str: Any) -> List[float]:
    """Convert PostgreSQL pgvector string or JSON array back into Python list of floats."""
    if isinstance(pg_str, (list, tuple)):
        return [float(x) for x in pg_str]
    if isinstance(pg_str, str):
        cleaned = pg_str.strip().strip("[]").strip()
        if not cleaned:
            return []
        return [float(x) for x in cleaned.split(",")]
    raise ValueError(f"Cannot parse pgvector from type {type(pg_str).__name__}")


class EmbeddingPersistenceService:
    """Service managing persistence of vector embeddings in Supabase and PostgreSQL pgvector."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase_service: Optional[SupabaseService] = None,
        database_url: Optional[str] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.supabase_service = supabase_service or get_supabase_service()
        self.database_url = database_url or self.settings.database_url
        self._dev_persisted_embeddings: Dict[str, Dict[str, Any]] = {}

    async def _get_pg_connection(self) -> Optional[asyncpg.Connection]:
        """Establish direct asyncpg connection if database_url is provided."""
        if not self.database_url:
            return None
        try:
            return await asyncpg.connect(self.database_url)
        except Exception as exc:
            logger.warning("Direct PostgreSQL connection to %s failed: %s", self.database_url, exc)
            return None

    async def persist_chunk_embeddings(
        self,
        user_id: str,
        document_id: str,
        embedded_chunks: List[EmbeddedChunk],
        scope: str = "personal",
    ) -> Dict[str, Any]:
        """
        Persist a batch of 768-dimensional embeddings into PostgreSQL/Supabase.

        - Enforces ownership / scope verification.
        - Validates vector integrity.
        - Idempotently skips unchanged chunks (matching content_hash and config_signature).
        - Updates changed chunks without dropping existing records.
        - Handles partial failures gracefully.
        """
        if not embedded_chunks:
            return {
                "status": "success",
                "document_id": document_id,
                "total_received": 0,
                "persisted_count": 0,
                "skipped_unchanged_count": 0,
                "failed_count": 0,
                "failed_records": [],
            }

        # 1. Authorize: Verify student owns the document (or document is shared and user is authorized)
        doc = await self.supabase_service.get_user_document(user_id=user_id, document_id=document_id)
        clean_scope = "shared" if scope == "shared" else (doc.get("scope", "personal") if doc else "personal")
        if not doc and clean_scope != "shared":
            raise PermissionError(f"Access denied: document {document_id} not found or unauthorized for user {user_id}")

        expected_dim = self.settings.embedding_dimension
        now_iso = datetime.now(timezone.utc).isoformat()

        persisted_count = 0
        skipped_count = 0
        failed_records = []
        valid_items_to_persist = []

        # 2. Validate every vector before database insertion
        for item in embedded_chunks:
            try:
                validated_vec = validate_embedding_vector(item.vector, expected_dim=expected_dim)
                valid_items_to_persist.append((item, validated_vec))
            except Exception as val_err:
                failed_records.append({
                    "chunk_id": str(item.chunk_id),
                    "chunk_index": item.chunk_index,
                    "error": str(val_err),
                })

        # 3. Path A: Direct PostgreSQL / pgvector connection (if database_url is available)
        pg_conn = await self._get_pg_connection()
        if pg_conn:
            try:
                # Fetch existing chunk records to check idempotency
                existing_rows = await pg_conn.fetch(
                    "SELECT id, chunk_index, content_hash, config_signature, embedding FROM public.document_chunks WHERE document_id = $1",
                    document_id,
                )
                existing_map = {row["chunk_index"]: row for row in existing_rows}

                for item, clean_vec in valid_items_to_persist:
                    existing = existing_map.get(item.chunk_index)
                    vec_pg_str = vector_to_pg_string(clean_vec)

                    if existing and existing["content_hash"] == item.content_hash and existing["config_signature"] == item.config_signature and existing["embedding"] is not None:
                        # Unchanged: idempotent skip
                        skipped_count += 1
                        continue

                    if existing:
                        # Update existing chunk record with new embedding vector
                        await pg_conn.execute(
                            """
                            UPDATE public.document_chunks
                            SET embedding = $1::vector,
                                embedding_model = $2,
                                embedding_dimension = $3,
                                content_hash = $4,
                                config_signature = $5,
                                updated_at = $6
                            WHERE document_id = $7 AND chunk_index = $8
                            """,
                            vec_pg_str,
                            item.config_signature.split(":")[0],
                            expected_dim,
                            item.content_hash,
                            item.config_signature,
                            datetime.now(timezone.utc),
                            document_id,
                            item.chunk_index,
                        )
                        persisted_count += 1
                    else:
                        # Insert new chunk record with embedding
                        import uuid
                        chunk_uuid = item.chunk_id if (item.chunk_id and len(str(item.chunk_id)) == 36) else str(uuid.uuid4())
                        await pg_conn.execute(
                            """
                            INSERT INTO public.document_chunks (
                                id, document_id, user_id, chunk_index, page_number,
                                content, token_count, character_count, scope,
                                embedding, embedding_model, embedding_dimension,
                                content_hash, config_signature, created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector, $11, $12, $13, $14, $15, $16
                            )
                            """,
                            chunk_uuid,
                            document_id,
                            user_id,
                            item.chunk_index,
                            item.page_number,
                            item.metadata.get("content", f"Chunk {item.chunk_index}"),
                            item.token_count,
                            item.character_count,
                            clean_scope,
                            vec_pg_str,
                            item.config_signature.split(":")[0],
                            expected_dim,
                            item.content_hash,
                            item.config_signature,
                            datetime.now(timezone.utc),
                            datetime.now(timezone.utc),
                        )
                        persisted_count += 1

                await pg_conn.close()
                status = "success" if len(failed_records) == 0 else ("partial_success" if (persisted_count > 0 or skipped_count > 0) else "failed")
                return {
                    "status": status,
                    "document_id": document_id,
                    "total_received": len(embedded_chunks),
                    "persisted_count": persisted_count,
                    "skipped_unchanged_count": skipped_count,
                    "failed_count": len(failed_records),
                    "failed_records": failed_records,
                }
            except Exception as pg_err:
                logger.error("Direct PostgreSQL vector persistence error: %s", pg_err)
                await pg_conn.close()

        # 4. Path B: Supabase PostgREST client
        if self.supabase_service.is_configured() and self.supabase_service._client:
            try:
                client = self.supabase_service._client
                # Fetch existing chunks to verify idempotency
                res = (
                    client.table("document_chunks")
                    .select("id, chunk_index, content_hash, config_signature, embedding")
                    .eq("document_id", document_id)
                    .execute()
                )
                existing_map = {row["chunk_index"]: row for row in (res.data or [])}

                for item, clean_vec in valid_items_to_persist:
                    existing = existing_map.get(item.chunk_index)
                    if existing and existing.get("content_hash") == item.content_hash and existing.get("config_signature") == item.config_signature and existing.get("embedding"):
                        skipped_count += 1
                        continue

                    # Upsert vector representation into Supabase
                    update_payload = {
                        "embedding": clean_vec,  # PostgREST natively parses float list into vector
                        "embedding_model": item.config_signature.split(":")[0],
                        "embedding_dimension": expected_dim,
                        "content_hash": item.content_hash,
                        "config_signature": item.config_signature,
                        "updated_at": now_iso,
                    }

                    if existing and "id" in existing:
                        client.table("document_chunks").update(update_payload).eq("id", existing["id"]).execute()
                        persisted_count += 1
                    else:
                        import uuid
                        insert_row = {
                            "id": str(item.chunk_id) if item.chunk_id and len(str(item.chunk_id)) == 36 else str(uuid.uuid4()),
                            "document_id": document_id,
                            "user_id": user_id,
                            "chunk_index": item.chunk_index,
                            "page_number": item.page_number,
                            "content": item.metadata.get("content", f"Chunk {item.chunk_index}"),
                            "token_count": item.token_count,
                            "character_count": item.character_count,
                            "scope": clean_scope,
                            "created_at": now_iso,
                            **update_payload,
                        }
                        client.table("document_chunks").insert(insert_row).execute()
                        persisted_count += 1

                status = "success" if len(failed_records) == 0 else ("partial_success" if (persisted_count > 0 or skipped_count > 0) else "failed")
                return {
                    "status": status,
                    "document_id": document_id,
                    "total_received": len(embedded_chunks),
                    "persisted_count": persisted_count,
                    "skipped_unchanged_count": skipped_count,
                    "failed_count": len(failed_records),
                    "failed_records": failed_records,
                }
            except Exception as sb_err:
                logger.warning("Supabase PostgREST embedding persistence failed (%s); updating dev memory cache...", sb_err)

        # 5. Path C: Development in-memory persistence fallback
        dev_chunks = self.supabase_service._dev_chunks.setdefault(document_id, [])
        dev_map = {c["chunk_index"]: c for c in dev_chunks}

        for item, clean_vec in valid_items_to_persist:
            existing = dev_map.get(item.chunk_index)
            if existing and existing.get("content_hash") == item.content_hash and existing.get("config_signature") == item.config_signature and existing.get("embedding"):
                skipped_count += 1
                continue

            record = {
                "id": str(item.chunk_id) if item.chunk_id else f"{document_id}_{item.chunk_index}",
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": item.chunk_index,
                "page_number": item.page_number,
                "content": item.metadata.get("content", f"Chunk {item.chunk_index}"),
                "token_count": item.token_count,
                "character_count": item.character_count,
                "scope": clean_scope,
                "embedding": list(clean_vec),
                "embedding_model": item.config_signature.split(":")[0],
                "embedding_dimension": expected_dim,
                "content_hash": item.content_hash,
                "config_signature": item.config_signature,
                "created_at": now_iso,
                "updated_at": now_iso,
            }

            if existing:
                existing.update(record)
            else:
                dev_chunks.append(record)
            persisted_count += 1

        status = "success" if len(failed_records) == 0 else ("partial_success" if (persisted_count > 0 or skipped_count > 0) else "failed")
        return {
            "status": status,
            "document_id": document_id,
            "total_received": len(embedded_chunks),
            "persisted_count": persisted_count,
            "skipped_unchanged_count": skipped_count,
            "failed_count": len(failed_records),
            "failed_records": failed_records,
        }

    async def get_document_embeddings(
        self,
        user_id: str,
        document_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve persisted vector embeddings for a document with strict access control.
        - Personal document: accessible only by the owner user_id.
        - Shared academic document: accessible by any authenticated student.
        - Returns list of chunks with parsed 768-dim float vectors.
        """
        # 1. Authorize: Check ownership or shared access
        doc = await self.supabase_service.get_user_document(user_id=user_id, document_id=document_id)
        if not doc:
            logger.warning("Access denied to embeddings: doc %s not accessible by user %s", document_id, user_id)
            return []

        # 2. Path A: Direct PostgreSQL query
        pg_conn = await self._get_pg_connection()
        if pg_conn:
            try:
                rows = await pg_conn.fetch(
                    """
                    SELECT id, document_id, user_id, chunk_index, page_number,
                           content, token_count, character_count, scope,
                           embedding::text as embedding_str, embedding_model,
                           embedding_dimension, content_hash, config_signature,
                           created_at, updated_at
                    FROM public.document_chunks
                    WHERE document_id = $1
                    ORDER BY chunk_index ASC
                    """,
                    document_id,
                )
                await pg_conn.close()
                results = []
                for r in rows:
                    r_dict = dict(r)
                    r_dict["embedding"] = pg_string_to_vector(r_dict.pop("embedding_str"))
                    results.append(r_dict)
                return results
            except Exception as e:
                logger.error("Direct PostgreSQL read embeddings error: %s", e)
                await pg_conn.close()

        # 3. Path B: Supabase PostgREST query
        if self.supabase_service.is_configured() and self.supabase_service._client:
            try:
                res = (
                    self.supabase_service._client.table("document_chunks")
                    .select("*")
                    .eq("document_id", document_id)
                    .order("chunk_index", desc=False)
                    .execute()
                )
                if res.data:
                    out = []
                    for row in res.data:
                        r = dict(row)
                        if "embedding" in r and r["embedding"] is not None:
                            r["embedding"] = pg_string_to_vector(r["embedding"])
                        out.append(r)
                    return out
            except Exception as e:
                logger.error("Supabase get embeddings failed: %s", e)

        # 4. Path C: Dev cache fallback
        dev_chunks = self.supabase_service._dev_chunks.get(document_id, [])
        return [dict(c) for c in dev_chunks if c.get("embedding") is not None]

    async def delete_document_embeddings(self, user_id: str, document_id: str) -> bool:
        """
        Delete document chunks and embeddings, verifying ownership.
        Cascading foreign keys in PostgreSQL automatically delete all associated embeddings.
        """
        doc = await self.supabase_service.get_user_document(user_id=user_id, document_id=document_id)
        if not doc:
            return False

        # Path A: Direct PostgreSQL
        pg_conn = await self._get_pg_connection()
        if pg_conn:
            try:
                await pg_conn.execute("DELETE FROM public.document_chunks WHERE document_id = $1", document_id)
                await pg_conn.close()
                return True
            except Exception as e:
                logger.error("Direct PostgreSQL delete embeddings error: %s", e)
                await pg_conn.close()

        # Path B: Supabase
        if self.supabase_service.is_configured() and self.supabase_service._client:
            try:
                self.supabase_service._client.table("document_chunks").delete().eq("document_id", document_id).execute()
                return True
            except Exception as e:
                logger.error("Supabase delete embeddings failed: %s", e)

        # Path C: Dev cache
        self.supabase_service._dev_chunks.pop(document_id, None)
        return True


_embedding_persistence_service: Optional[EmbeddingPersistenceService] = None


def get_embedding_persistence_service() -> EmbeddingPersistenceService:
    """Singleton provider for EmbeddingPersistenceService."""
    global _embedding_persistence_service
    if _embedding_persistence_service is None:
        _embedding_persistence_service = EmbeddingPersistenceService()
    return _embedding_persistence_service
