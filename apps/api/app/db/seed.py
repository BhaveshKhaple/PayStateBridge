"""
Seed script — loads all synthetic dev incidents into SQLite.
Usage: python -m app.db.seed
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import MerchantOrder, PaymentCase, PaymentEvidence
from app.schemas.payment import SyntheticIncident

INCIDENTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "incidents" / "dev"


def load_incident_files() -> list[SyntheticIncident]:
    incidents: list[SyntheticIncident] = []
    files = sorted(INCIDENTS_DIR.glob("*.json"))
    if not files:
        print(f"No JSON files found in {INCIDENTS_DIR}", file=sys.stderr)
        sys.exit(1)
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        incidents.append(SyntheticIncident.model_validate(data))
    return incidents


async def seed() -> None:
    await init_db()
    incidents = load_incident_files()

    async with AsyncSessionLocal() as db:
        for inc in incidents:
            # Upsert MerchantOrder
            result = await db.execute(
                select(MerchantOrder).where(MerchantOrder.order_id == inc.merchant_order.order_id)
            )
            order = result.scalar_one_or_none()
            if not order:
                order = MerchantOrder(
                    order_id=inc.merchant_order.order_id,
                    reference=inc.merchant_order.reference,
                    amount_paise=inc.merchant_order.amount_paise,
                    status=inc.merchant_order.status,
                    created_at=inc.merchant_order.created_at,
                )
                db.add(order)
                await db.flush()

            # Create PaymentCase
            case = PaymentCase(
                order_id=inc.merchant_order.order_id,
                state="CLASSIFIED",
                payment_state=inc.expected_state.value,
                action=inc.expected_action.value,
                incident_id=inc.incident_id,
            )
            db.add(case)
            await db.flush()

            # Add gateway evidence
            for evt in inc.gateway_events:
                ev = PaymentEvidence(
                    case_id=case.id,
                    source_type=evt.source,
                    event_reference=evt.provider_payment_id,
                    amount_paise=evt.amount_paise,
                    status=evt.status,
                    occurred_at=evt.occurred_at,
                    raw_data=evt.model_dump(mode="json"),
                )
                db.add(ev)

            # Add customer report evidence
            if inc.customer_report:
                cr = PaymentEvidence(
                    case_id=case.id,
                    source_type=inc.customer_report.source,
                    event_reference=inc.customer_report.utr_like_reference,
                    amount_paise=inc.customer_report.amount_paise,
                    status=inc.customer_report.reported_status,
                    occurred_at=inc.customer_report.occurred_at,
                    raw_data=inc.customer_report.model_dump(mode="json"),
                )
                db.add(cr)

        await db.commit()

    print(f"Seeded {len(incidents)} synthetic dev incidents into SQLite.")
    print("SYNTHETIC DATA ONLY — no real payment data.")


if __name__ == "__main__":
    asyncio.run(seed())
