"""
Fixture-driven safety tests — run every dev incident through the classifier
and verify expected state/action.
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

INCIDENTS_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "data"
    / "incidents"
    / "dev"
)


def load_incidents() -> list[SyntheticIncident]:
    return [
        SyntheticIncident.model_validate(json.loads(f.read_text()))
        for f in sorted(INCIDENTS_DIR.glob("*.json"))
    ]


@pytest.mark.parametrize("incident", load_incidents(), ids=lambda i: i.incident_id)
def test_incident_expected_state_matches(incident: SyntheticIncident):
    scenario = incident.scenario
    hint = ""
    if scenario in ("WRONG_RECIPIENT",):
        hint = "WRONG_RECIPIENT"
    elif scenario in ("UNAUTHORIZED",):
        hint = "UNAUTHORIZED"

    decision = classify(
        incident.merchant_order,
        incident.gateway_events,
        incident.customer_report,
        scenario_hint=hint,
    )
    assert decision.state == incident.expected_state, (
        f"{incident.incident_id}: expected {incident.expected_state}, got {decision.state}\n"
        f"reason_codes={decision.reason_codes}"
    )


@pytest.mark.parametrize("incident", load_incidents(), ids=lambda i: i.incident_id)
def test_incident_expected_action_matches(incident: SyntheticIncident):
    scenario = incident.scenario
    hint = ""
    if scenario in ("WRONG_RECIPIENT",):
        hint = "WRONG_RECIPIENT"
    elif scenario in ("UNAUTHORIZED",):
        hint = "UNAUTHORIZED"

    decision = classify(
        incident.merchant_order,
        incident.gateway_events,
        incident.customer_report,
        scenario_hint=hint,
    )
    assert decision.action == incident.expected_action, (
        f"{incident.incident_id}: expected action {incident.expected_action}, got {decision.action}"
    )


def test_no_pending_incident_expects_recovery_permit():
    """Safety: PENDING or OUTCOME_UNKNOWN must never expect CREATE_RECOVERY_PERMIT."""
    incidents = load_incidents()
    violations = [
        inc.incident_id
        for inc in incidents
        if inc.expected_state in (PaymentState.PENDING, PaymentState.OUTCOME_UNKNOWN)
        and inc.expected_action == RecoveryAction.CREATE_RECOVERY_PERMIT
    ]
    assert violations == [], f"Safety violation: {violations}"


def test_all_20_dev_incidents_present():
    incidents = load_incidents()
    assert len(incidents) >= 20, f"Expected ≥20 dev incidents, got {len(incidents)}"
