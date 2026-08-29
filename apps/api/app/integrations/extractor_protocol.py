"""
Extractor protocol and shared result schema.
All extractors (fake or real) return ExtractionResult — never a payment state or action.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractedCustomerReport(BaseModel):
    """
    Structured fields extracted from untrusted customer text or synthetic screenshot.
    ALWAYS labelled as untrusted — never used as authoritative payment evidence.
    """
    source_type: Literal["customer_report", "synthetic_screenshot"]
    trust_boundary: Literal["untrusted_customer_provided"] = "untrusted_customer_provided"
    confidence_level: Literal["high", "medium", "low", "none"] = "low"

    # Extracted fields — all optional because AI may miss them
    reported_amount_paise: int | None = Field(default=None, ge=1)
    reported_status: Literal["success", "failed", "pending", "unknown"] | None = None
    utr_like_reference: str | None = Field(default=None, max_length=64)
    reported_at: datetime | None = None
    original_message: str | None = Field(default=None, max_length=2000)
    missing_fields: list[str] = Field(default_factory=list)
    extraction_notes: str = ""


class ExtractionResult(BaseModel):
    status: ExtractionStatus
    customer_report: ExtractedCustomerReport | None = None
    error_message: str | None = None
    fallback_action: Literal["OUTCOME_UNKNOWN", "human_review"] = "OUTCOME_UNKNOWN"
    provider: str = "unknown"


@runtime_checkable
class EvidenceExtractor(Protocol):
    """Protocol all extractors must satisfy."""

    async def extract_from_text(self, text: str) -> ExtractionResult: ...

    async def extract_from_synthetic_screenshot(
        self, fixture_name: str
    ) -> ExtractionResult: ...
