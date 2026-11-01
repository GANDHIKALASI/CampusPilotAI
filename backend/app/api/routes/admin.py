"""Protected Administrative endpoints for CampusPilot AI.

Enforces server-side administrative verification. Students are strictly rejected with HTTP 403.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, get_current_admin_user
from app.schemas.admin import (
    AdminAssignPlanRequest,
    AdminStudentItem,
    CreateStudentAccountRequest,
    PlatformMetricsResponse,
    UpdateStudentStatusRequest,
    UpdateWaitlistStatusRequest,
    WaitlistAdminItem,
)
from app.schemas.document import DocumentItem
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# =============================================================================
# 1. Platform Metrics Overview
# =============================================================================

@router.get("/metrics", response_model=PlatformMetricsResponse)
async def get_platform_metrics(
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Retrieve platform aggregate metrics (students, subscriptions, docs, payments)."""
    metrics = await supabase_service.get_platform_metrics()
    return PlatformMetricsResponse(**metrics)


# =============================================================================
# 2. Student Account Management
# =============================================================================

@router.get("/students", response_model=List[AdminStudentItem])
async def list_students(
    search: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """List students with their profile, subscription plan, and credit balance."""
    students = await supabase_service.list_students(search=search, limit=limit, offset=offset)
    return [AdminStudentItem(**s) for s in students]


@router.post("/students", response_model=AdminStudentItem)
async def create_student_account(
    payload: CreateStudentAccountRequest,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Create a new student account using Supabase Auth Admin API (service role).

    Guarantees:
    - Never exposes passwords or sensitive credentials in logs or audit records.
    - Automatically grants exactly 20 initial free AI credits.
    """
    try:
        created = await supabase_service.admin_create_student_account(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            institution=payload.institution,
            role=payload.role,
            admin_id=admin.user_id,
        )
        sub = await supabase_service.get_user_subscription(created["id"])
        return AdminStudentItem(
            id=created["id"],
            email=created["email"],
            full_name=created["full_name"],
            institution=created.get("institution"),
            role=created.get("role", "student"),
            status=created.get("status", "active"),
            credits_balance=created.get("credits_balance", 20),
            plan=sub.get("plan", "free"),
            subscription_status=sub.get("status", "active"),
            subscription_expiry=sub.get("current_period_end"),
            created_at=created.get("created_at"),
        )
    except Exception as e:
        logger.error("Admin account creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/students/{student_id}/status")
async def update_student_status(
    student_id: str,
    payload: UpdateStudentStatusRequest,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Activate, suspend, or deactivate a student account with audit logging."""
    return await supabase_service.update_student_status(
        student_id=student_id,
        status=payload.status,
        admin_id=admin.user_id,
    )


@router.post("/students/{student_id}/plan")
async def assign_student_plan(
    student_id: str,
    payload: AdminAssignPlanRequest,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Administratively grant or extend a student subscription with audit logging."""
    sub = await supabase_service.admin_assign_plan(
        student_id=student_id,
        plan=payload.plan,
        days=payload.days,
        admin_id=admin.user_id,
        reason=payload.reason,
    )
    return {
        "status": "success",
        "message": f"Successfully assigned {payload.plan} plan for {payload.days} days.",
        "subscription": sub,
    }


@router.delete("/students/{student_id}")
async def delete_student_account(
    student_id: str,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Permanently delete a student account and purge all associated records with audit logging."""
    success = await supabase_service.delete_user_account(student_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student account not found or could not be deleted.",
        )
    await supabase_service.record_admin_audit_log(
        admin_id=admin.user_id,
        action="delete_student_account",
        target_type="student",
        target_id=student_id,
    )
    return {
        "status": "success",
        "message": "Student account and all associated documents, conversations, and records permanently deleted.",
    }


# =============================================================================
# 3. Academic Shared Document Management
# =============================================================================

@router.get("/documents", response_model=List[DocumentItem])
async def list_shared_documents(
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """List all shared academic documents uploaded by administrators."""
    all_docs = await supabase_service.list_user_documents(admin.user_id)
    shared_docs = [d for d in all_docs if d.get("scope") == "shared"]
    return [
        DocumentItem(
            id=d["id"],
            filename=d["filename"],
            file_size=d["file_size"],
            mime_type=d["mime_type"],
            processing_status=d["processing_status"],
            scope=d.get("scope", "shared"),
            created_at=d["created_at"],
        )
        for d in shared_docs
    ]


@router.delete("/documents/{document_id}")
async def delete_shared_document(
    document_id: str,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Delete a shared academic PDF and its chunks with audit logging."""
    success = await supabase_service.delete_shared_document(document_id, admin_id=admin.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shared document not found or could not be deleted.")
    return {"status": "success", "message": "Shared document deleted successfully."}


# =============================================================================
# 4. Payments & Subscriptions Management
# =============================================================================

@router.get("/payments")
async def list_all_payments(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """View all platform transactions and payment statuses."""
    payments = await supabase_service.list_all_payments(limit=limit, offset=offset)
    return payments


@router.get("/subscriptions")
async def list_all_subscriptions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """View all student subscriptions and expiry dates."""
    subs = await supabase_service.list_all_subscriptions(limit=limit, offset=offset)
    return subs


@router.post("/subscriptions/resolve")
async def resolve_subscription_issue(
    student_id: str = Query(..., description="Target student ID"),
    plan: str = Query("monthly", description="Plan to grant ('monthly' or 'yearly')"),
    days: int = Query(30, ge=1, le=365, description="Days to grant"),
    reason: str = Query(..., min_length=3, description="Audit reason for resolution"),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Manually resolve a payment/subscription issue with audit record."""
    sub = await supabase_service.admin_assign_plan(
        student_id=student_id,
        plan=plan,
        days=days,
        admin_id=admin.user_id,
        reason=f"Manual resolution: {reason}",
    )
    return {
        "status": "success",
        "message": "Subscription resolved and activated with audit log.",
        "subscription": sub,
    }


# =============================================================================
# 5. Waitlist Triage
# =============================================================================

@router.get("/waitlist", response_model=List[WaitlistAdminItem])
async def list_waitlist_applications(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, contacted"),
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """List waitlist applications for administrative triage."""
    items = await supabase_service.list_waitlist(status_filter=status)
    return [
        WaitlistAdminItem(
            id=str(w.get("id")),
            full_name=w.get("full_name", ""),
            email=w.get("email", ""),
            institution=w.get("institution"),
            status=w.get("status", "pending"),
            created_at=str(w.get("created_at")),
        )
        for w in items
    ]


@router.patch("/waitlist/{entry_id}")
async def update_waitlist_status(
    entry_id: str,
    payload: UpdateWaitlistStatusRequest,
    admin: AuthenticatedUser = Depends(get_current_admin_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Update waitlist entry status (pending, approved, rejected, contacted) with audit log."""
    try:
        return await supabase_service.update_waitlist_status(
            entry_id=entry_id,
            status=payload.status,
            admin_id=admin.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
