from src.Board import Board
from src.Move import Actions
from src.Rules import Rules

def print_board(grid):
    for row in grid:
        print(" ".join(row))
    print()

def test(board):
    m = Actions(board)
    # print_board(board.grid)
    # print(f"Player positions: {board.player_positions or 'not found'}")
    m.player_move("A")
    print_board(board.grid)
    # print(f"Player positions: {board.player_positions or 'not found'}")
    m.player_move("W")
    print_board(board.grid)
    # print(f"Player positions: {board.player_positions or 'not found'}")
    m.player_move("W")
    print_board(board.grid)
    # print(f"Player positions: {board.player_positions or 'not found'}")
    # print(f"Goal positions: {board.goal_positions or 'not found'}")
    # print(f"Lava cells: {board.lava_positions or 'none'}")
    # print(f"Aqua cells: {board.aqua_positions or 'none'}")
    # print(f"Box cells: {board.box_positions or 'none'}")

def game_loop(board):
    actions = Actions(board)
    rules = Rules(board)
    print_board(board.grid)
    print("Controls: W/A/S/D to move, Q to quit.\n")

    while True:
        try:
            cmd = input("Move (W/A/S/D or Q): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if cmd == "Q":
            print("bye!")
            break
        if cmd not in ("W","A","S","D"):
            print("invalid key.")
            continue

        mv = rules.apply_move(actions, cmd)
        if mv["status"] == "blocked":
            print(f"blocked: {mv.get('reason', 'unknown')}")
            print_board(board.grid)
            continue
        
        if mv["status"] == "win":
            print_board(board.grid)
            print("YOU WIN!")
            break

        if mv["status"] == "lose":
            print_board(board.grid)
            print("YOU LOSE! (stepped into lava)")
            break

        lava = rules.apply_spread(actions, "lava")
        if lava["status"] == "lose":
            print_board(board.grid)
            print("YOU LOSE! (lava spread)")
            break

        print_board(board.grid)

def main():
    try:
        level = int(input("please write the level you need to play: ").strip())
    except ValueError:
        print("invalid level number.")
        return

    board = Board(level)
    game_loop(board)

    

if __name__ == '__main__':
    main()
