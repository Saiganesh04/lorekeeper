"""Narrative generation Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PlayerActionRequest(BaseModel):
    """Schema for player action submission."""

    action: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = None
    dice_result: Optional[dict] = None  # If player pre-rolled


class NewEntity(BaseModel):
    """Schema for a new entity introduced in the narrative."""

    name: str
    entity_type: str  # character, location, item, etc.
    description: str
    properties: Optional[dict] = None


class KnowledgeUpdate(BaseModel):
    """Schema for a knowledge graph update."""

    action: str  # add_relationship, remove_relationship, update_property
    entity: str
    relationship: Optional[str] = None
    target: Optional[str] = None
    properties: Optional[dict] = None


class DiceRollResult(BaseModel):
    """Schema for a dice roll result."""

    notation: str
    total: int
    rolls: list[int]
    modifier: int = 0
    success: Optional[bool] = None
    critical: Optional[str] = None  # hit, fail


class StoryBeatResponse(BaseModel):
    """Schema for a story beat response from AI."""

    id: str
    session_id: str
    event_type: str
    content: str  # The narrative text (markdown)
    player_action: Optional[str] = None
    choices: Optional[list[str]] = None
    mood: str
    speaker: Optional[str] = None
    dice_rolls: Optional[list[DiceRollResult]] = None
    new_entities: Optional[list[NewEntity]] = None
    knowledge_updates: Optional[list[KnowledgeUpdate]] = None
    xp_awarded: Optional[int] = None
    items_awarded: Optional[list[dict]] = None
    sequence_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class StoryFeedResponse(BaseModel):
    """Schema for full story feed."""

    session_id: str
    events: list[StoryBeatResponse]
    total_events: int
    current_mood: str
    current_location: Optional[str] = None


class ChoiceSelectRequest(BaseModel):
    """Schema for selecting a branching choice."""

    event_id: str
    choice_index: int = Field(..., ge=0)


class RecapResponse(BaseModel):
    """Schema for session recap."""

    session_id: str
    session_number: int
    recap: str
    key_events: list[str]
    characters_met: list[str]
    locations_visited: list[str]
    items_acquired: list[str]
    total_xp: int


class OpeningRequest(BaseModel):
    """Schema for generating campaign/session opening."""

    style: str = Field(default="dramatic", pattern="^(dramatic|mysterious|action|calm)$")
    include_recap: bool = False
    focus_characters: Optional[list[str]] = None
    focus_location: Optional[str] = None
