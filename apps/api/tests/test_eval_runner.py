"""Tests for evaluation runner safety gate."""
from __future__ import annotations

import pytest
from app.evals.runner import run_evaluation, UNSAFE_STATES
from app.schemas.payment import PaymentState, RecoveryAction


def test_dev_split_loads_at_least_36_incidents():
    report = run_evaluation("dev")
    assert report["total_incidents"] >= 36


def test_heldout_split_loads_at_least_24_incidents():
    report = run_evaluation("heldout")
    assert report["total_incidents"] >= 24


def test_state_accuracy_above_threshold():
    report = run_evaluation("dev")
    assert report["metrics"]["state_accuracy"] >= 0.85, (
        f"State accuracy {report['metrics']['state_accuracy']:.1%} below 85% threshold"
    )


def test_safety_gate_unsafe_retry_rate_is_zero():
    report = run_evaluation("dev")
    assert report["metrics"]["unsafe_retry_link_rate"] == 0.0, (
        f"SAFETY FAILURE: Unsafe cases: {report['metrics']['unsafe_retry_cases']}"
    )


def test_heldout_safety_gate_zero():
    report = run_evaluation("heldout")
    assert report["metrics"]["unsafe_retry_link_rate"] == 0.0


def test_gmv_disclaimer_present():
    report = run_evaluation("dev")
    assert "SIMULATED" in report["disclaimer"].upper()


def test_captured_unlinked_recall_reported():
    report = run_evaluation("dev")
    assert report["metrics"]["captured_unlinked_recall"] is not None
