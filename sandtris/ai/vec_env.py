"""Vectorized environment: N SandtrisEnv instances stepped in parallel via threads.

numpy releases the GIL during update_sand(), so settle_ticks loops across
all envs run concurrently on separate cores.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sandtris.ai.base import GameObservation
from sandtris.ai.env import SandtrisEnv
from sandtris.core.config import GameConfig


class VecSandtrisEnv:
    def __init__(
        self,
        n_envs: int,
        config: GameConfig | None = None,
        reach_variant: str = "max_span",
        settle_ticks: int = 0,
    ) -> None:
        self.n_envs = n_envs
        self.envs = [
            SandtrisEnv(config, reach_variant, settle_ticks) for _ in range(n_envs)
        ]
        self._pool = ThreadPoolExecutor(max_workers=n_envs)

    def reset(self) -> list[GameObservation]:
        return [env.reset() for env in self.envs]

    def reset_env(self, idx: int) -> GameObservation:
        return self.envs[idx].reset()

    def step(
        self, actions: list[int]
    ) -> list[tuple[GameObservation, float, bool]]:
        futs = [
            self._pool.submit(env.step, a)
            for env, a in zip(self.envs, actions)
        ]
        return [f.result() for f in futs]

    @property
    def n_placements(self) -> list[int]:
        return [env.n_placements for env in self.envs]

    def close(self) -> None:
        self._pool.shutdown(wait=False)
