"""
Rule knowledge base — maps classifier reason codes to cited principles.
These are curated references for a portfolio prototype. Where a rule reflects
a documented Razorpay/NPCI concept we say so; where it is our own safety policy
we label it 'PayState policy'. We do NOT fabricate exact doc section numbers.
"""
from __future__ import annotations

from pydantic import BaseModel


class RuleCitation(BaseModel):
    rule_id: str
    title: str
    principle: str
    source: str          # e.g. "Razorpay Payment Links — webhooks concept", "NPCI UPI dispute process", "PayState safety policy"
    source_kind: str     # "razorpay" | "npci" | "paystate_policy"


CITATIONS: dict[str, RuleCitation] = {
    "GATEWAY_STATUS_PENDING": RuleCitation(
        rule_id="R-PENDING-01",
        title="Do not retry while the first payment is pending",
        principle="A UPI payment can be debited at the customer's bank before the merchant receives a final capture/failure. Asking the customer to pay again during this window risks a duplicate debit.",
        source="Razorpay payment lifecycle (authorized→captured) + PayState safety policy",
        source_kind="razorpay",
    ),
    "NO_FINAL_FAILURE_RECEIPT": RuleCitation(
        rule_id="R-PENDING-02",
        title="A recovery link requires a conclusive failure",
        principle="Only a final 'failed' gateway event authorises a replacement payment link. Absence of success is not proof of failure.",
        source="PayState safety policy (stopping rule)",
        source_kind="paystate_policy",
    ),
    "CAPTURED_ORDER_NOT_LINKED": RuleCitation(
        rule_id="R-CAP-01",
        title="Reconcile a captured payment to its order",
        principle="When the gateway shows 'captured' but the merchant order is unpaid (a missed/lost webhook), the payment should be linked to the order — recovering revenue without a second charge.",
        source="Razorpay webhooks — payment.captured / order reconciliation concept",
        source_kind="razorpay",
    ),
    "MULTIPLE_CAPTURED_EVENTS": RuleCitation(
        rule_id="R-DUP-01",
        title="Two captures for one order → human refund review",
        principle="Multiple successful captures mapping to one intended order indicate a duplicate payment. Refunds must be merchant-approved, never automatic.",
        source="Razorpay Refunds API is merchant-authorised + PayState policy",
        source_kind="razorpay",
    ),
    "GATEWAY_STATUS_FAILED": RuleCitation(
        rule_id="R-FAIL-01",
        title="Verified failure unlocks exactly one recovery link",
        principle="A final 'failed' status means no money was captured, so a single fresh Test Mode payment link is safe to offer.",
        source="Razorpay Payment Links — create after verified failure",
        source_kind="razorpay",
    ),
    "CUSTOMER_CLAIM_OVERRIDDEN_BY_GATEWAY": RuleCitation(
        rule_id="R-TRUST-01",
        title="Gateway evidence outranks customer report",
        principle="A customer screenshot or message is untrusted context. Authoritative payment state comes only from gateway/merchant events.",
        source="PayState trust-boundary policy",
        source_kind="paystate_policy",
    ),
    "CONFLICTING_GATEWAY_EVENTS": RuleCitation(
        rule_id="R-UNK-01",
        title="Conflicting evidence → do not guess",
        principle="When gateway events conflict (e.g. captured and failed), the system must not fabricate a decision; it builds an evidence packet for human/official review.",
        source="PayState safety policy (fail-closed)",
        source_kind="paystate_policy",
    ),
    "NO_GATEWAY_EVENT": RuleCitation(
        rule_id="R-UNK-02",
        title="No merchant evidence → outcome unknown",
        principle="With no gateway/order evidence, the outcome is unknowable from the merchant side; the safe action is to escalate via the official UPI dispute route, never to retry.",
        source="NPCI UPI dispute/grievance process (official route)",
        source_kind="npci",
    ),
    "WRONG_RECIPIENT_CLAIM": RuleCitation(
        rule_id="R-WR-01",
        title="Merchant cannot reverse a wrong-recipient transfer",
        principle="A completed UPI transfer to a wrong VPA cannot be reversed by the merchant; the customer must use the bank/NPCI recall and grievance process.",
        source="NPCI UPI wrong-credit / grievance process",
        source_kind="npci",
    ),
    "UNAUTHORIZED_CLAIM": RuleCitation(
        rule_id="R-UA-01",
        title="Unauthorised payment → security escalation",
        principle="An allegation that the customer did not initiate the payment must exit the normal recovery flow and route to bank/security escalation.",
        source="RBI/NPCI unauthorised-transaction reporting + PayState policy",
        source_kind="npci",
    ),
    "AMOUNT_MISMATCH": RuleCitation(
        rule_id="R-UNK-04",
        title="Captured amount does not match the order → do not act",
        principle="When a captured payment's amount does not equal the expected order amount, the payment cannot be safely reconciled to the order. Treat the outcome as unknown and escalate for review rather than link or retry.",
        source="PayState safety policy (fail-closed) + order reconciliation concept",
        source_kind="paystate_policy",
    ),
    "UNDETERMINED_EVIDENCE": RuleCitation(
        rule_id="R-UNK-03",
        title="Undetermined evidence → outcome unknown",
        principle="If evidence does not match any known safe pattern, classify as outcome-unknown and escalate rather than act.",
        source="PayState safety policy (fail-closed)",
        source_kind="paystate_policy",
    ),
}


def cite_reason_codes(reason_codes: list[str]) -> list[dict]:
    """Return ordered, de-duplicated citations for a decision's reason codes."""
    seen: set[str] = set()
    out: list[dict] = []
    for code in reason_codes:
        c = CITATIONS.get(code)
        if c and c.rule_id not in seen:
            seen.add(c.rule_id)
            out.append(c.model_dump())
    return out
