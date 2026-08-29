"""
Webhook handler tests — HMAC verification, deduplication, state transition.
"""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient, ASGITransport

from app.integrations.fake_provider import FAKE_WEBHOOK_SECRET
from app.main import app
from app.db.database import init_db, AsyncSessionLocal
from app.db.models import MerchantOrder, PaymentCase, RecoveryAction


@pytest.fixture(autouse=True)
async def setup():
    await init_db()
    yield


def _sign(body: bytes, secret: str = FAKE_WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode(), body, "sha256").hexdigest()


def _make_paid_payload(link_id: str, payment_id: str = "pay_fake_001", event_id: str | None = None) -> bytes:
    # FakePaymentProvider reads payload.payment_link.id and payload.payment_link.status
    # and payload.payment.id — match that structure exactly
    evt_id = event_id or f"evt_{link_id[:8]}"
    return json.dumps({
        "id": evt_id,
        "event": "payment_link.paid",
        "event_id": evt_id,
        "payload": {
            "payment_link": {
                "id": link_id,
                "status": "paid",
                "amount": 99900,
                "reference_id": "idem_key_123",
            },
            "payment": {"id": payment_id},
        },
    }).encode()


@pytest.mark.asyncio
async def test_invalid_signature_returns_400():
    body = _make_paid_payload("fake_link_abc123", event_id="evt_inv_sig_001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks/razorpay",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": "bad_signature_xyz",
            },
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_valid_signature_returns_200():
    body = _make_paid_payload("fake_link_valid_001", event_id="evt_valid_001")
    sig = _sign(body)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks/razorpay",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": sig,
            },
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_duplicate_event_is_ignored():
    body = _make_paid_payload("fake_link_dup_001", event_id="evt_dup_001_unique")
    sig = _sign(body)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post(
            "/v1/webhooks/razorpay",
            content=body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        r2 = await client.post(
            "/v1/webhooks/razorpay",
            content=body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json().get("status") == "duplicate_ignored"


@pytest.mark.asyncio
async def test_webhook_transitions_case_to_recovery_paid():
    from datetime import datetime, timezone
    # Create a case + link action in DB
    async with AsyncSessionLocal() as db:
        order = MerchantOrder(
            order_id="ORD-WH-001",
            reference="ORD-WH-001",
            amount_paise=99900,
            status="payment_pending",
            created_at=datetime(2026, 8, 30, 8, 0, 0, tzinfo=timezone.utc),
        )
        db.add(order)
        await db.flush()
        case = PaymentCase(
            order_id="ORD-WH-001",
            state="RECOVERY_LINK_CREATED",
            payment_state="FAILED",
        )
        db.add(case)
        await db.flush()
        link_action = RecoveryAction(
            case_id=case.id,
            action_kind="RECOVERY_LINK",
            idempotency_key="idem_wh_001",
            provider_link_id="fake_link_webhook_test",
            status="fake_provider_v1",
            expires_at=datetime(2026, 9, 5, 0, 0, 0, tzinfo=timezone.utc),
        )
        db.add(link_action)
        await db.commit()
        case_id = case.id

    body = _make_paid_payload("fake_link_webhook_test", "pay_wh_001", event_id="evt_wh_unique_001")
    sig = _sign(body)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/v1/webhooks/razorpay",
            content=body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
    assert resp.status_code == 200

    # Verify case transitioned
    from app.services.case_service import get_case
    async with AsyncSessionLocal() as db:
        updated = await get_case(db, case_id)
    assert updated.state == "RECOVERY_PAID_TEST"
