"""Tests for legal state transition enforcement."""
import pytest

from app.domain.state_machine import (
    LEGAL_TRANSITIONS,
    TERMINAL_STATES,
    assert_legal_transition,
    is_legal_transition,
)


def test_case_opened_can_transition_to_evidence_collecting():
    assert is_legal_transition("CASE_OPENED", "EVIDENCE_COLLECTING")


def test_cannot_skip_directly_from_opened_to_classified():
    assert not is_legal_transition("CASE_OPENED", "CLASSIFIED")


def test_classified_can_go_to_recovery_permit_issued():
    assert is_legal_transition("CLASSIFIED", "RECOVERY_PERMIT_ISSUED")


def test_pending_state_cannot_go_to_recovery_link():
    # PENDING is a payment state, not a lifecycle state — but classified PENDING
    # must go through WAITING_RECONCILIATION before permit, not directly
    assert is_legal_transition("CLASSIFIED", "WAITING_RECONCILIATION")
    assert not is_legal_transition("CLASSIFIED", "RECOVERY_LINK_CREATED")


def test_terminal_states_have_no_outgoing_transitions():
    for state in TERMINAL_STATES:
        assert LEGAL_TRANSITIONS[state] == set()


def test_assert_legal_raises_on_illegal_transition():
    with pytest.raises(ValueError, match="Illegal state transition"):
        assert_legal_transition("CASE_OPENED", "RECOVERY_LINK_CREATED")


def test_assert_legal_passes_on_valid_transition():
    assert_legal_transition("CASE_OPENED", "EVIDENCE_COLLECTING")  # no error
