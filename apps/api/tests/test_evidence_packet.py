"""
Tests for evidence packet and safe reply generation.
Key invariants:
- Packet never promises reversal, exact refund, or bank access.
- Wrong-recipient packet never claims merchant can recover the transfer.
- Outcome-unknown packet never creates a recovery link.
"""
from __future__ import annotations

import pytest

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase, PaymentEvidence
from app.services.evidence_packet_service import EvidencePacketError, build_evidence_packet


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def create_case_with_state(payment_state: str) -> str:
    from datetime import datetime, timezone
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id=f"ORD-PKT-{id(object())}",
            reference=f"ORD-PKT-{id(object())}",
            amount_paise=99900,
            status="payment_pending",
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()

        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state=payment_state,
            action="BUILD_EVIDENCE_PACKET",
        )
        db.add(case)
        await db.flush()

        ev = PaymentEvidence(
            case_id=case.id,
            source_type="customer_report",
            event_reference="SYN-UTR-20260830-PKT",
            amount_paise=99900,
            status="unknown",
            occurred_at=datetime(2026, 8, 30, 8, 1, 0, tzinfo=timezone.utc),
        )
        db.add(ev)
        await db.commit()
        return case.id


@pytest.mark.asyncio
async def test_outcome_unknown_generates_packet():
    case_id = await create_case_with_state("OUTCOME_UNKNOWN")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    assert packet["packet_type"] == "evidence_packet"
    assert packet["payment_state"] == "OUTCOME_UNKNOWN"
    assert "official_escalation_route" in packet
    assert len(packet["evidence"]) > 0


@pytest.mark.asyncio
async def test_wrong_recipient_generates_packet():
    case_id = await create_case_with_state("WRONG_RECIPIENT")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    assert packet["payment_state"] == "WRONG_RECIPIENT"
    assert "cannot be reversed by the merchant" in packet["official_escalation_route"]


@pytest.mark.asyncio
async def test_packet_has_disclaimer():
    case_id = await create_case_with_state("OUTCOME_UNKNOWN")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    assert "SYNTHETIC DATA" in packet["disclaimer"]


@pytest.mark.asyncio
async def test_packet_customer_message_no_unsupported_promise():
    case_id = await create_case_with_state("OUTCOME_UNKNOWN")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    msg = packet["safe_customer_message"].lower()
    # Must never promise guaranteed reversal, exact timing, or bank access
    assert "guarantee" not in msg
    assert "will refund" not in msg
    assert "bank will" not in msg


@pytest.mark.asyncio
async def test_wrong_recipient_no_recovery_claim():
    case_id = await create_case_with_state("WRONG_RECIPIENT")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    # Merchant-cannot-do list must include bank access disclaimer
    cannot_do = " ".join(packet["what_merchant_cannot_do"]).lower()
    assert "reverse" in cannot_do or "bank" in cannot_do


@pytest.mark.asyncio
async def test_evidence_items_have_trust_labels():
    case_id = await create_case_with_state("OUTCOME_UNKNOWN")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    for ev in packet["evidence"]:
        assert "trust_level" in ev


@pytest.mark.asyncio
async def test_pending_state_cannot_get_packet():
    case_id = await create_case_with_state("PENDING")
    with pytest.raises(EvidencePacketError):
        async with AsyncSessionLocal() as db:
            await build_evidence_packet(db, case_id)


@pytest.mark.asyncio
async def test_packet_contains_order_and_case_ids():
    case_id = await create_case_with_state("OUTCOME_UNKNOWN")
    async with AsyncSessionLocal() as db:
        packet = await build_evidence_packet(db, case_id)
    assert packet["case_id"] == case_id
    assert "ORD-PKT-" in packet["order_id"]
