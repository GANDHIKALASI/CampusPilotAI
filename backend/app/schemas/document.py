from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    page_number: int = Field(..., description="1-indexed physical page number")
    content: str = Field(..., description="Extracted textual content of the page")
    character_count: int = Field(..., description="Total character length of extracted text")
    has_text: bool = Field(..., description="True if extractable text was found, False if blank or image-only")


class DocumentExtractionResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded PDF file")
    total_pages: int = Field(..., description="Total number of pages detected in the document")
    extracted_pages: int = Field(..., description="Count of pages containing non-empty extractable text")
    file_size_bytes: int = Field(..., description="Total uploaded file size in bytes")
    pages: List[ExtractedPage] = Field(..., description="Ordered list of page extraction details")
    status: str = Field(default="success", description="Overall extraction outcome")


class DocumentItem(BaseModel):
    """Represents a persisted student or shared academic document record."""

    id: str
    user_id: str
    filename: str
    storage_path: str
    mime_type: str
    file_size: int
    processing_status: str
    scope: str = "personal"  # 'personal' or 'shared'
    semester_id: Optional[str] = None
    subject_id: Optional[str] = None
    unit_id: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentUploadResponse(BaseModel):
    """Response returned when an authenticated document is uploaded and processed."""

    document: DocumentItem
    total_pages: int
    total_chunks: int
    status: str = "success"


class DocumentDownloadResponse(BaseModel):
    """Authorized signed URL response for document download."""

    document_id: str
    filename: str
    signed_url: str
    expires_in_seconds: int = 3600
