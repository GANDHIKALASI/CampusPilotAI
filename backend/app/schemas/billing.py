"""Schemas for Razorpay billing, subscriptions, and AI credits."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    """Request to generate a trusted Razorpay order."""
    plan: Literal["monthly", "yearly"] = Field(
        ..., description="Target plan ('monthly' or 'yearly')"
    )


class CreateOrderResponse(BaseModel):
    """Details returned to frontend to initiate Razorpay Standard Checkout."""
    order_id: str
    amount_paise: int
    currency: str = "INR"
    key_id: str
    plan: str
    notes: dict = Field(default_factory=dict)


class VerifyPaymentRequest(BaseModel):
    """Verification payload submitted after Razorpay checkout completion."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentItem(BaseModel):
    """Representation of a verified payment transaction."""
    id: str
    user_id: str
    plan: str
    amount_inr: float
    currency: str = "INR"
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: str
    created_at: str


class SubscriptionResponse(BaseModel):
    """Active subscription status for a student."""
    plan: str
    status: str
    is_active: bool
    is_paid: bool
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    remaining_days: Optional[int] = None


class CreditBalanceResponse(BaseModel):
    """Student free credit balance status."""
    credits_balance: int
    is_paid_subscriber: bool
    plan: str
    threshold_warning: bool
    is_exhausted: bool


class CreditTransactionItem(BaseModel):
    """Audit log entry of a credit change."""
    id: str
    amount: int
    balance_after: int
    action: str
    description: Optional[str] = None
    created_at: str


class ProfileResponse(BaseModel):
    """Student profile attributes."""
    id: str
    email: str
    full_name: str
    institution: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    status: str
    credits_balance: int
    plan: str
    is_paid: bool


class UpdateProfileRequest(BaseModel):
    """Payload to update student profile attributes."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    institution: Optional[str] = Field(None, max_length=150)
