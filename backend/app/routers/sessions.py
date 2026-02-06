"""Game session management API endpoints."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign, GameSession, StoryEvent, Encounter
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionEndRequest,
)
from app.services.narrative_engine import get_narrative_engine

router = APIRouter(tags=["sessions"])


@router.post("/api/campaigns/{campaign_id}/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    campaign_id: str,
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Start a new game session for a campaign."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get next session number
    count_result = await db.execute(
        select(func.count(GameSession.id)).where(
            GameSession.campaign_id == campaign_id
        )
    )
    session_number = count_result.scalar() + 1

    # Create session
    session = GameSession(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        session_number=session_number,
        status="active",
        notes=session_data.notes,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=session.id,
        campaign_id=session.campaign_id,
        session_number=session.session_number,
        status=session.status,
        recap=session.recap,
        notes=session.notes,
        started_at=session.started_at,
        ended_at=session.ended_at,
        event_count=0,
        encounter_count=0,
    )


@router.get("/api/campaigns/{campaign_id}/sessions", response_model=SessionListResponse)
async def list_sessions(
    campaign_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List all sessions for a campaign."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get sessions
    result = await db.execute(
        select(GameSession)
        .where(GameSession.campaign_id == campaign_id)
        .order_by(GameSession.session_number.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count(GameSession.id)).where(
            GameSession.campaign_id == campaign_id
        )
    )
    total = count_result.scalar()

    # Build responses with counts
    session_responses = []
    for session in sessions:
        event_count = await db.execute(
            select(func.count(StoryEvent.id)).where(
                StoryEvent.session_id == session.id
            )
        )
        encounter_count = await db.execute(
            select(func.count(Encounter.id)).where(
                Encounter.session_id == session.id
            )
        )

        session_responses.append(
            SessionResponse(
                id=session.id,
                campaign_id=session.campaign_id,
                session_number=session.session_number,
                status=session.status,
                recap=session.recap,
                notes=session.notes,
                started_at=session.started_at,
                ended_at=session.ended_at,
                event_count=event_count.scalar(),
                encounter_count=encounter_count.scalar(),
            )
        )

    return SessionListResponse(sessions=session_responses, total=total)


@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Get a session by ID."""
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get counts
    event_count = await db.execute(
        select(func.count(StoryEvent.id)).where(
            StoryEvent.session_id == session.id
        )
    )
    encounter_count = await db.execute(
        select(func.count(Encounter.id)).where(
            Encounter.session_id == session.id
        )
    )

    return SessionResponse(
        id=session.id,
        campaign_id=session.campaign_id,
        session_number=session.session_number,
        status=session.status,
        recap=session.recap,
        notes=session.notes,
        started_at=session.started_at,
        ended_at=session.ended_at,
        event_count=event_count.scalar(),
        encounter_count=encounter_count.scalar(),
    )


@router.put("/api/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Update a session."""
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields
    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    # Get counts
    event_count = await db.execute(
        select(func.count(StoryEvent.id)).where(
            StoryEvent.session_id == session.id
        )
    )
    encounter_count = await db.execute(
        select(func.count(Encounter.id)).where(
            Encounter.session_id == session.id
        )
    )

    return SessionResponse(
        id=session.id,
        campaign_id=session.campaign_id,
        session_number=session.session_number,
        status=session.status,
        recap=session.recap,
        notes=session.notes,
        started_at=session.started_at,
        ended_at=session.ended_at,
        event_count=event_count.scalar(),
        encounter_count=encounter_count.scalar(),
    )


@router.post("/api/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    end_data: SessionEndRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """End a game session, optionally generating a recap."""
    result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Generate recap if requested
    if end_data.generate_recap:
        narrative_engine = get_narrative_engine()
        recap_data = await narrative_engine.generate_recap(db, session_id)
        session.recap = recap_data.get("recap", "")

    # End session
    session.status = "completed"
    session.ended_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    # Get counts
    event_count = await db.execute(
        select(func.count(StoryEvent.id)).where(
            StoryEvent.session_id == session.id
        )
    )
    encounter_count = await db.execute(
        select(func.count(Encounter.id)).where(
            Encounter.session_id == session.id
        )
    )

    return SessionResponse(
        id=session.id,
        campaign_id=session.campaign_id,
        session_number=session.session_number,
        status=session.status,
        recap=session.recap,
        notes=session.notes,
        started_at=session.started_at,
        ended_at=session.ended_at,
        event_count=event_count.scalar(),
        encounter_count=encounter_count.scalar(),
    )
