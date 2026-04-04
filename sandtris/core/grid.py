from collections import deque
import random

import numpy as np


class Grid:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.data = np.zeros((height, width), dtype=np.uint8)

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
        for y in range(self.height - 2, -1, -1):
            xs = list(range(self.width))
            random.shuffle(xs)

            for x in xs:
                color = self.data[y, x]
                if color != 0:
                    if self.data[y + 1, x] == 0:
                        self.data[y, x] = 0
                        self.data[y + 1, x] = color
                    else:
                        dir1 = random.choice([-1, 1])
                        dir2 = -dir1

                        if (
                            0 <= x + dir1 < self.width
                            and self.data[y + 1, x + dir1] == 0
                        ):
                            self.data[y, x] = 0
                            self.data[y + 1, x + dir1] = color
                        elif (
                            0 <= x + dir2 < self.width
                            and self.data[y + 1, x + dir2] == 0
                        ):
                            self.data[y, x] = 0
                            self.data[y + 1, x + dir2] = color

    def check_line_clears(self) -> int:
        to_clear = set()
        visited = set()

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

        for nx, ny in to_clear:
            self.data[ny, nx] = 0

        return len(to_clear)
