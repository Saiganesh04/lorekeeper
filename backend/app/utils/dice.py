"""Dice rolling utilities for RPG mechanics."""

import random
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiceResult:
    """Result of a dice roll."""

    notation: str
    total: int
    rolls: list[int]
    modifier: int = 0
    success: Optional[bool] = None
    critical: Optional[str] = None  # "hit" or "fail" for d20 rolls
    advantage_rolls: Optional[list[int]] = None  # For advantage/disadvantage


class DiceRoller:
    """Utility class for dice rolling operations."""

    DICE_PATTERN = re.compile(r"^(\d+)?d(\d+)([+-]\d+)?$", re.IGNORECASE)
    VALID_DICE = {4, 6, 8, 10, 12, 20, 100}

    @classmethod
    def parse_notation(cls, notation: str) -> tuple[int, int, int]:
        """Parse dice notation string (e.g., '2d6+3').

        Returns (count, sides, modifier).
        """
        notation = notation.replace(" ", "").lower()
        match = cls.DICE_PATTERN.match(notation)

        if not match:
            raise ValueError(f"Invalid dice notation: {notation}")

        count = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        if sides not in cls.VALID_DICE:
            raise ValueError(f"Invalid die type: d{sides}. Valid types: {cls.VALID_DICE}")

        if count < 1 or count > 100:
            raise ValueError(f"Dice count must be between 1 and 100: {count}")

        return count, sides, modifier

    @classmethod
    def roll_die(cls, sides: int) -> int:
        """Roll a single die."""
        return random.randint(1, sides)

    @classmethod
    def roll(cls, notation: str) -> DiceResult:
        """Roll dice using standard notation (e.g., '2d6+3')."""
        count, sides, modifier = cls.parse_notation(notation)
        rolls = [cls.roll_die(sides) for _ in range(count)]
        total = sum(rolls) + modifier

        critical = None
        if sides == 20 and count == 1:
            if rolls[0] == 20:
                critical = "hit"
            elif rolls[0] == 1:
                critical = "fail"

        return DiceResult(
            notation=notation,
            total=total,
            rolls=rolls,
            modifier=modifier,
            critical=critical,
        )

    @classmethod
    def roll_with_advantage(cls, notation: str = "1d20") -> DiceResult:
        """Roll with advantage (roll twice, take higher)."""
        count, sides, modifier = cls.parse_notation(notation)
        roll1 = [cls.roll_die(sides) for _ in range(count)]
        roll2 = [cls.roll_die(sides) for _ in range(count)]

        sum1, sum2 = sum(roll1), sum(roll2)
        if sum1 >= sum2:
            rolls, advantage_rolls = roll1, roll2
        else:
            rolls, advantage_rolls = roll2, roll1

        total = sum(rolls) + modifier

        critical = None
        if sides == 20 and count == 1:
            if rolls[0] == 20:
                critical = "hit"
            elif rolls[0] == 1:
                critical = "fail"

        return DiceResult(
            notation=f"{notation} (advantage)",
            total=total,
            rolls=rolls,
            modifier=modifier,
            critical=critical,
            advantage_rolls=advantage_rolls,
        )

    @classmethod
    def roll_with_disadvantage(cls, notation: str = "1d20") -> DiceResult:
        """Roll with disadvantage (roll twice, take lower)."""
        count, sides, modifier = cls.parse_notation(notation)
        roll1 = [cls.roll_die(sides) for _ in range(count)]
        roll2 = [cls.roll_die(sides) for _ in range(count)]

        sum1, sum2 = sum(roll1), sum(roll2)
        if sum1 <= sum2:
            rolls, advantage_rolls = roll1, roll2
        else:
            rolls, advantage_rolls = roll2, roll1

        total = sum(rolls) + modifier

        critical = None
        if sides == 20 and count == 1:
            if rolls[0] == 20:
                critical = "hit"
            elif rolls[0] == 1:
                critical = "fail"

        return DiceResult(
            notation=f"{notation} (disadvantage)",
            total=total,
            rolls=rolls,
            modifier=modifier,
            critical=critical,
            advantage_rolls=advantage_rolls,
        )

    @classmethod
    def skill_check(
        cls,
        dc: int,
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> DiceResult:
        """Make a skill check against a DC."""
        notation = f"1d20{'+' if modifier >= 0 else ''}{modifier}" if modifier else "1d20"

        if advantage and not disadvantage:
            result = cls.roll_with_advantage(notation)
        elif disadvantage and not advantage:
            result = cls.roll_with_disadvantage(notation)
        else:
            result = cls.roll(notation)

        result.success = result.total >= dc
        return result

    @classmethod
    def saving_throw(
        cls,
        dc: int,
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> DiceResult:
        """Make a saving throw against a DC."""
        return cls.skill_check(dc, modifier, advantage, disadvantage)

    @classmethod
    def attack_roll(
        cls,
        ac: int,
        modifier: int = 0,
        advantage: bool = False,
        disadvantage: bool = False,
    ) -> DiceResult:
        """Make an attack roll against AC."""
        result = cls.skill_check(ac, modifier, advantage, disadvantage)

        # Critical hits always succeed, critical fails always miss
        if result.critical == "hit":
            result.success = True
        elif result.critical == "fail":
            result.success = False

        return result

    @classmethod
    def roll_initiative(cls, dex_modifier: int = 0) -> DiceResult:
        """Roll initiative (d20 + DEX modifier)."""
        notation = f"1d20{'+' if dex_modifier >= 0 else ''}{dex_modifier}"
        return cls.roll(notation)

    @classmethod
    def roll_damage(cls, notation: str, critical: bool = False) -> DiceResult:
        """Roll damage dice, optionally doubling for critical hit."""
        count, sides, modifier = cls.parse_notation(notation)

        if critical:
            count *= 2

        actual_notation = f"{count}d{sides}{'+' if modifier >= 0 else ''}{modifier}" if modifier else f"{count}d{sides}"
        return cls.roll(actual_notation)

    @classmethod
    def roll_stat(cls) -> int:
        """Roll a stat (4d6, drop lowest)."""
        rolls = [cls.roll_die(6) for _ in range(4)]
        rolls.sort(reverse=True)
        return sum(rolls[:3])

    @classmethod
    def roll_stats(cls) -> dict[str, int]:
        """Roll a complete stat block."""
        stats = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        return {stat: cls.roll_stat() for stat in stats}


# Convenience functions
def roll(notation: str) -> DiceResult:
    """Roll dice using standard notation."""
    return DiceRoller.roll(notation)


def roll_with_advantage(notation: str = "1d20") -> DiceResult:
    """Roll with advantage."""
    return DiceRoller.roll_with_advantage(notation)


def roll_with_disadvantage(notation: str = "1d20") -> DiceResult:
    """Roll with disadvantage."""
    return DiceRoller.roll_with_disadvantage(notation)
