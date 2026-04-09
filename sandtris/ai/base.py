from dataclasses import dataclass
from enum import Enum, auto

import numpy as np


class Action(Enum):
    NONE = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    ROTATE = auto()
    SOFT_DROP = auto()
    HARD_DROP = auto()


@dataclass
class GameObservation:
    grid: np.ndarray        # shape (height, width), dtype uint8 — copy of engine.grid.data
    piece_shape: str | None  # piece.name
    piece_x: int
    piece_y: int
    piece_rotation: int
    next_shape: str | None
    score: int
    level: int
    game_over: bool


class AgentBase:
    def reset(self) -> None:
        """Called at the start of each game."""

    def decide(self, obs: GameObservation) -> Action:
        """Return the next action given the current observation."""
        raise NotImplementedError
