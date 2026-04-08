import pygame

from sandtris.core.config import GameConfig
from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
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
        ]

        line_h = self.body_font.get_linesize()
        y = panel.top + 100
        for line in instructions:
            text = self.body_font.render(line, True, self.theme.body_text)
            surface.blit(text, text.get_rect(centerx=panel.centerx, top=y))
            y += line_h

        y += line_h
        controls_label = self.body_font.render(
            "CONTROLS:", True, self.theme.title_text
        )
        surface.blit(
            controls_label,
            controls_label.get_rect(centerx=panel.centerx, top=y),
        )
        y += line_h + line_h // 2

        controls = [
            (config.key_left, "Move Left"),
            (config.key_right, "Move Right"),
            (config.key_up, "Rotate"),
            (
                config.key_down + config.key_drop,
                "Fast Drop",
            ),
            (config.key_pause, "Pause"),
        ]

        margin = self.dims.modal_button_margin
        for keys, action in controls:
            keys_str = " / ".join(
                pygame.key.name(k).upper() for k in keys
            )
            keys_surf = self.body_font.render(
                keys_str, True, self.theme.title_text
            )
            action_surf = self.body_font.render(
                action, True, self.theme.body_text
            )
            surface.blit(
                keys_surf,
                keys_surf.get_rect(left=panel.left + margin, top=y),
            )
            surface.blit(
                action_surf,
                action_surf.get_rect(right=panel.right - margin, top=y),
            )
            y += line_h + line_h // 4

        hov_back = layout["back"].collidepoint(mouse_pos)
        self.back_button.draw(
            surface,
            layout["back"],
            self.body_font,
            self.theme,
            hov_back,
            hov_back and mouse_down,
        )
