import pygame
import numpy as np
from pathlib import Path
from enum import Enum, auto

from sandtris.core.engine import SandtrisEngine
from sandtris.core.config import GameConfig
from sandtris.render.gameplay_screen import GameplayScreen
from sandtris.render.pause_screen import PauseScreen
from sandtris.render.game_over_screen import GameOverScreen
from sandtris.render.main_menu_screen import MainMenuScreen
from sandtris.render.how_to_play_screen import HowToPlayScreen

COLOR_PALETTE = {
    0: (20, 20, 30),
    1: (0, 255, 255),
    2: (0, 0, 255),
    3: (255, 165, 0),
    4: (255, 255, 0),
    5: (0, 255, 0),
    6: (128, 0, 128),
    7: (255, 0, 0),
}

for i in range(1, 8):
    r, g, b = COLOR_PALETTE[i]
    COLOR_PALETTE[i + 10] = (
        max(0, r - 80),
        max(0, g - 80),
        max(0, b - 80),
    )


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

        if not self.config.headless:
            pygame.init()
            self.screen = pygame.display.set_mode((720, 900), pygame.RESIZABLE)
            pygame.display.set_caption("Sandtris")
            self.clock = pygame.time.Clock()
            font_path = (
                Path(__file__).parent.parent.parent
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
            self.main_menu_view = MainMenuScreen(
                self.title_font, self.body_font
            )
            self.how_to_play_view = HowToPlayScreen(
                self.title_font, self.body_font
            )
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
            elif self.state == GameState.HOW_TO_PLAY:
                self._handle_how_to_play_events(event)

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

    def _handle_main_menu_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse_down = True
            screen_rect = self.screen.get_rect()
            if self.main_menu_view.play_button_contains(
                screen_rect, event.pos
            ):
                self.engine = SandtrisEngine(self.config)
                self.state = GameState.PLAYING
                self.paused = False
                self.fast_dropping = False
                self.current_fall_delay = self.config.fall_delay
            elif self.main_menu_view.settings_button_contains(
                screen_rect, event.pos
            ):
                print("GO TO SETTINGS")
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
                    self.engine = SandtrisEngine(self.config)
                    self.paused = False
                    self.fast_dropping = False
                    self.current_fall_delay = self.config.fall_delay
                    return
                if self.game_over_view.save_button_contains(
                    screen_rect, event.pos
                ):
                    print("SAVE SCORE CLICKED")
                    return
                if self.game_over_view.menu_button_contains(
                    screen_rect, event.pos
                ):
                    self.state = GameState.MAIN_MENU
                    return
            elif self.paused:
                if self.pause_view.yes_button_contains(screen_rect, event.pos):
                    if self.pause_view.confirming_restart:
                        self.engine = SandtrisEngine(self.config)
                        self.paused = False
                        self.fast_dropping = False
                        self.current_fall_delay = self.config.fall_delay
                        self.pause_view.confirming_restart = False
                    elif self.pause_view.confirming_menu:
                        self.state = GameState.MAIN_MENU
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
                    print("SETTINGS CLICKED")
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
            if event.key == self.config.key_pause:
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

            if event.key == self.config.key_left:
                self.engine.move_active_piece(-1, 0)
            elif event.key == self.config.key_right:
                self.engine.move_active_piece(1, 0)
            elif event.key == self.config.key_up:
                self.engine.rotate_active_piece()
            elif event.key in (self.config.key_down, self.config.key_drop):
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

        color_data = np.zeros(
            (self.config.width, self.config.height, 3), dtype=np.uint8
        )
        color_data[:, :] = COLOR_PALETTE[0]

        for y in range(self.config.height):
            for x in range(self.config.width):
                val = self.engine.grid.data[y, x]
                if val > 0:
                    color_data[x, y] = COLOR_PALETTE[val]

        if self.engine.active_piece:
            for bx, by, color in self.engine.active_piece.get_cells():
                if (
                    0 <= bx < self.config.width
                    and 0 <= by < self.config.height
                ):
                    color_data[bx, by] = COLOR_PALETTE[color]

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
            COLOR_PALETTE,
            pygame.mouse.get_pos(),
            self.mouse_down,
        )

        if self.engine.game_over:
            self.game_over_view.draw(
                self.screen,
                self.engine.score,
                self.engine.level,
                self.engine.max_combo,
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

    def run(self) -> None:
        while self.running:
            if not self.config.headless:
                self.handle_events()

            self.update()

            if not self.config.headless:
                self.draw()
                self.clock.tick(self.config.fps)

        if not self.config.headless:
            pygame.quit()
