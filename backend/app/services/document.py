import logging
from typing import List
import pymupdf
from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.schemas.document import DocumentExtractionResponse, ExtractedPage

logger = logging.getLogger(__name__)

PDF_MAGIC_BYTES = b"%PDF"


class DocumentService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def extract_text_from_pdf(self, file: UploadFile) -> DocumentExtractionResponse:
        """
        Validates and extracts page-by-page text from an uploaded PDF completely in-memory.
        No files are saved to permanent storage or disk.
        """
        filename = file.filename or "uploaded_document.pdf"

        # 1. Extension validation
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension for '{filename}'. Only .pdf files are accepted.",
            )

        # 2. Content type header validation (if provided)
        if file.content_type and file.content_type.lower() not in [
            "application/pdf",
            "application/x-pdf",
            "application/acrobat",
            "applications/vnd.pdf",
            "text/pdf",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME content-type '{file.content_type}'. Must be application/pdf.",
            )

        # 3. Read in-memory bytes with size limit enforcement
        max_bytes = self.settings.max_upload_size_bytes
        file_bytes = await file.read()
        file_size = len(file_bytes)

        # 4. Empty file check
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The uploaded file '{filename}' is empty (0 bytes).",
            )

        # 5. Size limit check
        if file_size > max_bytes:
            max_mb = max_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
            )

        # 6. Magic bytes validation (verifying true PDF header)
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' does not have a valid PDF header signature (%PDF-). It may be corrupted or disguised.",
            )

        return self.extract_from_bytes(file_bytes=file_bytes, filename=filename)

    def extract_from_bytes(self, file_bytes: bytes, filename: str) -> DocumentExtractionResponse:
        """Extract text from in-memory PDF bytes with validation and page tracking."""
        file_size = len(file_bytes)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The uploaded file '{filename}' is empty (0 bytes).",
            )

        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' does not have a valid PDF header signature (%PDF-).",
            )

        doc = None
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            logger.warning("PyMuPDF failed opening stream for '%s': %s", filename, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to parse '{filename}'. The PDF structure appears corrupted or unreadable.",
            ) from exc

        try:
            total_pages = doc.page_count
            if total_pages == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The PDF '{filename}' contains 0 pages.",
                )

            extracted_pages_list: List[ExtractedPage] = []
            non_empty_page_count = 0

            for page_index in range(total_pages):
                page = doc.load_page(page_index)
                raw_text = page.get_text("text") or ""
                cleaned_text = raw_text.strip()
                has_text = len(cleaned_text) > 0

                if has_text:
                    non_empty_page_count += 1
                    content = cleaned_text
                else:
                    content = "[No extractable text on this page (scanned or image-only)]"

                extracted_pages_list.append(
                    ExtractedPage(
                        page_number=page_index + 1,
                        content=content,
                        character_count=len(cleaned_text),
                        has_text=has_text,
                    )
                )

            return DocumentExtractionResponse(
                filename=filename,
                total_pages=total_pages,
                extracted_pages=non_empty_page_count,
                file_size_bytes=file_size,
                pages=extracted_pages_list,
                status="success",
            )
        finally:
            if doc is not None:
                doc.close()


_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
