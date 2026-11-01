"""
Phase 3.4.1 — Embedding Model Evaluation & Validation Experiment.
Tests and benchmarks Google's Gemini Embedding 2 for CampusPilot AI.
"""

import math
import json
import time
from app.core.config import get_settings
from app.services.embedding import EmbeddingService, get_embedding_service

def run_experiment():
    print("\n=======================================================")
    print("PHASE 3.4.1 — EMBEDDING MODEL EVALUATION EXPERIMENT")
    print("=======================================================\n")

    settings = get_settings()
    service = get_embedding_service()

    print(f"1. Configuration Check:")
    print(f"   - Model: {settings.gemini_embedding_model}")
    print(f"   - Configured Dimension: {settings.embedding_dimension}")
    print(f"   - API Key Configured: {bool(settings.gemini_api_key)}")
    print(f"   - Key Length: {len(settings.gemini_api_key) if settings.gemini_api_key else 0} chars (Stored in backend/.env only)")

    assert service.is_configured(), "EmbeddingService reports unconfigured API key!"

    # -------------------------------------------------------------------------
    # Test Data: 4 Chunks + 2 Queries
    # -------------------------------------------------------------------------
    academic_paragraph = (
        "Distributed systems achieve fault tolerance through consensus replication protocols such as Raft and Paxos. "
        "In these protocols, a designated leader node sequences log entries and replicates them across follower nodes, "
        "requiring a majority quorum before committing state machine transitions."
    )

    academic_definition = (
        "A derivative represents the instantaneous rate of change of a continuous function with respect to its independent variable, "
        "formally defined in mathematical analysis as the limit of the difference quotient (f(x + h) - f(x)) / h as h approaches zero."
    )

    technical_explanation = (
        "Gradient descent is a first-order iterative optimization algorithm used to minimize differentiable objective loss functions. "
        "Model parameters theta are adjusted iteratively in the direction of steepest descent: theta := theta - alpha * nabla J(theta), "
        "where alpha represents the step size or learning rate."
    )

    multilingual_hindi = (
        "एल्गोरिदम (Algorithm) किसी विशिष्ट गणना या समस्या को हल करने के लिए नियमों और चरणों का एक स्पष्ट समूह है। "
        "कंप्यूटर विज्ञान में डेटा संरचनाएं (Data Structures) जानकारी को मेमोरी में व्यवस्थित और कुशलता से संग्रहीत करने का साधन प्रदान करती हैं।"
    )

    query_related = "How does the learning rate alpha affect parameter updates in gradient descent optimization?"
    query_unrelated = "What are the opening hours for the campus student cafeteria and gym on Sunday?"
    query_hindi = "कंप्यूटर प्रोग्रामिंग में एल्गोरिदम क्या होता है?"

    test_inputs = {
        "sample_1_academic_paragraph": {"text": academic_paragraph, "task": "RETRIEVAL_DOCUMENT", "title": "Distributed Systems"},
        "sample_2_academic_definition": {"text": academic_definition, "task": "RETRIEVAL_DOCUMENT", "title": "Calculus Foundations"},
        "sample_3_technical_explanation": {"text": technical_explanation, "task": "RETRIEVAL_DOCUMENT", "title": "Machine Learning Optimization"},
        "sample_4_multilingual_hindi": {"text": multilingual_hindi, "task": "RETRIEVAL_DOCUMENT", "title": "Computer Science Hindi"},
        "query_related_ml": {"text": query_related, "task": "RETRIEVAL_QUERY", "title": None},
        "query_unrelated_campus": {"text": query_unrelated, "task": "RETRIEVAL_QUERY", "title": None},
        "query_hindi_algo": {"text": query_hindi, "task": "RETRIEVAL_QUERY", "title": None},
    }

    # -------------------------------------------------------------------------
    # Generation & Dimensionality Verification
    # -------------------------------------------------------------------------
    print("\n2. Generating and Validating Vectors:")
    vectors = {}
    latencies = {}

    for name, item in test_inputs.items():
        t0 = time.perf_counter()
        if item["task"] == "RETRIEVAL_DOCUMENT":
            vec = service.embed_document_chunk(item["text"], document_title=item["title"])
        else:
            vec = service.embed_query(item["text"])
        t1 = time.perf_counter()
        latencies[name] = round((t1 - t0) * 1000, 2)

        # Validation Checks
        assert isinstance(vec, list), f"{name}: Vector is not a list!"
        assert len(vec) == 768, f"{name}: Dimension mismatch! Expected 768, got {len(vec)}"
        assert all(isinstance(v, (float, int)) for v in vec), f"{name}: Non-numeric value found!"
        assert all(math.isfinite(v) for v in vec), f"{name}: NaN or Infinite value found!"
        assert any(v != 0.0 for v in vec), f"{name}: All-zero vector!"

        vectors[name] = vec
        print(f"   ✓ {name:32} -> Dim: {len(vec)} | Latency: {latencies[name]}ms | Norm: {math.sqrt(sum(v*v for v in vec)):.4f}")

    # -------------------------------------------------------------------------
    # Cosine Similarity Benchmarking
    # -------------------------------------------------------------------------
    print("\n3. Cosine Similarity Matrix (Exploratory Benchmarking):")
    q_ml = vectors["query_related_ml"]
    sim_ml_to_s3 = service.cosine_similarity(q_ml, vectors["sample_3_technical_explanation"])
    sim_ml_to_s2 = service.cosine_similarity(q_ml, vectors["sample_2_academic_definition"])
    sim_ml_to_s1 = service.cosine_similarity(q_ml, vectors["sample_1_academic_paragraph"])
    sim_ml_to_s4 = service.cosine_similarity(q_ml, vectors["sample_4_multilingual_hindi"])
    sim_ml_to_unrelated = service.cosine_similarity(q_ml, vectors["query_unrelated_campus"])

    print(f"   • Query (ML Optimization) <-> Sample 3 (Technical Explanation - ML):     {sim_ml_to_s3:.4f} (STRONG MATCH)")
    print(f"   • Query (ML Optimization) <-> Sample 2 (Calculus Derivative Definition):  {sim_ml_to_s2:.4f} (MODERATE - mathematical context)")
    print(f"   • Query (ML Optimization) <-> Sample 1 (Distributed Systems Consensus):   {sim_ml_to_s1:.4f} (LOW - different CS domain)")
    print(f"   • Query (ML Optimization) <-> Sample 4 (Multilingual Hindi CS text):      {sim_ml_to_s4:.4f} (LOW - different topic)")
    print(f"   • Query (ML Optimization) <-> Query (Cafeteria / Campus Facilities):      {sim_ml_to_unrelated:.4f} (VERY LOW - unrelated domain)")

    assert sim_ml_to_s3 > sim_ml_to_s1, "Target chunk should have higher similarity than unrelated CS topic!"
    assert sim_ml_to_s3 > sim_ml_to_unrelated, "Target chunk should have higher similarity than cafeteria query!"

    # Multilingual Hindi test
    q_hi = vectors["query_hindi_algo"]
    sim_hi_to_s4 = service.cosine_similarity(q_hi, vectors["sample_4_multilingual_hindi"])
    sim_hi_to_s1 = service.cosine_similarity(q_hi, vectors["sample_1_academic_paragraph"])
    print(f"\n   • Multilingual Hindi Query <-> Hindi CS Document Chunk:                   {sim_hi_to_s4:.4f} (STRONG MATCH)")
    print(f"   • Multilingual Hindi Query <-> English Distributed Systems Chunk:         {sim_hi_to_s1:.4f} (LOW)")

    assert sim_hi_to_s4 > sim_hi_to_s1, "Hindi algorithm query should match Hindi algorithm chunk strongly!"

    # -------------------------------------------------------------------------
    # Error Handling & Edge Case Tests
    # -------------------------------------------------------------------------
    print("\n4. Error Handling & Edge Cases:")
    # 1. Empty string check
    try:
        service.embed_text("   \n\t  ")
        assert False, "Should have raised ValueError on empty string!"
    except ValueError as e:
        print(f"   ✓ Empty string rejected: {e}")

    # 2. None check
    try:
        service.embed_text("")
        assert False, "Should have raised ValueError on empty string!"
    except ValueError as e:
        print(f"   ✓ Zero-length string rejected: {e}")

    # -------------------------------------------------------------------------
    # Output Summary JSON
    # -------------------------------------------------------------------------
    summary = {
        "status": "PASS",
        "model_evaluated": settings.gemini_embedding_model,
        "dimensionality": settings.embedding_dimension,
        "sample_preview_vector_first_5": vectors["sample_3_technical_explanation"][:5],
        "similarities": {
            "query_ml_to_target_ml_explanation": round(sim_ml_to_s3, 4),
            "query_ml_to_math_calculus_definition": round(sim_ml_to_s2, 4),
            "query_ml_to_distributed_systems_chunk": round(sim_ml_to_s1, 4),
            "query_ml_to_hindi_chunk": round(sim_ml_to_s4, 4),
            "query_ml_to_unrelated_campus_facilities": round(sim_ml_to_unrelated, 4),
            "query_hindi_to_hindi_chunk": round(sim_hi_to_s4, 4),
            "query_hindi_to_english_systems_chunk": round(sim_hi_to_s1, 4),
        },
        "average_latency_ms": round(sum(latencies.values()) / len(latencies), 1),
    }

    print("\n=======================================================")
    print("EXPERIMENT RESULT SUMMARY JSON:")
    print("=======================================================")
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_experiment()
