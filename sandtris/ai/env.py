"""
Headless Sandtris environment for RL training.

Usage:
    env = SandtrisEnv()
    obs = env.reset()
    while True:
        action = agent.decide(obs)
        obs, reward, done = env.step(action)
        if done:
            break
"""

import numpy as np
from scipy.ndimage import label

from sandtris.ai.base import Action, GameObservation
from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine

_CONNECTIVITY = np.ones((3, 3), dtype=int)  # 8-connected, matches BFS in grid.py


def _bfs_reach(data: np.ndarray) -> float:
    """For each color, find connected components touching the left wall (col 0)
    and measure how far right they reach. Returns avg max-reach across colors,
    normalized to [0, 1]. Reaches 1.0 only when a component spans wall-to-wall
    (i.e. a line clear is imminent / just happened).
    """
    h, w = data.shape
    base = (data % 10).astype(np.uint8)
    total = 0.0
    for color in range(1, 8):
        mask = base == color
        if not mask[:, 0].any():
            continue  # nothing on left wall for this color
        labeled, _ = label(mask, structure=_CONNECTIVITY)
        left_labels = set(labeled[:, 0]) - {0}
        if not left_labels:
            continue
        max_col = 0
        for lbl in left_labels:
            cols = np.where((labeled == lbl).any(axis=0))[0]
            if len(cols):
                max_col = max(max_col, cols[-1])
        total += max_col / (w - 1)
    return total / 7.0


def _aggregate_height(data: np.ndarray) -> int:
    occupied = data > 0
    col_heights = np.where(
        occupied.any(axis=0),
        data.shape[0] - occupied.argmax(axis=0),
        0,
    ).astype(np.int32)
    return int(col_heights.sum())


class SandtrisEnv:
    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0
        self._prev_pieces = 0
        self._prev_height = 0
        self._prev_reach = 0.0
        self._settle_ticks = round(
            self.config.lock_delay_ms * self.config.fps / 1000
        )

    def reset(self) -> GameObservation:
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0
        self._prev_pieces = 0
        self._prev_height = _aggregate_height(self.engine.grid.data)
        self._prev_reach = _bfs_reach(self.engine.grid.data)
        return self._observe()

    def _lock_and_settle(self) -> None:
        self.engine.lock_piece()
        for _ in range(self._settle_ticks):
            self.engine.tick()

    def _lock_reward(self) -> float:
        """Shaping reward computed once per piece placed."""
        data = self.engine.grid.data
        area = data.size
        height = _aggregate_height(data)
        reach = _bfs_reach(data)

        r = 0.0
        r -= (height - self._prev_height) / area * 2.0
        r += (reach - self._prev_reach) * 5.0  # reward extending wall-to-wall reach

        self._prev_height = height
        self._prev_reach = reach
        return r

    def step(self, action: Action) -> tuple[GameObservation, float, bool]:
        if action == Action.MOVE_LEFT:
            self.engine.move_active_piece(-1, 0)
        elif action == Action.MOVE_RIGHT:
            self.engine.move_active_piece(1, 0)
        elif action == Action.ROTATE:
            self.engine.rotate_active_piece()
        elif action == Action.SOFT_DROP:
            moved = self.engine.move_active_piece(0, 1)
            if not moved:
                self._lock_and_settle()
        elif action == Action.HARD_DROP:
            while self.engine.move_active_piece(0, 1):
                pass
            self._lock_and_settle()

        # gravity: advance piece 1 row every step; lock when it lands
        if (
            action not in (Action.SOFT_DROP, Action.HARD_DROP)
            and self.engine.active_piece is not None
            and not self.engine.game_over
        ):
            if not self.engine.move_active_piece(0, 1):
                self._lock_and_settle()

        self.engine.tick()

        reward = (self.engine.score - self._prev_score) / 20.0  # 5x stronger clear signal
        self._prev_score = self.engine.score

        reward -= 0.001  # per-step survival cost

        if self.engine.pieces_placed != self._prev_pieces:
            reward += 0.1
            reward += self._lock_reward()
            self._prev_pieces = self.engine.pieces_placed

        if self.engine.game_over:
            reward -= 1.0

        return self._observe(), reward, self.engine.game_over

    def _observe(self) -> GameObservation:
        piece = self.engine.active_piece
        return GameObservation(
            grid=self.engine.grid.data.copy(),
            piece_shape=piece.name if piece else None,
            piece_color=piece.color if piece else 0,
            piece_x=piece.x if piece else 0,
            piece_y=piece.y if piece else 0,
            piece_rotation=piece.rotation if piece else 0,
            next_shape=self.engine.next_shape_name,
            next_color=self.engine.next_color_id or 0,
            score=self.engine.score,
            level=self.engine.level,
            game_over=self.engine.game_over,
        )
