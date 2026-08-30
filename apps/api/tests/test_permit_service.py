"""
Tests for RecoveryPermit issuance safety.
CRITICAL: PENDING and OUTCOME_UNKNOWN must never receive a permit.
"""
from __future__ import annotations

import pytest

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase
from app.services.permit_service import PermitDeniedError, issue_recovery_permit
from app.schemas.payment import PaymentState


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield


async def create_case_with_payment_state(payment_state: str, order_status: str = "payment_pending") -> str:
    import uuid
    from datetime import datetime, timezone
    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id=f"ORD-PERMIT-{uid}",
            reference=f"ORD-PERMIT-{uid}",
            amount_paise=99900,
            status=order_status,
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()
        case = PaymentCase(
            order_id=order.order_id,
            state="CLASSIFIED",
            payment_state=payment_state,
            action="CREATE_RECOVERY_PERMIT" if payment_state == "FAILED" else "DO_NOT_RETRY",
            original_payment_reference="SYN-PAY-20260830-FAILED-001",
        )
        db.add(case)
        await db.commit()
        return case.id


@pytest.mark.asyncio
async def test_failed_case_gets_permit():
    case_id = await create_case_with_payment_state("FAILED")
    async with AsyncSessionLocal() as db:
        permit = await issue_recovery_permit(db, case_id)
    assert permit.environment == "test"
    assert permit.amount_paise == 99900
    assert len(permit.idempotency_key) == 32


@pytest.mark.asyncio
async def test_pending_case_denied():
    case_id = await create_case_with_payment_state("PENDING")
    with pytest.raises(PermitDeniedError, match="PENDING"):
        async with AsyncSessionLocal() as db:
            await issue_recovery_permit(db, case_id)


@pytest.mark.asyncio
async def test_outcome_unknown_denied():
    case_id = await create_case_with_payment_state("OUTCOME_UNKNOWN")
    with pytest.raises(PermitDeniedError):
        async with AsyncSessionLocal() as db:
            await issue_recovery_permit(db, case_id)


@pytest.mark.asyncio
async def test_captured_unlinked_denied():
    case_id = await create_case_with_payment_state("CAPTURED_UNLINKED")
    with pytest.raises(PermitDeniedError):
        async with AsyncSessionLocal() as db:
            await issue_recovery_permit(db, case_id)


@pytest.mark.asyncio
async def test_wrong_recipient_denied():
    case_id = await create_case_with_payment_state("WRONG_RECIPIENT")
    with pytest.raises(PermitDeniedError):
        async with AsyncSessionLocal() as db:
            await issue_recovery_permit(db, case_id)


@pytest.mark.asyncio
async def test_idempotent_permit_same_key_returned():
    case_id = await create_case_with_payment_state("FAILED")
    async with AsyncSessionLocal() as db:
        permit1 = await issue_recovery_permit(db, case_id)
    async with AsyncSessionLocal() as db:
        permit2 = await issue_recovery_permit(db, case_id)
    assert permit1.idempotency_key == permit2.idempotency_key


@pytest.mark.asyncio
async def test_already_paid_order_denied():
    case_id = await create_case_with_payment_state("FAILED", order_status="paid_reconciled")
    with pytest.raises(PermitDeniedError, match="already paid"):
        async with AsyncSessionLocal() as db:
            await issue_recovery_permit(db, case_id)


def test_config_rejects_live_key():
    from app.config import AppConfig, ConfigError
    import os
    env_backup = os.environ.copy()
    os.environ["APP_ENV"] = "demo"
    os.environ["RAZORPAY_KEY_ID"] = "rzp_live_XXXXXXXXXX"
    os.environ["RAZORPAY_KEY_SECRET"] = "secret"
    cfg = AppConfig()
    with pytest.raises(ConfigError, match="rzp_test_"):
        cfg.validate()
    os.environ.clear()
    os.environ.update(env_backup)


def test_config_rejects_non_demo_env():
    from app.config import AppConfig, ConfigError
    import os
    env_backup = os.environ.copy()
    os.environ["APP_ENV"] = "production"
    cfg = AppConfig()
    with pytest.raises(ConfigError, match="demo"):
        cfg.validate()
    os.environ.clear()
    os.environ.update(env_backup)


def test_config_accepts_test_key():
    from app.config import AppConfig
    import os
    env_backup = os.environ.copy()
    os.environ["APP_ENV"] = "demo"
    os.environ["RAZORPAY_KEY_ID"] = "rzp_test_XXXXXXXXXX"
    os.environ["RAZORPAY_KEY_SECRET"] = "secret"
    cfg = AppConfig()
    cfg.validate()  # should not raise
    os.environ.clear()
    os.environ.update(env_backup)
