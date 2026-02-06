"""Narrative engine service for story generation."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, GameSession, StoryEvent, Character, Location
from app.services.ai_engine import AIEngine, get_ai_engine
from app.services.knowledge_graph import KnowledgeGraph
from app.utils.prompts import PromptTemplates


class NarrativeEngine:
    """Service for generating story content using AI with knowledge graph context."""

    def __init__(
        self,
        ai_engine: Optional[AIEngine] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ):
        """Initialize narrative engine.

        Args:
            ai_engine: AI engine instance
            knowledge_graph: Knowledge graph instance
        """
        self.ai_engine = ai_engine or get_ai_engine()
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()

    async def _get_campaign_context(
        self, db: AsyncSession, campaign_id: str
    ) -> dict[str, Any]:
        """Get campaign information for prompts.

        Args:
            db: Database session
            campaign_id: Campaign ID

        Returns:
            Campaign context dictionary
        """
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return {}

        return {
            "campaign_name": campaign.name,
            "genre": campaign.genre,
            "tone": campaign.tone,
            "setting_description": campaign.setting_description or "",
        }

    async def _get_recent_events(
        self, db: AsyncSession, session_id: str, limit: int = 10
    ) -> str:
        """Get recent story events summary.

        Args:
            db: Database session
            session_id: Game session ID
            limit: Maximum events to include

        Returns:
            Formatted events summary
        """
        result = await db.execute(
            select(StoryEvent)
            .where(StoryEvent.session_id == session_id)
            .order_by(StoryEvent.sequence_order.desc())
            .limit(limit)
        )
        events = result.scalars().all()

        if not events:
            return "This is the beginning of the adventure."

        # Reverse to get chronological order
        events = list(reversed(events))

        summaries = []
        for event in events:
            if event.player_action:
                summaries.append(f"Player: {event.player_action}")
            if event.content:
                # Truncate long content
                content = event.content[:200] + "..." if len(event.content) > 200 else event.content
                summaries.append(f"Story: {content}")

        return "\n".join(summaries[-20:])  # Last 20 entries

    async def _get_character_summaries(
        self, db: AsyncSession, campaign_id: str, character_type: str = "pc"
    ) -> str:
        """Get summaries of characters.

        Args:
            db: Database session
            campaign_id: Campaign ID
            character_type: Type filter (pc, npc, all)

        Returns:
            Formatted character summaries
        """
        query = select(Character).where(
            Character.campaign_id == campaign_id,
            Character.is_alive == True,
        )

        if character_type != "all":
            query = query.where(Character.character_type == character_type)

        result = await db.execute(query.limit(10))
        characters = result.scalars().all()

        if not characters:
            return "No active characters."

        summaries = []
        for char in characters:
            summary = f"- {char.name}"
            if char.race and char.char_class:
                summary += f" ({char.race} {char.char_class}, Level {char.level})"
            summary += f" - HP: {char.hp_current}/{char.hp_max}"
            if char.personality_traits:
                traits = ", ".join(char.personality_traits[:3])
                summary += f" - Traits: {traits}"
            summaries.append(summary)

        return "\n".join(summaries)

    async def _get_location_description(
        self, db: AsyncSession, location_id: Optional[str]
    ) -> str:
        """Get current location description.

        Args:
            db: Database session
            location_id: Location ID

        Returns:
            Location description
        """
        if not location_id:
            return "Location unknown."

        result = await db.execute(
            select(Location).where(Location.id == location_id)
        )
        location = result.scalar_one_or_none()

        if not location:
            return "Location unknown."

        description = f"{location.name}"
        if location.location_type:
            description += f" ({location.location_type})"
        description += f"\n{location.description or 'No description available.'}"

        if location.atmosphere:
            description += f"\nAtmosphere: {location.atmosphere}"

        return description

    async def _get_next_sequence_order(
        self, db: AsyncSession, session_id: str
    ) -> int:
        """Get the next sequence order for events.

        Args:
            db: Database session
            session_id: Game session ID

        Returns:
            Next sequence order number
        """
        result = await db.execute(
            select(func.max(StoryEvent.sequence_order)).where(
                StoryEvent.session_id == session_id
            )
        )
        max_order = result.scalar()
        return (max_order or 0) + 1

    async def generate_story_beat(
        self,
        db: AsyncSession,
        session_id: str,
        player_action: str,
        additional_context: str = "",
    ) -> StoryEvent:
        """Generate a story beat in response to player action.

        Args:
            db: Database session
            session_id: Game session ID
            player_action: Player's declared action
            additional_context: Any additional context

        Returns:
            Created StoryEvent
        """
        # Get session and campaign info
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        campaign_context = await self._get_campaign_context(db, session.campaign_id)

        # Load knowledge graph if not already loaded
        if self.knowledge_graph.campaign_id != session.campaign_id:
            await self.knowledge_graph.load_from_database(db, session.campaign_id)

        # Build context for AI
        recent_events = await self._get_recent_events(db, session_id)
        character_summaries = await self._get_character_summaries(db, session.campaign_id)

        # Get PCs for knowledge graph context
        pc_result = await db.execute(
            select(Character).where(
                Character.campaign_id == session.campaign_id,
                Character.character_type == "pc",
            )
        )
        pcs = pc_result.scalars().all()
        pc_ids = [pc.id for pc in pcs]

        # Get location from first PC or default
        location_id = pcs[0].current_location_id if pcs else None
        location_description = await self._get_location_description(db, location_id)

        # Get knowledge graph context
        context_entity_ids = pc_ids.copy()
        if location_id:
            context_entity_ids.append(location_id)
        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt(context_entity_ids)

        # Format system prompt
        system_prompt = PromptTemplates.NARRATIVE_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
            campaign_name=campaign_context.get("campaign_name", "Unknown Campaign"),
            tone=campaign_context.get("tone", "serious"),
            knowledge_graph_context=knowledge_context,
            recent_events_summary=recent_events,
            character_summaries=character_summaries,
            location_description=location_description,
        )

        # Format user prompt
        user_prompt = PromptTemplates.NARRATIVE_USER.format(
            player_action=player_action,
            additional_context=additional_context or "None",
        )

        # Generate response
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Process new entities and update knowledge graph
        new_entities = response.get("new_entities", [])
        for entity in new_entities or []:
            if entity.get("name") and entity.get("type"):
                self.knowledge_graph.add_entity(
                    node_id=str(uuid.uuid4()),
                    node_type=entity["type"],
                    name=entity["name"],
                    description=entity.get("description"),
                )

        # Process knowledge updates
        knowledge_updates = response.get("knowledge_updates", [])
        # These would be processed to update the graph relationships

        # Create story event
        sequence_order = await self._get_next_sequence_order(db, session_id)

        story_event = StoryEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            event_type="narrative",
            content=response.get("narrative", ""),
            player_action=player_action,
            choices=response.get("choices"),
            mood=response.get("mood", "neutral"),
            new_entities=new_entities,
            knowledge_updates=knowledge_updates,
            xp_awarded=response.get("xp_awarded"),
            sequence_order=sequence_order,
            location_id=location_id,
        )

        db.add(story_event)
        await db.commit()
        await db.refresh(story_event)

        # Save knowledge graph updates
        await self.knowledge_graph.save_to_database(db, session.campaign_id)

        return story_event

    async def generate_opening(
        self,
        db: AsyncSession,
        session_id: str,
        style: str = "dramatic",
        include_recap: bool = False,
    ) -> StoryEvent:
        """Generate an opening scene for a session.

        Args:
            db: Database session
            session_id: Game session ID
            style: Opening style (dramatic, mysterious, action, calm)
            include_recap: Whether to include recap of previous session

        Returns:
            Created StoryEvent
        """
        # Get session info
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        campaign_context = await self._get_campaign_context(db, session.campaign_id)

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != session.campaign_id:
            await self.knowledge_graph.load_from_database(db, session.campaign_id)

        # Get recap from previous session if needed
        recap_section = ""
        if include_recap and session.session_number > 1:
            prev_session_result = await db.execute(
                select(GameSession).where(
                    GameSession.campaign_id == session.campaign_id,
                    GameSession.session_number == session.session_number - 1,
                )
            )
            prev_session = prev_session_result.scalar_one_or_none()
            if prev_session and prev_session.recap:
                recap_section = f"\nPREVIOUSLY:\n{prev_session.recap}"

        # Build context
        character_summaries = await self._get_character_summaries(db, session.campaign_id)

        pc_result = await db.execute(
            select(Character).where(
                Character.campaign_id == session.campaign_id,
                Character.character_type == "pc",
            )
        )
        pcs = pc_result.scalars().all()
        location_id = pcs[0].current_location_id if pcs else None
        location_description = await self._get_location_description(db, location_id)

        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt(
            [pc.id for pc in pcs]
        )

        # Format prompts
        system_prompt = PromptTemplates.NARRATIVE_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
            campaign_name=campaign_context.get("campaign_name", "Unknown Campaign"),
            tone=campaign_context.get("tone", "serious"),
            knowledge_graph_context=knowledge_context,
            recent_events_summary="Starting new session.",
            character_summaries=character_summaries,
            location_description=location_description,
        )

        user_prompt = PromptTemplates.OPENING_SCENE.format(
            style=style,
            recap_section=recap_section,
        )

        # Generate response
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Create story event
        story_event = StoryEvent(
            id=str(uuid.uuid4()),
            session_id=session_id,
            event_type="narrative",
            content=response.get("narrative", ""),
            choices=response.get("choices"),
            mood=response.get("mood", "dramatic"),
            new_entities=response.get("new_entities"),
            knowledge_updates=response.get("knowledge_updates"),
            sequence_order=1,
            location_id=location_id,
        )

        db.add(story_event)
        await db.commit()
        await db.refresh(story_event)

        return story_event

    async def generate_scene_description(
        self,
        db: AsyncSession,
        campaign_id: str,
        location_id: str,
    ) -> str:
        """Generate a detailed scene description for a location.

        Args:
            db: Database session
            campaign_id: Campaign ID
            location_id: Location ID

        Returns:
            Detailed scene description
        """
        campaign_context = await self._get_campaign_context(db, campaign_id)
        location_description = await self._get_location_description(db, location_id)

        if self.knowledge_graph.campaign_id != campaign_id:
            await self.knowledge_graph.load_from_database(db, campaign_id)

        location_context = self.knowledge_graph.get_context_for_location(location_id)
        context_text = self.knowledge_graph.get_subgraph_for_prompt([location_id])

        system_prompt = f"""You are describing a location in a {campaign_context.get('genre', 'fantasy')} campaign.
The tone is {campaign_context.get('tone', 'serious')}. Create vivid, immersive descriptions."""

        user_prompt = f"""Describe this location in detail:

{location_description}

CONTEXT:
{context_text}

Include:
- Sensory details (sights, sounds, smells)
- Atmosphere and mood
- Notable features
- Any NPCs or creatures present
- Points of interest

Keep it to 2-3 paragraphs."""

        response = await self.ai_engine.generate(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        return response

    async def generate_recap(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> dict[str, Any]:
        """Generate a recap for a session.

        Args:
            db: Database session
            session_id: Game session ID

        Returns:
            Recap data including narrative and key points
        """
        # Get session info
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        campaign_context = await self._get_campaign_context(db, session.campaign_id)

        # Get all events from the session
        events_result = await db.execute(
            select(StoryEvent)
            .where(StoryEvent.session_id == session_id)
            .order_by(StoryEvent.sequence_order)
        )
        events = events_result.scalars().all()

        if not events:
            return {
                "recap": "Nothing significant happened in this session.",
                "key_events": [],
                "characters_met": [],
                "locations_visited": [],
                "items_acquired": [],
            }

        # Build events summary
        events_summary = []
        characters_met = set()
        locations_visited = set()
        items_acquired = []
        total_xp = 0

        for event in events:
            if event.content:
                events_summary.append(event.content[:300])
            if event.new_entities:
                for entity in event.new_entities:
                    if entity.get("type") == "character":
                        characters_met.add(entity.get("name", "Unknown"))
            if event.xp_awarded:
                total_xp += event.xp_awarded
            if event.items_awarded:
                items_acquired.extend(event.items_awarded)
            if event.location_id:
                locations_visited.add(event.location_id)

        # Get location names
        if locations_visited:
            loc_result = await db.execute(
                select(Location).where(Location.id.in_(locations_visited))
            )
            locations = loc_result.scalars().all()
            location_names = [loc.name for loc in locations]
        else:
            location_names = []

        # Generate recap
        system_prompt = PromptTemplates.RECAP_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
            tone=campaign_context.get("tone", "serious"),
        )

        user_prompt = PromptTemplates.RECAP_USER.format(
            session_number=session.session_number,
            events_summary="\n".join(events_summary[:20]),
            characters=", ".join(characters_met) or "None",
            locations=", ".join(location_names) or "Unknown",
            items=", ".join([str(i) for i in items_acquired[:10]]) or "None",
        )

        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Update session with recap
        session.recap = response.get("recap", "")
        await db.commit()

        return {
            "session_id": session_id,
            "session_number": session.session_number,
            "recap": response.get("recap", ""),
            "key_events": response.get("key_events", []),
            "characters_met": list(characters_met),
            "locations_visited": location_names,
            "items_acquired": items_acquired,
            "total_xp": total_xp,
        }

    async def branch_story(
        self,
        db: AsyncSession,
        session_id: str,
        event_id: str,
        choice_index: int,
    ) -> StoryEvent:
        """Branch the story based on a player choice.

        Args:
            db: Database session
            session_id: Game session ID
            event_id: Event with choices
            choice_index: Index of chosen option

        Returns:
            New story event continuing from the choice
        """
        # Get the event with choices
        event_result = await db.execute(
            select(StoryEvent).where(StoryEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()

        if not event or not event.choices:
            raise ValueError("Event not found or has no choices")

        if choice_index >= len(event.choices):
            raise ValueError(f"Invalid choice index: {choice_index}")

        chosen_action = event.choices[choice_index]

        # Mark the choice on the original event
        event.chosen_index = choice_index
        await db.commit()

        # Generate story beat based on the choice
        return await self.generate_story_beat(
            db=db,
            session_id=session_id,
            player_action=chosen_action,
            additional_context=f"The player chose: {chosen_action}",
        )


# Singleton instance
_narrative_engine: Optional[NarrativeEngine] = None


def get_narrative_engine() -> NarrativeEngine:
    """Get the narrative engine singleton."""
    global _narrative_engine
    if _narrative_engine is None:
        _narrative_engine = NarrativeEngine()
    return _narrative_engine
