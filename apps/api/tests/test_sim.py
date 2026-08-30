"""Tests for the PayState World simulator engine."""
from __future__ import annotations

import pytest

from app.sim.engine import run_story_classifier
from app.sim.stories import STORIES, get_story, list_stories


def test_three_stories_exist():
    assert len(STORIES) == 3
    assert "lost_webhook" in STORIES
    assert "cab_driver" in STORIES
    assert "portal_timeout" in STORIES


def test_list_stories_returns_metadata():
    stories = list_stories()
    assert len(stories) == 3
    for s in stories:
        assert "story_id" in s
        assert "title" in s
        assert s["event_count"] > 0


@pytest.mark.parametrize("story_id", list(STORIES.keys()))
def test_story_classifier_matches_expected(story_id: str):
    """INTEGRITY: the real classifier must produce the story's expected outcome."""
    story = get_story(story_id)
    decision = run_story_classifier(story)
    assert decision["state"] == story.expected_final_state, (
        f"{story_id}: classifier gave {decision['state']}, expected {story.expected_final_state}"
    )
    assert decision["action"] == story.expected_final_action


def test_lost_webhook_recovers_gmv():
    decision = run_story_classifier(get_story("lost_webhook"))
    assert decision["state"] == "CAPTURED_UNLINKED"
    assert decision["action"] == "RECONCILE_ORDER"


def test_cab_driver_opens_review_not_refund():
    decision = run_story_classifier(get_story("cab_driver"))
    assert decision["state"] == "DUPLICATE_SUCCESS"
    assert decision["action"] == "OPEN_DUPLICATE_REVIEW"


def test_portal_timeout_refuses_to_guess():
    decision = run_story_classifier(get_story("portal_timeout"))
    assert decision["state"] == "OUTCOME_UNKNOWN"


def test_events_are_time_ordered():
    for story in STORIES.values():
        offsets = [e.t_offset_ms for e in story.events]
        assert offsets == sorted(offsets), f"{story.story_id} events not time-ordered"
