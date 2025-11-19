"""Domain events emitted by systems during a Lava & Aqua turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple

Coord = Tuple[int, int]


@dataclass(frozen=True)
class PushEvent:
    from_pos: Coord
    to_pos: Coord
    neutralized_kind: str | None = None


@dataclass(frozen=True)
class MoveEvent:
    actor: str
    origin: Coord
    destination: Coord
    target_kind: str | None
    landed_on_goal: bool
    push: PushEvent | None = None


@dataclass(frozen=True)
class SpreadEvent:
    kind: str
    sources: FrozenSet[Coord]
    new_cells: FrozenSet[Coord]
    hits_player: bool
    new_walls: FrozenSet[Coord]


@dataclass(frozen=True)
class CounterEvent:
    removed: FrozenSet[Coord]
    updated: Dict[Coord, int]
