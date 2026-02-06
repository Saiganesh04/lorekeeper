"""Story event database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import GameSession


class StoryEvent(Base):
    """Story event model for tracking narrative beats."""

    __tablename__ = "story_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )

    # Event type and content
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="narrative"
    )  # narrative, dialogue, combat, roll, system, choice
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Player interaction
    player_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    choices: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Available choices
    chosen_index: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Which choice was picked

    # Narrative metadata
    mood: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # tense, calm, mysterious, triumphant, somber, humorous
    speaker: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # For dialogue events

    # Dice rolls
    dice_rolls: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{notation, result, success}]

    # Knowledge graph updates triggered by this event
    knowledge_updates: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{action, entity, relationship, target}]
    new_entities: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{name, type, description}]

    # Rewards
    xp_awarded: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    items_awarded: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Ordering
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Associated entities
    location_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    encounter_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    character_ids: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Characters involved

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    session: Mapped["GameSession"] = relationship(
        "GameSession", back_populates="story_events"
    )

    def __repr__(self) -> str:
        return f"<StoryEvent(id={self.id}, type={self.event_type}, order={self.sequence_order})>"
