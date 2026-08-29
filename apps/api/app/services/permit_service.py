"""
Recovery permit service.
Issues a short-lived RecoveryPermit ONLY when original payment is conclusively FAILED.
All other states are blocked.
Idempotent: repeated requests return the existing permit.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent, PaymentCase, RecoveryAction
from app.domain.classifier import BLOCKED_STATES
from app.schemas.payment import PaymentState, RecoveryPermit
from app.services.case_service import CaseNotFoundError, get_case

PERMIT_EXPIRY_MINUTES = 60
BLOCKED_PAYMENT_STATES = {s.value for s in BLOCKED_STATES} | {
    "CAPTURED_UNLINKED",
    "DUPLICATE_SUCCESS",
    "WRONG_RECIPIENT",
    "UNAUTHORIZED",
}


class PermitDeniedError(Exception):
    """Raised when a recovery permit cannot be issued for this case."""


def _make_idempotency_key(case_id: str, order_id: str, amount_paise: int) -> str:
    raw = f"permit:{case_id}:{order_id}:{amount_paise}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def issue_recovery_permit(
    db: AsyncSession,
    case_id: str,
    *,
    actor: str = "operator",
) -> RecoveryPermit:
    """
    Issue a RecoveryPermit for a FAILED payment case.
    Returns existing permit if one already exists (idempotent).
    """
    case = await get_case(db, case_id)

    # Enforce payment state safety
    if case.payment_state != PaymentState.FAILED.value:
        blocked = case.payment_state or "unknown"
        raise PermitDeniedError(
            f"Recovery permit denied: payment state is {blocked!r}. "
            "Permits are only issued for conclusively FAILED payments. "
            f"State {blocked!r} must not trigger a recovery link."
        )

    # Order must be unpaid
    if case.order.status in ("paid_reconciled", "paid"):
        raise PermitDeniedError(
            f"Order {case.order_id!r} is already paid. No recovery needed."
        )

    # Build stable idempotency key
    idem_key = _make_idempotency_key(case_id, case.order_id, case.order.amount_paise)

    # Check for existing permit (idempotency)
    existing = await db.execute(
        select(RecoveryAction).where(
            RecoveryAction.case_id == case.id,
            RecoveryAction.action_kind == "RECOVERY_PERMIT",
            RecoveryAction.idempotency_key == idem_key,
        )
    )
    existing_action = existing.scalar_one_or_none()
    if existing_action:
        # Return existing permit without creating a new one
        return RecoveryPermit(
            case_id=uuid.UUID(case.id),
            original_payment_id=case.original_payment_reference or "unknown",
            order_id=case.order_id,
            amount_paise=case.order.amount_paise,
            idempotency_key=idem_key,
            expires_at=existing_action.expires_at,
            environment="test",
        )

    # Create new permit record
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PERMIT_EXPIRY_MINUTES)

    action = RecoveryAction(
        case_id=case.id,
        action_kind="RECOVERY_PERMIT",
        idempotency_key=idem_key,
        status="issued",
        expires_at=expires_at,
    )
    db.add(action)

    # Transition lifecycle state
    prior_state = case.state
    case.state = "RECOVERY_PERMIT_ISSUED"

    audit = AuditEvent(
        case_id=case.id,
        event_type="RECOVERY_PERMIT_ISSUED",
        actor=actor,
        prior_state=prior_state,
        new_state="RECOVERY_PERMIT_ISSUED",
        action="CREATE_RECOVERY_PERMIT",
        reason_codes=["PAYMENT_CONCLUSIVELY_FAILED", "ORDER_UNPAID"],
        evidence_ids=[case.original_payment_reference or ""],
        customer_message=(
            "The first payment has been verified as failed. "
            "We are preparing one recovery link for you."
        ),
    )
    db.add(audit)

    await db.commit()

    return RecoveryPermit(
        case_id=uuid.UUID(case.id),
        original_payment_id=case.original_payment_reference or "unknown",
        order_id=case.order_id,
        amount_paise=case.order.amount_paise,
        idempotency_key=idem_key,
        expires_at=expires_at,
        environment="test",
    )
