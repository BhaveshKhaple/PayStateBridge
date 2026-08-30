"""
FakePaymentProvider — deterministic provider for CI tests.
Never makes HTTP calls. Never requires credentials.
Always returns stable fake link_id based on idempotency_key.
"""
from __future__ import annotations

import hashlib
import hmac
import json

from app.integrations.payment_provider import (
    FetchedPayment,
    ProviderLinkResult,
    VerifiedWebhookEvent,
)
from app.schemas.payment import RecoveryPermit

FAKE_WEBHOOK_SECRET = "fake_webhook_secret_for_testing"


class FakePaymentProvider:
    provider = "fake_provider_v1"

    async def create_recovery_link(
        self, *, permit: RecoveryPermit
    ) -> ProviderLinkResult:
        # Stable fake link_id derived from idempotency_key — always same for same permit
        link_id = "fake_link_" + hashlib.md5(permit.idempotency_key.encode()).hexdigest()[:12]
        return ProviderLinkResult(
            provider=self.provider,
            link_id=link_id,
            short_url=f"https://rzp.io/fake/{link_id}",
            amount_paise=permit.amount_paise,
            status="created",
            idempotency_key=permit.idempotency_key,
            expires_at=permit.expires_at,
            environment="fake",
            test_mode_label="FAKE PROVIDER — CI only, no real Razorpay call",
        )

    def verify_webhook(
        self, raw_body: bytes, signature: str
    ) -> VerifiedWebhookEvent:
        expected = hmac.new(
            FAKE_WEBHOOK_SECRET.encode(),
            raw_body,
            "sha256",
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid webhook signature")

        data = json.loads(raw_body)
        return VerifiedWebhookEvent(
            event_id=data.get("event_id", "fake-evt-001"),
            event_type=data.get("event", "payment_link.paid"),
            payment_link_id=data.get("payload", {}).get("payment_link", {}).get("id"),
            payment_id=data.get("payload", {}).get("payment", {}).get("id"),
            order_id=data.get("payload", {}).get("order", {}).get("id"),
            status=data.get("payload", {}).get("payment_link", {}).get("status", "paid"),
            amount_paise=data.get("payload", {}).get("payment_link", {}).get("amount"),
            provider=self.provider,
        )

    async def fetch_payment(self, payment_id: str) -> FetchedPayment:
        # Deterministic synthetic mapping for demo IDs
        pid = payment_id.strip()
        # Map by last char for predictable demos
        suffix = pid[-1].lower() if pid else "0"
        if suffix in "013":
            status, amount = "pending", 49900
        elif suffix in "24":
            status, amount = "captured", 49900
        elif suffix in "56":
            status, amount = "failed", 149900
        elif suffix in "7":
            status, amount = "captured", 99900   # will look captured-unlinked
        else:
            status, amount = "pending", 79900
        return FetchedPayment(
            provider=self.provider,
            found=True,
            payment_id=pid or "pay_demo",
            order_id="order_demo_" + (pid[-4:] if len(pid) >= 4 else "0001"),
            amount_paise=amount,
            status=status,
            method="upi",
            created_at="2026-08-31T00:00:00Z",
            data_source="synthetic_demo",
            note="No Razorpay keys configured — synthetic demo data. Add rzp_test_ keys for real lookups.",
        )
