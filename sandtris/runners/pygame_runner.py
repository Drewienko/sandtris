import json
import os
import sys
import time
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
from sandtris.render.high_scores_screen import HighScoresScreen
from sandtris.render.ui import (
    SAND_PALETTE_PRESETS,
    THEME_PRESETS,
    build_color_palette,
)
from sandtris.render.vs_screen import VsScreen
from sandtris.ai.base import Action, GameObservation
from sandtris.ai.dqn_agent import DQNAgent

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
    if fallback_path.exists():
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


_DEFAULT_HIGH_SCORES = [
    {
        "player": "ALEXEY",
        "score": 99999,
        "level": 99,
        "max_combo": 10,
        "date": "1984-06-06",
        "pieces_placed": 999,
        "pixels_cleared": 9999,
        "duration_s": 600,
    },
    {
        "player": "CONWAY",
        "score": 42000,
        "level": 21,
        "max_combo": 9,
        "date": "1970-10-21",
        "pieces_placed": 280,
        "pixels_cleared": 4200,
        "duration_s": 480,
    },
    {
        "player": "NEUMANN",
        "score": 29000,
        "level": 14,
        "max_combo": 8,
        "date": "1966-03-29",
        "pieces_placed": 190,
        "pixels_cleared": 2900,
        "duration_s": 360,
    },
    {
        "player": "SANDY",
        "score": 13700,
        "level": 7,
        "max_combo": 6,
        "date": "2024-04-01",
        "pieces_placed": 91,
        "pixels_cleared": 1370,
        "duration_s": 214,
    },
]


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING = auto()
    SETTINGS = auto()
    HOW_TO_PLAY = auto()
    HIGH_SCORES = auto()
    PLAYER_VS_AI = auto()


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
        self.player_name = settings_data.get("player_name", "PLAYER")
        self.game_start_time = time.time()
        loaded_hs = load_persistent_data("sandtris_highscore", self.high_score_path)
        if not isinstance(loaded_hs, list):
            self._cached_high_score: list = list(_DEFAULT_HIGH_SCORES)
            save_persistent_data(
                "sandtris_highscore", self.high_score_path, self._cached_high_score
            )
        else:
            self._cached_high_score: list = loaded_hs
        self.level_up_timer_ms: float = 0.0
        self._prev_level: int = 1
        self.menu_focus: int = 0
        self._game_over_reloaded: bool = False
        self.ai_engine: SandtrisEngine | None = None
        self.ai_agent: DQNAgent | None = None
        self.ai_piece_drop_accumulator_ms: float = 0.0
        self._ai_piece_ticks: int = 0
        self.vs_result: str | None = None

        if not self.config.headless:
            if not window and os.environ.get("WAYLAND_DISPLAY"):
                os.environ.setdefault("SDL_VIDEODRIVER", "wayland")
            pygame.init()
            self.screen = pygame.display.set_mode(
                self._initial_window_size(), pygame.RESIZABLE
            )
            pygame.display.set_caption("Sandtris")
            self.clock = pygame.time.Clock()
            if window:
                window.canvas.style.imageRendering = "pixelated"
                window.canvas.style.setProperty("image-rendering", "pixelated")
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
            self.high_scores_view = HighScoresScreen(
                self.title_font, self.body_font
            )
            self.vs_view = VsScreen(self.title_font, self.body_font)
            self._apply_theme(self.theme_name)
            pygame.key.set_repeat(200, 50)

        self.current_fall_delay = self.config.fall_delay
        self.running = True
        self.fast_dropping = False
        self.paused = False
        self.mouse_down = False
        self.piece_drop_accumulator_ms = 0.0
        self.sand_step_accumulator_ms = 0.0
        self.pending_lock = False
        self.lock_timer_ms = 0.0
        self.pending_lock_ai = False
        self.lock_timer_ai_ms = 0.0
        self._das_left_ms: float = 0.0
        self._das_right_ms: float = 0.0

    def _initial_window_size(self) -> tuple[int, int]:
        if window:
            width = max(720, int(window.innerWidth))
            height = max(900, int(window.innerHeight))
            return width, height
        return 720, 900

    def _sync_window_size(self) -> None:
        if not window:
            return
        width = max(720, int(window.innerWidth))
        height = max(900, int(window.innerHeight))
        if self.screen.get_size() != (width, height):
            self.screen = pygame.display.set_mode(
                (width, height), pygame.RESIZABLE
            )

    def _piece_drop_interval_ms(self) -> float:
        return (self.current_fall_delay / self.config.fps) * 1000.0

    def _sand_step_interval_ms(self) -> float:
        sand_fps = min(self.config.fps, 30) if window else self.config.fps
        return 1000.0 / sand_fps

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE and not window:
                if os.environ.get("SDL_VIDEODRIVER") == "wayland":
                    self.screen = pygame.display.get_surface()
                else:
                    self.screen = pygame.display.set_mode(
                        event.size, pygame.RESIZABLE
                    )

            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu_events(event)
            elif self.state == GameState.PLAYING:
                self._handle_playing_events(event)
            elif self.state == GameState.SETTINGS:
                self._handle_settings_events(event)
            elif self.state == GameState.HOW_TO_PLAY:
                self._handle_how_to_play_events(event)
            elif self.state == GameState.HIGH_SCORES:
                self._handle_high_scores_events(event)
            elif self.state == GameState.PLAYER_VS_AI:
                self._handle_vs_events(event)

    def _save_settings(self) -> None:
        save_persistent_data(
            "sandtris_settings",
            self.settings_path,
            {
                "theme_name": self.theme_name,
                "sand_palette_name": self.sand_palette_name,
                "player_name": self.player_name,
            },
        )

    def _rebuild_palette_lut(self) -> None:
        lut = np.zeros((256, 3), dtype=np.uint8)
        for k, v in self.color_palette.items():
            lut[k] = v
        self._palette_lut = lut

    def _apply_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name
        theme = THEME_PRESETS[theme_name]
        self.screen_view.theme = theme
        self.pause_view.theme = theme
        self.game_over_view.theme = theme
        self.main_menu_view.theme = theme
        self.how_to_play_view.theme = theme
        self.high_scores_view.theme = theme
        self.settings_view.theme = theme
        if hasattr(self, "vs_view"):
            self.vs_view.theme = theme
        self.color_palette = build_color_palette(
            theme.screen_bg,
            SAND_PALETTE_PRESETS[self.sand_palette_name],
        )
        self._rebuild_palette_lut()
        self._save_settings()

    def _apply_sand_palette(self, palette_name: str) -> None:
        self.sand_palette_name = palette_name
        self.color_palette = build_color_palette(
            THEME_PRESETS[self.theme_name].screen_bg,
            SAND_PALETTE_PRESETS[self.sand_palette_name],
        )
        self._rebuild_palette_lut()
        self._save_settings()

    def _get_rank(self) -> int | None:
        score = self.engine.score
        rank = (
            sum(1 for e in self._cached_high_score if e.get("score", 0) > score)
            + 1
        )
        return rank if rank <= 10 else None

    def _save_high_score(self) -> None:
        duration_s = int(time.time() - self.game_start_time)
        entry = {
            "player": self.player_name,
            "score": self.engine.score,
            "level": self.engine.level,
            "max_combo": self.engine.max_combo,
            "date": time.strftime("%Y-%m-%d"),
            "pieces_placed": self.engine.pieces_placed,
            "pixels_cleared": self.engine.pixels_cleared,
            "duration_s": duration_s,
        }
        saved = load_persistent_data(
            "sandtris_highscore", self.high_score_path
        )
        scores = saved if isinstance(saved, list) else []
        scores.append(entry)
        scores.sort(key=lambda e: e.get("score", 0), reverse=True)
        scores = scores[:10]
        save_persistent_data(
            "sandtris_highscore", self.high_score_path, scores
        )
        self._cached_high_score = scores
        saved_rank = next(
            (
                i + 1
                for i, e in enumerate(scores)
                if e.get("score") == entry["score"]
                and e.get("player") == entry["player"]
            ),
            None,
        )
        if saved_rank == 1:
            self.game_over_status = "New high score!"
        elif saved_rank is not None:
            self.game_over_status = f"Saved as #{saved_rank}"
        else:
            self.game_over_status = "Not in top 10"

    def _open_settings(self) -> None:
        self.previous_state = self.state
        self.state = GameState.SETTINGS
        self.menu_focus = 0
        self.settings_view.name_field_active = False

    def _restart_game(self) -> None:
        self.main_menu_view.confirming_quit = False
        self.engine = SandtrisEngine(self.config)
        self.paused = False
        self.fast_dropping = False
        self.current_fall_delay = self.config.fall_delay
        self.piece_drop_accumulator_ms = 0.0
        self.sand_step_accumulator_ms = 0.0
        self.pause_view.confirming_restart = False
        self.pause_view.confirming_menu = False
        self.game_over_status = "Save your score"
        self.game_start_time = time.time()
        self.level_up_timer_ms = 0.0
        self._prev_level = 1
        self.menu_focus = 0
        self._game_over_reloaded = False
        self.pending_lock = False
        self.lock_timer_ms = 0.0
        self._das_left_ms = 0.0
        self._das_right_ms = 0.0

    def _handle_settings_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.settings_view.name_field_contains(screen_rect, event.pos):
                self.settings_view.name_field_active = True
                return
            self.settings_view.name_field_active = False
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
                self.settings_view.name_field_active = False
                self._save_settings()
                self.state = self.previous_state

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN:
            if self.settings_view.name_field_active:
                if event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.settings_view.name_field_active = False
                    self._save_settings()
                elif (
                    event.unicode.isprintable() and len(self.player_name) < 12
                ):
                    self.player_name += event.unicode.upper()
                return
            if event.key in self.config.key_pause:
                self._save_settings()
                self.state = self.previous_state
                self.menu_focus = 0
                return
            if event.key in self.config.key_down:
                self.menu_focus = (self.menu_focus + 1) % 4
            elif event.key in self.config.key_up:
                self.menu_focus = (self.menu_focus - 1) % 4
            elif event.key in self.config.key_left:
                if self.menu_focus == 1:
                    themes = list(THEME_PRESETS.keys())
                    self._apply_theme(themes[(themes.index(self.theme_name) - 1) % len(themes)])
                elif self.menu_focus == 2:
                    palettes = list(SAND_PALETTE_PRESETS.keys())
                    self._apply_sand_palette(palettes[(palettes.index(self.sand_palette_name) - 1) % len(palettes)])
            elif event.key in self.config.key_right:
                if self.menu_focus == 1:
                    themes = list(THEME_PRESETS.keys())
                    self._apply_theme(themes[(themes.index(self.theme_name) + 1) % len(themes)])
                elif self.menu_focus == 2:
                    palettes = list(SAND_PALETTE_PRESETS.keys())
                    self._apply_sand_palette(palettes[(palettes.index(self.sand_palette_name) + 1) % len(palettes)])
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_focus == 0:
                    self.settings_view.name_field_active = True
                elif self.menu_focus == 3:
                    self.settings_view.name_field_active = False
                    self._save_settings()
                    self.state = self.previous_state
                    self.menu_focus = 0

    def _start_vs_game(self) -> None:
        self.ai_engine = SandtrisEngine(self.config)
        self.ai_piece_drop_accumulator_ms = 0.0
        self.pending_lock_ai = False
        self.lock_timer_ai_ms = 0.0
        self.vs_result = None
        self.menu_focus = 0

        # prefer scale8 final, then latest numbered checkpoint
        _candidates = [
            Path("models/scale8BFS/dqn_final.pt"),
            Path("models/scale8/dqn_final.pt"),
            Path("models/dqn_final.pt"),
            *sorted(Path("models").glob("dqn_[0-9]*.pt")),
        ]
        model_path = next((p for p in _candidates if p.exists()), None)
        if model_path is not None:
            try:
                self.ai_agent = DQNAgent(model_path)
                self.ai_agent.reset()
            except Exception:
                self.ai_agent = None
        else:
            self.ai_agent = None

        self._restart_game()
        self.state = GameState.PLAYER_VS_AI

    def _handle_vs_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.vs_result is not None:
                if self.vs_view.restart_button_contains(screen_rect, event.pos):
                    self._start_vs_game()
                    return
                if self.vs_view.menu_button_contains(screen_rect, event.pos):
                    self.state = GameState.MAIN_MENU
                    self.menu_focus = 0
                    return
            elif self.paused:
                if self.pause_view.yes_button_contains(screen_rect, event.pos):
                    if self.pause_view.confirming_restart:
                        self._start_vs_game()
                    elif self.pause_view.confirming_menu:
                        self.state = GameState.MAIN_MENU
                        self.paused = False
                        self.pause_view.confirming_menu = False
                    return
                if self.pause_view.no_button_contains(screen_rect, event.pos):
                    self.pause_view.confirming_restart = False
                    self.pause_view.confirming_menu = False
                    return
                if self.pause_view.resume_button_contains(screen_rect, event.pos):
                    self.paused = False
                    return
                if self.pause_view.restart_button_contains(screen_rect, event.pos):
                    self.pause_view.confirming_restart = True
                    return
                if self.pause_view.settings_button_contains(screen_rect, event.pos):
                    self._open_settings()
                    return
                if self.pause_view.menu_button_contains(screen_rect, event.pos):
                    self.pause_view.confirming_menu = True
                    return
            else:
                if self.vs_view.pause_button_contains(screen_rect, event.pos):
                    self.paused = True
                    self.menu_focus = 0
                    return
                if self.vs_view.quit_button_contains(screen_rect, event.pos):
                    self.engine.game_over = True
                    self.vs_result = (
                        "YOU WIN!" if self.engine.score > self.ai_engine.score else "AI WINS!"
                    )
                    self.menu_focus = 0
                    return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN:
            if event.key in self.config.key_pause:
                if self.vs_result is None:
                    self.paused = not self.paused
                    if not self.paused:
                        self.pause_view.confirming_restart = False
                        self.pause_view.confirming_menu = False
                elif self.vs_result is not None:
                    self.state = GameState.MAIN_MENU
                    self.menu_focus = 0
                return

            if self.vs_result is not None:
                if event.key in self.config.key_down:
                    self.menu_focus = (self.menu_focus + 1) % 2
                elif event.key in self.config.key_up:
                    self.menu_focus = (self.menu_focus - 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.menu_focus == 0:
                        self._start_vs_game()
                    else:
                        self.state = GameState.MAIN_MENU
                        self.menu_focus = 0
                return

            if self.paused:
                confirming = (
                    self.pause_view.confirming_restart
                    or self.pause_view.confirming_menu
                )
                n = 2 if confirming else 4
                if event.key in self.config.key_down:
                    self.menu_focus = (self.menu_focus + 1) % n
                elif event.key in self.config.key_up:
                    self.menu_focus = (self.menu_focus - 1) % n
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if confirming:
                        if self.menu_focus == 0:
                            if self.pause_view.confirming_restart:
                                self._start_vs_game()
                            else:
                                self.state = GameState.MAIN_MENU
                                self.paused = False
                                self.pause_view.confirming_menu = False
                        else:
                            self.pause_view.confirming_restart = False
                            self.pause_view.confirming_menu = False
                            self.menu_focus = 0
                    else:
                        if self.menu_focus == 0:
                            self.paused = False
                            self.menu_focus = 0
                        elif self.menu_focus == 1:
                            self.pause_view.confirming_restart = True
                            self.menu_focus = 1
                        elif self.menu_focus == 2:
                            self._open_settings()
                        elif self.menu_focus == 3:
                            self.pause_view.confirming_menu = True
                            self.menu_focus = 1
                return

            if self.engine.game_over:
                return

            if event.key in self.config.key_left:
                moved = self.engine.move_active_piece(-1, 0)
                if moved and self.pending_lock:
                    if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                        self.pending_lock = False
                    else:
                        self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_right:
                moved = self.engine.move_active_piece(1, 0)
                if moved and self.pending_lock:
                    if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                        self.pending_lock = False
                    else:
                        self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_up:
                self.engine.rotate_active_piece()
                if self.pending_lock:
                    self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_drop:
                while self.engine.move_active_piece(0, 1):
                    pass
                self.pending_lock = True
                self.lock_timer_ms = self.config.lock_delay_ms
                self.piece_drop_accumulator_ms = 0
                self.fast_dropping = False
                self.current_fall_delay = self.config.fall_delay
            elif event.key in self.config.key_down:
                if not self.pending_lock:
                    self.fast_dropping = True
                    self.current_fall_delay = self.config.fast_fall_delay

        if event.type == pygame.KEYUP:
            if event.key in self.config.key_down:
                self.fast_dropping = False
                self.current_fall_delay = self.config.fall_delay

    def _handle_how_to_play_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.how_to_play_view.back_button_contains(
                screen_rect, event.pos
            ):
                self.state = self.previous_state

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN and event.key in self.config.key_pause:
            self.state = self.previous_state

    def _handle_high_scores_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            if self.high_scores_view.back_button_contains(
                self.screen.get_rect(), event.pos
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
            _show_vs = window is None
            if self.main_menu_view.yes_button_contains(screen_rect, event.pos):
                self.running = False
            elif self.main_menu_view.no_button_contains(
                screen_rect, event.pos
            ):
                self.main_menu_view.confirming_quit = False
            elif self.main_menu_view.play_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                self._restart_game()
                self.state = GameState.PLAYING
            elif self.main_menu_view.vs_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                self._start_vs_game()
            elif self.main_menu_view.settings_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                self._open_settings()
            elif self.main_menu_view.scores_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                loaded = load_persistent_data(
                    "sandtris_highscore", self.high_score_path
                )
                self._cached_high_score = (
                    loaded if isinstance(loaded, list) else []
                )
                self.state = GameState.HIGH_SCORES
            elif self.main_menu_view.help_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                self.previous_state = GameState.MAIN_MENU
                self.state = GameState.HOW_TO_PLAY
            elif self.main_menu_view.quit_button_contains(
                screen_rect, event.pos, _show_vs
            ):
                self.main_menu_view.confirming_quit = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse_down = False

        if event.type == pygame.KEYDOWN:
            if self.main_menu_view.confirming_quit:
                if event.key in (pygame.K_ESCAPE,):
                    self.main_menu_view.confirming_quit = False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.menu_focus == 0:
                        self.running = False
                    else:
                        self.main_menu_view.confirming_quit = False
                elif event.key in self.config.key_down:
                    self.menu_focus = (self.menu_focus + 1) % 2
                elif event.key in self.config.key_up:
                    self.menu_focus = (self.menu_focus - 1) % 2
                return
            _show_vs = window is None
            _n_items = 6 if _show_vs else 5
            if event.key in self.config.key_down:
                self.menu_focus = (self.menu_focus + 1) % _n_items
            elif event.key in self.config.key_up:
                self.menu_focus = (self.menu_focus - 1) % _n_items
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                # indices: play=0, [vs=1,] settings, scores, help, quit
                idx = self.menu_focus
                if idx == 0:
                    self._restart_game()
                    self.state = GameState.PLAYING
                elif _show_vs and idx == 1:
                    self._start_vs_game()
                else:
                    offset = 2 if _show_vs else 1
                    rel = idx - offset
                    if rel == 0:
                        self._open_settings()
                    elif rel == 1:
                        loaded = load_persistent_data(
                            "sandtris_highscore", self.high_score_path
                        )
                        self._cached_high_score = (
                            loaded if isinstance(loaded, list) else []
                        )
                        self.state = GameState.HIGH_SCORES
                        self.menu_focus = 0
                    elif rel == 2:
                        self.previous_state = GameState.MAIN_MENU
                        self.state = GameState.HOW_TO_PLAY
                        self.menu_focus = 0
                    elif rel == 3:
                        self.main_menu_view.confirming_quit = True
                        self.menu_focus = 1

    def _handle_playing_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()

            if self.engine.game_over:
                if self.game_over_view.name_field_contains(screen_rect, event.pos):
                    self.menu_focus = -1
                    return
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
                    self.menu_focus = 0
                    return
                if self.screen_view.help_button_contains(
                    screen_rect, event.pos
                ):
                    self.paused = True
                    self.previous_state = GameState.PLAYING
                    self.state = GameState.HOW_TO_PLAY
                    return
                if self.screen_view.skull_button_contains(
                    screen_rect, event.pos
                ):
                    self.engine.game_over = True
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

            if self.engine.game_over:
                if event.key in (pygame.K_DOWN,):
                    if self.menu_focus == -1:
                        self.menu_focus = 0
                    else:
                        self.menu_focus = (self.menu_focus + 1) % 3
                elif event.key in (pygame.K_UP,):
                    if self.menu_focus == 0:
                        self.menu_focus = -1
                    elif self.menu_focus > 0:
                        self.menu_focus -= 1
                elif event.key in (pygame.K_RETURN,):
                    if self.menu_focus == 0:
                        self._restart_game()
                    elif self.menu_focus == 1:
                        self._save_high_score()
                    elif self.menu_focus == 2:
                        self.state = GameState.MAIN_MENU
                        self.paused = False
                        self.menu_focus = 0
                elif self.menu_focus == -1:
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.unicode.isprintable() and len(self.player_name) < 12:
                        self.player_name += event.unicode.upper()
                return

            if self.paused:
                confirming = (
                    self.pause_view.confirming_restart
                    or self.pause_view.confirming_menu
                )
                n = 2 if confirming else 4
                if event.key in self.config.key_down:
                    self.menu_focus = (self.menu_focus + 1) % n
                elif event.key in self.config.key_up:
                    self.menu_focus = (self.menu_focus - 1) % n
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if confirming:
                        if self.menu_focus == 0:
                            if self.pause_view.confirming_restart:
                                self._restart_game()
                            else:
                                self.state = GameState.MAIN_MENU
                                self.paused = False
                                self.pause_view.confirming_menu = False
                        else:
                            self.pause_view.confirming_restart = False
                            self.pause_view.confirming_menu = False
                            self.menu_focus = 0
                    else:
                        if self.menu_focus == 0:
                            self.paused = False
                            self.menu_focus = 0
                        elif self.menu_focus == 1:
                            self.pause_view.confirming_restart = True
                            self.menu_focus = 1
                        elif self.menu_focus == 2:
                            self._open_settings()
                        elif self.menu_focus == 3:
                            self.pause_view.confirming_menu = True
                            self.menu_focus = 1
                return

            if self.fast_dropping:
                return

            if event.key in self.config.key_left:
                moved = self.engine.move_active_piece(-1, 0)
                if moved and self.pending_lock:
                    if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                        self.pending_lock = False
                    else:
                        self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_right:
                moved = self.engine.move_active_piece(1, 0)
                if moved and self.pending_lock:
                    if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                        self.pending_lock = False
                    else:
                        self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_up:
                self.engine.rotate_active_piece()
                if self.pending_lock:
                    self.lock_timer_ms = self.config.lock_delay_ms
            elif event.key in self.config.key_drop:
                while self.engine.move_active_piece(0, 1):
                    pass
                self.pending_lock = True
                self.lock_timer_ms = self.config.lock_delay_ms
                self.piece_drop_accumulator_ms = 0
                self.fast_dropping = False
                self.current_fall_delay = self.config.fall_delay
            elif event.key in self.config.key_down:
                if not self.pending_lock:
                    self.fast_dropping = True
                    self.current_fall_delay = self.config.fast_fall_delay

    def _update_vs(self, dt_ms: float) -> None:
        if self.vs_result is not None or self.ai_engine is None or self.paused:
            return

        if not self.engine.game_over:
            if self.pending_lock:
                self.lock_timer_ms -= dt_ms
                if self.lock_timer_ms <= 0:
                    self.pending_lock = False
                    self.engine.lock_piece()
                    self.fast_dropping = False
                    self.current_fall_delay = self.config.fall_delay
                    self.piece_drop_accumulator_ms = 0.0
            else:
                self.piece_drop_accumulator_ms += dt_ms
                interval = self._piece_drop_interval_ms()
                while self.piece_drop_accumulator_ms >= interval:
                    self.piece_drop_accumulator_ms -= interval
                    if self.engine.active_piece:
                        if not self.engine.move_active_piece(0, 1):
                            self.pending_lock = True
                            self.lock_timer_ms = self.config.lock_delay_ms
                            self.fast_dropping = False
                            self.current_fall_delay = self.config.fall_delay
                            break

        if not self.ai_engine.game_over:
            if self.pending_lock_ai:
                self.lock_timer_ai_ms -= dt_ms
                if self.lock_timer_ai_ms <= 0:
                    self.pending_lock_ai = False
                    self.ai_engine.lock_piece()
                    self.ai_piece_drop_accumulator_ms = 0.0
            else:
                self.ai_piece_drop_accumulator_ms += dt_ms
                ai_interval = (self.config.fall_delay / self.config.fps) * 1000.0 / 6
                while self.ai_piece_drop_accumulator_ms >= ai_interval:
                    self.ai_piece_drop_accumulator_ms -= ai_interval
                    if self.ai_engine.active_piece:
                        if not self.ai_engine.move_active_piece(0, 1):
                            self.pending_lock_ai = True
                            self.lock_timer_ai_ms = self.config.lock_delay_ms
                            break

        sand_interval = self._sand_step_interval_ms()
        self.sand_step_accumulator_ms = min(
            self.sand_step_accumulator_ms + dt_ms, sand_interval * 2
        )
        while self.sand_step_accumulator_ms >= sand_interval:
            self.sand_step_accumulator_ms -= sand_interval
            self.engine.tick(sand_interval)
            self.ai_engine.tick(sand_interval)

            if self.ai_engine.active_piece and not self.pending_lock_ai:
                self._ai_piece_ticks += 1

            # agent decides every 3rd sand tick (~10hz)
            if (
                self.ai_agent is not None
                and self.ai_engine.active_piece
                and not self.ai_engine.game_over
                and not self.pending_lock_ai
                and self._ai_piece_ticks % 3 == 0
            ):
                piece = self.ai_engine.active_piece
                obs = GameObservation(
                    grid=self.ai_engine.grid.data.copy(),
                    piece_shape=piece.name,
                    piece_color=piece.color,
                    piece_x=piece.x,
                    piece_y=piece.y,
                    piece_rotation=piece.rotation,
                    next_shape=self.ai_engine.next_shape_name,
                    next_color=self.ai_engine.next_color_id or 0,
                    score=self.ai_engine.score,
                    level=self.ai_engine.level,
                    game_over=self.ai_engine.game_over,
                )
                action = self.ai_agent.decide(obs)
                if action == Action.MOVE_LEFT:
                    self.ai_engine.move_active_piece(-1, 0)
                elif action == Action.MOVE_RIGHT:
                    self.ai_engine.move_active_piece(1, 0)
                elif action == Action.ROTATE:
                    self.ai_engine.rotate_active_piece()
                elif action == Action.HARD_DROP:
                    while self.ai_engine.move_active_piece(0, 1):
                        pass
                    self.pending_lock_ai = True
                    self.lock_timer_ai_ms = self.config.lock_delay_ms

        p_over = self.engine.game_over
        if p_over:
            self.vs_result = (
                "YOU WIN!" if self.engine.score > self.ai_engine.score else "AI WINS!"
            )
            self.menu_focus = 0

    _DAS_DELAY_MS = 150.0
    _DAS_REPEAT_MS = 50.0

    def _update_das(self, dt_ms: float) -> None:
        keys = pygame.key.get_pressed()
        left = any(keys[k] for k in self.config.key_left)
        right = any(keys[k] for k in self.config.key_right)

        if left:
            self._das_left_ms += dt_ms
            if self._das_left_ms >= self._DAS_DELAY_MS:
                reps = int((self._das_left_ms - self._DAS_DELAY_MS) / self._DAS_REPEAT_MS)
                prev = int((self._das_left_ms - dt_ms - self._DAS_DELAY_MS) / self._DAS_REPEAT_MS) if self._das_left_ms - dt_ms >= self._DAS_DELAY_MS else -1
                if reps > prev:
                    moved = self.engine.move_active_piece(-1, 0)
                    if moved and self.pending_lock:
                        if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                            self.pending_lock = False
                        else:
                            self.lock_timer_ms = self.config.lock_delay_ms
        else:
            self._das_left_ms = 0.0

        if right:
            self._das_right_ms += dt_ms
            if self._das_right_ms >= self._DAS_DELAY_MS:
                reps = int((self._das_right_ms - self._DAS_DELAY_MS) / self._DAS_REPEAT_MS)
                prev = int((self._das_right_ms - dt_ms - self._DAS_DELAY_MS) / self._DAS_REPEAT_MS) if self._das_right_ms - dt_ms >= self._DAS_DELAY_MS else -1
                if reps > prev:
                    moved = self.engine.move_active_piece(1, 0)
                    if moved and self.pending_lock:
                        if self.engine.active_piece and not self.engine._check_collision_at(self.engine.active_piece, 0, 1):
                            self.pending_lock = False
                        else:
                            self.lock_timer_ms = self.config.lock_delay_ms
        else:
            self._das_right_ms = 0.0

    def update(self, dt_ms: float) -> None:
        if self.state == GameState.PLAYER_VS_AI:
            self._update_vs(dt_ms)
            return

        if self.state != GameState.PLAYING:
            return

        if self.paused:
            return

        if not self.engine.game_over:
            if self.pending_lock:
                self.lock_timer_ms -= dt_ms
                if self.lock_timer_ms <= 0:
                    self.pending_lock = False
                    self.engine.lock_piece()
                    self.fast_dropping = False
                    self.current_fall_delay = self.config.fall_delay
                    self.piece_drop_accumulator_ms = 0.0
            else:
                self.piece_drop_accumulator_ms += dt_ms
                piece_drop_interval_ms = self._piece_drop_interval_ms()
                while self.piece_drop_accumulator_ms >= piece_drop_interval_ms:
                    self.piece_drop_accumulator_ms -= piece_drop_interval_ms
                    if self.engine.active_piece:
                        if not self.engine.move_active_piece(0, 1):
                            self.pending_lock = True
                            self.lock_timer_ms = self.config.lock_delay_ms
                            self.fast_dropping = False
                            self.current_fall_delay = self.config.fall_delay
                            break

        if not self.engine.game_over and not self.paused:
            self._update_das(dt_ms)

        if self.engine.game_over and not self._game_over_reloaded:
            self._game_over_reloaded = True
            loaded = load_persistent_data("sandtris_highscore", self.high_score_path)
            self._cached_high_score = loaded if isinstance(loaded, list) else []

        if self.engine.level > self._prev_level:
            self.level_up_timer_ms = 2000.0
            self._prev_level = self.engine.level
        if self.level_up_timer_ms > 0:
            self.level_up_timer_ms = max(0.0, self.level_up_timer_ms - dt_ms)

        sand_step_interval_ms = self._sand_step_interval_ms()
        self.sand_step_accumulator_ms = min(
            self.sand_step_accumulator_ms + dt_ms,
            sand_step_interval_ms * 2,
        )
        while self.sand_step_accumulator_ms >= sand_step_interval_ms:
            self.sand_step_accumulator_ms -= sand_step_interval_ms
            self.engine.tick(sand_step_interval_ms)

    def _make_board_surf(
        self, engine: SandtrisEngine, ghost: bool = True
    ) -> pygame.Surface:
        color_data = self._palette_lut[engine.grid.data].transpose(1, 0, 2).copy()
        if engine.active_piece and not engine.game_over:
            piece = engine.active_piece
            if ghost:
                drop = 0
                while not engine._check_collision_at(piece, 0, drop + 1):
                    drop += 1
                if drop > 0:
                    for bx, by, color in piece.get_cells():
                        gy = by + drop
                        if (
                            0 <= bx < engine.config.width
                            and 0 <= gy < engine.config.height
                            and engine.grid.data[gy, bx] == 0
                        ):
                            color_data[bx, gy] = self._palette_lut[color] // 3
            for bx, by, color in piece.get_cells():
                if 0 <= bx < engine.config.width and 0 <= by < engine.config.height:
                    color_data[bx, by] = self._palette_lut[color]
        return pygame.surfarray.make_surface(color_data)

    def draw(self) -> None:
        if self.config.headless:
            return

        if self.state == GameState.MAIN_MENU:
            self.main_menu_view.draw(
                self.screen,
                pygame.mouse.get_pos(),
                self.mouse_down,
                self.menu_focus,
                show_vs=window is None,
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
        elif self.state == GameState.HIGH_SCORES:
            self.high_scores_view.draw(
                self.screen,
                self._cached_high_score,
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
                self.player_name,
                pygame.mouse.get_pos(),
                self.mouse_down,
                self.menu_focus,
            )
            pygame.display.flip()
            return
        elif self.state == GameState.PLAYER_VS_AI:
            if self.ai_engine is not None:
                self.vs_view.draw(
                    self.screen,
                    self._make_board_surf(self.engine),
                    self._make_board_surf(self.ai_engine, ghost=False),
                    self.engine.score,
                    self.ai_engine.score,
                    self.engine.level,
                    self.ai_engine.level,
                    self.player_name,
                    self.vs_result,
                    pygame.mouse.get_pos(),
                    self.mouse_down,
                    self.menu_focus,
                    ai_dead=self.ai_engine.game_over,
                )
                if self.paused:
                    self.pause_view.draw(
                        self.screen,
                        pygame.mouse.get_pos(),
                        self.mouse_down,
                        self.menu_focus,
                    )
            pygame.display.flip()
            return

        # grid.data is (height, width); surfarray expects (width, height, 3)
        color_data = (
            self._palette_lut[self.engine.grid.data].transpose(1, 0, 2).copy()
        )

        if self.engine.active_piece and not self.engine.game_over:
            piece = self.engine.active_piece
            drop = 0
            while not self.engine._check_collision_at(piece, 0, drop + 1):
                drop += 1
            if drop > 0:
                for bx, by, color in piece.get_cells():
                    gy = by + drop
                    if (
                        0 <= bx < self.config.width
                        and 0 <= gy < self.config.height
                        and self.engine.grid.data[gy, bx] == 0
                    ):
                        color_data[bx, gy] = self._palette_lut[color] // 3

            for bx, by, color in piece.get_cells():
                if (
                    0 <= bx < self.config.width
                    and 0 <= by < self.config.height
                ):
                    color_data[bx, by] = self._palette_lut[color]

        if self.engine.flash_timer_ms > 0 and self.engine.flash_cells:
            alpha = self.engine.flash_timer_ms / 280.0
            flash_rgb = np.array([255, 240, 160], dtype=np.float32)
            cells = np.array(self.engine.flash_cells)
            xs, ys = cells[:, 0], cells[:, 1]
            valid = (
                (xs >= 0)
                & (xs < self.config.width)
                & (ys >= 0)
                & (ys < self.config.height)
            )
            xs, ys = xs[valid], ys[valid]
            orig = color_data[xs, ys].astype(np.float32)
            color_data[xs, ys] = (
                orig * (1.0 - alpha) + flash_rgb * alpha
            ).astype(np.uint8)

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
            self.engine.combo_timer_ms,
            pygame.mouse.get_pos(),
            self.mouse_down,
        )

        if self.level_up_timer_ms > 0 and not self.engine.game_over:
            t = self.level_up_timer_ms
            text_alpha = int(min((2000.0 - t) / 300.0, t / 400.0, 1.0) * 255)
            layout = self.screen_view.get_layout(self.screen.get_rect())
            level_surf = self.title_font.render(
                f"LEVEL {self.engine.level}!", True, (255, 255, 255)
            )
            level_surf.set_alpha(text_alpha)
            self.screen.blit(
                level_surf,
                level_surf.get_rect(center=layout.board_rect.center),
            )

        if self.engine.game_over:
            self.game_over_view.draw(
                self.screen,
                self.engine.score,
                self.engine.level,
                self.engine.max_combo,
                self._get_rank(),
                self.game_over_status,
                self.player_name,
                pygame.mouse.get_pos(),
                self.mouse_down,
                self.menu_focus,
            )
        elif self.paused:
            self.pause_view.draw(
                self.screen,
                pygame.mouse.get_pos(),
                self.mouse_down,
                self.menu_focus,
            )

        pygame.display.flip()

    def run(self) -> None:
        target_frame_ms = 1000.0 / self.config.fps
        while self.running:
            dt_ms = target_frame_ms
            if not self.config.headless:
                self.handle_events()
                dt_ms = float(self.clock.tick(self.config.fps))

            self.update(dt_ms)

            if not self.config.headless:
                self.draw()

        if not self.config.headless:
            pygame.quit()

    async def run_async(self) -> None:
        import asyncio

        target_frame_ms = 1000.0 / self.config.fps
        while self.running:
            dt_ms = target_frame_ms
            if not self.config.headless:
                self.handle_events()
                self._sync_window_size()
                dt_ms = float(self.clock.tick(self.config.fps))

            self.update(dt_ms)

            if not self.config.headless:
                self.draw()

            await asyncio.sleep(0)

        if not self.config.headless:
            pygame.quit()
