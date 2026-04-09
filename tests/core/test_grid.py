from sandtris.core.grid import Grid


def test_is_occupied_out_of_bounds_left() -> None:
    grid = Grid(5, 5)
    assert grid.is_occupied(-1, 2) is True


def test_is_occupied_out_of_bounds_right() -> None:
    grid = Grid(5, 5)
    assert grid.is_occupied(5, 2) is True


def test_is_occupied_out_of_bounds_bottom() -> None:
    grid = Grid(5, 5)
    assert grid.is_occupied(2, 5) is True


def test_is_occupied_above_grid_is_free() -> None:
    grid = Grid(5, 5)
    assert grid.is_occupied(2, -1) is False


def test_add_sand_out_of_bounds_is_ignored() -> None:
    grid = Grid(5, 5)
    grid.add_sand(-1, 0, 3)
    grid.add_sand(5, 0, 3)
    grid.add_sand(0, 5, 3)
    assert grid.data.sum() == 0


def test_update_sand_particle_falls_one_row() -> None:
    grid = Grid(5, 5)
    grid.add_sand(2, 0, 3)
    grid.update_sand()
    assert grid.data[0, 2] == 0
    assert grid.data[1, 2] == 3


def test_update_sand_particle_rests_at_bottom() -> None:
    grid = Grid(5, 5)
    grid.add_sand(2, 4, 3)
    grid.update_sand()
    assert grid.data[4, 2] == 3


def test_check_line_clears_empty_grid_returns_zero() -> None:
    grid = Grid(5, 5)
    assert grid.check_line_clears() == 0


def test_check_line_clears_partial_row_not_cleared() -> None:
    grid = Grid(5, 5)
    for x in range(4):
        grid.add_sand(x, 3, 2)
    cleared = grid.check_line_clears()
    assert cleared == 0
    assert grid.data[3, :4].sum() != 0


def test_check_line_clears_different_colors_not_merged() -> None:
    grid = Grid(6, 5)
    for x in range(3):
        grid.add_sand(x, 2, 1)
    for x in range(3, 6):
        grid.add_sand(x, 2, 2)
    cleared = grid.check_line_clears()
    assert cleared == 0


def test_line_clear_removes_connected_component_touching_both_walls() -> None:
    grid = Grid(5, 5)

    connected = [(0, 2, 3), (1, 2, 13), (2, 2, 3), (3, 2, 13), (4, 2, 3)]
    for x, y, color in connected:
        grid.add_sand(x, y, color)

    grid.add_sand(0, 4, 3)
    grid.add_sand(1, 4, 3)

    cleared = grid.check_line_clears()

    assert cleared == 5
    assert grid.data[2, :].sum() == 0
    assert grid.data[4, 0] == 3
    assert grid.data[4, 1] == 3


def test_line_clear_uses_diagonal_connectivity() -> None:
    grid = Grid(5, 5)

    diagonal = [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)]
    for x, y in diagonal:
        grid.add_sand(x, y, 4)

    cleared = grid.check_line_clears()

    assert cleared == 5
    assert grid.data.sum() == 0
