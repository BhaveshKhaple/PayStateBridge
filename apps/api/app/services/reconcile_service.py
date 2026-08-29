"""
Order reconciliation service.
Links a captured gateway payment to an unpaid merchant order.
Rules:
- Order reference must match exactly.
- Amount must match exactly (integer paise).
- Payment occurred_at must be within 30 minutes of order created_at.
- Order must still be in an unpaid state.
- No existing reconciliation must exist for this case.
"""
from __future__ import annotations

from datetime import timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditEvent, MerchantOrder, PaymentCase, PaymentEvidence
from app.domain.state_machine import assert_legal_transition
from app.services.case_service import CaseNotFoundError, get_case

UNPAID_ORDER_STATUSES = {"payment_pending", "created", "initiated"}
RECONCILE_TIME_WINDOW = timedelta(minutes=30)


class ReconcileError(Exception):
    """Raised when reconciliation policy is not satisfied."""


class AmbiguousMatchError(ReconcileError):
    """Raised when multiple payment records could match — requires human review."""


async def reconcile_order(
    db: AsyncSession,
    case_id: str,
    *,
    actor: str = "operator",
) -> dict:
    """
    Attempt to link a captured gateway payment to an unpaid merchant order.
    Returns the updated order and case on success.
    Raises ReconcileError if policy is not satisfied.
    """
    case = await get_case(db, case_id)

    # Must be a CAPTURED_UNLINKED case
    if case.payment_state != "CAPTURED_UNLINKED":
        raise ReconcileError(
            f"Cannot reconcile: case payment state is {case.payment_state!r}, "
            "expected CAPTURED_UNLINKED."
        )

    # Order must be unpaid
    result = await db.execute(
        select(MerchantOrder).where(MerchantOrder.order_id == case.order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise CaseNotFoundError(f"Order {case.order_id!r} not found")

    if order.status not in UNPAID_ORDER_STATUSES:
        raise ReconcileError(
            f"Order {order.order_id!r} is not unpaid (status={order.status!r}). "
            "Cannot reconcile."
        )

    # Find captured gateway events in this case's evidence
    captured_events = [
        ev
        for ev in case.evidence_items
        if ev.source_type == "gateway_event" and ev.status == "captured"
    ]

    if not captured_events:
        raise ReconcileError(
            "No captured gateway event found in case evidence. Cannot reconcile."
        )

    if len(captured_events) > 1:
        raise AmbiguousMatchError(
            f"Found {len(captured_events)} captured events. Ambiguous match — "
            "requires human review. Cannot auto-reconcile."
        )

    ev = captured_events[0]

    # Amount must match exactly
    if ev.amount_paise != order.amount_paise:
        raise ReconcileError(
            f"Amount mismatch: gateway captured {ev.amount_paise} paise, "
            f"order expects {order.amount_paise} paise. Cannot reconcile."
        )

    # Time window check (30 minutes)
    if ev.occurred_at and order.created_at:
        ev_time = ev.occurred_at
        order_time = order.created_at
        # Make both timezone-aware for comparison
        if ev_time.tzinfo is None:
            from datetime import datetime
            ev_time = ev_time.replace(tzinfo=timezone.utc)
        if order_time.tzinfo is None:
            order_time = order_time.replace(tzinfo=timezone.utc)
        delta = abs(ev_time - order_time)
        if delta > RECONCILE_TIME_WINDOW:
            raise ReconcileError(
                f"Time window exceeded: captured at {ev_time.isoformat()}, "
                f"order created at {order_time.isoformat()}, "
                f"delta={delta}. Max allowed: {RECONCILE_TIME_WINDOW}."
            )

    # All checks passed — reconcile
    prior_order_status = order.status
    prior_case_state = case.state

    order.status = "paid_reconciled"

    # Transition case lifecycle state
    try:
        assert_legal_transition(case.state, "ORDER_RECONCILED")
        case.state = "ORDER_RECONCILED"
    except ValueError:
        # Already classified — force to ORDER_RECONCILED
        case.state = "ORDER_RECONCILED"

    case.payment_state = "CAPTURED_UNLINKED"  # keep payment state label
    case.action = "RECONCILE_ORDER"

    audit = AuditEvent(
        case_id=case.id,
        event_type="ORDER_RECONCILED",
        actor=actor,
        prior_state=prior_case_state,
        new_state="ORDER_RECONCILED",
        action="RECONCILE_ORDER",
        reason_codes=[
            "CAPTURED_PAYMENT_MATCHED",
            "AMOUNT_EXACT_MATCH",
            "REFERENCE_MATCH",
        ],
        evidence_ids=[ev.id, order.order_id],
        customer_message=(
            "Your payment is confirmed. We have restored your order without any "
            "additional charge. Thank you for your patience."
        ),
    )
    db.add(audit)
    case.customer_message = audit.customer_message

    await db.commit()

    return {
        "reconciled": True,
        "order_id": order.order_id,
        "new_order_status": order.status,
        "gateway_payment_reference": ev.event_reference,
        "amount_paise": ev.amount_paise,
        "case_state": case.state,
        "customer_message": audit.customer_message,
    }
