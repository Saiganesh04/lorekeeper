"""Encounter engine service for combat, social, and puzzle encounters."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Campaign, GameSession, Encounter, Character, Location
from app.services.ai_engine import AIEngine, get_ai_engine
from app.services.knowledge_graph import KnowledgeGraph
from app.utils.dice import DiceRoller
from app.utils.prompts import PromptTemplates


class EncounterEngine:
    """Service for generating and managing encounters."""

    # Difficulty multipliers for encounter balancing
    DIFFICULTY_MULTIPLIERS = {
        "easy": 0.5,
        "medium": 1.0,
        "hard": 1.5,
        "deadly": 2.0,
    }

    def __init__(
        self,
        ai_engine: Optional[AIEngine] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ):
        """Initialize encounter engine.

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
        }

    async def _get_party_info(
        self, db: AsyncSession, campaign_id: str
    ) -> dict[str, Any]:
        """Get party information for balancing."""
        result = await db.execute(
            select(Character).where(
                Character.campaign_id == campaign_id,
                Character.character_type == "pc",
                Character.is_alive == True,
            )
        )
        pcs = result.scalars().all()

        if not pcs:
            return {"size": 4, "average_level": 1, "total_hp": 40}

        levels = [pc.level for pc in pcs]
        total_hp = sum(pc.hp_current for pc in pcs)

        return {
            "size": len(pcs),
            "average_level": sum(levels) / len(levels),
            "total_hp": total_hp,
            "characters": [
                {
                    "id": pc.id,
                    "name": pc.name,
                    "class": pc.char_class,
                    "level": pc.level,
                    "hp_current": pc.hp_current,
                    "hp_max": pc.hp_max,
                    "ac": pc.armor_class,
                }
                for pc in pcs
            ],
        }

    def _calculate_enemy_power(self, enemies: list[dict]) -> float:
        """Calculate total enemy power for balancing."""
        power = 0
        for enemy in enemies:
            hp = enemy.get("hp_max", 10)
            ac = enemy.get("armor_class", 10)
            # Simplified power calculation
            power += (hp * 0.5) + (ac * 2)
            # Add for special abilities
            if enemy.get("special_abilities"):
                power += len(enemy["special_abilities"]) * 5
        return power

    def _calculate_party_power(self, party_info: dict) -> float:
        """Calculate party power for balancing."""
        size = party_info.get("size", 4)
        avg_level = party_info.get("average_level", 1)
        total_hp = party_info.get("total_hp", 40)
        # Simplified party power calculation
        return (total_hp * 0.5) + (avg_level * size * 10)

    async def generate_encounter(
        self,
        db: AsyncSession,
        session_id: str,
        encounter_type: str = "combat",
        difficulty: str = "medium",
        location_id: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> Encounter:
        """Generate a new encounter.

        Args:
            db: Database session
            session_id: Game session ID
            encounter_type: Type of encounter
            difficulty: Difficulty level
            location_id: Location ID
            theme: Enemy/encounter theme

        Returns:
            Created Encounter
        """
        # Get session and campaign info
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        campaign_context = await self._get_campaign_context(db, session.campaign_id)
        party_info = await self._get_party_info(db, session.campaign_id)

        # Load knowledge graph
        if self.knowledge_graph.campaign_id != session.campaign_id:
            await self.knowledge_graph.load_from_database(db, session.campaign_id)

        # Get location description
        location_description = "Unknown location"
        if location_id:
            loc_result = await db.execute(
                select(Location).where(Location.id == location_id)
            )
            location = loc_result.scalar_one_or_none()
            if location:
                location_description = f"{location.name}: {location.description or 'No description'}"

        knowledge_context = self.knowledge_graph.get_subgraph_for_prompt(
            [location_id] if location_id else []
        )

        # Get recent events for context
        recent_events = "No recent events."

        # Format prompts based on encounter type
        system_prompt = PromptTemplates.ENCOUNTER_GENERATION_SYSTEM.format(
            encounter_type=encounter_type,
            genre=campaign_context.get("genre", "fantasy"),
            difficulty=difficulty,
            party_size=party_info["size"],
            party_level=int(party_info["average_level"]),
            location_description=location_description,
            knowledge_graph_context=knowledge_context,
            recent_events=recent_events,
        )

        if encounter_type == "combat":
            user_prompt = PromptTemplates.COMBAT_ENCOUNTER_USER.format(
                theme=theme or "appropriate for the location",
                party_size=party_info["size"],
                party_level=int(party_info["average_level"]),
                difficulty=difficulty,
                location=location_description,
            )
        elif encounter_type == "social":
            user_prompt = PromptTemplates.SOCIAL_ENCOUNTER_USER.format(
                stakes="varies",
                npcs="to be determined",
                location=location_description,
                tension="medium",
            )
        elif encounter_type == "puzzle":
            user_prompt = PromptTemplates.PUZZLE_ENCOUNTER_USER.format(
                theme=theme or "mysterious",
                difficulty=difficulty,
                location=location_description,
            )
        else:
            user_prompt = PromptTemplates.COMBAT_ENCOUNTER_USER.format(
                theme=theme or "exploration hazard",
                party_size=party_info["size"],
                party_level=int(party_info["average_level"]),
                difficulty=difficulty,
                location=location_description,
            )

        # Generate encounter
        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Process enemies for combat encounters
        enemies = None
        initiative_order = None

        if encounter_type in ("combat", "boss"):
            enemies = response.get("enemies", [])
            # Assign IDs to enemies
            for i, enemy in enumerate(enemies):
                enemy["id"] = f"enemy_{i}_{uuid.uuid4().hex[:8]}"
                enemy["hp_current"] = enemy.get("hp_max", 10)
                enemy["is_defeated"] = False

            # Roll initiative for enemies
            initiative_order = []
            for enemy in enemies:
                dex_mod = (enemy.get("abilities", {}).get("dexterity", 10) - 10) // 2
                init_roll = DiceRoller.roll_initiative(dex_mod)
                initiative_order.append({
                    "character_id": enemy["id"],
                    "character_name": enemy["name"],
                    "initiative_roll": init_roll.total,
                    "is_enemy": True,
                    "is_current": False,
                })

            # Add party members to initiative
            for pc in party_info.get("characters", []):
                dex_mod = 0  # Would get from character stats
                init_roll = DiceRoller.roll_initiative(dex_mod)
                initiative_order.append({
                    "character_id": pc["id"],
                    "character_name": pc["name"],
                    "initiative_roll": init_roll.total,
                    "is_enemy": False,
                    "is_current": False,
                })

            # Sort by initiative (highest first)
            initiative_order.sort(key=lambda x: x["initiative_roll"], reverse=True)
            if initiative_order:
                initiative_order[0]["is_current"] = True

        # Create encounter
        encounter = Encounter(
            id=str(uuid.uuid4()),
            session_id=session_id,
            location_id=location_id,
            name=response.get("name", "Unknown Encounter"),
            encounter_type=encounter_type,
            description=response.get("description", ""),
            difficulty=difficulty,
            status="active",
            current_round=1,
            enemies=enemies,
            initiative_order=initiative_order,
            current_turn_index=0,
            combat_log=[],
            environmental_effects=response.get("environmental_effects"),
            terrain_features=response.get("terrain_features"),
            rewards=response.get("rewards"),
            party_level_at_start=int(party_info["average_level"]),
            party_size_at_start=party_info["size"],
        )

        # Add puzzle-specific fields
        if encounter_type == "puzzle":
            encounter.puzzle_description = response.get("setup")
            encounter.puzzle_solution = response.get("solution")
            encounter.puzzle_hints = response.get("hints", [])

        db.add(encounter)
        await db.commit()
        await db.refresh(encounter)

        return encounter

    async def balance_encounter(
        self,
        db: AsyncSession,
        encounter_id: str,
    ) -> dict[str, Any]:
        """Analyze and report on encounter balance.

        Args:
            db: Database session
            encounter_id: Encounter ID

        Returns:
            Balance report
        """
        encounter_result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = encounter_result.scalar_one_or_none()

        if not encounter:
            raise ValueError(f"Encounter {encounter_id} not found")

        # Get session to find campaign
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == encounter.session_id)
        )
        session = session_result.scalar_one_or_none()

        party_info = await self._get_party_info(db, session.campaign_id)

        party_power = self._calculate_party_power(party_info)
        enemy_power = self._calculate_enemy_power(encounter.enemies or [])

        # Calculate ratios
        power_ratio = enemy_power / party_power if party_power > 0 else 1

        # Determine actual difficulty
        if power_ratio < 0.6:
            actual_difficulty = "easy"
            survival_chance = 0.95
        elif power_ratio < 1.0:
            actual_difficulty = "medium"
            survival_chance = 0.85
        elif power_ratio < 1.5:
            actual_difficulty = "hard"
            survival_chance = 0.70
        else:
            actual_difficulty = "deadly"
            survival_chance = 0.50

        # Estimate rounds
        avg_damage_per_round = party_power * 0.1
        total_enemy_hp = sum(e.get("hp_max", 10) for e in (encounter.enemies or []))
        estimated_rounds = max(1, int(total_enemy_hp / avg_damage_per_round)) if avg_damage_per_round > 0 else 5

        # Generate recommendations
        recommendations = []
        if power_ratio > 1.5:
            recommendations.append("Consider removing an enemy or reducing HP")
        if power_ratio < 0.5:
            recommendations.append("Consider adding enemies or increasing difficulty")
        if estimated_rounds > 10:
            recommendations.append("Combat may be too long - consider reducing enemy HP")
        if estimated_rounds < 2:
            recommendations.append("Combat may be too short - consider adding enemies")

        return {
            "encounter_id": encounter_id,
            "difficulty_rating": actual_difficulty,
            "intended_difficulty": encounter.difficulty,
            "party_power": party_power,
            "enemy_power": enemy_power,
            "power_ratio": round(power_ratio, 2),
            "estimated_rounds": estimated_rounds,
            "survival_chance": survival_chance,
            "resource_cost": "high" if power_ratio > 1.2 else "medium" if power_ratio > 0.8 else "low",
            "recommendations": recommendations,
        }

    async def resolve_action(
        self,
        db: AsyncSession,
        encounter_id: str,
        character_id: str,
        action_type: str,
        target_id: Optional[str] = None,
        dice_result: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """Resolve a combat or encounter action.

        Args:
            db: Database session
            encounter_id: Encounter ID
            character_id: Acting character ID
            action_type: Type of action
            target_id: Target of action
            dice_result: Pre-rolled dice result
            description: Action description

        Returns:
            Action resolution result
        """
        encounter_result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = encounter_result.scalar_one_or_none()

        if not encounter or encounter.status != "active":
            raise ValueError("Encounter not found or not active")

        # Find the actor
        is_player = False
        actor_name = "Unknown"
        actor_stats = {}

        # Check if actor is an enemy
        for enemy in (encounter.enemies or []):
            if enemy.get("id") == character_id:
                actor_name = enemy.get("name", "Enemy")
                actor_stats = enemy
                break
        else:
            # Actor is a player character
            is_player = True
            session_result = await db.execute(
                select(GameSession).where(GameSession.id == encounter.session_id)
            )
            session = session_result.scalar_one_or_none()

            if session:
                char_result = await db.execute(
                    select(Character).where(Character.id == character_id)
                )
                character = char_result.scalar_one_or_none()
                if character:
                    actor_name = character.name
                    actor_stats = {
                        "strength": character.strength,
                        "dexterity": character.dexterity,
                    }

        # Find target
        target_name = None
        target_stats = {}
        target_is_enemy = False

        if target_id:
            for enemy in (encounter.enemies or []):
                if enemy.get("id") == target_id:
                    target_name = enemy.get("name", "Enemy")
                    target_stats = enemy
                    target_is_enemy = True
                    break

        # Resolve based on action type
        result = {
            "success": True,
            "description": "",
            "damage_dealt": None,
            "healing": None,
            "conditions_applied": [],
            "target_defeated": False,
            "dice_rolls": [],
        }

        if action_type == "attack":
            # Roll attack
            if dice_result:
                attack_roll = dice_result.get("total", 10)
            else:
                str_mod = (actor_stats.get("strength", 10) - 10) // 2
                roll = DiceRoller.attack_roll(
                    ac=target_stats.get("armor_class", 10),
                    modifier=str_mod,
                )
                attack_roll = roll.total
                result["dice_rolls"].append({
                    "type": "attack",
                    "notation": roll.notation,
                    "total": roll.total,
                    "success": roll.success,
                    "critical": roll.critical,
                })

            target_ac = target_stats.get("armor_class", 10)
            hit = attack_roll >= target_ac

            if hit:
                # Roll damage
                damage_roll = DiceRoller.roll("1d8+2")
                damage = damage_roll.total
                result["damage_dealt"] = damage
                result["dice_rolls"].append({
                    "type": "damage",
                    "notation": "1d8+2",
                    "total": damage,
                })

                # Apply damage to target
                if target_is_enemy:
                    for enemy in encounter.enemies:
                        if enemy.get("id") == target_id:
                            enemy["hp_current"] = max(0, enemy.get("hp_current", 0) - damage)
                            if enemy["hp_current"] <= 0:
                                enemy["is_defeated"] = True
                                result["target_defeated"] = True
                            break

                result["success"] = True
                result["description"] = f"{actor_name} hits {target_name} for {damage} damage!"
                if result["target_defeated"]:
                    result["description"] += f" {target_name} is defeated!"
            else:
                result["success"] = False
                result["description"] = f"{actor_name}'s attack misses {target_name}."

        elif action_type == "dodge":
            result["description"] = f"{actor_name} takes the Dodge action, gaining defensive advantage."
            result["conditions_applied"] = ["dodging"]

        elif action_type == "dash":
            result["description"] = f"{actor_name} dashes, doubling their movement speed."

        elif action_type == "help":
            result["description"] = f"{actor_name} helps an ally, granting them advantage on their next action."

        # Add to combat log
        if encounter.combat_log is None:
            encounter.combat_log = []

        encounter.combat_log.append({
            "round": encounter.current_round,
            "actor": actor_name,
            "actor_id": character_id,
            "action": action_type,
            "target": target_name,
            "target_id": target_id,
            "result": result["description"],
            "damage": result["damage_dealt"],
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Advance turn
        round_changed = False
        new_round = None

        if encounter.initiative_order:
            encounter.current_turn_index += 1
            if encounter.current_turn_index >= len(encounter.initiative_order):
                encounter.current_turn_index = 0
                encounter.current_round += 1
                round_changed = True
                new_round = encounter.current_round

            # Update current turn marker
            for i, entry in enumerate(encounter.initiative_order):
                entry["is_current"] = (i == encounter.current_turn_index)

        # Check if encounter is over
        enemies_remaining = sum(
            1 for e in (encounter.enemies or [])
            if not e.get("is_defeated", False)
        )

        if enemies_remaining == 0:
            encounter.status = "resolved"
            encounter.ended_at = datetime.utcnow()

        await db.commit()

        # Get next turn info
        next_turn = None
        if encounter.initiative_order and encounter.status == "active":
            next_turn = encounter.initiative_order[encounter.current_turn_index]

        return {
            "encounter_id": encounter_id,
            "action_result": result,
            "narrative": result["description"],
            "next_turn": next_turn,
            "encounter_status": encounter.status,
            "enemies_remaining": enemies_remaining,
            "round_changed": round_changed,
            "new_round": new_round,
        }

    async def generate_loot(
        self,
        db: AsyncSession,
        encounter_id: str,
    ) -> dict[str, Any]:
        """Generate loot for a completed encounter.

        Args:
            db: Database session
            encounter_id: Encounter ID

        Returns:
            Generated loot
        """
        encounter_result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = encounter_result.scalar_one_or_none()

        if not encounter:
            raise ValueError(f"Encounter {encounter_id} not found")

        # Use rewards from encounter generation, or generate new
        if encounter.rewards:
            return encounter.rewards

        # Get session info for campaign context
        session_result = await db.execute(
            select(GameSession).where(GameSession.id == encounter.session_id)
        )
        session = session_result.scalar_one_or_none()

        campaign_context = await self._get_campaign_context(db, session.campaign_id)

        system_prompt = PromptTemplates.ITEM_GENERATION_SYSTEM.format(
            genre=campaign_context.get("genre", "fantasy"),
        )

        user_prompt = PromptTemplates.LOOT_GENERATION_USER.format(
            difficulty=encounter.difficulty,
            encounter_type=encounter.encounter_type,
            party_level=encounter.party_level_at_start or 1,
            theme="general",
            location="unknown",
        )

        response = await self.ai_engine.generate_structured(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        # Store rewards on encounter
        encounter.rewards = response
        await db.commit()

        return response

    async def resolve_encounter(
        self,
        db: AsyncSession,
        encounter_id: str,
        outcome: str,
        distribute_rewards: bool = True,
    ) -> dict[str, Any]:
        """Resolve and end an encounter.

        Args:
            db: Database session
            encounter_id: Encounter ID
            outcome: How the encounter ended
            distribute_rewards: Whether to give rewards

        Returns:
            Resolution summary
        """
        encounter_result = await db.execute(
            select(Encounter).where(Encounter.id == encounter_id)
        )
        encounter = encounter_result.scalar_one_or_none()

        if not encounter:
            raise ValueError(f"Encounter {encounter_id} not found")

        encounter.status = "resolved"
        encounter.ended_at = datetime.utcnow()

        result = {
            "encounter_id": encounter_id,
            "outcome": outcome,
            "rounds_taken": encounter.current_round,
            "rewards_distributed": False,
            "rewards": None,
        }

        if distribute_rewards and outcome == "victory":
            loot = await self.generate_loot(db, encounter_id)
            result["rewards"] = loot
            result["rewards_distributed"] = True
            encounter.rewards_distributed = True

        await db.commit()

        return result


# Singleton instance
_encounter_engine: Optional[EncounterEngine] = None


def get_encounter_engine() -> EncounterEngine:
    """Get the encounter engine singleton."""
    global _encounter_engine
    if _encounter_engine is None:
        _encounter_engine = EncounterEngine()
    return _encounter_engine
