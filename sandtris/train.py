"""DQN training entrypoint.

Usage:
    uv run sandtris-train
    uv run sandtris-train --steps 500000 --scale 8 --out models/
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from sandtris.ai.dqn import (
    N_ACTIONS,
    TRAIN_ACTIONS,
    SandtrisNet,
    obs_to_arrays,
)
from sandtris.ai.env import SandtrisEnv
from sandtris.ai.replay import ReplayBuffer, Transition
from sandtris.core.config import GameConfig

# --- hyperparameters ---
GAMMA = 0.99
LR = 1e-4
BATCH_SIZE = 32
BUFFER_SIZE = 100_000
TRAIN_START = 1_000
TRAIN_EVERY = 4      # env steps between each gradient update
TARGET_SYNC = 1_000
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 0.999990
LOG_EVERY = 10       # episodes
SAVE_EVERY = 100_000  # steps


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Sandtris DQN agent")
    p.add_argument("--steps", type=int, default=1_000_000)
    p.add_argument("--scale", type=int, default=8)
    p.add_argument("--buffer-size", type=int, default=None,
                   help="replay buffer capacity (default: 100k for scale≤4, 25k for scale>4)")
    p.add_argument("--out", type=Path, default=Path("models"))
    p.add_argument("--resume", type=Path, default=None,
                   help="checkpoint .pt to resume from")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  scale={args.scale}  steps={args.steps:,}")

    args.out.mkdir(exist_ok=True)

    config = GameConfig(scale=args.scale, lock_delay_ms=0, headless=True)
    env = SandtrisEnv(config)

    online = SandtrisNet().to(device)
    target = SandtrisNet().to(device)

    if args.resume:
        online.load_state_dict(torch.load(args.resume, map_location=device))
        print(f"resumed from {args.resume}")

    target.load_state_dict(online.state_dict())
    target.eval()

    optimizer = torch.optim.Adam(online.parameters(), lr=LR)
    buf_size = args.buffer_size or (BUFFER_SIZE if args.scale <= 4 else 25_000)
    print(f"buffer={buf_size:,}  (~{buf_size * args.scale**2 * 2 // 1024 // 1024} MB)")
    buffer = ReplayBuffer(buf_size)

    eps = EPS_START
    obs = env.reset()
    episode_reward = 0.0
    episode_steps = 0
    episode = 0
    total_clears = 0
    t0 = time.perf_counter()

    for step in range(1, args.steps + 1):
        # --- select action ---
        if random.random() < eps:
            action_idx = random.randrange(N_ACTIONS)
        else:
            online.eval()
            with torch.no_grad():
                action_idx = online.act(obs, device)
            online.train()
        eps = max(EPS_END, eps * EPS_DECAY)

        # --- env step ---
        prev_score = obs.score
        next_obs, reward, done = env.step(TRAIN_ACTIONS[action_idx])
        if next_obs.score > prev_score:
            total_clears += 1
        episode_reward += reward
        episode_steps += 1

        grid, piece_info = obs_to_arrays(obs)
        next_grid, next_piece_info = obs_to_arrays(next_obs)
        buffer.push(Transition(grid, piece_info, action_idx, reward,
                               next_grid, next_piece_info, done))

        obs = env.reset() if done else next_obs

        if done:
            episode += 1
            if episode % LOG_EVERY == 0:
                sps = step / (time.perf_counter() - t0)
                print(
                    f"step={step:>8,}  ep={episode:>5}  "
                    f"reward={episode_reward:>7.2f}  "
                    f"steps/ep={episode_steps:>5}  "
                    f"clears={total_clears:>6,}  "
                    f"eps={eps:.3f}  sps={sps:>6.0f}"
                )
            episode_reward = 0.0
            episode_steps = 0

        # --- train ---
        if len(buffer) >= TRAIN_START and step % TRAIN_EVERY == 0:
            batch = buffer.sample(BATCH_SIZE, device)

            # batch.states already (B, 7, H, W) — no unsqueeze needed
            q_all = online(batch.states, batch.piece_infos)
            q_sa = q_all.gather(1, batch.actions.unsqueeze(1)).squeeze(1)

            with torch.no_grad():
                # Double DQN: online selects action, target evaluates it
                best_actions = online(
                    batch.next_states, batch.next_piece_infos
                ).argmax(1, keepdim=True)
                q_next = target(
                    batch.next_states, batch.next_piece_infos
                ).gather(1, best_actions).squeeze(1)
                q_target = batch.rewards + GAMMA * q_next * ~batch.dones

            loss = F.mse_loss(q_sa, q_target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # --- sync target network ---
        if step % TARGET_SYNC == 0:
            target.load_state_dict(online.state_dict())

        # --- checkpoint ---
        if step % SAVE_EVERY == 0:
            path = args.out / f"dqn_{step:08d}.pt"
            torch.save(online.state_dict(), path)
            print(f"saved {path}")

    final = args.out / "dqn_final.pt"
    torch.save(online.state_dict(), final)
    print(f"training done → {final}")
