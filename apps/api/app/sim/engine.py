"""
Deterministic simulator engine for PayState World.
Produces a timeline of events and runs gateway events through the
REAL classifier (app.domain.classifier). No fake agent logic here.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.domain.classifier import classify
from app.schemas.payment import (
    CustomerReport,
    GatewayPaymentEvent,
    MerchantOrderSchema,
)
from app.sim.schemas import SimEventType, SimStory


def _base_time() -> datetime:
    return datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc)


def run_story_classifier(story: SimStory) -> dict:
    """
    Reconstruct the order + gateway events from a story's events and run the
    REAL classifier. Returns the decision so the sim can emit AGENT_DECISION.
    This is the integrity guarantee: the sim feeds the real policy engine.
    """
    order = None
    gateway_events: list[GatewayPaymentEvent] = []
    customer_report: CustomerReport | None = None
    scenario_hint = ""

    for ev in story.events:
        if ev.type == SimEventType.ORDER_CREATED and ev.payload:
            order = MerchantOrderSchema.model_validate(ev.payload)
        elif ev.type == SimEventType.GATEWAY_EVENT and ev.payload:
            try:
                gateway_events.append(GatewayPaymentEvent.model_validate(ev.payload))
            except Exception:
                pass
        elif ev.type == SimEventType.CUSTOMER_DEBITED and ev.payload.get("customer_report"):
            try:
                customer_report = CustomerReport.model_validate(ev.payload["customer_report"])
            except Exception:
                pass

    # scenario hint from story metadata
    if "wrong_recipient" in story.story_id.lower():
        scenario_hint = "WRONG_RECIPIENT"
    elif "unauthorized" in story.story_id.lower():
        scenario_hint = "UNAUTHORIZED"

    if order is None:
        order = MerchantOrderSchema(
            order_id="ORD-SIM",
            reference="ORD-SIM",
            amount_paise=49900,
            status="payment_pending",
            created_at=_base_time(),
        )

    decision = classify(order, gateway_events, customer_report, scenario_hint=scenario_hint)
    return {
        "state": decision.state.value,
        "action": decision.action.value,
        "reason_codes": decision.reason_codes,
        "customer_message": decision.customer_message,
        "authoritative_evidence_ids": decision.authoritative_evidence_ids,
        "policy_version": decision.policy_version,
    }
