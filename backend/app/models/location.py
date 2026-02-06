"""Location database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.character import Character
    from app.models.encounter import Encounter


class Location(Base):
    """Location model for places in the game world."""

    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="wilderness"
    )  # city, dungeon, wilderness, building, room, tavern, temple, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Map position
    x_coord: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y_coord: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Attributes
    danger_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # 1-10
    is_discovered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_accessible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Environment
    terrain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    climate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    atmosphere: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Mood description

    # Contents
    points_of_interest: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    resources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    environmental_effects: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Connections
    connected_locations: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # [{location_id, path_type, travel_time}]

    # Hierarchy (room in dungeon, shop in city, etc.)
    parent_location_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # Additional properties
    properties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="locations")
    characters: Mapped[List["Character"]] = relationship(
        "Character", back_populates="current_location"
    )
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter", back_populates="location"
    )
    children: Mapped[List["Location"]] = relationship(
        "Location",
        back_populates="parent",
        remote_side=[id],
        foreign_keys=[parent_location_id],
    )
    parent: Mapped[Optional["Location"]] = relationship(
        "Location",
        back_populates="children",
        remote_side=[parent_location_id],
        foreign_keys=[parent_location_id],
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name={self.name}, type={self.location_type})>"
