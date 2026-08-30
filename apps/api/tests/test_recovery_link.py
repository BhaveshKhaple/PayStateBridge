"""
Recovery link service tests using FakePaymentProvider.
No real Razorpay credentials needed.
"""
from __future__ import annotations

import uuid

import pytest

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase
from app.services.permit_service import PermitDeniedError, issue_recovery_permit
from app.services.recovery_link_service import create_recovery_link


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def create_failed_case() -> str:
    from datetime import datetime, timezone
    import uuid
    async with AsyncSessionLocal() as db:
        _oid = f"ORD-LINK-{uuid.uuid4().hex[:12]}"
        order = MerchantOrder(
            order_id=_oid,
            reference=_oid,
            amount_paise=99900,
            status="payment_pending",
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()
        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state="FAILED",
            action="CREATE_RECOVERY_PERMIT",
            original_payment_reference="SYN-PAY-FAILED-001",
        )
        db.add(case)
        await db.commit()
        return case.id


@pytest.mark.asyncio
async def test_failed_case_creates_recovery_link():
    case_id = await create_failed_case()
    # Issue permit first
    async with AsyncSessionLocal() as db:
        await issue_recovery_permit(db, case_id)
    # Create link
    async with AsyncSessionLocal() as db:
        link = await create_recovery_link(db, case_id)
    assert link.link_id.startswith("fake_link_")
    assert link.environment == "fake"
    assert "TEST" in link.test_mode_label.upper() or "FAKE" in link.test_mode_label.upper()


@pytest.mark.asyncio
async def test_recovery_link_is_idempotent():
    case_id = await create_failed_case()
    async with AsyncSessionLocal() as db:
        await issue_recovery_permit(db, case_id)
    async with AsyncSessionLocal() as db:
        link1 = await create_recovery_link(db, case_id)
    async with AsyncSessionLocal() as db:
        link2 = await create_recovery_link(db, case_id)
    assert link1.link_id == link2.link_id


@pytest.mark.asyncio
async def test_no_permit_blocks_link_creation():
    case_id = await create_failed_case()
    with pytest.raises(PermitDeniedError, match="permit"):
        async with AsyncSessionLocal() as db:
            await create_recovery_link(db, case_id)


@pytest.mark.asyncio
async def test_pending_case_cannot_get_link():
    from datetime import datetime, timezone
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id=f"ORD-PEND-{uuid.uuid4().hex[:12]}",
            reference=f"ORD-PEND-{uuid.uuid4().hex[:12]}",
            amount_paise=99900,
            status="payment_pending",
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()
        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state="PENDING",
            action="DO_NOT_RETRY",
        )
        db.add(case)
        await db.commit()
        case_id = case.id

    with pytest.raises(PermitDeniedError):
        async with AsyncSessionLocal() as db:
            await create_recovery_link(db, case_id)
