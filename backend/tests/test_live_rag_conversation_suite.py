"""
CampusPilot AI — Phase 3.5.3: Live RAG Integration & Safe Credit Handling Test Suite.

Covers all 14 required test scenarios:
1. Relevant PDF question retrieves context.
2. No relevant documents produces a clean general-knowledge response.
3. Private document isolation.
4. Shared document retrieval.
5. Fabricated citations are rejected.
6. Gemini success deducts exactly one credit.
7. Gemini failure deducts zero credits.
8. Paid subscriber deducts zero free credits.
9. Insufficient balance preserves 402 behavior.
10. Conversation history remains clean.
11. Existing conversations still work.
12. Duplicate/retry behavior does not double-charge.
13. Retrieval failure is handled explicitly.
14. Existing upload and embedding regression tests still pass.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.routes.conversations import send_conversation_message
from app.core.auth import AuthenticatedUser
from app.schemas.chat import ChatMessage, ChatResponse, Role
from app.schemas.conversation import MessageCreate
from app.schemas.rag import RAGCitation, RAGContext
from app.services.idempotency import AcquireOutcome, IdempotencyService, IdempotencyStatus
from app.services.rag import RAGRetrievalError, RAGService


class TestLiveRAGConversationSuite(unittest.IsolatedAsyncioTestCase):
    """Test suite covering all 14 scenarios for live RAG and safe credit handling."""

    def setUp(self):
        self.user = AuthenticatedUser(
            user_id="user-uuid-1111",
            email="student@university.edu",
        )
        self.conv_id = "conv-uuid-aaaa"

        self.mock_supabase = MagicMock()
        self.mock_gemini = MagicMock()
        self.mock_rag = MagicMock()
        self.mock_title = MagicMock()

        # Default mock setup
        self.mock_supabase.get_conversation = AsyncMock(
            return_value={
                "id": self.conv_id,
                "user_id": self.user.user_id,
                "title": "New Academic Conversation",
                "messages": [],
            }
        )
        self.mock_supabase.get_user_subscription = AsyncMock(return_value={"is_paid": False})
        self.mock_supabase.get_user_credits = AsyncMock(return_value=20)
        self.mock_supabase.deduct_credit_atomic = AsyncMock(return_value=19)
        self.mock_supabase.add_message = AsyncMock(
            side_effect=lambda conversation_id, role, content: {
                "id": f"msg-{role}-{DateMock.now_str()}",
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": "2026-11-01T12:00:00Z",
            }
        )
        self.mock_supabase.find_document_by_name = AsyncMock(return_value=None)
        self.mock_supabase.get_conversation_documents = AsyncMock(return_value=[])
        self.mock_supabase.link_conversation_document = AsyncMock(return_value=True)
        self.mock_supabase.rename_conversation = AsyncMock(return_value=True)

        async def _mock_save_turn(
            user_id,
            conversation_id,
            user_content,
            assistant_content,
            is_paid=False,
            idempotency_key=None,
            owner_token=None,
            response_data=None,
            **kw,
        ):
            rem = None
            if not is_paid:
                rem = await self.mock_supabase.deduct_credit_atomic(
                    user_id=user_id,
                    action="ai_message",
                    description=f"AI query in conversation {conversation_id}",
                )
            u_msg = {
                "id": f"msg-user-{DateMock.now_str()}",
                "conversation_id": conversation_id,
                "role": "user",
                "content": user_content,
                "created_at": "2026-11-01T12:00:00Z",
            }
            a_msg = {
                "id": f"msg-model-{DateMock.now_str()}",
                "conversation_id": conversation_id,
                "role": "model",
                "content": assistant_content,
                "created_at": "2026-11-01T12:00:01Z",
            }
            return {
                "user_message": u_msg,
                "assistant_message": a_msg,
                "remaining_credits": rem,
            }

        self.mock_supabase.save_conversation_turn_atomic = AsyncMock(side_effect=_mock_save_turn)
        self.mock_title.generate_title = AsyncMock(return_value="Study: Neural Networks")
        self.mock_rag.retrieve_context = AsyncMock(
            return_value=RAGContext(
                query="default query",
                augmented_prompt="default prompt",
                context_text="",
                citations=[],
                source_lookup={},
                total_sources=0,
                has_relevant_context=False,
            )
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query="", history=None, rag_context=None, **kw: MagicMock(
                message=raw_query, history=history or []
            )
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value="Default assistant response"
        )

    # --------------------------------------------------------------------------
    # Scenario 1: Relevant PDF question retrieves context
    # --------------------------------------------------------------------------
    async def test_01_relevant_pdf_question_retrieves_context(self):
        payload = MessageCreate(content="Explain Drew Conway Venn Diagram in Data Science.")

        citation = RAGCitation(
            source_id="S1",
            document_id="doc-ds-1",
            filename="Data Science-New (Unit-I).pdf",
            page_number=1,
            similarity_score=0.82,
            chunk_id="chunk-1",
            scope="personal",
        )
        rag_ctx = RAGContext(
            query=payload.content,
            augmented_prompt="=== VERIFIED COURSE STUDY MATERIAL ===\n[Source S1: Data Science-New (Unit-I).pdf, Page 1]\n...",
            context_text="...",
            citations=[citation],
            source_lookup={"S1": citation},
            total_sources=1,
            has_relevant_context=True,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(
                message=rag_context.augmented_prompt, history=history
            )
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(
                reply="According to [S1], Drew Conway's Venn Diagram comprises hacking skills, math knowledge, and substantive expertise.",
                model="gemini-3.5-flash-lite",
            )
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[citation])
        self.mock_rag.format_citation_metadata = MagicMock(
            return_value=[
                {
                    "source_id": "S1",
                    "filename": "Data Science-New (Unit-I).pdf",
                    "page_number": 1,
                    "similarity_score": 0.82,
                }
            ]
        )

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        self.assertIn("Drew Conway", res.assistant_message.content)
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0]["source_id"], "S1")
        self.assertEqual(res.citations[0]["filename"], "Data Science-New (Unit-I).pdf")
        self.assertEqual(res.remaining_credits, 19)
        self.mock_supabase.deduct_credit_atomic.assert_awaited_once()

    # --------------------------------------------------------------------------
    # Scenario 2: No relevant documents produces a clean general-knowledge response
    # --------------------------------------------------------------------------
    async def test_02_no_relevant_documents_general_knowledge(self):
        payload = MessageCreate(content="What is Quicksort time complexity?")

        rag_ctx = RAGContext(
            query=payload.content,
            augmented_prompt=payload.content,
            context_text="",
            citations=[],
            source_lookup={},
            total_sources=0,
            has_relevant_context=False,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(
                message=raw_query, history=history
            )
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(
                reply="Quicksort has an average time complexity of O(n log n) and worst-case of O(n^2).",
                model="gemini-3.5-flash-lite",
            )
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.format_citation_metadata = MagicMock(return_value=[])

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        self.assertIn("O(n log n)", res.assistant_message.content)
        self.assertEqual(res.citations, [])
        self.assertEqual(res.remaining_credits, 19)

    # --------------------------------------------------------------------------
    # Scenario 3: Private document isolation
    # --------------------------------------------------------------------------
    async def test_03_private_document_isolation(self):
        payload = MessageCreate(content="[Referencing uploaded PDF: OtherUserSecret.pdf] Tell me secrets.")

        self.mock_supabase.find_document_by_name = AsyncMock(
            return_value={"id": "doc-alien", "filename": "OtherUserSecret.pdf"}
        )
        self.mock_rag.retrieve_context = AsyncMock(
            side_effect=PermissionError("Access denied: document doc-alien not accessible by user-uuid-1111")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 403)
        self.mock_gemini.generate_response.assert_not_called()
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 4: Shared document retrieval
    # --------------------------------------------------------------------------
    async def test_04_shared_document_retrieval(self):
        payload = MessageCreate(content="What are the compulsory subjects in BCA Semester 5?")

        shared_citation = RAGCitation(
            source_id="S1",
            document_id="doc-bca-syllabus",
            filename="BCA.pdf",
            page_number=14,
            similarity_score=0.88,
            scope="shared",
        )
        rag_ctx = RAGContext(
            query=payload.content,
            augmented_prompt="=== VERIFIED COURSE STUDY MATERIAL ===\n[Source S1: BCA.pdf, Page 14]\n...",
            context_text="...",
            citations=[shared_citation],
            source_lookup={"S1": shared_citation},
            total_sources=1,
            has_relevant_context=True,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(
                message=rag_context.augmented_prompt, history=history
            )
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(
                reply="According to [S1], Semester 5 includes Introduction to AI and Introduction to Data Science.",
                model="gemini-3.5-flash-lite",
            )
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[shared_citation])
        self.mock_rag.format_citation_metadata = MagicMock(
            return_value=[
                {
                    "source_id": "S1",
                    "filename": "BCA.pdf",
                    "page_number": 14,
                    "similarity_score": 0.88,
                    "scope": "shared",
                }
            ]
        )

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        self.assertEqual(res.citations[0]["scope"], "shared")
        self.assertEqual(res.citations[0]["filename"], "BCA.pdf")

    # --------------------------------------------------------------------------
    # Scenario 5: Fabricated citations are rejected
    # --------------------------------------------------------------------------
    async def test_05_fabricated_citations_are_rejected(self):
        payload = MessageCreate(content="Tell me about algorithms.")

        citation_s1 = RAGCitation(
            source_id="S1",
            document_id="d1",
            filename="Algorithms.pdf",
            page_number=5,
            similarity_score=0.80,
        )
        rag_ctx = RAGContext(
            query=payload.content,
            augmented_prompt="...",
            context_text="...",
            citations=[citation_s1],
            source_lookup={"S1": citation_s1},
            total_sources=1,
            has_relevant_context=True,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(
                message=raw_query, history=history
            )
        )
        # Model hallucinates [S99] and [S42]
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(
                reply="According to [S1] and [S99] and [S42], algorithms require finite steps.",
                model="gemini-3.5-flash-lite",
            )
        )
        # Real extract_citations logic rejects S99 and S42
        from app.services.rag import RAGService
        real_rag = RAGService()
        self.mock_rag.extract_citations = MagicMock(
            side_effect=lambda reply_text, source_lookup: real_rag.extract_citations(reply_text, source_lookup)
        )
        self.mock_rag.format_citation_metadata = MagicMock(
            side_effect=lambda cits: real_rag.format_citation_metadata(cits)
        )

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        # Only S1 is in the citations; fabricated S99 and S42 are rejected
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0]["source_id"], "S1")

    # --------------------------------------------------------------------------
    # Scenario 6: Gemini success deducts exactly one credit
    # --------------------------------------------------------------------------
    async def test_06_gemini_success_deducts_exactly_one_credit(self):
        payload = MessageCreate(content="Hello")
        rag_ctx = RAGContext(
            query="Hello", augmented_prompt="Hello", citations=[], source_lookup={}, has_relevant_context=False
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(message=raw_query, history=history)
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(reply="Hi there!", model="gemini-3.5-flash-lite")
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.format_citation_metadata = MagicMock(return_value=[])

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        self.mock_supabase.deduct_credit_atomic.assert_awaited_once_with(
            user_id=self.user.user_id,
            action="ai_message",
            description=f"AI query in conversation {self.conv_id}",
        )
        self.assertEqual(res.remaining_credits, 19)

    # --------------------------------------------------------------------------
    # Scenario 7: Gemini failure deducts zero credits
    # --------------------------------------------------------------------------
    async def test_07_gemini_failure_deducts_zero_credits(self):
        payload = MessageCreate(content="Failing query")
        rag_ctx = RAGContext(
            query="Failing query", augmented_prompt="...", citations=[], source_lookup={}, has_relevant_context=False
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(message=raw_query, history=history)
        )
        # Gemini fails with 503 Overload
        self.mock_gemini.generate_response = AsyncMock(
            side_effect=RuntimeError("Google Gemini API 503 Service Overloaded")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 502)
        # Credit was NOT deducted!
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 8: Paid subscriber deducts zero free credits
    # --------------------------------------------------------------------------
    async def test_08_paid_subscriber_deducts_zero_free_credits(self):
        # Set subscription to paid
        self.mock_supabase.get_user_subscription = AsyncMock(return_value={"is_paid": True})

        payload = MessageCreate(content="Subscriber query")
        rag_ctx = RAGContext(
            query="q", augmented_prompt="q", citations=[], source_lookup={}, has_relevant_context=False
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(message=raw_query, history=history)
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(reply="Subscriber answer", model="gemini-3.5-flash-lite")
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.format_citation_metadata = MagicMock(return_value=[])

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        # 0 credit deductions for paid subscriber
        self.mock_supabase.deduct_credit_atomic.assert_not_called()
        self.assertTrue(res.is_paid)
        self.assertIsNone(res.remaining_credits)

    # --------------------------------------------------------------------------
    # Scenario 9: Insufficient balance preserves 402 behavior
    # --------------------------------------------------------------------------
    async def test_09_insufficient_balance_returns_402(self):
        self.mock_supabase.get_user_credits = AsyncMock(return_value=0)

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="I want an answer but have 0 credits"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 402)
        self.assertIn("Free trial credits exhausted", cm.exception.detail)
        self.mock_rag.retrieve_context.assert_not_called()
        self.mock_gemini.generate_response.assert_not_called()
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 10: Conversation history remains clean
    # --------------------------------------------------------------------------
    async def test_10_conversation_history_remains_clean(self):
        raw_student_text = "What is CPU pipelining?"
        payload = MessageCreate(content=raw_student_text)

        rag_ctx = RAGContext(
            query=raw_student_text,
            augmented_prompt="=== VERIFIED COURSE STUDY MATERIAL ===\n[Source S1: COA.pdf]\n...\nStudent Question:\nWhat is CPU pipelining?",
            citations=[],
            source_lookup={},
            has_relevant_context=True,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)
        self.mock_rag.prepare_chat_request = MagicMock(
            side_effect=lambda raw_query, history, rag_context: MagicMock(
                message=rag_context.augmented_prompt, history=history
            )
        )
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(reply="Pipelining overlaps instruction execution stages.", model="gemini-3.5-flash-lite")
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.format_citation_metadata = MagicMock(return_value=[])

        await send_conversation_message(
            conversation_id=self.conv_id,
            payload=payload,
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        # Check what was saved in the database:
        # save_conversation_turn_atomic must receive clean raw_student_text
        saved_call = self.mock_supabase.save_conversation_turn_atomic.await_args.kwargs
        self.assertEqual(saved_call["user_content"], raw_student_text)
        # The database message does NOT contain the injected material!
        self.assertNotIn("=== VERIFIED COURSE STUDY MATERIAL ===", saved_call["user_content"])

    # --------------------------------------------------------------------------
    # Scenario 11: Existing multi-turn conversations still work
    # --------------------------------------------------------------------------
    async def test_11_existing_multi_turn_conversations_work(self):
        # Conversation already has 2 turns
        self.mock_supabase.get_conversation = AsyncMock(
            return_value={
                "id": self.conv_id,
                "user_id": self.user.user_id,
                "title": "Study Session",
                "messages": [
                    {"role": "user", "content": "Turn 1 question"},
                    {"role": "model", "content": "Turn 1 answer"},
                ],
            }
        )

        rag_ctx = RAGContext(
            query="Turn 2 question",
            augmented_prompt="Turn 2 question",
            citations=[],
            source_lookup={},
            has_relevant_context=False,
        )
        self.mock_rag.retrieve_context = AsyncMock(return_value=rag_ctx)

        captured_history = []
        def capture_prep(raw_query, history, rag_context):
            nonlocal captured_history
            captured_history = list(history)
            return MagicMock(message=raw_query, history=history)

        self.mock_rag.prepare_chat_request = MagicMock(side_effect=capture_prep)
        self.mock_gemini.generate_response = AsyncMock(
            return_value=ChatResponse(reply="Turn 2 answer", model="gemini-3.5-flash-lite")
        )
        self.mock_rag.extract_citations = MagicMock(return_value=[])
        self.mock_rag.format_citation_metadata = MagicMock(return_value=[])

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=MessageCreate(content="Turn 2 question"),
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        self.assertEqual(len(captured_history), 2)
        self.assertEqual(captured_history[0].content, "Turn 1 question")
        self.assertEqual(captured_history[1].content, "Turn 1 answer")
        self.assertEqual(res.assistant_message.content, "Turn 2 answer")

    # --------------------------------------------------------------------------
    # Scenario 12: Duplicate/retry behavior does not double-charge
    # --------------------------------------------------------------------------
    async def test_12_duplicate_retry_does_not_double_charge(self):
        # Conversation already has the identical user message answered 2 seconds ago
        now_iso = datetime.now(timezone.utc).isoformat()
        self.mock_supabase.get_conversation = AsyncMock(
            return_value={
                "id": self.conv_id,
                "user_id": self.user.user_id,
                "title": "Study Session",
                "messages": [
                    {
                        "id": "m1",
                        "conversation_id": self.conv_id,
                        "role": "user",
                        "content": "What is Python?",
                        "created_at": now_iso,
                    },
                    {
                        "id": "m2",
                        "conversation_id": self.conv_id,
                        "role": "model",
                        "content": "Python is a programming language.",
                        "created_at": now_iso,
                    },
                ],
            }
        )

        res = await send_conversation_message(
            conversation_id=self.conv_id,
            payload=MessageCreate(content="What is Python?"),
            user=self.user,
            supabase_service=self.mock_supabase,
            gemini_service=self.mock_gemini,
            rag_service=self.mock_rag,
            title_service=self.mock_title,
        )

        # Returns cached turn
        self.assertEqual(res.assistant_message.content, "Python is a programming language.")
        # Zero credit deductions
        self.mock_supabase.deduct_credit_atomic.assert_not_called()
        self.mock_gemini.generate_response.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 13: Retrieval failure is handled explicitly
    # --------------------------------------------------------------------------
    async def test_13_retrieval_failure_handled_explicitly(self):
        self.mock_rag.retrieve_context = AsyncMock(
            side_effect=RAGRetrievalError("Supabase pgvector connection timed out")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Query when vector DB is down"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 503)
        self.assertIn("Document retrieval service is temporarily unavailable", cm.exception.detail)
        self.mock_gemini.generate_response.assert_not_called()
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 14: Existing upload and embedding regression verification
    # --------------------------------------------------------------------------
    def test_14_existing_upload_and_embedding_regression(self):
        # Verify that existing embedding and persistence services remain intact
        from app.services.embedding import EmbeddingService, get_embedding_service
        from app.services.embedding_persistence import EmbeddingPersistenceService, get_embedding_persistence_service
        from app.services.semantic_search import SemanticSearchService, get_semantic_search_service

        emb_svc = get_embedding_service()
        self.assertIsInstance(emb_svc, EmbeddingService)
        persist_svc = get_embedding_persistence_service()
        self.assertIsInstance(persist_svc, EmbeddingPersistenceService)
        search_svc = get_semantic_search_service()
        self.assertIsInstance(search_svc, SemanticSearchService)

    # --------------------------------------------------------------------------
    # Scenario 15: Idempotency - Same key and same payload returns original result
    # --------------------------------------------------------------------------
    async def test_15_idempotency_same_key_same_payload_returns_cached_result(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            idem_svc = IdempotencyService(sqlite_db_path=tf.name)
            key = "test-key-uuid-15"
            payload = MessageCreate(content="What is an API gateway?")

            # 1. First execution
            res1 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                idempotency_key=key,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=idem_svc,
            )

            # 2. Duplicate retry with same key and same payload
            res2 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                idempotency_key=key,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=idem_svc,
            )

            # Assert: Gemini only called once, credit deducted only once
            self.mock_gemini.generate_response.assert_awaited_once()
            self.mock_supabase.deduct_credit_atomic.assert_awaited_once()
            self.assertEqual(res1.assistant_message.content, res2.assistant_message.content)
            self.assertEqual(res1.user_message.id, res2.user_message.id)

    # --------------------------------------------------------------------------
    # Scenario 16: Idempotency - Same key with different payload returns HTTP 409
    # --------------------------------------------------------------------------
    async def test_16_idempotency_same_key_different_payload_returns_409(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            idem_svc = IdempotencyService(sqlite_db_path=tf.name)
            key = "test-key-uuid-16"

            # 1. First call
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Original question"),
                idempotency_key=key,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=idem_svc,
            )

            # 2. Second call with SAME key but DIFFERENT payload
            with self.assertRaises(HTTPException) as cm:
                await send_conversation_message(
                    conversation_id=self.conv_id,
                    payload=MessageCreate(content="Tampered / completely different question"),
                    idempotency_key=key,
                    user=self.user,
                    supabase_service=self.mock_supabase,
                    gemini_service=self.mock_gemini,
                    rag_service=self.mock_rag,
                    title_service=self.mock_title,
                    idempotency_service=idem_svc,
                )

            self.assertEqual(cm.exception.status_code, 409)
            self.assertIn("Idempotency-Key was already used with a different request payload", cm.exception.detail)

    # --------------------------------------------------------------------------
    # Scenario 17: Idempotency - Concurrent duplicate requests execute only once
    # --------------------------------------------------------------------------
    async def test_17_idempotency_concurrent_duplicate_requests_execute_once(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            idem_svc = IdempotencyService(sqlite_db_path=tf.name)
            key = "test-key-uuid-17"

            # Acquire lock simulating in-flight request
            outcome, _, _ = await idem_svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key=key,
                content="Concurrent query test",
            )
            self.assertEqual(outcome, AcquireOutcome.ACQUIRED)

            # Attempt concurrent execution with same key
            with self.assertRaises(HTTPException) as cm:
                await send_conversation_message(
                    conversation_id=self.conv_id,
                    payload=MessageCreate(content="Concurrent query test"),
                    idempotency_key=key,
                    user=self.user,
                    supabase_service=self.mock_supabase,
                    gemini_service=self.mock_gemini,
                    rag_service=self.mock_rag,
                    title_service=self.mock_title,
                    idempotency_service=idem_svc,
                )

            self.assertEqual(cm.exception.status_code, 409)
            self.assertIn("currently being processed", cm.exception.detail)
            # Gemini not called
            self.mock_gemini.generate_response.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 18: Idempotency - Process restart does not erase state
    # --------------------------------------------------------------------------
    async def test_18_idempotency_process_restart_preserves_state(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            # Process 1 executes and completes request
            proc1_idem = IdempotencyService(sqlite_db_path=tf.name)
            key = "test-key-uuid-18"
            payload = MessageCreate(content="Explain TCP 3-way handshake.")

            res1 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                idempotency_key=key,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=proc1_idem,
            )

            # Process 2 starts fresh (simulating worker restart / new container)
            proc2_idem = IdempotencyService(sqlite_db_path=tf.name)
            res2 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=payload,
                idempotency_key=key,
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=proc2_idem,
            )

            # Preserved across process boundary: zero second execution
            self.mock_gemini.generate_response.assert_awaited_once()
            self.assertEqual(res1.assistant_message.content, res2.assistant_message.content)

    # --------------------------------------------------------------------------
    # Scenario 19: Idempotency - Stale processing record is recovered safely
    # --------------------------------------------------------------------------
    async def test_19_idempotency_stale_processing_record_recovered(self):
        with tempfile.NamedTemporaryFile(suffix=".db") as tf:
            idem_svc = IdempotencyService(sqlite_db_path=tf.name, stale_timeout_seconds=1)
            key = "test-key-uuid-19"
            payload = MessageCreate(content="Recoverable query")

            # Acquire lock
            outcome1, _, _ = await idem_svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key=key,
                content=payload.content,
            )
            self.assertEqual(outcome1, AcquireOutcome.ACQUIRED)

            # Simulate worker dying mid-flight and waiting 1.1s for stale timeout
            await asyncio.sleep(1.1)

            # Next request attempts to run
            outcome2, _, _ = await idem_svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key=key,
                content=payload.content,
            )
            self.assertEqual(outcome2, AcquireOutcome.RECOVERED)

    # --------------------------------------------------------------------------
    # Scenario 20: Credits - Gemini failure persists zero messages
    # --------------------------------------------------------------------------
    async def test_20_gemini_failure_persists_zero_messages(self):
        self.mock_gemini.generate_response = AsyncMock(
            side_effect=RuntimeError("Google Gemini API 500 Internal Server Error")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Question when Gemini crashes"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 502)
        # CRITICAL: Neither user nor model message was saved!
        self.mock_supabase.save_conversation_turn_atomic.assert_not_called()
        self.mock_supabase.add_message.assert_not_called()
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 21: Credits - Persistence failure raises 500 without losing credits
    # --------------------------------------------------------------------------
    async def test_21_persistence_failure_triggers_compensating_refund_safety(self):
        self.mock_supabase.save_conversation_turn_atomic = AsyncMock(
            side_effect=RuntimeError("PostgreSQL connection lost during insert")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Question when persistence fails"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 500)
        self.assertIn("No credits were lost", cm.exception.detail)

    # --------------------------------------------------------------------------
    # Scenario 22: Credits - Concurrent requests cannot overspend balance
    # --------------------------------------------------------------------------
    async def test_22_concurrent_requests_cannot_overspend_balance(self):
        # Initial check passes (student has 1 credit)
        self.mock_supabase.get_user_credits = AsyncMock(return_value=1)
        # But during turn persistence, atomic deduction rejects with ValueError (balance <= 0)
        self.mock_supabase.save_conversation_turn_atomic = AsyncMock(
            side_effect=ValueError("Insufficient credits. Balance is 0.")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Question when last credit was taken concurrently"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 402)
        self.assertIn("Free trial credits exhausted", cm.exception.detail)

    # --------------------------------------------------------------------------
    # Scenario 23: Citations - Prompt and parser agree on syntax variants and deduplicate
    # --------------------------------------------------------------------------
    def test_23_citation_syntax_variants_accepted_and_deduplicated(self):
        rag_service = RAGService()
        cit1 = RAGCitation(
            source_id="S1",
            document_id="doc-1",
            filename="OS_Concepts.pdf",
            page_number=42,
            similarity_score=0.89,
            chunk_id="chunk-1",
            scope="shared",
        )
        cit2 = RAGCitation(
            source_id="S2",
            document_id="doc-2",
            filename="Networks.pdf",
            page_number=10,
            similarity_score=0.78,
            chunk_id="chunk-2",
            scope="personal",
        )
        source_lookup = {"S1": cit1, "S2": cit2}

        # Model output includes [S1], [Source S1], [Source: S1], [S1, S2], [Source S1: OS_Concepts.pdf, Page 42], and fabricated [S99]
        ai_reply = (
            "According to [S1], virtualization allows resource sharing. "
            "Furthermore, as stated in [Source S1] and [Source: S1, S2], packets route through IP layers. "
            "See also [Source S1: OS_Concepts.pdf, Page 42]. "
            "Finally, an uncited claim mentions fabricated [S99]."
        )

        extracted = rag_service.extract_citations(ai_reply, source_lookup)

        # Assert: Only authentic S1 and S2 are present
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0].source_id, "S1")
        self.assertEqual(extracted[1].source_id, "S2")
        # Assert: S1 is deduplicated (only 1 entry in list, not 4!)
        s1_entries = [c for c in extracted if c.source_id == "S1"]
        self.assertEqual(len(s1_entries), 1)

    # --------------------------------------------------------------------------
    # Scenario 24: Citations - Missing metadata on chunk is handled safely
    # --------------------------------------------------------------------------
    async def test_24_missing_citation_metadata_handled_safely(self):
        # Document chunk without filename or page number
        chunk_missing = MagicMock(
            chunk_id="ch-missing",
            document_id="doc-missing",
            filename=None,
            page_number=0,
            similarity_score=0.75,
            chunk_index=0,
            scope="personal",
            content="Sample academic content with missing metadata",
        )
        self.mock_rag.search_service.search = AsyncMock(
            return_value=MagicMock(results=[chunk_missing])
        )

        rag_service = RAGService(
            search_service=self.mock_rag.search_service,
            gemini_service=self.mock_gemini,
            supabase_service=self.mock_supabase,
        )

        context = await rag_service.retrieve_context(
            user_id=self.user.user_id,
            query="Query about missing metadata chunk",
        )

        self.assertTrue(context.has_relevant_context)
        self.assertEqual(len(context.citations), 1)
        self.assertEqual(context.citations[0].filename, "academic_document.pdf")
        self.assertEqual(context.citations[0].page_number, 1)

    # --------------------------------------------------------------------------
    # Scenario 25: Citations - No retrieved context means zero citations
    # --------------------------------------------------------------------------
    def test_25_no_retrieved_context_produces_zero_citations(self):
        rag_service = RAGService()
        # Model hallucinates [S1] when no sources exist
        ai_reply = "According to [S1], general physics applies."
        extracted = rag_service.extract_citations(ai_reply, source_lookup={})
        self.assertEqual(extracted, [])

    # --------------------------------------------------------------------------
    # Scenario 26: Access Control - Cross-user document ID attack rejected
    # --------------------------------------------------------------------------
    async def test_26_cross_student_document_id_attack_rejected(self):
        # Student A passes Student B's private document ID
        victim_doc_id = "doc-victim-private-9999"
        self.mock_rag.retrieve_context = AsyncMock(
            side_effect=PermissionError(f"Access denied: document {victim_doc_id} not accessible by user {self.user.user_id}")
        )

        with self.assertRaises(HTTPException) as cm:
            await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content=f"[Referencing uploaded PDF: victim.pdf] summarize this"),
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
            )

        self.assertEqual(cm.exception.status_code, 403)
        self.assertIn("Access denied", cm.exception.detail)
        self.mock_gemini.generate_response.assert_not_called()
        self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 27: Access Control - Academic filters passed directly to retrieval
    # --------------------------------------------------------------------------
    async def test_27_academic_filters_passed_to_retrieval_service(self):
        mock_search = AsyncMock()
        mock_search.search = AsyncMock(return_value=MagicMock(results=[]))
        rag_service = RAGService(
            search_service=mock_search,
            gemini_service=self.mock_gemini,
            supabase_service=self.mock_supabase,
        )

        await rag_service.retrieve_context(
            user_id=self.user.user_id,
            query="What is normalization?",
            subject_id="subj-dbms-1",
            semester_id="sem-5",
            unit_id="unit-2",
        )

        # Assert: Academic filters were passed down to search_service.search for database-level execution
        mock_search.search.assert_awaited_once()
        _, kwargs = mock_search.search.await_args
        self.assertEqual(kwargs["subject_id"], "subj-dbms-1")
        self.assertEqual(kwargs["semester_id"], "sem-5")
        self.assertEqual(kwargs["unit_id"], "unit-2")

    # --------------------------------------------------------------------------
    # Scenario 28: Idempotency Lease - Renewal (Heartbeat) prevents early recovery
    # --------------------------------------------------------------------------
    async def test_28_idempotency_lease_renewal_extends_timeout(self):
        import tempfile
        import asyncio
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test.db")
            svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                stale_timeout_seconds=1,
                sqlite_db_path=db_file,
            )
            # Worker 1 acquires key
            outcome1, _, token1 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-heartbeat",
                content="Long running query",
            )
            self.assertEqual(outcome1, AcquireOutcome.ACQUIRED)
            self.assertIsNotNone(token1)

            # Worker 1 runs and issues heartbeat at t=0.6s
            await asyncio.sleep(0.6)
            renewed = await svc.renew_lease(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-heartbeat",
                owner_token=token1,
            )
            self.assertTrue(renewed)

            # Another 0.6s passes (total elapsed 1.2s > initial 1.0s timeout)
            await asyncio.sleep(0.6)

            # Worker 2 attempts acquire; must still be IN_PROGRESS because lease was renewed
            outcome2, _, _ = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-heartbeat",
                content="Long running query",
            )
            self.assertEqual(outcome2, AcquireOutcome.IN_PROGRESS)

    # --------------------------------------------------------------------------
    # Scenario 29: Idempotency Lease - Stale record recovered after timeout
    # --------------------------------------------------------------------------
    async def test_29_idempotency_recovery_after_stale_timeout(self):
        import tempfile
        import asyncio
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test.db")
            svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                stale_timeout_seconds=1,
                sqlite_db_path=db_file,
            )
            # Worker 1 acquires key but abandons it / crashes
            outcome1, _, token1 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-abandoned",
                content="Abandoned query",
            )
            self.assertEqual(outcome1, AcquireOutcome.ACQUIRED)

            # Wait past timeout
            await asyncio.sleep(1.1)

            # Worker 2 recovers the key safely with a new token
            outcome2, _, token2 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-abandoned",
                content="Abandoned query",
            )
            self.assertEqual(outcome2, AcquireOutcome.RECOVERED)
            self.assertNotEqual(token1, token2)

    # --------------------------------------------------------------------------
    # Scenario 30: Idempotency Fencing - Expired worker cannot complete request
    # --------------------------------------------------------------------------
    async def test_30_fencing_prevents_expired_worker_from_completing(self):
        import tempfile
        import asyncio
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test.db")
            svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                stale_timeout_seconds=1,
                sqlite_db_path=db_file,
            )
            # Worker 1 acquires key
            _, _, token1 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-fencing",
                content="Fencing test query",
            )

            # Worker 1 hangs; timeout expires and Worker 2 recovers
            await asyncio.sleep(1.1)
            outcome2, _, token2 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-fencing",
                content="Fencing test query",
            )
            self.assertEqual(outcome2, AcquireOutcome.RECOVERED)

            # Expired Worker 1 attempts to complete with its stale token1
            w1_completed = await svc.complete_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-fencing",
                response_data={"reply": "Worker 1 stale response"},
                owner_token=token1,
            )
            # Fencing guarantee: Worker 1 MUST fail completion
            self.assertFalse(w1_completed)

            # Active Worker 2 completes with valid token2
            w2_completed = await svc.complete_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-fencing",
                response_data={"reply": "Worker 2 authentic response"},
                owner_token=token2,
            )
            self.assertTrue(w2_completed)

            # Subsequent retry returns Worker 2's response, NOT Worker 1's
            outcome_final, cached, _ = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-fencing",
                content="Fencing test query",
            )
            self.assertEqual(outcome_final, AcquireOutcome.COMPLETED)
            self.assertEqual(cached["reply"], "Worker 2 authentic response")

    # --------------------------------------------------------------------------
    # Scenario 31: Idempotency Fencing - Expired worker fails to renew lease
    # --------------------------------------------------------------------------
    async def test_31_expired_worker_fails_to_renew_lease(self):
        import tempfile
        import asyncio
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test.db")
            svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                stale_timeout_seconds=1,
                sqlite_db_path=db_file,
            )
            _, _, token1 = await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-renew-fail",
                content="Query",
            )

            # Timeout and recovery by worker 2
            await asyncio.sleep(1.1)
            await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-renew-fail",
                content="Query",
            )

            # Expired worker 1 tries to renew lease
            renew_res = await svc.renew_lease(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="key-renew-fail",
                owner_token=token1,
            )
            self.assertFalse(renew_res)

    # --------------------------------------------------------------------------
    # Scenario 32: Production Safety - Fails closed if PostgreSQL unavailable
    # --------------------------------------------------------------------------
    async def test_32_production_fails_closed_when_postgres_unavailable(self):
        from app.core.config import Settings
        prod_settings = Settings(app_env="production")
        svc = IdempotencyService(
            settings=prod_settings,
            supabase_service=MagicMock(is_configured=lambda: False),
        )

        with self.assertRaises(RuntimeError) as cm:
            await svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="prod-key-1",
                content="Production test",
            )

        self.assertIn("CRITICAL: PostgreSQL idempotency table 'idempotency_keys' is unavailable in production", str(cm.exception))
        self.assertIn("SQLite fallback is disabled in multi-instance production", str(cm.exception))

    # --------------------------------------------------------------------------
    # Scenario 33: Heartbeat - Long running request retains lease via heartbeat
    # --------------------------------------------------------------------------
    async def test_33_request_running_long_retains_lease_with_heartbeat(self):
        import tempfile
        import asyncio
        from unittest.mock import patch
        from app.core.config import Settings

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_heartbeat_33.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
                stale_timeout_seconds=1,  # Short timeout for controlled test
            )
            key = "key-long-running-33"

            # Simulate Gemini taking 1.4s (longer than 1.0s timeout)
            # Heartbeat will renew at 0.4s, 0.8s, and 1.2s
            async def slow_gemini(*args, **kwargs):
                await asyncio.sleep(1.4)
                return "Slow AI response completed successfully"

            self.mock_gemini.generate_response = AsyncMock(side_effect=slow_gemini)

            test_settings = Settings(idempotency_heartbeat_interval_seconds=0.4)
            with patch("app.api.routes.conversations.get_settings", return_value=test_settings):
                task = asyncio.create_task(
                    send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="Slow complex question"),
                        idempotency_key=key,
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )
                )

                # Wait 1.1s (past initial 1.0s timeout, but heartbeat renewed at 0.4s and 0.8s)
                await asyncio.sleep(1.1)

                # Worker 2 attempts acquire with same key
                outcome2, _, _ = await idem_svc.acquire_key(
                    user_id=self.user.user_id,
                    conversation_id=self.conv_id,
                    idempotency_key=key,
                    content="Slow complex question",
                )
                # Worker 2 CANNOT recover the key because heartbeat kept it active!
                self.assertEqual(outcome2, AcquireOutcome.IN_PROGRESS)

                res = await task
                self.assertEqual(res.assistant_message.content, "Slow AI response completed successfully")
                self.assertEqual(res.remaining_credits, 19)

    # --------------------------------------------------------------------------
    # Scenario 34: Heartbeat - Failure to renew prevents completion and charge
    # --------------------------------------------------------------------------
    async def test_34_heartbeat_renewal_failure_prevents_worker_from_completing_or_charging(self):
        import tempfile
        import asyncio
        from unittest.mock import patch
        from app.core.config import Settings

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_heartbeat_34.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
                stale_timeout_seconds=1,
            )
            key = "key-renew-fail-34"

            # Mock renew_lease to simulate losing ownership
            async def failing_renew(*args, **kwargs):
                return False  # Simulate lease revoked / lost

            idem_svc.renew_lease = AsyncMock(side_effect=failing_renew)

            async def delayed_gemini(*args, **kwargs):
                await asyncio.sleep(0.3)
                return "Delayed reply"

            self.mock_gemini.generate_response = AsyncMock(side_effect=delayed_gemini)

            test_settings = Settings(idempotency_heartbeat_interval_seconds=0.1)
            with patch("app.api.routes.conversations.get_settings", return_value=test_settings):
                with self.assertRaises(HTTPException) as cm:
                    await send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="Query that loses lease"),
                        idempotency_key=key,
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )

                self.assertEqual(cm.exception.status_code, 409)
                self.assertIn("exceeded lease duration", cm.exception.detail)
                # Guarantees: Zero credits deducted, zero messages persisted
                self.mock_supabase.deduct_credit_atomic.assert_not_called()

    # --------------------------------------------------------------------------
    # Scenario 35: Heartbeat - Stopped cleanly on success and every failure path
    # --------------------------------------------------------------------------
    async def test_35_heartbeat_stopped_after_success_and_all_failure_paths(self):
        import tempfile
        from unittest.mock import patch
        from contextlib import asynccontextmanager
        from app.core.config import Settings

        test_settings = Settings(idempotency_heartbeat_interval_seconds=0.1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test_35.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
            )

            captured_heartbeats = []
            orig_scope = idem_svc.heartbeat_scope

            @asynccontextmanager
            async def tracking_scope(*args, **kwargs):
                async with orig_scope(*args, **kwargs) as hb:
                    captured_heartbeats.append(hb)
                    yield hb

            idem_svc.heartbeat_scope = tracking_scope

            with patch("app.api.routes.conversations.get_settings", return_value=test_settings):
                # 1. Success exit path
                await send_conversation_message(
                    conversation_id=self.conv_id,
                    payload=MessageCreate(content="Success query"),
                    idempotency_key="key-exit-success",
                    user=self.user,
                    supabase_service=self.mock_supabase,
                    gemini_service=self.mock_gemini,
                    rag_service=self.mock_rag,
                    title_service=self.mock_title,
                    idempotency_service=idem_svc,
                )
                self.assertFalse(captured_heartbeats[-1].is_active)

                # 2. Gemini failure exit path
                self.mock_gemini.generate_response = AsyncMock(side_effect=RuntimeError("Gemini 500 error"))
                with self.assertRaises(HTTPException):
                    await send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="Gemini fail query"),
                        idempotency_key="key-exit-gemini-fail",
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )
                self.assertFalse(captured_heartbeats[-1].is_active)

                # 3. RAG retrieval failure exit path
                self.mock_gemini.generate_response = AsyncMock(return_value="OK")
                self.mock_rag.retrieve_context = AsyncMock(side_effect=RAGRetrievalError("RAG timeout"))
                with self.assertRaises(HTTPException):
                    await send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="RAG fail query"),
                        idempotency_key="key-exit-rag-fail",
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )
                self.assertFalse(captured_heartbeats[-1].is_active)

                # 4. Database persistence failure exit path
                self.mock_rag.retrieve_context = AsyncMock(return_value=MagicMock(citations=[], source_lookup={}))
                self.mock_supabase.save_conversation_turn_atomic = AsyncMock(side_effect=RuntimeError("DB write fail"))
                with self.assertRaises(HTTPException):
                    await send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="DB fail query"),
                        idempotency_key="key-exit-db-fail",
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )
                self.assertFalse(captured_heartbeats[-1].is_active)

    # --------------------------------------------------------------------------
    # Scenario 36: Heartbeat - Request cancellation cleanly stops heartbeat task
    # --------------------------------------------------------------------------
    async def test_36_request_cancellation_cleans_up_heartbeat_task(self):
        import tempfile
        import asyncio
        from unittest.mock import patch
        from contextlib import asynccontextmanager
        from app.core.config import Settings

        test_settings = Settings(idempotency_heartbeat_interval_seconds=0.1)

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test_36.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
            )
            captured_heartbeats = []
            orig_scope = idem_svc.heartbeat_scope

            @asynccontextmanager
            async def tracking_scope(*args, **kwargs):
                async with orig_scope(*args, **kwargs) as hb:
                    captured_heartbeats.append(hb)
                    yield hb

            idem_svc.heartbeat_scope = tracking_scope

            # Gemini hangs until cancelled
            async def hanging_gemini(*args, **kwargs):
                await asyncio.sleep(5.0)
                return "Never reached"

            self.mock_gemini.generate_response = AsyncMock(side_effect=hanging_gemini)

            with patch("app.api.routes.conversations.get_settings", return_value=test_settings):
                req_task = asyncio.create_task(
                    send_conversation_message(
                        conversation_id=self.conv_id,
                        payload=MessageCreate(content="Cancelled query"),
                        idempotency_key="key-cancel-36",
                        user=self.user,
                        supabase_service=self.mock_supabase,
                        gemini_service=self.mock_gemini,
                        rag_service=self.mock_rag,
                        title_service=self.mock_title,
                        idempotency_service=idem_svc,
                    )
                )

                # Wait for request to start and heartbeat to become active
                await asyncio.sleep(0.15)
                self.assertTrue(len(captured_heartbeats) > 0)
                hb = captured_heartbeats[0]
                self.assertTrue(hb.is_active)

                # Cancel the parent request task (e.g. client disconnect)
                req_task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await req_task

                # Heartbeat must be cleanly cancelled and no longer active
                self.assertFalse(hb.is_active)

    def test_37_two_concurrent_requests_same_key_one_acquires_second_in_progress(self):
        """Verify that two concurrent requests with identical key: first acquires, second receives IN_PROGRESS."""
        asyncio.run(self._async_test_37())

    async def _async_test_37(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test_37.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
            )

            outcome1, cached1, token1 = await idem_svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="concurrent-key-1",
                content="Same query text",
            )
            self.assertEqual(outcome1, AcquireOutcome.ACQUIRED)
            self.assertIsNotNone(token1)

            outcome2, cached2, token2 = await idem_svc.acquire_key(
                user_id=self.user.user_id,
                conversation_id=self.conv_id,
                idempotency_key="concurrent-key-1",
                content="Same query text",
            )
            self.assertEqual(outcome2, AcquireOutcome.IN_PROGRESS)
            self.assertIsNone(token2)

    def test_38_atomic_single_transaction_cached_response_retrieval_without_second_gemini_call(self):
        """Verify that a completed idempotency turn returns the complete cached response with citations and 0 extra Gemini calls."""
        asyncio.run(self._async_test_38())

    async def _async_test_38(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_file = os.path.join(tmp_dir, "idem_test_38.db")
            idem_svc = IdempotencyService(
                supabase_service=MagicMock(is_configured=lambda: False),
                sqlite_db_path=db_file,
            )

            # Turn 1: Process message and complete
            res1 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Explain context switching in OS"),
                idempotency_key="key-cached-38",
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=idem_svc,
            )
            self.assertEqual(self.mock_gemini.generate_response.call_count, 1)
            self.assertEqual(res1.user_message.content, "Explain context switching in OS")

            # Turn 2: Retry with exact same key and content
            res2 = await send_conversation_message(
                conversation_id=self.conv_id,
                payload=MessageCreate(content="Explain context switching in OS"),
                idempotency_key="key-cached-38",
                user=self.user,
                supabase_service=self.mock_supabase,
                gemini_service=self.mock_gemini,
                rag_service=self.mock_rag,
                title_service=self.mock_title,
                idempotency_service=idem_svc,
            )

            # ZERO additional Gemini calls, exact cached response returned
            self.assertEqual(self.mock_gemini.generate_response.call_count, 1)
            self.assertEqual(res2.assistant_message.content, res1.assistant_message.content)
            self.assertEqual(res2.user_message.id, res1.user_message.id)


class DateMock:
    _c = 0
    @classmethod
    def now_str(cls):
        cls._c += 1
        return str(cls._c)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
