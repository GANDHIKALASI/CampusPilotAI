"""Verification test suite for CampusPilot AI — Phase 3.3.
Tests:
- Waitlist application and duplicate prevention
- Token validation and 401 rejection for unauthenticated protected routes
- Absence of public registration/signup
- Persistent conversation lifecycle (create, list, get, rename, delete)
- Persistent message sending & AI response persistence
- Authenticated PDF upload, storage, extraction, chunking, and metadata tracking
- Secure signed download URL generation
- Strict user data isolation (User A vs User B)
- Backward compatibility for existing endpoints
"""

import jwt
import pymupdf
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

def create_mock_jwt(user_id: str, email: str) -> str:
    """Generate a valid test JWT token payload for testing."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "exp": 253402300799, # Far future
    }
    return jwt.encode(payload, "test-secret-key", algorithm="HS256")

def create_sample_pdf(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=10)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def run_tests():
    print("=== STARTING CAMPUSPILOT AI PHASE 3.3 TEST SUITE ===\n")
    passed = 0
    total = 10

    # User identities for testing
    user_a_id = str(uuid.uuid4())
    user_a_email = "student_a@university.edu"
    token_a = create_mock_jwt(user_a_id, user_a_email)

    user_b_id = str(uuid.uuid4())
    user_b_email = "student_b@university.edu"
    token_b = create_mock_jwt(user_b_id, user_b_email)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # --------------------------------------------------------------------------
    # Test 1: Waitlist Submission & Duplicate Handling
    # --------------------------------------------------------------------------
    print("Test 1: Waitlist Submission & Duplicate Handling")
    email_test = f"waitlist_student_{uuid.uuid4().hex[:6]}@college.edu"
    w_res1 = requests.post(f"{BASE_URL}/api/waitlist", json={
        "full_name": "Jordan Lee",
        "email": email_test,
        "institution": "Berkeley",
    })
    assert w_res1.status_code == 200, f"Waitlist submit failed: {w_res1.text}"
    assert w_res1.json()["status"] == "success"

    # Duplicate check
    w_res2 = requests.post(f"{BASE_URL}/api/waitlist", json={
        "full_name": "Jordan Lee",
        "email": email_test,
        "institution": "Berkeley",
    })
    assert w_res2.status_code == 200
    assert w_res2.json()["status"] == "already_registered"

    # Invalid email check
    w_res_invalid = requests.post(f"{BASE_URL}/api/waitlist", json={
        "full_name": "Bad Email",
        "email": "not-an-email",
    })
    assert w_res_invalid.status_code == 422, "Invalid email should be rejected with 422 Unprocessable Entity"
    print(" -> PASSED: Waitlist accepts valid entries, rejects bad emails, and prevents duplicates.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 2: Unauthenticated Protected Route Rejection (401)
    # --------------------------------------------------------------------------
    print("Test 2: Protected Routes Reject Unauthenticated Requests with 401")
    res_unauth_conv = requests.get(f"{BASE_URL}/api/conversations")
    assert res_unauth_conv.status_code == 401, f"Expected 401, got {res_unauth_conv.status_code}"

    res_unauth_docs = requests.get(f"{BASE_URL}/api/documents")
    assert res_unauth_docs.status_code == 401, f"Expected 401, got {res_unauth_docs.status_code}"
    print(" -> PASSED: Protected endpoints correctly return 401 Unauthorized without token.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 3: Absence of Public Registration / Signup Endpoints
    # --------------------------------------------------------------------------
    print("Test 3: Verify Public Registration Endpoint Does Not Exist")
    res_reg1 = requests.post(f"{BASE_URL}/api/auth/register", json={"email": "a@b.com", "password": "123"})
    assert res_reg1.status_code == 404, "No public register endpoint should exist"
    res_reg2 = requests.post(f"{BASE_URL}/api/auth/signup", json={"email": "a@b.com", "password": "123"})
    assert res_reg2.status_code == 404, "No public signup endpoint should exist"
    print(" -> PASSED: No public signup or registration endpoint is exposed.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 4: Conversation Lifecycle (Create, List, Rename, Delete)
    # --------------------------------------------------------------------------
    print("Test 4: Conversation Lifecycle (Create, List, Rename, Delete)")
    c_res = requests.post(f"{BASE_URL}/api/conversations", json={"title": "Linear Algebra Studies"}, headers=headers_a)
    assert c_res.status_code == 201
    conv_data = c_res.json()
    conv_id = conv_data["id"]
    assert conv_data["title"] == "Linear Algebra Studies"
    assert conv_data["user_id"] == user_a_id

    # List conversations for User A
    list_res = requests.get(f"{BASE_URL}/api/conversations", headers=headers_a)
    assert list_res.status_code == 200
    user_a_conv_ids = [c["id"] for c in list_res.json()]
    assert conv_id in user_a_conv_ids

    # Rename conversation
    rename_res = requests.patch(f"{BASE_URL}/api/conversations/{conv_id}", json={"title": "Advanced Matrix Theory"}, headers=headers_a)
    assert rename_res.status_code == 200
    assert rename_res.json()["title"] == "Advanced Matrix Theory"
    print(" -> PASSED: Conversation created, listed, and renamed successfully.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 5: Persistent Message Flow & Gemini Academic Response
    # --------------------------------------------------------------------------
    print("Test 5: Persistent Message Flow & Gemini Academic Response")
    msg_res = requests.post(
        f"{BASE_URL}/api/conversations/{conv_id}/messages",
        json={"content": "What is an eigenvalue in academic linear algebra?"},
        headers=headers_a,
    )
    assert msg_res.status_code == 200, f"Send message failed: {msg_res.text}"
    msg_data = msg_res.json()
    assert msg_data["user_message"]["role"] == "user"
    assert "eigenvalue" in msg_data["user_message"]["content"]
    assert msg_data["assistant_message"]["role"] == "model"
    assert len(msg_data["assistant_message"]["content"]) > 10

    # Retrieve conversation detail and verify chronological messages persisted
    detail_res = requests.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=headers_a)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert len(detail_data["messages"]) >= 2
    assert detail_data["messages"][0]["role"] == "user"
    assert detail_data["messages"][1]["role"] == "model"
    print(" -> PASSED: User message and Gemini assistant response persisted in conversation.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 6: Authenticated Document Upload, Storage, and Processing
    # --------------------------------------------------------------------------
    print("Test 6: Authenticated Document Upload, Storage, and Processing")
    pdf_sample = create_sample_pdf(
        "Operating Systems Syllabus. Module 1: Concurrency and Mutual Exclusion. "
        "Deadlocks occur when processes hold resources while waiting for others. "
        "Module 2: Virtual Memory and Paging."
    )
    upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        files={"file": ("os_syllabus.pdf", pdf_sample, "application/pdf")},
        headers=headers_a,
    )
    assert upload_res.status_code == 201, f"Document upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    doc_id = upload_data["document"]["id"]
    assert upload_data["document"]["filename"] == "os_syllabus.pdf"
    assert upload_data["document"]["processing_status"] == "completed"
    assert upload_data["total_pages"] == 1
    assert upload_data["total_chunks"] >= 1
    assert upload_data["document"]["user_id"] == user_a_id
    print(f" -> PASSED: Document persisted with {upload_data['total_chunks']} chunks in 'completed' status.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 7: List User Documents & Secure Signed Download URL
    # --------------------------------------------------------------------------
    print("Test 7: List User Documents & Secure Signed Download URL")
    docs_res = requests.get(f"{BASE_URL}/api/documents", headers=headers_a)
    assert docs_res.status_code == 200
    docs_list = docs_res.json()
    assert any(d["id"] == doc_id for d in docs_list)

    # Secure signed download URL
    dl_res = requests.get(f"{BASE_URL}/api/documents/{doc_id}/download", headers=headers_a)
    assert dl_res.status_code == 200
    dl_data = dl_res.json()
    assert "signed_url" in dl_data
    assert dl_data["filename"] == "os_syllabus.pdf"
    print(" -> PASSED: Document listed and secure signed download URL generated.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 8: Strict User Isolation (User B cannot access User A's data)
    # --------------------------------------------------------------------------
    print("Test 8: Strict User Isolation (User B cannot access User A's data)")
    # User B tries to view User A's conversation
    u_b_conv = requests.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=headers_b)
    assert u_b_conv.status_code == 404, f"User B should get 404 for User A's conversation, got {u_b_conv.status_code}"

    # User B tries to post a message into User A's conversation
    u_b_msg = requests.post(f"{BASE_URL}/api/conversations/{conv_id}/messages", json={"content": "Hacking"}, headers=headers_b)
    assert u_b_msg.status_code == 404

    # User B tries to get User A's document download URL
    u_b_dl = requests.get(f"{BASE_URL}/api/documents/{doc_id}/download", headers=headers_b)
    assert u_b_dl.status_code == 404, f"User B should get 404 for User A's document, got {u_b_dl.status_code}"

    # User B's document list should not contain User A's document
    u_b_docs = requests.get(f"{BASE_URL}/api/documents", headers=headers_b).json()
    assert not any(d["id"] == doc_id for d in u_b_docs)
    print(" -> PASSED: Complete tenant isolation verified between User A and User B.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 9: Conversation Deletion
    # --------------------------------------------------------------------------
    print("Test 9: Conversation Deletion")
    del_res = requests.delete(f"{BASE_URL}/api/conversations/{conv_id}", headers=headers_a)
    assert del_res.status_code == 204
    # Verify it is gone
    get_del = requests.get(f"{BASE_URL}/api/conversations/{conv_id}", headers=headers_a)
    assert get_del.status_code == 404
    print(" -> PASSED: Conversation deleted and verified absent.")
    passed += 1

    # --------------------------------------------------------------------------
    # Test 10: Backward Compatibility for Existing Endpoints
    # --------------------------------------------------------------------------
    print("Test 10: Backward Compatibility for Existing Endpoints")
    # Health check
    h_res = requests.get(f"{BASE_URL}/api/chat/health")
    assert h_res.status_code == 200 and h_res.json()["status"] == "healthy"

    # Stateless extraction
    ext_res = requests.post(f"{BASE_URL}/api/documents/extract", files={"file": ("test.pdf", pdf_sample, "application/pdf")})
    assert ext_res.status_code == 200 and ext_res.json()["total_pages"] == 1

    # Stateless chunking
    chunk_res = requests.post(f"{BASE_URL}/api/documents/chunk", files={"file": ("test.pdf", pdf_sample, "application/pdf")})
    assert chunk_res.status_code == 200 and chunk_res.json()["total_chunks"] >= 1
    print(" -> PASSED: All previous milestone endpoints continue operating without regression.")
    passed += 1

    print(f"\n=== ALL {passed}/{total} PHASE 3.3 TESTS COMPLETED AND PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
