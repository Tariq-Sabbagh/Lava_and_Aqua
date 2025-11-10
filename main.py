from src.Board import Board


global board_info

def print_board(grid):
    for row in grid:
        for col in grid[row]:
            print(grid[row][col])
        print("\n")
    
def main():
    level = int(input("please write the level you need to play"))
    board = Board(level)

    board_info = {
        "grid": board.grid,
        "rows": board.row,
        "cols": board.col,
    }

    rows = board_info["rows"]
    cols = board_info["cols"]
    print_board(board_info["grid"])

if __name__ == '__main__':
    main()