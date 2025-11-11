from src.Board import Board
from src.Rules import Rules

class Actions:
    def __init__(self , board):
        self.board = board
        self.key_to_delta = {
            "W": (-1, 0),  # up
            "A": (0, -1),  # left
            "S": (1, 0),   # down
            "D": (0, 1),   # right
        }
        

    def player_move(self , key):
        (r, c) = next(iter(self.board.player_positions))
        dr , dc = self.key_to_delta.get(key.upper(),(0,0))
        nr , nc = r + dr , c + dc
        
        if not self.board.in_bounds(nr, nc) or self.board.is_wall(nr , nc):
            print("blocked: out of bounds | blocked: wall")
            return False
        
        self.spread("lava")
        target = self.board.get(nr, nc)
        

        self.board.update_entity("player", (r, c), (nr, nc))
        self.player_pos = (nr, nc)
        return True

    def spread(self , kind):
        if kind not in ("lava", "aqua"):
            raise ValueError(f"spread: unknown kind '{kind}'")
        
        sources = self.board.lava_positions if kind == "lava" else self.board.aqua_positions

        current = set(sources)
        new_cells = set()

        for r , c in current:
            for nr, nc in self.board.getNeighbors(r, c):
                if self.board.is_wall(nr, nc):
                    continue
                if self.board.get(nr, nc) == ".":    
                    new_cells.add((nr, nc))

        for pos in new_cells:
            self.board.add_entity("lava", pos)
        
        player_hit = any(pos in self.board.player_positions for pos in new_cells)
        return {"added": len(new_cells), "player_hit": player_hit}
