from __future__ import annotations

import pytest

from app.services.lookup_service import lookup_and_decide


@pytest.mark.asyncio
async def test_lookup_requires_an_id():
    r = await lookup_and_decide()
    assert "error" in r


@pytest.mark.asyncio
async def test_pending_demo_id_is_do_not_retry():
    # suffix "1" -> pending in fake provider
    r = await lookup_and_decide(payment_id="pay_demo_001")
    assert r["found"] is True
    assert r["data_source"] == "synthetic_demo"
    assert r["decision"]["state"] == "PENDING"
    assert r["decision"]["action"] == "DO_NOT_RETRY"


@pytest.mark.asyncio
async def test_failed_demo_id_allows_recovery():
    # suffix "5" -> failed
    r = await lookup_and_decide(payment_id="pay_demo_005")
    assert r["decision"]["state"] == "FAILED"
    assert r["decision"]["action"] == "CREATE_RECOVERY_PERMIT"


@pytest.mark.asyncio
async def test_lookup_reports_data_source():
    r = await lookup_and_decide(payment_id="pay_demo_002")
    assert r["data_source"] in ("synthetic_demo", "razorpay_test")
