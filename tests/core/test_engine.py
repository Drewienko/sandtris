from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine


def test_tick_scores_cleared_pixels_and_starts_combo() -> None:
    engine = SandtrisEngine(GameConfig(scale=2))
    engine.active_piece = None
    engine.grid.data.fill(0)

    y = engine.grid.height - 1
    values = [3, 13] * (engine.grid.width // 2)
    if len(values) < engine.grid.width:
        values.append(3)

    for x, color in enumerate(values[: engine.grid.width]):
        engine.grid.add_sand(x, y, color)

    engine.tick()

    assert engine.score == engine.grid.width
    assert engine.combo == 2
    assert engine.combo_timer == engine.config.fps * 3


def test_tick_resets_combo_when_timer_expires() -> None:
    engine = SandtrisEngine(GameConfig(scale=2))
    engine.combo = 4
    engine.combo_timer = 1
    engine.active_piece = None
    engine.grid.data.fill(0)

    engine.tick()

    assert engine.combo == 1
    assert engine.combo_timer == 0
