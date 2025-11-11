import json
import os
from collections import defaultdict


class Board:
    SYMBOL_MAP = {
        "player": {"P"},
        "goal": {"G"},
        "lava": {"L"},
        "aqua": {"A"},
        "box": {"B"},
    }

    def __init__(self, level_number, base_dir="levels"):
        self.level_number = level_number
        self.base_dir = base_dir
        self.grid = self._load_grid()
        self.row = len(self.grid)
        self.col = len(self.grid[0]) if self.grid else 0


        self.entities = self._scan_entities()
        self.player_positions = self.entities.get("player", set())
        self.goal_positions = self.entities.get("goal", set())
        self.lava_positions = self.entities.get("lava", set())
        self.aqua_positions = self.entities.get("aqua", set())
        self.box_positions = self.entities.get("box", set())

    def iter_cells(self):
        for r, row_values in enumerate(self.grid):
            for c, symbol in enumerate(row_values):
                yield r, c, symbol


    def get_positions(self, entity_name):
        return set(self.entities.get(entity_name, []))

    def _scan_entities(self):
        found = defaultdict(set)
        for r, c, symbol in self.iter_cells():
            for entity, symbols in self.SYMBOL_MAP.items():
                if symbol in symbols:
                    found[entity].add((r, c))
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
    
    def get(self , r , c):
        return self.grid[r][c]
    
    def set (self , r , c , val):
        self.grid[r][c]= val

    def getBoard(self):
        return self.grid
    
    def getNeighbors(self , r , c):
        for dr, dc in ((-1,0),(1,0),(0,1),(0,-1)):
            nr, nc = r+dr, c+dc
            if self.in_bounds(nr, nc):
                yield (nr, nc)

    def update_entity(self, kind, old_pos, new_pos):
        olr, olc = old_pos
        nr, nc = new_pos
        if not (self.in_bounds(olr,olc) and self.in_bounds(nr,nc)):
            raise ValueError(f"update_entity {kind}: out of bounds")

        if self.grid[olr][olc] == "P": self.grid[olr][olc] = "."
        elif self.grid[olr][olc] in ("L","A","B"): self.grid[olr][olc] = "."

        symbol = {"player":"P","goal":"G","lava":"L","aqua":"A","box":"B"}[kind]
        self.grid[nr][nc] = symbol

        if kind == "player":
            self.player_positions.discard(old_pos)
            self.player_positions.add(new_pos)
        elif kind == "lava":
            self.lava_positions.discard(old_pos)
            self.lava_positions.add(new_pos)
        elif kind == "aqua":
            self.aqua_positions.discard(old_pos)
            self.aqua_positions.add(new_pos)
        elif kind == "box":
            self.box_positions.discard(old_pos)
            self.box_positions.add(new_pos)

    def add_entity(self, kind, pos):
        r, c = pos
        if not self.in_bounds(r,c): 
            raise ValueError(f"add_entity {kind}: out of bounds {pos}")
        symbol = {"player":"P","goal":"G","lava":"L","aqua":"A","box":"B"}[kind]
        self.grid[r][c] = symbol
        if kind == "player": self.player_positions.add(pos)
        elif kind == "lava": self.lava_positions.add(pos)
        elif kind == "aqua": self.aqua_positions.add(pos)
        elif kind == "box": self.box_positions.add(pos)

    def remove_entity(self, kind, pos):
        r, c = pos
        if not self.in_bounds(r,c): 
            raise ValueError(f"remove_entity {kind}: out of bounds {pos}")
        self.grid[r][c] = "."
        if kind == "player": self.player_positions.discard(pos)
        elif kind == "lava": self.lava_positions.discard(pos)
        elif kind == "aqua": self.aqua_positions.discard(pos)
        elif kind == "box": self.box_positions.discard(pos)
        
    
    def in_bounds(self, r, c): return 0 <= r < self.row and 0 <= c < self.col
    def is_wall(self, r, c): return self.grid[r][c] == "W"