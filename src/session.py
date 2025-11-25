import copy
from dataclasses import dataclass
from typing import Dict, Tuple

from src.Board import BoardState
from src.factory import GameFactory, GameContext
from src.result import Result


@dataclass
class StepOutcome:

    result: Result


class GameSession:
    def __init__(self, factory: GameFactory, level_number: int):
        self.factory = factory
        self.level_number = level_number
        self._history: list[BoardState] = []
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
        self._history.clear()
        self._ctx = self.factory.create(self.level_number)

    def step(self, command: str) -> StepOutcome:
        command = command.upper()
        if command == "U":
            return self._undo()

        snapshot = self._snapshot_state()
        movement = self._ctx.movement.move_player(command)
        if not movement.ok:
            blocked = Result(
                ok=False,
                status="blocked",
                reason=movement.reason,
                data=movement.data,
            )
            return StepOutcome(self._attach_metadata(blocked))

        self._history.append(snapshot)

        events: list[object] = list(movement.events)

        counter_event = self._ctx.counter.tick()
        events.append(counter_event)

        for kind in ("aqua", "lava"):
            spread_event = self._ctx.spread.spread(kind)
            events.append(spread_event)

        result = self._ctx.rules_engine.evaluate(events, movement.data)
        return StepOutcome(self._attach_metadata(result))

    # ----------------------------------------------------------- Undo helpers

    def _snapshot_state(self) -> BoardState:
        return copy.deepcopy(self._ctx.board.state)

    def _restore_state(self, state: BoardState) -> None:
        self._ctx.board.state = state

    def _undo(self) -> StepOutcome:
        if not self._history:
            result = Result(ok=False, status="blocked", reason="no_undo", data={"undone": False})
            return StepOutcome(self._attach_metadata(result))

        prior_state = self._history.pop()
        self._restore_state(prior_state)
        result = Result(ok=True, status="undo", data={"undone": True})
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
