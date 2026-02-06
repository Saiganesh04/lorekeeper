"""Item database model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    """Item model for weapons, armor, artifacts, and consumables."""

    __tablename__ = "items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="misc"
    )  # weapon, armor, potion, scroll, artifact, quest_item, misc
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rarity and value
    rarity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="common"
    )  # common, uncommon, rare, very_rare, legendary, artifact
    value_gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weight: Mapped[float] = mapped_column(default=0.0)

    # Equipment stats
    damage_dice: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # "1d8+2"
    damage_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # slashing, piercing, fire, etc.
    armor_bonus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    properties: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # finesse, versatile, etc.

    # Magic properties
    is_magical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    magic_bonus: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # +1, +2, +3
    enchantments: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{name, effect}]
    attunement_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    attuned_to_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # Character ID

    # Consumable properties
    is_consumable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    charges: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_charges: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    consumable_effect: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quest item properties
    is_quest_item: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    quest_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Ownership
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # Character ID
    location_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # If not owned, where is it?

    # Lore
    history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_history: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # What players know

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, name={self.name}, type={self.item_type})>"
