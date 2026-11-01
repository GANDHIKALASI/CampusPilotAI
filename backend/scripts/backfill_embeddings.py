"""
CampusPilot AI — Safe Production Embeddings Backfill Script.

Generates and persists 768-dimensional Gemini embeddings (`gemini-embedding-2`)
for existing document chunks in hosted Supabase PostgreSQL pgvector.

Features:
- Queries only chunks where embedding IS NULL (or incompatible).
- Configurable batch size (default: 20 chunks per batch).
- Safe dry-run mode (--dry-run) making zero writes.
- Strict numeric validation (768 finite floats).
- Idempotency via EmbeddingPersistenceService.
- Bounded exponential backoff on transient Gemini API errors.
- Progress logging and resumption support on interruption.
- Preserves all chunk IDs, document associations, and academic metadata.
"""

import argparse
import asyncio
import json
import logging
import math
import sys
import time
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings
from app.schemas.embedding import EmbeddedChunk
from app.services.embedding import (
    EmbeddingService,
    compute_chunk_hash,
    compute_config_signature,
    get_embedding_service,
    validate_vector,
)
from app.services.embedding_persistence import (
    EmbeddingPersistenceService,
    get_embedding_persistence_service,
    validate_embedding_vector,
)
from app.services.supabase import SupabaseService, get_supabase_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("backfill_embeddings")


class EmbeddingsBackfiller:
    """Manages the controlled batch backfill of document chunks."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase_service: Optional[SupabaseService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        persistence_service: Optional[EmbeddingPersistenceService] = None,
        batch_size: int = 20,
        dry_run: bool = False,
    ) -> None:
        self.settings = settings or get_settings()
        self.supabase_service = supabase_service or get_supabase_service()
        self.embedding_service = embedding_service or get_embedding_service()
        self.persistence_service = persistence_service or get_embedding_persistence_service()
        self.batch_size = max(1, min(batch_size, 50))
        self.dry_run = dry_run

    def fetch_eligible_chunks(self) -> List[Dict[str, Any]]:
        """Fetch all chunks from hosted Supabase where embedding is NULL."""
        if not self.supabase_service.is_configured() or not self.supabase_service._client:
            raise RuntimeError("Supabase client is not configured with live credentials.")

        client = self.supabase_service._client
        # Query chunks with null embeddings ordered by document_id and chunk_index
        res = (
            client.table("document_chunks")
            .select(
                "id, document_id, user_id, chunk_index, page_number, content, "
                "token_count, character_count, scope, semester_id, subject_id, unit_id, "
                "content_hash, config_signature, embedding"
            )
            .is_("embedding", "null")
            .order("document_id")
            .order("chunk_index")
            .execute()
        )
        return res.data or []

    def fetch_document_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Fetch document metadata for contextual title inclusion in embeddings."""
        client = self.supabase_service._client
        res = client.table("documents").select("id, filename, scope, user_id").execute()
        return {d["id"]: d for d in (res.data or [])}

    async def run(self) -> Dict[str, Any]:
        """Execute the controlled batch backfill."""
        start_time = time.perf_counter()
        logger.info("Starting Embeddings Backfill (Dry Run = %s, Batch Size = %d)...", self.dry_run, self.batch_size)

        eligible_chunks = self.fetch_eligible_chunks()
        total_eligible = len(eligible_chunks)
        logger.info("Found %d chunks eligible for backfill (embedding IS NULL).", total_eligible)

        if total_eligible == 0:
            logger.info("No chunks require backfill. All existing chunks have valid embeddings.")
            return {
                "status": "success",
                "total_eligible": 0,
                "total_embedded": 0,
                "total_persisted": 0,
                "elapsed_seconds": 0.0,
            }

        doc_lookup = self.fetch_document_lookup()

        total_batches = math.ceil(total_eligible / self.batch_size)
        total_chars = sum(c.get("character_count", len(c.get("content", ""))) for c in eligible_chunks)
        est_cost = (total_chars / 1000.0) * 0.00002

        logger.info(
            "Backfill Plan: %d chunks across %d batches | %d chars | Est. Cost: $%.5f USD",
            total_eligible,
            total_batches,
            total_chars,
            est_cost,
        )

        if self.dry_run:
            logger.info("=== DRY RUN MODE: No API calls to generate embeddings or DB writes will occur ===")
            doc_groups: Dict[str, int] = {}
            for c in eligible_chunks:
                d_id = c["document_id"]
                fname = doc_lookup.get(d_id, {}).get("filename", "Unknown")
                doc_groups[fname] = doc_groups.get(fname, 0) + 1

            for fname, count in doc_groups.items():
                logger.info("  - Document '%s': %d chunks scheduled", fname, count)

            return {
                "status": "dry_run_complete",
                "total_eligible": total_eligible,
                "batches_planned": total_batches,
                "total_characters": total_chars,
                "estimated_cost_usd": est_cost,
                "documents_count": len(doc_groups),
                "documents_breakdown": doc_groups,
            }

        # LIVE EXECUTION MODE
        total_persisted = 0
        total_failed = 0
        failed_chunk_ids = []

        for batch_idx in range(0, total_eligible, self.batch_size):
            batch = eligible_chunks[batch_idx : batch_idx + self.batch_size]
            current_batch_num = (batch_idx // self.batch_size) + 1
            logger.info(
                "Processing Batch %d/%d (%d chunks)...",
                current_batch_num,
                total_batches,
                len(batch),
            )

            # Group batch by document_id to provide accurate document_title
            batch_by_doc: Dict[str, List[Dict[str, Any]]] = {}
            for item in batch:
                batch_by_doc.setdefault(item["document_id"], []).append(item)

            for d_id, doc_chunks in batch_by_doc.items():
                doc_info = doc_lookup.get(d_id, {})
                filename = doc_info.get("filename", "document.pdf")
                scope = doc_info.get("scope", "personal")
                user_id = doc_info.get("user_id") or doc_chunks[0].get("user_id")

                # Generate embeddings for these chunks
                try:
                    bulk_res = self.embedding_service.embed_chunks_bulk(
                        chunks=doc_chunks,
                        document_title=filename,
                        force_reembed=False,
                    )
                except Exception as emb_err:
                    logger.error("Embedding API failure on batch %d for doc %s: %s", current_batch_num, d_id, emb_err)
                    total_failed += len(doc_chunks)
                    failed_chunk_ids.extend([c["id"] for c in doc_chunks])
                    continue

                if bulk_res.status == "failed" or not bulk_res.successful_chunks:
                    err_msg = bulk_res.failed_chunks[0].error if bulk_res.failed_chunks else "Unknown embedding error"
                    logger.error("Batch embedding returned failed status for doc %s: %s", d_id, err_msg)
                    total_failed += len(doc_chunks)
                    failed_chunk_ids.extend([c["id"] for c in doc_chunks])
                    continue

                # Validate vectors
                valid_embeddings = []
                for ec in bulk_res.successful_chunks:
                    try:
                        validate_embedding_vector(ec.vector, expected_dim=self.settings.embedding_dimension)
                        valid_embeddings.append(ec)
                    except Exception as val_err:
                        logger.error("Vector validation error for chunk %s: %s", ec.chunk_id, val_err)
                        total_failed += 1
                        failed_chunk_ids.append(str(ec.chunk_id))

                if not valid_embeddings:
                    continue

                # Persist via EmbeddingPersistenceService
                try:
                    persist_res = await self.persistence_service.persist_chunk_embeddings(
                        user_id=user_id,
                        document_id=d_id,
                        embedded_chunks=valid_embeddings,
                        scope=scope,
                    )
                    persisted = persist_res.get("persisted_count", 0)
                    skipped = persist_res.get("skipped_unchanged_count", 0)
                    failed = persist_res.get("failed_count", 0)
                    failed_recs = persist_res.get("failed_records", [])

                    if persist_res.get("status") == "failed" or (persisted == 0 and skipped == 0 and len(valid_embeddings) > 0):
                        logger.error("Persistence failed for doc %s: %s", d_id, failed_recs)
                        total_failed += len(valid_embeddings)
                        failed_chunk_ids.extend([c.chunk_id for c in valid_embeddings])
                    else:
                        total_persisted += persisted
                        total_failed += failed
                        if failed > 0:
                            failed_chunk_ids.extend([r.get("chunk_id") for r in failed_recs if r.get("chunk_id")])
                        logger.info(
                            "  -> Doc '%s': %d embeddings persisted (%d unchanged skipped, %d failed)",
                            filename,
                            persisted,
                            skipped,
                            failed,
                        )
                except Exception as persist_err:
                    logger.error("Persistence failed for doc %s: %s", d_id, persist_err)
                    total_failed += len(valid_embeddings)
                    failed_chunk_ids.extend([c.chunk_id for c in valid_embeddings])

            # Rate limit courtesy pause between batches
            await asyncio.sleep(0.5)

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Backfill Complete in %.2fs: %d persisted, %d failed out of %d eligible.",
            elapsed,
            total_persisted,
            total_failed,
            total_eligible,
        )

        return {
            "status": "success" if total_failed == 0 else "partial_success",
            "total_eligible": total_eligible,
            "total_persisted": total_persisted,
            "total_failed": total_failed,
            "failed_chunk_ids": failed_chunk_ids,
            "elapsed_seconds": round(elapsed, 2),
        }


def main():
    parser = argparse.ArgumentParser(description="Backfill document chunk embeddings in hosted Supabase pgvector.")
    parser.add_argument("--batch-size", type=int, default=20, help="Number of chunks per batch (1-50, default: 20)")
    parser.add_argument("--dry-run", action="store_true", help="Perform preflight and planning checks without writing embeddings")
    args = parser.parse_args()

    backfiller = EmbeddingsBackfiller(batch_size=args.batch_size, dry_run=args.dry_run)
    result = asyncio.run(backfiller.run())
    print("\nBACKFILL EXECUTION SUMMARY:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
