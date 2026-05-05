from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from sandtris.ai.base import GameObservation

MAX_PLACEMENTS = 320  # 4 rotations × 80 cols (scale=8 upper bound)
N_COLOR_CHANNELS = 7  # one binary channel per sand color

SHAPE_NAMES = ["I", "J", "L", "O", "S", "T", "Z"]
_SHAPE_TO_ID: dict[str, int] = {name: i for i, name in enumerate(SHAPE_NAMES)}


def obs_to_arrays(obs: GameObservation) -> tuple[np.ndarray, np.ndarray]:
    """Convert observation to compact numpy arrays for replay buffer storage.

    Returns:
        grid:       (H, W) uint8 — base color 0-7 (val%10)
        piece_info: (4,) float32 — [shape_id/6, rotation/3, color/7, next_color/7]
    """
    grid = (obs.grid % 10).astype(np.uint8)
    shape_id = _SHAPE_TO_ID.get(obs.piece_shape or "I", 0) / 6.0
    rotation = obs.piece_rotation / 3.0
    color = obs.piece_color / 7.0
    next_color = obs.next_color / 7.0
    piece_info = np.array(
        [shape_id, rotation, color, next_color],
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
    """CNN + piece embedding → Q-values for each placement."""

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
            nn.MaxPool2d(2),               # (B,64,40,20) → (B,64,20,10)
            nn.Flatten(),                  # 64*20*10 = 12800
            nn.Linear(12800, 256),
            nn.ReLU(),
        )
        self.piece_head = nn.Sequential(
            nn.Linear(4, 32),  # shape_id, rotation, color, next_color
            nn.ReLU(),
        )
        self.q_head = nn.Sequential(
            nn.Linear(256 + 32, 128),
            nn.ReLU(),
            nn.Linear(128, MAX_PLACEMENTS),
        )

    def forward(
        self, grid: torch.Tensor, piece_info: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            grid:       (B, 7, H, W) float32
            piece_info: (B, 4)       float32

        Returns:
            q_values: (B, MAX_PLACEMENTS) float32
        """
        return self.q_head(
            torch.cat([self.cnn(grid), self.piece_head(piece_info)], dim=1)
        )

    @torch.no_grad()
    def act(
        self, obs: GameObservation, n_placements: int, device: torch.device
    ) -> int:
        """Greedy placement index, masking positions beyond n_placements."""
        grid_arr, piece_arr = obs_to_arrays(obs)
        grid_t = grids_to_tensor(grid_arr[np.newaxis], device)
        piece_t = torch.from_numpy(piece_arr).unsqueeze(0).to(device)
        q = self.forward(grid_t, piece_t)
        q[0, n_placements:] = -float("inf")
        return int(q.argmax(dim=1).item())

    @torch.no_grad()
    def act_batch(
        self,
        obses: list[GameObservation],
        n_placements_list: list[int],
        device: torch.device,
    ) -> list[int]:
        """Batched greedy action selection — single forward pass for all observations."""
        arrays = [obs_to_arrays(obs) for obs in obses]
        grids = np.stack([a[0] for a in arrays])
        pieces = np.stack([a[1] for a in arrays])
        grid_t = grids_to_tensor(grids, device)
        piece_t = torch.from_numpy(pieces).to(device)
        q = self.forward(grid_t, piece_t)
        for i, n in enumerate(n_placements_list):
            q[i, n:] = -float("inf")
        return q.argmax(dim=1).tolist()
