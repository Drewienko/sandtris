"""
Headless Sandtris environment for RL training.

Usage:
    env = SandtrisEnv()
    obs = env.reset()
    while True:
        action_idx = agent.decide(obs, env.n_placements)
        obs, reward, done = env.step(action_idx)
        if done:
            break
"""

from typing import cast

import numpy as np

from sandtris.ai.base import GameObservation
from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine
from sandtris.core.pieces import Tetromino

_CONNECTIVITY = np.ones((3, 3), dtype=int)  # 8-connected, matches BFS in grid.py

_NEIGHBOR_OFFSETS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def _best_span_per_color(data: np.ndarray) -> np.ndarray:
    """Max horizontal span of best connected component per color.

    Returns shape-(7,) float64, one entry per color 1-7, normalized to [0,1].
    Colors with no sand return 0.0.
    """
    from scipy.ndimage import label  # lazy: not available on web/WASM
    _, w = data.shape
    base = (data % 10).astype(np.uint8)
    spans = np.zeros(7, dtype=np.float64)
    for color in range(1, 8):
        mask = base == color
        if not mask.any():
            continue
        labeled, n = cast(
            tuple[np.ndarray, int], label(mask, structure=_CONNECTIVITY)
        )
        for lbl in range(1, n + 1):
            cols = np.where((labeled == lbl).any(axis=0))[0]
            if len(cols) >= 2:
                spans[color - 1] = max(
                    spans[color - 1], (cols[-1] - cols[0]) / (w - 1)
                )
    return spans


def _reach_max_span(data: np.ndarray) -> float:
    """Best span across all colors and components. [0, 1]"""
    return float(_best_span_per_color(data).max())


def _reach_avg_span(data: np.ndarray) -> float:
    """Average best span across all 7 colors. [0, 1]"""
    return float(_best_span_per_color(data).mean())


def _reach_surface_span(data: np.ndarray) -> float:
    """Max span of the topmost component per color. Buried components ignored. [0, 1]"""
    from scipy.ndimage import label  # lazy: not available on web/WASM
    _, w = data.shape
    base = (data % 10).astype(np.uint8)
    best = 0.0
    for color in range(1, 8):
        mask = base == color
        if not mask.any():
            continue
        labeled, n = cast(
            tuple[np.ndarray, int], label(mask, structure=_CONNECTIVITY)
        )
        top_lbl, top_row = 0, data.shape[0]
        for lbl in range(1, n + 1):
            rows = np.where((labeled == lbl).any(axis=1))[0]
            if len(rows) and rows[0] < top_row:
                top_row = rows[0]
                top_lbl = lbl
        if top_lbl:
            cols = np.where((labeled == top_lbl).any(axis=0))[0]
            if len(cols) >= 2:
                best = max(best, (cols[-1] - cols[0]) / (w - 1))
    return best


def _aggregate_height(data: np.ndarray) -> int:
    occupied = data > 0
    col_heights = np.where(
        occupied.any(axis=0),
        data.shape[0] - occupied.argmax(axis=0),
        0,
    ).astype(np.int32)
    return int(col_heights.sum())


def compute_placements(engine: SandtrisEngine) -> list[tuple[int, int]]:
    """All legal (rotation, col) pairs for the active piece in engine."""
    piece = engine.active_piece
    if piece is None:
        return []
    placements: list[tuple[int, int]] = []
    w = engine.grid.width
    seen_shapes: set[bytes] = set()
    for rot in range(4):
        clone = Tetromino(piece.name, 0, piece.y, piece.color, piece.scale)
        clone.rotate(times=rot)
        shape_key = clone.shape.tobytes()
        if shape_key in seen_shapes:
            continue
        seen_shapes.add(shape_key)
        for col in range(w):
            clone.x = col
            if not engine._check_collision(clone):
                placements.append((rot, col))
    return placements


class SandtrisEnv:
    def __init__(
        self,
        config: GameConfig | None = None,
        reach_variant: str = "max_span",
        settle_ticks: int = 0,
    ) -> None:
        self.config = config or GameConfig()
        self.reach_variant = reach_variant
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0
        self._prev_height = 0
        self._prev_reach = 0.0
        self._settle_ticks = settle_ticks
        match reach_variant:
            case "max_span":
                self._reach_fn = _reach_max_span
            case "avg_span":
                self._reach_fn = _reach_avg_span
            case "surface_span":
                self._reach_fn = _reach_surface_span
            case _:
                raise ValueError(f"unknown reach_variant: {reach_variant!r}")
        self._placements: list[tuple[int, int]] = []

    @property
    def n_placements(self) -> int:
        return len(self._placements)

    def reset(self) -> GameObservation:
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0
        self._prev_height = _aggregate_height(self.engine.grid.data)
        self._prev_reach = self._reach_fn(self.engine.grid.data)
        self._placements = self._compute_placements()
        return self._observe()

    def _compute_placements(self) -> list[tuple[int, int]]:
        return compute_placements(self.engine)

    def _lock_and_settle(self) -> None:
        self.engine.lock_piece()
        for _ in range(self._settle_ticks):
            self.engine.grid.update_sand()

    def _color_match_bonus(
        self, data_before: np.ndarray, data_after: np.ndarray
    ) -> float:
        """Bonus for new sand cells landing adjacent to pre-existing same-color sand.

        Uses data_before for neighbor lookup so intra-piece adjacency is excluded.
        Normalized by grid area so the signal is scale-independent.
        """
        new_mask = (data_after != 0) & (data_before == 0)
        if not new_mask.any():
            return 0.0
        h, w = data_after.shape
        base_new = (data_after % 10).astype(np.uint8)
        base_old = (data_before % 10).astype(np.uint8)
        count = 0
        for dy, dx in _NEIGHBOR_OFFSETS:
            src_r = slice(max(0, dy),  h + min(0, dy))
            dst_r = slice(max(0, -dy), h - max(0, dy))
            src_c = slice(max(0, dx),  w + min(0, dx))
            dst_c = slice(max(0, -dx), w - max(0, dx))
            old_neighbor = np.zeros_like(base_old)
            old_neighbor[dst_r, dst_c] = base_old[src_r, src_c]
            same = (base_new == old_neighbor) & (old_neighbor != 0)
            count += int(np.count_nonzero(new_mask & same))
        return count / (h * w) * 16.0

    def _lock_reward(self, data_before: np.ndarray) -> float:
        """Shaping reward computed once per piece placed."""
        data = self.engine.grid.data
        area = data.size
        height = _aggregate_height(data)
        reach = self._reach_fn(data)

        r = 0.0
        r -= (height - self._prev_height) / area * 2.0
        r += (reach - self._prev_reach) * 5.0
        r += self._color_match_bonus(data_before, data)

        self._prev_height = height
        self._prev_reach = reach
        return r

    def step(self, placement_idx: int) -> tuple[GameObservation, float, bool]:
        rot, col = self._placements[placement_idx]
        piece = self.engine.active_piece
        assert piece is not None
        piece.rotate(times=rot)
        piece.x = col
        while self.engine.move_active_piece(0, 1):
            pass
        data_before = self.engine.grid.data.copy()
        self._lock_and_settle()
        self.engine.tick()

        reward = (self.engine.score - self._prev_score) / 20.0
        self._prev_score = self.engine.score
        reward += 0.1  # per-piece alive bonus
        reward += self._lock_reward(data_before)

        if self.engine.game_over:
            reward -= 1.0

        self._placements = self._compute_placements()
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
