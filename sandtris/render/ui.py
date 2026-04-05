from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class ThemeColors:
    screen_bg: tuple[int, int, int] = (20, 19, 29)
    panel_bg: tuple[int, int, int] = (36, 33, 43)
    panel_bg_alt: tuple[int, int, int] = (28, 25, 34)
    panel_border: tuple[int, int, int] = (185, 141, 88)
    panel_border_bright: tuple[int, int, int] = (216, 178, 122)
    title_text: tuple[int, int, int] = (242, 193, 79)
    body_text: tuple[int, int, int] = (239, 224, 176)
    accent_text: tuple[int, int, int] = (58, 166, 160)
    accent_panel: tuple[int, int, int] = (47, 95, 168)
    button_bg: tuple[int, int, int] = (54, 46, 37)
    button_hover: tuple[int, int, int] = (72, 60, 46)
    button_pressed: tuple[int, int, int] = (96, 77, 53)
    overlay: tuple[int, int, int, int] = (12, 10, 18, 170)


@dataclass(frozen=True)
class UIDimensions:
    margin: int = 16
    gap: int = 16
    hud_height: int = 88
    side_min_width: int = 190
    next_panel_height: int = 160

    button_height: int = 56
    modal_button_height: int = 50
    modal_button_margin: int = 20
    modal_button_step: int = 60

    panel_border: int = 3
    panel_trim_margin: int = 8
    panel_trim_width: int = 1
    panel_corner_step: int = 8
    panel_corner_width: int = 2


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    trim_color: tuple[int, int, int],
    dims: UIDimensions = UIDimensions(),
) -> None:
    pygame.draw.rect(surface, fill_color, rect)
    pygame.draw.rect(surface, border_color, rect, dims.panel_border)

    trim = rect.inflate(
        -dims.panel_trim_margin * 2, -dims.panel_trim_margin * 2
    )
    if trim.width > 0 and trim.height > 0:
        pygame.draw.rect(surface, trim_color, trim, dims.panel_trim_width)

    step = dims.panel_corner_step
    inset = dims.margin
    top = [
        (rect.left + inset, rect.top),
        (rect.left + inset + step, rect.top - step),
        (rect.right - inset - step, rect.top - step),
        (rect.right - inset, rect.top),
    ]
    bottom = [
        (rect.left + inset, rect.bottom),
        (rect.left + inset + step, rect.bottom + step),
        (rect.right - inset - step, rect.bottom + step),
        (rect.right - inset, rect.bottom),
    ]
    pygame.draw.lines(surface, trim_color, False, top, dims.panel_corner_width)
    pygame.draw.lines(
        surface, trim_color, False, bottom, dims.panel_corner_width
    )


class PixelButton:
    def __init__(self, label: str) -> None:
        self.label = label

    def draw(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        font: pygame.font.Font,
        theme: ThemeColors,
        hovered: bool,
        pressed: bool,
    ) -> None:
        fill = theme.button_bg
        if pressed:
            fill = theme.button_pressed
        elif hovered:
            fill = theme.button_hover

        draw_panel(
            surface, rect, fill, theme.panel_border, theme.panel_border_bright
        )
        text = font.render(self.label, True, theme.body_text)
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)
