"""
Razorpay webhook handler.
Verifies HMAC on raw body before any parsing.
Deduplicates by event_id — same event processed only once.
Only applies legal state transitions.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import PaymentCase, RecoveryAction
from app.services.recovery_link_service import apply_webhook_paid, get_payment_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])

# In-memory dedup set (use DB table in production)
_processed_event_ids: set[str] = set()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw_body = await request.body()

    # Step 1: Verify HMAC signature on raw body FIRST
    provider = get_payment_provider()
    try:
        event = provider.verify_webhook(raw_body, x_razorpay_signature)
    except ValueError as e:
        logger.warning("Webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Step 2: Deduplicate by event_id
    if event.event_id in _processed_event_ids:
        return {"received": True, "status": "duplicate_ignored", "event_id": event.event_id}
    _processed_event_ids.add(event.event_id)

    # Step 3: Route by event type
    if event.event_type == "payment_link.paid" and event.payment_link_id:
        # Find case by recovery action's provider_link_id
        link_result = await db.execute(
            select(RecoveryAction).where(
                RecoveryAction.provider_link_id == event.payment_link_id,
                RecoveryAction.action_kind == "RECOVERY_LINK",
            )
        )
        link_action = link_result.scalar_one_or_none()

        if link_action:
            case_result = await db.execute(
                select(PaymentCase).where(PaymentCase.id == link_action.case_id)
            )
            case = case_result.scalar_one_or_none()
            if case:
                result = await apply_webhook_paid(
                    db,
                    case.id,
                    link_id=event.payment_link_id,
                    payment_id=event.payment_id or "",
                )
                return {"received": True, "applied": result["applied"], "event_id": event.event_id}

    return {"received": True, "status": "event_processed", "event_id": event.event_id}
