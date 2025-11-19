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
            blocked = Result(
                ok=False,
                status="blocked",
                reason=movement.reason,
                data=movement.data,
            )
            return StepOutcome(self._attach_metadata(blocked))

        events: list[object] = list(movement.events)

        counter_event = self._ctx.counter.tick()
        events.append(counter_event)

        for kind in ("lava", "aqua"):
            spread_event = self._ctx.spread.spread(kind)
            events.append(spread_event)

        result = self._ctx.rules_engine.evaluate(events, movement.data)
        return StepOutcome(self._attach_metadata(result))

    def _attach_metadata(self, result: Result) -> Result:
        data = {**(result.data or {})}
        data.update(
            {
                "available_moves": self.available_moves(),
                "orbs_remaining": self.board.orbs_remaining,
                "orbs_total": self.board.orbs_total,
                "orbs_collected": self.board.orbs_total - self.board.orbs_remaining,
            }
        )
        return Result(ok=result.ok, status=result.status, reason=result.reason, data=data)
