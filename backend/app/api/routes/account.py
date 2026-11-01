import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthenticatedUser, get_current_user
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["Account"])


@router.delete(
    "/me",
    summary="Permanently delete authenticated user's account and all associated data",
    status_code=status.HTTP_200_OK,
)
async def delete_my_account(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Permanently delete the authenticated user's account.
    Purges user profile, personal documents, document chunks, storage PDFs,
    conversations, messages, credit balances, and subscriptions.
    """
    logger.info("Account deletion initiated by user %s (%s)", user.user_id, user.email)
    success = await supabase_service.delete_user_account(user_id=user.user_id)
    if not success:
        logger.error("Failed to delete account for user %s", user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please try again or contact campus support.",
        )
    return {
        "status": "success",
        "message": "Your account and all associated data have been permanently deleted.",
    }
