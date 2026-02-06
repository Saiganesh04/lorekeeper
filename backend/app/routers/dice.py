"""Dice rolling API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.utils.dice import DiceRoller

router = APIRouter(prefix="/api/dice", tags=["dice"])


class DiceRollRequest(BaseModel):
    """Schema for dice roll request."""
    notation: str = Field(..., pattern=r"^\d*d\d+([+-]\d+)?$", examples=["1d20", "2d6+3", "4d8-2"])
    advantage: bool = False
    disadvantage: bool = False


class DiceRollResponse(BaseModel):
    """Schema for dice roll response."""
    notation: str
    total: int
    rolls: list[int]
    modifier: int
    success: Optional[bool] = None
    critical: Optional[str] = None
    advantage_rolls: Optional[list[int]] = None


class SkillCheckRequest(BaseModel):
    """Schema for skill check request."""
    dc: int = Field(..., ge=1, le=30)
    modifier: int = Field(default=0)
    advantage: bool = False
    disadvantage: bool = False


class AttackRollRequest(BaseModel):
    """Schema for attack roll request."""
    target_ac: int = Field(..., ge=1, le=30)
    modifier: int = Field(default=0)
    advantage: bool = False
    disadvantage: bool = False
    damage_dice: Optional[str] = Field(None, examples=["1d8+3", "2d6+5"])


class AttackRollResponse(BaseModel):
    """Schema for attack roll response."""
    attack_roll: DiceRollResponse
    hit: bool
    critical_hit: bool
    critical_miss: bool
    damage: Optional[DiceRollResponse] = None


class InitiativeRollRequest(BaseModel):
    """Schema for initiative roll request."""
    dexterity_modifier: int = Field(default=0)


class StatsRollResponse(BaseModel):
    """Schema for stat roll response."""
    stats: dict[str, int]
    total: int
    rolls_detail: dict[str, list[int]]


@router.post("/roll", response_model=DiceRollResponse)
async def roll_dice(request: DiceRollRequest) -> DiceRollResponse:
    """Roll dice using standard notation."""
    try:
        if request.advantage and not request.disadvantage:
            result = DiceRoller.roll_with_advantage(request.notation)
        elif request.disadvantage and not request.advantage:
            result = DiceRoller.roll_with_disadvantage(request.notation)
        else:
            result = DiceRoller.roll(request.notation)

        return DiceRollResponse(
            notation=result.notation,
            total=result.total,
            rolls=result.rolls,
            modifier=result.modifier,
            success=result.success,
            critical=result.critical,
            advantage_rolls=result.advantage_rolls,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skill-check", response_model=DiceRollResponse)
async def skill_check(request: SkillCheckRequest) -> DiceRollResponse:
    """Make a skill check against a DC."""
    result = DiceRoller.skill_check(
        dc=request.dc,
        modifier=request.modifier,
        advantage=request.advantage,
        disadvantage=request.disadvantage,
    )

    return DiceRollResponse(
        notation=result.notation,
        total=result.total,
        rolls=result.rolls,
        modifier=result.modifier,
        success=result.success,
        critical=result.critical,
        advantage_rolls=result.advantage_rolls,
    )


@router.post("/saving-throw", response_model=DiceRollResponse)
async def saving_throw(request: SkillCheckRequest) -> DiceRollResponse:
    """Make a saving throw against a DC."""
    result = DiceRoller.saving_throw(
        dc=request.dc,
        modifier=request.modifier,
        advantage=request.advantage,
        disadvantage=request.disadvantage,
    )

    return DiceRollResponse(
        notation=result.notation,
        total=result.total,
        rolls=result.rolls,
        modifier=result.modifier,
        success=result.success,
        critical=result.critical,
        advantage_rolls=result.advantage_rolls,
    )


@router.post("/attack", response_model=AttackRollResponse)
async def attack_roll(request: AttackRollRequest) -> AttackRollResponse:
    """Make an attack roll against AC."""
    attack = DiceRoller.attack_roll(
        ac=request.target_ac,
        modifier=request.modifier,
        advantage=request.advantage,
        disadvantage=request.disadvantage,
    )

    attack_response = DiceRollResponse(
        notation=attack.notation,
        total=attack.total,
        rolls=attack.rolls,
        modifier=attack.modifier,
        success=attack.success,
        critical=attack.critical,
        advantage_rolls=attack.advantage_rolls,
    )

    damage_response = None
    if attack.success and request.damage_dice:
        is_crit = attack.critical == "hit"
        damage = DiceRoller.roll_damage(request.damage_dice, critical=is_crit)
        damage_response = DiceRollResponse(
            notation=damage.notation,
            total=damage.total,
            rolls=damage.rolls,
            modifier=damage.modifier,
            success=None,
            critical=None,
            advantage_rolls=None,
        )

    return AttackRollResponse(
        attack_roll=attack_response,
        hit=attack.success or False,
        critical_hit=attack.critical == "hit",
        critical_miss=attack.critical == "fail",
        damage=damage_response,
    )


@router.post("/initiative", response_model=DiceRollResponse)
async def initiative_roll(request: InitiativeRollRequest) -> DiceRollResponse:
    """Roll initiative."""
    result = DiceRoller.roll_initiative(request.dexterity_modifier)

    return DiceRollResponse(
        notation=result.notation,
        total=result.total,
        rolls=result.rolls,
        modifier=result.modifier,
        success=None,
        critical=result.critical,
        advantage_rolls=None,
    )


@router.post("/stats", response_model=StatsRollResponse)
async def roll_stats() -> StatsRollResponse:
    """Roll a complete stat block (4d6 drop lowest for each)."""
    stats = {}
    rolls_detail = {}

    stat_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

    for stat in stat_names:
        # Roll 4d6
        rolls = [DiceRoller.roll_die(6) for _ in range(4)]
        rolls_sorted = sorted(rolls, reverse=True)
        # Drop lowest, sum top 3
        value = sum(rolls_sorted[:3])
        stats[stat] = value
        rolls_detail[stat] = rolls

    return StatsRollResponse(
        stats=stats,
        total=sum(stats.values()),
        rolls_detail=rolls_detail,
    )
