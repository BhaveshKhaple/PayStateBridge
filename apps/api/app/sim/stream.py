"""
SSE stream for PayState World.
Streams a story's events at deterministic timings, then emits the REAL
classifier decision as the final AGENT_DECISION event.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.sim.engine import run_story_classifier
from app.sim.stories import get_story, list_stories

router = APIRouter(prefix="/v1/sim", tags=["simulator"])

# Speed multiplier: 1.0 = real-time, >1 = faster. Demo default 1.0.
DEFAULT_SPEED = 1.0
MAX_WAIT_MS = 8000  # cap any single gap so demo never stalls


@router.get("/stories")
async def stories_route() -> list[dict]:
    return list_stories()


@router.get("/stories/{story_id}")
async def story_detail_route(story_id: str) -> dict:
    story = get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"Story {story_id!r} not found")
    decision = run_story_classifier(story)
    return {
        "story": story.model_dump(mode="json"),
        "agent_decision": decision,
    }


async def _event_generator(story_id: str, speed: float):
    story = get_story(story_id)
    if not story:
        yield f"event: error\ndata: {json.dumps({'error': 'story not found'})}\n\n"
        return

    # Emit a start event
    yield f"event: start\ndata: {json.dumps({'story_id': story.story_id, 'title': story.title})}\n\n"

    prev_offset = 0
    for ev in sorted(story.events, key=lambda e: e.t_offset_ms):
        gap_ms = min((ev.t_offset_ms - prev_offset) / max(speed, 0.1), MAX_WAIT_MS)
        if gap_ms > 0:
            await asyncio.sleep(gap_ms / 1000.0)
        prev_offset = ev.t_offset_ms
        yield f"event: sim\ndata: {json.dumps(ev.model_dump(mode='json'))}\n\n"

    # Run the REAL classifier and emit the decision
    decision = run_story_classifier(story)
    yield f"event: decision\ndata: {json.dumps(decision)}\n\n"

    # Verify decision matches expected (integrity signal)
    matched = (
        decision["state"] == story.expected_final_state
        and decision["action"] == story.expected_final_action
    )
    yield f"event: end\ndata: {json.dumps({'story_id': story.story_id, 'decision_matches_expected': matched})}\n\n"


@router.get("/stream")
async def stream_route(
    story: str = Query(..., description="story_id"),
    speed: float = Query(DEFAULT_SPEED, ge=0.1, le=10.0),
) -> StreamingResponse:
    if not get_story(story):
        raise HTTPException(status_code=404, detail=f"Story {story!r} not found")
    return StreamingResponse(
        _event_generator(story, speed),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
