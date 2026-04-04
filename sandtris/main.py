import argparse
from sandtris.core.config import GameConfig
from sandtris.runners.pygame_runner import PygameRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Sandtris")
    parser.add_argument(
        "--headless", action="store_true", help="Run without UI"
    )
    args = parser.parse_args()

    config = GameConfig(headless=args.headless)

    runner = PygameRunner(config=config)
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
