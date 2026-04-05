import itertools

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


def test_spawn_piece_selects_shape_and_color_independently(
    monkeypatch,
) -> None:
    choices = itertools.cycle(["I", 5])

    def fake_choice(_values):
        return next(choices)

    monkeypatch.setattr("sandtris.core.engine.random.choice", fake_choice)

    engine = SandtrisEngine(GameConfig(scale=2))

    assert engine.active_piece is not None
    assert engine.active_piece.name == "I"
    assert engine.active_piece.color == 5


def test_check_game_over_detects_blocked_spawn() -> None:
    engine = SandtrisEngine(GameConfig(scale=2))
    engine.grid.data.fill(0)
    engine.active_piece = None
    engine.next_shape_name = "O"
    engine.next_color_id = 3

    spawn_x, spawn_y = engine._get_spawn_position("O")
    engine.grid.add_sand(spawn_x, spawn_y, 4)

    assert engine.check_game_over() is True
    assert engine.game_over is True
