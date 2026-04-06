import pygame

from sandtris.core.config import GameConfig
from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_keycap,
    draw_panel,
)


class HowToPlayScreen:
    def __init__(
        self,
        title_font: pygame.font.Font,
        body_font: pygame.font.Font,
        theme: ThemeColors | None = None,
        dims: UIDimensions | None = None,
    ) -> None:
        self.title_font = title_font
        self.body_font = body_font
        self.theme = theme or ThemeColors()
        self.dims = dims or UIDimensions()
        self.back_button = PixelButton("BACK")

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        panel_width = min(600, surface_rect.width - 40)
        panel_height = min(700, surface_rect.height - 40)

        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = surface_rect.center

        btn_h = self.dims.modal_button_height
        margin = self.dims.modal_button_margin

        return {
            "panel": panel,
            "back": pygame.Rect(
                panel.left + margin,
                panel.bottom - btn_h - margin,
                panel.width - margin * 2,
                btn_h,
            ),
        }

    def back_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["back"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        config: GameConfig,
        mouse_pos: tuple[int, int],
        mouse_down: bool,
    ) -> None:
        surface.fill(self.theme.screen_bg)

        layout = self.get_layout(surface.get_rect())
        panel = layout["panel"]

        draw_panel(
            surface,
            panel,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )

        title = self.title_font.render(
            "HOW TO PLAY", True, self.theme.title_text
        )
        title_rect = title.get_rect(center=(panel.centerx, panel.top + 46))
        surface.blit(title, title_rect)

        instructions = [
            "Pieces turn into sand on impact.",
            "Sand cascades down and settles.",
            "Clear sand by connecting a",
            "continuous path of the same color",
            "from the left wall to the right wall.",
            "",
            "CONTROLS:",
        ]

        controls = [
            (
                [pygame.key.name(k).upper() for k in config.key_left]
                + [pygame.key.name(k).upper() for k in config.key_right],
                "Move Left / Right",
            ),
            ([pygame.key.name(k).upper() for k in config.key_up], "Rotate"),
            (
                [pygame.key.name(k).upper() for k in config.key_down]
                + [pygame.key.name(k).upper() for k in config.key_drop],
                "Fast Drop",
            ),
            ([pygame.key.name(k).upper() for k in config.key_pause], "Pause"),
        ]

        y_offset = panel.top + 100
        for line in instructions:
            text = self.body_font.render(line, True, self.theme.body_text)
            text_rect = text.get_rect(centerx=panel.centerx, top=y_offset)
            surface.blit(text, text_rect)
            y_offset += 30

        y_offset += 10
        for keys, action in controls:
            action_text = self.body_font.render(
                action, True, self.theme.body_text
            )
            action_rect = action_text.get_rect(
                left=panel.centerx + 20, top=y_offset
            )

            right_edge = panel.centerx - 20
            key_rects = []
            for label in reversed(keys):
                text = self.body_font.render(label, True, self.theme.body_text)
                key_width = text.get_width() + self.dims.keycap_padding_x * 2
                key_rect = draw_keycap(
                    surface,
                    label,
                    (right_edge - key_width // 2, y_offset + 10),
                    self.body_font,
                    self.theme,
                    self.dims,
                )
                key_rects.append(key_rect)
                right_edge = key_rect.left - 8

            if len(keys) > 1:
                slash = self.body_font.render("/", True, self.theme.body_text)
                slash_rect = slash.get_rect(
                    center=(key_rects[0].left + 4, y_offset + 10)
                )
                surface.blit(slash, slash_rect)

            surface.blit(action_text, action_rect)
            y_offset += 40

        hov_back = layout["back"].collidepoint(mouse_pos)
        self.back_button.draw(
            surface,
            layout["back"],
            self.body_font,
            self.theme,
            hov_back,
            hov_back and mouse_down,
        )
