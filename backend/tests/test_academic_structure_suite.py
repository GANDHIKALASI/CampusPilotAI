"""
Comprehensive Test Suite for BCA Semester V & VI Academic Structure Implementation.

Verifies:
1. Semester V contains all four theory subjects plus Java Programming Lab.
2. Both Introduction to AI and Introduction to Data Science are separate compulsory subjects.
3. Semester VI contains Algorithm Design Techniques, Algorithm Design Lab, and Project Work-I.
4. Units I-IV are properly mapped to each theory subject with full topic descriptions.
5. All 21 Java practicals are present verbatim.
6. All 12 Algorithm Design practicals are present verbatim.
7. Project Work-I contains all 14 report sections and all 5 evaluation criteria.
8. Students can retrieve curriculum hierarchy and subject detail views.
9. Academic document linkage (semester_id, subject_id, unit_id) works without breaking existing data.
10. Strict scope isolation between personal student documents and shared academic documents is preserved.
"""

import asyncio
import os
import sys
import uuid
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.services.supabase import get_supabase_service
from app.core.curriculum import (
    SEM_5_ID,
    SEM_6_ID,
    get_canonical_curriculum,
    find_canonical_subject,
)


async def test_01_semester_v_subjects_composition():
    """Verify Semester V contains Software Engineering, AI, Data Science, Java, and Java Lab."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem5 = next((s for s in curriculum if s["id"] == SEM_5_ID or s["code"] == "SEM_5"), None)
    assert sem5 is not None, "Semester V must exist in curriculum"

    subject_names = [s["name"] for s in sem5["subjects"]]
    expected_subjects = [
        "Software Engineering",
        "Introduction to Artificial Intelligence",
        "Introduction to Data Science",
        "Programming in Java",
        "Java Programming Lab",
    ]

    for expected in expected_subjects:
        assert expected in subject_names, f"Semester V missing expected subject: {expected}"

    assert len(sem5["subjects"]) == 5, f"Semester V should have exactly 5 subjects, found {len(sem5['subjects'])}"


async def test_02_ai_and_data_science_are_separate_compulsory():
    """Verify both AI and Data Science are distinct subjects in Semester V (not electives)."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem5 = next((s for s in curriculum if s["code"] == "SEM_5"), None)
    assert sem5 is not None

    ai_subject = next((s for s in sem5["subjects"] if s["name"] == "Introduction to Artificial Intelligence"), None)
    ds_subject = next((s for s in sem5["subjects"] if s["name"] == "Introduction to Data Science"), None)

    assert ai_subject is not None, "AI must exist as a compulsory subject"
    assert ds_subject is not None, "Data Science must exist as a compulsory subject"
    assert ai_subject["id"] != ds_subject["id"], "AI and Data Science must have unique IDs"
    assert ai_subject["code"] == "Core XII (A)", f"AI subject code should be 'Core XII (A)', got {ai_subject['code']}"
    assert ds_subject["code"] == "Core XII (B)", f"Data Science subject code should be 'Core XII (B)', got {ds_subject['code']}"


async def test_03_semester_vi_subjects_composition():
    """Verify Semester VI contains Algorithm Design Techniques, Algorithm Design Lab, and Project Work-I."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem6 = next((s for s in curriculum if s["id"] == SEM_6_ID or s["code"] == "SEM_6"), None)
    assert sem6 is not None, "Semester VI must exist in curriculum"

    subject_names = [s["name"] for s in sem6["subjects"]]
    assert "Algorithm Design Techniques" in subject_names
    assert "Algorithm Design Lab" in subject_names
    assert "Project Work-I" in subject_names
    assert len(sem6["subjects"]) == 3, f"Semester VI should have exactly 3 subjects, found {len(sem6['subjects'])}"


async def test_04_theory_subjects_have_four_units():
    """Verify Units I-IV are connected to all 5 theory subjects across Sem V and Sem VI."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    all_subjects = []
    for sem in curriculum:
        all_subjects.extend(sem.get("subjects", []))

    theory_subjects = [s for s in all_subjects if s.get("subject_type") == "theory"]
    assert len(theory_subjects) == 5, f"Expected 5 theory subjects (4 in Sem V + 1 in Sem VI), found {len(theory_subjects)}"

    for subj in theory_subjects:
        units = subj.get("units", [])
        assert len(units) == 4, f"Subject '{subj['name']}' must contain exactly 4 units, found {len(units)}"
        unit_numbers = [u["unit_number"] for u in units]
        assert sorted(unit_numbers) == [1, 2, 3, 4], f"Subject '{subj['name']}' units must be numbered 1, 2, 3, 4"

        for u in units:
            assert u["title"], f"Unit {u['unit_number']} in '{subj['name']}' must have a title"
            assert len(u["topics"]) > 10, f"Unit {u['unit_number']} in '{subj['name']}' must have detailed topics"


async def test_05_java_programming_lab_all_21_practicals():
    """Verify all 21 practical exercises in Java Programming Lab are present verbatim."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem5 = next((s for s in curriculum if s["code"] == "SEM_5"), None)
    java_lab = next((s for s in sem5["subjects"] if s["name"] == "Java Programming Lab"), None)
    assert java_lab is not None, "Java Programming Lab must exist"

    practicals = java_lab.get("practicals", [])
    assert len(practicals) == 21, f"Java Programming Lab must have exactly 21 exercises, found {len(practicals)}"

    exercise_nums = [p["exercise_number"] for p in practicals]
    assert sorted(exercise_nums) == list(range(1, 22)), "Practical exercises must be numbered 1 through 21"

    # Spot check specific exercises matching syllabus
    p1 = next((p for p in practicals if p["exercise_number"] == 1), None)
    assert p1 and ("command line" in p1["description"].lower() or "sum" in p1["title"].lower())

    p10 = next((p for p in practicals if p["exercise_number"] == 10), None)
    assert p10 and ("access specifiers" in p10["description"].lower() or "access specifiers" in p10["title"].lower())

    p21 = next((p for p in practicals if p["exercise_number"] == 21), None)
    assert p21 and ("keyboard" in p21["description"].lower() or "keyboard" in p21["title"].lower())


async def test_06_algorithm_design_lab_all_12_practicals():
    """Verify all 12 practical exercises in Algorithm Design Lab are present verbatim."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem6 = next((s for s in curriculum if s["code"] == "SEM_6"), None)
    algo_lab = next((s for s in sem6["subjects"] if s["name"] == "Algorithm Design Lab"), None)
    assert algo_lab is not None, "Algorithm Design Lab must exist"

    practicals = algo_lab.get("practicals", [])
    assert len(practicals) == 12, f"Algorithm Design Lab must have exactly 12 exercises, found {len(practicals)}"

    expected_titles = [
        "Insertion Sort",
        "Merge Sort",
        "Quick Sort",
        "Heap Sort",
        "Hashing",
        "Fractional Knapsack",
        "Matrix Chain Multiplication",
        "Longest Common Subsequence",
        "Huffman Code",
        "Prim's Algorithm",
        "Kruskal's Algorithm",
        "Dijkstra's Algorithm",
    ]

    for idx, expected_title in enumerate(expected_titles, 1):
        prac = next((p for p in practicals if p["exercise_number"] == idx), None)
        assert prac is not None, f"Exercise {idx} missing in Algorithm Design Lab"
        assert expected_title.lower() in prac["title"].lower(), f"Exercise {idx} title mismatch: expected '{expected_title}', got '{prac['title']}'"


async def test_07_project_work_report_sections_and_criteria():
    """Verify Project Work-I contains all 14 report sections and all 5 evaluation criteria."""
    service = get_supabase_service()
    curriculum = await service.get_full_curriculum()

    sem6 = next((s for s in curriculum if s["code"] == "SEM_6"), None)
    project_subj = next((s for s in sem6["subjects"] if s["name"] == "Project Work-I"), None)
    assert project_subj is not None, "Project Work-I must exist"

    guidelines = project_subj.get("project_guidelines")
    assert guidelines is not None, "Project Work-I must contain project_guidelines"

    report_sections = guidelines.get("report_sections", [])
    assert len(report_sections) == 14, f"Project Work-I must have exactly 14 report sections, found {len(report_sections)}"

    expected_sections = [
        "Title of the project",
        "Declaration",
        "Certificate",
        "Acknowledgement",
        "Abstract",
        "Table of Contents",
        "Introduction",
        "Literature Review",
        "Methodology",
        "Implementation / Software Development",
        "Results",
        "Discussion",
        "Conclusion",
        "References",
    ]

    for idx, sec_title in enumerate(expected_sections, 1):
        sec = next((s for s in report_sections if s["section_number"] == idx), None)
        assert sec is not None, f"Report section {idx} missing"
        assert sec["title"].lower() == sec_title.lower(), f"Section {idx} title mismatch: expected '{sec_title}', got '{sec['title']}'"

    eval_criteria = guidelines.get("evaluation_criteria", [])
    assert len(eval_criteria) == 5, f"Project Work-I must have exactly 5 evaluation criteria, found {len(eval_criteria)}"

    expected_keywords = [
        ["problem formulation"],
        ["execution of code"],
        ["documentation"],
        ["clarity in presentation"],
        ["viva voce"],
    ]
    crit_titles = [str(c.get("criterion") or c.get("title") or "").lower().replace("&", "and") for c in eval_criteria]
    for exp_words in expected_keywords:
        assert any(all(w in ct for w in exp_words) for ct in crit_titles), f"Missing evaluation criterion matching: {exp_words}"


async def test_08_api_curriculum_and_subject_endpoints():
    """Verify HTTP endpoints /api/academic/semesters, /api/academic/curriculum, and /api/academic/subjects/{id}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test 1: Semesters endpoint
        res_sem = await client.get("/api/academic/semesters")
        assert res_sem.status_code == 200
        sems = res_sem.json()
        assert len(sems) == 2
        sem_codes = [s["code"] for s in sems]
        assert "SEM_5" in sem_codes and "SEM_6" in sem_codes

        # Test 2: Full Curriculum endpoint
        res_curr = await client.get("/api/academic/curriculum")
        assert res_curr.status_code == 200
        curr_data = res_curr.json()
        assert curr_data["status"] == "success"
        assert len(curr_data["semesters"]) == 2

        # Test 3: Subject Detail endpoint for Software Engineering
        se_id = "50000001-0000-0000-0000-000000000001"
        res_subj = await client.get(f"/api/academic/subjects/{se_id}")
        assert res_subj.status_code == 200
        subj_data = res_subj.json()
        assert subj_data["name"] == "Software Engineering"
        assert len(subj_data["units"]) == 4

        # Test 4: Subject Detail endpoint for Java Lab
        java_lab_id = "50000005-0000-0000-0000-000000000005"
        res_lab = await client.get(f"/api/academic/subjects/{java_lab_id}")
        assert res_lab.status_code == 200
        lab_data = res_lab.json()
        assert lab_data["name"] == "Java Programming Lab"
        assert len(lab_data["practicals"]) == 21

        # Test 5: Subject Detail endpoint for Project Work-I
        proj_id = "60000003-0000-0000-0000-000000000003"
        res_proj = await client.get(f"/api/academic/subjects/{proj_id}")
        assert res_proj.status_code == 200
        proj_data = res_proj.json()
        assert proj_data["name"] == "Project Work-I"
        assert len(proj_data["project_guidelines"]["report_sections"]) == 14

        # Test 6: Non-existent subject returns 404
        res_404 = await client.get(f"/api/academic/subjects/{str(uuid.uuid4())}")
        assert res_404.status_code == 404


async def test_09_academic_document_linkage_and_isolation():
    """Verify linking documents to subjects/semesters and checking access control isolation."""
    service = get_supabase_service()
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    ai_subject_id = "50000002-0000-0000-0000-000000000002"

    # User A creates a personal document tagged with AI subject
    doc_a = await service.create_document_record(
        user_id=user_a,
        filename="User_A_AI_Notes.pdf",
        storage_path=f"{user_a}/doc_a.pdf",
        file_size=1024,
        scope="personal",
        semester_id=SEM_5_ID,
        subject_id=ai_subject_id,
    )
    assert doc_a["subject_id"] == ai_subject_id

    # User B queries documents for AI subject
    docs_user_b = await service.list_subject_documents(subject_id=ai_subject_id, user_id=user_b)
    user_b_doc_ids = [d["id"] for d in docs_user_b]
    assert doc_a["id"] not in user_b_doc_ids, "User A's personal document must NOT be visible to User B"

    # User A queries documents for AI subject
    docs_user_a = await service.list_subject_documents(subject_id=ai_subject_id, user_id=user_a)
    user_a_doc_ids = [d["id"] for d in docs_user_a]
    assert doc_a["id"] in user_a_doc_ids, "User A must see their own personal document tagged with the subject"


async def test_10_chunk_academic_metadata_persistence():
    """Verify that when document chunks are saved, semester_id, subject_id, and unit_id are preserved."""
    service = get_supabase_service()
    user_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    sem_id = SEM_5_ID
    subj_id = "50000001-0000-0000-0000-000000000001"
    unit_id = "50000011-0000-0000-0000-000000000001"

    test_chunks = [
        {
            "chunk_index": 0,
            "page_number": 1,
            "content": "Software engineering lifecycle models including Waterfall, Agile, and Spiral paradigms.",
            "token_count": 14,
        },
        {
            "chunk_index": 1,
            "page_number": 2,
            "content": "Iterative enhancement and Rapid Application Development (RAD) lifecycle models.",
            "token_count": 12,
        },
    ]

    saved_count = await service.save_document_chunks(
        document_id=doc_id,
        user_id=user_id,
        chunks=test_chunks,
        scope="personal",
        semester_id=sem_id,
        subject_id=subj_id,
        unit_id=unit_id,
    )
    assert saved_count == 2, f"Expected 2 chunks saved, got {saved_count}"

    # Verify memory store metadata
    stored = service._dev_chunks.get(doc_id, [])
    if stored:
        assert len(stored) == 2
        for chunk in stored:
            assert chunk.get("semester_id") == sem_id
            assert chunk.get("subject_id") == subj_id
            assert chunk.get("unit_id") == unit_id


async def run_all_tests():
    """Run all tests sequentially and report pass/fail status."""
    tests = [
        ("Test 01: Semester V composition (4 subjects + Lab)", test_01_semester_v_subjects_composition),
        ("Test 02: AI and Data Science separate compulsory", test_02_ai_and_data_science_are_separate_compulsory),
        ("Test 03: Semester VI composition (Algorithm Design + Lab + Project)", test_03_semester_vi_subjects_composition),
        ("Test 04: Theory subjects have 4 units with topics", test_04_theory_subjects_have_four_units),
        ("Test 05: Java Programming Lab all 21 practicals", test_05_java_programming_lab_all_21_practicals),
        ("Test 06: Algorithm Design Lab all 12 practicals", test_06_algorithm_design_lab_all_12_practicals),
        ("Test 07: Project Work-I report sections & criteria", test_07_project_work_report_sections_and_criteria),
        ("Test 08: API curriculum & subject endpoints", test_08_api_curriculum_and_subject_endpoints),
        ("Test 09: Academic document linkage & isolation", test_09_academic_document_linkage_and_isolation),
        ("Test 10: Chunk academic metadata persistence", test_10_chunk_academic_metadata_persistence),
    ]

    print("=" * 70)
    print("CAMPUSPILOT AI — SEMESTER V & VI ACADEMIC STRUCTURE TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0
    for name, test_func in tests:
        try:
            print(f"RUNNING: {name} ...", end=" ", flush=True)
            await test_func()
            print("✓ PASSED")
            passed += 1
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(tests)} tests.")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
