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

from app.integrations.payment_provider import (
    FetchedPayment,
    ProviderLinkResult,
    VerifiedWebhookEvent,
)
from app.schemas.payment import RecoveryPermit

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
TIMEOUT_SECONDS = 15.0


class RazorpayConfigError(Exception):
    pass


def _map_razorpay_status(status: str, captured: bool) -> str:
    # Razorpay: created, authorized, captured, refunded, failed
    if status == "captured" or captured:
        return "captured"
    if status == "failed":
        return "failed"
    if status in ("created", "authorized"):
        return "pending"   # authorized-but-not-captured is the classic ambiguity
    return "pending"


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

    async def fetch_payment(self, payment_id: str) -> FetchedPayment:
        """Fetch a real payment from Razorpay Test Mode: GET /v1/payments/{id}."""
        async with httpx.AsyncClient(
            auth=(self._key_id, self._key_secret), timeout=TIMEOUT_SECONDS
        ) as client:
            resp = await client.get(f"{RAZORPAY_API_BASE}/payments/{payment_id}")
        if resp.status_code == 404:
            return FetchedPayment(
                provider=self.provider,
                found=False,
                payment_id=payment_id,
                data_source="razorpay_test",
                note="Payment not found in Razorpay Test Mode.",
            )
        resp.raise_for_status()
        d = resp.json()
        # Map Razorpay status → our gateway status vocabulary
        razorpay_status = d.get("status", "")
        mapped = _map_razorpay_status(razorpay_status, d.get("captured", False))
        return FetchedPayment(
            provider=self.provider,
            found=True,
            payment_id=d.get("id", payment_id),
            order_id=d.get("order_id"),
            amount_paise=d.get("amount"),
            status=mapped,
            method=d.get("method"),
            created_at=str(d.get("created_at", "")),
            data_source="razorpay_test",
            raw_status=razorpay_status,
        )
