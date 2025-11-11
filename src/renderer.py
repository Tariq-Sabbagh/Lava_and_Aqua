"""
Pygame renderer for the Lava & Aqua board.

This module stays optional: importing it requires pygame to be installed,
but the CLI game loop continues to work without it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, Tuple

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - pygame optional in tests
    raise RuntimeError(
        "pygame is required for the graphical renderer. "
        "Install it via `pip install pygame` before using GameRenderer."
    ) from exc

from src.Board import Board

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class TileTheme:
    """Defines fill/outline colors for a tile type."""

    fill: Color
    border: Color


class GameRenderer:
    """Minimal Pygame renderer handling drawing and simple animations."""

    DEFAULT_THEME = {
        ".": TileTheme((30, 30, 30), (45, 45, 45)),
        "W": TileTheme((70, 70, 70), (110, 110, 110)),
        "P": TileTheme((60, 140, 255), (255, 255, 255)),
        "G": TileTheme((70, 200, 120), (255, 255, 255)),
        "L": TileTheme((220, 80, 30), (255, 160, 120)),
        "A": TileTheme((40, 180, 220), (120, 230, 255)),
        "B": TileTheme((200, 170, 90), (255, 220, 120)),
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
        """Blit the entire board state to the screen."""
        for r, row in enumerate(self.board.grid):
            for c, symbol in enumerate(row):
                rect = pygame.Rect(
                    c * self.cell_size, r * self.cell_size, self.cell_size, self.cell_size
                )
                theme = self._theme_for_symbol(symbol)
                pygame.draw.rect(self.display, theme.fill, rect)
                pygame.draw.rect(self.display, theme.border, rect, width=2)

                if symbol.isdigit():
                    self._draw_counter_value(symbol, rect)

        pygame.display.flip()

    def _draw_counter_value(self, value: str, rect: pygame.Rect) -> None:
        text = self.font.render(value, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        self.display.blit(text, text_rect)

    def _theme_for_symbol(self, symbol: str) -> TileTheme:
        if symbol.isdigit():
            return self.COUNTER_THEME
        return self.DEFAULT_THEME.get(symbol, self.DEFAULT_THEME["."])

    # ----------------------------------------------------------- Input helpers

    def next_command(self) -> str | None:
        """
        Poll pygame events and translate arrow/WASD inputs into move commands.
        Returns "W", "A", "S", "D", "Q" or None if no actionable input was found.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Q"
            if event.type == pygame.KEYDOWN:
                keymap = {
                    pygame.K_w: "W",
                    pygame.K_s: "S",
                    pygame.K_a: "A",
                    pygame.K_d: "D",
                    pygame.K_UP: "W",
                    pygame.K_DOWN: "S",
                    pygame.K_LEFT: "A",
                    pygame.K_RIGHT: "D",
                    pygame.K_ESCAPE: "Q",
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
        """
        Simple lerp animation between start and end cells for the provided symbol.
        Call this after a successful move to smooth the transition.
        """
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
        """Cap the frame rate; call once per loop iteration."""
        self.clock.tick(self.fps)

    def close(self) -> None:
        pygame.quit()


def play_with_renderer(level: int, factory) -> None:
    """
    Convenience helper to run the existing logic with the renderer.
    This keeps main.py clean while demonstrating how to integrate Pygame.
    """
    ctx = factory.create(level)
    renderer = GameRenderer(ctx.board)
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
            move = ctx.rules.apply_move(cmd)
            if move.status == "ok":
                data = move.data or {}
                if data.get("from") and data.get("to"):
                    renderer.animate_move(data["from"], data["to"])
            elif move.status in ("win", "lose"):
                renderer.draw_board()
                time.sleep(1.5)
                running = False
                continue

            ctx.rules.tick_counters()
            ctx.rules.apply_spread("lava")
            ctx.rules.apply_spread("aqua")
    finally:
        renderer.close()
