from src.factory import GameFactory
from src.renderer import play_with_renderer
from src.session import GameSession

def print_board(board):
    for r, row in enumerate(board.grid):
        display_row = []
        for c, symbol in enumerate(row):
            display_symbol = "O" if board.has_orb((r, c)) else symbol
            display_row.append(display_symbol)
        print(" ".join(display_row))
    print()

def game_loop(session: GameSession):
    board = session.board

    print_board(board)
    print("Controls: W/A/S/D to move, Q to quit.\n")

    while True:
        try:
            cmd = input("Move (W/A/S/D/R or Q): ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if cmd == "Q":
            print("bye!")
            break
        elif cmd == "R":
            print("initial board.")
            session.reset()
            board = session.board
            print_board(board)
            continue
        elif cmd not in ("W","A","S","D"):
            print("invalid key.")
            continue
        

        outcome = session.step(cmd).result
        board = session.board

        if outcome.status == "blocked":
            print(f"blocked: {outcome.reason or 'unknown'}")
            print_board(board)
            continue
        
        if outcome.status == "win":
            print_board(board)
            print("YOU WIN!")
            break

        if outcome.status == "lose":
            print_board(board)
            print(f"YOU LOSE! ({outcome.reason or 'move failed'})")
            break

        print_board(board)

def main():
    try:
        level = int(input("please write the level you need to play: ").strip())
    except ValueError:
        print("invalid level number.")
        return

    use_renderer = input("Run with Pygame renderer? (y/N): ").strip().lower() == "y"
    factory = GameFactory()
    if use_renderer:
        play_with_renderer(level, factory)
    else:
        session = GameSession(factory, level)
        game_loop(session)



if __name__ == '__main__':
    main()
