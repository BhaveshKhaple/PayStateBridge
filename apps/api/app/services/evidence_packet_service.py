"""
Evidence packet service.
For OUTCOME_UNKNOWN: build a structured evidence packet with order/payment refs,
source labels, timestamps, and official escalation route.
For WRONG_RECIPIENT: provide official-route guidance only — no recovery claim.

Neither generates a recovery link. Neither promises bank reversal or exact timing.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PaymentCase
from app.services.case_service import CaseNotFoundError, get_case

OFFICIAL_UPI_ROUTE = (
    "Official escalation route: (1) Raise a dispute through the UPI app "
    "used for payment (PhonePe Help, Google Pay Help, etc.). "
    "(2) Contact your bank's customer care with the UTR reference. "
    "(3) File a grievance at pgms.npci.org.in if the bank does not resolve within 3 business days. "
    "Keep all transaction references and screenshots."
)

WRONG_RECIPIENT_ROUTE = (
    "A completed UPI transfer to a wrong recipient cannot be reversed by the merchant. "
    "Merchants do not have access to recipient bank accounts. "
    "Official steps: (1) Contact your bank immediately with the UTR reference. "
    "(2) Request a 'wrong credit recall' through your bank. "
    "(3) File a complaint at pgms.npci.org.in. "
    "The merchant cannot guarantee or promise reversal."
)


class EvidencePacketError(Exception):
    pass


PACKET_ELIGIBLE_STATES = {"OUTCOME_UNKNOWN", "WRONG_RECIPIENT"}


async def build_evidence_packet(
    db: AsyncSession,
    case_id: str,
    *,
    actor: str = "operator",
) -> dict:
    """
    Build a structured evidence packet for OUTCOME_UNKNOWN or WRONG_RECIPIENT cases.
    Returns a dict with all case references and official escalation guidance.
    Never submits a complaint, never promises recovery.
    """
    case = await get_case(db, case_id)

    if case.payment_state not in PACKET_ELIGIBLE_STATES:
        raise EvidencePacketError(
            f"Evidence packet only available for {PACKET_ELIGIBLE_STATES}. "
            f"Current state: {case.payment_state!r}."
        )

    # Build evidence summary — no secrets, only synthetic references
    evidence_summary = []
    for ev in case.evidence_items:
        evidence_summary.append({
            "source_type": ev.source_type,
            "reference": ev.event_reference,
            "amount_paise": ev.amount_paise,
            "status": ev.status,
            "occurred_at": ev.occurred_at.isoformat() if ev.occurred_at else None,
            "trust_level": (
                "authoritative"
                if ev.source_type in ("gateway_event", "merchant_order")
                else "untrusted_customer_provided"
            ),
        })

    official_route = (
        WRONG_RECIPIENT_ROUTE
        if case.payment_state == "WRONG_RECIPIENT"
        else OFFICIAL_UPI_ROUTE
    )

    packet = {
        "packet_type": "evidence_packet",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_id": case.id,
        "order_id": case.order_id,
        "payment_state": case.payment_state,
        "disclaimer": (
            "SYNTHETIC DATA — this is a portfolio prototype. "
            "All references are synthetic. No real complaint has been filed."
        ),
        "evidence": evidence_summary,
        "official_escalation_route": official_route,
        "what_merchant_cannot_do": [
            "Access NPCI switch or bank-core settlement data",
            "Reverse a wrong-recipient UPI transfer",
            "Guarantee a refund timeline",
            "File a complaint on behalf of the customer",
        ],
        "safe_customer_message": (
            "We have prepared your evidence packet. "
            "Please use the official escalation route below. "
            "We cannot access your bank or NPCI data directly. "
            "Do not pay again while this is unresolved."
            if case.payment_state == "OUTCOME_UNKNOWN"
            else (
                "Your transfer went to a different recipient. "
                "We cannot reverse this transfer. "
                "Please follow the official bank and NPCI process below."
            )
        ),
    }

    # Record audit event
    from app.db.models import AuditEvent
    audit = AuditEvent(
        case_id=case.id,
        event_type="EVIDENCE_PACKET_GENERATED",
        actor=actor,
        prior_state=case.state,
        new_state="EVIDENCE_PACKET_READY" if case.state != "EVIDENCE_PACKET_READY" else case.state,
        action="BUILD_EVIDENCE_PACKET",
        reason_codes=["PACKET_GENERATED"],
        customer_message=packet["safe_customer_message"],
    )
    db.add(audit)

    if case.state == "CLASSIFIED":
        case.state = "EVIDENCE_PACKET_READY"

    case.customer_message = packet["safe_customer_message"]
    await db.commit()

    return packet
