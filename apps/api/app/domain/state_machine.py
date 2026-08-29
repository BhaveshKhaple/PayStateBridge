"""
Legal state transitions for PayState Bridge.
Prevents impossible moves in the payment case lifecycle.
"""
from __future__ import annotations

# Legal transitions: current_state → set of allowed next states
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "CASE_OPENED": {"EVIDENCE_COLLECTING"},
    "EVIDENCE_COLLECTING": {"CLASSIFIED"},
    "CLASSIFIED": {
        "WAITING_RECONCILIATION",
        "ORDER_RECONCILED",
        "RECOVERY_PERMIT_ISSUED",
        "DUPLICATE_REVIEW_OPEN",
        "EVIDENCE_PACKET_READY",
        "OFFICIAL_ROUTE_GUIDANCE",
        "HUMAN_SECURITY_ESCALATION",
        "CLOSED_NO_ACTION",
    },
    "WAITING_RECONCILIATION": {"ORDER_RECONCILED", "RECOVERY_PERMIT_ISSUED", "EVIDENCE_PACKET_READY"},
    "RECOVERY_PERMIT_ISSUED": {"RECOVERY_LINK_CREATED"},
    "RECOVERY_LINK_CREATED": {"RECOVERY_PAID_TEST", "CLOSED_NO_ACTION"},
    # Terminal states — no further transitions
    "ORDER_RECONCILED": set(),
    "RECOVERY_PAID_TEST": set(),
    "DUPLICATE_REVIEW_OPEN": set(),
    "EVIDENCE_PACKET_READY": {"HUMAN_ESCALATION"},
    "HUMAN_ESCALATION": set(),
    "OFFICIAL_ROUTE_GUIDANCE": set(),
    "HUMAN_SECURITY_ESCALATION": set(),
    "CLOSED_NO_ACTION": set(),
}

TERMINAL_STATES = {
    state for state, nexts in LEGAL_TRANSITIONS.items() if not nexts
}


def is_legal_transition(current: str, next_state: str) -> bool:
    allowed = LEGAL_TRANSITIONS.get(current, set())
    return next_state in allowed


def assert_legal_transition(current: str, next_state: str) -> None:
    if not is_legal_transition(current, next_state):
        raise ValueError(
            f"Illegal state transition: {current!r} → {next_state!r}. "
            f"Allowed from {current!r}: {LEGAL_TRANSITIONS.get(current, set())}"
        )
