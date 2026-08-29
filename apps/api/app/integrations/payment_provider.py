"""
Payment provider protocol and shared types.
FakePaymentProvider is used in all CI tests.
RazorpayTestModeProvider is used only with valid rzp_test_ credentials.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

from app.schemas.payment import RecoveryPermit


class ProviderLinkResult(BaseModel):
    provider: str
    link_id: str
    short_url: str
    amount_paise: int
    status: str
    idempotency_key: str
    expires_at: datetime
    environment: Literal["test", "fake"]
    test_mode_label: str = "TEST MODE — no real money"


class VerifiedWebhookEvent(BaseModel):
    event_id: str
    event_type: str
    payment_link_id: str | None
    payment_id: str | None
    order_id: str | None
    status: str
    amount_paise: int | None
    provider: str


@runtime_checkable
class PaymentProvider(Protocol):
    async def create_recovery_link(
        self, *, permit: RecoveryPermit
    ) -> ProviderLinkResult: ...

    def verify_webhook(
        self, raw_body: bytes, signature: str
    ) -> VerifiedWebhookEvent: ...
