"""
Deterministic payment-state classifier.

Rules (in order of precedence):
1. Gateway/merchant event evidence wins over customer report.
2. If evidence is missing or conflicts -> OUTCOME_UNKNOWN.
3. Never issue a recovery permit for PENDING or OUTCOME_UNKNOWN.
"""
from __future__ import annotations

from app.schemas.payment import (
    CustomerReport,
    GatewayPaymentEvent,
    MerchantOrderSchema,
    PaymentState,
    RecoveryAction,
    RecoveryDecision,
)

POLICY_VERSION = "v0.1.0"

# Customer messages per state
_CUSTOMER_MESSAGES: dict[PaymentState, str] = {
    PaymentState.PENDING: (
        "We are verifying your payment. Please do not pay again. "
        "We will confirm your order if the payment completes, or guide you "
        "after the payment is conclusively marked failed."
    ),
    PaymentState.FAILED: (
        "The first payment has been verified as failed by our payment gateway. "
        "We are preparing one secure recovery link for you."
    ),
    PaymentState.CAPTURED_UNLINKED: (
        "Your payment is confirmed. We are restoring your order without any "
        "additional charge."
    ),
    PaymentState.DUPLICATE_SUCCESS: (
        "We found two completed payments for the same order. Our team is "
        "reviewing the duplicate. Please do not pay again."
    ),
    PaymentState.OUTCOME_UNKNOWN: (
        "We cannot confirm the outcome of your payment yet. Please do not pay "
        "again. We are preparing your evidence packet for review."
    ),
    PaymentState.WRONG_RECIPIENT: (
        "Your payment was sent to a different recipient. Merchant cannot "
        "reverse this transfer. Please follow the official bank or NPCI "
        "grievance process."
    ),
    PaymentState.UNAUTHORIZED: (
        "This payment does not match any of your initiated transactions. "
        "Please contact your bank immediately and use the official security "
        "escalation process."
    ),
}

_STATE_TO_ACTION: dict[PaymentState, RecoveryAction] = {
    PaymentState.PENDING: RecoveryAction.DO_NOT_RETRY,
    PaymentState.FAILED: RecoveryAction.CREATE_RECOVERY_PERMIT,
    PaymentState.CAPTURED_UNLINKED: RecoveryAction.RECONCILE_ORDER,
    PaymentState.DUPLICATE_SUCCESS: RecoveryAction.OPEN_DUPLICATE_REVIEW,
    PaymentState.OUTCOME_UNKNOWN: RecoveryAction.BUILD_EVIDENCE_PACKET,
    PaymentState.WRONG_RECIPIENT: RecoveryAction.OFFICIAL_ROUTE_GUIDANCE,
    PaymentState.UNAUTHORIZED: RecoveryAction.SECURITY_ESCALATION,
}

# States that must NEVER create a recovery/payment link
BLOCKED_STATES = {PaymentState.PENDING, PaymentState.OUTCOME_UNKNOWN}


def classify(
    order: MerchantOrderSchema,
    gateway_events: list[GatewayPaymentEvent],
    customer_report: CustomerReport | None = None,
    *,
    scenario_hint: str = "",
) -> RecoveryDecision:
    """
    Deterministically classify a payment case from authoritative evidence.
    Customer report is context only — it cannot override gateway evidence.
    """
    reason_codes: list[str] = []
    evidence_ids: list[str] = []

    # Collect gateway status codes
    statuses = [e.status for e in gateway_events]
    for e in gateway_events:
        evidence_ids.append(e.provider_payment_id)

    # --- Classification rules (gateway evidence wins) ---

    if not gateway_events:
        # No merchant-side evidence
        reason_codes.append("NO_GATEWAY_EVENT")
        state = PaymentState.OUTCOME_UNKNOWN

    elif scenario_hint == "WRONG_RECIPIENT" or (
        customer_report and "wrong" in customer_report.message.lower()
        and not any(s in ("captured", "failed") for s in statuses)
    ):
        reason_codes.append("WRONG_RECIPIENT_CLAIM")
        state = PaymentState.WRONG_RECIPIENT

    elif scenario_hint == "UNAUTHORIZED":
        reason_codes.append("UNAUTHORIZED_CLAIM")
        state = PaymentState.UNAUTHORIZED

    elif len([s for s in statuses if s == "captured"]) >= 2:
        # Two captured events for one order -> duplicate
        reason_codes.append("MULTIPLE_CAPTURED_EVENTS")
        state = PaymentState.DUPLICATE_SUCCESS

    elif statuses == ["captured"] or (
        len(statuses) == 1 and statuses[0] == "captured"
        and order.status in ("payment_pending", "created")
    ):
        # Captured but order not linked
        reason_codes.append("CAPTURED_ORDER_NOT_LINKED")
        state = PaymentState.CAPTURED_UNLINKED

    elif all(s == "failed" for s in statuses) and statuses:
        reason_codes.append("GATEWAY_STATUS_FAILED")
        # Customer claiming success while gateway says failed -> gateway wins
        if customer_report and customer_report.reported_status == "success":
            reason_codes.append("CUSTOMER_CLAIM_OVERRIDDEN_BY_GATEWAY")
        state = PaymentState.FAILED

    elif all(s == "pending" for s in statuses) and statuses:
        reason_codes.append("GATEWAY_STATUS_PENDING")
        reason_codes.append("NO_FINAL_FAILURE_RECEIPT")
        state = PaymentState.PENDING

    elif len(set(statuses)) > 1:
        # Conflicting statuses
        reason_codes.append("CONFLICTING_GATEWAY_EVENTS")
        state = PaymentState.OUTCOME_UNKNOWN

    else:
        reason_codes.append("UNDETERMINED_EVIDENCE")
        state = PaymentState.OUTCOME_UNKNOWN

    evidence_ids.append(order.order_id)
    action = _STATE_TO_ACTION[state]

    return RecoveryDecision(
        state=state,
        action=action,
        reason_codes=reason_codes,
        authoritative_evidence_ids=evidence_ids,
        customer_message=_CUSTOMER_MESSAGES[state],
        policy_version=POLICY_VERSION,
    )
