"""
Safety tests for the deterministic payment-state classifier.
CRITICAL: PENDING and OUTCOME_UNKNOWN must NEVER produce CREATE_RECOVERY_PERMIT.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.classifier import BLOCKED_STATES, classify
from app.schemas.payment import (
    CustomerReport,
    GatewayPaymentEvent,
    MerchantOrderSchema,
    PaymentState,
    RecoveryAction,
    SyntheticIncident,
)

BASE_DATE = "2026-08-30T08:00:00Z"
BASE_ORDER = MerchantOrderSchema(
    order_id="ORD-TEST",
    reference="ORD-TEST",
    amount_paise=99900,
    status="payment_pending",
    created_at=BASE_DATE,
)


def make_event(status: str, payment_id: str = "SYN-PAY-001") -> GatewayPaymentEvent:
    return GatewayPaymentEvent(
        provider="synthetic",
        provider_payment_id=payment_id,
        amount_paise=99900,
        status=status,
        occurred_at=BASE_DATE,
        source="gateway_event",
    )


# --- Core safety assertions ---

def test_pending_never_creates_recovery_link():
    decision = classify(BASE_ORDER, [make_event("pending")])
    assert decision.state == PaymentState.PENDING
    assert decision.action == RecoveryAction.DO_NOT_RETRY
    assert decision.action != RecoveryAction.CREATE_RECOVERY_PERMIT


def test_outcome_unknown_never_creates_recovery_link():
    decision = classify(BASE_ORDER, [])  # no gateway events
    assert decision.state == PaymentState.OUTCOME_UNKNOWN
    assert decision.action != RecoveryAction.CREATE_RECOVERY_PERMIT


def test_blocked_states_set_is_complete():
    assert PaymentState.PENDING in BLOCKED_STATES
    assert PaymentState.OUTCOME_UNKNOWN in BLOCKED_STATES


# --- State classification ---

def test_failed_gateway_event_classifies_as_failed():
    decision = classify(BASE_ORDER, [make_event("failed")])
    assert decision.state == PaymentState.FAILED
    assert decision.action == RecoveryAction.CREATE_RECOVERY_PERMIT


def test_customer_success_claim_overridden_by_gateway_failed():
    report = CustomerReport(
        message="PhonePe shows success",
        amount_paise=99900,
        reported_status="success",
        source="customer_report",
    )
    decision = classify(BASE_ORDER, [make_event("failed")], customer_report=report)
    assert decision.state == PaymentState.FAILED
    assert "CUSTOMER_CLAIM_OVERRIDDEN_BY_GATEWAY" in decision.reason_codes


def test_captured_unlinked_order_classifies_correctly():
    decision = classify(BASE_ORDER, [make_event("captured")])
    assert decision.state == PaymentState.CAPTURED_UNLINKED
    assert decision.action == RecoveryAction.RECONCILE_ORDER


def test_two_captured_events_are_duplicate_success():
    events = [make_event("captured", "SYN-PAY-001"), make_event("captured", "SYN-PAY-002")]
    decision = classify(BASE_ORDER, events)
    assert decision.state == PaymentState.DUPLICATE_SUCCESS
    assert decision.action == RecoveryAction.OPEN_DUPLICATE_REVIEW


def test_conflicting_events_yield_outcome_unknown():
    events = [make_event("captured", "SYN-PAY-001"), make_event("failed", "SYN-PAY-002")]
    decision = classify(BASE_ORDER, events)
    assert decision.state == PaymentState.OUTCOME_UNKNOWN


def test_wrong_recipient_scenario():
    decision = classify(BASE_ORDER, [], scenario_hint="WRONG_RECIPIENT")
    assert decision.state == PaymentState.WRONG_RECIPIENT
    assert decision.action == RecoveryAction.OFFICIAL_ROUTE_GUIDANCE


def test_unauthorized_scenario():
    decision = classify(BASE_ORDER, [], scenario_hint="UNAUTHORIZED")
    assert decision.state == PaymentState.UNAUTHORIZED
    assert decision.action == RecoveryAction.SECURITY_ESCALATION


# --- Synthetic fixture validation ---

INCIDENTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "incidents" / "dev"


def test_all_dev_incidents_have_required_fields():
    incident_files = list(INCIDENTS_DIR.glob("*.json"))
    assert len(incident_files) >= 20, f"Expected at least 20 dev incidents, found {len(incident_files)}"
    for f in incident_files:
        data = json.loads(f.read_text())
        incident = SyntheticIncident.model_validate(data)
        assert incident.incident_id.startswith("INC-")
        assert incident.split == "dev"
        assert incident.expected_state is not None
        assert incident.expected_action is not None


def test_pending_fixtures_never_produce_recovery_link():
    incident_files = list(INCIDENTS_DIR.glob("*.json"))
    for f in incident_files:
        data = json.loads(f.read_text())
        incident = SyntheticIncident.model_validate(data)
        if incident.expected_state in (PaymentState.PENDING, PaymentState.OUTCOME_UNKNOWN):
            assert incident.expected_action != RecoveryAction.CREATE_RECOVERY_PERMIT, (
                f"{incident.incident_id}: PENDING/UNKNOWN incident must not expect CREATE_RECOVERY_PERMIT"
            )
