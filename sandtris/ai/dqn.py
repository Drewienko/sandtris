from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from sandtris.ai.base import Action, GameObservation

# Reduced action space — NONE and SOFT_DROP excluded
TRAIN_ACTIONS: list[Action] = [
    Action.MOVE_LEFT,
    Action.MOVE_RIGHT,
    Action.ROTATE,
    Action.HARD_DROP,
]
N_ACTIONS = len(TRAIN_ACTIONS)
N_COLOR_CHANNELS = 7  # one binary channel per sand color

SHAPE_NAMES = ["I", "J", "L", "O", "S", "T", "Z"]
_SHAPE_TO_ID: dict[str, int] = {name: i for i, name in enumerate(SHAPE_NAMES)}


def obs_to_arrays(obs: GameObservation) -> tuple[np.ndarray, np.ndarray]:
    """Convert observation to compact numpy arrays for replay buffer storage.

    Returns:
        grid:       (H, W) uint8 — base color 0-7 (val%10); stored compact, expanded to
                    7 binary channels only when feeding the network (see grids_to_tensor)
        piece_info: (6,) float32 — [shape_id/6, rotation/3, color/7, next_color/7,
                    piece_x/W, piece_y/H]
    """
    grid = (obs.grid % 10).astype(np.uint8)
    h, w = grid.shape
    shape_id = _SHAPE_TO_ID.get(obs.piece_shape or "I", 0) / 6.0
    rotation = obs.piece_rotation / 3.0
    color = obs.piece_color / 7.0
    next_color = obs.next_color / 7.0
    piece_x = obs.piece_x / max(w - 1, 1)
    piece_y = obs.piece_y / max(h - 1, 1)
    piece_info = np.array(
        [shape_id, rotation, color, next_color, piece_x, piece_y],
        dtype=np.float32,
    )
    return grid, piece_info


def grids_to_tensor(grids: np.ndarray, device: torch.device) -> torch.Tensor:
    """(B, H, W) uint8 → (B, 7, H, W) float32 — one binary channel per color."""
    channels = np.stack(
        [(grids == c).astype(np.float32) for c in range(1, N_COLOR_CHANNELS + 1)],
        axis=1,
    )
    return torch.from_numpy(channels).to(device)


class SandtrisNet(nn.Module):
    """CNN + piece embedding → Q-values for each action."""

    def __init__(self) -> None:
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(N_COLOR_CHANNELS, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((8, 8)),
            nn.Flatten(),                  # 64*8*8 = 4096
            nn.Linear(4096, 256),
            nn.ReLU(),
        )
        self.piece_head = nn.Sequential(
            nn.Linear(6, 32),  # shape, rotation, color, next_color, piece_x, piece_y
            nn.ReLU(),
        )
        self.q_head = nn.Sequential(
            nn.Linear(256 + 32, 128),
            nn.ReLU(),
            nn.Linear(128, N_ACTIONS),
        )

    def forward(
        self, grid: torch.Tensor, piece_info: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            grid:       (B, 7, H, W) float32
            piece_info: (B, 6)       float32

        Returns:
            q_values: (B, N_ACTIONS) float32
        """
        return self.q_head(
            torch.cat([self.cnn(grid), self.piece_head(piece_info)], dim=1)
        )

    @torch.no_grad()
    def act(self, obs: GameObservation, device: torch.device) -> int:
        """Greedy action index from a single observation."""
        grid_arr, piece_arr = obs_to_arrays(obs)
        grid_t = grids_to_tensor(grid_arr[np.newaxis], device)  # (1, 7, H, W)
        piece_t = torch.from_numpy(piece_arr).unsqueeze(0).to(device)  # (1, 6)
        return int(self.forward(grid_t, piece_t).argmax(dim=1).item())
