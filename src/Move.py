class Actions:
    """Handles concrete state mutations on top of a Board instance."""

    KEY_TO_DELTA = {
        "W": (-1, 0),  # up
        "A": (0, -1),  # left
        "S": (1, 0),   # down
        "D": (0, 1),   # right
    }

    def __init__(self, board):
        self.board = board

    def player_move(self, key):
        if not self.board.player_positions:
            return {"ok": False, "status": "blocked", "reason": "no_player"}
    
        (r, c) = next(iter(self.board.player_positions))
        dr, dc = self.KEY_TO_DELTA.get(key.upper(), (0, 0))
        nr, nc = r + dr, c + dc
    
        if not self.board.in_bounds(nr, nc):
            return {"ok": False, "status": "blocked", "reason": "out_of_bounds"}
        if self.board.is_wall(nr, nc):
            return {"ok": False, "status": "blocked", "reason": "wall"}
    
        target = self.board.get(nr, nc)
        self.board.update_entity("player", (r, c), (nr, nc))
        return {"ok": True, "status": "ok", "target": target, "from": (r, c), "to": (nr, nc)}

    def spread(self, kind):
        if kind not in ("lava", "aqua"):
            raise ValueError(f"spread: unknown kind '{kind}'")

        sources = self.board.lava_positions if kind == "lava" else self.board.aqua_positions
        current = set(sources)
        new_cells = set()
        hits_player = False

        for r, c in current:
            for nr, nc in self.board.getNeighbors(r, c):
                if self.board.is_wall(nr, nc):
                    continue
                if self.board.get(nr, nc) == ".":
                    new_cells.add((nr, nc))
                elif self.board.get(nr, nc) == "P":
                    hits_player = True 

        for pos in new_cells:
            self.board.add_entity(kind, pos)

        return {"ok": True, "status": "ok" if not hits_player else "lose",
                "reason": "player_hit" if hits_player else None,
                "effects": {"added": len(new_cells), "new_cells": new_cells}}
