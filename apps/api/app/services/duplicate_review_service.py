"""
Duplicate-success review service.
Opens a human review case when two captured payments map to one intended order.
Does NOT execute a refund — merchant approval is required.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent, MerchantOrder, PaymentCase, PaymentEvidence
from app.services.case_service import CaseNotFoundError, get_case


class DuplicateReviewError(Exception):
    pass


async def open_duplicate_review(
    db: AsyncSession,
    case_id: str,
    *,
    actor: str = "operator",
) -> dict:
    """
    Open a duplicate-success review for a case.
    Records both captured payment IDs and amounts in the audit trail.
    Never calls any refund provider.
    """
    case = await get_case(db, case_id)

    if case.payment_state != "DUPLICATE_SUCCESS":
        raise DuplicateReviewError(
            f"Cannot open duplicate review: payment state is {case.payment_state!r}, "
            "expected DUPLICATE_SUCCESS."
        )

    if case.state == "DUPLICATE_REVIEW_OPEN":
        raise DuplicateReviewError("Duplicate review is already open for this case.")

    # Collect all captured payment events
    captured = [
        ev
        for ev in case.evidence_items
        if ev.source_type == "gateway_event" and ev.status == "captured"
    ]

    payment_ids = [ev.event_reference for ev in captured]
    amounts = [ev.amount_paise for ev in captured]

    prior_state = case.state
    case.state = "DUPLICATE_REVIEW_OPEN"

    audit = AuditEvent(
        case_id=case.id,
        event_type="DUPLICATE_REVIEW_OPENED",
        actor=actor,
        prior_state=prior_state,
        new_state="DUPLICATE_REVIEW_OPEN",
        action="OPEN_DUPLICATE_REVIEW",
        reason_codes=["MULTIPLE_CAPTURED_EVENTS", "HUMAN_REVIEW_REQUIRED"],
        evidence_ids=[ev.id for ev in captured],
        customer_message=(
            "We found two completed payments for the same order. "
            "Our team is reviewing the duplicate. "
            "Please do not pay again — we will contact you with the resolution."
        ),
    )
    db.add(audit)
    case.customer_message = audit.customer_message

    await db.commit()

    return {
        "review_opened": True,
        "case_id": case.id,
        "order_id": case.order_id,
        "captured_payment_ids": payment_ids,
        "captured_amounts_paise": amounts,
        "case_state": case.state,
        "note": "No automatic refund. Merchant approval required before any refund action.",
        "customer_message": audit.customer_message,
    }


async def record_review_decision(
    db: AsyncSession,
    case_id: str,
    *,
    decision: str,
    actor: str = "operator",
    notes: str = "",
) -> dict:
    """
    Record the operator's approve/reject decision for a duplicate review.
    Does NOT call any refund provider in v0.
    """
    case = await get_case(db, case_id)

    if case.state != "DUPLICATE_REVIEW_OPEN":
        raise DuplicateReviewError(
            f"Case is not in DUPLICATE_REVIEW_OPEN state (current: {case.state!r})."
        )

    if decision not in ("approve_refund_review", "reject"):
        raise DuplicateReviewError(
            f"Invalid decision {decision!r}. Must be 'approve_refund_review' or 'reject'."
        )

    audit = AuditEvent(
        case_id=case.id,
        event_type="DUPLICATE_REVIEW_DECISION",
        actor=actor,
        prior_state=case.state,
        new_state=case.state,
        action=decision.upper(),
        reason_codes=["OPERATOR_DECISION"],
        customer_message=(
            "Your duplicate payment case has been reviewed. "
            "Our team will process the refund through the official merchant channel."
            if decision == "approve_refund_review"
            else "Your duplicate payment review has been closed."
        ),
    )
    if notes:
        audit.reason_codes = (audit.reason_codes or []) + [f"NOTE:{notes[:100]}"]
    db.add(audit)

    await db.commit()

    return {
        "decision_recorded": True,
        "decision": decision,
        "case_id": case.id,
        "note": "v0: no live refund API called. Merchant must process refund manually.",
    }
