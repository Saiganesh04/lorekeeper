"""Knowledge graph database models for persistent storage."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign


class KnowledgeNode(Base):
    """Knowledge node model representing entities in the knowledge graph."""

    __tablename__ = "knowledge_nodes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )

    # Node identification
    node_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # character, location, event, item, faction, quest, lore
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Reference to actual entity (if applicable)
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )  # ID from characters, locations, items tables
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Table name

    # Additional properties (flexible JSON for type-specific data)
    properties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Importance score for context selection
    importance: Mapped[int] = mapped_column(default=5)  # 1-10

    # Timestamps
    first_mentioned_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="knowledge_nodes"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeNode(id={self.id}, type={self.node_type}, name={self.name})>"


class KnowledgeEdge(Base):
    """Knowledge edge model representing relationships between entities."""

    __tablename__ = "knowledge_edges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Source and target nodes
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_nodes.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship type
    edge_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # located_in, owns, knows, member_of, participated_in, etc.

    # Relationship properties
    properties: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # sentiment, weight, distance, etc.

    # For temporal relationships
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEdge(source={self.source_id}, target={self.target_id}, type={self.edge_type})>"
