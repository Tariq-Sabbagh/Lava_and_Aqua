from __future__ import annotations

from typing import Dict, Iterable, List, Set, Tuple

from src.level_data import Coord, LevelLayout


BOARD_SYMBOL_MAP: Dict[str, Set[str]] = {
    "player": {"P"},
    "goal": {"G"},
    "lava": {"L"},
    "aqua": {"A"},
    "box": {"B"},
}
BOARD_DYNAMIC_KINDS = {"player", "lava", "aqua", "box"}
BOARD_KIND_TO_SYMBOL = {kind: next(iter(symbols)) for kind, symbols in BOARD_SYMBOL_MAP.items()}
BOARD_SYMBOL_TO_KIND: Dict[str, str] = {
    symbol: kind for kind, symbols in BOARD_SYMBOL_MAP.items() for symbol in symbols
}


class BoardState:
    """Mutable board data derived from an immutable LevelLayout."""

    SYMBOL_MAP = BOARD_SYMBOL_MAP
    DYNAMIC_KINDS = BOARD_DYNAMIC_KINDS
    KIND_TO_SYMBOL = BOARD_KIND_TO_SYMBOL
    SYMBOL_TO_KIND = BOARD_SYMBOL_TO_KIND

    def __init__(self, layout: LevelLayout):
        self.layout = layout
        self.rows = layout.rows
        self.cols = layout.cols
        self.grid = layout.grid_copy()
        self._base = layout.base_copy()
        self._static_goals = set(layout.static_goals)
        self._counters: Dict[Coord, int] = {}
        self._entities: Dict[str, Set[Coord]] = {kind: set() for kind in BOARD_DYNAMIC_KINDS}
        self._init_counters()
        self._entities = self._scan_entities()

    def iter_cells(self) -> Iterable[Tuple[int, int, str]]:
        for r, row_values in enumerate(self.grid):
            for c, symbol in enumerate(row_values):
                yield r, c, symbol

    def positions(self, entity_name: str):
        if entity_name == "goal":
            return frozenset(self._static_goals)
        return frozenset(self._entities.get(entity_name, set()))

    @property
    def player_positions(self):
        return self.positions("player")

    @property
    def goal_positions(self):
        return self.positions("goal")

    @property
    def lava_positions(self):
        return self.positions("lava")

    @property
    def aqua_positions(self):
        return self.positions("aqua")

    @property
    def box_positions(self):
        return self.positions("box")

    def is_goal_cell(self, r, c):
        return (r, c) in self._static_goals

    def _scan_entities(self):
        found: Dict[str, Set[Coord]] = {kind: set() for kind in BOARD_DYNAMIC_KINDS}
        for r, c, symbol in self.iter_cells():
            kind = BOARD_SYMBOL_TO_KIND.get(symbol)
            if kind in BOARD_DYNAMIC_KINDS:
                found[kind].add((r, c))
        return found

    def _symbol_is_counter(self, symbol: str) -> bool:
        return isinstance(symbol, str) and symbol.isdigit()

    def _init_counters(self):
        for r, row in enumerate(self.grid):
            for c, symbol in enumerate(row):
                if self._symbol_is_counter(symbol):
                    self._counters[(r, c)] = int(symbol)

    def get(self, r, c):
        return self.grid[r][c]

    def cell_base(self, r, c):
        return self._base[r][c]

    def is_counter(self, r, c):
        return (r, c) in self._counters

    def set(self, r, c, val):
        if not self.in_bounds(r, c):
            raise ValueError(f"set: out of bounds {(r, c)}")

        if val == ".":
            val = self._base[r][c]

        old_symbol = self.grid[r][c]
        if old_symbol == val and not self._symbol_is_counter(val):
            return

        if val == "W":
            self._base[r][c] = "W"

        self.grid[r][c] = val

        if self._symbol_is_counter(old_symbol):
            self._counters.pop((r, c), None)

        old_kind = BOARD_SYMBOL_TO_KIND.get(old_symbol)
        if old_kind in self._entities:
            self._entities[old_kind].discard((r, c))

        new_kind = BOARD_SYMBOL_TO_KIND.get(val)
        if new_kind in self._entities:
            self._entities[new_kind].add((r, c))

    def neighbors4(self, r, c) -> List[Coord]:
        neighbors: List[Coord] = []
        for dr, dc in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def update_entity(self, kind, old_pos, new_pos):
        if kind not in BOARD_DYNAMIC_KINDS:
            raise ValueError(f"update_entity: unsupported kind '{kind}'")

        olr, olc = old_pos
        nr, nc = new_pos
        if not (self.in_bounds(olr, olc) and self.in_bounds(nr, nc)):
            raise ValueError(f"update_entity {kind}: out of bounds")

        symbol = BOARD_KIND_TO_SYMBOL[kind]
        self.set(olr, olc, ".")
        self.set(nr, nc, symbol)

    def add_entity(self, kind, pos):
        if kind not in BOARD_DYNAMIC_KINDS:
            raise ValueError(f"add_entity: unsupported kind '{kind}'")
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"add_entity {kind}: out of bounds {pos}")
        symbol = BOARD_KIND_TO_SYMBOL[kind]
        self.set(r, c, symbol)

    def remove_entity(self, kind, pos):
        if kind not in BOARD_DYNAMIC_KINDS:
            raise ValueError(f"remove_entity: unsupported kind '{kind}'")
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"remove_entity {kind}: out of bounds {pos}")
        self.set(r, c, ".")

    def tick_counters(self):
        if not self._counters:
            return {"removed": set(), "updated": {}}

        removed = set()
        updated = {}
        for (r, c), value in list(self._counters.items()):
            value -= 1
            if value <= 0:
                removed.add((r, c))
                self._counters.pop((r, c), None)
                self.set(r, c, ".")
            else:
                self._counters[(r, c)] = value
                self.grid[r][c] = str(value)
                updated[(r, c)] = value
        return {"removed": removed, "updated": updated}

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, r, c):
        return self.grid[r][c] == "W" or self.is_counter(r, c)


class Board:
    """Facade combining an immutable layout with a mutable BoardState."""

    SYMBOL_MAP = BOARD_SYMBOL_MAP
    DYNAMIC_KINDS = BOARD_DYNAMIC_KINDS
    KIND_TO_SYMBOL = BOARD_KIND_TO_SYMBOL
    SYMBOL_TO_KIND = BOARD_SYMBOL_TO_KIND

    def __init__(self, layout: LevelLayout, state: BoardState | None = None):
        self.layout = layout
        self.state = state or BoardState(layout)

    def __getattr__(self, item):
        # Delegate stateful behavior to BoardState so existing call sites keep working.
        if item == "state":
            raise AttributeError
        return getattr(self.state, item)
