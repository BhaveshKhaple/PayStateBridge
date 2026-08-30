"""
Recovery lookup service — the 'paste a payment/order ID' entry point.
Fetches a payment (real Razorpay Test Mode if configured, else synthetic demo),
builds the evidence, runs the REAL deterministic classifier, returns the decision.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.domain.classifier import classify
from app.schemas.payment import GatewayPaymentEvent, MerchantOrderSchema
from app.services.recovery_link_service import get_payment_provider


async def lookup_and_decide(
    *,
    payment_id: str | None = None,
    order_id: str | None = None,
    expected_amount_paise: int | None = None,
) -> dict:
    if not payment_id and not order_id:
        return {"error": "Provide a payment_id or order_id."}

    provider = get_payment_provider()

    # If only order_id given, we still try payment_id path; provider fetch is by payment_id.
    lookup_id = payment_id or order_id or ""
    fetched = await provider.fetch_payment(lookup_id)

    if not fetched.found:
        return {
            "found": False,
            "data_source": fetched.data_source,
            "note": fetched.note,
            "lookup_id": lookup_id,
        }

    resolved_order_id = order_id or fetched.order_id or f"ORD-{lookup_id[-6:]}"
    amount = expected_amount_paise or fetched.amount_paise or 0

    order = MerchantOrderSchema(
        order_id=resolved_order_id,
        reference=resolved_order_id,
        amount_paise=amount if amount > 0 else 1,
        status="payment_pending",
        created_at=datetime.now(timezone.utc),
    )

    gateway_events: list[GatewayPaymentEvent] = []
    if fetched.status:
        gateway_events.append(
            GatewayPaymentEvent(
                provider="razorpay_test" if fetched.data_source == "razorpay_test" else "synthetic",
                provider_payment_id=fetched.payment_id,
                provider_order_id=fetched.order_id,
                amount_paise=fetched.amount_paise or amount or 1,
                status=fetched.status,  # created/authorized mapped to pending already
                occurred_at=datetime.now(timezone.utc),
                raw_event_id=fetched.payment_id,
                source="gateway_event",
            )
        )

    decision = classify(order, gateway_events, None)

    return {
        "found": True,
        "data_source": fetched.data_source,
        "note": fetched.note,
        "payment": {
            "payment_id": fetched.payment_id,
            "order_id": fetched.order_id,
            "amount_paise": fetched.amount_paise,
            "amount_rupees": round((fetched.amount_paise or 0) / 100, 2),
            "status": fetched.status,
            "raw_status": fetched.raw_status,
            "method": fetched.method,
        },
        "decision": {
            "state": decision.state.value,
            "action": decision.action.value,
            "reason_codes": decision.reason_codes,
            "customer_message": decision.customer_message,
            "policy_version": decision.policy_version,
        },
        "safe": decision.action.value not in ("CREATE_RECOVERY_PERMIT",) or decision.state.value == "FAILED",
    }
