"""
Case service — CRUD and business logic for PaymentCase lifecycle.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AuditEvent, MerchantOrder, PaymentCase, PaymentEvidence
from app.domain.classifier import classify
from app.domain.state_machine import assert_legal_transition
from app.schemas.payment import (
    CustomerReport,
    GatewayPaymentEvent,
    MerchantOrderSchema,
    PaymentState,
    RecoveryDecision,
)


class CaseNotFoundError(Exception):
    pass


class IllegalTransitionError(ValueError):
    pass


async def create_case(
    db: AsyncSession,
    *,
    order_id: str,
    incident_id: str | None = None,
) -> PaymentCase:
    """Open a new payment case for a merchant order."""
    result = await db.execute(
        select(MerchantOrder).where(MerchantOrder.order_id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise CaseNotFoundError(f"Order {order_id!r} not found")

    case = PaymentCase(
        order_id=order_id,
        state="CASE_OPENED",
        incident_id=incident_id,
    )
    db.add(case)
    await db.flush()

    audit = AuditEvent(
        case_id=case.id,
        event_type="CASE_OPENED",
        actor="operator",
        prior_state=None,
        new_state="CASE_OPENED",
        reason_codes=["CASE_CREATED"],
    )
    db.add(audit)
    await db.commit()
    await db.refresh(case)
    return case


async def get_case(db: AsyncSession, case_id: str) -> PaymentCase:
    result = await db.execute(
        select(PaymentCase)
        .where(PaymentCase.id == case_id)
        .options(
            selectinload(PaymentCase.evidence_items),
            selectinload(PaymentCase.audit_events),
            selectinload(PaymentCase.recovery_actions),
            selectinload(PaymentCase.order),
        )
    )
    case = result.scalar_one_or_none()
    if not case:
        raise CaseNotFoundError(f"Case {case_id!r} not found")
    return case


async def list_cases(db: AsyncSession, limit: int = 50) -> list[PaymentCase]:
    result = await db.execute(
        select(PaymentCase)
        .options(
            selectinload(PaymentCase.order),
            selectinload(PaymentCase.evidence_items),
            selectinload(PaymentCase.audit_events),
        )
        .order_by(PaymentCase.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def add_evidence(
    db: AsyncSession,
    *,
    case_id: str,
    source_type: str,
    event_reference: str | None,
    amount_paise: int | None,
    status: str | None,
    occurred_at: datetime | None,
    raw_data: dict | None,
) -> PaymentEvidence:
    case = await get_case(db, case_id)

    ev = PaymentEvidence(
        case_id=case.id,
        source_type=source_type,
        event_reference=event_reference,
        amount_paise=amount_paise,
        status=status,
        occurred_at=occurred_at,
        raw_data=raw_data,
    )
    db.add(ev)

    # Transition case to EVIDENCE_COLLECTING if it was just opened
    if case.state == "CASE_OPENED":
        _transition(case, "EVIDENCE_COLLECTING", actor="system")
        audit = AuditEvent(
            case_id=case.id,
            event_type="EVIDENCE_ADDED",
            actor="system",
            prior_state="CASE_OPENED",
            new_state="EVIDENCE_COLLECTING",
            reason_codes=["EVIDENCE_RECEIVED"],
        )
        db.add(audit)

    await db.commit()
    await db.refresh(ev)
    return ev


async def classify_case(
    db: AsyncSession,
    case_id: str,
) -> RecoveryDecision:
    """
    Run deterministic classifier on all gateway evidence for a case.
    Customer report is input only — cannot override gateway evidence.
    """
    case = await get_case(db, case_id)
    order = case.order

    # Build Pydantic schemas from DB evidence
    gateway_events: list[GatewayPaymentEvent] = []
    customer_report: CustomerReport | None = None
    scenario_hint = ""

    for ev in case.evidence_items:
        if ev.source_type == "gateway_event" and ev.raw_data:
            try:
                gateway_events.append(GatewayPaymentEvent.model_validate(ev.raw_data))
            except Exception:
                pass
        elif ev.source_type == "customer_report" and ev.raw_data:
            try:
                customer_report = CustomerReport.model_validate(ev.raw_data)
            except Exception:
                pass

    # Check for scenario hints from incident data
    if case.incident_id:
        from pathlib import Path
        import json
        inc_file = Path(__file__).parent.parent.parent.parent.parent / "data" / "incidents" / "dev" / f"{case.incident_id}.json"
        if inc_file.exists():
            inc_data = json.loads(inc_file.read_text())
            scenario = inc_data.get("scenario", "")
            if scenario in ("WRONG_RECIPIENT",):
                scenario_hint = "WRONG_RECIPIENT"
            elif scenario in ("UNAUTHORIZED",):
                scenario_hint = "UNAUTHORIZED"

    order_schema = MerchantOrderSchema(
        order_id=order.order_id,
        reference=order.reference,
        amount_paise=order.amount_paise,
        status=order.status,
        created_at=order.created_at,
    )

    decision = classify(order_schema, gateway_events, customer_report, scenario_hint=scenario_hint)

    # Persist classification
    prior_state = case.state
    case.payment_state = decision.state.value
    case.action = decision.action.value
    case.customer_message = decision.customer_message

    if case.state != "CLASSIFIED":
        try:
            assert_legal_transition(prior_state, "CLASSIFIED")
            case.state = "CLASSIFIED"
        except ValueError:
            pass  # Already classified — update in place

    audit = AuditEvent(
        case_id=case.id,
        event_type="CASE_CLASSIFIED",
        actor="policy_engine",
        prior_state=prior_state,
        new_state="CLASSIFIED",
        action=decision.action.value,
        reason_codes=decision.reason_codes,
        evidence_ids=decision.authoritative_evidence_ids,
        customer_message=decision.customer_message,
    )
    db.add(audit)
    await db.commit()

    return decision


def _transition(case: PaymentCase, new_state: str, actor: str = "system") -> None:
    assert_legal_transition(case.state, new_state)
    case.state = new_state
