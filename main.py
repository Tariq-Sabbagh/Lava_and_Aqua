from src.factory import GameFactory

def print_board(grid):
    for row in grid:
        print(" ".join(row))
    print()

def game_loop(ctx):
    board = ctx.board
    rules = ctx.rules

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

        mv = rules.apply_move(cmd)
        if mv.status == "blocked":
            print(f"blocked: {mv.reason or 'unknown'}")
            print_board(board.grid)
            continue
        
        if mv.status == "win":
            print_board(board.grid)
            print("YOU WIN!")
            break

        if mv.status == "lose":
            print_board(board.grid)
            print(f"YOU LOSE! ({mv.reason or 'move failed'})")
            break

        lava = rules.apply_spread("lava")
        if lava.status == "lose":
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

    factory = GameFactory()
    ctx = factory.create(level)
    game_loop(ctx)



if __name__ == '__main__':
    main()
