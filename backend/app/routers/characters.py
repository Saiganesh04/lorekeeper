"""Character management API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign, Character
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    CharacterListResponse,
    NPCCreate,
    DialogueRequest,
    DialogueResponse,
)
from app.services.npc_engine import get_npc_engine

router = APIRouter(tags=["characters"])


def _character_to_response(char: Character) -> CharacterResponse:
    """Convert Character model to response schema."""
    return CharacterResponse(
        id=char.id,
        campaign_id=char.campaign_id,
        name=char.name,
        character_type=char.character_type,
        race=char.race,
        char_class=char.char_class,
        level=char.level,
        hp_current=char.hp_current,
        hp_max=char.hp_max,
        armor_class=char.armor_class,
        strength=char.strength,
        dexterity=char.dexterity,
        constitution=char.constitution,
        intelligence=char.intelligence,
        wisdom=char.wisdom,
        charisma=char.charisma,
        personality_traits=char.personality_traits,
        backstory=char.backstory,
        appearance=char.appearance,
        motivation=char.motivation,
        secret=char.secret,
        speech_pattern=char.speech_pattern,
        disposition=char.disposition,
        inventory=char.inventory,
        equipment=char.equipment,
        gold=char.gold,
        experience_points=char.experience_points,
        skills=char.skills,
        proficiencies=char.proficiencies,
        languages=char.languages,
        is_alive=char.is_alive,
        conditions=char.conditions,
        current_location_id=char.current_location_id,
        created_at=char.created_at,
        updated_at=char.updated_at,
        strength_modifier=char.strength_modifier,
        dexterity_modifier=char.dexterity_modifier,
        constitution_modifier=char.constitution_modifier,
        intelligence_modifier=char.intelligence_modifier,
        wisdom_modifier=char.wisdom_modifier,
        charisma_modifier=char.charisma_modifier,
    )


@router.post("/api/campaigns/{campaign_id}/characters", response_model=CharacterResponse, status_code=201)
async def create_character(
    campaign_id: str,
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Create a new player character."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Create character
    character = Character(
        id=str(uuid.uuid4()),
        campaign_id=campaign_id,
        name=character_data.name,
        character_type=character_data.character_type,
        race=character_data.race,
        char_class=character_data.char_class,
        level=character_data.level,
        hp_current=character_data.hp_max,
        hp_max=character_data.hp_max,
        armor_class=character_data.armor_class,
        strength=character_data.strength,
        dexterity=character_data.dexterity,
        constitution=character_data.constitution,
        intelligence=character_data.intelligence,
        wisdom=character_data.wisdom,
        charisma=character_data.charisma,
        personality_traits=character_data.personality_traits,
        backstory=character_data.backstory,
        appearance=character_data.appearance,
        skills=character_data.skills,
        proficiencies=character_data.proficiencies,
        languages=character_data.languages,
    )

    db.add(character)
    await db.commit()
    await db.refresh(character)

    return _character_to_response(character)


@router.post("/api/campaigns/{campaign_id}/npcs", response_model=CharacterResponse, status_code=201)
async def create_npc(
    campaign_id: str,
    npc_data: NPCCreate,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Create a new NPC, optionally with AI generation."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    if npc_data.generate_with_ai:
        # Generate NPC with AI
        npc_engine = get_npc_engine()
        character = await npc_engine.generate_npc(
            db=db,
            campaign_id=campaign_id,
            role=npc_data.role,
            location_id=npc_data.location_id,
            personality_hints=npc_data.personality_hints,
            name=npc_data.name,
        )
    else:
        # Create basic NPC
        character = Character(
            id=str(uuid.uuid4()),
            campaign_id=campaign_id,
            name=npc_data.name or "Unknown NPC",
            character_type="npc",
            level=1,
            hp_current=10,
            hp_max=10,
            current_location_id=npc_data.location_id,
        )
        db.add(character)
        await db.commit()
        await db.refresh(character)

    return _character_to_response(character)


@router.get("/api/campaigns/{campaign_id}/characters", response_model=CharacterListResponse)
async def list_characters(
    campaign_id: str,
    character_type: Optional[str] = Query(None, pattern="^(pc|npc|monster)$"),
    alive_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CharacterListResponse:
    """List characters in a campaign."""
    # Build query
    query = select(Character).where(Character.campaign_id == campaign_id)

    if character_type:
        query = query.where(Character.character_type == character_type)

    if alive_only:
        query = query.where(Character.is_alive == True)

    query = query.order_by(Character.name).offset(skip).limit(limit)

    result = await db.execute(query)
    characters = result.scalars().all()

    # Get total count
    count_query = select(func.count(Character.id)).where(
        Character.campaign_id == campaign_id
    )
    if character_type:
        count_query = count_query.where(Character.character_type == character_type)
    if alive_only:
        count_query = count_query.where(Character.is_alive == True)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CharacterListResponse(
        characters=[_character_to_response(c) for c in characters],
        total=total,
    )


@router.get("/api/characters/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Get a character by ID."""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    return _character_to_response(character)


@router.put("/api/characters/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: str,
    character_data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """Update a character."""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # Update fields
    update_data = character_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    await db.commit()
    await db.refresh(character)

    return _character_to_response(character)


@router.delete("/api/characters/{character_id}", status_code=204)
async def delete_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a character."""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    await db.delete(character)
    await db.commit()


@router.post("/api/characters/{character_id}/dialogue", response_model=DialogueResponse)
async def chat_with_npc(
    character_id: str,
    dialogue_data: DialogueRequest,
    db: AsyncSession = Depends(get_db),
) -> DialogueResponse:
    """Have a conversation with an NPC."""
    result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if character.character_type != "npc":
        raise HTTPException(status_code=400, detail="Can only chat with NPCs")

    npc_engine = get_npc_engine()
    response = await npc_engine.generate_dialogue(
        db=db,
        npc_id=character_id,
        player_message=dialogue_data.message,
        context=dialogue_data.context,
    )

    return DialogueResponse(
        character_id=response["character_id"],
        character_name=response["character_name"],
        dialogue=response["dialogue"],
        mood=response["mood"],
        disposition_change=response["disposition_change"],
        revealed_information=response.get("revealed_information"),
        knowledge_updates=response.get("knowledge_updates"),
    )
