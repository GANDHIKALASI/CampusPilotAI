"""
CampusPilot AI — RAG (Retrieval-Augmented Generation) Orchestration Service.

Connects semantic similarity search (pgvector) with Gemini prompt engineering:
- Orchestrates query retrieval using existing SemanticSearchService.
- Applies strict citation integrity ([S1], [S2] source contract).
- Preserves clean conversation history and isolates context augmentation to the current turn.
- Strictly enforces personal document ownership and authorized shared curriculum access.
- Validates and structures citations from authentic database chunk metadata.
- Handles empty retrieval and search service failures transparently.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatMessage, ChatRequest
from app.schemas.rag import RAGCitation, RAGContext, RAGResult
from app.schemas.search import SearchResultChunk, SemanticSearchResponse
from app.services.gemini import GeminiService, get_gemini_service
from app.services.semantic_search import SemanticSearchService, get_semantic_search_service
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)


class RAGRetrievalError(Exception):
    """Raised when semantic retrieval fails critically."""
    pass


class RAGService:
    """Orchestrates document chunk retrieval, context formatting, and citation parsing."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        search_service: Optional[SemanticSearchService] = None,
        gemini_service: Optional[GeminiService] = None,
        supabase_service: Optional[SupabaseService] = None,
        default_top_k: int = 4,
        default_threshold: Optional[float] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.search_service = search_service or get_semantic_search_service()
        self.gemini_service = gemini_service or get_gemini_service()
        self.supabase_service = supabase_service or get_supabase_service()
        self.default_top_k = max(1, min(default_top_k, self.settings.search_max_top_k))
        # Configurable similarity threshold; defaults to settings if not provided
        self.default_threshold = (
            default_threshold
            if default_threshold is not None
            else self.settings.search_default_threshold
        )

    async def retrieve_context(
        self,
        user_id: str,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        document_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        raise_on_error: bool = True,
    ) -> RAGContext:
        """
        Retrieve relevant document chunks and build an authenticated RAG context.

        Args:
            user_id: Authenticated student's UUID.
            query: Natural language academic query.
            top_k: Maximum number of chunks to return (default: 4).
            similarity_threshold: Minimum cosine similarity required.
            document_id: Optional document ID to scope retrieval within.
            subject_id: Optional academic subject ID filter.
            semester_id: Optional academic semester ID filter.
            unit_id: Optional academic unit ID filter.
            raise_on_error: If True, raises RAGRetrievalError on search failure.

        Returns:
            RAGContext containing formatted prompt, citations, and metadata.
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required and cannot be empty.")
        if not query or not query.strip():
            raise ValueError("query is required and cannot be empty.")

        clean_query = query.strip()
        effective_top_k = min(
            max(1, top_k if top_k is not None else self.default_top_k),
            self.settings.search_max_top_k,
        )
        effective_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.default_threshold
        )

        academic_filters: Dict[str, Any] = {}
        if document_id:
            academic_filters["document_id"] = document_id
        if subject_id:
            academic_filters["subject_id"] = subject_id
        if semester_id:
            academic_filters["semester_id"] = semester_id
        if unit_id:
            academic_filters["unit_id"] = unit_id

        # 1. Execute semantic search with database-level academic filtering
        try:
            search_kwargs: Dict[str, Any] = {
                "user_id": user_id,
                "query": clean_query,
                "top_k": effective_top_k,
                "similarity_threshold": effective_threshold,
                "document_id": document_id,
            }
            if subject_id is not None:
                search_kwargs["subject_id"] = subject_id
            if semester_id is not None:
                search_kwargs["semester_id"] = semester_id
            if unit_id is not None:
                search_kwargs["unit_id"] = unit_id

            search_response: SemanticSearchResponse = await self.search_service.search(**search_kwargs)
            raw_chunks: List[SearchResultChunk] = search_response.results or []
        except PermissionError:
            raise
        except Exception as exc:
            logger.error("RAG retrieval failed for user %s: %s", user_id, exc)
            if raise_on_error:
                raise RAGRetrievalError(f"Semantic search service failure: {exc}") from exc
            raw_chunks = []

        # 2. Re-verify academic curriculum filters as safeguard
        filtered_chunks = await self._apply_academic_filters(
            chunks=raw_chunks,
            user_id=user_id,
            subject_id=subject_id,
            semester_id=semester_id,
            unit_id=unit_id,
        )

        # 3. Handle empty retrieval or below-threshold chunks gracefully
        if not filtered_chunks:
            return RAGContext(
                query=clean_query,
                augmented_prompt=clean_query,
                context_text="",
                citations=[],
                source_lookup={},
                total_sources=0,
                has_relevant_context=False,
                academic_filters=academic_filters,
            )

        # 4. Assign source IDs (S1, S2, etc.) and construct citation metadata
        citations: List[RAGCitation] = []
        source_lookup: Dict[str, RAGCitation] = {}
        context_snippets: List[str] = []

        for idx, chunk in enumerate(filtered_chunks, start=1):
            source_id = f"S{idx}"
            safe_filename = chunk.filename or "academic_document.pdf"
            safe_page = max(1, chunk.page_number)
            score = round(chunk.similarity_score, 4)

            clean_snippet = chunk.content.strip()
            if len(clean_snippet) > 400:
                clean_snippet = clean_snippet[:397] + "..."

            citation = RAGCitation(
                source_id=source_id,
                document_id=chunk.document_id,
                filename=safe_filename,
                page_number=safe_page,
                similarity_score=score,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                scope=chunk.scope,
                snippet=clean_snippet,
                academic_context=academic_filters if academic_filters else None,
            )
            citations.append(citation)
            source_lookup[source_id] = citation

            snippet_header = (
                f"[Source {source_id}: {safe_filename}, Page {safe_page}, Relevance: {score:.2f}]"
            )
            context_snippets.append(f"{snippet_header}\n{chunk.content.strip()}")

        context_block = "\n\n---\n\n".join(context_snippets)

        # 5. Build clean, strictly-delimited augmented prompt
        augmented_prompt = (
            f"=== VERIFIED COURSE STUDY MATERIAL ===\n"
            f"{context_block}\n"
            f"=== END OF STUDY MATERIAL ===\n\n"
            f"Grounding Directives for Response:\n"
            f"1. Base your answers on the provided study materials where relevant.\n"
            f"2. Whenever citing facts, definitions, or equations from this material, cite the source ID in square brackets, e.g., [S1], [S2].\n"
            f"3. Do not invent source IDs, file names, or page numbers not provided above.\n"
            f"4. If the provided material does not address the question, clearly state that the provided course material does not directly cover it, and then provide a thorough pedagogical explanation using general academic knowledge.\n\n"
            f"Student Question:\n{clean_query}"
        )

        return RAGContext(
            query=clean_query,
            augmented_prompt=augmented_prompt,
            context_text=context_block,
            citations=citations,
            source_lookup=source_lookup,
            total_sources=len(citations),
            has_relevant_context=True,
            academic_filters=academic_filters,
        )

    async def _apply_academic_filters(
        self,
        chunks: List[SearchResultChunk],
        user_id: str,
        subject_id: Optional[str] = None,
        semester_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> List[SearchResultChunk]:
        """Post-filter chunks by document academic metadata if filters are requested."""
        if not (subject_id or semester_id or unit_id) or not chunks:
            return chunks

        doc_ids: Set[str] = {c.document_id for c in chunks}
        matching_doc_ids: Set[str] = set()

        for d_id in doc_ids:
            try:
                doc = await self.supabase_service.get_user_document(user_id=user_id, document_id=d_id)
                if not doc:
                    continue

                matches = True
                if subject_id and str(doc.get("subject_id") or "") != str(subject_id):
                    matches = False
                if semester_id and str(doc.get("semester_id") or "") != str(semester_id):
                    matches = False
                if unit_id and str(doc.get("unit_id") or "") != str(unit_id):
                    matches = False

                if matches:
                    matching_doc_ids.add(d_id)
            except Exception as e:
                logger.warning("Error evaluating academic filter on doc %s: %s", d_id, e)

        return [c for c in chunks if c.document_id in matching_doc_ids]

    def extract_citations(
        self,
        reply_text: str,
        source_lookup: Dict[str, RAGCitation],
    ) -> List[RAGCitation]:
        """
        Extract and validate source citations from model reply.

        - Extracts source tags like [S1], [S2], [Source S1], [Source: S1], [S1, S2], [Source S1: ..., Page ...].
        - Rejects fabricated source IDs (e.g. [S99] if only S1, S2 exist in retrieved context).
        - Deduplicates repeated citations across the response.
        - Preserves authentic metadata (filename, page_number, similarity_score, chunk_id).
        - Returns ordered, deduplicated citations.

        IMPORTANT ARCHITECTURAL DISTINCTION:
        This function performs structural citation syntax extraction and validates that the referenced
        source identifiers (e.g., S1, S2) exist within the authenticated retrieved context set.
        It strictly verifies source ID existence and prevents fabricated citations; it does not perform
        natural language inference (NLI) claim entailment proof.
        """
        if not reply_text or not source_lookup:
            return []

        # Find all patterns like [S1], [Source S1], [Source: S1], [S1, S2], [Source S1: ..., Page ...]
        raw_matches = re.findall(
            r"\[(?:Source:?\s*)?(S\d+(?:[\s,]+(?:Source:?\s*)?S\d+)*)(?::[^\]]*)?\]",
            reply_text,
            re.IGNORECASE,
        )
        found_source_ids: Set[str] = set()

        for match in raw_matches:
            # Split comma/space separated tags like S1, S2 or Source S1, Source S2
            parts = re.split(r"[\s,]+", match)
            for part in parts:
                clean_id = re.sub(r"^Source:?\s*", "", part.strip(), flags=re.IGNORECASE).upper()
                if clean_id.startswith("S") and clean_id in source_lookup:
                    found_source_ids.add(clean_id)

        # Return sorted by source index (S1, S2, etc.) with deduplicated entries
        valid_citations: List[RAGCitation] = []
        for sid in sorted(found_source_ids, key=lambda s: int(s[1:]) if s[1:].isdigit() else 999):
            valid_citations.append(source_lookup[sid])

        return valid_citations

    def prepare_chat_request(
        self,
        raw_query: str,
        history: List[ChatMessage],
        rag_context: RAGContext,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> ChatRequest:
        """
        Construct a ChatRequest for Gemini isolating RAG context to the current turn.

        Ensures:
        - raw_query remains pristine in caller's conversation persistence.
        - history contains only clean historical dialogue turns.
        - augmented prompt is sent only for the current active turn.
        """
        message_for_model = (
            rag_context.augmented_prompt
            if rag_context.has_relevant_context
            else raw_query
        )

        return ChatRequest(
            message=message_for_model,
            history=history,
            model=model,
            temperature=temperature if temperature is not None else 0.7,
        )

    def format_citation_metadata(self, citations: List[RAGCitation]) -> List[Dict[str, Any]]:
        """Format citations into the expected frontend/API contract."""
        return [
            {
                "source_id": c.source_id,
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "similarity_score": c.similarity_score,
                "chunk_id": c.chunk_id,
                "scope": c.scope,
                "snippet": c.snippet,
                "academic_context": c.academic_context,
            }
            for c in citations
        ]


_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
