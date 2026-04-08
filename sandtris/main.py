import asyncio
import argparse
from sandtris.core.config import GameConfig
from sandtris.runners.pygame_runner import PygameRunner


def _make_runner(argv: list[str] | None = None) -> PygameRunner:
    parser = argparse.ArgumentParser(description="Sandtris")
    parser.add_argument(
        "--headless", action="store_true", help="Run without UI"
    )
    args, _unknown = parser.parse_known_args(argv)
    return PygameRunner(config=GameConfig(headless=args.headless))


async def amain() -> int:
    await _make_runner().run_async()
    return 0


def main() -> int:
    try:
        _make_runner().run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
