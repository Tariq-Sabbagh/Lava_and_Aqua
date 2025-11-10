from src.Board import Board

def print_board(grid):
    for row in grid:
        print(" ".join(row))
    print()
    
def main():
    level = int(input("please write the level you need to play: "))
    board = Board(level)

    board_info = {
        "grid": board.grid,
        "rows": board.row,
        "cols": board.col,
    }

    rows = board_info["rows"]
    cols = board_info["cols"]
    # print_board(board_info["grid"])
    # print(f"Player positions: {board.player_positions or 'not found'}")
    # print(f"Goal positions: {board.goal_positions or 'not found'}")
    # print(f"Lava cells: {board.lava_positions or 'none'}")
    # print(f"Aqua cells: {board.aqua_positions or 'none'}")
    # print(f"Box cells: {board.box_positions or 'none'}")

if __name__ == '__main__':
    main()
