"""Campaign management API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign, GameSession, Character, Location
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Create a new campaign."""
    campaign = Campaign(
        id=str(uuid.uuid4()),
        name=campaign_data.name,
        description=campaign_data.description,
        genre=campaign_data.genre,
        tone=campaign_data.tone,
        setting_description=campaign_data.setting_description,
        world_rules=campaign_data.world_rules,
    )

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        genre=campaign.genre,
        tone=campaign.tone,
        setting_description=campaign.setting_description,
        world_rules=campaign.world_rules,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        session_count=0,
        character_count=0,
        location_count=0,
    )


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CampaignListResponse:
    """List all campaigns."""
    # Get campaigns
    result = await db.execute(
        select(Campaign)
        .order_by(Campaign.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    campaigns = result.scalars().all()

    # Get total count
    count_result = await db.execute(select(func.count(Campaign.id)))
    total = count_result.scalar()

    # Get counts for each campaign
    campaign_responses = []
    for campaign in campaigns:
        session_count = await db.execute(
            select(func.count(GameSession.id)).where(
                GameSession.campaign_id == campaign.id
            )
        )
        character_count = await db.execute(
            select(func.count(Character.id)).where(
                Character.campaign_id == campaign.id
            )
        )
        location_count = await db.execute(
            select(func.count(Location.id)).where(
                Location.campaign_id == campaign.id
            )
        )

        campaign_responses.append(
            CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                description=campaign.description,
                genre=campaign.genre,
                tone=campaign.tone,
                setting_description=campaign.setting_description,
                world_rules=campaign.world_rules,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
                session_count=session_count.scalar(),
                character_count=character_count.scalar(),
                location_count=location_count.scalar(),
            )
        )

    return CampaignListResponse(campaigns=campaign_responses, total=total)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Get a campaign by ID."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get counts
    session_count = await db.execute(
        select(func.count(GameSession.id)).where(
            GameSession.campaign_id == campaign.id
        )
    )
    character_count = await db.execute(
        select(func.count(Character.id)).where(
            Character.campaign_id == campaign.id
        )
    )
    location_count = await db.execute(
        select(func.count(Location.id)).where(
            Location.campaign_id == campaign.id
        )
    )

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        genre=campaign.genre,
        tone=campaign.tone,
        setting_description=campaign.setting_description,
        world_rules=campaign.world_rules,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        session_count=session_count.scalar(),
        character_count=character_count.scalar(),
        location_count=location_count.scalar(),
    )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Update a campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update fields
    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    await db.commit()
    await db.refresh(campaign)

    # Get counts
    session_count = await db.execute(
        select(func.count(GameSession.id)).where(
            GameSession.campaign_id == campaign.id
        )
    )
    character_count = await db.execute(
        select(func.count(Character.id)).where(
            Character.campaign_id == campaign.id
        )
    )
    location_count = await db.execute(
        select(func.count(Location.id)).where(
            Location.campaign_id == campaign.id
        )
    )

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        genre=campaign.genre,
        tone=campaign.tone,
        setting_description=campaign.setting_description,
        world_rules=campaign.world_rules,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        session_count=session_count.scalar(),
        character_count=character_count.scalar(),
        location_count=location_count.scalar(),
    )


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a campaign."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()
