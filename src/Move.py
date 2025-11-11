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
        push_info = None
        if target == "B":
            push_result = self._push_box((nr, nc), (dr, dc))
            if not push_result.ok:
                return push_result
            push_info = push_result.data or {}

        landed_goal = self.board.is_goal_cell(nr, nc)
        self.board.update_entity("player", start, (nr, nc))
        return Result(
            ok=True,
            status="ok",
            data={
                "from": start,
                "to": (nr, nc),
                "target": target,
                "on_goal": landed_goal,
                "push": push_info,
            },
        )

    def spread(self, kind):
        if kind not in ("lava", "aqua"):
            return Result(ok=False, status="blocked", reason=f"unknown_{kind}")

        sources = (
            self.board.lava_positions if kind == "lava" else self.board.aqua_positions
        )
        new_cells = set()
        hits_player = False
        new_walls = set()

        for r, c in sources:
            for nr, nc in self.board.neighbors4(r, c):
                tile = self.board.get(nr, nc)
                if tile == "W":
                    continue
                if tile == ".":
                    new_cells.add((nr, nc))
                    continue
                if tile == "P":
                    if kind == "lava":
                        hits_player = True
                    continue
                if kind == "aqua" and tile == "L":
                    self.board.set(nr, nc, "W")
                    new_walls.add((nr, nc))
                    continue
                if kind == "lava" and tile == "A":
                    self.board.set(nr, nc, "W")
                    new_walls.add((nr, nc))
                    continue

        for pos in new_cells:
            self.board.add_entity(kind, pos)

        return Result(
            ok=True,
            status="ok",
            data={
                "new_cells": frozenset(new_cells),
                "hits_player": hits_player,
                "new_walls": frozenset(new_walls),
            },
        )

    def _push_box(self, box_pos, delta):
        br, bc = box_pos
        dr, dc = delta
        dest = (br + dr, bc + dc)

        if not self.board.in_bounds(*dest):
            return Result(ok=False, status="blocked", reason="box_out_of_bounds")

        tile = self.board.get(*dest)
        if tile in ("W", "B"):
            return Result(ok=False, status="blocked", reason="box_blocked")

        neutralized = False
        if tile == "L":
            self.board.remove_entity("lava", dest)
            neutralized = True
        elif tile not in (".", "G"):
            return Result(ok=False, status="blocked", reason=f"box_hits_{tile}")

        self.board.update_entity("box", box_pos, dest)
        return Result(
            ok=True,
            status="ok",
            data={"from": box_pos, "to": dest, "neutralized_lava": neutralized},
        )
