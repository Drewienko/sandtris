import itertools


from sandtris.core.config import GameConfig
from sandtris.core.engine import SandtrisEngine
from sandtris.core.pieces import Tetromino


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
    assert engine.combo_timer_ms == 3000.0


def test_tick_resets_combo_when_timer_expires() -> None:
    engine = SandtrisEngine(GameConfig(scale=2))
    engine.combo = 4
    engine.combo_timer_ms = 1.0
    engine.active_piece = None
    engine.grid.data.fill(0)

    engine.tick()

    assert engine.combo == 1
    assert engine.combo_timer_ms == 0.0


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


def test_move_active_piece_blocked_at_left_wall() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    engine.active_piece = Tetromino("O", x=0, y=0, color_id=1, scale=1)
    result = engine.move_active_piece(-1, 0)
    assert result is False
    assert engine.active_piece.x == 0


def test_move_active_piece_blocked_at_right_wall() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    piece = Tetromino("O", x=engine.grid.width - 2, y=0, color_id=1, scale=1)
    engine.active_piece = piece
    result = engine.move_active_piece(1, 0)
    assert result is False
    assert engine.active_piece.x == engine.grid.width - 2


def test_move_active_piece_blocked_by_occupied_cell() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    engine.active_piece = Tetromino("O", x=2, y=0, color_id=1, scale=1)
    engine.grid.add_sand(4, 0, 3)
    result = engine.move_active_piece(1, 0)
    assert result is False
    assert engine.active_piece.x == 2


def test_rotate_active_piece_reverts_on_collision() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    engine.active_piece = Tetromino("I", x=0, y=0, color_id=1, scale=1)
    import numpy as np

    original_shape = engine.active_piece.shape.copy()
    engine.grid.data.fill(1)
    engine.active_piece.shape = original_shape.copy()
    engine.rotate_active_piece()
    assert np.array_equal(engine.active_piece.shape, original_shape)


def test_lock_piece_increments_pieces_placed() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    engine.active_piece = Tetromino("O", x=0, y=0, color_id=2, scale=1)
    before = engine.pieces_placed
    engine.lock_piece()
    assert engine.pieces_placed == before + 1


def test_lock_piece_places_cells_into_grid() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    piece = Tetromino("O", x=0, y=engine.grid.height - 2, color_id=3, scale=1)
    engine.active_piece = piece
    engine.lock_piece()
    assert engine.grid.data[engine.grid.height - 2, 0] != 0
    assert engine.grid.data[engine.grid.height - 1, 0] != 0


def test_lock_piece_spawns_next_piece() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.grid.data.fill(0)
    engine.next_shape_name = "O"
    engine.next_color_id = 1
    locked = Tetromino("I", x=0, y=5, color_id=2, scale=1)
    engine.active_piece = locked
    engine.lock_piece()
    assert engine.active_piece is not locked or engine.game_over


def test_tick_accumulates_pixels_cleared() -> None:
    engine = SandtrisEngine(GameConfig(scale=1))
    engine.active_piece = None
    engine.grid.data.fill(0)
    w = engine.grid.width

    for x in range(w):
        engine.grid.add_sand(x, engine.grid.height - 1, 3)
    engine.tick()
    first_clear = engine.pixels_cleared

    for x in range(w):
        engine.grid.add_sand(x, engine.grid.height - 1, 3)
    engine.tick()
    assert engine.pixels_cleared == first_clear + w
