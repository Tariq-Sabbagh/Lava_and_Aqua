
from typing import Dict, Iterable, List, Set, Tuple

from src.level_data import Coord, LevelLayout
from src.tiles import (
    DYNAMIC_KINDS as TILE_DYNAMIC_KINDS,
    KIND_TO_SYMBOL as TILE_KIND_TO_SYMBOL,
    SYMBOL_TO_KIND as TILE_SYMBOL_TO_KIND,
)


class BoardState:
    """Mutable board data derived from an immutable LevelLayout."""

    DYNAMIC_KINDS = TILE_DYNAMIC_KINDS
    KIND_TO_SYMBOL = TILE_KIND_TO_SYMBOL
    SYMBOL_TO_KIND = TILE_SYMBOL_TO_KIND

    def __init__(self, layout: LevelLayout):
        self.layout = layout
        self.rows = layout.rows
        self.cols = layout.cols
        self.grid = layout.grid_copy()
        self._base = layout.base_copy()
        self._static_goals = set(layout.static_goals)
        self._orbs: Set[Coord] = set(layout.orbs)
        self._total_orbs = len(layout.orbs)
        self._counters: Dict[Coord, int] = {}
        self._entities: Dict[str, Set[Coord]] = {kind: set() for kind in TILE_DYNAMIC_KINDS}
        self._overlays: Dict[Coord, str] = {}
        self._init_counters()
        self._entities = self._scan_entities()

    def iter_cells(self) -> Iterable[Tuple[int, int, str]]:
        for r, row_values in enumerate(self.grid):
            for c, symbol in enumerate(row_values):
                yield r, c, symbol

    def positions(self, entity_name: str, include_overlays: bool = False):
        if entity_name == "goal":
            return frozenset(self._static_goals)
        if entity_name == "orb":
            return frozenset(self._orbs)
        base = set(self._entities.get(entity_name, set()))
        if include_overlays:
            base.update(
                pos
                for pos, symbol in self._overlays.items()
                if TILE_SYMBOL_TO_KIND.get(symbol) == entity_name
            )
        return frozenset(base)

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
        return self.positions("aqua", include_overlays=True)

    @property
    def box_positions(self):
        return self.positions("box")

    def is_goal_cell(self, r, c):
        return (r, c) in self._static_goals

    @property
    def orbs_remaining(self) -> int:
        return len(self._orbs)

    @property
    def orbs_total(self) -> int:
        return self._total_orbs

    def has_orb(self, pos: Coord) -> bool:
        return pos in self._orbs

    def collect_orb(self, pos: Coord) -> bool:
        if pos in self._orbs:
            self._orbs.remove(pos)
            self.set(*pos, ".")
            return True
        return False

    def _scan_entities(self):
        found: Dict[str, Set[Coord]] = {kind: set() for kind in TILE_DYNAMIC_KINDS}
        for r, c, symbol in self.iter_cells():
            kind = TILE_SYMBOL_TO_KIND.get(symbol)
            if kind in TILE_DYNAMIC_KINDS:
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

    def overlay_symbol(self, r, c):
        return self._overlays.get((r, c))

    def overlay_kind(self, r, c):
        symbol = self.overlay_symbol(r, c)
        if symbol is None:
            return None
        return TILE_SYMBOL_TO_KIND.get(symbol)

    def add_overlay(self, kind, pos):
        if kind not in TILE_DYNAMIC_KINDS:
            raise ValueError(f"add_overlay: unsupported kind '{kind}'")
        symbol = TILE_KIND_TO_SYMBOL[kind]
        self._overlays[pos] = symbol

    def set(self, r, c, val, *, preserve_symbol: str | None = None):
        if not self.in_bounds(r, c):
            raise ValueError(f"set: out of bounds {(r, c)}")

        if val == ".":
            overlay_symbol = self._overlays.pop((r, c), None)
            if overlay_symbol:
                val = overlay_symbol
            else:
                val = self._base[r][c]
        else:
            if preserve_symbol:
                self._overlays[(r, c)] = preserve_symbol
            else:
                self._overlays.pop((r, c), None)

        old_symbol = self.grid[r][c]
        if old_symbol == val and not self._symbol_is_counter(val):
            return

        if val == "W":
            self._base[r][c] = "W"

        self.grid[r][c] = val

        if self._symbol_is_counter(old_symbol):
            self._counters.pop((r, c), None)

        preserve_same_symbol = preserve_symbol == old_symbol
        if old_symbol == "O" and not preserve_same_symbol:
            self._orbs.discard((r, c))

        old_kind = TILE_SYMBOL_TO_KIND.get(old_symbol)
        if old_kind in self._entities:
            self._entities[old_kind].discard((r, c))

        new_kind = TILE_SYMBOL_TO_KIND.get(val)
        if new_kind in self._entities:
            self._entities[new_kind].add((r, c))

    def neighbors4(self, r, c) -> List[Coord]:
        neighbors: List[Coord] = []
        for dr, dc in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def update_entity(self, kind, old_pos, new_pos, *, preserve_symbol: str | None = None):
        if kind not in TILE_DYNAMIC_KINDS:
            raise ValueError(f"update_entity: unsupported kind '{kind}'")

        olr, olc = old_pos
        nr, nc = new_pos
        if not (self.in_bounds(olr, olc) and self.in_bounds(nr, nc)):
            raise ValueError(f"update_entity {kind}: out of bounds")

        symbol = TILE_KIND_TO_SYMBOL[kind]
        self.set(olr, olc, ".")
        self.set(nr, nc, symbol, preserve_symbol=preserve_symbol)

    def add_entity(self, kind, pos):
        if kind not in TILE_DYNAMIC_KINDS:
            raise ValueError(f"add_entity: unsupported kind '{kind}'")
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"add_entity {kind}: out of bounds {pos}")
        symbol = TILE_KIND_TO_SYMBOL[kind]
        self.set(r, c, symbol)

    def remove_entity(self, kind, pos):
        if kind not in TILE_DYNAMIC_KINDS:
            raise ValueError(f"remove_entity: unsupported kind '{kind}'")
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"remove_entity {kind}: out of bounds {pos}")
        overlay_symbol = self._overlays.get((r, c))
        if overlay_symbol and TILE_SYMBOL_TO_KIND.get(overlay_symbol) == kind:
            self._overlays.pop((r, c), None)
            return
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

    DYNAMIC_KINDS = TILE_DYNAMIC_KINDS
    KIND_TO_SYMBOL = TILE_KIND_TO_SYMBOL
    SYMBOL_TO_KIND = TILE_SYMBOL_TO_KIND

    def __init__(self, layout: LevelLayout, state: BoardState | None = None):
        self.layout = layout
        self.state = state or BoardState(layout)

    def __getattr__(self, item):
        # Delegate stateful behavior to BoardState so existing call sites keep working.
        if item == "state":
            raise AttributeError
        return getattr(self.state, item)

    def add_overlay(self, kind, pos):
        return self.state.add_overlay(kind, pos)

    @property
    def orbs_remaining(self):
        return self.state.orbs_remaining

    @property
    def orbs_total(self):
        return self.state.orbs_total
