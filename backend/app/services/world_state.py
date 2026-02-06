"""World state manager service for tracking the complete game state."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Campaign,
    GameSession,
    Character,
    Location,
    StoryEvent,
    Encounter,
    Item,
)
from app.services.knowledge_graph import KnowledgeGraph


class WorldStateManager:
    """Central manager for tracking and querying world state.

    This service provides a unified view of the game world by combining
    database queries with knowledge graph context.
    """

    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        """Initialize world state manager.

        Args:
            knowledge_graph: Knowledge graph instance
        """
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()

    async def get_campaign_state(
        self,
        db: AsyncSession,
        campaign_id: str,
    ) -> dict[str, Any]:
        """Get complete campaign state.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Complete campaign state dictionary
        """
        # Get campaign
        campaign_result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = campaign_result.scalar_one_or_none()

        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != campaign_id:
            await self.knowledge_graph.load_from_database(db, campaign_id)

        # Get counts
        session_count = await db.execute(
            select(func.count(GameSession.id)).where(
                GameSession.campaign_id == campaign_id
            )
        )
        character_count = await db.execute(
            select(func.count(Character.id)).where(
                Character.campaign_id == campaign_id
            )
        )
        location_count = await db.execute(
            select(func.count(Location.id)).where(
                Location.campaign_id == campaign_id
            )
        )

        # Get active session
        active_session_result = await db.execute(
            select(GameSession).where(
                GameSession.campaign_id == campaign_id,
                GameSession.status == "active",
            )
        )
        active_session = active_session_result.scalar_one_or_none()

        # Get PCs
        pcs_result = await db.execute(
            select(Character).where(
                Character.campaign_id == campaign_id,
                Character.character_type == "pc",
            )
        )
        pcs = pcs_result.scalars().all()

        # Get knowledge graph stats
        graph_stats = self.knowledge_graph.get_stats()

        return {
            "campaign": {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description,
                "genre": campaign.genre,
                "tone": campaign.tone,
                "created_at": campaign.created_at.isoformat(),
            },
            "stats": {
                "sessions": session_count.scalar(),
                "characters": character_count.scalar(),
                "locations": location_count.scalar(),
                "knowledge_nodes": graph_stats["total_nodes"],
                "knowledge_edges": graph_stats["total_edges"],
            },
            "active_session": {
                "id": active_session.id,
                "number": active_session.session_number,
                "started_at": active_session.started_at.isoformat(),
            } if active_session else None,
            "party": [
                {
                    "id": pc.id,
                    "name": pc.name,
                    "race": pc.race,
                    "class": pc.char_class,
                    "level": pc.level,
                    "hp_current": pc.hp_current,
                    "hp_max": pc.hp_max,
                }
                for pc in pcs
            ],
        }

    async def get_session_state(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> dict[str, Any]:
        """Get current session state.

        Args:
            db: Database session
            session_id: Game session ID

        Returns:
            Session state dictionary
        """
        # Get session
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != session.campaign_id:
            await self.knowledge_graph.load_from_database(db, session.campaign_id)

        # Get event count
        event_count = await db.execute(
            select(func.count(StoryEvent.id)).where(
                StoryEvent.session_id == session_id
            )
        )

        # Get latest event
        latest_event_result = await db.execute(
            select(StoryEvent)
            .where(StoryEvent.session_id == session_id)
            .order_by(StoryEvent.sequence_order.desc())
            .limit(1)
        )
        latest_event = latest_event_result.scalar_one_or_none()

        # Get active encounter
        active_encounter_result = await db.execute(
            select(Encounter).where(
                Encounter.session_id == session_id,
                Encounter.status == "active",
            )
        )
        active_encounter = active_encounter_result.scalar_one_or_none()

        # Get PCs and their current locations
        pcs_result = await db.execute(
            select(Character).where(
                Character.campaign_id == session.campaign_id,
                Character.character_type == "pc",
                Character.is_alive == True,
            )
        )
        pcs = pcs_result.scalars().all()

        # Get current location (from first PC)
        current_location = None
        if pcs and pcs[0].current_location_id:
            loc_result = await db.execute(
                select(Location).where(Location.id == pcs[0].current_location_id)
            )
            loc = loc_result.scalar_one_or_none()
            if loc:
                current_location = {
                    "id": loc.id,
                    "name": loc.name,
                    "type": loc.location_type,
                    "description": loc.description,
                    "danger_level": loc.danger_level,
                }

        return {
            "session": {
                "id": session.id,
                "campaign_id": session.campaign_id,
                "number": session.session_number,
                "status": session.status,
                "started_at": session.started_at.isoformat(),
            },
            "event_count": event_count.scalar(),
            "latest_event": {
                "id": latest_event.id,
                "type": latest_event.event_type,
                "mood": latest_event.mood,
                "content_preview": latest_event.content[:200] if latest_event.content else None,
                "has_choices": bool(latest_event.choices),
            } if latest_event else None,
            "active_encounter": {
                "id": active_encounter.id,
                "name": active_encounter.name,
                "type": active_encounter.encounter_type,
                "status": active_encounter.status,
                "round": active_encounter.current_round,
            } if active_encounter else None,
            "party_status": [
                {
                    "id": pc.id,
                    "name": pc.name,
                    "hp_current": pc.hp_current,
                    "hp_max": pc.hp_max,
                    "conditions": pc.conditions or [],
                }
                for pc in pcs
            ],
            "current_location": current_location,
        }

    async def get_party_status(
        self,
        db: AsyncSession,
        campaign_id: str,
    ) -> dict[str, Any]:
        """Get detailed party status.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Party status dictionary
        """
        # Get PCs
        pcs_result = await db.execute(
            select(Character).where(
                Character.campaign_id == campaign_id,
                Character.character_type == "pc",
            )
        )
        pcs = pcs_result.scalars().all()

        total_hp = sum(pc.hp_current for pc in pcs if pc.is_alive)
        total_max_hp = sum(pc.hp_max for pc in pcs if pc.is_alive)
        total_xp = sum(pc.experience_points for pc in pcs)
        avg_level = sum(pc.level for pc in pcs) / len(pcs) if pcs else 1

        return {
            "party_size": len(pcs),
            "alive_members": sum(1 for pc in pcs if pc.is_alive),
            "total_hp": total_hp,
            "total_max_hp": total_max_hp,
            "hp_percentage": round(total_hp / total_max_hp * 100, 1) if total_max_hp > 0 else 0,
            "average_level": round(avg_level, 1),
            "total_xp": total_xp,
            "total_gold": sum(pc.gold for pc in pcs),
            "members": [
                {
                    "id": pc.id,
                    "name": pc.name,
                    "race": pc.race,
                    "class": pc.char_class,
                    "level": pc.level,
                    "hp_current": pc.hp_current,
                    "hp_max": pc.hp_max,
                    "hp_percentage": round(pc.hp_current / pc.hp_max * 100, 1) if pc.hp_max > 0 else 0,
                    "ac": pc.armor_class,
                    "is_alive": pc.is_alive,
                    "conditions": pc.conditions or [],
                    "gold": pc.gold,
                    "xp": pc.experience_points,
                    "current_location_id": pc.current_location_id,
                }
                for pc in pcs
            ],
        }

    async def get_location_state(
        self,
        db: AsyncSession,
        location_id: str,
    ) -> dict[str, Any]:
        """Get detailed location state.

        Args:
            db: Database session
            location_id: Location ID

        Returns:
            Location state dictionary
        """
        # Get location
        loc_result = await db.execute(
            select(Location).where(Location.id == location_id)
        )
        location = loc_result.scalar_one_or_none()

        if not location:
            raise ValueError(f"Location {location_id} not found")

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != location.campaign_id:
            await self.knowledge_graph.load_from_database(db, location.campaign_id)

        # Get characters at location
        chars_result = await db.execute(
            select(Character).where(
                Character.current_location_id == location_id,
                Character.is_alive == True,
            )
        )
        characters = chars_result.scalars().all()

        # Get knowledge graph context for location
        location_context = self.knowledge_graph.get_context_for_location(location_id)

        return {
            "location": {
                "id": location.id,
                "name": location.name,
                "type": location.location_type,
                "description": location.description,
                "detailed_description": location.detailed_description,
                "danger_level": location.danger_level,
                "is_discovered": location.is_discovered,
                "terrain": location.terrain,
                "climate": location.climate,
                "atmosphere": location.atmosphere,
                "coordinates": {"x": location.x_coord, "y": location.y_coord},
            },
            "characters_present": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.character_type,
                    "disposition": c.disposition if c.character_type == "npc" else None,
                }
                for c in characters
            ],
            "points_of_interest": location.points_of_interest or [],
            "environmental_effects": location.environmental_effects or [],
            "connected_locations": location.connected_locations or [],
            "parent_location_id": location.parent_location_id,
            "knowledge_context": {
                "recent_events": [
                    {"name": e.get("name"), "description": e.get("description")}
                    for e in location_context.get("recent_events", [])[:5]
                ],
                "known_items": [
                    {"name": i.get("name")}
                    for i in location_context.get("items", [])[:10]
                ],
            },
        }

    async def move_party(
        self,
        db: AsyncSession,
        campaign_id: str,
        destination_id: str,
    ) -> dict[str, Any]:
        """Move the party to a new location.

        Args:
            db: Database session
            campaign_id: Campaign ID
            destination_id: Destination location ID

        Returns:
            Movement result with new location info
        """
        # Verify destination exists
        dest_result = await db.execute(
            select(Location).where(Location.id == destination_id)
        )
        destination = dest_result.scalar_one_or_none()

        if not destination:
            raise ValueError(f"Destination {destination_id} not found")

        # Get all PCs
        pcs_result = await db.execute(
            select(Character).where(
                Character.campaign_id == campaign_id,
                Character.character_type == "pc",
                Character.is_alive == True,
            )
        )
        pcs = pcs_result.scalars().all()

        # Get previous location
        previous_location = None
        if pcs and pcs[0].current_location_id:
            prev_result = await db.execute(
                select(Location).where(Location.id == pcs[0].current_location_id)
            )
            previous_location = prev_result.scalar_one_or_none()

        # Update all PCs to new location
        for pc in pcs:
            pc.current_location_id = destination_id

        # Mark location as discovered
        if not destination.is_discovered:
            destination.is_discovered = True

        await db.commit()

        return {
            "success": True,
            "previous_location": {
                "id": previous_location.id,
                "name": previous_location.name,
            } if previous_location else None,
            "new_location": {
                "id": destination.id,
                "name": destination.name,
                "type": destination.location_type,
                "description": destination.description,
                "danger_level": destination.danger_level,
            },
            "party_moved": len(pcs),
            "newly_discovered": not destination.is_discovered,
        }

    async def award_xp(
        self,
        db: AsyncSession,
        campaign_id: str,
        xp_amount: int,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """Award XP to the party.

        Args:
            db: Database session
            campaign_id: Campaign ID
            xp_amount: Amount of XP to award
            reason: Reason for award

        Returns:
            XP award result with level up info
        """
        # Get all living PCs
        pcs_result = await db.execute(
            select(Character).where(
                Character.campaign_id == campaign_id,
                Character.character_type == "pc",
                Character.is_alive == True,
            )
        )
        pcs = pcs_result.scalars().all()

        # XP per character (split evenly)
        xp_per_char = xp_amount // len(pcs) if pcs else 0

        # XP thresholds for leveling (simplified D&D 5e)
        xp_thresholds = [
            0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
            85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000
        ]

        level_ups = []

        for pc in pcs:
            old_level = pc.level
            pc.experience_points += xp_per_char

            # Check for level up
            new_level = old_level
            for level, threshold in enumerate(xp_thresholds):
                if pc.experience_points >= threshold:
                    new_level = level + 1

            if new_level > old_level and new_level <= 20:
                pc.level = new_level
                # Increase HP on level up (simplified)
                hp_increase = 5 + (pc.constitution - 10) // 2
                pc.hp_max += hp_increase
                pc.hp_current += hp_increase

                level_ups.append({
                    "character_id": pc.id,
                    "character_name": pc.name,
                    "old_level": old_level,
                    "new_level": new_level,
                    "hp_increase": hp_increase,
                })

        await db.commit()

        return {
            "total_xp_awarded": xp_amount,
            "xp_per_character": xp_per_char,
            "reason": reason,
            "characters_awarded": len(pcs),
            "level_ups": level_ups,
        }

    async def get_timeline(
        self,
        db: AsyncSession,
        campaign_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get campaign timeline of events.

        Args:
            db: Database session
            campaign_id: Campaign ID
            limit: Maximum events to return

        Returns:
            List of timeline events
        """
        # Get sessions for campaign
        sessions_result = await db.execute(
            select(GameSession).where(GameSession.campaign_id == campaign_id)
        )
        sessions = sessions_result.scalars().all()
        session_ids = [s.id for s in sessions]

        if not session_ids:
            return []

        # Get events
        events_result = await db.execute(
            select(StoryEvent)
            .where(StoryEvent.session_id.in_(session_ids))
            .order_by(StoryEvent.created_at.desc())
            .limit(limit)
        )
        events = events_result.scalars().all()

        timeline = []
        for event in events:
            session = next((s for s in sessions if s.id == event.session_id), None)
            timeline.append({
                "event_id": event.id,
                "session_id": event.session_id,
                "session_number": session.session_number if session else None,
                "event_type": event.event_type,
                "content_preview": event.content[:150] if event.content else None,
                "mood": event.mood,
                "has_choices": bool(event.choices),
                "xp_awarded": event.xp_awarded,
                "created_at": event.created_at.isoformat(),
            })

        return timeline


# Singleton instance
_world_state_manager: Optional[WorldStateManager] = None


def get_world_state_manager() -> WorldStateManager:
    """Get the world state manager singleton."""
    global _world_state_manager
    if _world_state_manager is None:
        _world_state_manager = WorldStateManager()
    return _world_state_manager
