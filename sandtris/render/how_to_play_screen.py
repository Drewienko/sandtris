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
            "",
            "CONTROLS:",
        ]

        controls = [
            (
                f"{pygame.key.name(config.key_left).upper()} / {pygame.key.name(config.key_right).upper()}",
                "Move Left / Right",
            ),
            (f"{pygame.key.name(config.key_up).upper()}", "Rotate"),
            (
                f"{pygame.key.name(config.key_down).upper()} / {pygame.key.name(config.key_drop).upper()}",
                "Fast Drop",
            ),
            (f"{pygame.key.name(config.key_pause).upper()}", "Pause"),
        ]

        y_offset = panel.top + 100
        for line in instructions:
            text = self.body_font.render(line, True, self.theme.body_text)
            text_rect = text.get_rect(centerx=panel.centerx, top=y_offset)
            surface.blit(text, text_rect)
            y_offset += 30

        y_offset += 10
        for key, action in controls:
            key_text = self.body_font.render(key, True, self.theme.accent_text)
            action_text = self.body_font.render(
                action, True, self.theme.body_text
            )

            key_rect = key_text.get_rect(
                right=panel.centerx - 20, top=y_offset
            )
            action_rect = action_text.get_rect(
                left=panel.centerx + 20, top=y_offset
            )

            surface.blit(key_text, key_rect)
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
