"""
RazorpayTestModeProvider — creates Test Mode Payment Links via Razorpay API.
Only active when rzp_test_ credentials are configured.
Uses idempotency_key to prevent duplicate link creation.
"""
from __future__ import annotations

import hmac
import json
import os

import httpx

from app.integrations.payment_provider import ProviderLinkResult, VerifiedWebhookEvent
from app.schemas.payment import RecoveryPermit

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
TIMEOUT_SECONDS = 15.0


class RazorpayConfigError(Exception):
    pass


class RazorpayTestModeProvider:
    provider = "razorpay_test_mode"

    def __init__(self) -> None:
        self._key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        self._key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        self._webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

        if not self._key_id.startswith("rzp_test_"):
            raise RazorpayConfigError(
                "RAZORPAY_KEY_ID must start with 'rzp_test_'. Live keys are not permitted."
            )

    async def create_recovery_link(
        self, *, permit: RecoveryPermit
    ) -> ProviderLinkResult:
        payload = {
            "amount": permit.amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": f"PayState Bridge recovery — order {permit.order_id}",
            "reference_id": permit.idempotency_key,
            "expire_by": int(permit.expires_at.timestamp()),
            "reminder_enable": False,
            "notify": {"sms": False, "email": False},
        }

        async with httpx.AsyncClient(
            auth=(self._key_id, self._key_secret),
            timeout=TIMEOUT_SECONDS,
        ) as client:
            resp = await client.post(
                f"{RAZORPAY_API_BASE}/payment_links",
                json=payload,
                headers={"Idempotency-Key": permit.idempotency_key},
            )
            resp.raise_for_status()
            data = resp.json()

        return ProviderLinkResult(
            provider=self.provider,
            link_id=data["id"],
            short_url=data.get("short_url", ""),
            amount_paise=data["amount"],
            status=data.get("status", "created"),
            idempotency_key=permit.idempotency_key,
            expires_at=permit.expires_at,
            environment="test",
            test_mode_label="Razorpay TEST MODE — no real money charged",
        )

    def verify_webhook(
        self, raw_body: bytes, signature: str
    ) -> VerifiedWebhookEvent:
        if not self._webhook_secret:
            raise ValueError("RAZORPAY_WEBHOOK_SECRET not configured")

        expected = hmac.new(
            self._webhook_secret.encode(),
            raw_body,
            "sha256",
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise ValueError("Invalid Razorpay webhook signature")

        data = json.loads(raw_body)
        payload = data.get("payload", {})
        pl = payload.get("payment_link", {}).get("entity", {})
        pay = payload.get("payment", {}).get("entity", {})

        return VerifiedWebhookEvent(
            event_id=data.get("id", ""),
            event_type=data.get("event", ""),
            payment_link_id=pl.get("id"),
            payment_id=pay.get("id"),
            order_id=pl.get("reference_id"),
            status=pl.get("status", ""),
            amount_paise=pl.get("amount"),
            provider=self.provider,
        )
