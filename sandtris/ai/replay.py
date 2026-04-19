from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

import numpy as np
import torch

from sandtris.ai.dqn import grids_to_tensor


@dataclass(frozen=True, slots=True)
class Transition:
    state: np.ndarray       # (H, W) uint8 — base color 0-7, compact storage
    piece_info: np.ndarray  # (6,) float32
    action: int
    reward: float
    next_state: np.ndarray
    next_piece_info: np.ndarray
    done: bool


@dataclass(slots=True)
class Batch:
    states: torch.Tensor       # (B, 7, H, W) float32
    piece_infos: torch.Tensor  # (B, 6)
    actions: torch.Tensor      # (B,) long
    rewards: torch.Tensor      # (B,) float
    next_states: torch.Tensor  # (B, 7, H, W) float32
    next_piece_infos: torch.Tensor
    dones: torch.Tensor        # (B,) bool


class ReplayBuffer:
    def __init__(self, capacity: int = 100_000) -> None:
        self._buf: deque[Transition] = deque(maxlen=capacity)

    def push(self, transition: Transition) -> None:
        self._buf.append(transition)

    def sample(self, batch_size: int, device: torch.device) -> Batch:
        transitions = random.sample(self._buf, batch_size)
        # grids stored as (H,W) uint8 → expand to (B,7,H,W) float32 here
        states_np = np.stack([t.state for t in transitions])
        next_states_np = np.stack([t.next_state for t in transitions])
        return Batch(
            states=grids_to_tensor(states_np, device),
            piece_infos=torch.from_numpy(
                np.stack([t.piece_info for t in transitions])
            ).to(device),
            actions=torch.tensor(
                [t.action for t in transitions], dtype=torch.long, device=device
            ),
            rewards=torch.tensor(
                [t.reward for t in transitions], dtype=torch.float32, device=device
            ),
            next_states=grids_to_tensor(next_states_np, device),
            next_piece_infos=torch.from_numpy(
                np.stack([t.next_piece_info for t in transitions])
            ).to(device),
            dones=torch.tensor(
                [t.done for t in transitions], dtype=torch.bool, device=device
            ),
        )

    def __len__(self) -> int:
        return len(self._buf)
