from collections import deque

import numpy as np


class Grid:
    def __init__(self, width: int, height: int, diagonal_prob: float = 0.4):
        self.width = width
        self.height = height
        self.diagonal_prob = diagonal_prob
        self.data = np.zeros((height, width), dtype=np.uint8)
        self.last_cleared: list[tuple[int, int]] = []
        self._frame_parity: bool = False

    def is_occupied(self, x: int, y: int) -> bool:
        if x < 0 or x >= self.width or y >= self.height:
            return True
        if y < 0:
            return False
        return self.data[y, x] != 0

    def add_sand(self, x: int, y: int, color_id: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[y, x] = color_id

    def update_sand(self) -> None:
        self._frame_parity = not self._frame_parity
        pref_dir = 1 if self._frame_parity else -1
        xs = np.arange(self.width)

        for y in range(self.height - 2, -1, -1):
            row = self.data[y]
            if not row.any():
                continue

            below = self.data[y + 1]

            fall = (row != 0) & (below == 0)
            below[fall] = row[fall]
            row[fall] = 0

            remaining = row != 0
            if not remaining.any():
                continue

            gate = np.random.random(self.width) < self.diagonal_prob

            for dx in (pref_dir, -pref_dir):
                nx = xs + dx
                in_bounds = (nx >= 0) & (nx < self.width)
                nx_safe = np.where(in_bounds, nx, 0)
                can_move = remaining & gate & in_bounds & (below[nx_safe] == 0)
                if not can_move.any():
                    continue
                srcs = np.where(can_move)[0]
                tgts = nx_safe[srcs]
                _, first = np.unique(tgts, return_index=True)
                srcs, tgts = srcs[first], tgts[first]
                below[tgts] = row[srcs]
                row[srcs] = 0
                remaining = row != 0
                if not remaining.any():
                    break

    def check_line_clears(self) -> tuple[int, int]:
        """Returns (pixels_cleared, connections_cleared)."""
        if not self.data[:, 0].any():
            return 0, 0

        to_clear = set()
        visited = set()
        connections = 0

        for y in range(self.height):
            cell_val = self.data[y, 0]
            if cell_val != 0 and (0, y) not in visited:
                base_color = cell_val % 10
                component = set()
                queue = deque([(0, y)])
                component.add((0, y))
                visited.add((0, y))
                reaches_right = False

                while queue:
                    cx, cy = queue.popleft()

                    if cx == self.width - 1:
                        reaches_right = True

                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                n_val = self.data[ny, nx]
                                if (
                                    n_val != 0
                                    and n_val % 10 == base_color
                                    and (nx, ny) not in visited
                                ):
                                    visited.add((nx, ny))
                                    component.add((nx, ny))
                                    queue.append((nx, ny))

                if reaches_right:
                    to_clear.update(component)
                    connections += 1

        self.last_cleared = list(to_clear)
        for nx, ny in to_clear:
            self.data[ny, nx] = 0

        return len(to_clear), connections
