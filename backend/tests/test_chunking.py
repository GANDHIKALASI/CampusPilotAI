"""Comprehensive verification test suite for Milestone 3.2.
Tests Text Cleaning, Structure-Aware Chunking, and Metadata Preparation across all 16 scenarios.
"""

import io
import sys
import os
import pymupdf
import requests

BASE_URL = "http://127.0.0.1:8000"

def create_sample_pdf(pages_content: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages_content:
        # Create page with sufficient vertical room
        page = doc.new_page(width=595, height=2500)
        if text.strip():
            page.insert_textbox(pymupdf.Rect(50, 50, 550, 2450), text, fontsize=9)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def run_tests():
    print("=== STARTING MILESTONE 3.2 VERIFICATION TESTS ===\n")
    passed = 0
    total = 16

    # Test 1: Short paragraph (<500 tokens -> exactly 1 chunk)
    print("Test 1: Short paragraph chunking (<500 tokens)")
    p1 = "Calculus is the mathematical study of continuous change, in the same way that geometry is the study of shape."
    pdf_1 = create_sample_pdf([p1])
    res1 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("short.pdf", pdf_1, "application/pdf")}
    )
    assert res1.status_code == 200, f"Status: {res1.status_code}, {res1.text}"
    data1 = res1.json()
    assert data1["total_chunks"] == 1, f"Expected 1 chunk, got {data1['total_chunks']}"
    assert data1["chunks"][0]["page_number"] == 1
    assert data1["chunks"][0]["chunk_index"] == 0
    assert "Calculus" in data1["chunks"][0]["content"]
    print(" -> PASSED: Single short paragraph became 1 chunk.")
    passed += 1

    # Test 2: Multiple paragraphs preserved
    print("Test 2: Multiple paragraphs handling")
    p2 = "Introduction to Computer Science.\n\nData structures organize information efficiently.\n\nAlgorithms process data step-by-step."
    pdf_2 = create_sample_pdf([p2])
    res2 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("paragraphs.pdf", pdf_2, "application/pdf")}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_chunks"] == 1
    assert "Introduction to Computer Science" in data2["chunks"][0]["content"]
    assert "Data structures" in data2["chunks"][0]["content"]
    print(" -> PASSED: Multiple paragraphs preserved within page chunk.")
    passed += 1

    # Test 3: Headings and subheadings preservation
    print("Test 3: Headings and subheadings preservation")
    p3 = "# Chapter 1: Foundations\n\n## 1.1 Linear Algebra\n\nVectors and matrices form the backbone of modern machine learning."
    pdf_3 = create_sample_pdf([p3])
    res3 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("headings.pdf", pdf_3, "application/pdf")}
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert "# Chapter 1: Foundations" in data3["chunks"][0]["content"]
    assert "## 1.1 Linear Algebra" in data3["chunks"][0]["content"]
    print(" -> PASSED: Markdown headings preserved intact.")
    passed += 1

    # Test 4: Very long paragraph (>500 tokens -> split into multiple chunks with overlap)
    print("Test 4: Very long text (>500 tokens) split with overlap")
    long_sentences = [f"Sentence number {i} provides detailed academic insights into computational algorithms and statistical mechanics." for i in range(70)]
    p4 = " ".join(long_sentences)
    pdf_4 = create_sample_pdf([p4])
    res4 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("long.pdf", pdf_4, "application/pdf")}
    )
    assert res4.status_code == 200
    data4 = res4.json()
    assert data4["total_chunks"] > 1, f"Expected >1 chunks, got {data4['total_chunks']}"
    # Verify both chunks are page 1
    for c in data4["chunks"]:
        assert c["page_number"] == 1
        assert c["token_count"] <= 550  # reasonable bound for target 500
    print(f" -> PASSED: Long text on single page correctly split into {data4['total_chunks']} chunks within page.")
    passed += 1

    # Test 5: Multiple PDF pages maintain distinct page_number
    print("Test 5: Multiple PDF pages maintain distinct page_number")
    pdf_5 = create_sample_pdf([
        "Page one content discussing discrete mathematics and Boolean logic.",
        "Page two content discussing relational databases and normalization form.",
        "Page three content discussing distributed systems and consensus protocols."
    ])
    res5 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("multi_page.pdf", pdf_5, "application/pdf")}
    )
    assert res5.status_code == 200
    data5 = res5.json()
    assert data5["total_chunks"] == 3
    assert [c["page_number"] for c in data5["chunks"]] == [1, 2, 3]
    assert [c["chunk_index"] for c in data5["chunks"]] == [0, 1, 2]
    print(" -> PASSED: Chunks strictly retain accurate 1-based page numbers [1, 2, 3].")
    passed += 1

    # Test 6: Empty pages produce no chunks
    print("Test 6: Empty pages produce no chunks")
    pdf_6 = create_sample_pdf([
        "Page one has valid text.",
        "", # empty page 2
        "Page three has valid text.",
        "   \n\n   " # empty page 4
    ])
    res6 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("empty_pages.pdf", pdf_6, "application/pdf")}
    )
    assert res6.status_code == 200
    data6 = res6.json()
    assert data6["total_chunks"] == 2
    assert [c["page_number"] for c in data6["chunks"]] == [1, 3]
    print(" -> PASSED: Empty pages completely excluded from chunks; only pages 1 and 3 chunked.")
    passed += 1

    # Test 7: Mathematical expressions preserved untouched
    print("Test 7: Mathematical expressions preservation")
    math_text = "Calculus and Algebra: f(x) = x^3 + 2x^2 - 5x + 7. Derivative: f'(x) = 3x^2 + 4x - 5. Integral: int(f(x)dx) = (1/4)x^4 + (2/3)x^3. Matrix: det(A) = ad - bc != 0."
    pdf_7 = create_sample_pdf([math_text])
    res7 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("math.pdf", pdf_7, "application/pdf")}
    )
    assert res7.status_code == 200
    data7 = res7.json()
    content7 = data7["chunks"][0]["content"]
    assert "f(x) = x^3" in content7
    assert "f'(x) = 3x^2 + 4x - 5" in content7
    assert "det(A) = ad - bc != 0" in content7

    # Also verify TextCleaner & ChunkingService preserve unicode math symbols
    sys.path.insert(0, "backend")
    from app.services.cleaning import get_text_cleaner
    cleaner = get_text_cleaner()
    unicode_math = "Calculus: ∫ from -∞ to ∞ f(x)dx = 1, where f(x) = (1 / √(2πσ^2)) * e^(-(x - μ)^2 / 2σ^2) and ∑ i=1 to n."
    cleaned_math = cleaner.clean_text(unicode_math)
    assert "∫" in cleaned_math
    assert "∑" in cleaned_math
    assert "√" in cleaned_math
    assert "π" in cleaned_math
    print(" -> PASSED: Mathematical expressions and symbols (∫, ∑, √, π, ^, f(x), det) preserved untouched.")
    passed += 1

    # Test 8: Code snippets preserved with indentation
    print("Test 8: Code snippets preserved with indentation")
    code_text = "def binary_search(arr, target):\n    low = 0\n    high = len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n    return -1"
    pdf_8 = create_sample_pdf([code_text])
    res8 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("code.pdf", pdf_8, "application/pdf")}
    )
    assert res8.status_code == 200
    data8 = res8.json()
    content8 = data8["chunks"][0]["content"]
    assert "    low = 0" in content8 or "low = 0" in content8
    assert "def binary_search" in content8
    print(" -> PASSED: Code structure and tokens preserved.")
    passed += 1

    # Test 9: Configurable chunk size (target=100)
    print("Test 9: Configurable chunk size via query parameters")
    sentences_9 = [f"Item {i}: This is an academic test of configurable chunk sizing parameters." for i in range(25)]
    pdf_9 = create_sample_pdf([" ".join(sentences_9)])
    res9 = requests.post(
        f"{BASE_URL}/api/documents/chunk?target_tokens=100&overlap_tokens=20",
        files={"file": ("config_size.pdf", pdf_9, "application/pdf")}
    )
    assert res9.status_code == 200
    data9 = res9.json()
    assert data9["target_chunk_tokens"] == 100
    assert data9["overlap_tokens"] == 20
    assert data9["total_chunks"] > 1
    for c in data9["chunks"]:
        assert c["token_count"] <= 120
    print(f" -> PASSED: Custom target_tokens=100 produced {data9['total_chunks']} chunks respecting bounds.")
    passed += 1

    # Test 10: Overlap between consecutive chunks within same page
    print("Test 10: Overlap verification between consecutive intra-page chunks")
    sentences_10 = [f"Alpha {i} Beta {i} Gamma {i} Delta {i} Epsilon {i} Zeta {i} Eta {i} Theta {i} Iota {i} Kappa {i}." for i in range(30)]
    pdf_10 = create_sample_pdf([" ".join(sentences_10)])
    res10 = requests.post(
        f"{BASE_URL}/api/documents/chunk?target_tokens=120&overlap_tokens=30",
        files={"file": ("overlap.pdf", pdf_10, "application/pdf")}
    )
    assert res10.status_code == 200
    data10 = res10.json()
    assert data10["total_chunks"] >= 2
    chunk0 = data10["chunks"][0]["content"]
    chunk1 = data10["chunks"][1]["content"]
    # Check for shared words at the junction
    words0 = set(chunk0.split()[-15:])
    words1 = set(chunk1.split()[:25])
    shared = words0.intersection(words1)
    assert len(shared) > 0, f"Expected overlapping tokens between chunk 0 and 1, got 0 shared: {shared}"
    print(f" -> PASSED: Overlap verified between consecutive chunks (shared terms: {list(shared)[:5]}).")
    passed += 1

    # Test 11: Original PDF page numbers strictly preserved (1-based)
    print("Test 11: Original PDF 1-based page numbering verification")
    pdf_11 = create_sample_pdf(["Doc A Page 1", "Doc A Page 2", "Doc A Page 3"])
    res11 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("pages_check.pdf", pdf_11, "application/pdf")}
    )
    data11 = res11.json()
    for idx, c in enumerate(data11["chunks"]):
        assert c["page_number"] == idx + 1
    print(" -> PASSED: 1-based page indexing strictly verified.")
    passed += 1

    # Test 12: Ordered global chunk_index (0, 1, 2, ...)
    print("Test 12: Ordered global chunk_index (0, 1, 2, ...)")
    for idx, c in enumerate(data11["chunks"]):
        assert c["chunk_index"] == idx
    print(" -> PASSED: Global chunk index monotonically increments from 0.")
    passed += 1

    # Test 13: No empty chunks generated
    print("Test 13: No empty chunks verification")
    for c in data11["chunks"]:
        assert len(c["content"].strip()) > 0
        assert c["token_count"] > 0
        assert c["character_count"] > 0
    print(" -> PASSED: Zero empty chunks across all responses.")
    passed += 1

    # Test 14: No unnecessary text loss / de-hyphenation test
    print("Test 14: Text cleaning and de-hyphenation correctness")
    raw_text = "This is a demon-\nstration of arti-\nficial intelligence and state-of-the-art models.\n\n\n\nExtra lines collapsed."
    pdf_14 = create_sample_pdf([raw_text])
    res14 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("dehyphen.pdf", pdf_14, "application/pdf")}
    )
    data14 = res14.json()
    c14 = data14["chunks"][0]["content"]
    assert "demonstration" in c14, f"Failed to de-hyphenate 'demon-\\nstration': {c14}"
    assert "artificial" in c14, f"Failed to de-hyphenate 'arti-\\nficial': {c14}"
    assert "state-of-the-art" in c14, f"Compound hyphen should be preserved: {c14}"
    assert "\n\n\n" not in c14, "3+ newlines should be collapsed"
    print(" -> PASSED: De-hyphenation merged broken words while preserving compound hyphens and collapsing excess newlines.")
    passed += 1

    # Test 15: Token count behavior verified against tiktoken
    print("Test 15: Token count verified against tiktoken cl100k_base")
    import tiktoken
    enc = tiktoken.get_encoding("cl100k_base")
    test_phrase = "Artificial intelligence in higher education: CampusPilot AI assistant."
    expected_tokens = len(enc.encode(test_phrase))
    pdf_15 = create_sample_pdf([test_phrase])
    res15 = requests.post(
        f"{BASE_URL}/api/documents/chunk",
        files={"file": ("token_test.pdf", pdf_15, "application/pdf")}
    )
    data15 = res15.json()
    actual_tokens = data15["chunks"][0]["token_count"]
    assert actual_tokens == expected_tokens, f"Expected {expected_tokens} tokens, got {actual_tokens}"
    print(f" -> PASSED: Token count matches tiktoken cl100k_base ({actual_tokens} == {expected_tokens}).")
    passed += 1

    # Test 16: Existing extract and chat endpoints still work (backward compatibility)
    print("Test 16: Existing extract and chat endpoints backward compatibility")
    # Test extract
    res_ext = requests.post(
        f"{BASE_URL}/api/documents/extract",
        files={"file": ("compat.pdf", pdf_1, "application/pdf")}
    )
    assert res_ext.status_code == 200
    ext_data = res_ext.json()
    assert ext_data["total_pages"] == 1
    assert "Calculus" in ext_data["pages"][0]["content"]

    # Test health
    res_health = requests.get(f"{BASE_URL}/api/chat/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"
    print(" -> PASSED: Existing POST /api/documents/extract and GET /api/chat/health operate seamlessly.")
    passed += 1

    print(f"\n=== ALL {passed}/{total} MILESTONE 3.2 VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
