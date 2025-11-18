"""Shared game session orchestration for Lava & Aqua."""

from __future__ import annotations

from dataclasses import dataclass

from src.factory import GameFactory, GameContext
from src.result import Result


@dataclass
class StepOutcome:
    """Wrapper for per-command results so we can return move data on success."""

    result: Result


class GameSession:
    """Owns a GameContext lifecycle and encapsulates a full turn flow."""

    def __init__(self, factory: GameFactory, level_number: int):
        self.factory = factory
        self.level_number = level_number
        self._ctx: GameContext = self.factory.create(level_number)

    @property
    def context(self) -> GameContext:
        return self._ctx

    @property
    def board(self):
        return self._ctx.board

    def reset(self) -> None:
        self._ctx = self.factory.create(self.level_number)

    def step(self, command: str) -> StepOutcome:
        """Process one player command and all automatic follow-up actions."""

        move = self._ctx.rules.apply_move(command)
        if move.status != "ok":
            return StepOutcome(move)

        self._ctx.rules.tick_counters()

        lava = self._ctx.rules.apply_spread("lava")
        if lava.status != "ok":
            return StepOutcome(lava)

        aqua = self._ctx.rules.apply_spread("aqua")
        if aqua.status != "ok":
            return StepOutcome(aqua)

        return StepOutcome(move)
