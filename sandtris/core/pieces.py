import numpy as np

PIECE_COLOR_IDS = (1, 2, 3, 4, 5, 6, 7)

SHAPES = {
    "I": np.array(
        [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
        dtype=np.uint8,
    ),
    "J": np.array([[1, 0, 0], [1, 1, 1], [0, 0, 0]], dtype=np.uint8),
    "L": np.array([[0, 0, 1], [1, 1, 1], [0, 0, 0]], dtype=np.uint8),
    "O": np.array([[1, 1], [1, 1]], dtype=np.uint8),
    "S": np.array([[0, 1, 1], [1, 1, 0], [0, 0, 0]], dtype=np.uint8),
    "T": np.array([[0, 1, 0], [1, 1, 1], [0, 0, 0]], dtype=np.uint8),
    "Z": np.array([[1, 1, 0], [0, 1, 1], [0, 0, 0]], dtype=np.uint8),
}


class Tetromino:
    def __init__(
        self,
        shape_name: str,
        x: int,
        y: int,
        color_id: int,
        scale: int = 4,
    ):
        self.name = shape_name
        self.scale = scale
        base_shape = SHAPES[shape_name].copy()
        if scale > 1:
            self.shape = np.kron(
                base_shape, np.ones((scale, scale), dtype=np.uint8)
            )
        else:
            self.shape = base_shape

        self.color = color_id
        self.x = x
        self.y = y

        self.color_matrix = np.zeros_like(self.shape, dtype=np.uint8)
        dark_color = self.color + 10

        rows, cols = self.shape.shape
        for r in range(rows):
            for c in range(cols):
                if self.shape[r, c] != 0:
                    is_edge = False
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if (
                                nr < 0
                                or nr >= rows
                                or nc < 0
                                or nc >= cols
                                or self.shape[nr, nc] == 0
                            ):
                                is_edge = True
                                break
                        if is_edge:
                            break
                    self.color_matrix[r, c] = (
                        dark_color if is_edge else self.color
                    )

    def rotate(self, times: int = 1) -> None:
        self.shape = np.rot90(self.shape, k=-times)
        self.color_matrix = np.rot90(self.color_matrix, k=-times)

    def get_cells(self) -> list[tuple[int, int, int]]:
        cells = []
        for row in range(self.shape.shape[0]):
            for col in range(self.shape.shape[1]):
                if self.shape[row, col] != 0:
                    cells.append(
                        (
                            self.x + col,
                            self.y + row,
                            self.color_matrix[row, col],
                        )
                    )
        return cells
