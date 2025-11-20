"""Rules engine evaluating domain events to produce outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Protocol

from src.events import MoveEvent, SpreadEvent
from src.result import Result


class RuleHandler(Protocol):
    def evaluate(self, events: Iterable[object], base_data: dict | None) -> Result | None:
        ...


@dataclass
class RulesEngine:
    handlers: List[RuleHandler]

    def evaluate(self, events: List[object], base_data: dict | None) -> Result:
        base = {**(base_data or {})}
        for handler in self.handlers:
            outcome = handler.evaluate(events, base)
            if outcome is not None:
                return outcome
        return Result(ok=True, status="ok", data=base)


class LavaContactRule:
    def evaluate(self, events: Iterable[object], base_data: dict | None) -> Result | None:
        for event in events:
            if isinstance(event, MoveEvent) and event.actor == "player" and event.target_kind == "lava":
                return Result(ok=False, status="lose", reason="lava_hit", data=base_data)
        return None


class PlayerGoalRule:
    def evaluate(self, events: Iterable[object], base_data: dict | None) -> Result | None:
        orbs_remaining = (base_data or {}).get("orbs_remaining", 0)
        for event in events:
            if isinstance(event, MoveEvent) and event.actor == "player" and event.landed_on_goal:
                if orbs_remaining > 0:
                    return None
                print("you win")
                return Result(ok=True, status="win", data=base_data)
        return None


class LavaSpreadHitRule:
    def evaluate(self, events: Iterable[object], base_data: dict | None) -> Result | None:
        for event in events:
            if isinstance(event, SpreadEvent) and event.kind == "lava" and event.hits_player:
                return Result(ok=False, status="lose", reason="lava_spread_hit", data=base_data)
        return None
