import asyncio
import argparse
from sandtris.core.config import GameConfig
from sandtris.runners.pygame_runner import PygameRunner


async def amain() -> int:
    parser = argparse.ArgumentParser(description="Sandtris")
    parser.add_argument(
        "--headless", action="store_true", help="Run without UI"
    )
    args, _unknown = parser.parse_known_args()

    config = GameConfig(headless=args.headless)

    runner = PygameRunner(config=config)
    await runner.run()
    return 0


def main() -> int:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
