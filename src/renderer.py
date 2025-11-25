import time
from dataclasses import dataclass
from typing import Tuple

try:
    import pygame # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - pygame optional in tests
    raise RuntimeError(
        "pygame is required for the graphical renderer. "
        "Install it via `pip install pygame` before using GameRenderer."
    ) from exc

from src.Board import Board
from src.session import GameSession

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class TileTheme:
    fill: Color
    border: Color


class GameRenderer:

    DEFAULT_THEME = {
        ".": TileTheme((30, 30, 30), (45, 45, 45)),
        "W": TileTheme((70, 70, 70), (110, 110, 110)),
        "P": TileTheme((60, 140, 255), (255, 255, 255)),
        "G": TileTheme((70, 200, 120), (255, 255, 255)),
        "L": TileTheme((220, 80, 30), (255, 160, 120)),
        "A": TileTheme((40, 180, 220), (120, 230, 255)),
        "B": TileTheme((200, 170, 90), (255, 220, 120)),
        "O": TileTheme((255, 215, 0), (255, 255, 255)),
    }

    COUNTER_THEME = TileTheme((90, 75, 160), (150, 130, 210))

    def __init__(self, board: Board, cell_size: int = 48, fps: int = 60):
        self.board = board
        self.cell_size = cell_size
        self.fps = fps

        pygame.init()
        pygame.font.init()

        self.width = board.cols * cell_size
        self.height = board.rows * cell_size
        self.display = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Lava & Aqua")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", cell_size // 2, bold=True)

    # ------------------------------------------------------------------ Drawing

    def draw_board(self) -> None:
        for r, row in enumerate(self.board.grid):
            for c, symbol in enumerate(row):
                rect = pygame.Rect(
                    c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size
                )
                has_orb = self.board.has_orb((r, c))

                base_symbol = symbol
                if symbol == "O":
                    base_symbol = self.board.cell_base(r, c)

                theme = self._theme_for_symbol(base_symbol)
                pygame.draw.rect(self.display, theme.fill, rect)
                pygame.draw.rect(self.display, theme.border, rect, width=2)

                if symbol.isdigit():
                    self._draw_counter_value(symbol, rect)
                if has_orb:
                    self._draw_orb(rect)

        pygame.display.flip()

    def _draw_counter_value(self, value: str, rect: pygame.Rect) -> None:
        text = self.font.render(value, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        self.display.blit(text, text_rect)

    def _draw_orb(self, rect: pygame.Rect) -> None:
        center = rect.center
        theme = self.DEFAULT_THEME["O"]
        outer_radius = self.cell_size * 0.22
        inner_radius = outer_radius * 0.6
        pygame.draw.circle(self.display, theme.border, center, outer_radius)
        pygame.draw.circle(self.display, theme.fill, center, inner_radius)

    def _theme_for_symbol(self, symbol: str) -> TileTheme:
        if symbol.isdigit():
            return self.COUNTER_THEME
        return self.DEFAULT_THEME.get(symbol, self.DEFAULT_THEME["."])

    # ----------------------------------------------------------- Input helpers

    def next_command(self) -> str | None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Q"
            if event.type == pygame.KEYDOWN:
                keymap = {
                    pygame.K_w: "W",
                    pygame.K_s: "S",
                    pygame.K_a: "A",
                    pygame.K_d: "D",
                    pygame.K_u: "U",
                    pygame.K_UP: "W",
                    pygame.K_DOWN: "S",
                    pygame.K_LEFT: "A",
                    pygame.K_RIGHT: "D",
                    pygame.K_ESCAPE: "Q",
                    pygame.K_r: "R"
                    
                }
                return keymap.get(event.key)
        return None

    # ------------------------------------------------------------- Animations

    def animate_move(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        symbol: str = "P",
        duration_ms: int = 150,
    ) -> None:
        start_px = self._cell_center(start)
        end_px = self._cell_center(end)
        duration = max(duration_ms / 1000.0, 0.01)
        elapsed = 0.0

        while elapsed < duration:
            t = elapsed / duration
            pos = (
                start_px[0] + (end_px[0] - start_px[0]) * t,
                start_px[1] + (end_px[1] - start_px[1]) * t,
            )
            self.draw_board()
            self._draw_symbol_at(symbol, pos)
            pygame.display.flip()
            dt = self.clock.tick(self.fps) / 1000.0
            elapsed += dt

        # final frame
        self.draw_board()

    def _cell_center(self, coord: Tuple[int, int]) -> Tuple[float, float]:
        r, c = coord
        return (
            c * self.cell_size + self.cell_size / 2,
            r * self.cell_size + self.cell_size / 2,
        )

    def _draw_symbol_at(self, symbol: str, pos: Tuple[float, float]) -> None:
        radius = self.cell_size * 0.35
        theme = self._theme_for_symbol(symbol)
        pygame.draw.circle(self.display, theme.fill, pos, radius)
        pygame.draw.circle(self.display, theme.border, pos, radius, width=3)

    # ---------------------------------------------------------------- Utility

    def tick(self) -> None:
        self.clock.tick(self.fps)

    def close(self) -> None:
        pygame.quit()


def play_with_renderer(level: int, factory) -> None:
    session = GameSession(factory, level)
    renderer = GameRenderer(session.board)
    try:
        running = True
        while running:
            renderer.draw_board()
            cmd = renderer.next_command()
            if cmd is None:
                renderer.tick()
                continue
            if cmd == "Q":
                running = False
                continue
            if cmd == "R":
                session.reset()
                renderer = GameRenderer(session.board)
                continue
            outcome = session.step(cmd).result
            if outcome.status == "blocked":
                print(f"blocked: {outcome.reason or 'unknown'}")
                renderer.draw_board()
                continue
            elif outcome.status == "ok":
                data = outcome.data or {}
                if data.get("from") and data.get("to"):
                    renderer.animate_move(data["from"], data["to"])
            elif outcome.status == "undo":
                renderer.draw_board()
                continue
            elif outcome.status in ("win", "lose"):
                renderer.draw_board()
                time.sleep(1.5)
                running = False
                continue
    finally:
        renderer.close()
