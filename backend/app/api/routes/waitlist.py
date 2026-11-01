"""Waitlist submission API route for CampusPilot AI.

Enables prospective students and academic visitors to register for early access.
Submissions are stored privately in Supabase PostgreSQL without creating
Supabase Auth accounts. Public read access is strictly denied.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.waitlist import WaitlistSubmissionRequest, WaitlistSubmissionResponse
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post(
    "",
    response_model=WaitlistSubmissionResponse,
    summary="Submit early access application to the CampusPilot AI waitlist",
    description=(
        "Public endpoint accepting applicant full name, valid email, and optional university. "
        "Validates email format, prevents duplicate registrations, and saves records securely in "
        "PostgreSQL. Does NOT create Supabase Auth accounts."
    ),
)
async def submit_waitlist_entry(
    request: WaitlistSubmissionRequest,
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> WaitlistSubmissionResponse:
    try:
        result = await supabase_service.add_to_waitlist(
            full_name=request.full_name,
            email=request.email,
            institution=request.institution,
        )
        return WaitlistSubmissionResponse(
            status=result["status"],
            message=result["message"],
            data=result.get("data"),
        )
    except Exception as exc:
        logger.error("Error processing waitlist application: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to submit waitlist application at this time. Please try again later.",
        ) from exc
