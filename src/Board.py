import json
import os
from collections import defaultdict
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

        self._entities: Dict[str, Set[Coord]] = self._scan_entities()
        for kind in self.SYMBOL_MAP:
            self._entities.setdefault(kind, set())

    def iter_cells(self) -> Iterable[Tuple[int, int, str]]:
        for r, row_values in enumerate(self.grid):
            for c, symbol in enumerate(row_values):
                yield r, c, symbol

    def positions(self, entity_name: str):
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

    def _scan_entities(self):
        found: Dict[str, Set[Coord]] = defaultdict(set)
        for r, c, symbol in self.iter_cells():
            kind = self.SYMBOL_TO_KIND.get(symbol)
            if kind:
                found[kind].add((r, c))
        return {name: set(positions) for name, positions in found.items()}

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
    
    def set(self, r, c, val):
        if not self.in_bounds(r, c):
            raise ValueError(f"set: out of bounds {(r, c)}")
        old_symbol = self.grid[r][c]
        if old_symbol == val:
            return
        self.grid[r][c] = val

        old_kind = self.SYMBOL_TO_KIND.get(old_symbol)
        if old_kind:
            self._entities.setdefault(old_kind, set()).discard((r, c))

        new_kind = self.SYMBOL_TO_KIND.get(val)
        if new_kind:
            self._entities.setdefault(new_kind, set()).add((r, c))

    def neighbors4(self, r, c) -> List[Coord]:
        neighbors: List[Coord] = []
        for dr, dc in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def update_entity(self, kind, old_pos, new_pos):
        olr, olc = old_pos
        nr, nc = new_pos
        if not (self.in_bounds(olr, olc) and self.in_bounds(nr, nc)):
            raise ValueError(f"update_entity {kind}: out of bounds")

        symbol = self.KIND_TO_SYMBOL[kind]
        self.set(olr, olc, ".")
        self.set(nr, nc, symbol)

    def add_entity(self, kind, pos):
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"add_entity {kind}: out of bounds {pos}")
        symbol = self.KIND_TO_SYMBOL[kind]
        self.set(r, c, symbol)

    def remove_entity(self, kind, pos):
        r, c = pos
        if not self.in_bounds(r, c):
            raise ValueError(f"remove_entity {kind}: out of bounds {pos}")
        self.set(r, c, ".")
        
    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_wall(self, r, c):
        return self.grid[r][c] == "W"
