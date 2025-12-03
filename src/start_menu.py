import random
from dataclasses import dataclass
from typing import Dict, Iterable, List

import pygame  # type: ignore


@dataclass
class MenuSelection:
    level: int
    mode: str  # "player" or "auto"
    solver: str  # "bfs" or "dfs" or "astar"
    use_renderer: bool


class StartMenu:
    """Simple Pygame start screen to pick the level and mode."""

    def __init__(self, levels: Iterable[int]):
        self.levels: List[int] = sorted({lvl for lvl in levels})
        if not self.levels:
            raise ValueError("StartMenu requires at least one level.")
        self.level_index = 0

        self.state = MenuSelection(
            level=self.levels[0],
            mode="player",
            solver="bfs",
            use_renderer=True,
        )

        pygame.init()
        pygame.font.init()

        self.width = 880
        self.height = 560
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Lava & Aqua – Start")
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("poppins", 50, bold=True)
        self.label_font = pygame.font.SysFont("poppins", 28, bold=True)
        self.small_font = pygame.font.SysFont("poppins", 19)

        self.bg_top = (16, 24, 42)
        self.bg_bottom = (8, 12, 24)
        self.panel = (26, 36, 54)
        self.panel_alt = (32, 44, 62)
        self.accent = (106, 220, 255)
        self.accent_alt = (64, 200, 170)
        self.text = (238, 242, 248)
        self.muted = (150, 158, 172)

        self.bg_surface = self._build_gradient()
        self.ambient_glow = [self._spawn_orb() for _ in range(14)]

    # --------------------------------------------------------------- Helpers

    def _build_gradient(self) -> pygame.Surface:
        surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r = int(self.bg_top[0] * (1 - t) + self.bg_bottom[0] * t)
            g = int(self.bg_top[1] * (1 - t) + self.bg_bottom[1] * t)
            b = int(self.bg_top[2] * (1 - t) + self.bg_bottom[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y))
        return surf

    def _spawn_orb(self) -> Dict[str, float]:
        return {
            "x": random.uniform(-80, self.width + 80),
            "y": random.uniform(-80, self.height + 80),
            "r": random.uniform(40, 120),
            "speed": random.uniform(6, 14),
            "alpha": random.randint(22, 50),
            "color": random.choice(
                [
                    (*self.accent, 0),
                    (*self.accent_alt, 0),
                    (120, 140, 255, 0),
                ]
            ),
        }

    def _update_orbs(self) -> None:
        for orb in self.ambient_glow:
            orb["y"] += orb["speed"] * 0.12
            if orb["y"] - orb["r"] > self.height + 120:
                orb.update(self._spawn_orb())
                orb["y"] = -orb["r"]
            radius = int(orb["r"])
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (*orb["color"][:3], int(orb["alpha"]))
            pygame.draw.circle(glow, color, (radius, radius), radius)
            self.screen.blit(glow, (orb["x"] - radius, orb["y"] - radius))

    # ----------------------------------------------------------------- Public

    def run(self) -> MenuSelection | None:
        selection: MenuSelection | None = None
        running = True
        while running:
            hitboxes = self._draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                        break
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self._shift_level(-1)
                    if event.key in (pygame.K_RIGHT, pygame.K_d):
                        self._shift_level(1)
                    if event.key in (pygame.K_TAB, pygame.K_SPACE):
                        self._toggle_mode()
                    if event.key == pygame.K_s and self.state.mode == "auto":
                        self._toggle_solver()
                    if event.key == pygame.K_r:
                        self.state.use_renderer = not self.state.use_renderer
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        selection = MenuSelection(
                            level=self.state.level,
                            mode=self.state.mode,
                            solver=self.state.solver,
                            use_renderer=self.state.use_renderer,
                        )
                        running = False
                        break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self._handle_click(event.pos, hitboxes)
                    if action == "start":
                        selection = MenuSelection(
                            level=self.state.level,
                            mode=self.state.mode,
                            solver=self.state.solver,
                            use_renderer=self.state.use_renderer,
                        )
                        running = False
                        break
                    if action == "quit":
                        running = False
                        break

            self.clock.tick(60)

        pygame.display.quit()
        pygame.quit()
        return selection

    # --------------------------------------------------------------- Drawing

    def _draw(self) -> Dict[str, pygame.Rect]:
        self.screen.blit(self.bg_surface, (0, 0))
        self._update_orbs()
        hitboxes: Dict[str, pygame.Rect] = {}

        card = pygame.Rect(60, 120, self.width - 120, 340)
        self._draw_panel(card)

        title = self.title_font.render("Lava & Aqua", True, self.text)
        subtitle = self.small_font.render("Pick a level, choose player or auto, then press Start.", True, self.muted)
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 70)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 105)))

        self._pill(f"{len(self.levels)} levels", (self.width - 90, 30))
        self._pill("WASD to move • U undo", (90, 30))

        hitboxes.update(self._draw_level_row(y=190))
        hitboxes.update(self._draw_mode_row(y=260))
        hitboxes.update(self._draw_solver_row(y=330))
        hitboxes.update(self._draw_renderer_row(y=400))
        hitboxes.update(self._draw_actions_row(y=455))

        tip = self.small_font.render(
            "Shortcuts: arrows change level • Tab switches mode • R toggles renderer • Enter to start",
            True,
            self.muted,
        )
        self.screen.blit(tip, tip.get_rect(center=(self.width // 2, self.height - 28)))

        pygame.display.flip()
        return hitboxes

    def _draw_level_row(self, y: int) -> Dict[str, pygame.Rect]:
        hit: Dict[str, pygame.Rect] = {}
        label = self.label_font.render("Level", True, self.text)
        self.screen.blit(label, label.get_rect(midleft=(80, y)))

        hit["level_dec"] = self._button("-", center=(self.width // 2 - 140, y), width=64, height=56)
        hit["level_inc"] = self._button("+", center=(self.width // 2 + 140, y), width=64, height=56)

        level_text = f"{self.state.level} / {self.levels[-1]}"
        level_rect = pygame.Rect(0, 0, 220, 56)
        level_rect.center = (self.width // 2, y)
        pygame.draw.rect(self.screen, self.panel, level_rect, border_radius=12)
        pygame.draw.rect(self.screen, self.accent, level_rect, width=2, border_radius=12)
        text = self.label_font.render(level_text, True, self.text)
        self.screen.blit(text, text.get_rect(center=level_rect.center))

        return hit

    def _draw_mode_row(self, y: int) -> Dict[str, pygame.Rect]:
        hit: Dict[str, pygame.Rect] = {}
        label = self.label_font.render("Mode", True, self.text)
        self.screen.blit(label, label.get_rect(midleft=(80, y)))

        hit["mode_player"] = self._button(
            "Player",
            center=(self.width // 2 - 90, y),
            width=170,
            height=56,
            selected=self.state.mode == "player",
        )
        hit["mode_auto"] = self._button(
            "Auto solver",
            center=(self.width // 2 + 90, y),
            width=170,
            height=56,
            selected=self.state.mode == "auto",
        )
        return hit

    def _draw_solver_row(self, y: int) -> Dict[str, pygame.Rect]:
        hit: Dict[str, pygame.Rect] = {}
        label = self.label_font.render("Solver", True, self.text if self.state.mode == "auto" else self.muted)
        self.screen.blit(label, label.get_rect(midleft=(80, y)))

        is_auto = self.state.mode == "auto"
        hit["solver_bfs"] = self._button(
            "BFS",
            center=(self.width // 2 - 90, y),
            width=130,
            height=50,
            selected=is_auto and self.state.solver == "bfs",
            disabled=not is_auto,
        )
        hit["solver_dfs"] = self._button(
            "DFS",
            center=(self.width // 2 + 90, y),
            width=130,
            height=50,
            selected=is_auto and self.state.solver == "dfs",
            disabled=not is_auto,
        )
        hit["solver_astar"] = self._button(
            "A*",
            center=(self.width // 2 + 250, y),
            width=130,
            height=50,
            selected=is_auto and self.state.solver == "astar",
            disabled=not is_auto,
        )
        solver_names = {
            "bfs": "BFS – Breadth-First Search",
            "dfs": "DFS – Depth-First Search",
            "astar": "A* – A-star Search",
        }
        current = solver_names.get(self.state.solver, self.state.solver.upper())

        helper_text = "Auto playback uses the renderer when enabled below."
        helper = self.small_font.render(helper_text, True, self.muted)
        self.screen.blit(helper, helper.get_rect(center=(self.width // 2, y + 46)))
        return hit

    def _draw_renderer_row(self, y: int) -> Dict[str, pygame.Rect]:
        hit: Dict[str, pygame.Rect] = {}
        label = self.label_font.render("Renderer", True, self.text)
        self.screen.blit(label, label.get_rect(midleft=(80, y)))

        status = "On – use Pygame visuals" if self.state.use_renderer else "Off – play/solve in terminal"
        hit["renderer"] = self._button(
            status,
            center=(self.width // 2, y),
            width=360,
            height=56,
            selected=self.state.use_renderer,
        )
        return hit

    def _draw_actions_row(self, y: int) -> Dict[str, pygame.Rect]:
        hit: Dict[str, pygame.Rect] = {}
        hit["start"] = self._button(
            "Start",
            center=(self.width // 2 - 90, y),
            width=170,
            height=56,
            selected=True,
        )
        hit["quit"] = self._button(
            "Quit",
            center=(self.width // 2 + 90, y),
            width=170,
            height=56,
            selected=False,
        )
        return hit

    def _draw_panel(self, rect: pygame.Rect) -> None:
        shadow = rect.inflate(24, 24)
        shadow_surf = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 110), shadow_surf.get_rect(), border_radius=26)
        self.screen.blit(shadow_surf, shadow.topleft)

        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*self.panel, 220), surf.get_rect(), border_radius=22)
        outline = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(outline, self.accent, outline.get_rect(), width=2, border_radius=22)
        surf.blit(outline, (0, 0))
        self.screen.blit(surf, rect.topleft)

    def _pill(self, text: str, pos: tuple[int, int]) -> None:
        surf = self.small_font.render(text, True, self.text)
        padding = 14
        rect = pygame.Rect(0, 0, surf.get_width() + padding * 2, surf.get_height() + 10)
        rect.center = pos
        pill = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(pill, (*self.panel_alt, 220), pill.get_rect(), border_radius=14)
        pygame.draw.rect(pill, self.accent, pill.get_rect(), width=1, border_radius=14)
        pill.blit(surf, surf.get_rect(center=pill.get_rect().center))
        self.screen.blit(pill, rect.topleft)

    def _button(
        self,
        label: str,
        center: tuple[int, int],
        width: int,
        height: int,
        selected: bool = False,
        disabled: bool = False,
    ) -> pygame.Rect:
        rect = pygame.Rect(0, 0, width, height)
        rect.center = center
        base_fill = self.panel if not selected else self.accent
        border = self.accent if selected else self.panel_alt
        if disabled:
            base_fill = self.panel_alt
            border = self.panel_alt

        shadow_rect = rect.inflate(10, 10)
        shadow = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 105), shadow.get_rect(), border_radius=16)
        self.screen.blit(shadow, shadow_rect.topleft)

        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            t = y / max(1, rect.height - 1)
            r = int(base_fill[0] * (0.9 + 0.1 * (1 - t)))
            g = int(base_fill[1] * (0.9 + 0.1 * (1 - t)))
            b = int(base_fill[2] * (0.9 + 0.1 * (1 - t)))
            pygame.draw.line(surface, (r, g, b), (0, y), (rect.width, y))
        pygame.draw.rect(surface, border, surface.get_rect(), width=2, border_radius=14)

        if selected and not disabled:
            glow = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.accent, 70), glow.get_rect(), border_radius=16)
            surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)

        self.screen.blit(surface, rect.topleft)

        color = self.bg_top if selected else (self.muted if disabled else self.text)
        text = self.label_font.render(label, True, color)
        self.screen.blit(text, text.get_rect(center=rect.center))
        return rect

    # --------------------------------------------------------------- Actions

    def _handle_click(self, pos: tuple[int, int], hitboxes: Dict[str, pygame.Rect]) -> str | None:
        if hitboxes["level_dec"].collidepoint(pos):
            self._shift_level(-1)
            return None
        if hitboxes["level_inc"].collidepoint(pos):
            self._shift_level(1)
            return None
        if hitboxes["mode_player"].collidepoint(pos):
            self.state.mode = "player"
            return None
        if hitboxes["mode_auto"].collidepoint(pos):
            self.state.mode = "auto"
            return None
        if hitboxes["solver_bfs"].collidepoint(pos) and self.state.mode == "auto":
            self.state.solver = "bfs"
            return None
        if hitboxes["solver_dfs"].collidepoint(pos) and self.state.mode == "auto":
            self.state.solver = "dfs"
            return None
        if hitboxes["renderer"].collidepoint(pos):
            self.state.use_renderer = not self.state.use_renderer
            return None
        if hitboxes["start"].collidepoint(pos):
            return "start"
        if hitboxes["quit"].collidepoint(pos):
            return "quit"
        return None

    def _shift_level(self, delta: int) -> None:
        self.level_index = max(0, min(self.level_index + delta, len(self.levels) - 1))
        self.state.level = self.levels[self.level_index]

    def _toggle_mode(self) -> None:
        self.state.mode = "auto" if self.state.mode == "player" else "player"

    def _toggle_solver(self) -> None:

        if self.state.solver == "bfs":
            self.state.solver = "dfs"
        elif self.state.solver == "dfs":
            self.state.solver = "astar"
        else:
            self.state.solver = "bfs"
