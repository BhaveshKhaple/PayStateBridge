"""
Recovery link service.
Creates one Razorpay Test Mode (or Fake) payment link from a valid RecoveryPermit.
Idempotent: repeated calls return the stored link without new provider call.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AuditEvent, RecoveryAction
from app.integrations.payment_provider import ProviderLinkResult
from app.schemas.payment import RecoveryPermit
from app.services.case_service import get_case
from app.services.permit_service import PermitDeniedError


def get_payment_provider():
    if settings.use_fake_provider:
        from app.integrations.fake_provider import FakePaymentProvider
        return FakePaymentProvider()
    from app.integrations.razorpay_provider import RazorpayTestModeProvider
    return RazorpayTestModeProvider()


async def create_recovery_link(
    db: AsyncSession,
    case_id: str,
    *,
    actor: str = "operator",
) -> ProviderLinkResult:
    """
    Create one recovery payment link for a FAILED case.
    Returns existing stored link if already created (idempotent).
    """
    case = await get_case(db, case_id)

    # Safety check — must still be FAILED
    if case.payment_state != "FAILED":
        raise PermitDeniedError(
            f"Cannot create recovery link: payment state is {case.payment_state!r}. "
            "Only FAILED payments may receive a recovery link."
        )

    # Find existing permit
    permit_result = await db.execute(
        select(RecoveryAction).where(
            RecoveryAction.case_id == case.id,
            RecoveryAction.action_kind == "RECOVERY_PERMIT",
        )
    )
    permit_action = permit_result.scalar_one_or_none()
    if not permit_action:
        raise PermitDeniedError(
            "No recovery permit found for this case. "
            "Issue a permit first via POST /v1/cases/{id}/recovery-permit."
        )

    # Check if link already exists (idempotency)
    link_result = await db.execute(
        select(RecoveryAction).where(
            RecoveryAction.case_id == case.id,
            RecoveryAction.action_kind == "RECOVERY_LINK",
        )
    )
    existing_link = link_result.scalar_one_or_none()
    if existing_link and existing_link.provider_link_id:
        # Return stored link without new provider call
        return ProviderLinkResult(
            provider=existing_link.status,
            link_id=existing_link.provider_link_id,
            short_url=f"https://rzp.io/stored/{existing_link.provider_link_id}",
            amount_paise=case.order.amount_paise,
            status="created",
            idempotency_key=permit_action.idempotency_key,
            expires_at=permit_action.expires_at,
            environment="test",
            test_mode_label="TEST MODE — existing link returned (idempotent)",
        )

    # Build permit object
    permit = RecoveryPermit(
        case_id=uuid.UUID(case.id),
        original_payment_id=case.original_payment_reference or "unknown",
        order_id=case.order_id,
        amount_paise=case.order.amount_paise,
        idempotency_key=permit_action.idempotency_key,
        expires_at=permit_action.expires_at,
        environment="test",
    )

    # Call provider
    provider = get_payment_provider()
    link = await provider.create_recovery_link(permit=permit)

    # Store link record — use link_ prefix to avoid unique constraint collision with permit key
    link_action = RecoveryAction(
        case_id=case.id,
        action_kind="RECOVERY_LINK",
        idempotency_key="link:" + link.idempotency_key,
        provider_link_id=link.link_id,
        status=link.provider,
        expires_at=link.expires_at,
    )
    db.add(link_action)

    # Transition state
    prior_state = case.state
    case.state = "RECOVERY_LINK_CREATED"

    audit = AuditEvent(
        case_id=case.id,
        event_type="RECOVERY_LINK_CREATED",
        actor=actor,
        prior_state=prior_state,
        new_state="RECOVERY_LINK_CREATED",
        action="CREATE_RECOVERY_LINK",
        reason_codes=["PERMIT_VALID", "PAYMENT_FAILED"],
        evidence_ids=[link.link_id],
        customer_message=(
            f"Here is your recovery payment link ({link.test_mode_label}). "
            "This link expires in 60 minutes. Please use it to complete your order."
        ),
    )
    db.add(audit)
    case.customer_message = audit.customer_message
    await db.commit()

    return link


async def apply_webhook_paid(
    db: AsyncSession,
    case_id: str,
    *,
    link_id: str,
    payment_id: str,
    actor: str = "webhook",
) -> dict:
    """Apply a verified 'payment_link.paid' webhook event to a case."""
    case = await get_case(db, case_id)

    if case.state not in ("RECOVERY_LINK_CREATED", "RECOVERY_PERMIT_ISSUED"):
        return {"applied": False, "reason": f"Case not in expected state: {case.state}"}

    prior_state = case.state
    case.state = "RECOVERY_PAID_TEST"

    audit = AuditEvent(
        case_id=case.id,
        event_type="RECOVERY_PAID_TEST",
        actor=actor,
        prior_state=prior_state,
        new_state="RECOVERY_PAID_TEST",
        action="RECOVERY_LINK_PAID",
        reason_codes=["WEBHOOK_VERIFIED", "PAYMENT_LINK_PAID"],
        evidence_ids=[link_id, payment_id],
        customer_message="Your payment has been confirmed via the recovery link. Order is now complete.",
    )
    db.add(audit)
    case.customer_message = audit.customer_message
    await db.commit()

    return {
        "applied": True,
        "new_state": "RECOVERY_PAID_TEST",
        "link_id": link_id,
        "payment_id": payment_id,
    }
