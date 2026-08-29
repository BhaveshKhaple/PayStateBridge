"""
FakeEvidenceExtractor — deterministic extractor for tests and CI.

Parses well-known synthetic fixture patterns into ExtractedCustomerReport.
Used when GEMINI_API_KEY is absent or during testing.
Never uses an LLM. Always returns the same output for the same input.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.integrations.extractor_protocol import (
    ExtractedCustomerReport,
    ExtractionResult,
    ExtractionStatus,
)

# Synthetic screenshot fixtures (keyed by fixture name)
_SCREENSHOT_FIXTURES: dict[str, dict] = {
    "phonepay_success_999": {
        "reported_amount_paise": 99900,
        "reported_status": "success",
        "utr_like_reference": "SYN-UTR-20260830-001",
        "reported_at": datetime(2026, 8, 30, 8, 1, 0, tzinfo=timezone.utc),
        "confidence_level": "medium",
    },
    "phonepay_pending_499": {
        "reported_amount_paise": 49900,
        "reported_status": "pending",
        "utr_like_reference": "SYN-UTR-20260830-002",
        "reported_at": datetime(2026, 8, 30, 9, 0, 0, tzinfo=timezone.utc),
        "confidence_level": "medium",
    },
    "gpay_failed_1499": {
        "reported_amount_paise": 149900,
        "reported_status": "failed",
        "utr_like_reference": "SYN-UTR-20260830-003",
        "reported_at": datetime(2026, 8, 30, 10, 0, 0, tzinfo=timezone.utc),
        "confidence_level": "medium",
    },
}

# Injection patterns to detect and block
_INJECTION_PATTERNS = [
    r"ignore\s+(the\s+)?rules",
    r"create\s+(a\s+)?payment\s+link",
    r"generate\s+(a\s+)?refund",
    r"override\s+(the\s+)?policy",
    r"mark\s+(the\s+)?order\s+paid",
    r"system\s*prompt",
    r"forget\s+(the\s+)?instructions",
    r"act\s+as\s+(an?\s+)?",
]

_AMOUNT_PATTERN = re.compile(r"₹\s*(\d[\d,]*(?:\.\d{1,2})?)")
_UTR_PATTERN = re.compile(r"(?:UTR|SYN-UTR)[:\s\-]*([\w\-]+)", re.IGNORECASE)
_STATUS_PATTERN = re.compile(
    r"\b(success(?:ful)?|failed?|failure|pending|deducted|debited|credited)\b",
    re.IGNORECASE,
)

_STATUS_MAP = {
    "success": "success",
    "successful": "success",
    "debited": "success",
    "credited": "success",
    "deducted": "success",
    "failed": "failed",
    "fail": "failed",
    "failure": "failed",
    "pending": "pending",
}


def _detect_injection(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in _INJECTION_PATTERNS)


def _parse_amount(text: str) -> int | None:
    match = _AMOUNT_PATTERN.search(text)
    if not match:
        return None
    raw = match.group(1).replace(",", "")
    try:
        rupees = float(raw)
        return int(rupees * 100)
    except ValueError:
        return None


def _parse_status(text: str) -> str | None:
    match = _STATUS_PATTERN.search(text)
    if not match:
        return None
    word = match.group(1).lower()
    return _STATUS_MAP.get(word, "unknown")


def _parse_utr(text: str) -> str | None:
    match = _UTR_PATTERN.search(text)
    return match.group(1) if match else None


class FakeEvidenceExtractor:
    """Deterministic extractor — same input always produces same output."""

    provider = "fake_extractor_v1"

    async def extract_from_text(self, text: str) -> ExtractionResult:
        # Detect injection attempts first
        if _detect_injection(text):
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message="Injection pattern detected. Extraction refused.",
                fallback_action="OUTCOME_UNKNOWN",
                provider=self.provider,
            )

        # Parse synthetic text
        amount = _parse_amount(text)
        status = _parse_status(text)
        utr = _parse_utr(text)

        missing: list[str] = []
        if amount is None:
            missing.append("amount")
        if status is None:
            missing.append("reported_status")

        # Determine confidence
        fields_found = sum(x is not None for x in [amount, status, utr])
        confidence = (
            "high" if fields_found >= 3
            else "medium" if fields_found == 2
            else "low" if fields_found == 1
            else "none"
        )

        report = ExtractedCustomerReport(
            source_type="customer_report",
            trust_boundary="untrusted_customer_provided",
            confidence_level=confidence,
            reported_amount_paise=amount,
            reported_status=status,
            utr_like_reference=utr,
            original_message=text[:500],
            missing_fields=missing,
            extraction_notes="Parsed by FakeEvidenceExtractor — deterministic, no LLM.",
        )

        ext_status = (
            ExtractionStatus.SUCCESS
            if fields_found >= 2
            else ExtractionStatus.PARTIAL
            if fields_found == 1
            else ExtractionStatus.FAILED
        )

        return ExtractionResult(
            status=ext_status,
            customer_report=report,
            provider=self.provider,
        )

    async def extract_from_synthetic_screenshot(
        self, fixture_name: str
    ) -> ExtractionResult:
        fixture = _SCREENSHOT_FIXTURES.get(fixture_name)
        if not fixture:
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message=f"Unknown synthetic screenshot fixture: {fixture_name!r}",
                fallback_action="OUTCOME_UNKNOWN",
                provider=self.provider,
            )

        report = ExtractedCustomerReport(
            source_type="synthetic_screenshot",
            trust_boundary="untrusted_customer_provided",
            extraction_notes=f"Loaded from synthetic fixture: {fixture_name}",
            **fixture,
        )

        return ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            customer_report=report,
            provider=self.provider,
        )
