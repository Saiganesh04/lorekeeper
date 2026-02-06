"""Encounter management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GameSession, Encounter
from app.schemas.encounter import (
    EncounterCreate,
    EncounterResponse,
    EncounterActionRequest,
    EncounterActionResponse,
    BalanceReport,
    EncounterResolveRequest,
    LootResponse,
)
from app.services.encounter_engine import get_encounter_engine

router = APIRouter(tags=["encounters"])


def _encounter_to_response(encounter: Encounter) -> EncounterResponse:
    """Convert Encounter model to response schema."""
    return EncounterResponse(
        id=encounter.id,
        session_id=encounter.session_id,
        location_id=encounter.location_id,
        name=encounter.name,
        encounter_type=encounter.encounter_type,
        description=encounter.description or "",
        difficulty=encounter.difficulty,
        status=encounter.status,
        current_round=encounter.current_round,
        current_phase=encounter.current_phase,
        enemies=encounter.enemies,
        initiative_order=encounter.initiative_order,
        current_turn_index=encounter.current_turn_index,
        combat_log=encounter.combat_log,
        environmental_effects=encounter.environmental_effects,
        terrain_features=encounter.terrain_features,
        rewards=encounter.rewards,
        created_at=encounter.created_at,
        ended_at=encounter.ended_at,
    )


@router.post("/api/sessions/{session_id}/encounters", response_model=EncounterResponse, status_code=201)
async def create_encounter(
    session_id: str,
    encounter_data: EncounterCreate,
    db: AsyncSession = Depends(get_db),
) -> EncounterResponse:
    """Generate a new encounter for the session."""
    # Verify session exists and is active
    session_result = await db.execute(
        select(GameSession).where(GameSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    # Generate encounter
    encounter_engine = get_encounter_engine()
    encounter = await encounter_engine.generate_encounter(
        db=db,
        session_id=session_id,
        encounter_type=encounter_data.encounter_type,
        difficulty=encounter_data.difficulty,
        location_id=encounter_data.location_id,
        theme=encounter_data.theme,
    )

    return _encounter_to_response(encounter)


@router.get("/api/encounters/{encounter_id}", response_model=EncounterResponse)
async def get_encounter(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
) -> EncounterResponse:
    """Get an encounter by ID."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    return _encounter_to_response(encounter)


@router.post("/api/encounters/{encounter_id}/action", response_model=EncounterActionResponse)
async def submit_encounter_action(
    encounter_id: str,
    action_data: EncounterActionRequest,
    db: AsyncSession = Depends(get_db),
) -> EncounterActionResponse:
    """Submit an action in an encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    if encounter.status != "active":
        raise HTTPException(status_code=400, detail="Encounter is not active")

    # Resolve action
    encounter_engine = get_encounter_engine()
    response = await encounter_engine.resolve_action(
        db=db,
        encounter_id=encounter_id,
        character_id=action_data.character_id,
        action_type=action_data.action_type,
        target_id=action_data.target_id,
        dice_result=action_data.dice_result,
        description=action_data.description,
    )

    return EncounterActionResponse(
        encounter_id=response["encounter_id"],
        action_result=response["action_result"],
        narrative=response["narrative"],
        next_turn=response["next_turn"],
        encounter_status=response["encounter_status"],
        enemies_remaining=response["enemies_remaining"],
        round_changed=response["round_changed"],
        new_round=response["new_round"],
    )


@router.get("/api/encounters/{encounter_id}/balance", response_model=BalanceReport)
async def get_balance_report(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
) -> BalanceReport:
    """Get a balance report for an encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    encounter_engine = get_encounter_engine()
    report = await encounter_engine.balance_encounter(db, encounter_id)

    return BalanceReport(
        encounter_id=report["encounter_id"],
        difficulty_rating=report["difficulty_rating"],
        party_power=report["party_power"],
        enemy_power=report["enemy_power"],
        estimated_rounds=report["estimated_rounds"],
        survival_chance=report["survival_chance"],
        resource_cost=report["resource_cost"],
        recommendations=report["recommendations"],
    )


@router.post("/api/encounters/{encounter_id}/resolve")
async def resolve_encounter(
    encounter_id: str,
    resolve_data: EncounterResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resolve and end an encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    encounter_engine = get_encounter_engine()
    resolution = await encounter_engine.resolve_encounter(
        db=db,
        encounter_id=encounter_id,
        outcome=resolve_data.outcome,
        distribute_rewards=resolve_data.distribute_rewards,
    )

    return resolution


@router.get("/api/encounters/{encounter_id}/loot", response_model=LootResponse)
async def get_loot(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
) -> LootResponse:
    """Get or generate loot for an encounter."""
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")

    encounter_engine = get_encounter_engine()
    loot = await encounter_engine.generate_loot(db, encounter_id)

    return LootResponse(
        items=loot.get("items", []),
        gold=loot.get("gold", 0),
        experience=loot.get("xp", 0),
    )
