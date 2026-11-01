"""
Phase 3.4.2 Comprehensive Bulk Embedding Verification Suite.

Tests all 10 required scenarios:
1. One chunk
2. Multiple chunks
3. Empty chunks
4. Long chunks
5. API failure
6. Retry behavior
7. Partial batch failure
8. Duplicate processing (Idempotency)
9. Changed chunk content
10. Vector dimension validation
"""

import json
import logging
import math
import sys
import time
from unittest.mock import MagicMock, patch

from google.genai.errors import APIError

from app.core.config import get_settings
from app.schemas.chunk import DocumentChunk
from app.schemas.embedding import (
    BulkEmbeddingResult,
    EmbeddedChunk,
    FailedChunk,
    SkippedChunk,
)
from app.services.embedding import (
    EmbeddingService,
    compute_chunk_hash,
    compute_config_signature,
    estimate_embedding_cost,
    get_embedding_service,
    validate_vector,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_all_tests():
    settings = get_settings()
    svc = get_embedding_service()

    print("=======================================================")
    print("PHASE 3.4.2 — BULK EMBEDDING VERIFICATION SUITE")
    print("=======================================================")
    print(f"Model: {settings.gemini_embedding_model}")
    print(f"Configured Dimension: {settings.embedding_dimension}")
    print(f"Batch Size: {settings.embedding_batch_size}")
    print(f"Max Retries: {settings.embedding_max_retries}")
    print("=======================================================\n")

    results = {}
    total_start = time.perf_counter()

    # -------------------------------------------------------------
    # TEST 1: One Chunk
    # -------------------------------------------------------------
    print("[TEST 1/10] One Chunk Embedding...")
    t1_chunk = {
        "id": "doc_test_c1",
        "chunk_index": 0,
        "page_number": 1,
        "filename": "computer_architecture.pdf",
        "content": (
            "Pipelining is an implementation technique whereby multiple instructions are overlapped "
            "in execution. The computer pipeline is divided in stages, each designed to perform a particular "
            "part of the instruction cycle (Fetch, Decode, Execute, Memory Access, Write Back)."
        ),
        "token_count": 48,
    }

    t1_res = svc.embed_chunks_bulk(
        chunks=[t1_chunk],
        document_title="Computer Architecture Ch. 3",
    )

    assert t1_res.status == "success", f"Expected success, got {t1_res.status}"
    assert t1_res.successful_count == 1, f"Expected 1 successful chunk, got {t1_res.successful_count}"
    assert t1_res.failed_count == 0
    assert len(t1_res.successful_chunks) == 1
    t1_vec = t1_res.successful_chunks[0].vector
    assert len(t1_vec) == 768, f"Expected 768 dim, got {len(t1_vec)}"
    assert t1_res.successful_chunks[0].chunk_id == "doc_test_c1"
    assert t1_res.successful_chunks[0].page_number == 1
    assert t1_res.successful_chunks[0].filename == "computer_architecture.pdf"
    assert len(t1_res.successful_chunks[0].content_hash) == 64

    results["TEST_1_ONE_CHUNK"] = {
        "status": "PASS",
        "dimension": len(t1_vec),
        "chunk_id": t1_res.successful_chunks[0].chunk_id,
        "api_calls": t1_res.api_calls_made,
        "latency_sec": t1_res.total_latency_seconds,
    }
    print(f" -> PASS: Single chunk embedded into {len(t1_vec)} dimensions in {t1_res.total_latency_seconds:.3f}s\n")

    # -------------------------------------------------------------
    # TEST 2: Multiple Chunks (Batching)
    # -------------------------------------------------------------
    print("[TEST 2/10] Multiple Chunks with Batching...")
    t2_chunks = [
        {
            "id": f"chunk_multi_{i}",
            "chunk_index": i,
            "page_number": (i // 2) + 1,
            "filename": "quantum_mechanics.pdf",
            "content": content,
            "token_count": len(content.split()),
        }
        for i, content in enumerate([
            "Wave-particle duality postulates that every particle or quantum entity may be described as either a particle or a wave.",
            "The Schrödinger equation is a linear partial differential equation that governs the wave function of a quantum-mechanical system.",
            "Heisenberg uncertainty principle states that the position and momentum of a particle cannot be simultaneously measured with arbitrarily high precision.",
            "Quantum entanglement is a phenomenon where quantum particles become inextricably linked regardless of distance.",
            "Superposition principle asserts that any two or more quantum states can be added together and the result will be another valid quantum state.",
        ])
    ]

    # Use batch_size=2 to test multi-batch orchestration (5 chunks in batches of 2 -> 3 API calls)
    t2_res = svc.embed_chunks_bulk(
        chunks=t2_chunks,
        document_title="Principles of Quantum Mechanics",
        batch_size=2,
    )

    assert t2_res.status == "success"
    assert t2_res.successful_count == 5
    assert t2_res.failed_count == 0
    assert t2_res.api_calls_made == 3, f"Expected 3 batch calls for 5 chunks (batch size 2), got {t2_res.api_calls_made}"
    for idx, c in enumerate(t2_res.successful_chunks):
        assert c.chunk_index == idx
        assert len(c.vector) == 768
        assert c.filename == "quantum_mechanics.pdf"

    results["TEST_2_MULTIPLE_CHUNKS"] = {
        "status": "PASS",
        "total_chunks": 5,
        "successful_count": t2_res.successful_count,
        "batch_size_used": 2,
        "api_calls_made": t2_res.api_calls_made,
        "average_call_latency_ms": t2_res.average_latency_per_call_ms,
        "estimated_cost_usd": t2_res.estimated_cost_usd,
    }
    print(f" -> PASS: 5 chunks successfully embedded across {t2_res.api_calls_made} batch API calls.\n")

    # -------------------------------------------------------------
    # TEST 3: Empty Chunks (Trap without sending to API)
    # -------------------------------------------------------------
    print("[TEST 3/10] Empty Chunks Handling...")
    t3_chunks = [
        {"id": "c_empty_1", "chunk_index": 0, "content": ""},
        {"id": "c_empty_2", "chunk_index": 1, "content": "   \n\t  "},
    ]

    t3_res = svc.embed_chunks_bulk(chunks=t3_chunks)
    assert t3_res.status == "failed"
    assert t3_res.successful_count == 0
    assert t3_res.failed_count == 2
    assert t3_res.api_calls_made == 0, f"Empty chunks must not trigger API network calls, but made {t3_res.api_calls_made}"
    assert "empty" in t3_res.failed_chunks[0].error.lower()

    results["TEST_3_EMPTY_CHUNKS"] = {
        "status": "PASS",
        "empty_chunks_received": 2,
        "failed_count": t3_res.failed_count,
        "api_calls_made": t3_res.api_calls_made,
        "error_message": t3_res.failed_chunks[0].error,
    }
    print(" -> PASS: Empty and whitespace-only chunks trapped locally; 0 network calls executed.\n")

    # -------------------------------------------------------------
    # TEST 4: Long Chunks (Within 8192 Token Window)
    # -------------------------------------------------------------
    print("[TEST 4/10] Long Chunk (Dense Academic Treatise)...")
    long_academic_text = (
        "In the formal verification of distributed consensus protocols, safety and liveness "
        "properties must be mathematically proven under asynchronous network assumptions. "
        "A consensus algorithm ensures that a set of processes agree on a single value or state machine "
        "transition despite network delays, packet reordering, and arbitrary crash failures. "
    ) * 15  # ~600 words, ~3,700 characters

    t4_chunk = {
        "id": "c_long_1",
        "chunk_index": 0,
        "page_number": 42,
        "filename": "distributed_consensus_handbook.pdf",
        "content": long_academic_text,
    }

    t4_res = svc.embed_chunks_bulk(
        chunks=[t4_chunk],
        document_title="Formal Verification of Distributed Protocols",
    )

    assert t4_res.status == "success"
    assert t4_res.successful_count == 1
    assert len(t4_res.successful_chunks[0].vector) == 768
    assert t4_res.total_characters_embedded == len(long_academic_text)

    results["TEST_4_LONG_CHUNK"] = {
        "status": "PASS",
        "character_count": len(long_academic_text),
        "dimension": len(t4_res.successful_chunks[0].vector),
        "cost_usd": t4_res.estimated_cost_usd,
    }
    print(f" -> PASS: Long academic chunk ({len(long_academic_text)} chars) embedded smoothly.\n")

    # -------------------------------------------------------------
    # TEST 5: API Failure (Non-fatal, Structured Reporting)
    # -------------------------------------------------------------
    print("[TEST 5/10] API Failure Simulation...")
    # Mock client to simulate an unrecoverable 403 API key permission error
    mock_bad_client = MagicMock()
    mock_bad_client.models.embed_content.side_effect = APIError(
        403,
        {"error": {"message": "API_KEY_INVALID: The provided API key does not have permission."}},
    )

    with patch.object(svc, "_client", mock_bad_client):
        t5_res = svc.embed_chunks_bulk(
            chunks=[{"id": "bad_chunk_1", "chunk_index": 0, "content": "Sample content"}],
            max_retries=1,
        )

    assert t5_res.status == "failed"
    assert t5_res.failed_count == 1
    assert t5_res.successful_count == 0
    assert "403" in t5_res.failed_chunks[0].error or "permission" in t5_res.failed_chunks[0].error.lower()
    assert t5_res.failed_chunks[0].retryable is False

    results["TEST_5_API_FAILURE"] = {
        "status": "PASS",
        "status_reported": t5_res.status,
        "failed_chunks": t5_res.failed_count,
        "error_captured": t5_res.failed_chunks[0].error,
    }
    print(f" -> PASS: Fatal API error cleanly captured without crashing service.\n")

    # -------------------------------------------------------------
    # TEST 6: Retry Behavior with Exponential Backoff
    # -------------------------------------------------------------
    print("[TEST 6/10] Retry Behavior on Transient Errors...")
    attempt_counter = {"count": 0}

    def flaky_embed_content(*args, **kwargs):
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 2:
            raise APIError(503, {"error": {"message": "The service is temporarily overloaded."}})
        # Success on attempt 2
        mock_resp = MagicMock()
        mock_resp.embeddings = [MagicMock(values=[0.1] * 768)]
        return mock_resp

    mock_flaky_client = MagicMock()
    mock_flaky_client.models.embed_content.side_effect = flaky_embed_content

    with patch.object(svc, "_client", mock_flaky_client):
        t6_res = svc.embed_chunks_bulk(
            chunks=[{"id": "flaky_chunk", "chunk_index": 0, "content": "Transient test content"}],
            max_retries=3,
        )

    assert t6_res.status == "success"
    assert t6_res.successful_count == 1
    assert attempt_counter["count"] == 2, f"Expected 2 attempts (1 failure + 1 success), got {attempt_counter['count']}"

    results["TEST_6_RETRY_BEHAVIOR"] = {
        "status": "PASS",
        "attempts_executed": attempt_counter["count"],
        "final_status": t6_res.status,
    }
    print(f" -> PASS: Transient 503 error successfully retried and recovered on attempt {attempt_counter['count']}.\n")

    # -------------------------------------------------------------
    # TEST 7: Partial Batch Failure (Granular Fallback)
    # -------------------------------------------------------------
    print("[TEST 7/10] Partial Batch Failure Isolation...")

    def selective_embed_content(*args, **kwargs):
        contents = kwargs.get("contents")
        # If batch call with list of contents -> fail the whole batch
        if isinstance(contents, list) and len(contents) > 1:
            raise APIError(500, {"error": {"message": "Internal batch processor exception"}})
        # If single item call in fallback -> chunk 1 fails, chunk 0 and 2 succeed
        text = contents if isinstance(contents, str) else contents[0].parts[0].text
        if "bad_item" in text:
            raise ValueError("Corrupted character stream in single item")
        mock_resp = MagicMock()
        mock_resp.embeddings = [MagicMock(values=[0.05] * 768)]
        return mock_resp

    mock_selective_client = MagicMock()
    mock_selective_client.models.embed_content.side_effect = selective_embed_content

    t7_batch = [
        {"id": "good_1", "chunk_index": 0, "content": "Good chunk 1"},
        {"id": "bad_1", "chunk_index": 1, "content": "Contains bad_item sequence"},
        {"id": "good_2", "chunk_index": 2, "content": "Good chunk 2"},
    ]

    with patch.object(svc, "_client", mock_selective_client):
        t7_res = svc.embed_chunks_bulk(chunks=t7_batch, max_retries=1)

    assert t7_res.status == "partial_success", f"Expected partial_success, got {t7_res.status}"
    assert t7_res.successful_count == 2
    assert t7_res.failed_count == 1
    assert t7_res.failed_chunks[0].chunk_id == "bad_1"

    results["TEST_7_PARTIAL_BATCH_FAILURE"] = {
        "status": "PASS",
        "status_reported": t7_res.status,
        "successful_count": t7_res.successful_count,
        "failed_count": t7_res.failed_count,
        "isolated_failed_chunk_id": t7_res.failed_chunks[0].chunk_id,
    }
    print(f" -> PASS: Batch failure isolated: 2 good chunks succeeded, 1 bad chunk recorded.\n")

    # -------------------------------------------------------------
    # TEST 8: Duplicate Processing (Idempotency - No Repeated Calls)
    # -------------------------------------------------------------
    print("[TEST 8/10] Duplicate Processing & Idempotency...")
    # Build existing embeddings cache from Test 2
    existing_registry = {}
    for c in t2_res.successful_chunks:
        existing_registry[str(c.chunk_id)] = {
            "content_hash": c.content_hash,
            "config_signature": c.config_signature,
            "vector": c.vector,
        }

    # Run bulk embedding again with identical chunks and the existing registry
    t8_res = svc.embed_chunks_bulk(
        chunks=t2_chunks,
        document_title="Principles of Quantum Mechanics",
        existing_embeddings=existing_registry,
    )

    assert t8_res.status == "success"
    assert t8_res.skipped_count == 5, f"Expected 5 skipped chunks, got {t8_res.skipped_count}"
    assert t8_res.api_calls_made == 0, f"Idempotency must prevent repeated API calls, made {t8_res.api_calls_made}"
    assert t8_res.successful_count == 5, "Successful results should still be returned from cache"

    results["TEST_8_DUPLICATE_PROCESSING"] = {
        "status": "PASS",
        "chunks_checked": len(t2_chunks),
        "skipped_unchanged": t8_res.skipped_count,
        "api_calls_saved": len(t2_chunks),
        "api_calls_made": t8_res.api_calls_made,
    }
    print(f" -> PASS: Idempotency verified: 5/5 unchanged chunks skipped, 0 API calls made.\n")

    # -------------------------------------------------------------
    # TEST 9: Changed Chunk Content (Selective Invalidation)
    # -------------------------------------------------------------
    print("[TEST 9/10] Changed Chunk Content Detection...")
    # Modify chunk 2 content
    modified_chunks = [dict(c) for c in t2_chunks]
    modified_chunks[2]["content"] = (
        "MODIFIED CONTENT: The generalized Robertson-Schrödinger uncertainty relation "
        "provides a stronger lower bound on the product of standard deviations."
    )

    t9_res = svc.embed_chunks_bulk(
        chunks=modified_chunks,
        document_title="Principles of Quantum Mechanics",
        existing_embeddings=existing_registry,
    )

    assert t9_res.status == "success"
    assert t9_res.skipped_count == 4, f"Expected 4 unchanged chunks skipped, got {t9_res.skipped_count}"
    assert t9_res.successful_count == 5
    assert t9_res.api_calls_made == 1, f"Expected exactly 1 API call for the modified chunk, got {t9_res.api_calls_made}"

    # Verify that the modified chunk got a new content hash
    old_c2_hash = existing_registry[modified_chunks[2]["id"]]["content_hash"]
    new_c2 = next(c for c in t9_res.successful_chunks if c.chunk_id == modified_chunks[2]["id"])
    assert new_c2.content_hash != old_c2_hash, "Modified chunk must have a different content hash"

    results["TEST_9_CHANGED_CONTENT"] = {
        "status": "PASS",
        "skipped_unchanged": t9_res.skipped_count,
        "reembedded_count": 1,
        "api_calls_made": t9_res.api_calls_made,
        "hash_invalidated_chunk": modified_chunks[2]["id"],
    }
    print(f" -> PASS: Modified chunk detected, content hash invalidated, and re-embedded while keeping others cached.\n")

    # -------------------------------------------------------------
    # TEST 10: Vector Dimension Validation
    # -------------------------------------------------------------
    print("[TEST 10/10] Vector Dimension and Numerical Integrity Validation...")
    # Test validator directly
    try:
        validate_vector([0.1] * 512, expected_dim=768)
        assert False, "Should have rejected 512-dim vector"
    except ValueError as e:
        assert "dimension" in str(e).lower()

    try:
        validate_vector([0.1] * 767 + [float("nan")], expected_dim=768)
        assert False, "Should have rejected NaN vector"
    except ValueError as e:
        assert "nan" in str(e).lower()

    # Test through embed_chunks_bulk with corrupted vector from mock
    mock_bad_vec_client = MagicMock()
    mock_bad_vec_client.models.embed_content.return_value = MagicMock(
        embeddings=[MagicMock(values=[0.1] * 256)]  # Wrong dimension (256 instead of 768)
    )

    with patch.object(svc, "_client", mock_bad_vec_client):
        t10_res = svc.embed_chunks_bulk(
            chunks=[{"id": "dim_test_chunk", "chunk_index": 0, "content": "Testing dimensions"}],
            max_retries=0,
        )

    assert t10_res.status == "failed"
    assert t10_res.failed_count == 1
    assert "Expected vector dimension 768" in t10_res.failed_chunks[0].error

    results["TEST_10_VECTOR_VALIDATION"] = {
        "status": "PASS",
        "wrong_dimension_rejected": True,
        "nan_rejected": True,
        "error_captured": t10_res.failed_chunks[0].error,
    }
    print(" -> PASS: Strict dimension (768) and finite floating point validation enforced.\n")

    # -------------------------------------------------------------
    # PRINT FINAL SUMMARY
    # -------------------------------------------------------------
    total_elapsed = time.perf_counter() - total_start
    print("=======================================================")
    print(f"ALL 10 TESTS COMPLETED IN {total_elapsed:.2f}s")
    print("=======================================================")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    results = run_all_tests()
    all_passed = all(r.get("status") == "PASS" for r in results.values())
    if not all_passed:
        sys.exit(1)
