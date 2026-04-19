from __future__ import annotations

from pathlib import Path

import torch

from sandtris.ai.base import Action, AgentBase, GameObservation
from sandtris.ai.dqn import TRAIN_ACTIONS, SandtrisNet


class DQNAgent(AgentBase):
    """Plays Sandtris using a trained DQN checkpoint."""

    def __init__(
        self,
        model_path: str | Path,
        device: str = "auto",
    ) -> None:
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device)
        self.net = SandtrisNet().to(self.device)
        self.net.load_state_dict(
            torch.load(model_path, map_location=self.device, weights_only=True)
        )
        self.net.eval()

    def reset(self) -> None:
        pass  # stateless — no hidden state to clear

    def decide(self, obs: GameObservation) -> Action:
        return TRAIN_ACTIONS[self.net.act(obs, self.device)]
