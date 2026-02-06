"""Map generator service for locations and world building."""

import random
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, Location
from app.services.ai_engine import AIEngine, get_ai_engine
from app.services.knowledge_graph import KnowledgeGraph
from app.utils.prompts import PromptTemplates


class MapGenerator:
    """Service for generating locations and maps."""

    # Location type hierarchies
    LOCATION_HIERARCHY = {
        "world": ["region", "continent"],
        "region": ["city", "town", "village", "wilderness", "dungeon"],
        "city": ["district", "building", "landmark"],
        "town": ["building", "landmark"],
        "village": ["building"],
        "dungeon": ["level", "room"],
        "building": ["room", "floor"],
        "wilderness": ["clearing", "cave", "ruin"],
    }

    # Default terrain types
    TERRAIN_TYPES = [
        "plains", "forest", "mountains", "desert", "swamp",
        "tundra", "jungle", "coastal", "underground", "urban",
    ]

    def __init__(
        self,
        ai_engine: Optional[AIEngine] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ):
        """Initialize map generator.

        Args:
            ai_engine: AI engine instance
            knowledge_graph: Knowledge graph instance
        """
        self.ai_engine = ai_engine or get_ai_engine()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()

    async def _get_campaign_context(
        self, db: AsyncSession, campaign_id: str
    ) -> dict[str, Any]:
        """Get campaign information for prompts."""
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return {"genre": "fantasy", "tone": "serious"}

        return {
            "campaign_name": campaign.name,
            "genre": campaign.genre,
            "tone": campaign.tone,
            "setting_description": campaign.setting_description or "",
        }

    def _generate_coordinates(
        self,
        parent_location: Optional[Location] = None,
        existing_locations: list[Location] = None,
    ) -> tuple[float, float]:
        """Generate coordinates for a new location.

        Args:
            parent_location: Parent location for relative positioning
            existing_locations: Existing locations to avoid overlap

        Returns:
            (x, y) coordinates
        """
        if parent_location:
            # Position relative to parent
            base_x = parent_location.x_coord
            base_y = parent_location.y_coord
            # Random offset within parent area
            x = base_x + random.uniform(-50, 50)
            y = base_y + random.uniform(-50, 50)
        else:
            # Random position in world space
            x = random.uniform(-500, 500)
            y = random.uniform(-500, 500)

        # Avoid overlap with existing locations
        if existing_locations:
            for _ in range(10):  # Max attempts
                overlap = False
                for loc in existing_locations:
                    dist = ((x - loc.x_coord) ** 2 + (y - loc.y_coord) ** 2) ** 0.5
                    if dist < 20:  # Minimum distance
                        overlap = True
                        break
                if not overlap:
                    break
                x += random.uniform(-30, 30)
                y += random.uniform(-30, 30)

        return round(x, 2), round(y, 2)

    async def generate_location(
        self,
        db: AsyncSession,
        campaign_id: str,
        location_type: str,
        theme: Optional[str] = None,
        danger_level: int = 3,
        parent_location_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Location:
        """Generate a new location with AI.

        Args:
            db: Database session
            campaign_id: Campaign ID
            location_type: Type of location
            theme: Thematic element
            danger_level: Danger level 1-10
            parent_location_id: Parent location ID
            name: Optional pre-set name

        Returns:
            Created Location
        """
        campaign_context = await self._get_campaign_context(db, campaign_id)

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != campaign_id:
            await self.knowledge_graph.load_from_database(db, campaign_id)

        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt([])

        # Get connected locations
        connected_locations = []
        if parent_location_id:
            parent_result = await db.execute(
                select(Location).where(Location.id == parent_location_id)
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                connected_locations.append(parent.name)

        # Format prompts
        system_prompt = PromptTemplates.LOCATION_GENERATION_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
            tone=campaign_context.get("tone", "serious"),
            knowledge_graph_context=knowledge_context,
        )

        user_prompt = PromptTemplates.LOCATION_GENERATION_USER.format(
            location_type=location_type,
            theme=theme or "appropriate to the world",
            danger_level=danger_level,
            connected_locations=", ".join(connected_locations) if connected_locations else "None specified",
        )

        # Generate location
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Get existing locations for coordinate generation
        existing_result = await db.execute(
            select(Location).where(Location.campaign_id == campaign_id)
        )
        existing_locations = existing_result.scalars().all()

        # Generate coordinates
        parent_loc = None
        if parent_location_id:
            for loc in existing_locations:
                if loc.id == parent_location_id:
                    parent_loc = loc
                    break

        x, y = self._generate_coordinates(parent_loc, list(existing_locations))

        # Create location
        location = Location(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            name=name or response.get("name", "Unknown Location"),
            location_type=response.get("location_type", location_type),
            description=response.get("description", ""),
            detailed_description=response.get("detailed_description"),
            x_coord=x,
            y_coord=y,
            danger_level=response.get("danger_level", danger_level),
            is_discovered=False,
            terrain=response.get("terrain"),
            climate=response.get("climate"),
            atmosphere=response.get("atmosphere"),
            points_of_interest=response.get("points_of_interest"),
            resources=response.get("resources"),
            environmental_effects=response.get("environmental_effects"),
            connected_locations=response.get("connected_locations"),
            parent_location_id=parent_location_id,
            properties={
                "lore": response.get("lore"),
                "potential_encounters": response.get("potential_encounters"),
                "npcs": response.get("npcs"),
            },
        )

        db.add(location)
        await db.commit()
        await db.refresh(location)

        # Add to knowledge graph
        self.knowledge_graph.add_entity(
            node_id=location.id,
            node_type="location",
            name=location.name,
            description=location.description,
            properties={
                "location_type": location.location_type,
                "danger_level": location.danger_level,
                "terrain": location.terrain,
            },
        )

        # Add connection to parent
        if parent_location_id:
            self.knowledge_graph.add_relationship(
                source_id=location.id,
                target_id=parent_location_id,
                edge_type="part_of",
            )
            self.knowledge_graph.add_relationship(
                source_id=location.id,
                target_id=parent_location_id,
                edge_type="connected_to",
                properties={"path_type": "contained"},
            )

        await self.knowledge_graph.save_to_database(db, campaign_id)

        return location

    async def generate_dungeon(
        self,
        db: AsyncSession,
        campaign_id: str,
        name: str,
        theme: str,
        num_rooms: int = 10,
        danger_level: int = 5,
        parent_location_id: Optional[str] = None,
    ) -> list[Location]:
        """Generate a complete dungeon with multiple rooms.

        Args:
            db: Database session
            campaign_id: Campaign ID
            name: Dungeon name
            theme: Dungeon theme
            num_rooms: Number of rooms to generate
            danger_level: Base danger level
            parent_location_id: Parent location

        Returns:
            List of created Location objects
        """
        locations = []

        # Create main dungeon entrance
        entrance = await self.generate_location(
            db=db,
            campaign_id=campaign_id,
            location_type="dungeon",
            theme=theme,
            danger_level=danger_level,
            parent_location_id=parent_location_id,
            name=name,
        )
        locations.append(entrance)

        # Generate rooms
        room_types = ["chamber", "corridor", "hall", "vault", "trap room", "puzzle room", "boss chamber"]
        previous_room_id = entrance.id

        for i in range(num_rooms):
            room_type = random.choice(room_types)
            room_danger = danger_level + random.randint(-1, 2)
            room_danger = max(1, min(10, room_danger))

            # Last room is boss chamber
            if i == num_rooms - 1:
                room_type = "boss chamber"
                room_danger = min(10, danger_level + 2)

            room = await self.generate_location(
                db=db,
                campaign_id=campaign_id,
                location_type="room",
                theme=f"{theme} {room_type}",
                danger_level=room_danger,
                parent_location_id=entrance.id,
                name=f"{name} - {room_type.title()} {i + 1}",
            )
            locations.append(room)

            # Connect to previous room
            self.knowledge_graph.add_relationship(
                source_id=previous_room_id,
                target_id=room.id,
                edge_type="connected_to",
                properties={"path_type": "passage"},
            )

            # Some rooms connect to multiple previous rooms
            if i > 2 and random.random() < 0.3:
                random_earlier_room = random.choice(locations[1:-1])
                self.knowledge_graph.add_relationship(
                    source_id=random_earlier_room.id,
                    target_id=room.id,
                    edge_type="connected_to",
                    properties={"path_type": "secret passage"},
                )

            previous_room_id = room.id

        await self.knowledge_graph.save_to_database(db, campaign_id)

        return locations

    async def generate_world_region(
        self,
        db: AsyncSession,
        campaign_id: str,
        theme: str,
        num_locations: int = 5,
    ) -> list[Location]:
        """Generate a world region with multiple locations.

        Args:
            db: Database session
            campaign_id: Campaign ID
            theme: Regional theme
            num_locations: Number of locations to generate

        Returns:
            List of created locations
        """
        locations = []

        # Create region
        region = await self.generate_location(
            db=db,
            campaign_id=campaign_id,
            location_type="region",
            theme=theme,
            danger_level=3,
        )
        locations.append(region)

        # Generate various location types
        location_types = ["city", "town", "village", "wilderness", "dungeon", "landmark"]

        for i in range(num_locations):
            loc_type = random.choice(location_types)
            danger = random.randint(1, 7)

            location = await self.generate_location(
                db=db,
                campaign_id=campaign_id,
                location_type=loc_type,
                theme=theme,
                danger_level=danger,
                parent_location_id=region.id,
            )
            locations.append(location)

            # Connect to nearby locations
            if len(locations) > 2:
                # Connect to 1-2 random other locations
                num_connections = random.randint(1, min(2, len(locations) - 2))
                for _ in range(num_connections):
                    other = random.choice(locations[1:-1])
                    if other.id != location.id:
                        self.knowledge_graph.add_relationship(
                            source_id=location.id,
                            target_id=other.id,
                            edge_type="connected_to",
                            properties={
                                "path_type": random.choice(["road", "trail", "river", "mountain pass"]),
                                "travel_time": f"{random.randint(1, 48)} hours",
                            },
                        )

        await self.knowledge_graph.save_to_database(db, campaign_id)

        return locations

    async def connect_locations(
        self,
        db: AsyncSession,
        location_a_id: str,
        location_b_id: str,
        path_type: str = "road",
        travel_time: Optional[str] = None,
    ) -> None:
        """Connect two locations.

        Args:
            db: Database session
            location_a_id: First location ID
            location_b_id: Second location ID
            path_type: Type of path
            travel_time: Travel time description
        """
        # Get locations to verify they exist
        loc_a_result = await db.execute(
            select(Location).where(Location.id == location_a_id)
        )
        loc_a = loc_a_result.scalar_one_or_none()

        loc_b_result = await db.execute(
            select(Location).where(Location.id == location_b_id)
        )
        loc_b = loc_b_result.scalar_one_or_none()

        if not loc_a or not loc_b:
            raise ValueError("One or both locations not found")

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != loc_a.campaign_id:
            await self.knowledge_graph.load_from_database(db, loc_a.campaign_id)

        # Add bidirectional connection
        properties = {"path_type": path_type}
        if travel_time:
            properties["travel_time"] = travel_time

        self.knowledge_graph.add_relationship(
            source_id=location_a_id,
            target_id=location_b_id,
            edge_type="connected_to",
            properties=properties,
        )

        self.knowledge_graph.add_relationship(
            source_id=location_b_id,
            target_id=location_a_id,
            edge_type="connected_to",
            properties=properties,
        )

        # Update location records
        if loc_a.connected_locations is None:
            loc_a.connected_locations = []
        loc_a.connected_locations.append({
            "location_id": location_b_id,
            "name": loc_b.name,
            "path_type": path_type,
            "travel_time": travel_time,
        })

        if loc_b.connected_locations is None:
            loc_b.connected_locations = []
        loc_b.connected_locations.append({
            "location_id": location_a_id,
            "name": loc_a.name,
            "path_type": path_type,
            "travel_time": travel_time,
        })

        await db.commit()
        await self.knowledge_graph.save_to_database(db, loc_a.campaign_id)

    async def discover_location(
        self,
        db: AsyncSession,
        location_id: str,
    ) -> Location:
        """Mark a location as discovered.

        Args:
            db: Database session
            location_id: Location ID

        Returns:
            Updated location
        """
        result = await db.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()

        if not location:
            raise ValueError(f"Location {location_id} not found")

        location.is_discovered = True
        await db.commit()
        await db.refresh(location)

        return location

    async def get_map_data(
        self,
        db: AsyncSession,
        campaign_id: str,
        include_undiscovered: bool = False,
    ) -> dict[str, Any]:
        """Get map data for visualization.

        Args:
            db: Database session
            campaign_id: Campaign ID
            include_undiscovered: Include undiscovered locations

        Returns:
            Map data with nodes and edges
        """
        query = select(Location).where(Location.campaign_id == campaign_id)
        if not include_undiscovered:
            query = query.where(Location.is_discovered == True)

        result = await db.execute(query)
        locations = result.scalars().all()

        nodes = []
        edges = []

        for loc in locations:
            nodes.append({
                "id": loc.id,
                "name": loc.name,
                "type": loc.location_type,
                "x": loc.x_coord,
                "y": loc.y_coord,
                "danger_level": loc.danger_level,
                "is_discovered": loc.is_discovered,
                "terrain": loc.terrain,
                "parent_id": loc.parent_location_id,
            })

            # Add edges for connections
            for conn in (loc.connected_locations or []):
                # Only add edge once (check if already added in reverse)
                conn_id = conn.get("location_id")
                if conn_id:
                    # Check if reverse edge exists
                    reverse_exists = any(
                        e["source"] == conn_id and e["target"] == loc.id
                        for e in edges
                    )
                    if not reverse_exists:
                        edges.append({
                            "source": loc.id,
                            "target": conn_id,
                            "path_type": conn.get("path_type", "road"),
                            "travel_time": conn.get("travel_time"),
                        })

        return {
            "campaign_id": campaign_id,
            "nodes": nodes,
            "edges": edges,
            "total_locations": len(locations),
        }


# Singleton instance
_map_generator: Optional[MapGenerator] = None


def get_map_generator() -> MapGenerator:
    """Get the map generator singleton."""
    global _map_generator
    if _map_generator is None:
        _map_generator = MapGenerator()
    return _map_generator
