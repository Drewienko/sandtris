# Sandtris

[![Play in Browser](https://img.shields.io/badge/Play_in_Browser-blue?style=for-the-badge&logo=web)](https://Drewienko.github.io/sandtris/)

Tetris + falling sand physics. Pieces dissolve into sand particles on lock. Clear lines by connecting same-color sand from the left wall to the right wall.

## Play

- **Browser:** [Drewienko.github.io/sandtris](https://Drewienko.github.io/sandtris/)
- **Local:** `uv run sandtris`

## Controls

| Action | Keys |
|--------|------|
| Move | `←` `→` / `A` `D` |
| Rotate | `↑` / `W` |
| Soft drop | `↓` / `S` |
| Hard drop | `Space` / `Enter` |
| Pause | `Esc` / `P` |

## Install

Requires Python 3.12+ and `uv`.

```bash
git clone https://github.com/Drewienko/sandtris.git
cd sandtris
uv run sandtris
```

## AI

`SandtrisEnv` in `sandtris/ai/env.py` exposes a Gym-like interface for training agents.

```python
from sandtris.ai.env import SandtrisEnv
from sandtris.ai.base import Action

env = SandtrisEnv()
obs = env.reset()
obs, reward, done = env.step(Action.HARD_DROP)
```

Train a DQN agent:
```bash
uv run sandtris-train
```

See [DQN.md](DQN.md) for architecture and training details.

## Dev

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run pygbag --build . # web build
```

Optional dependency groups: `ai-torch`, `ai-llm`, `api`, `web`.
