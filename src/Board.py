import json
import os
from typing import Dict, Iterable, List, Set, Tuple

Coord = Tuple[int, int]


class Board:
    SYMBOL_MAP: Dict[str, Set[str]] = {
        "player": {"P"},
        "goal": {"G"},
        "lava": {"L"},
        "aqua": {"A"},
        "box": {"B"},
    }
    DYNAMIC_KINDS = {"player", "lava", "aqua", "box"}
    KIND_TO_SYMBOL = {kind: next(iter(symbols)) for kind, symbols in SYMBOL_MAP.items()}
    SYMBOL_TO_KIND: Dict[str, str] = {
        symbol: kind for kind, symbols in SYMBOL_MAP.items() for symbol in symbols
    }

    def __init__(self, level_number, base_dir="levels"):
        self.level_number = level_number
        self.base_dir = base_dir
        self.grid = self._load_grid()
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.grid else 0

        self._base = self._build_base_grid()
        self._static_goals = {
            (r, c) for r, row in enumerate(self._base) for c, val in enumerate(row) if val == "G"
        }
        self._counters: Dict[Coord, int] = {}
        self._init_counters()
        self._entities: Dict[str, Set[Coord]] = self._scan_entities()

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
        found: Dict[str, Set[Coord]] = {kind: set() for kind in self.DYNAMIC_KINDS}
        for r, c, symbol in self.iter_cells():
            kind = self.SYMBOL_TO_KIND.get(symbol)
            if kind in self.DYNAMIC_KINDS:
                found[kind].add((r, c))
        return found
    
    def _symbol_is_counter(self, symbol: str) -> bool:
        return isinstance(symbol, str) and symbol.isdigit()

    def _init_counters(self):
        for r, row in enumerate(self.grid):
            for c, symbol in enumerate(row):
                if self._symbol_is_counter(symbol):
                    self._counters[(r, c)] = int(symbol)

    def _build_base_grid(self):
        base = []
        for row in self.grid:
            base_row = []
            for symbol in row:
                if symbol == "W":
                    base_row.append("W")
                elif symbol == "G":
                    base_row.append("G")
                else:
                    base_row.append(".")
            base.append(base_row)
        return base

    def _load_grid(self):
        filename = f"level_{self.level_number}.json"
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing level file: {filepath}")

        with open(filepath, "r", encoding="utf-8") as fp:
            level_data = json.load(fp)

        board = level_data.get("board")
        if not isinstance(board, list):
            raise ValueError(f"Level {self.level_number} has no 'board' definition")

        return [list(row) for row in board]
    
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

        old_kind = self.SYMBOL_TO_KIND.get(old_symbol)
        if old_kind in self._entities:
            self._entities[old_kind].discard((r, c))

        new_kind = self.SYMBOL_TO_KIND.get(val)
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
        if kind not in self.DYNAMIC_KINDS:
            raise ValueError(f"update_entity: unsupported kind '{kind}'")

        olr, olc = old_pos
        nr, nc = new_pos
        if not (self.in_bounds(olr, olc) and self.in_bounds(nr, nc)):
            raise ValueError(f"update_entity {kind}: out of bounds")

        symbol = self.KIND_TO_SYMBOL[kind]
        self.set(olr, olc, ".")
        self.set(nr, nc, symbol)

    def add_entity(self, kind, pos):
        if kind not in self.DYNAMIC_KINDS:
            raise ValueError(f"add_entity: unsupported kind '{kind}'")
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"add_entity {kind}: out of bounds {pos}")
        symbol = self.KIND_TO_SYMBOL[kind]
        self.set(r, c, symbol)

    def remove_entity(self, kind, pos):
        if kind not in self.DYNAMIC_KINDS:
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
