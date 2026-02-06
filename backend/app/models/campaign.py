"""Campaign database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.session import GameSession
    from app.models.character import Character
    from app.models.location import Location
    from app.models.knowledge import KnowledgeNode


class Campaign(Base):
    """Campaign model representing a complete game campaign."""

    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[str] = mapped_column(
        String(50), nullable=False, default="fantasy"
    )  # fantasy, sci-fi, horror, steampunk
    tone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="serious"
    )  # serious, lighthearted, dark, epic
    setting_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    world_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    sessions: Mapped[List["GameSession"]] = relationship(
        "GameSession", back_populates="campaign", cascade="all, delete-orphan"
    )
    characters: Mapped[List["Character"]] = relationship(
        "Character", back_populates="campaign", cascade="all, delete-orphan"
    )
    locations: Mapped[List["Location"]] = relationship(
        "Location", back_populates="campaign", cascade="all, delete-orphan"
    )
    knowledge_nodes: Mapped[List["KnowledgeNode"]] = relationship(
        "KnowledgeNode", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name})>"
