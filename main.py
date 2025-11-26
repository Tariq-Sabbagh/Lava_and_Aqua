import time

import pygame # type: ignore

from src.factory import GameFactory
from src.renderer import GameRenderer, play_with_renderer
from src.solver import BFSSolver, DFSSolver
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
    print("Controls: W/A/S/D to move, U to undo, Q to quit.\n")

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
        elif cmd not in ("W","A","S","D","U"):
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

    mode = input("Play yourself or let solver? (p = play / a = auto): ").strip().lower()
    solver_kind = "bfs"
    use_renderer = False
    if mode == "p":
        use_renderer = input("Run with Pygame renderer? (y/N): ").strip().lower() == "y"
    factory = GameFactory()
    if mode == "a":
        solver_choice = input("Choose solver (b = BFS / d = DFS): ").strip().lower()
        solver_kind = "dfs" if solver_choice == "d" else "bfs"
        solver = DFSSolver(factory, level) if solver_kind == "dfs" else BFSSolver(factory, level)
        auto_renderer = input("Show solver in Pygame? (y/N): ").strip().lower() == "y"
        solution = solver.solve()
        if solution is None:
            print(f"No solution found with {solver_kind.upper()}.")
            return
        label = solver_kind.upper()
        print(
            f"{label} found a solution in {len(solution.moves)} moves "
            f"(attempts: {solution.attempts}, visited: {solution.visited}, solve time: {solution.solve_time:.2f}s)."
        )
        print(" -> ".join(solution.moves))
        session = GameSession(factory, level)
        if auto_renderer:
            renderer = GameRenderer(session.board)
            start_time = time.time()
            total_moves = len(solution.moves)
            renderer.render_with_overlay(
                [
                    f"Solver: {label}",
                    f"Moves: 0/{total_moves}",
                    f"Attempts: {solution.attempts}",
                    f"Visited: {solution.visited}",
                    f"Solved in: {solution.solve_time:.2f}s",
                    f"Elapsed: 0.00s",
                ]
            )
            final_status = "ok"
            for idx, move in enumerate(solution.moves, start=1):
                outcome = session.step(move).result
                data = outcome.data or {}
                elapsed = time.time() - start_time
                renderer.render_with_overlay(
                    [
                        f"Solver: {label}",
                        f"Moves: {idx}/{total_moves}",
                        f"Attempts: {solution.attempts}",
                        f"Visited: {solution.visited}",
                        f"Solved in: {solution.solve_time:.2f}s",
                        f"Elapsed: {elapsed:.2f}s",
                        f"Step {idx}/{len(solution.moves)}: {move}",
                    ]
                )
                if data.get("from") and data.get("to"):
                    renderer.animate_move(data["from"], data["to"])
                else:
                    renderer.render_with_overlay(
                    [
                        f"Solver: {label}",
                        f"Moves: {idx}/{total_moves}",
                        f"Attempts: {solution.attempts}",
                        f"Visited: {solution.visited}",
                        f"Solved in: {solution.solve_time:.2f}s",
                        f"Elapsed: {elapsed:.2f}s",
                        f"Step {idx}/{len(solution.moves)}: {move}",
                    ]
                )
                if outcome.status in ("win", "lose"):
                    final_status = outcome.status
                    break
            elapsed = time.time() - start_time
            final_lines = [
                f"Solver: {label}",
                f"Attempts: {solution.attempts}",
                f"Visited: {solution.visited}",
                f"Moves: {len(solution.moves)}/{total_moves}",
                f"Solved in: {solution.solve_time:.2f}s",
                f"Elapsed: {elapsed:.2f}s",
                f"Finished with status: {final_status}",
            ]
            renderer.render_with_overlay(final_lines)
            if final_status == "win":
                display_for = 180  # seconds
                end_start = time.time()
                while time.time() - end_start < display_for:
                    remaining = int(display_for - (time.time() - end_start))
                    renderer.render_with_overlay(final_lines + [f"Closing in: {remaining}s"])
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            display_for = 0
                            break
                    renderer.tick()
            renderer.close()
        else:
            for move in solution.moves:
                outcome = session.step(move).result
                print(f"Move {move}: {outcome.status}")
                print_board(session.board)
                if outcome.status in ("win", "lose"):
                    break
        return
    if use_renderer:
        play_with_renderer(level, factory)
    else:
        session = GameSession(factory, level)
        game_loop(session)



if __name__ == '__main__':
    main()
