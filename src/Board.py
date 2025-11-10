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
        return list(self.entities.get(entity_name, []))

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

    def getBoaed(self):
        return self.grid