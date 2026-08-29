"""
GeminiEvidenceExtractor — uses Gemini structured output to parse
synthetic customer messages into ExtractedCustomerReport.

Safety boundaries (enforced here and by Pydantic):
- Output is ALWAYS tagged untrusted_customer_provided.
- Timeout, bad schema, or injection → ExtractionResult(status=FAILED).
- Model output is NEVER used to set payment state or call Razorpay.
- Max input length: 2000 characters.
- Max retries: 1.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime, timezone

import httpx

from app.integrations.extractor_protocol import (
    ExtractedCustomerReport,
    ExtractionResult,
    ExtractionStatus,
)
from app.integrations.fake_extractor import _detect_injection

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
MAX_INPUT_LENGTH = 2000
TIMEOUT_SECONDS = 10.0
MAX_RETRIES = 1

_EXTRACTION_PROMPT = """You are a payment evidence parser for a merchant support tool.
Your ONLY job is to extract structured fields from the customer's message.

HARD RULES:
1. Output ONLY the JSON fields listed below. Nothing else.
2. Do NOT decide whether the payment succeeded or failed authoritatively.
3. Do NOT suggest creating payment links, refunds, or any recovery actions.
4. Do NOT call any tools or APIs.
5. If a field is not clearly present, output null for that field.
6. reported_status must be exactly one of: "success", "failed", "pending", "unknown".

Output JSON with exactly these fields:
{
  "reported_amount_paise": <integer paise, e.g. 99900 for ₹999, or null>,
  "reported_status": <"success"|"failed"|"pending"|"unknown"|null>,
  "utr_like_reference": <string max 64 chars or null>,
  "extraction_notes": <short string explaining what you found or could not find>,
  "missing_fields": <list of field names you could not extract>
}

Customer message to parse:
"""


def _parse_gemini_response(raw: str) -> dict:
    """Extract JSON from Gemini response text, stripping markdown fences."""
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


class GeminiEvidenceExtractor:
    """Live Gemini extractor. Falls back to FAILED on any error."""

    provider = "gemini-1.5-flash"

    def __init__(self) -> None:
        self._api_key = os.environ["GEMINI_API_KEY"]

    async def extract_from_text(self, text: str) -> ExtractionResult:
        # Pre-flight: injection detection
        if _detect_injection(text):
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                error_message="Injection pattern detected before API call.",
                fallback_action="OUTCOME_UNKNOWN",
                provider=self.provider,
            )

        # Truncate to max length
        truncated = text[:MAX_INPUT_LENGTH]
        prompt = _EXTRACTION_PROMPT + truncated

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 256,
            },
        }

        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                    resp = await client.post(
                        f"{GEMINI_API_URL}?key={self._api_key}",
                        json=payload,
                    )
                resp.raise_for_status()
                data = resp.json()
                raw_text = (
                    data["candidates"][0]["content"]["parts"][0]["text"]
                )
                parsed = _parse_gemini_response(raw_text)

                # Validate with Pydantic
                report = ExtractedCustomerReport(
                    source_type="customer_report",
                    trust_boundary="untrusted_customer_provided",
                    confidence_level="medium",
                    reported_amount_paise=parsed.get("reported_amount_paise"),
                    reported_status=parsed.get("reported_status"),
                    utr_like_reference=parsed.get("utr_like_reference"),
                    original_message=truncated,
                    missing_fields=parsed.get("missing_fields", []),
                    extraction_notes=parsed.get("extraction_notes", ""),
                )

                return ExtractionResult(
                    status=ExtractionStatus.SUCCESS,
                    customer_report=report,
                    provider=self.provider,
                )

            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == MAX_RETRIES:
                    return ExtractionResult(
                        status=ExtractionStatus.FAILED,
                        error_message=f"Gemini API error after {MAX_RETRIES + 1} attempts: {e}",
                        fallback_action="OUTCOME_UNKNOWN",
                        provider=self.provider,
                    )
                await asyncio.sleep(1.0)

            except (KeyError, IndexError, json.JSONDecodeError, Exception) as e:
                return ExtractionResult(
                    status=ExtractionStatus.FAILED,
                    error_message=f"Gemini response parse error: {type(e).__name__}: {e}",
                    fallback_action="OUTCOME_UNKNOWN",
                    provider=self.provider,
                )

        # Should not reach here
        return ExtractionResult(
            status=ExtractionStatus.FAILED,
            error_message="Unexpected extractor exit.",
            fallback_action="OUTCOME_UNKNOWN",
            provider=self.provider,
        )

    async def extract_from_synthetic_screenshot(
        self, fixture_name: str
    ) -> ExtractionResult:
        """For screenshot intake, delegate to FakeExtractor (uses synthetic fixtures only)."""
        from app.integrations.fake_extractor import FakeEvidenceExtractor
        fake = FakeEvidenceExtractor()
        result = await fake.extract_from_synthetic_screenshot(fixture_name)
        # Re-label provider
        if result.customer_report:
            result.customer_report.extraction_notes += " (via GeminiEvidenceExtractor fixture delegation)"
        return result
