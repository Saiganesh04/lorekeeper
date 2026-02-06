"""NPC engine service for character generation and dialogue."""

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, Character, Location
from app.services.ai_engine import AIEngine, get_ai_engine
from app.services.knowledge_graph import KnowledgeGraph
from app.utils.prompts import PromptTemplates


class NPCEngine:
    """Service for NPC generation, personality, and dialogue."""

    def __init__(
        self,
        ai_engine: Optional[AIEngine] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ):
        """Initialize NPC engine.

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

    async def generate_npc(
        self,
        db: AsyncSession,
        campaign_id: str,
        role: Optional[str] = None,
        location_id: Optional[str] = None,
        personality_hints: Optional[list[str]] = None,
        name: Optional[str] = None,
    ) -> Character:
        """Generate a new NPC with AI.

        Args:
            db: Database session
            campaign_id: Campaign ID
            role: NPC role (innkeeper, guard, merchant, etc.)
            location_id: Location where NPC is found
            personality_hints: Hints for personality generation
            name: Optional pre-set name

        Returns:
            Created NPC Character
        """
        campaign_context = await self._get_campaign_context(db, campaign_id)

        # Load knowledge graph for context
        if self.knowledge_graph.campaign_id != campaign_id:
            await self.knowledge_graph.load_from_database(db, campaign_id)

        # Get location info
        location_name = "Unknown location"
        if location_id:
            loc_result = await db.execute(
                select(Location).where(Location.id == location_id)
            )
            location = loc_result.scalar_one_or_none()
            if location:
                location_name = f"{location.name} ({location.location_type})"

        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt(
            [location_id] if location_id else []
        )

        # Format prompts
        system_prompt = PromptTemplates.NPC_GENERATION_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
            tone=campaign_context.get("tone", "serious"),
            knowledge_graph_context=knowledge_context,
        )

        user_prompt = PromptTemplates.NPC_GENERATION_USER.format(
            role=role or "general townsperson",
            location=location_name,
            personality_hints=", ".join(personality_hints) if personality_hints else "None specified",
        )

        # Generate NPC
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Create character from response
        npc = Character(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            name=name or response.get("name", "Unknown NPC"),
            character_type="npc",
            race=response.get("race", "Human"),
            char_class=response.get("occupation"),
            level=1,
            hp_current=10,
            hp_max=10,
            personality_traits=response.get("personality_traits", []),
            backstory=response.get("backstory"),
            appearance=response.get("appearance"),
            motivation=response.get("motivation"),
            secret=response.get("secret"),
            speech_pattern=response.get("speech_pattern", "casual"),
            disposition=response.get("initial_disposition", 0),
            npc_memory=[],
            current_location_id=location_id,
        )

        db.add(npc)
        await db.commit()
        await db.refresh(npc)

        # Add to knowledge graph
        self.knowledge_graph.add_entity(
            node_id=npc.id,
            node_type="character",
            name=npc.name,
            description=npc.backstory,
            properties={
                "role": role,
                "personality": npc.personality_traits,
                "motivation": npc.motivation,
            },
        )

        if location_id:
            self.knowledge_graph.add_relationship(
                source_id=npc.id,
                target_id=location_id,
                edge_type="located_in",
            )

        await self.knowledge_graph.save_to_database(db, campaign_id)

        return npc

    async def generate_dialogue(
        self,
        db: AsyncSession,
        npc_id: str,
        player_message: str,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate NPC dialogue in response to player.

        Args:
            db: Database session
            npc_id: NPC character ID
            player_message: What the player said
            context: Additional context

        Returns:
            Dialogue response with mood and effects
        """
        # Get NPC
        npc_result = await db.execute(
            select(Character).where(Character.id == npc_id)
        )
        npc = npc_result.scalar_one_or_none()

        if not npc or npc.character_type != "npc":
            raise ValueError(f"NPC {npc_id} not found")

        campaign_context = await self._get_campaign_context(db, npc.campaign_id)

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != npc.campaign_id:
            await self.knowledge_graph.load_from_database(db, npc.campaign_id)

        # Get NPC's knowledge context
        npc_knowledge = self.knowledge_graph.get_character_knowledge(npc_id)
        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt([npc_id])

        # Format NPC memory
        npc_memory_text = "No previous interactions."
        if npc.npc_memory:
            memory_items = [f"- {m}" for m in npc.npc_memory[-10:]]
            npc_memory_text = "\n".join(memory_items)

        # Get current situation
        current_situation = "General conversation"
        if npc.current_location_id:
            loc_result = await db.execute(
                select(Location).where(Location.id == npc.current_location_id)
            )
            location = loc_result.scalar_one_or_none()
            if location:
                current_situation = f"At {location.name}"

        # Format prompts
        system_prompt = PromptTemplates.NPC_DIALOGUE_SYSTEM.format(
            npc_name=npc.name,
            genre=campaign_context.get("genre", "fantasy"),
            personality_traits=", ".join(npc.personality_traits or ["neutral"]),
            motivation=npc.motivation or "Unknown",
            secret=npc.secret or "None",
            speech_pattern=npc.speech_pattern or "casual",
            disposition=npc.disposition,
            npc_memory=npc_memory_text,
            knowledge_graph_context=knowledge_context,
            current_situation=current_situation,
        )

        user_prompt = PromptTemplates.NPC_DIALOGUE_USER.format(
            player_message=player_message,
            context=context or "None",
        )

        # Generate dialogue
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
            temperature=0.9,  # Slightly higher for more varied dialogue
        )

        # Update NPC memory
        memory_entry = f"Player said: '{player_message[:100]}' - Responded with {response.get('mood', 'neutral')} mood"
        if npc.npc_memory is None:
            npc.npc_memory = []
        npc.npc_memory.append(memory_entry)

        # Update disposition
        disposition_change = response.get("disposition_change", 0)
        npc.disposition = max(-100, min(100, npc.disposition + disposition_change))

        await db.commit()

        return {
            "character_id": npc_id,
            "character_name": npc.name,
            "dialogue": response.get("dialogue", "..."),
            "mood": response.get("mood", "neutral"),
            "disposition_change": disposition_change,
            "new_disposition": npc.disposition,
            "revealed_information": response.get("revealed_information"),
            "knowledge_updates": response.get("knowledge_updates"),
            "internal_thoughts": response.get("internal_thoughts"),
        }

    async def update_npc_disposition(
        self,
        db: AsyncSession,
        npc_id: str,
        event_description: str,
        disposition_change: int,
    ) -> None:
        """Update NPC's disposition based on events.

        Args:
            db: Database session
            npc_id: NPC character ID
            event_description: What happened
            disposition_change: How much to change disposition
        """
        npc_result = await db.execute(
            select(Character).where(Character.id == npc_id)
        )
        npc = npc_result.scalar_one_or_none()

        if not npc:
            return

        # Update disposition
        npc.disposition = max(-100, min(100, npc.disposition + disposition_change))

        # Add to memory
        if npc.npc_memory is None:
            npc.npc_memory = []
        npc.npc_memory.append(f"Event: {event_description} (disposition {'+' if disposition_change >= 0 else ''}{disposition_change})")

        await db.commit()

    async def get_npc_memory(
        self,
        db: AsyncSession,
        npc_id: str,
    ) -> dict[str, Any]:
        """Get what an NPC remembers about the party.

        Args:
            db: Database session
            npc_id: NPC character ID

        Returns:
            NPC memory and disposition info
        """
        npc_result = await db.execute(
            select(Character).where(Character.id == npc_id)
        )
        npc = npc_result.scalar_one_or_none()

        if not npc:
            raise ValueError(f"NPC {npc_id} not found")

        # Load knowledge graph for relationships
        if self.knowledge_graph.campaign_id != npc.campaign_id:
            await self.knowledge_graph.load_from_database(db, npc.campaign_id)

        npc_knowledge = self.knowledge_graph.get_character_knowledge(npc_id)

        return {
            "npc_id": npc_id,
            "npc_name": npc.name,
            "disposition": npc.disposition,
            "memory": npc.npc_memory or [],
            "known_characters": [
                {"id": c.get("id"), "name": c.get("name")}
                for c in npc_knowledge.get("known_characters", [])
            ],
            "known_locations": [
                {"id": l.get("id"), "name": l.get("name")}
                for l in npc_knowledge.get("known_locations", [])
            ],
            "faction_memberships": [
                {"id": f.get("id"), "name": f.get("name")}
                for f in npc_knowledge.get("faction_memberships", [])
            ],
        }

    async def get_npc_info_for_players(
        self,
        db: AsyncSession,
        npc_id: str,
    ) -> dict[str, Any]:
        """Get NPC info that players would know.

        This excludes secrets and internal motivations.

        Args:
            db: Database session
            npc_id: NPC character ID

        Returns:
            Player-visible NPC information
        """
        npc_result = await db.execute(
            select(Character).where(Character.id == npc_id)
        )
        npc = npc_result.scalar_one_or_none()

        if not npc:
            raise ValueError(f"NPC {npc_id} not found")

        # Basic info players can observe
        disposition_description = "hostile"
        if npc.disposition >= 50:
            disposition_description = "friendly"
        elif npc.disposition >= 20:
            disposition_description = "warm"
        elif npc.disposition >= -20:
            disposition_description = "neutral"
        elif npc.disposition >= -50:
            disposition_description = "cold"

        return {
            "id": npc.id,
            "name": npc.name,
            "race": npc.race,
            "occupation": npc.char_class,
            "appearance": npc.appearance,
            "demeanor": disposition_description,
            "observable_traits": npc.personality_traits[:2] if npc.personality_traits else [],
        }


# Singleton instance
_npc_engine: Optional[NPCEngine] = None


def get_npc_engine() -> NPCEngine:
    """Get the NPC engine singleton."""
    global _npc_engine
    if _npc_engine is None:
        _npc_engine = NPCEngine()
    return _npc_engine
