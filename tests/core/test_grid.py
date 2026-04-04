from sandtris.core.grid import Grid


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
