"""DQN training entrypoint.

Usage:
    uv run sandtris-train
    uv run sandtris-train --steps 500000 --scale 4 --out models/
    uv run sandtris-train --steps 500000 --reach-variant max_span avg_span surface_span
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import torch

from sandtris.ai.dqn import SandtrisNet, obs_to_arrays
from sandtris.ai.replay import (
    NStepBuffer, PrioritizedReplayBuffer, ReplayBuffer, Transition,
)
from sandtris.ai.vec_env import VecSandtrisEnv
from sandtris.core.config import GameConfig

GAMMA = 0.99
N_STEP = 5
GAMMA_N = GAMMA ** N_STEP   # discount on bootstrap in n-step target
LR = 1e-4
BATCH_SIZE = 32
BUFFER_SIZE = 100_000
TRAIN_START = 1_000
TRAIN_EVERY = 4       # env steps between each gradient update
TARGET_SYNC = 1_000
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 0.999990
LOG_EVERY = 10        # episodes
SAVE_EVERY = 100_000  # steps


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Sandtris DQN agent")
    p.add_argument("--steps", type=int, default=1_000_000)
    p.add_argument("--scale", type=int, default=8)
    p.add_argument("--buffer-size", type=int, default=None,
                   help="replay buffer capacity (default: 100k for scale≤4, 25k for scale>4)")
    p.add_argument("--out", type=Path, default=Path("models"))
    p.add_argument("--resume", type=Path, default=None,
                   help="checkpoint .pt to resume from (single-variant only)")
    p.add_argument(
        "--reach-variant",
        nargs="+",
        default=["max_span"],
        choices=["max_span", "avg_span", "surface_span"],
        dest="reach_variants",
        metavar="VARIANT",
    )
    p.add_argument(
        "--settle-ticks", type=int, default=0,
        help="grid.update_sand() calls after each lock before env tick (0=off)",
    )
    p.add_argument("--n-envs", type=int, default=1,
                   help="parallel envs (uses threads; GIL released during numpy physics)")
    p.add_argument("--per", action="store_true",
                   help="use Prioritized Experience Replay instead of uniform sampling")
    return p.parse_args()


def run_training(
    variant: str,
    config: GameConfig,
    out_dir: Path,
    args: argparse.Namespace,
    device: torch.device,
) -> None:
    """Train one DQN run for args.steps steps, saving checkpoints to out_dir."""
    n_envs = args.n_envs
    print(f"\n{'=' * 60}")
    print(
        f"variant={variant}  steps={args.steps:,}  scale={config.scale}  "
        f"n_envs={n_envs}  settle={args.settle_ticks}  out={out_dir}"
    )
    print(f"{'=' * 60}")

    vec_env = VecSandtrisEnv(
        n_envs, config, reach_variant=variant, settle_ticks=args.settle_ticks
    )
    nstep_bufs = [NStepBuffer(n=N_STEP, gamma=GAMMA) for _ in range(n_envs)]

    online = SandtrisNet().to(device)
    target = SandtrisNet().to(device)

    if args.resume:
        if len(args.reach_variants) > 1:
            print("warning: --resume ignored for multi-variant runs")
        else:
            ckpt = torch.load(args.resume, map_location=device, weights_only=False)
            sd = ckpt["state_dict"] if isinstance(ckpt, dict) else ckpt
            online.load_state_dict(sd)
            print(f"resumed from {args.resume}")

    target.load_state_dict(online.state_dict())
    target.eval()

    optimizer = torch.optim.Adam(online.parameters(), lr=LR)
    buf_size = args.buffer_size or (BUFFER_SIZE if config.scale <= 4 else 25_000)
    print(f"buffer={buf_size:,}  per={args.per}  "
          f"(~{buf_size * config.scale**2 * 2 // 1024 // 1024} MB)")
    buffer: ReplayBuffer | PrioritizedReplayBuffer = (
        PrioritizedReplayBuffer(buf_size, beta_steps=args.steps)
        if args.per else ReplayBuffer(buf_size)
    )

    eps = EPS_START
    obses = vec_env.reset()
    ep_rewards = [0.0] * n_envs
    ep_steps_list = [0] * n_envs
    episode = 0
    total_clears = 0
    step = 0
    t0 = time.perf_counter()

    while step < args.steps:
        # --- select actions (one forward pass for all envs) ---
        greedy = online.act_batch(obses, vec_env.n_placements, device)
        actions = [
            random.randrange(n) if random.random() < eps else g
            for g, n in zip(greedy, vec_env.n_placements)
        ]
        for _ in range(n_envs):
            eps = max(EPS_END, eps * EPS_DECAY)

        # --- step all envs in parallel ---
        results = vec_env.step(actions)

        for i, (next_obs, reward, done) in enumerate(results):
            step += 1
            if next_obs.score > obses[i].score:
                total_clears += 1
            ep_rewards[i] += reward
            ep_steps_list[i] += 1

            grid, piece_info = obs_to_arrays(obses[i])
            next_grid, next_piece_info = obs_to_arrays(next_obs)
            t = nstep_bufs[i].push(
                Transition(grid, piece_info, actions[i], reward,
                           next_grid, next_piece_info, done)
            )
            if t is not None:
                buffer.push(t)

            if done:
                episode += 1
                if episode % LOG_EVERY == 0:
                    elapsed = time.perf_counter() - t0
                    sps = step / elapsed
                    print(
                        f"[{variant}] "
                        f"step={step:>8,}  ep={episode:>5}  "
                        f"reward={ep_rewards[i]:>7.2f}  "
                        f"pieces/ep={ep_steps_list[i]:>5}  "
                        f"clears={total_clears:>6,}  "
                        f"eps={eps:.3f}  sps={sps:>6.0f}"
                    )
                ep_rewards[i] = 0.0
                ep_steps_list[i] = 0
                obses[i] = vec_env.reset_env(i)
            else:
                obses[i] = next_obs

            # --- train ---
            if len(buffer) >= TRAIN_START and step % TRAIN_EVERY == 0:
                batch = buffer.sample(BATCH_SIZE, device)

                q_all = online(batch.states, batch.piece_infos)
                q_sa = q_all.gather(1, batch.actions.unsqueeze(1)).squeeze(1)

                with torch.no_grad():
                    best_actions = online(
                        batch.next_states, batch.next_piece_infos
                    ).argmax(1, keepdim=True)
                    q_next = target(
                        batch.next_states, batch.next_piece_infos
                    ).gather(1, best_actions).squeeze(1)
                    q_target = batch.rewards + GAMMA_N * q_next * ~batch.dones

                td_errors = (q_target - q_sa).detach()
                if batch.weights is not None:
                    loss = (batch.weights * td_errors.pow(2)).mean()
                else:
                    loss = td_errors.pow(2).mean()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                if batch.indices is not None:
                    assert isinstance(buffer, PrioritizedReplayBuffer)
                    buffer.update_priorities(
                        batch.indices, td_errors.abs().cpu().numpy()
                    )

            # --- sync target network ---
            if step % TARGET_SYNC == 0:
                target.load_state_dict(online.state_dict())

            # --- checkpoint ---
            if step % SAVE_EVERY == 0:
                path = out_dir / f"dqn_{step:08d}.pt"
                torch.save({"state_dict": online.state_dict(), "settle_ticks": args.settle_ticks}, path)
                print(f"[{variant}] saved {path}")

    vec_env.close()
    ckpt = {"state_dict": online.state_dict(), "settle_ticks": args.settle_ticks}
    final = out_dir / "dqn_final.pt"
    torch.save(ckpt, final)
    testing_dir = args.out / "testing"
    testing_dir.mkdir(exist_ok=True)
    testing_path = testing_dir / f"{variant}_{args.steps}.pt"
    torch.save(ckpt, testing_path)
    print(f"[{variant}] done → {final}  ({testing_path})")


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = GameConfig(scale=args.scale, lock_delay_ms=0, headless=True)
    print(f"device={device}  scale={args.scale}  variants={args.reach_variants}")

    for variant in args.reach_variants:
        out_dir = args.out / variant
        out_dir.mkdir(parents=True, exist_ok=True)
        run_training(variant, config, out_dir, args, device)
