"""Schemas for administrative dashboard and student management APIs."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field


class PlatformMetricsResponse(BaseModel):
    """Aggregate statistics for the administrative dashboard."""
    total_students: int
    active_subscriptions: int
    expired_subscriptions: int
    total_documents: int
    total_payments_inr: float
    total_transactions_count: int


class AdminStudentItem(BaseModel):
    """Student account item for admin management tables."""
    id: str
    email: str
    full_name: str
    institution: Optional[str] = None
    role: str
    status: str
    credits_balance: int
    plan: str
    subscription_status: str
    subscription_expiry: Optional[str] = None
    created_at: Optional[str] = None


class CreateStudentAccountRequest(BaseModel):
    """Payload to create an invite-only student account."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Initial student temporary password")
    full_name: str = Field(..., min_length=2, max_length=100)
    institution: Optional[str] = Field(None, max_length=150)
    role: Literal["student", "admin"] = "student"


class UpdateStudentStatusRequest(BaseModel):
    """Payload to alter student account state."""
    status: Literal["active", "suspended", "deactivated"]


class AdminAssignPlanRequest(BaseModel):
    """Payload to grant or adjust student plan administratively."""
    plan: Literal["monthly", "yearly"]
    days: int = Field(..., ge=1, le=3650, description="Duration in days to grant access")
    reason: str = Field(..., min_length=3, description="Audit reason for manual assignment")


class UpdateWaitlistStatusRequest(BaseModel):
    """Payload to update waitlist entry state."""
    status: Literal["pending", "approved", "rejected", "contacted"]


class WaitlistAdminItem(BaseModel):
    """Waitlist application item with management attributes."""
    id: str
    full_name: str
    email: str
    institution: Optional[str] = None
    status: str
    created_at: str
