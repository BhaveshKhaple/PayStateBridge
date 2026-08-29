"""
Evaluation runner for PayState Bridge.
Runs all synthetic incidents through the classifier and reports metrics.

Usage:
    python -m app.evals.runner              # dev split
    python -m app.evals.runner --split all  # both splits
    python -m app.evals.runner --split heldout

EXIT CODES:
    0 = all safety assertions pass
    1 = unsafe retry-link rate > 0 (CRITICAL SAFETY FAILURE)
    2 = other evaluation error
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.domain.classifier import classify
from app.schemas.payment import (
    PaymentState,
    RecoveryAction,
    SyntheticIncident,
)

DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "incidents"

# States that must NEVER produce a recovery link
UNSAFE_STATES = {PaymentState.PENDING, PaymentState.OUTCOME_UNKNOWN}


def load_split(split: str) -> list[SyntheticIncident]:
    incidents = []
    if split in ("dev", "all"):
        for f in sorted((DATA_DIR / "dev").glob("*.json")):
            incidents.append(SyntheticIncident.model_validate(json.loads(f.read_text())))
    if split in ("heldout", "all"):
        for f in sorted((DATA_DIR / "heldout").glob("*.json")):
            incidents.append(SyntheticIncident.model_validate(json.loads(f.read_text())))
    return incidents


def _hint(inc: SyntheticIncident) -> str:
    notes = inc.notes.lower()
    if "wrong_recipient" in notes or inc.scenario == "WRONG_RECIPIENT":
        return "WRONG_RECIPIENT"
    if "unauthorized" in notes or inc.scenario == "UNAUTHORIZED":
        return "UNAUTHORIZED"
    return ""


def run_evaluation(split: str = "dev") -> dict:
    incidents = load_split(split)
    if not incidents:
        print(f"ERROR: No incidents found for split={split!r}", file=sys.stderr)
        sys.exit(2)

    results = []
    unsafe_retry_cases = []
    correct_state = 0
    captured_unlinked_total = 0
    captured_unlinked_correct = 0
    duplicate_total = 0
    duplicate_correct = 0
    failed_total = 0
    failed_correct = 0
    evidence_packet_total = 0
    evidence_packet_complete = 0
    simulated_gmv_recovered = 0

    for inc in incidents:
        decision = classify(
            inc.merchant_order,
            inc.gateway_events,
            inc.customer_report,
            scenario_hint=_hint(inc),
        )

        state_correct = decision.state == inc.expected_state
        action_correct = decision.action == inc.expected_action

        # Safety: PENDING/OUTCOME_UNKNOWN must never get CREATE_RECOVERY_PERMIT
        if inc.expected_state in UNSAFE_STATES:
            if decision.action == RecoveryAction.CREATE_RECOVERY_PERMIT:
                unsafe_retry_cases.append(inc.incident_id)

        if state_correct:
            correct_state += 1

        # Per-state metrics
        if inc.expected_state == PaymentState.CAPTURED_UNLINKED:
            captured_unlinked_total += 1
            if state_correct:
                captured_unlinked_correct += 1
                simulated_gmv_recovered += inc.simulated_gmv_paise

        if inc.expected_state == PaymentState.DUPLICATE_SUCCESS:
            duplicate_total += 1
            if state_correct:
                duplicate_correct += 1

        if inc.expected_state == PaymentState.FAILED:
            failed_total += 1
            if state_correct:
                failed_correct += 1
                simulated_gmv_recovered += inc.simulated_gmv_paise

        if inc.expected_state in (PaymentState.OUTCOME_UNKNOWN, PaymentState.WRONG_RECIPIENT):
            evidence_packet_total += 1
            has_required = bool(inc.merchant_order.order_id and inc.merchant_order.amount_paise)
            if has_required:
                evidence_packet_complete += 1

        results.append({
            "incident_id": inc.incident_id,
            "split": inc.split,
            "scenario": inc.scenario,
            "expected_state": inc.expected_state.value,
            "actual_state": decision.state.value,
            "expected_action": inc.expected_action.value,
            "actual_action": decision.action.value,
            "state_correct": state_correct,
            "action_correct": action_correct,
            "reason_codes": decision.reason_codes,
        })

    total = len(incidents)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "total_incidents": total,
        "disclaimer": "SIMULATED GMV — synthetic data only, not real money recovered",
        "metrics": {
            "state_accuracy": round(correct_state / total, 4) if total else 0,
            "unsafe_retry_link_rate": len(unsafe_retry_cases) / total if total else 0,
            "unsafe_retry_cases": unsafe_retry_cases,
            "captured_unlinked_recall": (
                round(captured_unlinked_correct / captured_unlinked_total, 4)
                if captured_unlinked_total else None
            ),
            "duplicate_success_recall": (
                round(duplicate_correct / duplicate_total, 4)
                if duplicate_total else None
            ),
            "failed_detection_recall": (
                round(failed_correct / failed_total, 4)
                if failed_total else None
            ),
            "evidence_packet_completeness": (
                round(evidence_packet_complete / evidence_packet_total, 4)
                if evidence_packet_total else None
            ),
            "simulated_gmv_recovered_paise": simulated_gmv_recovered,
            "simulated_gmv_recovered_rupees": round(simulated_gmv_recovered / 100, 2),
        },
        "results": results,
    }
    return report


def print_markdown_report(report: dict) -> None:
    m = report["metrics"]
    unsafe = m["unsafe_retry_cases"]
    print(f"""
# PayState Bridge — Evaluation Report

**Generated:** {report["generated_at"]}
**Split:** {report["split"]}
**Total incidents:** {report["total_incidents"]}

> {report["disclaimer"]}

## Safety (CRITICAL)

| Metric | Value | Target |
|---|---|---|
| Unsafe retry-link rate | {m["unsafe_retry_link_rate"]:.1%} | **0%** |
| Unsafe cases | {unsafe if unsafe else "None"} | None |

{"WARNING: SAFETY FAILURE: Unsafe retry cases detected!" if unsafe else "Safety gate PASSED -- zero unsafe retry-link cases."}

## Accuracy Metrics

| Metric | Value |
|---|---|
| State classification accuracy | {m["state_accuracy"]:.1%} |
| Captured-unlinked recall | {f"{m['captured_unlinked_recall']:.1%}" if m['captured_unlinked_recall'] is not None else "N/A"} |
| Duplicate-success recall | {f"{m['duplicate_success_recall']:.1%}" if m['duplicate_success_recall'] is not None else "N/A"} |
| Failed detection recall | {f"{m['failed_detection_recall']:.1%}" if m['failed_detection_recall'] is not None else "N/A"} |
| Evidence-packet completeness | {f"{m['evidence_packet_completeness']:.1%}" if m['evidence_packet_completeness'] is not None else "N/A"} |

## Simulated GMV

| Metric | Value |
|---|---|
| Simulated GMV recovered (paise) | {m["simulated_gmv_recovered_paise"]:,} |
| Simulated GMV recovered (Rs) | Rs {m["simulated_gmv_recovered_rupees"]:,.2f} |

*All GMV figures are simulated from synthetic incidents only.*
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="PayState Bridge evaluation runner")
    parser.add_argument("--split", default="dev", choices=["dev", "heldout", "all"])
    parser.add_argument("--json-out", default=None, help="Write JSON report to file")
    args = parser.parse_args()

    report = run_evaluation(args.split)
    print_markdown_report(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2))
        print(f"\nJSON report written to: {args.json_out}")

    # Safety gate -- exit non-zero if unsafe retry rate > 0
    unsafe = report["metrics"]["unsafe_retry_cases"]
    if unsafe:
        print(f"\nSAFETY GATE FAILED: {len(unsafe)} unsafe retry-link case(s): {unsafe}", file=sys.stderr)
        sys.exit(1)

    print(f"\nEvaluation complete. {report['total_incidents']} incidents. Safety gate passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
