"""Character database model for PCs and NPCs."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.location import Location


class Character(Base):
    """Character model for player characters and NPCs."""

    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    character_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="npc"
    )  # pc, npc, monster
    race: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    char_class: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Combat stats
    hp_current: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    hp_max: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    armor_class: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Ability scores
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    constitution: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    wisdom: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Personality and background
    personality_traits: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    backstory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    appearance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # NPC-specific fields
    motivation: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disposition: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )  # -100 to 100
    speech_pattern: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # formal, casual, archaic, broken, eloquent
    npc_memory: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # Interactions with party

    # Inventory and equipment
    inventory: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    equipment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Skills and proficiencies
    skills: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    proficiencies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    languages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Status
    is_alive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    conditions: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # poisoned, stunned, etc.

    # Location
    current_location_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # Experience
    experience_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="characters")
    current_location: Mapped[Optional["Location"]] = relationship(
        "Location", back_populates="characters"
    )

    @property
    def strength_modifier(self) -> int:
        return (self.strength - 10) // 2

    @property
    def dexterity_modifier(self) -> int:
        return (self.dexterity - 10) // 2

    @property
    def constitution_modifier(self) -> int:
        return (self.constitution - 10) // 2

    @property
    def intelligence_modifier(self) -> int:
        return (self.intelligence - 10) // 2

    @property
    def wisdom_modifier(self) -> int:
        return (self.wisdom - 10) // 2

    @property
    def charisma_modifier(self) -> int:
        return (self.charisma - 10) // 2

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name={self.name}, type={self.character_type})>"
