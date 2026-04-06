import pygame
from dataclasses import dataclass, field


@dataclass
class GameConfig:
    scale: int = 8
    fps: int = 60
    headless: bool = False
    fall_delay: int = 30
    fast_fall_delay: int = 1
    key_left: tuple[int, ...] = (pygame.K_LEFT, pygame.K_a)
    key_right: tuple[int, ...] = (pygame.K_RIGHT, pygame.K_d)
    key_up: tuple[int, ...] = (pygame.K_UP, pygame.K_w)
    key_down: tuple[int, ...] = (pygame.K_DOWN, pygame.K_s)
    key_drop: tuple[int, ...] = (pygame.K_SPACE, pygame.K_RETURN)
    key_pause: tuple[int, ...] = (pygame.K_ESCAPE, pygame.K_p)
    width: int = field(init=False)
    height: int = field(init=False)

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError("scale must be greater than 0")
        if self.fps <= 0:
            raise ValueError("fps must be greater than 0")
        if self.fall_delay <= 0:
            raise ValueError("fall_delay must be greater than 0")
        if self.fast_fall_delay <= 0:
            raise ValueError("fast_fall_delay must be greater than 0")

        self.width = 10 * self.scale
        self.height = 20 * self.scale
