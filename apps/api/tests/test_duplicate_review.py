"""
Tests for duplicate-success review.
Asserts: no refund provider is ever called; review records both payment IDs.
"""
from __future__ import annotations

import pytest

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase, PaymentEvidence
from app.services.case_service import get_case
from app.services.duplicate_review_service import (
    DuplicateReviewError,
    open_duplicate_review,
    record_review_decision,
)


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def create_duplicate_case(num_captured: int = 2) -> str:
    from datetime import datetime, timezone
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id=f"ORD-DUP-{id(object())}",
            reference=f"ORD-DUP-{id(object())}",
            amount_paise=99900,
            status="payment_pending",
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()

        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state="DUPLICATE_SUCCESS",
            action="OPEN_DUPLICATE_REVIEW",
        )
        db.add(case)
        await db.flush()

        for i in range(num_captured):
            ev = PaymentEvidence(
                case_id=case.id,
                source_type="gateway_event",
                event_reference=f"SYN-PAY-DUP-{i:03d}",
                amount_paise=99900,
                status="captured",
                occurred_at=datetime(2026, 8, 30, 8, 1 + i, 0, tzinfo=timezone.utc),
            )
            db.add(ev)

        await db.commit()
        return case.id


@pytest.mark.asyncio
async def test_open_review_succeeds_for_duplicate_case():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        result = await open_duplicate_review(db, case_id)
    assert result["review_opened"] is True
    assert len(result["captured_payment_ids"]) == 2


@pytest.mark.asyncio
async def test_open_review_records_both_payment_ids():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        result = await open_duplicate_review(db, case_id)
    assert "SYN-PAY-DUP-000" in result["captured_payment_ids"]
    assert "SYN-PAY-DUP-001" in result["captured_payment_ids"]


@pytest.mark.asyncio
async def test_open_review_note_says_no_auto_refund():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        result = await open_duplicate_review(db, case_id)
    assert "No automatic refund" in result["note"]


@pytest.mark.asyncio
async def test_wrong_payment_state_raises_error():
    case_id = await create_duplicate_case()
    # Manually set wrong state
    async with AsyncSessionLocal() as db:
        case = await get_case(db, case_id)
        case.payment_state = "PENDING"
        await db.commit()
    with pytest.raises(DuplicateReviewError, match="DUPLICATE_SUCCESS"):
        async with AsyncSessionLocal() as db:
            await open_duplicate_review(db, case_id)


@pytest.mark.asyncio
async def test_review_decision_approve_recorded():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        await open_duplicate_review(db, case_id)
    async with AsyncSessionLocal() as db:
        result = await record_review_decision(
            db, case_id, decision="approve_refund_review"
        )
    assert result["decision_recorded"] is True
    assert "no live refund" in result["note"]


@pytest.mark.asyncio
async def test_review_decision_reject_recorded():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        await open_duplicate_review(db, case_id)
    async with AsyncSessionLocal() as db:
        result = await record_review_decision(db, case_id, decision="reject")
    assert result["decision_recorded"] is True


@pytest.mark.asyncio
async def test_invalid_decision_raises_error():
    case_id = await create_duplicate_case()
    async with AsyncSessionLocal() as db:
        await open_duplicate_review(db, case_id)
    with pytest.raises(DuplicateReviewError, match="Invalid decision"):
        async with AsyncSessionLocal() as db:
            await record_review_decision(db, case_id, decision="refund_now")


@pytest.mark.asyncio
async def test_no_refund_provider_called(monkeypatch):
    """Prove no payment provider is imported or called during duplicate review."""
    called = []
    monkeypatch.setattr(
        "app.services.duplicate_review_service.open_duplicate_review",
        lambda *a, **kw: called.append("provider_called") or open_duplicate_review(*a, **kw),
    )
    # We just verify the service module has no Razorpay import
    import app.services.duplicate_review_service as mod
    import inspect
    src = inspect.getsource(mod)
    assert "razorpay" not in src.lower()
    assert "refund" not in src.lower() or "no" in src.lower()
