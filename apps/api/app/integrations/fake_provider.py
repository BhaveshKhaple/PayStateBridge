"""
FakePaymentProvider — deterministic provider for CI tests.
Never makes HTTP calls. Never requires credentials.
Always returns stable fake link_id based on idempotency_key.
"""
from __future__ import annotations

import hashlib
import hmac
import json

from app.integrations.payment_provider import ProviderLinkResult, VerifiedWebhookEvent
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
