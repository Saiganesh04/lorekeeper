"""Character Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AbilityScores(BaseModel):
    """Ability scores for a character."""

    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)


class CharacterBase(BaseModel):
    """Base schema for character data."""

    name: str = Field(..., min_length=1, max_length=255)
    character_type: str = Field(default="pc", pattern="^(pc|npc|monster)$")
    race: Optional[str] = None
    char_class: Optional[str] = None
    level: int = Field(default=1, ge=1, le=20)

    # Combat stats
    hp_max: int = Field(default=10, ge=1)
    armor_class: int = Field(default=10, ge=1)

    # Ability scores
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)

    # Personality
    personality_traits: Optional[list[str]] = None
    backstory: Optional[str] = None
    appearance: Optional[str] = None

    # Skills
    skills: Optional[dict[str, int]] = None
    proficiencies: Optional[list[str]] = None
    languages: Optional[list[str]] = None


class CharacterCreate(CharacterBase):
    """Schema for creating a new character."""

    pass


class NPCCreate(BaseModel):
    """Schema for creating an NPC with AI generation support."""

    name: Optional[str] = None  # Can be AI-generated
    role: Optional[str] = None  # Innkeeper, guard, merchant, etc.
    location_id: Optional[str] = None
    personality_hints: Optional[list[str]] = None
    generate_with_ai: bool = True


class CharacterUpdate(BaseModel):
    """Schema for updating a character."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    race: Optional[str] = None
    char_class: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=20)
    hp_current: Optional[int] = None
    hp_max: Optional[int] = Field(None, ge=1)
    armor_class: Optional[int] = Field(None, ge=1)

    strength: Optional[int] = Field(None, ge=1, le=30)
    dexterity: Optional[int] = Field(None, ge=1, le=30)
    constitution: Optional[int] = Field(None, ge=1, le=30)
    intelligence: Optional[int] = Field(None, ge=1, le=30)
    wisdom: Optional[int] = Field(None, ge=1, le=30)
    charisma: Optional[int] = Field(None, ge=1, le=30)

    personality_traits: Optional[list[str]] = None
    backstory: Optional[str] = None
    appearance: Optional[str] = None
    motivation: Optional[str] = None
    disposition: Optional[int] = Field(None, ge=-100, le=100)

    inventory: Optional[list[dict]] = None
    equipment: Optional[dict] = None
    gold: Optional[int] = Field(None, ge=0)
    experience_points: Optional[int] = Field(None, ge=0)

    is_alive: Optional[bool] = None
    conditions: Optional[list[str]] = None
    current_location_id: Optional[str] = None


class CharacterResponse(CharacterBase):
    """Schema for character response."""

    id: str
    campaign_id: str
    hp_current: int
    disposition: int = 0
    motivation: Optional[str] = None
    secret: Optional[str] = None
    speech_pattern: Optional[str] = None
    inventory: Optional[list[dict]] = None
    equipment: Optional[dict] = None
    gold: int = 0
    experience_points: int = 0
    is_alive: bool = True
    conditions: Optional[list[str]] = None
    current_location_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Calculated modifiers
    strength_modifier: int = 0
    dexterity_modifier: int = 0
    constitution_modifier: int = 0
    intelligence_modifier: int = 0
    wisdom_modifier: int = 0
    charisma_modifier: int = 0

    class Config:
        from_attributes = True


class CharacterListResponse(BaseModel):
    """Schema for list of characters."""

    characters: list[CharacterResponse]
    total: int


class DialogueRequest(BaseModel):
    """Schema for NPC dialogue request."""

    message: str = Field(..., min_length=1)
    context: Optional[str] = None
    include_knowledge: bool = True


class DialogueResponse(BaseModel):
    """Schema for NPC dialogue response."""

    character_id: str
    character_name: str
    dialogue: str
    mood: str
    disposition_change: int = 0
    revealed_information: Optional[list[str]] = None
    knowledge_updates: Optional[list[dict]] = None
