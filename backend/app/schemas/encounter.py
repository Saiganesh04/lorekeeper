"""Encounter Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EnemyStats(BaseModel):
    """Schema for enemy stat block."""

    id: str
    name: str
    hp_current: int
    hp_max: int
    armor_class: int
    speed: int = 30
    abilities: Optional[dict[str, int]] = None  # STR, DEX, etc.
    attacks: Optional[list[dict]] = None  # [{name, damage, to_hit}]
    special_abilities: Optional[list[dict]] = None
    legendary_actions: Optional[list[dict]] = None
    is_defeated: bool = False


class InitiativeEntry(BaseModel):
    """Schema for initiative order entry."""

    character_id: str
    character_name: str
    initiative_roll: int
    is_enemy: bool = False
    is_current: bool = False


class EncounterCreate(BaseModel):
    """Schema for creating an encounter."""

    encounter_type: str = Field(
        default="combat", pattern="^(combat|social|puzzle|exploration|boss)$"
    )
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard|deadly)$")
    location_id: Optional[str] = None
    enemy_types: Optional[list[str]] = None  # Types of enemies to include
    theme: Optional[str] = None  # Undead, beast, humanoid, etc.
    party_level: int = Field(default=1, ge=1, le=20)
    party_size: int = Field(default=4, ge=1, le=10)


class EncounterResponse(BaseModel):
    """Schema for encounter response."""

    id: str
    session_id: str
    location_id: Optional[str]
    name: str
    encounter_type: str
    description: str
    difficulty: str
    status: str
    current_round: int
    current_phase: Optional[str]
    enemies: Optional[list[EnemyStats]]
    initiative_order: Optional[list[InitiativeEntry]]
    current_turn_index: int
    combat_log: Optional[list[dict]]
    environmental_effects: Optional[list[str]]
    terrain_features: Optional[list[str]]
    rewards: Optional[dict]
    created_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


class EncounterActionRequest(BaseModel):
    """Schema for encounter action."""

    character_id: str
    action_type: str  # attack, cast, move, dash, dodge, help, hide, disengage, use_item, ability, dialogue
    target_id: Optional[str] = None
    ability_name: Optional[str] = None
    item_name: Optional[str] = None
    dialogue: Optional[str] = None  # For social encounters
    dice_result: Optional[dict] = None  # If player pre-rolled
    description: Optional[str] = None  # Free-form action description


class ActionResult(BaseModel):
    """Schema for action result."""

    success: bool
    description: str
    damage_dealt: Optional[int] = None
    damage_taken: Optional[int] = None
    healing: Optional[int] = None
    conditions_applied: Optional[list[str]] = None
    conditions_removed: Optional[list[str]] = None
    dice_rolls: Optional[list[dict]] = None
    target_defeated: bool = False
    triggered_effects: Optional[list[str]] = None


class EncounterActionResponse(BaseModel):
    """Schema for encounter action response."""

    encounter_id: str
    action_result: ActionResult
    narrative: str
    next_turn: Optional[InitiativeEntry]
    encounter_status: str
    enemies_remaining: int
    round_changed: bool = False
    new_round: Optional[int] = None


class BalanceReport(BaseModel):
    """Schema for encounter balance report."""

    encounter_id: str
    difficulty_rating: str
    party_power: float
    enemy_power: float
    estimated_rounds: int
    survival_chance: float  # 0-1
    resource_cost: str  # low, medium, high
    recommendations: list[str]


class EncounterResolveRequest(BaseModel):
    """Schema for resolving/ending an encounter."""

    outcome: str = Field(..., pattern="^(victory|defeat|fled|negotiated)$")
    distribute_rewards: bool = True


class LootResponse(BaseModel):
    """Schema for generated loot."""

    items: list[dict]
    gold: int
    experience: int
