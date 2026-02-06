"""Knowledge graph API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign, KnowledgeNode, KnowledgeEdge
from app.schemas.knowledge import (
    KnowledgeNodeCreate,
    KnowledgeNodeResponse,
    KnowledgeEdgeCreate,
    KnowledgeEdgeResponse,
    KnowledgeGraphResponse,
    KnowledgeSearchResult,
    NodeWithConnections,
    TimelineResponse,
    PathResponse,
    ContextRequest,
    ContextResponse,
)
from app.services.knowledge_graph import KnowledgeGraph

router = APIRouter(tags=["knowledge"])


# Knowledge graph instances per campaign
_knowledge_graphs: dict[str, KnowledgeGraph] = {}


async def get_knowledge_graph(campaign_id: str, db: AsyncSession) -> KnowledgeGraph:
    """Get or create knowledge graph for a campaign."""
    if campaign_id not in _knowledge_graphs:
        _knowledge_graphs[campaign_id] = KnowledgeGraph()
        await _knowledge_graphs[campaign_id].load_from_database(db, campaign_id)
    return _knowledge_graphs[campaign_id]


def _node_to_response(node: KnowledgeNode, connection_count: int = 0) -> KnowledgeNodeResponse:
    """Convert KnowledgeNode model to response schema."""
    return KnowledgeNodeResponse(
        id=node.id,
        campaign_id=node.campaign_id,
        node_type=node.node_type,
        name=node.name,
        description=node.description,
        entity_id=node.entity_id,
        entity_type=node.entity_type,
        properties=node.properties,
        importance=node.importance,
        first_mentioned_at=node.first_mentioned_at,
        last_updated_at=node.last_updated_at,
        connection_count=connection_count,
    )


def _edge_to_response(edge: KnowledgeEdge) -> KnowledgeEdgeResponse:
    """Convert KnowledgeEdge model to response schema."""
    return KnowledgeEdgeResponse(
        id=edge.id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        edge_type=edge.edge_type,
        properties=edge.properties,
        is_active=edge.is_active,
        created_at=edge.created_at,
    )


@router.get("/api/campaigns/{campaign_id}/knowledge", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph_data(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphResponse:
    """Get full knowledge graph data for visualization."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get nodes
    nodes_result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.campaign_id == campaign_id)
    )
    nodes = nodes_result.scalars().all()

    # Get edges
    node_ids = [n.id for n in nodes]
    edges_result = await db.execute(
        select(KnowledgeEdge).where(
            KnowledgeEdge.source_id.in_(node_ids),
            KnowledgeEdge.target_id.in_(node_ids),
        )
    )
    edges = edges_result.scalars().all()

    # Count connections for each node
    connection_counts = {}
    for edge in edges:
        connection_counts[edge.source_id] = connection_counts.get(edge.source_id, 0) + 1
        connection_counts[edge.target_id] = connection_counts.get(edge.target_id, 0) + 1

    return KnowledgeGraphResponse(
        campaign_id=campaign_id,
        nodes=[_node_to_response(n, connection_counts.get(n.id, 0)) for n in nodes],
        edges=[_edge_to_response(e) for e in edges],
        node_count=len(nodes),
        edge_count=len(edges),
    )


@router.get("/api/campaigns/{campaign_id}/knowledge/search", response_model=KnowledgeSearchResult)
async def search_knowledge(
    campaign_id: str,
    q: str = Query(..., min_length=1),
    node_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSearchResult:
    """Search the knowledge graph."""
    # Get knowledge graph
    kg = await get_knowledge_graph(campaign_id, db)

    # Search
    results = kg.search(q, node_type=node_type, limit=limit)

    # Convert to response format
    node_responses = []
    for result in results:
        # Get actual node from DB for full data
        node_result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id == result.get("id"))
        )
        node = node_result.scalar_one_or_none()
        if node:
            node_responses.append(_node_to_response(node))

    return KnowledgeSearchResult(
        query=q,
        results=node_responses,
        total=len(node_responses),
    )


@router.get("/api/campaigns/{campaign_id}/knowledge/{node_id}", response_model=NodeWithConnections)
async def get_knowledge_node(
    campaign_id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> NodeWithConnections:
    """Get a knowledge node with its connections."""
    # Get node
    node_result = await db.execute(
        select(KnowledgeNode).where(
            KnowledgeNode.id == node_id,
            KnowledgeNode.campaign_id == campaign_id,
        )
    )
    node = node_result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Get edges
    incoming_result = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.target_id == node_id)
    )
    incoming = incoming_result.scalars().all()

    outgoing_result = await db.execute(
        select(KnowledgeEdge).where(KnowledgeEdge.source_id == node_id)
    )
    outgoing = outgoing_result.scalars().all()

    # Get connected nodes
    connected_ids = set()
    for edge in incoming:
        connected_ids.add(edge.source_id)
    for edge in outgoing:
        connected_ids.add(edge.target_id)

    connected_nodes = []
    if connected_ids:
        connected_result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id.in_(connected_ids))
        )
        connected_nodes = connected_result.scalars().all()

    return NodeWithConnections(
        node=_node_to_response(node, len(incoming) + len(outgoing)),
        incoming_edges=[_edge_to_response(e) for e in incoming],
        outgoing_edges=[_edge_to_response(e) for e in outgoing],
        connected_nodes=[_node_to_response(n) for n in connected_nodes],
    )


@router.post("/api/campaigns/{campaign_id}/knowledge/nodes", response_model=KnowledgeNodeResponse, status_code=201)
async def create_knowledge_node(
    campaign_id: str,
    node_data: KnowledgeNodeCreate,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeNodeResponse:
    """Create a new knowledge node."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get knowledge graph and add node
    kg = await get_knowledge_graph(campaign_id, db)

    import uuid
    node_id = str(uuid.uuid4())

    kg.add_entity(
        node_id=node_id,
        node_type=node_data.node_type,
        name=node_data.name,
        description=node_data.description,
        properties=node_data.properties,
        importance=node_data.importance,
    )

    # Save to database
    await kg.save_to_database(db, campaign_id)

    # Get created node
    node_result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = node_result.scalar_one_or_none()

    return _node_to_response(node)


@router.post("/api/campaigns/{campaign_id}/knowledge/edges", response_model=KnowledgeEdgeResponse, status_code=201)
async def create_knowledge_edge(
    campaign_id: str,
    edge_data: KnowledgeEdgeCreate,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeEdgeResponse:
    """Create a new knowledge edge."""
    # Get knowledge graph
    kg = await get_knowledge_graph(campaign_id, db)

    # Add relationship
    result = kg.add_relationship(
        source_id=edge_data.source_id,
        target_id=edge_data.target_id,
        edge_type=edge_data.edge_type,
        properties=edge_data.properties,
    )

    if not result:
        raise HTTPException(status_code=400, detail="Source or target node not found")

    # Save to database
    await kg.save_to_database(db, campaign_id)

    # Get created edge
    edge_result = await db.execute(
        select(KnowledgeEdge).where(
            KnowledgeEdge.source_id == edge_data.source_id,
            KnowledgeEdge.target_id == edge_data.target_id,
        )
    )
    edge = edge_result.scalar_one_or_none()

    return _edge_to_response(edge)


@router.get("/api/campaigns/{campaign_id}/knowledge/timeline", response_model=TimelineResponse)
async def get_timeline(
    campaign_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> TimelineResponse:
    """Get chronological timeline of events."""
    # Get knowledge graph
    kg = await get_knowledge_graph(campaign_id, db)

    # Get timeline from graph
    events = kg.get_timeline(limit=limit)

    timeline_events = []
    for event in events:
        timeline_events.append({
            "event_id": event.get("id"),
            "name": event.get("name"),
            "description": event.get("description"),
            "timestamp": event.get("created_at"),
            "event_type": "event",
            "related_nodes": [],
        })

    return TimelineResponse(
        campaign_id=campaign_id,
        events=timeline_events,
        total=len(timeline_events),
    )


@router.post("/api/campaigns/{campaign_id}/knowledge/context", response_model=ContextResponse)
async def get_context(
    campaign_id: str,
    context_data: ContextRequest,
    db: AsyncSession = Depends(get_db),
) -> ContextResponse:
    """Get context summary for AI prompts."""
    # Get knowledge graph
    kg = await get_knowledge_graph(campaign_id, db)

    # Generate context
    context_text = kg.get_subgraph_for_prompt(
        entity_ids=context_data.entity_ids,
        max_depth=context_data.depth,
        max_nodes=context_data.max_nodes,
    )

    return ContextResponse(
        context_text=context_text,
        included_nodes=context_data.entity_ids,
        node_count=len(context_data.entity_ids),
    )
