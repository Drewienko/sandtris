import numpy as np

from sandtris.core.pieces import SHAPES, Tetromino


def test_get_cells_returns_correct_world_coords() -> None:
    piece = Tetromino("O", x=3, y=5, color_id=2, scale=1)
    cells = piece.get_cells()
    xs = {c[0] for c in cells}
    ys = {c[1] for c in cells}
    assert xs == {3, 4}
    assert ys == {5, 6}


def test_get_cells_count_matches_shape_at_scale_1() -> None:
    for name in SHAPES:
        piece = Tetromino(name, x=0, y=0, color_id=1, scale=1)
        expected = int(SHAPES[name].sum())
        assert len(piece.get_cells()) == expected, name


def test_scale_2_multiplies_cell_count() -> None:
    piece_s1 = Tetromino("I", x=0, y=0, color_id=1, scale=1)
    piece_s2 = Tetromino("I", x=0, y=0, color_id=1, scale=2)
    assert len(piece_s2.get_cells()) == len(piece_s1.get_cells()) * 4


def test_rotate_four_times_returns_to_original() -> None:
    piece = Tetromino("L", x=0, y=0, color_id=3, scale=1)
    original = piece.shape.copy()
    piece.rotate(times=4)
    assert np.array_equal(piece.shape, original)


def test_rotate_changes_shape() -> None:
    piece = Tetromino("L", x=0, y=0, color_id=3, scale=1)
    before = piece.shape.copy()
    piece.rotate()
    assert not np.array_equal(piece.shape, before)


def test_color_matrix_edge_cells_are_dark() -> None:
    piece = Tetromino("O", x=0, y=0, color_id=2, scale=3)
    for row in range(piece.shape.shape[0]):
        for col in range(piece.shape.shape[1]):
            if piece.shape[row, col] != 0:
                color = piece.color_matrix[row, col]
                assert color in (2, 12), (
                    f"unexpected color {color} at ({row},{col})"
                )


def test_color_matrix_interior_cells_use_base_color() -> None:
    piece = Tetromino("O", x=0, y=0, color_id=5, scale=4)
    interior_colors = set()
    rows, cols = piece.shape.shape
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if piece.shape[r, c] != 0:
                interior_colors.add(piece.color_matrix[r, c])
    assert 5 in interior_colors
