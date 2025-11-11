from src.Board import Board

class Move:
    def __init__(self , board):
        self.x_moves = [0 , 0 , 1 , -1]
        self.y_moves = [1 , -1 , 0 , 0]
        self.mapping = {
        "W": (-1, 0),  
        "A": (0, -1),  
        "S": (1, 0),   
        "D": (0, 1),   
    }
        self.board = board
        self.grid = board.grid
        self.rows, self.cols = board.row, board.col

        self.player_pos = next(iter(board.player_positions))
        self.lava_pos = board.lava_positions
        # self.lava_pos = next(iter(board.lava_positions))
        


    def player_move(self , key):
        r , c = self.player_pos
        dr , dc = self.mapping.get(key.upper(),(0,0))
        nr , nc = r + dr , c + dc
        
        if not self.board.in_bounds(nr, nc) or self.board.is_wall(nr , nc):
            print("blocked: out of bounds | blocked: wall")
            return False
        self.lava_move()
        target = self.grid[nr][nc]
        if target == "L":
            print("stepped into lava! (mark lose soon)")
        if target == "G":
            print("goal reached! (mark win soon)")

        self.board.update_entity("player", (r, c), (nr, nc))
        self.player_pos = (nr, nc)

    def lava_move(self):
        current = set(self.board.lava_positions)
        # print(current)
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


        


    def is_goal(self , r , c): return self.grid[r][c] == "G"
