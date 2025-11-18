from src.result import Result
from src.tiles import (
    BOX_PUSH_RULES,
    KIND_TO_SYMBOL,
    SPREAD_RULES,
    SYMBOL_TO_KIND,
)


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
                tile_symbol = self.board.get(nr, nc)
                if tile_symbol.isdigit():
                    continue

                tile_kind = SYMBOL_TO_KIND.get(tile_symbol)
                if tile_kind is None:
                    continue

                effect = SPREAD_RULES.get((kind, tile_kind))
                if effect is None:
                    continue

                if effect.hits_player:
                    hits_player = True

                if effect.convert_to_kind:
                    convert_symbol = KIND_TO_SYMBOL[effect.convert_to_kind]
                    self.board.set(nr, nc, convert_symbol)
                    if effect.convert_to_kind == "wall":
                        new_walls.add((nr, nc))

                if effect.spawn:
                    new_cells.add((nr, nc))

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

        tile_symbol = self.board.get(*dest)
        if tile_symbol.isdigit():
            return Result(ok=False, status="blocked", reason="box_blocked")

        tile_kind = SYMBOL_TO_KIND.get(tile_symbol)
        interaction = BOX_PUSH_RULES.get(tile_kind)
        if interaction is None or not interaction.allowed:
            reason = "box_blocked" if tile_symbol in ("W", "B") else f"box_hits_{tile_symbol}"
            return Result(ok=False, status="blocked", reason=reason)

        neutralized_lava = False
        neutralized_aqua = False
        if interaction.removes_kind:
            self.board.remove_entity(interaction.removes_kind, dest)
            neutralized_lava = interaction.removes_kind == "lava"
            neutralized_aqua = interaction.removes_kind == "aqua"

        self.board.update_entity("box", box_pos, dest)
        return Result(
            ok=True,
            status="ok",
            data={
                "from": box_pos,
                "to": dest,
                "neutralized_lava": neutralized_lava,
                "neutralized_aqua": neutralized_aqua,
            },
        )

    def tick_counters(self):
        return self.board.tick_counters()
