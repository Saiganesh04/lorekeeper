"""Knowledge graph Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeNodeCreate(BaseModel):
    """Schema for creating a knowledge node."""

    node_type: str = Field(
        ..., pattern="^(character|location|event|item|faction|quest|lore)$"
    )
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    properties: Optional[dict] = None
    importance: int = Field(default=5, ge=1, le=10)


class KnowledgeNodeResponse(BaseModel):
    """Schema for knowledge node response."""

    id: str
    campaign_id: str
    node_type: str
    name: str
    description: Optional[str]
    entity_id: Optional[str]
    entity_type: Optional[str]
    properties: Optional[dict]
    importance: int
    first_mentioned_at: datetime
    last_updated_at: datetime
    connection_count: int = 0

    class Config:
        from_attributes = True


class KnowledgeEdgeCreate(BaseModel):
    """Schema for creating a knowledge edge."""

    source_id: str
    target_id: str
    edge_type: str = Field(..., min_length=1, max_length=100)
    properties: Optional[dict] = None
    is_active: bool = True


class KnowledgeEdgeResponse(BaseModel):
    """Schema for knowledge edge response."""

    id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: Optional[dict]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NodeWithConnections(BaseModel):
    """Schema for a node with its connections."""

    node: KnowledgeNodeResponse
    incoming_edges: list[KnowledgeEdgeResponse]
    outgoing_edges: list[KnowledgeEdgeResponse]
    connected_nodes: list[KnowledgeNodeResponse]


class KnowledgeGraphResponse(BaseModel):
    """Schema for full knowledge graph data (for visualization)."""

    campaign_id: str
    nodes: list[KnowledgeNodeResponse]
    edges: list[KnowledgeEdgeResponse]
    node_count: int
    edge_count: int


class KnowledgeSearchResult(BaseModel):
    """Schema for knowledge search results."""

    query: str
    results: list[KnowledgeNodeResponse]
    total: int


class TimelineEvent(BaseModel):
    """Schema for timeline entry."""

    event_id: str
    name: str
    description: str
    timestamp: datetime
    event_type: str
    related_nodes: list[str]


class TimelineResponse(BaseModel):
    """Schema for campaign timeline."""

    campaign_id: str
    events: list[TimelineEvent]
    total: int


class PathResponse(BaseModel):
    """Schema for path between entities."""

    source_id: str
    target_id: str
    path: list[KnowledgeNodeResponse]
    edges: list[KnowledgeEdgeResponse]
    path_length: int


class ContextRequest(BaseModel):
    """Schema for requesting knowledge context."""

    entity_ids: list[str]
    depth: int = Field(default=2, ge=1, le=5)
    include_events: bool = True
    max_nodes: int = Field(default=50, ge=1, le=200)


class ContextResponse(BaseModel):
    """Schema for knowledge context (for AI prompts)."""

    context_text: str
    included_nodes: list[str]
    node_count: int
