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

from sandtris.ai.base import Action, AgentBase, GameObservation
from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine


class SandtrisEnv:
    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0

    def reset(self) -> GameObservation:
        self.engine = SandtrisEngine(self.config)
        self._prev_score = 0
        return self._observe()

    def step(self, action: Action) -> tuple[GameObservation, float, bool]:
        if action == Action.MOVE_LEFT:
            self.engine.move_active_piece(-1, 0)
        elif action == Action.MOVE_RIGHT:
            self.engine.move_active_piece(1, 0)
        elif action == Action.ROTATE:
            self.engine.rotate_active_piece()
        elif action == Action.SOFT_DROP:
            self.engine.move_active_piece(0, 1)
        elif action == Action.HARD_DROP:
            while self.engine.move_active_piece(0, 1):
                pass
            self.engine.lock_piece()

        self.engine.tick()

        reward = (self.engine.score - self._prev_score) / 100.0
        self._prev_score = self.engine.score
        if self.engine.game_over:
            reward -= 1.0

        return self._observe(), reward, self.engine.game_over

    def _observe(self) -> GameObservation:
        piece = self.engine.active_piece
        return GameObservation(
            grid=self.engine.grid.data.copy(),
            piece_shape=piece.name if piece else None,
            piece_x=piece.x if piece else 0,
            piece_y=piece.y if piece else 0,
            piece_rotation=0,
            next_shape=self.engine.next_shape_name,
            score=self.engine.score,
            level=self.engine.level,
            game_over=self.engine.game_over,
        )
