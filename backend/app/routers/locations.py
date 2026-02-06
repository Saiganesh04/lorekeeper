"""Location management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Campaign, Location
from app.services.map_generator import get_map_generator

router = APIRouter(tags=["locations"])


class LocationCreate(BaseModel):
    """Schema for creating a location."""
    location_type: str = Field(default="wilderness")
    theme: Optional[str] = None
    danger_level: int = Field(default=3, ge=1, le=10)
    parent_location_id: Optional[str] = None
    name: Optional[str] = None


class LocationResponse(BaseModel):
    """Schema for location response."""
    id: str
    campaign_id: str
    name: str
    location_type: str
    description: Optional[str]
    detailed_description: Optional[str]
    x_coord: float
    y_coord: float
    danger_level: int
    is_discovered: bool
    terrain: Optional[str]
    climate: Optional[str]
    atmosphere: Optional[str]
    points_of_interest: Optional[list]
    environmental_effects: Optional[list]
    connected_locations: Optional[list]
    parent_location_id: Optional[str]

    class Config:
        from_attributes = True


class LocationListResponse(BaseModel):
    """Schema for list of locations."""
    locations: list[LocationResponse]
    total: int


class MapDataResponse(BaseModel):
    """Schema for map visualization data."""
    campaign_id: str
    nodes: list[dict]
    edges: list[dict]
    total_locations: int


class ConnectLocationsRequest(BaseModel):
    """Schema for connecting two locations."""
    location_a_id: str
    location_b_id: str
    path_type: str = "road"
    travel_time: Optional[str] = None


def _location_to_response(loc: Location) -> LocationResponse:
    """Convert Location model to response schema."""
    return LocationResponse(
        id=loc.id,
        campaign_id=loc.campaign_id,
        name=loc.name,
        location_type=loc.location_type,
        description=loc.description,
        detailed_description=loc.detailed_description,
        x_coord=loc.x_coord,
        y_coord=loc.y_coord,
        danger_level=loc.danger_level,
        is_discovered=loc.is_discovered,
        terrain=loc.terrain,
        climate=loc.climate,
        atmosphere=loc.atmosphere,
        points_of_interest=loc.points_of_interest,
        environmental_effects=loc.environmental_effects,
        connected_locations=loc.connected_locations,
        parent_location_id=loc.parent_location_id,
    )


@router.get("/api/campaigns/{campaign_id}/locations", response_model=LocationListResponse)
async def list_locations(
    campaign_id: str,
    location_type: Optional[str] = None,
    discovered_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> LocationListResponse:
    """List locations in a campaign."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Build query
    query = select(Location).where(Location.campaign_id == campaign_id)

    if location_type:
        query = query.where(Location.location_type == location_type)

    if discovered_only:
        query = query.where(Location.is_discovered == True)

    query = query.order_by(Location.name).offset(skip).limit(limit)

    result = await db.execute(query)
    locations = result.scalars().all()

    # Get total count
    count_query = select(func.count(Location.id)).where(
        Location.campaign_id == campaign_id
    )
    if location_type:
        count_query = count_query.where(Location.location_type == location_type)
    if discovered_only:
        count_query = count_query.where(Location.is_discovered == True)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return LocationListResponse(
        locations=[_location_to_response(loc) for loc in locations],
        total=total,
    )


@router.post("/api/campaigns/{campaign_id}/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    campaign_id: str,
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    """Generate a new location with AI."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    map_generator = get_map_generator()
    location = await map_generator.generate_location(
        db=db,
        campaign_id=campaign_id,
        location_type=location_data.location_type,
        theme=location_data.theme,
        danger_level=location_data.danger_level,
        parent_location_id=location_data.parent_location_id,
        name=location_data.name,
    )

    return _location_to_response(location)


@router.get("/api/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    """Get a location by ID."""
    result = await db.execute(
        select(Location).where(Location.id == location_id)
    )
    location = result.scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    return _location_to_response(location)


@router.post("/api/locations/{location_id}/discover", response_model=LocationResponse)
async def discover_location(
    location_id: str,
    db: AsyncSession = Depends(get_db),
) -> LocationResponse:
    """Mark a location as discovered."""
    map_generator = get_map_generator()
    location = await map_generator.discover_location(db, location_id)

    return _location_to_response(location)


@router.get("/api/campaigns/{campaign_id}/map", response_model=MapDataResponse)
async def get_map_data(
    campaign_id: str,
    include_undiscovered: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> MapDataResponse:
    """Get map visualization data for a campaign."""
    # Verify campaign exists
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    if not campaign_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    map_generator = get_map_generator()
    map_data = await map_generator.get_map_data(
        db=db,
        campaign_id=campaign_id,
        include_undiscovered=include_undiscovered,
    )

    return MapDataResponse(
        campaign_id=map_data["campaign_id"],
        nodes=map_data["nodes"],
        edges=map_data["edges"],
        total_locations=map_data["total_locations"],
    )


@router.post("/api/campaigns/{campaign_id}/locations/connect")
async def connect_locations(
    campaign_id: str,
    connect_data: ConnectLocationsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Connect two locations."""
    map_generator = get_map_generator()

    await map_generator.connect_locations(
        db=db,
        location_a_id=connect_data.location_a_id,
        location_b_id=connect_data.location_b_id,
        path_type=connect_data.path_type,
        travel_time=connect_data.travel_time,
    )

    return {"success": True, "message": "Locations connected"}
