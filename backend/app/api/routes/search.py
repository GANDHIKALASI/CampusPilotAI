"""
API endpoints for semantic similarity search across academic documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.search import SemanticSearchRequest, SemanticSearchResponse
from app.services.semantic_search import SemanticSearchService, get_semantic_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post(
    "",
    response_model=SemanticSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic similarity search across academic documents",
    description=(
        "Accepts a student's natural-language question, embeds it via Gemini embedding service "
        "(gemini-embedding-2 with RETRIEVAL_QUERY), searches stored document embeddings in PostgreSQL "
        "via pgvector cosine distance, and returns ranked chunks respecting document access boundaries."
    ),
)
async def semantic_search_endpoint(
    request: SemanticSearchRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    search_service: SemanticSearchService = Depends(get_semantic_search_service),
) -> SemanticSearchResponse:
    """Execute an authenticated semantic similarity search for the verified student."""
    try:
        response = await search_service.search(
            user_id=user.user_id,
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_id=request.document_id,
        )
        return response
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
            detail="An unexpected error occurred while executing semantic similarity search.",
        )
