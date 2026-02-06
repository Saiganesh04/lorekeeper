"""Encounter database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import GameSession
    from app.models.location import Location


class Encounter(Base):
    """Encounter model for combat, social, puzzle, and exploration encounters."""

    __tablename__ = "encounters"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    encounter_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="combat"
    )  # combat, social, puzzle, exploration, boss
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Difficulty and status
    difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # easy, medium, hard, deadly
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, resolved, fled, failed

    # Current round/phase tracking
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_phase: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # For boss fights with phases

    # Combat-specific
    enemies: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{id, name, hp_current, hp_max, ac, stats, abilities}]
    initiative_order: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{character_id, initiative_roll, is_enemy}]
    current_turn_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Combat log
    combat_log: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{round, actor, action, target, result, damage}]

    # Social-specific
    participants: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # NPC IDs involved
    social_stakes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # What's at stake
    disposition_changes: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {npc_id: change}

    # Puzzle-specific
    puzzle_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    puzzle_solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    puzzle_hints: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    hints_revealed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Environmental effects
    environmental_effects: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    terrain_features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Rewards
    rewards: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {xp, gold, items}
    rewards_distributed: Mapped[bool] = mapped_column(default=False)

    # Metadata
    party_level_at_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    party_size_at_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    session: Mapped["GameSession"] = relationship(
        "GameSession", back_populates="encounters"
    )
    location: Mapped[Optional["Location"]] = relationship(
        "Location", back_populates="encounters"
    )

    def __repr__(self) -> str:
        return f"<Encounter(id={self.id}, name={self.name}, type={self.encounter_type})>"
