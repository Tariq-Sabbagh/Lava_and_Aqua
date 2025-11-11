from src.result import Result


class Actions:
    """Concrete mutations applied to the board."""

    KEY_TO_DELTA = {
        "W": (-1, 0),  # up
        "A": (0, -1),  # left
        "S": (1, 0),   # down
        "D": (0, 1),   # right
    }

    def __init__(self, board):
        self.board = board

    def player_move(self, key):
        key = key.upper()
        if key not in self.KEY_TO_DELTA:
            return Result(ok=False, status="blocked", reason="invalid_move_key")

        try:
            start = next(iter(self.board.player_positions))
        except StopIteration:
            return Result(ok=False, status="blocked", reason="no_player")

        dr, dc = self.KEY_TO_DELTA[key]
        nr, nc = start[0] + dr, start[1] + dc

        if not self.board.in_bounds(nr, nc):
            return Result(ok=False, status="blocked", reason="out_of_bounds")
        if self.board.is_wall(nr, nc):
            return Result(ok=False, status="blocked", reason="wall")

        target = self.board.get(nr, nc)
        self.board.update_entity("player", start, (nr, nc))
        return Result(
            ok=True,
            status="ok",
            data={"from": start, "to": (nr, nc), "target": target},
        )

    def spread(self, kind):
        if kind not in ("lava", "aqua"):
            return Result(ok=False, status="blocked", reason=f"unknown_{kind}")

        sources = (
            self.board.lava_positions if kind == "lava" else self.board.aqua_positions
        )
        new_cells = set()
        hits_player = False

        for r, c in sources:
            for nr, nc in self.board.neighbors4(r, c):
                tile = self.board.get(nr, nc)
                if tile == ".":
                    new_cells.add((nr, nc))
                elif tile == "P":
                    hits_player = True

        for pos in new_cells:
            self.board.add_entity(kind, pos)

        return Result(
            ok=True,
            status="ok",
            data={"new_cells": frozenset(new_cells), "hits_player": hits_player},
        )
