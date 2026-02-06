"""Campaign Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CampaignBase(BaseModel):
    """Base schema for campaign data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: str = Field(default="fantasy", pattern="^(fantasy|sci-fi|horror|steampunk)$")
    tone: str = Field(
        default="serious", pattern="^(serious|lighthearted|dark|epic)$"
    )
    setting_description: Optional[str] = None
    world_rules: Optional[dict] = None


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""

    pass


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = Field(None, pattern="^(fantasy|sci-fi|horror|steampunk)$")
    tone: Optional[str] = Field(None, pattern="^(serious|lighthearted|dark|epic)$")
    setting_description: Optional[str] = None
    world_rules: Optional[dict] = None


class CampaignResponse(CampaignBase):
    """Schema for campaign response."""

    id: str
    created_at: datetime
    updated_at: datetime
    session_count: int = 0
    character_count: int = 0
    location_count: int = 0

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Schema for list of campaigns."""

    campaigns: list[CampaignResponse]
    total: int
