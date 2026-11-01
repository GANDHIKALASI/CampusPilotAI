"""Pydantic schemas for waitlist submissions in CampusPilot AI."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field


class WaitlistSubmissionRequest(BaseModel):
    """Payload for submitting an early access request."""

    full_name: str = Field(..., min_length=2, max_length=120, description="Full name of student or academic applicant")
    email: EmailStr = Field(..., description="Valid academic or personal email address")
    institution: Optional[str] = Field(default=None, max_length=200, description="Optional university or college name")


class WaitlistSubmissionResponse(BaseModel):
    """Response returned upon waitlist submission."""

    status: str = Field(..., description="Submission outcome status: success or already_registered")
    message: str = Field(..., description="User-facing status message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Created waitlist record details")
