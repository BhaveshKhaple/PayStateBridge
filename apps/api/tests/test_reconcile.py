"""
Tests for captured-unlinked order reconciliation.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase, PaymentEvidence
from app.services.reconcile_service import (
    AmbiguousMatchError,
    ReconcileError,
    reconcile_order,
)


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def create_test_case(
    order_amount: int = 99900,
    ev_amount: int = 99900,
    ev_status: str = "captured",
    order_status: str = "payment_pending",
    payment_state: str = "CAPTURED_UNLINKED",
    num_captured: int = 1,
) -> str:
    """Helper: create a minimal case in the DB for testing."""
    import uuid
    from datetime import datetime, timezone
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id=f"ORD-TEST-{uid}",
            reference=f"ORD-TEST-{uid}",
            amount_paise=order_amount,
            status=order_status,
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()

        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state=payment_state,
            action="RECONCILE_ORDER",
        )
        db.add(case)
        await db.flush()

        for i in range(num_captured):
            ev = PaymentEvidence(
                case_id=case.id,
                source_type="gateway_event",
                event_reference=f"SYN-PAY-TEST-{i:03d}",
                amount_paise=ev_amount,
                status=ev_status,
                occurred_at=datetime(2026, 8, 30, 8, 1, 0, tzinfo=timezone.utc),
            )
            db.add(ev)

        await db.commit()
        return case.id


@pytest.mark.asyncio
async def test_successful_reconciliation():
    case_id = await create_test_case()
    async with AsyncSessionLocal() as db:
        result = await reconcile_order(db, case_id)
    assert result["reconciled"] is True
    assert result["new_order_status"] == "paid_reconciled"


@pytest.mark.asyncio
async def test_amount_mismatch_raises_reconcile_error():
    case_id = await create_test_case(order_amount=99900, ev_amount=50000)
    with pytest.raises(ReconcileError, match="Amount mismatch"):
        async with AsyncSessionLocal() as db:
            await reconcile_order(db, case_id)


@pytest.mark.asyncio
async def test_ambiguous_match_raises_error():
    case_id = await create_test_case(num_captured=2)
    with pytest.raises(AmbiguousMatchError):
        async with AsyncSessionLocal() as db:
            await reconcile_order(db, case_id)


@pytest.mark.asyncio
async def test_wrong_payment_state_raises_error():
    case_id = await create_test_case(payment_state="PENDING")
    with pytest.raises(ReconcileError, match="Cannot reconcile"):
        async with AsyncSessionLocal() as db:
            await reconcile_order(db, case_id)


@pytest.mark.asyncio
async def test_already_paid_order_raises_error():
    case_id = await create_test_case(order_status="paid_reconciled")
    with pytest.raises(ReconcileError, match="not unpaid"):
        async with AsyncSessionLocal() as db:
            await reconcile_order(db, case_id)


@pytest.mark.asyncio
async def test_reconcile_records_audit_event():
    from app.services.case_service import get_case
    case_id = await create_test_case()
    async with AsyncSessionLocal() as db:
        await reconcile_order(db, case_id)
        case = await get_case(db, case_id)
    audit_types = [ae.event_type for ae in case.audit_events]
    assert "ORDER_RECONCILED" in audit_types
