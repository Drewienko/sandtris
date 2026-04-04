import numpy as np

SHAPES = {
    "L": np.array([[0, 0, 1], [1, 1, 1], [0, 0, 0]], dtype=np.uint8),
}

scale = 4
shape = np.kron(SHAPES['L'], np.ones((scale, scale), dtype=np.uint8))
color_matrix_4 = np.zeros_like(shape)
color_matrix_8 = np.zeros_like(shape)

rows, cols = shape.shape
for r in range(rows):
    for c in range(cols):
        if shape[r, c] != 0:
            # 4 neighbors
            is_edge_4 = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= rows or nc < 0 or nc >= cols or shape[nr, nc] == 0:
                    is_edge_4 = True
                    break
            color_matrix_4[r, c] = 2 if is_edge_4 else 1

            # 8 neighbors
            is_edge_8 = False
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols or shape[nr, nc] == 0:
                        is_edge_8 = True
                        break
                if is_edge_8: break
            color_matrix_8[r, c] = 2 if is_edge_8 else 1

print("4-way neighbors:")
for r in range(rows):
    print("".join(str(x) if x != 0 else ' ' for x in color_matrix_4[r]))

print("\n8-way neighbors:")
for r in range(rows):
    print("".join(str(x) if x != 0 else ' ' for x in color_matrix_8[r]))

