import json
import os


class Board:
    row, col = 0, 0

    def __init__(self, level_number, base_dir="levels"):
        self.level_number = level_number
        self.base_dir = base_dir
        self.grid = self._load_grid()
        self.row = len(self.grid)
        self.col = len(self.grid[0]) if self.grid else 0

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
