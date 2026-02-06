"""API routers for Lorekeeper."""

from app.routers.campaigns import router as campaigns_router
from app.routers.sessions import router as sessions_router
from app.routers.characters import router as characters_router
from app.routers.narrative import router as narrative_router
from app.routers.encounters import router as encounters_router
from app.routers.locations import router as locations_router
from app.routers.knowledge import router as knowledge_router
from app.routers.dice import router as dice_router

__all__ = [
    "campaigns_router",
    "sessions_router",
    "characters_router",
    "narrative_router",
    "encounters_router",
    "locations_router",
    "knowledge_router",
    "dice_router",
]
