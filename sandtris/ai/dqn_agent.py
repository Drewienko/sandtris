from __future__ import annotations

from pathlib import Path

import torch

from sandtris.ai.base import AgentBase, GameObservation
from sandtris.ai.dqn import SandtrisNet


class DQNAgent(AgentBase):
    """Plays Sandtris using a trained DQN checkpoint.

    Returns a placement index (int) from decide().
    NOTE: pygame_runner.py expects Action — it needs updating to use
    placement-based stepping before this agent works in VS mode.
    """

    def __init__(
        self,
        model_path: str | Path,
        device: str = "auto",
    ) -> None:
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.net = SandtrisNet().to(self.device)
        ckpt = torch.load(model_path, map_location=self.device, weights_only=False)
        if isinstance(ckpt, dict) and "state_dict" in ckpt:
            self.net.load_state_dict(ckpt["state_dict"])
            self.settle_ticks: int = int(ckpt.get("settle_ticks", 0))
        else:
            self.net.load_state_dict(ckpt)
            self.settle_ticks = 0
        self.net.eval()

    def reset(self) -> None:
        pass  # stateless — no hidden state to clear

    def decide(self, obs: GameObservation, n_placements: int = 320) -> int:
        return self.net.act(obs, n_placements, self.device)
