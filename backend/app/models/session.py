"""Game session database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.event import StoryEvent
    from app.models.encounter import Encounter


class GameSession(Base):
    """Game session model representing a single play session."""

    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    session_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, completed, paused
    recap: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="sessions")
    story_events: Mapped[List["StoryEvent"]] = relationship(
        "StoryEvent", back_populates="session", cascade="all, delete-orphan"
    )
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GameSession(id={self.id}, campaign_id={self.campaign_id}, number={self.session_number})>"
