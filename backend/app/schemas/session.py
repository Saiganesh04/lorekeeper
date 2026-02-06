"""Game session Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SessionBase(BaseModel):
    """Base schema for session data."""

    notes: Optional[str] = None


class SessionCreate(SessionBase):
    """Schema for creating a new session."""

    pass


class SessionUpdate(BaseModel):
    """Schema for updating a session."""

    status: Optional[str] = Field(None, pattern="^(active|completed|paused)$")
    notes: Optional[str] = None
    recap: Optional[str] = None


class SessionResponse(SessionBase):
    """Schema for session response."""

    id: str
    campaign_id: str
    session_number: int
    status: str
    recap: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    event_count: int = 0
    encounter_count: int = 0

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""

    sessions: list[SessionResponse]
    total: int


class SessionEndRequest(BaseModel):
    """Schema for ending a session."""

    generate_recap: bool = True
