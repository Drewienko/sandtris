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


THEME_PRESETS: dict[str, ThemeColors] = {
    "Egyptian": ThemeColors(),
    "Midnight": ThemeColors(
        screen_bg=(12, 14, 24),
        panel_bg=(24, 28, 42),
        panel_bg_alt=(18, 22, 34),
        panel_border=(87, 117, 177),
        panel_border_bright=(138, 177, 255),
        title_text=(173, 205, 255),
        body_text=(224, 233, 255),
        accent_text=(111, 232, 255),
        accent_panel=(76, 93, 168),
        button_bg=(30, 40, 60),
        button_hover=(40, 54, 82),
        button_pressed=(55, 72, 102),
        overlay=(8, 10, 18, 180),
    ),
    "Oasis": ThemeColors(
        screen_bg=(17, 28, 24),
        panel_bg=(29, 45, 40),
        panel_bg_alt=(22, 34, 31),
        panel_border=(112, 165, 138),
        panel_border_bright=(175, 224, 191),
        title_text=(238, 224, 151),
        body_text=(223, 240, 216),
        accent_text=(101, 224, 206),
        accent_panel=(54, 130, 122),
        button_bg=(52, 69, 51),
        button_hover=(68, 88, 66),
        button_pressed=(87, 110, 85),
        overlay=(8, 18, 15, 180),
    ),
}


SAND_PALETTE_PRESETS: dict[str, dict[int, tuple[int, int, int]]] = {
    "Classic": {
        1: (0, 255, 255),
        2: (0, 0, 255),
        3: (255, 165, 0),
        4: (255, 255, 0),
        5: (0, 255, 0),
        6: (128, 0, 128),
        7: (255, 0, 0),
    },
    "Gemstone": {
        1: (61, 196, 255),
        2: (67, 106, 255),
        3: (255, 160, 74),
        4: (245, 223, 70),
        5: (84, 224, 110),
        6: (177, 74, 255),
        7: (255, 75, 108),
    },
    "Desert": {
        1: (91, 184, 207),
        2: (73, 99, 181),
        3: (217, 147, 63),
        4: (220, 195, 88),
        5: (115, 171, 84),
        6: (146, 82, 161),
        7: (204, 92, 74),
    },
}


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

    keycap_padding_x: int = 12
    keycap_padding_y: int = 8


def build_color_palette(
    background: tuple[int, int, int],
    sand_base: dict[int, tuple[int, int, int]],
) -> dict[int, tuple[int, int, int]]:
    palette = {0: background}
    for index, color in sand_base.items():
        palette[index] = color
        r, g, b = color
        palette[index + 10] = (
            max(0, r - 80),
            max(0, g - 80),
            max(0, b - 80),
        )
    return palette


def draw_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    trim_color: tuple[int, int, int],
    dims: UIDimensions = UIDimensions(),
    exterior_corners: bool = False,
) -> None:
    pygame.draw.rect(surface, fill_color, rect)
    pygame.draw.rect(surface, border_color, rect, dims.panel_border)

    trim = rect.inflate(
        -dims.panel_trim_margin * 2, -dims.panel_trim_margin * 2
    )
    if trim.width > 0 and trim.height > 0:
        pygame.draw.rect(surface, trim_color, trim, dims.panel_trim_width)

    if not exterior_corners:
        return

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


def draw_keycap(
    surface: pygame.Surface,
    label: str,
    center: tuple[int, int],
    font: pygame.font.Font,
    theme: ThemeColors,
    dims: UIDimensions,
) -> pygame.Rect:
    text = font.render(label, True, theme.body_text)
    rect = text.get_rect()
    rect.width += dims.keycap_padding_x * 2
    rect.height += dims.keycap_padding_y * 2
    rect.center = center
    draw_panel(
        surface,
        rect,
        theme.button_bg,
        theme.panel_border,
        theme.panel_border_bright,
        dims,
    )
    surface.blit(text, text.get_rect(center=rect.center))
    return rect
