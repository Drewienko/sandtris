import pygame
import numpy as np
from sandtris.core.engine import SandtrisEngine
from sandtris.core.config import GameConfig

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


class PygameRunner:
    def __init__(
        self,
        config: GameConfig,
        engine: SandtrisEngine | None = None,
    ) -> None:
        self.config = config
        self.engine = engine or SandtrisEngine(config)

        if not self.config.headless:
            pygame.init()
            self.screen = pygame.display.set_mode((400, 800))
            pygame.display.set_caption("Sandtris")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont(None, 36)
            pygame.key.set_repeat(200, 50)

        self.fall_timer = 0
        self.current_fall_delay = self.config.fall_delay
        self.running = True
        self.fast_dropping = False
        self.paused = False

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                    continue

                if self.paused:
                    continue

                if self.fast_dropping:
                    continue

                if event.key == pygame.K_LEFT:
                    self.engine.move_active_piece(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.engine.move_active_piece(1, 0)
                elif event.key == pygame.K_UP:
                    self.engine.rotate_active_piece()
                elif event.key in (pygame.K_DOWN, pygame.K_SPACE):
                    self.fast_dropping = True
                    self.current_fall_delay = self.config.fast_fall_delay

    def update(self) -> None:
        if self.paused:
            return

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
        surf = pygame.transform.scale(
            surf,
            self.screen.get_size(),
        )

        self.screen.blit(surf, (0, 0))

        score_surface = self.font.render(
            f"Score: {self.engine.score}", True, (255, 255, 255)
        )
        fps_surface = self.font.render(
            f"FPS: {int(self.clock.get_fps())}", True, (255, 255, 255)
        )

        self.screen.blit(score_surface, (10, 10))
        self.screen.blit(fps_surface, (10, 40))

        if self.engine.combo > 1:
            combo_surface = self.font.render(
                f"Combo: {self.engine.combo}x", True, (255, 255, 0)
            )
            self.screen.blit(combo_surface, (10, 70))

        if self.paused:
            paused_surface = self.font.render("Paused", True, (255, 255, 255))
            paused_rect = paused_surface.get_rect(
                center=self.screen.get_rect().center
            )
            self.screen.blit(paused_surface, paused_rect)

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
