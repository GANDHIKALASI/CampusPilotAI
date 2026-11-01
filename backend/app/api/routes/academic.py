"""Academic curriculum and syllabus management endpoints for BCA Semester V and Semester VI."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import AuthenticatedUser, get_optional_current_user
from app.schemas.academic import (
    FullCurriculumResponse,
    SemesterItem,
    SubjectDetailResponse,
    SubjectItem,
)
from app.schemas.document import DocumentItem
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/academic", tags=["Academic Curriculum"])


@router.get(
    "/semesters",
    response_model=List[SemesterItem],
    summary="List available academic semesters",
    description="Returns metadata for Semester V and Semester VI.",
)
async def list_semesters(
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> List[SemesterItem]:
    """Retrieve top-level semester metadata."""
    semesters = await supabase_service.get_semesters()
    return [
        SemesterItem(
            id=s["id"],
            name=s["name"],
            code=s["code"],
            academic_year=s.get("academic_year", "3rd Year"),
            order_index=s.get("order_index", 1),
            description=s.get("description"),
            subjects=[],
        )
        for s in semesters
    ]


@router.get(
    "/curriculum",
    response_model=FullCurriculumResponse,
    summary="Get full academic curriculum for Semesters V and VI",
    description=(
        "Returns the complete hierarchical academic structure: "
        "Semesters -> Subjects -> Units (4 per theory subject), "
        "Practicals (Java Lab: 21, Algorithm Design Lab: 12), and Project Guidelines (Project Work-I)."
    ),
)
async def get_curriculum(
    user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> FullCurriculumResponse:
    """Retrieve the entire curriculum tree for Semester V and VI."""
    user_id = user.user_id if user else None
    curriculum_data = await supabase_service.get_full_curriculum(user_id=user_id)
    return FullCurriculumResponse(
        program="Bachelor of Computer Applications (BCA)",
        academic_system="Semester",
        semesters=curriculum_data,
    )


@router.get(
    "/subjects/{subject_id}",
    response_model=SubjectDetailResponse,
    summary="Get subject detail with units, practicals, project specs, and related documents",
    description="Returns deep subject view including 4 syllabus units, practical exercises, or capstone guidelines.",
)
async def get_subject_detail(
    subject_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> SubjectDetailResponse:
    """Retrieve full details for a single subject."""
    user_id = user.user_id if user else None
    subject = await supabase_service.get_subject_detail(subject_id=subject_id, user_id=user_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with identifier '{subject_id}' not found in curriculum.",
        )
    return SubjectDetailResponse(**subject)


@router.get(
    "/subjects/{subject_id}/documents",
    response_model=List[DocumentItem],
    summary="List uploaded academic documents for a specific subject",
    description="Returns personal student documents or shared library documents tagged with this subject.",
)
async def list_subject_documents(
    subject_id: str,
    user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
) -> List[DocumentItem]:
    """Retrieve documents associated with a subject."""
    user_id = user.user_id if user else None
    docs = await supabase_service.list_subject_documents(subject_id=subject_id, user_id=user_id)
    return [
        DocumentItem(
            id=d["id"],
            user_id=d.get("user_id", ""),
            filename=d.get("filename", ""),
            storage_path=d.get("storage_path", ""),
            mime_type=d.get("mime_type", "application/pdf"),
            file_size=d.get("file_size", 0),
            processing_status=d.get("processing_status", "completed"),
            scope=d.get("scope", "personal"),
            semester_id=d.get("semester_id"),
            subject_id=d.get("subject_id"),
            unit_id=d.get("unit_id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )
        for d in docs
    ]
