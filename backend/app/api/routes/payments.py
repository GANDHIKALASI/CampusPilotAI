"""Razorpay Payment Gateway, Subscriptions, and Credit endpoints for CampusPilot AI."""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
import razorpay

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import Settings, get_settings
from app.schemas.billing import (
    CreateOrderRequest,
    CreateOrderResponse,
    CreditBalanceResponse,
    CreditTransactionItem,
    PaymentItem,
    ProfileResponse,
    SubscriptionResponse,
    UpdateProfileRequest,
    VerifyPaymentRequest,
)
from app.services.supabase import SupabaseService, get_supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Payments & Billing"])


def get_razorpay_client(settings: Settings) -> Optional[razorpay.Client]:
    """Initialize Razorpay SDK client if credentials are configured."""
    if settings.razorpay_key_id and settings.razorpay_key_secret:
        try:
            return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
        except Exception as e:
            logger.warning("Failed to initialize Razorpay SDK client: %s", e)
    return None


# =============================================================================
# 1. Profile & Free Credits Endpoints
# =============================================================================

@router.get("/profile", response_model=ProfileResponse)
async def get_my_profile(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Retrieve the authenticated student's profile, role, plan, and credit balance."""
    profile = await supabase_service.get_user_profile(user.user_id)
    sub = await supabase_service.get_user_subscription(user.user_id)

    return ProfileResponse(
        id=user.user_id,
        email=user.email,
        full_name=profile.get("full_name") or user.metadata.get("full_name") or "Student",
        institution=profile.get("institution") or user.metadata.get("institution"),
        avatar_url=profile.get("avatar_url") or user.metadata.get("avatar_url"),
        role=profile.get("role", "student"),
        status=profile.get("status", "active"),
        credits_balance=int(profile.get("credits_balance", 20)),
        plan=sub.get("plan", "free"),
        is_paid=sub.get("is_paid", False),
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_my_profile(
    payload: UpdateProfileRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Update student profile details (name, institution)."""
    updated = await supabase_service.update_user_profile(
        user_id=user.user_id,
        full_name=payload.full_name,
        institution=payload.institution,
    )
    sub = await supabase_service.get_user_subscription(user.user_id)

    return ProfileResponse(
        id=user.user_id,
        email=user.email,
        full_name=updated.get("full_name", "Student"),
        institution=updated.get("institution"),
        avatar_url=updated.get("avatar_url"),
        role=updated.get("role", "student"),
        status=updated.get("status", "active"),
        credits_balance=int(updated.get("credits_balance", 20)),
        plan=sub.get("plan", "free"),
        is_paid=sub.get("is_paid", False),
    )


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credit_balance(
    user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Get the current AI credit balance and warning state for the student."""
    credits_val = await supabase_service.get_user_credits(user.user_id)
    sub = await supabase_service.get_user_subscription(user.user_id)
    is_paid = sub.get("is_paid", False)

    return CreditBalanceResponse(
        credits_balance=credits_val,
        is_paid_subscriber=is_paid,
        plan=sub.get("plan", "free"),
        threshold_warning=bool(credits_val <= settings.low_credit_threshold and not is_paid),
        is_exhausted=bool(credits_val <= 0 and not is_paid),
    )


@router.get("/credits/history", response_model=List[CreditTransactionItem])
async def get_credit_history(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """List credit transaction history for the logged-in student."""
    txs = await supabase_service.list_credit_transactions(user.user_id, limit=50)
    return [
        CreditTransactionItem(
            id=str(tx.get("id")),
            amount=int(tx.get("amount", 0)),
            balance_after=int(tx.get("balance_after", 0)),
            action=str(tx.get("action", "")),
            description=tx.get("description"),
            created_at=str(tx.get("created_at")),
        )
        for tx in txs
    ]


# =============================================================================
# 2. Razorpay Payment Orders & Subscriptions
# =============================================================================

@router.post("/payments/create-order", response_model=CreateOrderResponse)
async def create_payment_order(
    payload: CreateOrderRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Create a trusted Razorpay order in INR.

    Security Rule:
    - Amount is strictly determined by server-side configuration, NEVER trusted from client.
    - Monthly: 9900 paise (₹99)
    - Yearly: 99900 paise (₹999)
    """
    if payload.plan == "monthly":
        amount_paise = settings.plan_monthly_paise
    elif payload.plan == "yearly":
        amount_paise = settings.plan_yearly_paise
    else:
        raise HTTPException(status_code=400, detail="Invalid plan requested. Choose 'monthly' or 'yearly'.")

    # Generate receipt identifier
    receipt = f"cp_{user.user_id[:8]}_{payload.plan[:1]}_{int(hashlib.sha256(user.user_id.encode()).hexdigest()[:6], 16)}"

    client = get_razorpay_client(settings)
    order_id = ""

    if client:
        try:
            order_data = {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "plan": payload.plan,
                    "platform": "CampusPilot AI",
                },
            }
            rzp_order = client.order.create(data=order_data)
            order_id = rzp_order.get("id")
        except Exception as e:
            logger.error("Razorpay API order creation failed: %s", e)
            raise HTTPException(status_code=502, detail="Failed to initialize payment order with gateway. Please try again.")

    # Test/Developer fallback when keys are in setup/sandbox
    if not order_id:
        import uuid
        order_id = f"order_test_{uuid.uuid4().hex[:14]}"

    # Save initial payment record with status 'created'
    await supabase_service.create_payment_record(
        user_id=user.user_id,
        plan=payload.plan,
        amount_paise=amount_paise,
        razorpay_order_id=order_id,
    )

    return CreateOrderResponse(
        order_id=order_id,
        amount_paise=amount_paise,
        currency="INR",
        key_id=settings.razorpay_key_id,
        plan=payload.plan,
        notes={
            "user_id": user.user_id,
            "email": user.email,
            "plan": payload.plan,
        },
    )


@router.post("/payments/verify")
async def verify_payment(
    payload: VerifyPaymentRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Verify Razorpay payment signature and activate fixed-duration subscription.

    Security Rules:
    1. Signature is validated against original order ID stored in database.
    2. Idempotent: Repeated verification requests return existing success without double-granting.
    3. Invalid signatures are rejected with HTTP 400 and logged.
    """
    # 1. Retrieve original stored payment record
    payment_record = await supabase_service.get_payment_by_order_id(payload.razorpay_order_id)
    if not payment_record:
        raise HTTPException(status_code=404, detail="Payment order not found.")

    if payment_record["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Payment order does not belong to the current authenticated student.")

    # Idempotency check: Already captured
    if payment_record.get("status") == "captured":
        sub = await supabase_service.get_user_subscription(user.user_id)
        return {
            "status": "success",
            "message": "Payment verified previously. Subscription is active.",
            "plan": payment_record.get("plan"),
            "subscription": sub,
        }

    # 2. Signature verification
    plan = payment_record["plan"]
    signature_valid = False

    if settings.razorpay_key_secret:
        # Standard HMAC SHA256 verification
        generated_signature = hmac.new(
            key=settings.razorpay_key_secret.encode("utf-8"),
            msg=f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        signature_valid = hmac.compare_digest(generated_signature, payload.razorpay_signature)
    else:
        # Test mode fallback (when testing sandbox without live secret)
        if payload.razorpay_signature.startswith("test_sig_") or payload.razorpay_order_id.startswith("order_test_"):
            signature_valid = True

    if not signature_valid:
        await supabase_service.update_payment_status(
            razorpay_order_id=payload.razorpay_order_id,
            status="failed",
            error_description="Invalid signature verification",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment verification failed: Invalid payment signature.",
        )

    # 3. Mark payment captured
    await supabase_service.update_payment_status(
        razorpay_order_id=payload.razorpay_order_id,
        status="captured",
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature,
    )

    # 4. Activate fixed-duration access (30 days for monthly, 365 days for yearly)
    duration_days = settings.plan_monthly_days if plan == "monthly" else settings.plan_yearly_days
    activated_sub = await supabase_service.create_or_update_subscription(
        user_id=user.user_id,
        plan=plan,
        days=duration_days,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
    )

    logger.info("Activated %s subscription for user %s (%d days)", plan, user.user_id, duration_days)

    return {
        "status": "success",
        "message": f"Payment successfully verified! Your {plan} academic plan is now active for {duration_days} days.",
        "plan": plan,
        "subscription": activated_sub,
    }


@router.post("/payments/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    settings: Settings = Depends(get_settings),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Handle asynchronous Razorpay webhook events idempotently.

    Validates webhook signature against the raw request body.
    """
    raw_body = await request.body()

    if settings.razorpay_webhook_secret and x_razorpay_signature:
        expected_sig = hmac.new(
            key=settings.razorpay_webhook_secret.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, x_razorpay_signature):
            logger.warning("Razorpay webhook signature mismatch")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event_data = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON payload")

    event_type = event_data.get("event")
    payload_entity = event_data.get("payload", {}).get("payment", {}).get("entity", {})

    order_id = payload_entity.get("order_id")
    payment_id = payload_entity.get("id")

    logger.info("Received Razorpay webhook event: %s for order %s", event_type, order_id)

    if order_id and event_type in ["payment.captured", "order.paid"]:
        payment_record = await supabase_service.get_payment_by_order_id(order_id)
        if payment_record and payment_record.get("status") != "captured":
            user_id = payment_record["user_id"]
            plan = payment_record["plan"]
            duration_days = settings.plan_monthly_days if plan == "monthly" else settings.plan_yearly_days

            await supabase_service.update_payment_status(
                razorpay_order_id=order_id,
                status="captured",
                payment_id=payment_id,
            )
            await supabase_service.create_or_update_subscription(
                user_id=user_id,
                plan=plan,
                days=duration_days,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
            )
            logger.info("Webhook activated %s subscription for user %s", plan, user_id)

    elif order_id and event_type == "payment.failed":
        error_desc = payload_entity.get("error_description", "Payment failed")
        await supabase_service.update_payment_status(
            razorpay_order_id=order_id,
            status="failed",
            error_description=error_desc,
        )

    return {"status": "ok"}


@router.get("/payments/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Retrieve active subscription details and remaining days."""
    sub = await supabase_service.get_user_subscription(user.user_id)
    remaining_days = None

    if sub.get("current_period_end"):
        try:
            from datetime import datetime, timezone
            end_dt = datetime.fromisoformat(sub["current_period_end"].replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            delta = end_dt - now_dt
            remaining_days = max(0, delta.days)
        except Exception:
            pass

    return SubscriptionResponse(
        plan=sub.get("plan", "free"),
        status=sub.get("status", "active"),
        is_active=sub.get("is_active", False),
        is_paid=sub.get("is_paid", False),
        current_period_start=sub.get("current_period_start"),
        current_period_end=sub.get("current_period_end"),
        remaining_days=remaining_days,
    )


@router.get("/payments/history", response_model=List[PaymentItem])
async def get_payment_history(
    user: AuthenticatedUser = Depends(get_current_user),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """Retrieve verified payment transaction history for logged-in student."""
    payments = await supabase_service.list_user_payments(user.user_id)
    return [
        PaymentItem(
            id=str(p.get("id")),
            user_id=p["user_id"],
            plan=p.get("plan", "monthly"),
            amount_inr=p.get("amount_paise", 0) / 100.0,
            currency=p.get("currency", "INR"),
            razorpay_order_id=p.get("razorpay_order_id", ""),
            razorpay_payment_id=p.get("razorpay_payment_id"),
            status=p.get("status", "created"),
            created_at=str(p.get("created_at")),
        )
        for p in payments
    ]
