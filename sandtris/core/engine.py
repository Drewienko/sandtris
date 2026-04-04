import random

from .grid import Grid
from .config import GameConfig
from .pieces import PIECE_COLOR_IDS, SHAPES, Tetromino


class SandtrisEngine:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.grid = Grid(config.width, config.height)
        self.active_piece: Tetromino | None = None
        self.game_over = False
        self.score = 0
        self.combo = 1
        self.combo_timer = 0
        self.spawn_piece()

    def spawn_piece(self) -> None:
        shape_name = random.choice(list(SHAPES.keys()))
        color_id = random.choice(PIECE_COLOR_IDS)
        base_shape = SHAPES[shape_name]
        piece_width = base_shape.shape[1] * self.config.scale
        start_x = (self.grid.width - piece_width) // 2
        start_y = 0

        self.active_piece = Tetromino(
            shape_name,
            start_x,
            start_y,
            color_id,
            scale=self.config.scale,
        )

        if self._check_collision(self.active_piece):
            self.game_over = True

    def _check_collision(self, piece: Tetromino) -> bool:
        for x, y, _ in piece.get_cells():
            if self.grid.is_occupied(x, y):
                return True
        return False

    def move_active_piece(self, dx: int, dy: int) -> bool:
        if not self.active_piece or self.game_over:
            return False

        self.active_piece.x += dx
        self.active_piece.y += dy

        if self._check_collision(self.active_piece):
            self.active_piece.x -= dx
            self.active_piece.y -= dy
            return False

        return True

    def rotate_active_piece(self) -> None:
        if not self.active_piece or self.game_over:
            return

        self.active_piece.rotate()

        if self._check_collision(self.active_piece):
            self.active_piece.rotate(times=3)

    def lock_piece(self) -> None:
        if not self.active_piece:
            return

        for x, y, color in self.active_piece.get_cells():
            self.grid.add_sand(x, y, color)

        self.active_piece = None
        self.spawn_piece()

    def tick(self) -> None:
        if self.game_over:
            return

        self.grid.update_sand()

        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 1

        cleared_pixels = self.grid.check_line_clears()
        if cleared_pixels > 0:
            self.score += cleared_pixels * self.combo
            self.combo = min(10, self.combo + 1)
            self.combo_timer = self.config.fps * 3
