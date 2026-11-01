"""
Pydantic schemas for semantic similarity search in CampusPilot AI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Request payload for semantic similarity search across academic documents."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Student natural-language search query",
        examples=["How does pipelining improve instruction throughput in computer architecture?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of relevant chunks to retrieve (1 to 20)",
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score required (0.0 to 1.0). Defaults to server configuration (0.60)",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Optional specific document ID to scope retrieval within. Enforces user ownership.",
    )


class SearchResultChunk(BaseModel):
    """Ranked document chunk matched by semantic similarity."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Source document identifier")
    filename: str = Field(..., description="Source document file name")
    chunk_index: int = Field(..., description="Global chunk sequential index across document")
    page_number: int = Field(..., description="1-indexed physical PDF page number")
    content: str = Field(..., description="Text content of the matched chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0, where 1.0 is identical)")
    scope: str = Field(..., description="Document scope: 'personal' or 'shared'")
    token_count: int = Field(default=0, description="Token count of the chunk content")
    character_count: int = Field(default=0, description="Character count of the chunk content")


class SemanticSearchResponse(BaseModel):
    """Response payload containing ranked matching chunks and search metadata."""

    query: str = Field(..., description="Original query evaluated")
    total_results: int = Field(..., description="Number of chunks matching the threshold and constraints")
    results: List[SearchResultChunk] = Field(default_factory=list, description="Ranked chunks ordered by descending similarity")
    execution_time_ms: float = Field(..., description="Total search roundtrip execution time in milliseconds")
    status: str = Field(default="success", description="Search execution outcome")
