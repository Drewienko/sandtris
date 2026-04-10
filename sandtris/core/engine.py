import random

from .grid import Grid
from .config import GameConfig
from .pieces import PIECE_COLOR_IDS, SHAPES, Tetromino


class SandtrisEngine:
    active_piece: Tetromino | None
    next_shape_name: str | None
    next_color_id: int | None

    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.grid = Grid(config.width, config.height, config.diagonal_prob)
        self.active_piece: Tetromino | None = None
        self.next_shape_name: str | None = None
        self.next_color_id: int | None = None
        self.game_over = False
        self.score = 0
        self.combo = 1
        self.combo_timer_ms = 0.0
        self.max_combo = 1
        self.level = 1
        self.pieces_placed = 0
        self.pixels_cleared = 0
        self.flash_cells: list[tuple[int, int]] = []
        self.flash_timer_ms: float = 0.0
        self.spawn_piece()

    def _roll_next_piece(self) -> None:
        self.next_shape_name = random.choice(list(SHAPES.keys()))
        self.next_color_id = random.choice(PIECE_COLOR_IDS)

    def _get_spawn_position(self, shape_name: str) -> tuple[int, int]:
        base_shape = SHAPES[shape_name]
        piece_width = base_shape.shape[1] * self.config.scale
        start_x = (self.grid.width - piece_width) // 2
        start_y = 0
        return start_x, start_y

    def _create_piece(self, shape_name: str, color_id: int) -> Tetromino:
        start_x, start_y = self._get_spawn_position(shape_name)
        return Tetromino(
            shape_name,
            start_x,
            start_y,
            color_id,
            scale=self.config.scale,
        )

    def check_game_over(self) -> bool:
        if self.active_piece is not None:
            self.game_over = self._check_collision(self.active_piece)
            return self.game_over

        if self.next_shape_name is None or self.next_color_id is None:
            self._roll_next_piece()

        assert self.next_shape_name is not None
        assert self.next_color_id is not None

        test_piece = self._create_piece(
            self.next_shape_name, self.next_color_id
        )
        self.game_over = self._check_collision(test_piece)
        return self.game_over

    def spawn_piece(self) -> None:
        if self.next_shape_name is None or self.next_color_id is None:
            self._roll_next_piece()

        assert self.next_shape_name is not None
        assert self.next_color_id is not None

        shape_name = self.next_shape_name
        color_id = self.next_color_id
        self.active_piece = self._create_piece(shape_name, color_id)

        self._roll_next_piece()
        self.check_game_over()

    def _check_collision(self, piece: Tetromino) -> bool:
        for x, y, _ in piece.get_cells():
            if self.grid.is_occupied(x, y):
                return True
        return False

    def _check_collision_at(self, piece: Tetromino, dx: int, dy: int) -> bool:
        for x, y, _ in piece.get_cells():
            if self.grid.is_occupied(x + dx, y + dy):
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

        self.pieces_placed += 1
        self.active_piece = None
        self.spawn_piece()

    def tick(self, dt_ms: float | None = None) -> None:
        if self.game_over:
            return

        if dt_ms is None:
            dt_ms = 1000.0 / self.config.fps

        self.grid.update_sand()

        if self.flash_timer_ms > 0:
            self.flash_timer_ms = max(0.0, self.flash_timer_ms - dt_ms)
            if self.flash_timer_ms == 0.0:
                self.flash_cells = []

        if self.combo_timer_ms > 0:
            self.combo_timer_ms = max(0.0, self.combo_timer_ms - dt_ms)
            if self.combo_timer_ms == 0.0:
                self.combo = 1

        cleared_pixels, connections = self.grid.check_line_clears()
        if cleared_pixels > 0:
            self.pixels_cleared += cleared_pixels
            self.score += (250 * connections + cleared_pixels) * self.combo
            self.combo = min(10, self.combo + 1)
            self.max_combo = max(self.max_combo, self.combo)
            self.level = (self.score // 2000) + 1
            self.combo_timer_ms = max(500.0, 3000.0 / self.level)
            self.flash_cells = self.grid.last_cleared
            self.flash_timer_ms = 280.0
