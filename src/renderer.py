import random
import time
from dataclasses import dataclass
from typing import Tuple

try:
    import pygame  # type: ignore
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
        "H": TileTheme((30, 30, 30), (45, 45, 45)),
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
        self.small_font = pygame.font.SysFont("consolas", max(12, cell_size // 3))

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
                if symbol == "P":
                    base_symbol = self.board.cell_base(r, c)

                theme = self._theme_for_symbol(base_symbol)
                pygame.draw.rect(self.display, theme.fill, rect)
                pygame.draw.rect(self.display, theme.border, rect, width=2)

                base_is_h = self.board.cell_base(r, c) == "H"
                if symbol.isdigit():
                    self._draw_counter_value(symbol, rect)
                if symbol == "P":
                    self._draw_player(rect)
                if has_orb:
                    self._draw_orb(rect)
                if base_is_h:
                    self._draw_h_tile(rect)

        pygame.display.flip()
        return self.display

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
        if symbol == "P":
            self._draw_player_at(pos)
            return
        radius = self.cell_size * 0.35
        theme = self._theme_for_symbol(symbol)
        pygame.draw.circle(self.display, theme.fill, pos, radius)
        pygame.draw.circle(self.display, theme.border, pos, radius, width=3)

    def _draw_player(self, rect: pygame.Rect) -> None:
        center = rect.center
        size = self.cell_size * 0.7
        self._draw_player_icon(center, size)

    def _draw_player_at(self, pos: Tuple[float, float]) -> None:
        size = self.cell_size * 0.65
        self._draw_player_icon(pos, size)

    def _draw_player_icon(self, center: Tuple[float, float], size: float) -> None:
        body_h = size * 0.9
        body_w = size * 0.55
        surf_w = int(body_w + size * 0.4)
        surf_h = int(body_h + size * 0.6)
        surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)

        body_rect = pygame.Rect(
            int((surf_w - body_w) / 2),
            int(surf_h - body_h - size * 0.12),
            int(body_w),
            int(body_h),
        )
        player_fill = (60, 140, 255)
        player_border = (255, 255, 255)

        pygame.draw.rect(surf, player_fill, body_rect, border_radius=int(body_w / 1.8))
        pygame.draw.rect(surf, player_border, body_rect, width=2, border_radius=int(body_w / 1.8))

        visor_rect = body_rect.inflate(int(-body_w * 0.35), int(-body_h * 0.45))
        visor_rect.y -= int(body_h * 0.18)
        pygame.draw.rect(surf, (255, 255, 255, 230), visor_rect, border_radius=int(visor_rect.width / 2))
        pygame.draw.rect(surf, (120, 200, 255, 230), visor_rect, width=2, border_radius=int(visor_rect.width / 2))

        head_center = (surf_w // 2, int(body_rect.top - size * 0.08))
        head_r = int(size * 0.22)
        pygame.draw.circle(surf, player_fill, head_center, head_r)
        pygame.draw.circle(surf, player_border, head_center, head_r, width=2)

        self.display.blit(surf, (center[0] - surf_w / 2, center[1] - surf_h / 2))

    def _draw_h_tile(self, rect: pygame.Rect) -> None:
        gap = self.cell_size * 0.14
        size = self.cell_size * 0.26
        square_fill = (115, 190, 220)
        square_border = (25, 55, 75)
        positions = [
            (rect.left + gap, rect.top + gap),
            (rect.right - gap - size, rect.top + gap),
            (rect.left + gap, rect.bottom - gap - size),
            (rect.right - gap - size, rect.bottom - gap - size),
        ]
        for x, y in positions:
            square = pygame.Rect(x, y, size, size)
            pygame.draw.rect(self.display, square_fill, square, border_radius=4)
            pygame.draw.rect(self.display, square_border, square, width=2, border_radius=4)

    def draw_overlay_text(self, lines):
        if not lines:
            return
        padding = 6
        line_surfaces = [self.font.render(line, True, (255, 255, 255)) for line in lines]
        max_width = max(surf.get_width() for surf in line_surfaces)
        total_height = sum(surf.get_height() for surf in line_surfaces) + padding * (len(lines) + 1)
        rect = pygame.Rect(padding, padding, max_width + padding * 2, total_height)
        surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 140))
        y = padding
        for surf in line_surfaces:
            surface.blit(surf, (padding, y))
            y += surf.get_height() + padding
        self.display.blit(surface, (0, 0))

    def render_with_overlay(self, lines):
        self.draw_board()
        self.draw_overlay_text(lines)
        pygame.display.flip()

    def show_end_screen(self, status: str, duration: float = 2.0) -> None:
        color = (90, 200, 140) if status == "win" else (220, 80, 80)
        title = "YOU WIN!" if status == "win" else "YOU LOSE!"
        subtitle = "Press any key to close" if status == "lose" else "Enjoy the victory!"

        particles = [
            {
                "x": random.uniform(0, self.width),
                "y": random.uniform(-self.height, 0),
                "vx": random.uniform(-20, 20),
                "vy": random.uniform(60, 140),
                "size": random.uniform(3, 7),
                "color": random.choice(
                    [
                        (255, 255, 255),
                        (255, 220, 180),
                        (200, 240, 255),
                        (255, 210, 240),
                    ]
                ),
            }
            for _ in range(80)
        ]

        start = time.time()
        waiting = True
        while waiting and time.time() - start < duration:
            self.draw_board()

            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((*color, 40))
            self.display.blit(overlay, (0, 0))

            for p in particles:
                p["x"] += p["vx"] * 0.016
                p["y"] += p["vy"] * 0.016
                if p["y"] > self.height:
                    p["y"] = random.uniform(-40, -10)
                    p["x"] = random.uniform(0, self.width)
                pygame.draw.rect(
                    self.display,
                    (*p["color"], 200),
                    pygame.Rect(p["x"], p["y"], p["size"], p["size"]),
                    border_radius=2,
                )

            title_surf = self.font.render(title, True, (255, 255, 255))
            sub_surf = self.small_font.render(subtitle, True, (230, 230, 235))
            self.display.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 2 - 10)))
            self.display.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, self.height // 2 + 26)))

            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                    break

            pygame.display.flip()
            self.tick()

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
                renderer.show_end_screen(outcome.status)
                running = False
                continue
    finally:
        renderer.close()
