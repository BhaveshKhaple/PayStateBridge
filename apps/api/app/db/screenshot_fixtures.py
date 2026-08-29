"""
Synthetic screenshot fixture registry.
Real screenshots from PhonePe/GPay/bank apps must NEVER be used.
Only synthetic mock data is permitted.
"""
from __future__ import annotations

SYNTHETIC_SCREENSHOTS: dict[str, dict] = {
    "phonepay_success_999": {
        "app": "PhonePe (synthetic mock)",
        "description": "Synthetic PhonePe-style success receipt showing ₹999 deduction",
        "fields_visible": ["amount", "status", "utr_like_reference", "timestamp"],
        "synthetic": True,
        "disclaimer": "SYNTHETIC DATA — not a real PhonePe screenshot",
    },
    "phonepay_pending_499": {
        "app": "PhonePe (synthetic mock)",
        "description": "Synthetic PhonePe-style pending status showing ₹499",
        "fields_visible": ["amount", "status", "timestamp"],
        "synthetic": True,
        "disclaimer": "SYNTHETIC DATA — not a real PhonePe screenshot",
    },
    "gpay_failed_1499": {
        "app": "Google Pay (synthetic mock)",
        "description": "Synthetic GPay-style failed transaction showing ₹1,499",
        "fields_visible": ["amount", "status", "utr_like_reference"],
        "synthetic": True,
        "disclaimer": "SYNTHETIC DATA — not a real Google Pay screenshot",
    },
}


def list_fixtures() -> list[dict]:
    return [
        {"fixture_name": name, **meta}
        for name, meta in SYNTHETIC_SCREENSHOTS.items()
    ]


def get_fixture(name: str) -> dict | None:
    return SYNTHETIC_SCREENSHOTS.get(name)
