"""
Extraction service — wires extractor output into a case's evidence.
Enforces trust boundary: extracted CustomerReport becomes PaymentEvidence
with source_type="customer_report" or "synthetic_screenshot".
Never changes payment state or calls recovery tools.
"""
from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.extractor_protocol import ExtractionResult, ExtractionStatus
from app.integrations.fake_extractor import FakeEvidenceExtractor
from app.services.case_service import add_evidence, get_case, CaseNotFoundError


def get_extractor():
    """Return Gemini extractor if key is present, else FakeEvidenceExtractor."""
    if os.getenv("GEMINI_API_KEY"):
        try:
            from app.integrations.gemini_extractor import GeminiEvidenceExtractor
            return GeminiEvidenceExtractor()
        except Exception:
            pass
    return FakeEvidenceExtractor()


async def extract_and_attach(
    db: AsyncSession,
    case_id: str,
    *,
    text: str | None = None,
    screenshot_fixture: str | None = None,
) -> dict:
    """
    Run extraction on text or synthetic screenshot fixture.
    Attach result as PaymentEvidence (source_type=customer_report/synthetic_screenshot).
    Returns extraction result summary — never a payment state or recovery action.
    """
    case = await get_case(db, case_id)
    extractor = get_extractor()

    if screenshot_fixture:
        result: ExtractionResult = await extractor.extract_from_synthetic_screenshot(
            screenshot_fixture
        )
        input_type = "synthetic_screenshot"
    elif text:
        result = await extractor.extract_from_text(text)
        input_type = "customer_report"
    else:
        return {
            "status": "failed",
            "error": "Provide either text or screenshot_fixture.",
            "fallback_action": "OUTCOME_UNKNOWN",
        }

    # Always attach to evidence even on partial/failed — marks the attempt
    source_type = (
        result.customer_report.source_type
        if result.customer_report
        else input_type
    )

    raw_data: dict = {
        "extraction_status": result.status.value,
        "provider": result.provider,
        "trust_boundary": "untrusted_customer_provided",
    }
    if result.customer_report:
        raw_data.update(result.customer_report.model_dump(mode="json"))
    if result.error_message:
        raw_data["error_message"] = result.error_message

    ev = await add_evidence(
        db,
        case_id=case_id,
        source_type=source_type,
        event_reference=result.customer_report.utr_like_reference if result.customer_report else None,
        amount_paise=result.customer_report.reported_amount_paise if result.customer_report else None,
        status=result.customer_report.reported_status if result.customer_report else None,
        occurred_at=result.customer_report.reported_at if result.customer_report else None,
        raw_data=raw_data,
    )

    return {
        "extraction_status": result.status.value,
        "provider": result.provider,
        "evidence_id": ev.id,
        "source_type": source_type,
        "trust_boundary": "untrusted_customer_provided",
        "extracted_fields": result.customer_report.model_dump(mode="json") if result.customer_report else None,
        "error_message": result.error_message,
        "fallback_action": result.fallback_action if result.status == ExtractionStatus.FAILED else None,
        "safety_note": (
            "This evidence is customer-provided and untrusted. "
            "Payment state is determined by gateway/merchant evidence only."
        ),
    }
