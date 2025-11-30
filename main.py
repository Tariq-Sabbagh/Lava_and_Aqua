import os
import time

import pygame  # type: ignore

from src.factory import GameFactory
from src.renderer import GameRenderer, play_with_renderer
from src.solver import BFSSolver, DFSSolver
from src.session import GameSession
from src.start_menu import MenuSelection, StartMenu

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

def discover_levels(levels_dir: str) -> list[int]:
    levels: list[int] = []
    if not os.path.isdir(levels_dir):
        return levels
    for name in os.listdir(levels_dir):
        if not (name.startswith("level_") and name.endswith(".json")):
            continue
        middle = name[len("level_") : -len(".json")]
        try:
            levels.append(int(middle))
        except ValueError:
            continue
    return sorted(levels)


def run_start_menu(levels: list[int]) -> MenuSelection | None:
    try:
        menu = StartMenu(levels)
    except Exception as exc:
        print(f"Start menu unavailable, using terminal prompts instead. ({exc})")
        return None
    return menu.run()


def prompt_via_terminal(levels: list[int]) -> MenuSelection | None:
    min_level = levels[0] if levels else 1
    max_level = levels[-1] if levels else 1
    try:
        level = int(input(f"Please choose a level ({min_level}-{max_level}): ").strip())
    except ValueError:
        print("invalid level number.")
        return None

    if level < min_level or level > max_level:
        print(f"Level must be between {min_level} and {max_level}.")
        return None

    mode_input = input("Play yourself or let solver? (p = play / a = auto): ").strip().lower()
    mode = "auto" if mode_input == "a" else "player"
    solver_kind = "bfs"
    use_renderer = False

    if mode == "player":
        use_renderer = input("Run with Pygame renderer? (y/N): ").strip().lower() == "y"
    else:
        solver_choice = input("Choose solver (b = BFS / d = DFS): ").strip().lower()
        solver_kind = "dfs" if solver_choice == "d" else "bfs"
        use_renderer = input("Show solver in Pygame? (y/N): ").strip().lower() == "y"

    return MenuSelection(level=level, mode=mode, solver=solver_kind, use_renderer=use_renderer)


def show_solution_with_renderer(session: GameSession, solution, label: str) -> None:
    renderer = GameRenderer(session.board)
    start_time = time.time()
    total_moves = len(solution.moves)

    def overlay(current_idx: int, move_label: str | None = None) -> None:
        elapsed = time.time() - start_time
        lines = [
            f"Solver: {label}",
            f"Moves: {current_idx}/{total_moves}",
            f"Attempts: {solution.attempts}",
            f"Visited: {solution.visited}",
            f"Generated: {solution.generated}",
            f"Solved in: {solution.solve_time:.2f}s",
            f"Elapsed: {elapsed:.2f}s",
        ]
        if move_label:
            lines.append(move_label)
        renderer.render_with_overlay(lines)

    overlay(0)
    final_status = "ok"
    try:
        for idx, move in enumerate(solution.moves, start=1):
            outcome = session.step(move).result
            data = outcome.data or {}
            overlay(idx, f"Step {idx}/{total_moves}: {move}")
            if data.get("from") and data.get("to"):
                renderer.animate_move(data["from"], data["to"])
            if outcome.status in ("win", "lose"):
                final_status = outcome.status
                break

        elapsed = time.time() - start_time
        final_lines = [
            f"Solver: {label}",
            f"Attempts: {solution.attempts}",
            f"Visited: {solution.visited}",
            f"Generated: {solution.generated}",
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
    finally:
        renderer.close()


def run_auto_mode(factory: GameFactory, selection: MenuSelection) -> None:
    solver_cls = DFSSolver if selection.solver == "dfs" else BFSSolver
    solver = solver_cls(factory, selection.level)
    solution = solver.solve()
    label = selection.solver.upper()
    if solution is None:
        print(f"No solution found with {label}.")
        return

    print(
        f"{label} found a solution in {len(solution.moves)} moves "
        f"(attempts: {solution.attempts}, visited: {solution.visited}, generated: {solution.generated}, solve time: {solution.solve_time:.2f}s)."
    )
    print(" -> ".join(solution.moves))

    session = GameSession(factory, selection.level)
    if selection.use_renderer:
        show_solution_with_renderer(session, solution, label)
        return

    for move in solution.moves:
        outcome = session.step(move).result
        print(f"Move {move}: {outcome.status}")
        print_board(session.board)
        if outcome.status in ("win", "lose"):
            break


def run_player_mode(factory: GameFactory, selection: MenuSelection) -> None:
    if selection.use_renderer:
        play_with_renderer(selection.level, factory)
        return
    session = GameSession(factory, selection.level)
    game_loop(session)


def main():
    factory = GameFactory()
    levels = discover_levels(factory.levels_dir)
    selection = run_start_menu(levels)
    if selection is None:
        selection = prompt_via_terminal(levels)
    if selection is None:
        print("No level selected. Exiting.")
        return

    if selection.mode == "auto":
        run_auto_mode(factory, selection)
    else:
        run_player_mode(factory, selection)


if __name__ == '__main__':
    main()
