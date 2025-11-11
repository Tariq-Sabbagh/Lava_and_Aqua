from src.Board import Board

class Rules:
    def __init__(self, board):
        self.board = board  

    @property
    def grid(self):
        return self.board.grid

    @property
    def rows(self):
        return self.board.row

    @property
    def cols(self):
        return self.board.col


    def is_goal(self , r , c): return self.grid[r][c] == "G"
