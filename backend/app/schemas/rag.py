"""Pydantic schemas for RAG (Retrieval-Augmented Generation) in CampusPilot AI."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RAGCitation(BaseModel):
    """Structured citation representation bound to an authentic retrieved chunk."""

    source_id: str = Field(..., description="Unique in-prompt source identifier, e.g. 'S1', 'S2'")
    document_id: str = Field(..., description="UUID of source document")
    filename: str = Field(..., description="Original PDF file name")
    page_number: int = Field(default=1, description="Physical 1-indexed PDF page number")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    chunk_id: Optional[str] = Field(default=None, description="UUID of document chunk")
    chunk_index: Optional[int] = Field(default=None, description="Sequential index of chunk in document")
    scope: Optional[str] = Field(default="personal", description="Access scope: 'personal' or 'shared'")
    snippet: Optional[str] = Field(default=None, description="Authentic extracted passage snippet from source chunk")
    academic_context: Optional[Dict[str, Any]] = Field(default=None, description="Academic metadata such as semester, subject, or unit")


class RAGContext(BaseModel):
    """Container for retrieved chunks, formatted prompt context, and citation metadata."""

    query: str = Field(..., description="Student's original query")
    augmented_prompt: str = Field(..., description="Prompt prepared for Gemini with attached context")
    context_text: str = Field(default="", description="Extracted context block without wrapper directives")
    citations: List[RAGCitation] = Field(default_factory=list, description="All eligible retrieved source citations")
    source_lookup: Dict[str, RAGCitation] = Field(default_factory=dict, description="Map of source_id -> citation")
    total_sources: int = Field(default=0, description="Count of sources included in context")
    has_relevant_context: bool = Field(default=False, description="True if at least one chunk exceeded threshold")
    academic_filters: Dict[str, Any] = Field(default_factory=dict, description="Applied subject/unit/semester filters")


class RAGResult(BaseModel):
    """Result of full RAG generation or citation extraction."""

    reply: str = Field(..., description="Model response text")
    cited_sources: List[RAGCitation] = Field(default_factory=list, description="Citations actually referenced in reply")
    all_sources: List[RAGCitation] = Field(default_factory=list, description="All retrieved sources provided in context")
    has_grounding: bool = Field(default=False, description="True if at least one valid source was cited")
