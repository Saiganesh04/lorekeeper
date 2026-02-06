"""Knowledge graph service using NetworkX for in-memory graph operations."""

from datetime import datetime
from typing import Any, Optional

import networkx as nx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import KnowledgeNode, KnowledgeEdge


class KnowledgeGraph:
    """In-memory knowledge graph manager using NetworkX.

    This service maintains a directed graph of entities and their relationships,
    providing fast querying for AI context generation.
    """

    # Valid node types
    NODE_TYPES = {"character", "location", "event", "item", "faction", "quest", "lore"}

    # Valid edge types
    EDGE_TYPES = {
        "located_in",
        "owns",
        "knows",
        "member_of",
        "participated_in",
        "occurred_at",
        "leads_to",
        "requires",
        "connected_to",
        "contains",
        "created_by",
        "destroyed_by",
        "allied_with",
        "enemy_of",
        "related_to",
        "part_of",
        "gave_to",
        "received_from",
    }

    def __init__(self):
        """Initialize empty knowledge graph."""
        self.graph = nx.DiGraph()
        self._campaign_id: Optional[str] = None

    @property
    def campaign_id(self) -> Optional[str]:
        """Get the current campaign ID."""
        return self._campaign_id

    def clear(self) -> None:
        """Clear the graph."""
        self.graph.clear()
        self._campaign_id = None

    def add_entity(
        self,
        node_id: str,
        node_type: str,
        name: str,
        description: Optional[str] = None,
        properties: Optional[dict] = None,
        importance: int = 5,
    ) -> dict:
        """Add an entity node to the graph.

        Args:
            node_id: Unique identifier for the node
            node_type: Type of entity (character, location, etc.)
            name: Display name
            description: Optional description
            properties: Additional type-specific properties
            importance: Importance score 1-10 for context selection

        Returns:
            The node data dictionary
        """
        if node_type not in self.NODE_TYPES:
            raise ValueError(f"Invalid node type: {node_type}. Must be one of {self.NODE_TYPES}")

        node_data = {
            "id": node_id,
            "type": node_type,
            "name": name,
            "description": description or "",
            "properties": properties or {},
            "importance": max(1, min(10, importance)),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        self.graph.add_node(node_id, **node_data)
        return node_data

    def update_entity(
        self,
        node_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[dict] = None,
        importance: Optional[int] = None,
    ) -> Optional[dict]:
        """Update an existing entity.

        Args:
            node_id: ID of the node to update
            name: New name (optional)
            description: New description (optional)
            properties: Properties to merge (optional)
            importance: New importance score (optional)

        Returns:
            Updated node data or None if not found
        """
        if node_id not in self.graph:
            return None

        node = self.graph.nodes[node_id]

        if name is not None:
            node["name"] = name
        if description is not None:
            node["description"] = description
        if properties is not None:
            node["properties"] = {**node.get("properties", {}), **properties}
        if importance is not None:
            node["importance"] = max(1, min(10, importance))

        node["updated_at"] = datetime.utcnow().isoformat()
        return dict(node)

    def remove_entity(self, node_id: str) -> bool:
        """Remove an entity and all its edges.

        Args:
            node_id: ID of the node to remove

        Returns:
            True if removed, False if not found
        """
        if node_id not in self.graph:
            return False

        self.graph.remove_node(node_id)
        return True

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        properties: Optional[dict] = None,
    ) -> Optional[dict]:
        """Add a relationship edge between two entities.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship
            properties: Additional edge properties (sentiment, weight, etc.)

        Returns:
            Edge data dictionary or None if nodes don't exist
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None

        edge_data = {
            "type": edge_type,
            "properties": properties or {},
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        self.graph.add_edge(source_id, target_id, **edge_data)
        return edge_data

    def remove_relationship(self, source_id: str, target_id: str) -> bool:
        """Remove a relationship between entities.

        Args:
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            True if removed, False if not found
        """
        if not self.graph.has_edge(source_id, target_id):
            return False

        self.graph.remove_edge(source_id, target_id)
        return True

    def get_entity(self, node_id: str) -> Optional[dict]:
        """Get an entity by ID.

        Args:
            node_id: Node ID to retrieve

        Returns:
            Node data dictionary or None if not found
        """
        if node_id not in self.graph:
            return None
        return dict(self.graph.nodes[node_id])

    def get_neighbors(
        self,
        node_id: str,
        edge_type: Optional[str] = None,
        direction: str = "both",
        depth: int = 1,
    ) -> list[dict]:
        """Get neighboring entities.

        Args:
            node_id: Starting node ID
            edge_type: Filter by relationship type (optional)
            direction: 'incoming', 'outgoing', or 'both'
            depth: How many hops to traverse (1 = direct neighbors)

        Returns:
            List of neighbor node data dictionaries with their edge info
        """
        if node_id not in self.graph:
            return []

        neighbors = []
        visited = {node_id}

        def collect_neighbors(current_id: str, current_depth: int):
            if current_depth > depth:
                return

            # Get outgoing edges
            if direction in ("outgoing", "both"):
                for _, target in self.graph.out_edges(current_id):
                    if target not in visited:
                        edge_data = self.graph.edges[current_id, target]
                        if edge_type is None or edge_data.get("type") == edge_type:
                            visited.add(target)
                            node_data = dict(self.graph.nodes[target])
                            node_data["_edge"] = {
                                "source": current_id,
                                "target": target,
                                "direction": "outgoing",
                                **edge_data,
                            }
                            neighbors.append(node_data)
                            collect_neighbors(target, current_depth + 1)

            # Get incoming edges
            if direction in ("incoming", "both"):
                for source, _ in self.graph.in_edges(current_id):
                    if source not in visited:
                        edge_data = self.graph.edges[source, current_id]
                        if edge_type is None or edge_data.get("type") == edge_type:
                            visited.add(source)
                            node_data = dict(self.graph.nodes[source])
                            node_data["_edge"] = {
                                "source": source,
                                "target": current_id,
                                "direction": "incoming",
                                **edge_data,
                            }
                            neighbors.append(node_data)
                            collect_neighbors(source, current_depth + 1)

        collect_neighbors(node_id, 1)
        return neighbors

    def get_context_for_location(self, location_id: str) -> dict:
        """Get all relevant context for a location.

        Args:
            location_id: Location node ID

        Returns:
            Dictionary with characters, items, events, and connected locations
        """
        context = {
            "location": self.get_entity(location_id),
            "characters": [],
            "items": [],
            "recent_events": [],
            "connected_locations": [],
            "factions": [],
        }

        if not context["location"]:
            return context

        neighbors = self.get_neighbors(location_id, depth=2)

        for neighbor in neighbors:
            node_type = neighbor.get("type")
            edge_type = neighbor.get("_edge", {}).get("type")

            if node_type == "character" and edge_type == "located_in":
                context["characters"].append(neighbor)
            elif node_type == "item" and edge_type == "located_in":
                context["items"].append(neighbor)
            elif node_type == "event" and edge_type == "occurred_at":
                context["recent_events"].append(neighbor)
            elif node_type == "location" and edge_type == "connected_to":
                context["connected_locations"].append(neighbor)
            elif node_type == "faction":
                context["factions"].append(neighbor)

        return context

    def get_character_knowledge(self, character_id: str) -> dict:
        """Get what a character knows and remembers.

        Args:
            character_id: Character node ID

        Returns:
            Dictionary with known entities, relationships, and events
        """
        knowledge = {
            "character": self.get_entity(character_id),
            "known_characters": [],
            "known_locations": [],
            "known_items": [],
            "participated_events": [],
            "faction_memberships": [],
        }

        if not knowledge["character"]:
            return knowledge

        neighbors = self.get_neighbors(character_id, depth=2)

        for neighbor in neighbors:
            node_type = neighbor.get("type")
            edge_type = neighbor.get("_edge", {}).get("type")

            if node_type == "character" and edge_type == "knows":
                neighbor["_relationship"] = neighbor.get("_edge", {}).get("properties", {})
                knowledge["known_characters"].append(neighbor)
            elif node_type == "location" and edge_type in ("located_in", "visited"):
                knowledge["known_locations"].append(neighbor)
            elif node_type == "item" and edge_type == "owns":
                knowledge["known_items"].append(neighbor)
            elif node_type == "event" and edge_type == "participated_in":
                knowledge["participated_events"].append(neighbor)
            elif node_type == "faction" and edge_type == "member_of":
                knowledge["faction_memberships"].append(neighbor)

        return knowledge

    def get_faction_status(self) -> dict:
        """Get the current political/faction landscape.

        Returns:
            Dictionary with all factions and their relationships
        """
        factions = []
        faction_relationships = []

        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("type") == "faction":
                faction_data = dict(node)
                faction_data["members"] = []

                # Get faction members
                for source, _ in self.graph.in_edges(node_id):
                    edge = self.graph.edges[source, node_id]
                    if edge.get("type") == "member_of":
                        member = self.graph.nodes[source]
                        faction_data["members"].append({"id": source, "name": member.get("name")})

                factions.append(faction_data)

        # Get inter-faction relationships
        for faction in factions:
            for other_faction in factions:
                if faction["id"] != other_faction["id"]:
                    if self.graph.has_edge(faction["id"], other_faction["id"]):
                        edge = self.graph.edges[faction["id"], other_faction["id"]]
                        faction_relationships.append({
                            "source": faction["id"],
                            "source_name": faction["name"],
                            "target": other_faction["id"],
                            "target_name": other_faction["name"],
                            "relationship": edge.get("type"),
                            "properties": edge.get("properties", {}),
                        })

        return {"factions": factions, "relationships": faction_relationships}

    def query_path(self, source_id: str, target_id: str) -> Optional[list[dict]]:
        """Find the shortest path between two entities.

        Args:
            source_id: Starting node ID
            target_id: Ending node ID

        Returns:
            List of nodes in the path, or None if no path exists
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph.to_undirected(), source_id, target_id)
            return [dict(self.graph.nodes[node_id]) for node_id in path]
        except nx.NetworkXNoPath:
            return None

    def get_timeline(self, limit: int = 50) -> list[dict]:
        """Get chronological list of events.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event nodes sorted by creation time
        """
        events = []
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            if node.get("type") == "event":
                events.append(dict(node))

        # Sort by created_at
        events.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return events[:limit]

    def search(
        self,
        query: str,
        node_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search for entities by name or description.

        Args:
            query: Search string
            node_type: Filter by type (optional)
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        query_lower = query.lower()
        results = []

        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]

            if node_type and node.get("type") != node_type:
                continue

            name = node.get("name", "").lower()
            description = node.get("description", "").lower()

            if query_lower in name or query_lower in description:
                results.append(dict(node))

        # Sort by importance and name match quality
        def score(node):
            name = node.get("name", "").lower()
            importance = node.get("importance", 5)
            name_match = 10 if query_lower == name else (5 if query_lower in name else 0)
            return -(importance + name_match)

        results.sort(key=score)
        return results[:limit]

    def get_nodes_by_type(self, node_type: str) -> list[dict]:
        """Get all nodes of a specific type.

        Args:
            node_type: Type to filter by

        Returns:
            List of matching nodes
        """
        return [
            dict(self.graph.nodes[node_id])
            for node_id in self.graph.nodes
            if self.graph.nodes[node_id].get("type") == node_type
        ]

    def serialize(self) -> dict:
        """Export the graph to a dictionary for persistence.

        Returns:
            Dictionary with nodes and edges
        """
        nodes = [dict(self.graph.nodes[node_id]) for node_id in self.graph.nodes]
        edges = [
            {
                "source": source,
                "target": target,
                **self.graph.edges[source, target],
            }
            for source, target in self.graph.edges
        ]

        return {
            "campaign_id": self._campaign_id,
            "nodes": nodes,
            "edges": edges,
            "exported_at": datetime.utcnow().isoformat(),
        }

    def deserialize(self, data: dict) -> None:
        """Import graph from a dictionary.

        Args:
            data: Dictionary with nodes and edges
        """
        self.clear()
        self._campaign_id = data.get("campaign_id")

        for node in data.get("nodes", []):
            node_id = node.pop("id")
            self.graph.add_node(node_id, id=node_id, **node)

        for edge in data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            self.graph.add_edge(source, target, **edge)

    def get_subgraph_for_prompt(
        self,
        entity_ids: list[str],
        max_depth: int = 2,
        max_nodes: int = 50,
    ) -> str:
        """Generate a natural language summary of relevant graph context.

        This is the critical method that creates context for AI prompts.

        Args:
            entity_ids: Starting entity IDs to build context around
            max_depth: Maximum relationship depth to traverse
            max_nodes: Maximum nodes to include in context

        Returns:
            Natural language summary string for AI context
        """
        if not entity_ids:
            return "No specific context available."

        # Collect relevant nodes
        relevant_nodes = set()
        for entity_id in entity_ids:
            if entity_id in self.graph:
                relevant_nodes.add(entity_id)
                neighbors = self.get_neighbors(entity_id, depth=max_depth)
                for neighbor in neighbors:
                    if len(relevant_nodes) < max_nodes:
                        relevant_nodes.add(neighbor.get("id"))

        if not relevant_nodes:
            return "No relevant entities found in the knowledge graph."

        # Build context sections
        sections = {
            "character": [],
            "location": [],
            "faction": [],
            "item": [],
            "event": [],
            "quest": [],
            "lore": [],
        }

        relationships = []

        for node_id in relevant_nodes:
            node = self.graph.nodes.get(node_id, {})
            node_type = node.get("type", "unknown")
            name = node.get("name", "Unknown")
            description = node.get("description", "")

            if node_type in sections:
                entry = f"- {name}"
                if description:
                    entry += f": {description}"
                sections[node_type].append(entry)

            # Collect relationships
            for _, target in self.graph.out_edges(node_id):
                if target in relevant_nodes:
                    edge = self.graph.edges[node_id, target]
                    target_node = self.graph.nodes.get(target, {})
                    rel = f"- {name} {edge.get('type', 'relates to').replace('_', ' ')} {target_node.get('name', 'Unknown')}"
                    props = edge.get("properties", {})
                    if props.get("sentiment"):
                        rel += f" ({props['sentiment']})"
                    relationships.append(rel)

        # Build output
        output_parts = []

        if sections["character"]:
            output_parts.append("CHARACTERS:\n" + "\n".join(sections["character"]))

        if sections["location"]:
            output_parts.append("LOCATIONS:\n" + "\n".join(sections["location"]))

        if sections["faction"]:
            output_parts.append("FACTIONS:\n" + "\n".join(sections["faction"]))

        if sections["item"]:
            output_parts.append("NOTABLE ITEMS:\n" + "\n".join(sections["item"]))

        if sections["event"]:
            output_parts.append("RECENT EVENTS:\n" + "\n".join(sections["event"][:10]))

        if sections["quest"]:
            output_parts.append("ACTIVE QUESTS:\n" + "\n".join(sections["quest"]))

        if sections["lore"]:
            output_parts.append("WORLD LORE:\n" + "\n".join(sections["lore"]))

        if relationships:
            output_parts.append("KEY RELATIONSHIPS:\n" + "\n".join(relationships[:20]))

        return "\n\n".join(output_parts) if output_parts else "No context available."

    async def load_from_database(self, db: AsyncSession, campaign_id: str) -> None:
        """Load graph from database for a campaign.

        Args:
            db: Database session
            campaign_id: Campaign to load
        """
        self.clear()
        self._campaign_id = campaign_id

        # Load nodes
        nodes_result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.campaign_id == campaign_id)
        )
        nodes = nodes_result.scalars().all()

        for node in nodes:
            self.add_entity(
                node_id=node.id,
                node_type=node.node_type,
                name=node.name,
                description=node.description,
                properties=node.properties,
                importance=node.importance,
            )

        # Load edges
        node_ids = {node.id for node in nodes}
        edges_result = await db.execute(
            select(KnowledgeEdge).where(
                KnowledgeEdge.source_id.in_(node_ids),
                KnowledgeEdge.target_id.in_(node_ids),
            )
        )
        edges = edges_result.scalars().all()

        for edge in edges:
            self.add_relationship(
                source_id=edge.source_id,
                target_id=edge.target_id,
                edge_type=edge.edge_type,
                properties=edge.properties,
            )

    async def save_to_database(self, db: AsyncSession, campaign_id: str) -> None:
        """Save graph to database.

        Args:
            db: Database session
            campaign_id: Campaign to save to
        """
        # This is a simplified version - in production you'd want upsert logic
        for node_id in self.graph.nodes:
            node = self.graph.nodes[node_id]
            db_node = KnowledgeNode(
                id=node_id,
                campaign_id=campaign_id,
                node_type=node.get("type"),
                name=node.get("name"),
                description=node.get("description"),
                properties=node.get("properties"),
                importance=node.get("importance", 5),
            )
            await db.merge(db_node)

        for source, target in self.graph.edges:
            edge = self.graph.edges[source, target]
            db_edge = KnowledgeEdge(
                source_id=source,
                target_id=target,
                edge_type=edge.get("type"),
                properties=edge.get("properties"),
                is_active=edge.get("is_active", True),
            )
            await db.merge(db_edge)

        await db.commit()

    def get_stats(self) -> dict:
        """Get graph statistics.

        Returns:
            Dictionary with node and edge counts by type
        """
        node_counts = {}
        for node_id in self.graph.nodes:
            node_type = self.graph.nodes[node_id].get("type", "unknown")
            node_counts[node_type] = node_counts.get(node_type, 0) + 1

        edge_counts = {}
        for source, target in self.graph.edges:
            edge_type = self.graph.edges[source, target].get("type", "unknown")
            edge_counts[edge_type] = edge_counts.get(edge_type, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes_by_type": node_counts,
            "edges_by_type": edge_counts,
        }
