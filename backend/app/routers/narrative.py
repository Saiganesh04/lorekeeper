"""Narrative generation API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GameSession, StoryEvent
from app.schemas.narrative import (
    PlayerActionRequest,
    StoryBeatResponse,
    StoryFeedResponse,
    ChoiceSelectRequest,
    RecapResponse,
    OpeningRequest,
)
from app.services.narrative_engine import get_narrative_engine

router = APIRouter(tags=["narrative"])


def _event_to_response(event: StoryEvent) -> StoryBeatResponse:
    """Convert StoryEvent model to response schema."""
    return StoryBeatResponse(
        id=event.id,
        session_id=event.session_id,
        event_type=event.event_type,
        content=event.content,
        player_action=event.player_action,
        choices=event.choices,
        mood=event.mood or "neutral",
        speaker=event.speaker,
        dice_rolls=event.dice_rolls,
        new_entities=event.new_entities,
        knowledge_updates=event.knowledge_updates,
        xp_awarded=event.xp_awarded,
        items_awarded=event.items_awarded,
        sequence_order=event.sequence_order,
        created_at=event.created_at,
    )


@router.post("/api/sessions/{session_id}/action", response_model=StoryBeatResponse)
async def submit_player_action(
    session_id: str,
    action_data: PlayerActionRequest,
    db: AsyncSession = Depends(get_db),
) -> StoryBeatResponse:
    """Submit a player action and get AI-generated story response."""
    # Verify session exists and is active
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Generate story beat
    narrative_engine = get_narrative_engine()
    event = await narrative_engine.generate_story_beat(
        db=db,
        session_id=session_id,
        player_action=action_data.action,
        additional_context=action_data.context or "",
    )

    return _event_to_response(event)


@router.post("/api/sessions/{session_id}/opening", response_model=StoryBeatResponse)
async def generate_opening(
    session_id: str,
    opening_data: Optional[OpeningRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> StoryBeatResponse:
    """Generate an opening scene for the session."""
    # Verify session exists
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate opening
    narrative_engine = get_narrative_engine()
    opening_data = opening_data or OpeningRequest()

    event = await narrative_engine.generate_opening(
        db=db,
        session_id=session_id,
        style=opening_data.style,
        include_recap=opening_data.include_recap,
    )

    return _event_to_response(event)


@router.post("/api/sessions/{session_id}/choice", response_model=StoryBeatResponse)
async def select_choice(
    session_id: str,
    choice_data: ChoiceSelectRequest,
    db: AsyncSession = Depends(get_db),
) -> StoryBeatResponse:
    """Select a branching choice from a previous story beat."""
    # Verify session exists and is active
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Branch story
    narrative_engine = get_narrative_engine()
    event = await narrative_engine.branch_story(
        db=db,
        session_id=session_id,
        event_id=choice_data.event_id,
        choice_index=choice_data.choice_index,
    )

    return _event_to_response(event)


@router.get("/api/sessions/{session_id}/story", response_model=StoryFeedResponse)
async def get_story_feed(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StoryFeedResponse:
    """Get the story feed for a session."""
    # Verify session exists
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get events
    events_result = await db.execute(
        select(StoryEvent)
        .where(StoryEvent.session_id == session_id)
        .order_by(StoryEvent.sequence_order)
        .offset(skip)
        .limit(limit)
    )
    events = events_result.scalars().all()

    # Get total count
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(StoryEvent.id)).where(
            StoryEvent.session_id == session_id
        )
    )
    total = count_result.scalar()

    # Get current mood from latest event
    current_mood = "neutral"
    if events:
        latest = events[-1]
        current_mood = latest.mood or "neutral"

    # Get current location (would need to query characters)
    current_location = None

    return StoryFeedResponse(
        session_id=session_id,
        events=[_event_to_response(e) for e in events],
        total_events=total,
        current_mood=current_mood,
        current_location=current_location,
    )


@router.post("/api/sessions/{session_id}/recap", response_model=RecapResponse)
async def generate_recap(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> RecapResponse:
    """Generate a recap for the session."""
    # Verify session exists
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate recap
    narrative_engine = get_narrative_engine()
    recap_data = await narrative_engine.generate_recap(db, session_id)

    return RecapResponse(
        session_id=recap_data["session_id"],
        session_number=recap_data["session_number"],
        recap=recap_data["recap"],
        key_events=recap_data["key_events"],
        characters_met=recap_data["characters_met"],
        locations_visited=recap_data["locations_visited"],
        items_acquired=recap_data["items_acquired"],
        total_xp=recap_data["total_xp"],
    )


@router.get("/api/events/{event_id}", response_model=StoryBeatResponse)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
) -> StoryBeatResponse:
    """Get a specific story event."""
    result = await db.execute(
        select(StoryEvent).where(StoryEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return _event_to_response(event)
