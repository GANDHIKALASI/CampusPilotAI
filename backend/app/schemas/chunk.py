"""Pydantic schemas for document chunking and metadata in CampusPilot AI."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents an individual chunk of text from a document with full metadata."""

    chunk_index: int = Field(..., description="Global zero-based sequential index of the chunk across the document")
    page_number: int = Field(..., description="1-based original PDF page number where this chunk originated")
    filename: str = Field(..., description="Name of the source document file")
    content: str = Field(..., description="Cleaned text content of the chunk")
    token_count: int = Field(..., description="Token count of the chunk content (BPE cl100k_base or fallback)")
    character_count: int = Field(..., description="Character count of the chunk content")
    start_char_offset: int = Field(..., description="Starting character offset of the chunk relative to cleaned page text")
    end_char_offset: int = Field(..., description="Ending character offset of the chunk relative to cleaned page text")
    document_id: Optional[str] = Field(
        default=None,
        description="Document identifier (null in Milestone 3.2 as PostgreSQL/database persistence is not yet implemented)",
    )


class ChunkedDocumentResponse(BaseModel):
    """Response returned when a document is cleaned and chunked."""

    filename: str = Field(..., description="Name of the processed document")
    total_pages: int = Field(..., description="Total number of pages in the original document")
    total_chunks: int = Field(..., description="Total number of generated text chunks")
    target_chunk_tokens: int = Field(..., description="Configured target chunk size in tokens")
    overlap_tokens: int = Field(..., description="Configured overlap size in tokens between consecutive intra-page chunks")
    chunks: List[DocumentChunk] = Field(default_factory=list, description="List of generated document chunks")
    status: str = Field(default="success", description="Status of the chunking operation")
