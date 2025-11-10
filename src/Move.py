from src.Board import Board

class Move:
    def __init__(self , board):
        x_moves = [0 , 0 , 1 , -1]
        y_moves = [1 , -1 , 0 , 0]
        board_info = {
        "grid": board.grid,
        "rows": board.row,
        "cols": board.col,
        }

        player_pos = board.player_positions


    def player_move(self , key):
        if key == "A":
            if self.is_wall():
                pass
            else:
                self.player_pos + self.y_moves[1]
                

            

    def is_wall(self , r , c):
        if self.grid[r][c] == "W":
            return False
        return True