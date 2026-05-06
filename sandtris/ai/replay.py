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
    piece_info: np.ndarray  # (4,) float32 — [shape_id, rotation, color, next_color]
    action: int
    reward: float
    next_state: np.ndarray
    next_piece_info: np.ndarray
    done: bool


@dataclass(slots=True)
class Batch:
    states: torch.Tensor       # (B, 7, H, W) float32
    piece_infos: torch.Tensor  # (B, 4)
    actions: torch.Tensor      # (B,) long
    rewards: torch.Tensor      # (B,) float
    next_states: torch.Tensor  # (B, 7, H, W) float32
    next_piece_infos: torch.Tensor
    dones: torch.Tensor        # (B,) bool
    indices: np.ndarray | None = None   # PER sample indices
    weights: torch.Tensor | None = None  # PER importance-sampling weights


class NStepBuffer:
    """Accumulates n transitions, folds rewards into a single n-step transition."""

    def __init__(self, n: int = 5, gamma: float = 0.99) -> None:
        self.n = n
        self.gamma = gamma
        self._buf: deque[Transition] = deque()

    def push(self, transition: Transition) -> Transition | None:
        self._buf.append(transition)
        if transition.done:
            result = self._flush_all()
            self._buf.clear()
            return result
        if len(self._buf) < self.n:
            return None
        return self._flush_one()

    def _fold(self, transitions: deque[Transition], done: bool) -> Transition:
        G = sum(self.gamma**i * t.reward for i, t in enumerate(transitions))
        t0, tn = transitions[0], transitions[-1]
        return Transition(t0.state, t0.piece_info, t0.action, G,
                          tn.next_state, tn.next_piece_info, done)

    def _flush_one(self) -> Transition:
        result = self._fold(self._buf, self._buf[-1].done)
        self._buf.popleft()
        return result

    def _flush_all(self) -> Transition:
        return self._fold(self._buf, True)


def _make_batch(transitions: list[Transition], device: torch.device,
                indices: np.ndarray | None = None,
                weights: np.ndarray | None = None) -> Batch:
    states_np = np.stack([t.state for t in transitions])
    next_states_np = np.stack([t.next_state for t in transitions])
    w_t = (
        torch.from_numpy(weights.astype(np.float32)).to(device)
        if weights is not None else None
    )
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
        indices=indices,
        weights=w_t,
    )


class ReplayBuffer:
    def __init__(self, capacity: int = 100_000) -> None:
        self._buf: deque[Transition] = deque(maxlen=capacity)

    def push(self, transition: Transition) -> None:
        self._buf.append(transition)

    def sample(self, batch_size: int, device: torch.device) -> Batch:
        return _make_batch(random.sample(self._buf, batch_size), device)

    def __len__(self) -> int:
        return len(self._buf)


class _SumTree:
    """Binary tree where each leaf stores priority; internal nodes store sums."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._tree = np.zeros(2 * capacity, dtype=np.float64)
        self._data: list[Transition | None] = [None] * capacity
        self._pos = 0
        self._size = 0

    def _propagate(self, idx: int, delta: float) -> None:
        parent = (idx - 1) // 2
        self._tree[parent] += delta
        if parent != 0:
            self._propagate(parent, delta)

    def add(self, priority: float, transition: Transition) -> int:
        leaf = self._pos + self.capacity - 1
        self._data[self._pos] = transition
        self.update(leaf, priority)
        self._pos = (self._pos + 1) % self.capacity
        self._size = min(self._size + 1, self.capacity)
        return leaf

    def update(self, leaf_idx: int, priority: float) -> None:
        delta = priority - self._tree[leaf_idx]
        self._tree[leaf_idx] = priority
        self._propagate(leaf_idx, delta)

    def get(self, s: float) -> tuple[int, float, Transition]:
        """Walk tree to find leaf whose cumulative sum >= s."""
        idx = 0
        while idx < self.capacity - 1:
            left = 2 * idx + 1
            if s <= self._tree[left]:
                idx = left
            else:
                s -= self._tree[left]
                idx = left + 1
        data_idx = idx - self.capacity + 1
        return idx, self._tree[idx], self._data[data_idx]  # type: ignore[return-value]

    @property
    def total(self) -> float:
        return float(self._tree[0])


class PrioritizedReplayBuffer:
    """Replay buffer with proportional prioritization (Schaul et al. 2016).

    Samples transitions proportional to |TD error|^alpha.
    Importance-sampling weights correct for the non-uniform distribution.
    """

    def __init__(
        self,
        capacity: int,
        alpha: float = 0.6,
        beta_start: float = 0.4,
        beta_steps: int = 1_000_000,
        eps: float = 1e-6,
    ) -> None:
        self._tree = _SumTree(capacity)
        self.capacity = capacity
        self.alpha = alpha
        self.beta_start = beta_start
        self.beta_steps = beta_steps
        self.eps = eps
        self._max_priority: float = 1.0
        self._step = 0

    def push(self, transition: Transition) -> None:
        # new transitions get max priority so they're sampled at least once
        self._tree.add(self._max_priority ** self.alpha, transition)

    def sample(self, batch_size: int, device: torch.device) -> Batch:
        beta = min(
            1.0,
            self.beta_start + self._step * (1.0 - self.beta_start) / self.beta_steps,
        )
        self._step += 1

        segment = self._tree.total / batch_size
        leaf_indices = np.empty(batch_size, dtype=np.int64)
        priorities = np.empty(batch_size, dtype=np.float64)
        transitions: list[Transition] = []

        for i in range(batch_size):
            s = random.uniform(segment * i, segment * (i + 1))
            leaf_idx, priority, t = self._tree.get(s)
            leaf_indices[i] = leaf_idx
            priorities[i] = priority
            transitions.append(t)

        probs = priorities / self._tree.total
        weights = (self._tree._size * probs) ** (-beta)
        weights /= weights.max()

        return _make_batch(transitions, device, leaf_indices, weights)

    def update_priorities(
        self, leaf_indices: np.ndarray, td_errors: np.ndarray
    ) -> None:
        priorities = (np.abs(td_errors) + self.eps) ** self.alpha
        self._max_priority = max(self._max_priority, float(priorities.max()))
        for idx, p in zip(leaf_indices, priorities):
            self._tree.update(int(idx), float(p))

    def __len__(self) -> int:
        return self._tree._size
