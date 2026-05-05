"""Benchmark: how many ticks until sand fully settles after a piece locks.

Usage:
    uv run python tests/bench_settle.py
    uv run python tests/bench_settle.py --scale 4 --pieces 500
"""

import argparse
import random

import numpy as np

from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine


def ticks_to_settle(engine: SandtrisEngine, max_ticks: int = 500) -> int:
    """Run ticks until grid stops changing. Returns tick count."""
    prev = engine.grid.data.copy()
    for i in range(1, max_ticks + 1):
        engine.grid.update_sand()
        curr = engine.grid.data
        if np.array_equal(prev, curr):
            return i
        prev = curr.copy()
    return max_ticks  # hit cap — sand never settled


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=int, default=8)
    p.add_argument("--pieces", type=int, default=500)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)
    config = GameConfig(scale=args.scale, lock_delay_ms=0, headless=True)
    engine = SandtrisEngine(config)

    counts: list[int] = []
    piece_num = 0

    while piece_num < args.pieces:
        if engine.game_over or engine.active_piece is None:
            engine = SandtrisEngine(config)
            continue

        # random legal placement
        piece = engine.active_piece
        w = engine.grid.width
        piece.x = random.randint(0, w - 1)
        while engine._check_collision(piece):
            piece.x = random.randint(0, w - 1)

        # hard drop
        while engine.move_active_piece(0, 1):
            pass

        # lock (no settle ticks — measure from scratch)
        engine.lock_piece()
        engine.tick()  # spawns next piece + 1 physics tick

        n = ticks_to_settle(engine)
        counts.append(n)
        piece_num += 1

    counts.sort()
    n = len(counts)
    print(f"scale={args.scale}  pieces={n}")
    print(f"  min    {counts[0]}")
    print(f"  p50    {counts[n // 2]}")
    print(f"  p75    {counts[int(n * 0.75)]}")
    print(f"  p90    {counts[int(n * 0.90)]}")
    print(f"  p99    {counts[int(n * 0.99)]}")
    print(f"  max    {counts[-1]}")
    print(f"  mean   {sum(counts) / n:.1f}")


if __name__ == "__main__":
    main()
