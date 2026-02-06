"""Pydantic schemas for request/response validation."""

from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
)
from app.schemas.session import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    CharacterListResponse,
    NPCCreate,
    DialogueRequest,
    DialogueResponse,
)
from app.schemas.narrative import (
    PlayerActionRequest,
    StoryBeatResponse,
    RecapResponse,
    StoryFeedResponse,
    ChoiceSelectRequest,
)
from app.schemas.encounter import (
    EncounterCreate,
    EncounterResponse,
    EncounterActionRequest,
    EncounterActionResponse,
    BalanceReport,
)
from app.schemas.knowledge import (
    KnowledgeNodeCreate,
    KnowledgeNodeResponse,
    KnowledgeEdgeCreate,
    KnowledgeEdgeResponse,
    KnowledgeGraphResponse,
    KnowledgeSearchResult,
)

__all__ = [
    # Campaign
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    "CampaignListResponse",
    # Session
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionListResponse",
    # Character
    "CharacterCreate",
    "CharacterUpdate",
    "CharacterResponse",
    "CharacterListResponse",
    "NPCCreate",
    "DialogueRequest",
    "DialogueResponse",
    # Narrative
    "PlayerActionRequest",
    "StoryBeatResponse",
    "RecapResponse",
    "StoryFeedResponse",
    "ChoiceSelectRequest",
    # Encounter
    "EncounterCreate",
    "EncounterResponse",
    "EncounterActionRequest",
    "EncounterActionResponse",
    "BalanceReport",
    # Knowledge
    "KnowledgeNodeCreate",
    "KnowledgeNodeResponse",
    "KnowledgeEdgeCreate",
    "KnowledgeEdgeResponse",
    "KnowledgeGraphResponse",
    "KnowledgeSearchResult",
]
