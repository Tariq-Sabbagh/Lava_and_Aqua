"""Shared game session orchestration for Lava & Aqua."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

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

    def available_moves(self) -> Dict[str, Tuple[int, int]]:
        return self._ctx.movement.available_moves()

    def reset(self) -> None:
        self._ctx = self.factory.create(self.level_number)

    def step(self, command: str) -> StepOutcome:
        """Process one player command and all automatic follow-up actions."""

        movement = self._ctx.movement.move_player(command)
        if not movement.ok:
            data = movement.data or {}
            blocked = Result(
                ok=False,
                status="blocked",
                reason=movement.reason,
                data=data,
            )
            return StepOutcome(self._attach_available_moves(blocked))

        events: list[object] = list(movement.events)

        counter_event = self._ctx.counter.tick()
        events.append(counter_event)

        for kind in ("aqua", "lava"):
            spread_event = self._ctx.spread.spread(kind)
            events.append(spread_event)

        result = self._ctx.rules_engine.evaluate(events, movement.data)
        return StepOutcome(self._attach_available_moves(result))

    def _attach_available_moves(self, result: Result) -> Result:
        data = {**(result.data or {})}
        data["available_moves"] = self.available_moves()
        return Result(ok=result.ok, status=result.status, reason=result.reason, data=data)
