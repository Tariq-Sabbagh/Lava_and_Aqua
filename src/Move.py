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


    def player_move(self , key):
        r , c = self.player_pos
        dr , dc = self.mapping.get(key.upper(),(0,0))
        nr , nc = r + dr , c + dc
        
        if not self.in_bounds(nr, nc):
            print("blocked: out of bounds")
            return False
    
        if self.is_wall(nr, nc):
            print("blocked: wall")
            return False
        
        self.grid[r][c] = "."
        self.grid[nr][nc] = "P"
        self.player_pos = (nr, nc)
        self.board.player_positions.remove((r, c))
        self.board.player_positions.add((nr, nc))


            

    def in_bounds(self , r, c): return 0 <= r < self.rows and 0 <= c < self.cols
    def is_wall(self , r, c):   return self.grid[r][c] == "W"
