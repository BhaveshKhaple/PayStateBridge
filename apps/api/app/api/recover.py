"""Recovery lookup route — paste a payment/order ID, get a real decision."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.lookup_service import lookup_and_decide

router = APIRouter(prefix="/v1/recover", tags=["recover"])


class RecoverLookupRequest(BaseModel):
    payment_id: str | None = None
    order_id: str | None = None
    expected_amount_paise: int | None = None


@router.post("/lookup")
async def recover_lookup(body: RecoverLookupRequest) -> dict:
    return await lookup_and_decide(
        payment_id=body.payment_id,
        order_id=body.order_id,
        expected_amount_paise=body.expected_amount_paise,
    )
