"""
CampusPilot AI — Phase 3.5.2: RAG Orchestrator & System Prompt Contract Test Suite.

Tests all 12 required scenarios:
1. Relevant chunks returned.
2. No chunks returned.
3. Chunks below configured threshold.
4. Multiple retrieved sources.
5. Correct source ID assignment ([S1], [S2]...).
6. Citation metadata comes from retrieved chunks.
7. Fabricated source IDs are rejected.
8. Missing filename/page metadata handled safely.
9. Semantic search failure handling.
10. Private / shared document access filters.
11. Subject and semester academic filters.
12. Retrieved context does not modify conversation history.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.chat import ChatMessage, ChatRequest, Role
from app.schemas.rag import RAGCitation, RAGContext
from app.schemas.search import SearchResultChunk, SemanticSearchResponse
from app.services.rag import RAGRetrievalError, RAGService


def make_dummy_chunk(
    chunk_id: str,
    doc_id: str,
    filename: str,
    page_number: int,
    similarity_score: float,
    content: str,
    scope: str = "personal",
    chunk_index: int = 0,
) -> SearchResultChunk:
    return SearchResultChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        filename=filename,
        chunk_index=chunk_index,
        page_number=page_number,
        content=content,
        similarity_score=similarity_score,
        scope=scope,
        token_count=len(content.split()),
        character_count=len(content),
    )


class TestRAGOrchestratorSuite(unittest.IsolatedAsyncioTestCase):
    """Test suite covering the 12 core requirements for Phase 3.5.2."""

    def setUp(self):
        self.mock_search_service = MagicMock()
        self.mock_gemini_service = MagicMock()
        self.mock_supabase_service = MagicMock()

        self.rag_service = RAGService(
            search_service=self.mock_search_service,
            gemini_service=self.mock_gemini_service,
            supabase_service=self.mock_supabase_service,
            default_top_k=4,
            default_threshold=0.60,
        )

    # --------------------------------------------------------------------------
    # Scenario 1: Relevant chunks returned
    # --------------------------------------------------------------------------
    async def test_01_relevant_chunks_returned(self):
        chunks = [
            make_dummy_chunk(
                chunk_id="c1",
                doc_id="d1",
                filename="Data_Science_Unit1.pdf",
                page_number=2,
                similarity_score=0.85,
                content="Data science comprises hacking skills, math knowledge, and substantive expertise.",
            ),
            make_dummy_chunk(
                chunk_id="c2",
                doc_id="d1",
                filename="Data_Science_Unit1.pdf",
                page_number=3,
                similarity_score=0.79,
                content="Exploratory data analysis helps discover patterns in initial data sets.",
            ),
        ]
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="What is data science?",
                total_results=2,
                results=chunks,
                execution_time_ms=12.5,
                status="success",
            )
        )

        ctx: RAGContext = await self.rag_service.retrieve_context(
            user_id="user-123",
            query="What is data science?",
        )

        self.assertTrue(ctx.has_relevant_context)
        self.assertEqual(ctx.total_sources, 2)
        self.assertEqual(len(ctx.citations), 2)
        self.assertIn("[Source S1: Data_Science_Unit1.pdf, Page 2, Relevance: 0.85]", ctx.augmented_prompt)
        self.assertIn("[Source S2: Data_Science_Unit1.pdf, Page 3, Relevance: 0.79]", ctx.augmented_prompt)
        self.assertIn("hacking skills", ctx.augmented_prompt)
        self.assertIn("Student Question:\nWhat is data science?", ctx.augmented_prompt)

    # --------------------------------------------------------------------------
    # Scenario 2: No chunks returned
    # --------------------------------------------------------------------------
    async def test_02_no_chunks_returned(self):
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="Out of domain question",
                total_results=0,
                results=[],
                execution_time_ms=5.0,
                status="success",
            )
        )

        ctx: RAGContext = await self.rag_service.retrieve_context(
            user_id="user-123",
            query="Out of domain question",
        )

        self.assertFalse(ctx.has_relevant_context)
        self.assertEqual(ctx.total_sources, 0)
        self.assertEqual(len(ctx.citations), 0)
        self.assertEqual(ctx.augmented_prompt, "Out of domain question")
        self.assertEqual(ctx.context_text, "")

    # --------------------------------------------------------------------------
    # Scenario 3: Chunks below the configured threshold
    # --------------------------------------------------------------------------
    async def test_03_configurable_similarity_threshold(self):
        # Verify custom threshold is passed down cleanly to search_service
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="Query",
                total_results=0,
                results=[],
                execution_time_ms=5.0,
                status="success",
            )
        )

        await self.rag_service.retrieve_context(
            user_id="user-123",
            query="Query",
            similarity_threshold=0.75,
        )

        self.mock_search_service.search.assert_awaited_once_with(
            user_id="user-123",
            query="Query",
            top_k=4,
            similarity_threshold=0.75,
            document_id=None,
        )

    # --------------------------------------------------------------------------
    # Scenario 4: Multiple retrieved sources
    # --------------------------------------------------------------------------
    async def test_04_multiple_retrieved_sources(self):
        chunks = [
            make_dummy_chunk("c1", "d1", "BCA.pdf", 14, 0.88, "BCA syllabus overview"),
            make_dummy_chunk("c2", "d2", "AI_Unit2.pdf", 5, 0.81, "A* search algorithm"),
            make_dummy_chunk("c3", "d3", "Java_Enterprise.pdf", 22, 0.76, "Spring beans"),
            make_dummy_chunk("c4", "d4", "Networks.pdf", 8, 0.72, "OSI 7 layers"),
        ]
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="General review",
                total_results=4,
                results=chunks,
                execution_time_ms=20.0,
                status="success",
            )
        )

        ctx = await self.rag_service.retrieve_context(
            user_id="user-123",
            query="General review",
            top_k=4,
        )

        self.assertEqual(ctx.total_sources, 4)
        self.assertEqual([c.source_id for c in ctx.citations], ["S1", "S2", "S3", "S4"])
        self.assertEqual(ctx.citations[0].filename, "BCA.pdf")
        self.assertEqual(ctx.citations[1].filename, "AI_Unit2.pdf")
        self.assertEqual(ctx.citations[2].filename, "Java_Enterprise.pdf")
        self.assertEqual(ctx.citations[3].filename, "Networks.pdf")

    # --------------------------------------------------------------------------
    # Scenario 5: Correct source ID assignment
    # --------------------------------------------------------------------------
    async def test_05_correct_source_id_assignment(self):
        chunks = [
            make_dummy_chunk("c1", "d1", "DocA.pdf", 1, 0.90, "Content A"),
            make_dummy_chunk("c2", "d2", "DocB.pdf", 2, 0.80, "Content B"),
        ]
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="q", total_results=2, results=chunks, execution_time_ms=1.0, status="success"
            )
        )

        ctx = await self.rag_service.retrieve_context(user_id="u1", query="q")
        self.assertIn("S1", ctx.source_lookup)
        self.assertIn("S2", ctx.source_lookup)
        self.assertEqual(ctx.source_lookup["S1"].filename, "DocA.pdf")
        self.assertEqual(ctx.source_lookup["S2"].filename, "DocB.pdf")

    # --------------------------------------------------------------------------
    # Scenario 6: Citation metadata comes from retrieved chunks
    # --------------------------------------------------------------------------
    async def test_06_citation_metadata_fidelity(self):
        chunk = make_dummy_chunk(
            chunk_id="chunk-uuid-4444",
            doc_id="doc-uuid-1111",
            filename="OS_Deadlocks.pdf",
            page_number=42,
            similarity_score=0.8876,
            content="Banker's algorithm avoids deadlock.",
            scope="shared",
            chunk_index=7,
        )
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="deadlock", total_results=1, results=[chunk], execution_time_ms=1.0, status="success"
            )
        )

        ctx = await self.rag_service.retrieve_context(user_id="u1", query="deadlock")
        cit = ctx.citations[0]
        self.assertEqual(cit.chunk_id, "chunk-uuid-4444")
        self.assertEqual(cit.document_id, "doc-uuid-1111")
        self.assertEqual(cit.filename, "OS_Deadlocks.pdf")
        self.assertEqual(cit.page_number, 42)
        self.assertEqual(cit.similarity_score, 0.8876)
        self.assertEqual(cit.scope, "shared")
        self.assertEqual(cit.chunk_index, 7)

    # --------------------------------------------------------------------------
    # Scenario 7: Fabricated source IDs are rejected
    # --------------------------------------------------------------------------
    def test_07_fabricated_source_ids_rejected(self):
        source_lookup = {
            "S1": RAGCitation(
                source_id="S1",
                document_id="d1",
                filename="AI_Notes.pdf",
                page_number=1,
                similarity_score=0.85,
            ),
            "S2": RAGCitation(
                source_id="S2",
                document_id="d2",
                filename="DBMS_Guide.pdf",
                page_number=5,
                similarity_score=0.78,
            ),
        }

        # Model hallucinates [S99], [S5], [S0], but validly cites [S1] and [S2]
        model_reply = (
            "According to [S1], neural networks require loss functions. "
            "Also, [S99] claims exam dates are next week. "
            "Furthermore [S2] defines relational schemas, while [S5] is completely fabricated."
        )

        valid_citations = self.rag_service.extract_citations(
            reply_text=model_reply,
            source_lookup=source_lookup,
        )

        self.assertEqual(len(valid_citations), 2)
        self.assertEqual([c.source_id for c in valid_citations], ["S1", "S2"])
        # Ensure S99 and S5 are not present
        cited_ids = [c.source_id for c in valid_citations]
        self.assertNotIn("S99", cited_ids)
        self.assertNotIn("S5", cited_ids)

    # --------------------------------------------------------------------------
    # Scenario 8: Missing filename/page metadata handled safely
    # --------------------------------------------------------------------------
    async def test_08_missing_metadata_handled_safely(self):
        chunk = SearchResultChunk(
            chunk_id="c_anon",
            document_id="d_anon",
            filename="",  # empty filename
            chunk_index=0,
            page_number=0,  # invalid page
            content="Some anonymous lecture excerpt",
            similarity_score=0.75,
            scope="personal",
        )
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="test", total_results=1, results=[chunk], execution_time_ms=1.0, status="success"
            )
        )

        ctx = await self.rag_service.retrieve_context(user_id="u1", query="test")
        cit = ctx.citations[0]
        self.assertEqual(cit.filename, "academic_document.pdf")
        self.assertEqual(cit.page_number, 1)

    # --------------------------------------------------------------------------
    # Scenario 9: Semantic search failure
    # --------------------------------------------------------------------------
    async def test_09_semantic_search_failure_handling(self):
        self.mock_search_service.search = AsyncMock(
            side_effect=RuntimeError("Google Gemini API 503 Overload")
        )

        # Mode A: raise_on_error=True (default) raises RAGRetrievalError
        with self.assertRaises(RAGRetrievalError) as cm:
            await self.rag_service.retrieve_context(
                user_id="u1",
                query="Test query",
                raise_on_error=True,
            )
        self.assertIn("Google Gemini API 503 Overload", str(cm.exception))

        # Mode B: raise_on_error=False falls back to ungrounded context safely
        ctx = await self.rag_service.retrieve_context(
            user_id="u1",
            query="Test query",
            raise_on_error=False,
        )
        self.assertFalse(ctx.has_relevant_context)
        self.assertEqual(ctx.citations, [])
        self.assertEqual(ctx.augmented_prompt, "Test query")

    # --------------------------------------------------------------------------
    # Scenario 10: Private / shared document access filters
    # --------------------------------------------------------------------------
    async def test_10_document_access_isolation(self):
        # If user attempts to access a document they do not own, PermissionError must propagate
        self.mock_search_service.search = AsyncMock(
            side_effect=PermissionError("Access denied: document d_alien not accessible by user-123")
        )

        with self.assertRaises(PermissionError):
            await self.rag_service.retrieve_context(
                user_id="user-123",
                query="Steal private notes",
                document_id="d_alien",
            )

    # --------------------------------------------------------------------------
    # Scenario 11: Subject and semester academic filters
    # --------------------------------------------------------------------------
    async def test_11_subject_and_semester_filters(self):
        chunks = [
            make_dummy_chunk("c1", "doc_ai", "AI_Syllabus.pdf", 1, 0.85, "AI curriculum"),
            make_dummy_chunk("c2", "doc_ds", "DataScience_Unit1.pdf", 1, 0.82, "Data Science Venn diagram"),
        ]
        self.mock_search_service.search = AsyncMock(
            return_value=SemanticSearchResponse(
                query="curriculum", total_results=2, results=chunks, execution_time_ms=1.0, status="success"
            )
        )

        # Mock supabase document metadata
        async def mock_get_user_doc(user_id, document_id):
            if document_id == "doc_ai":
                return {"id": "doc_ai", "subject_id": "sub_ai_502", "semester_id": "sem_5"}
            elif document_id == "doc_ds":
                return {"id": "doc_ds", "subject_id": "sub_ds_503", "semester_id": "sem_5"}
            return None

        self.mock_supabase_service.get_user_document = AsyncMock(side_effect=mock_get_user_doc)

        # Query with subject_id filter for Data Science
        ctx = await self.rag_service.retrieve_context(
            user_id="u1",
            query="curriculum",
            subject_id="sub_ds_503",
        )

        self.assertEqual(ctx.total_sources, 1)
        self.assertEqual(ctx.citations[0].document_id, "doc_ds")
        self.assertEqual(ctx.citations[0].filename, "DataScience_Unit1.pdf")

    # --------------------------------------------------------------------------
    # Scenario 12: Retrieved context does not modify conversation history
    # --------------------------------------------------------------------------
    def test_12_context_history_isolation(self):
        raw_query = "Explain Bayesian networks"
        history = [
            ChatMessage(role=Role.USER, content="Hello CampusPilot"),
            ChatMessage(role=Role.MODEL, content="Hello! How can I assist your studies today?"),
        ]

        rag_ctx = RAGContext(
            query=raw_query,
            augmented_prompt=(
                "=== VERIFIED COURSE STUDY MATERIAL ===\n"
                "[Source S1: AI.pdf, Page 10]\nBayesian networks represent probabilistic dependencies.\n"
                "=== END OF STUDY MATERIAL ===\n\nStudent Question:\nExplain Bayesian networks"
            ),
            context_text="[Source S1: AI.pdf, Page 10]\nBayesian networks...",
            citations=[
                RAGCitation(
                    source_id="S1",
                    document_id="d1",
                    filename="AI.pdf",
                    page_number=10,
                    similarity_score=0.88,
                )
            ],
            source_lookup={},
            total_sources=1,
            has_relevant_context=True,
        )

        # Prepare chat request
        chat_req: ChatRequest = self.rag_service.prepare_chat_request(
            raw_query=raw_query,
            history=history,
            rag_context=rag_ctx,
        )

        # 1. Active message sent to Gemini is the augmented prompt
        self.assertEqual(chat_req.message, rag_ctx.augmented_prompt)
        # 2. History remains completely pristine with original text
        self.assertEqual(len(chat_req.history), 2)
        self.assertEqual(chat_req.history[0].content, "Hello CampusPilot")
        self.assertEqual(chat_req.history[1].content, "Hello! How can I assist your studies today?")
        # 3. None of the history messages contain injected course material
        for h in chat_req.history:
            self.assertNotIn("=== VERIFIED COURSE STUDY MATERIAL ===", h.content)


def main():
    unittest.main()


if __name__ == "__main__":
    main()
