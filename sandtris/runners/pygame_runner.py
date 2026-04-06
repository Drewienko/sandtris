import json
import sys
import pygame
import numpy as np
from pathlib import Path
from enum import Enum, auto

from sandtris.core.engine import SandtrisEngine
from sandtris.core.config import GameConfig
from sandtris.render.gameplay_screen import GameplayScreen
from sandtris.render.pause_screen import PauseScreen
from sandtris.render.game_over_screen import GameOverScreen
from sandtris.render.settings_screen import SettingsScreen
from sandtris.render.main_menu_screen import MainMenuScreen
from sandtris.render.how_to_play_screen import HowToPlayScreen
from sandtris.render.ui import (
    SAND_PALETTE_PRESETS,
    THEME_PRESETS,
    build_color_palette,
)

# Try to get the window object for pygbag localStorage
window = None
if sys.platform == "emscripten":
    try:
        import platform

        window = platform.window
    except Exception:
        pass


def load_persistent_data(key: str, fallback_path: Path) -> dict:
    if window:
        try:
            val = window.localStorage.getItem(key)
            if val:
                return json.loads(val)
        except Exception:
            pass
    elif fallback_path.exists():
        try:
            return json.loads(fallback_path.read_text())
        except Exception:
            pass
    return {}


def save_persistent_data(key: str, fallback_path: Path, data: dict) -> None:
    json_str = json.dumps(data, indent=2)
    if window:
        try:
            window.localStorage.setItem(key, json_str)
        except Exception:
            pass
    else:
        try:
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            fallback_path.write_text(json_str)
        except Exception:
            pass


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    SETTINGS = auto()
    HOW_TO_PLAY = auto()


class PygameRunner:
    def __init__(
        self,
        config: GameConfig,
        engine: SandtrisEngine | None = None,
    ) -> None:
        self.config = config
        self.engine = engine or SandtrisEngine(config)
        self.state = GameState.MAIN_MENU
        self.previous_state = GameState.MAIN_MENU
        self.theme_name = "Egyptian"
        self.sand_palette_name = "Classic"

        self.high_score_path = (
            Path(__file__).parent.parent.parent / "data" / "high_score.json"
        )
        self.settings_path = (
            Path(__file__).parent.parent.parent / "data" / "settings.json"
        )

        settings_data = load_persistent_data(
            "sandtris_settings", self.settings_path
        )
        if (
            "theme_name" in settings_data
            and settings_data["theme_name"] in THEME_PRESETS
        ):
            self.theme_name = settings_data["theme_name"]
        if (
            "sand_palette_name" in settings_data
            and settings_data["sand_palette_name"] in SAND_PALETTE_PRESETS
        ):
            self.sand_palette_name = settings_data["sand_palette_name"]

        self.color_palette = build_color_palette(
            THEME_PRESETS[self.theme_name].screen_bg,
            SAND_PALETTE_PRESETS[self.sand_palette_name],
        )
        self.game_over_status = "Save your score"

        if not self.config.headless:
            pygame.init()
            self.screen = pygame.display.set_mode((720, 900), pygame.RESIZABLE)
            pygame.display.set_caption("Sandtris")
            self.clock = pygame.time.Clock()
            font_path = (
                Path(__file__).parent.parent
                / "assets"
                / "fonts"
                / "PressStart2P.ttf"
            )
            if font_path.exists():
                self.title_font = pygame.font.Font(str(font_path), 24)
                self.body_font = pygame.font.Font(str(font_path), 16)
            else:
                self.title_font = pygame.font.SysFont(None, 42)
                self.body_font = pygame.font.SysFont(None, 28)
            self.screen_view = GameplayScreen(self.title_font, self.body_font)
            self.pause_view = PauseScreen(self.title_font, self.body_font)
            self.game_over_view = GameOverScreen(
                self.title_font, self.body_font
            )
            self.settings_view = SettingsScreen(
                self.title_font, self.body_font
            )
            self.main_menu_view = MainMenuScreen(
                self.title_font, self.body_font
            )
            self.how_to_play_view = HowToPlayScreen(
                self.title_font, self.body_font
            )
            self._apply_theme(self.theme_name)
            pygame.key.set_repeat(200, 50)

        self.fall_timer = 0
        self.current_fall_delay = self.config.fall_delay
        self.running = True
        self.fast_dropping = False
        self.paused = False
        self.mouse_down = False

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu_events(event)
            elif self.state == GameState.PLAYING:
                self._handle_playing_events(event)
            elif self.state == GameState.SETTINGS:
                self._handle_settings_events(event)
            elif self.state == GameState.HOW_TO_PLAY:
                self._handle_how_to_play_events(event)

    def _save_settings(self) -> None:
        save_persistent_data(
            "sandtris_settings",
            self.settings_path,
            {
                "theme_name": self.theme_name,
                "sand_palette_name": self.sand_palette_name,
            },
        )

    def _apply_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name
        theme = THEME_PRESETS[theme_name]
        self.screen_view.theme = theme
        self.pause_view.theme = theme
        self.game_over_view.theme = theme
        self.main_menu_view.theme = theme
        self.how_to_play_view.theme = theme
        self.settings_view.theme = theme
        self.color_palette = build_color_palette(
            theme.screen_bg,
            SAND_PALETTE_PRESETS[self.sand_palette_name],
        )
        self._save_settings()

    def _apply_sand_palette(self, palette_name: str) -> None:
        self.sand_palette_name = palette_name
        self.color_palette = build_color_palette(
            THEME_PRESETS[self.theme_name].screen_bg,
            SAND_PALETTE_PRESETS[self.sand_palette_name],
        )
        self._save_settings()

    def _save_high_score(self) -> None:
        current = {
            "score": self.engine.score,
            "level": self.engine.level,
            "max_combo": self.engine.max_combo,
        }
        saved = load_persistent_data(
            "sandtris_highscore", self.high_score_path
        )

        if current["score"] > saved.get("score", 0):
            save_persistent_data(
                "sandtris_highscore", self.high_score_path, current
            )
            self.game_over_status = "New high score saved"
        else:
            self.game_over_status = "Score saved, best unchanged"

    def _open_settings(self) -> None:
        self.previous_state = self.state
        self.state = GameState.SETTINGS

    def _restart_game(self) -> None:
        self.engine = SandtrisEngine(self.config)
        self.paused = False
        self.fast_dropping = False
        self.current_fall_delay = self.config.fall_delay
        self.pause_view.confirming_restart = False
        self.pause_view.confirming_menu = False
        self.game_over_status = "Save your score"

    def _handle_settings_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            theme_name = self.settings_view.theme_at(screen_rect, event.pos)
            if theme_name is not None:
                self._apply_theme(theme_name)
                return
            sand_name = self.settings_view.sand_palette_at(
                screen_rect, event.pos
            )
            if sand_name is not None:
                self._apply_sand_palette(sand_name)
                return
            if self.settings_view.back_button_contains(screen_rect, event.pos):
                self.state = self.previous_state

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN and event.key in self.config.key_pause:
            self.state = self.previous_state

    def _handle_how_to_play_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.how_to_play_view.back_button_contains(
                screen_rect, event.pos
            ):
                self.state = GameState.MAIN_MENU

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN and event.key in self.config.key_pause:
            self.state = GameState.MAIN_MENU

    def _handle_main_menu_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.main_menu_view.play_button_contains(
                screen_rect, event.pos
            ):
                self._restart_game()
                self.state = GameState.PLAYING
            elif self.main_menu_view.settings_button_contains(
                screen_rect, event.pos
            ):
                self._open_settings()
            elif self.main_menu_view.help_button_contains(
                screen_rect, event.pos
            ):
                self.state = GameState.HOW_TO_PLAY
            elif self.main_menu_view.quit_button_contains(
                screen_rect, event.pos
            ):
                self.running = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

    def _handle_playing_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()

            if self.engine.game_over:
                if self.game_over_view.restart_button_contains(
                    screen_rect, event.pos
                ):
                    self._restart_game()
                    return
                if self.game_over_view.save_button_contains(
                    screen_rect, event.pos
                ):
                    self._save_high_score()
                    return
                if self.game_over_view.menu_button_contains(
                    screen_rect, event.pos
                ):
                    self.state = GameState.MAIN_MENU
                    self.paused = False
                    return
            elif self.paused:
                if self.pause_view.yes_button_contains(screen_rect, event.pos):
                    if self.pause_view.confirming_restart:
                        self._restart_game()
                    elif self.pause_view.confirming_menu:
                        self.state = GameState.MAIN_MENU
                        self.paused = False
                        self.pause_view.confirming_menu = False
                    return
                if self.pause_view.no_button_contains(screen_rect, event.pos):
                    self.pause_view.confirming_restart = False
                    self.pause_view.confirming_menu = False
                    return

                if self.pause_view.resume_button_contains(
                    screen_rect, event.pos
                ):
                    self.paused = False
                    return
                if self.pause_view.restart_button_contains(
                    screen_rect, event.pos
                ):
                    self.pause_view.confirming_restart = True
                    return
                if self.pause_view.settings_button_contains(
                    screen_rect, event.pos
                ):
                    self._open_settings()
                    return
                if self.pause_view.menu_button_contains(
                    screen_rect, event.pos
                ):
                    self.pause_view.confirming_menu = True
                    return
            else:
                if self.screen_view.pause_button_contains(
                    screen_rect, event.pos
                ):
                    self.paused = True
                    return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN:
            if event.key in self.config.key_pause:
                if not self.engine.game_over:
                    self.paused = not self.paused
                    if not self.paused:
                        self.pause_view.confirming_restart = False
                        self.pause_view.confirming_menu = False
                return

            if self.paused or self.engine.game_over:
                return

            if self.fast_dropping:
                return

            if event.key in self.config.key_left:
                self.engine.move_active_piece(-1, 0)
            elif event.key in self.config.key_right:
                self.engine.move_active_piece(1, 0)
            elif event.key in self.config.key_up:
                self.engine.rotate_active_piece()
            elif (
                event.key in self.config.key_down
                or event.key in self.config.key_drop
            ):
                self.fast_dropping = True
                self.current_fall_delay = self.config.fast_fall_delay

    def update(self) -> None:
        if self.state != GameState.PLAYING:
            return

        if self.paused:
            return

        if not self.engine.game_over:
            self.fall_timer += 1
            if self.fall_timer >= self.current_fall_delay:
                self.fall_timer = 0
                if self.engine.active_piece:
                    if not self.engine.move_active_piece(0, 1):
                        self.engine.lock_piece()
                        self.fast_dropping = False
                        self.current_fall_delay = self.config.fall_delay

        self.engine.tick()

    def draw(self) -> None:
        if self.config.headless:
            return

        if self.state == GameState.MAIN_MENU:
            self.main_menu_view.draw(
                self.screen,
                pygame.mouse.get_pos(),
                self.mouse_down,
            )
            pygame.display.flip()
            return
        elif self.state == GameState.HOW_TO_PLAY:
            self.how_to_play_view.draw(
                self.screen,
                self.config,
                pygame.mouse.get_pos(),
                self.mouse_down,
            )
            pygame.display.flip()
            return
        elif self.state == GameState.SETTINGS:
            self.settings_view.draw(
                self.screen,
                self.theme_name,
                self.sand_palette_name,
                pygame.mouse.get_pos(),
                self.mouse_down,
            )
            pygame.display.flip()
            return

        color_data = np.zeros(
            (self.config.width, self.config.height, 3), dtype=np.uint8
        )
        color_data[:, :] = self.color_palette[0]

        for y in range(self.config.height):
            for x in range(self.config.width):
                val = self.engine.grid.data[y, x]
                if val > 0:
                    color_data[x, y] = self.color_palette[val]

        if self.engine.active_piece:
            for bx, by, color in self.engine.active_piece.get_cells():
                if (
                    0 <= bx < self.config.width
                    and 0 <= by < self.config.height
                ):
                    color_data[bx, by] = self.color_palette[color]

        surf = pygame.surfarray.make_surface(color_data)
        self.screen_view.draw(
            self.screen,
            surf,
            self.engine.score,
            self.engine.level,
            self.engine.combo,
            int(self.clock.get_fps()),
            self.engine.next_shape_name,
            self.engine.next_color_id,
            self.config.scale,
            self.color_palette,
            pygame.mouse.get_pos(),
            self.mouse_down,
        )

        if self.engine.game_over:
            self.game_over_view.draw(
                self.screen,
                self.engine.score,
                self.engine.level,
                self.engine.max_combo,
                self.game_over_status,
                pygame.mouse.get_pos(),
                self.mouse_down,
            )
        elif self.paused:
            self.pause_view.draw(
                self.screen,
                pygame.mouse.get_pos(),
                self.mouse_down,
            )

        pygame.display.flip()

    async def run(self) -> None:
        import asyncio

        while self.running:
            if not self.config.headless:
                self.handle_events()

            self.update()

            if not self.config.headless:
                self.draw()
                self.clock.tick(self.config.fps)

            await asyncio.sleep(0)

        if not self.config.headless:
            pygame.quit()
