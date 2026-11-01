import io
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import Settings, get_settings
from app.schemas.chunk import ChunkedDocumentResponse
from app.schemas.document import (
    DocumentDownloadResponse,
    DocumentExtractionResponse,
    DocumentItem,
    DocumentUploadResponse,
)
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.chunking import ChunkingService, get_chunking_service
from app.services.document import DocumentService, get_document_service
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.embedding_persistence import (
    EmbeddingPersistenceService,
    get_embedding_persistence_service,
    validate_embedding_vector,
)
from app.services.supabase import SupabaseService, get_supabase_service
from app.services.semantic_search import SemanticSearchService, get_semantic_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# =============================================================================
# Authenticated Document Storage & Persistence (Phase 3.3)
# =============================================================================

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, store original PDF in private storage, extract, clean, and chunk",
    description=(
        "Full persistence pipeline: verifies student identity -> stores original binary in "
        "private bucket campuspilot-documents -> registers in PostgreSQL -> extracts pages -> "
        "cleans & chunks -> saves chunks to document_chunks table -> generates embeddings -> "
        "persists vectors into pgvector -> marks document completed."
    ),
)
async def upload_document_authenticated(
    file: UploadFile = File(..., description="PDF document to upload and persist"),
    scope: str = Query("personal", description="Document scope: 'personal' or 'shared'"),
    semester_id: Optional[str] = Query(None, description="Optional associated semester ID"),
    subject_id: Optional[str] = Query(None, description="Optional associated subject ID"),
    unit_id: Optional[str] = Query(None, description="Optional associated unit ID"),
    user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    document_service: DocumentService = Depends(get_document_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    embedding_persistence_service: EmbeddingPersistenceService = Depends(get_embedding_persistence_service),
) -> DocumentUploadResponse:
    # 0. Enforce permission: only administrators can upload shared documents
    clean_scope = "shared" if scope == "shared" else "personal"
    if clean_scope == "shared" and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only authorized administrators can upload shared academic documents.",
        )

    # 1. Validate file extension
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF documents are supported.",
        )

    # 2. Read file bytes
    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 3. Check file size
    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.max_upload_size_bytes // (1024 * 1024)} MB.",
        )

    # 4. Validate magic bytes (%PDF-)
    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF structure: missing standard PDF header signature.",
        )

    document_id = str(uuid.uuid4())

    try:
        # 5. Store binary in private Supabase Storage
        storage_path = await supabase_service.upload_document_file(
            user_id=user.user_id,
            document_id=document_id,
            file_bytes=file_bytes,
            filename=filename,
            mime_type=file.content_type or "application/pdf",
        )

        # 6. Create document database record
        doc_record = await supabase_service.create_document_record(
            user_id=user.user_id,
            filename=filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=file.content_type or "application/pdf",
            scope=clean_scope,
            semester_id=semester_id,
            subject_id=subject_id,
            unit_id=unit_id,
        )
        # Use database-generated ID
        actual_doc_id = doc_record["id"]

        # Mark processing
        await supabase_service.update_document_status(actual_doc_id, "processing")

        # 7. Extract text via DocumentService
        extracted_doc = document_service.extract_from_bytes(file_bytes, filename)

        # 8. Clean and chunk via ChunkingService
        chunked_doc = chunking_service.chunk_document(extracted_doc)

        # 9. Save chunks into document_chunks table
        raw_chunks = [c.model_dump() for c in chunked_doc.chunks]
        saved_chunk_count = await supabase_service.save_document_chunks(
            document_id=actual_doc_id,
            user_id=user.user_id,
            chunks=raw_chunks,
            scope=clean_scope,
            semester_id=semester_id,
            subject_id=subject_id,
            unit_id=unit_id,
        )

        # 10. Generate embeddings for document chunks using Gemini Embedding API
        if chunked_doc.chunks:
            try:
                bulk_res = embedding_service.embed_chunks_bulk(
                    chunks=chunked_doc.chunks,
                    document_title=filename,
                    force_reembed=False,
                )
            except Exception as emb_exc:
                logger.error("Embedding API error for document %s: %s", actual_doc_id, emb_exc)
                await supabase_service.update_document_status(actual_doc_id, "failed")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Document uploaded and chunked, but embedding generation failed: {str(emb_exc)}",
                ) from emb_exc

            if bulk_res.status == "failed" or not bulk_res.successful_chunks:
                err_detail = (
                    bulk_res.failed_chunks[0].error
                    if bulk_res.failed_chunks
                    else "Embedding generation failed for all chunks."
                )
                logger.error("Embedding generation failed for doc %s: %s", actual_doc_id, err_detail)
                await supabase_service.update_document_status(actual_doc_id, "failed")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Document uploaded and chunked, but vector embedding generation failed: {err_detail}",
                )

            # Validate each embedding vector (dimensions, finite values, mapping)
            for chunk_emb in bulk_res.successful_chunks:
                validate_embedding_vector(chunk_emb.vector, expected_dim=settings.embedding_dimension)

            # 11. Persist vector embeddings into pgvector / Supabase
            try:
                persist_res = await embedding_persistence_service.persist_chunk_embeddings(
                    user_id=user.user_id,
                    document_id=actual_doc_id,
                    embedded_chunks=bulk_res.successful_chunks,
                    scope=clean_scope,
                )
            except Exception as persist_exc:
                logger.error("Vector persistence error for document %s: %s", actual_doc_id, persist_exc)
                await supabase_service.update_document_status(actual_doc_id, "failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document uploaded and embedded, but vector persistence failed: {str(persist_exc)}",
                ) from persist_exc

            if persist_res.get("status") == "failed" or (
                persist_res.get("persisted_count", 0) == 0
                and persist_res.get("skipped_unchanged_count", 0) == 0
            ):
                err_detail = (
                    persist_res.get("failed_records", [{"error": "Persistence failure"}])[0].get("error", "Unknown persistence failure")
                    if persist_res.get("failed_records")
                    else "Vector persistence failed for chunks."
                )
                logger.error("Vector persistence failed for doc %s: %s", actual_doc_id, err_detail)
                await supabase_service.update_document_status(actual_doc_id, "failed")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Document uploaded and embedded, but vector persistence failed: {err_detail}",
                )

        # 12. Mark document completed only after both chunking and embedding persistence succeed
        await supabase_service.update_document_status(actual_doc_id, "completed")
        doc_record["processing_status"] = "completed"

        return DocumentUploadResponse(
            document=DocumentItem(**doc_record),
            total_pages=extracted_doc.total_pages,
            total_chunks=saved_chunk_count,
            status="success",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error persisting document: %s", exc)
        if "actual_doc_id" in locals():
            await supabase_service.update_document_status(actual_doc_id, "failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and store document: {str(exc)}",
        ) from exc


@router.get(
    "",
    response_model=List[DocumentItem],
    summary="List all documents owned by the authenticated student",
)
async def list_documents(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> List[DocumentItem]:
    docs = await supabase_service.list_user_documents(user_id=user.user_id)
    return [DocumentItem(**d) for d in docs]


@router.get(
    "/{document_id}/download",
    response_model=DocumentDownloadResponse,
    summary="Get authorized signed URL to download student's own PDF",
)
async def get_document_download_url(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> DocumentDownloadResponse:
    doc = await supabase_service.get_user_document(user_id=user.user_id, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied.",
        )

    signed_url = await supabase_service.create_signed_download_url(
        user_id=user.user_id,
        storage_path=doc["storage_path"],
        expires_in=3600,
    )

    return DocumentDownloadResponse(
        document_id=document_id,
        filename=doc["filename"],
        signed_url=signed_url,
        expires_in_seconds=3600,
    )


@router.delete(
    "/{document_id}",
    summary="Delete a student's personal document",
    status_code=status.HTTP_200_OK,
)
async def delete_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Permanently delete a student's personal document, its chunks, and its storage file."""
    success = await supabase_service.delete_user_document(user_id=user.user_id, document_id=document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found, access denied, or already deleted.",
        )
    return {"status": "success", "message": "Document deleted successfully."}


@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic similarity search across student-accessible documents",
    description="Embeds query with gemini-embedding-2 (RETRIEVAL_QUERY) and retrieves closest chunks via pgvector cosine distance.",
)
async def search_documents_endpoint(
    request: SemanticSearchRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    search_service: SemanticSearchService = Depends(get_semantic_search_service),
) -> SemanticSearchResponse:
    """Execute authenticated semantic similarity search for student documents."""
    try:
        return await search_service.search(
            user_id=user.user_id,
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_id=request.document_id,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except PermissionError as perm_err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(perm_err),
        )
    except Exception as exc:
        logger.error("Error executing semantic search for user %s: %s", user.user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute semantic similarity search across documents.",
        )


# =============================================================================
# In-Memory Stateless Endpoints (Phase 3.1 & 3.2 Compatibility)
# =============================================================================

@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
    summary="Extract page-by-page text from an uploaded PDF document (Stateless / in-memory)",
)
async def extract_document_text(
    file: UploadFile = File(..., description="PDF document to parse"),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExtractionResponse:
    return await document_service.extract_text_from_pdf(file)


@router.post(
    "/chunk",
    response_model=ChunkedDocumentResponse,
    summary="Extract, clean, and chunk text from an uploaded PDF document (Stateless / in-memory)",
)
async def chunk_document(
    file: UploadFile = File(..., description="PDF document to chunk"),
    target_tokens: Optional[int] = Query(None, description="Optional custom target chunk size in tokens (default: 500)"),
    overlap_tokens: Optional[int] = Query(None, description="Optional custom overlap size in tokens (default: 75)"),
    document_service: DocumentService = Depends(get_document_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
) -> ChunkedDocumentResponse:
    extracted_doc = await document_service.extract_text_from_pdf(file)
    return chunking_service.chunk_document(
        extracted_doc=extracted_doc,
        target_tokens=target_tokens,
        overlap_tokens=overlap_tokens,
    )
