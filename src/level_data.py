"""Level loading and immutable layout definitions for Lava & Aqua."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, List, Tuple

Coord = Tuple[int, int]


@dataclass(frozen=True)
class LevelLayout:
    """Immutable description of a parsed level file."""

    number: int
    rows: int
    cols: int
    raw_grid: Tuple[Tuple[str, ...], ...]
    base_grid: Tuple[Tuple[str, ...], ...]
    static_goals: frozenset[Coord]
    orbs: frozenset[Coord]

    def grid_copy(self) -> List[List[str]]:
        """Return a mutable copy of the raw grid values."""
        return [list(row) for row in self.raw_grid]

    def base_copy(self) -> List[List[str]]:
        """Return a mutable copy of the base terrain grid."""
        return [list(row) for row in self.base_grid]


class LevelRepository:
    """Loads JSON level definitions and produces LevelLayout objects."""

    def __init__(self, base_dir: str = "levels"):
        self.base_dir = base_dir

    def load(self, level_number: int) -> LevelLayout:
        filename = f"level_{level_number}.json"
        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing level file: {filepath}")

        with open(filepath, "r", encoding="utf-8") as fp:
            level_data = json.load(fp)

        board = level_data.get("board")
        if not isinstance(board, list):
            raise ValueError(f"Level {level_number} has no 'board' definition")

        grid_rows = [list(row) for row in board]
        if not grid_rows or not grid_rows[0]:
            raise ValueError(f"Level {level_number} has an empty board")

        rows = len(grid_rows)
        cols = len(grid_rows[0])
        if any(len(row) != cols for row in grid_rows):
            raise ValueError(f"Level {level_number} has inconsistent row lengths")

        base_grid, orbs = self._build_base_grid(grid_rows)
        static_goals = frozenset(
            (r, c)
            for r, row in enumerate(base_grid)
            for c, value in enumerate(row)
            if value == "G"
        )

        return LevelLayout(
            number=level_number,
            rows=rows,
            cols=cols,
            raw_grid=tuple(tuple(cell for cell in row) for row in grid_rows),
            base_grid=tuple(tuple(cell for cell in row) for row in base_grid),
            static_goals=static_goals,
            orbs=frozenset(orbs),
        )

    def _build_base_grid(self, grid_rows: Iterable[Iterable[str]]) -> Tuple[List[List[str]], List[Coord]]:
        base: List[List[str]] = []
        orbs: List[Coord] = []
        for r, row in enumerate(grid_rows):
            base_row: List[str] = []
            for c, symbol in enumerate(row):
                if symbol == "W":
                    base_row.append("W")
                elif symbol == "G":
                    base_row.append("G")
                elif symbol == "O":
                    base_row.append(".")
                    orbs.append((r, c))
                else:
                    base_row.append(".")
            base.append(base_row)
        return base, orbs
