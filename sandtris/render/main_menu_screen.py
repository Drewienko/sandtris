import pygame

from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class MainMenuScreen:
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
        self.play_button = PixelButton("PLAY")
        self.settings_button = PixelButton("SETTINGS")
        self.help_button = PixelButton("HOW TO PLAY")
        self.quit_button = PixelButton("QUIT")

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        menu_width = 320
        btn_h = self.dims.modal_button_height
        margin = self.dims.modal_button_margin
        step = self.dims.modal_button_step

        panel = pygame.Rect(0, 0, menu_width, 360)
        panel.center = surface_rect.center

        return {
            "panel": panel,
            "play": pygame.Rect(
                panel.left + margin,
                panel.top + 100,
                panel.width - margin * 2,
                btn_h,
            ),
            "settings": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step,
                panel.width - margin * 2,
                btn_h,
            ),
            "help": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * 2,
                panel.width - margin * 2,
                btn_h,
            ),
            "quit": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * 3,
                panel.width - margin * 2,
                btn_h,
            ),
        }

    def play_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["play"].collidepoint(pos)

    def settings_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["settings"].collidepoint(pos)

    def help_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["help"].collidepoint(pos)

    def quit_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["quit"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
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

        title = self.title_font.render("SANDTRIS", True, self.theme.title_text)
        title_rect = title.get_rect(center=(panel.centerx, panel.top + 46))
        surface.blit(title, title_rect)

        hov_play = layout["play"].collidepoint(mouse_pos)
        self.play_button.draw(
            surface,
            layout["play"],
            self.body_font,
            self.theme,
            hov_play,
            hov_play and mouse_down,
        )

        hov_settings = layout["settings"].collidepoint(mouse_pos)
        self.settings_button.draw(
            surface,
            layout["settings"],
            self.body_font,
            self.theme,
            hov_settings,
            hov_settings and mouse_down,
        )

        hov_help = layout["help"].collidepoint(mouse_pos)
        self.help_button.draw(
            surface,
            layout["help"],
            self.body_font,
            self.theme,
            hov_help,
            hov_help and mouse_down,
        )

        hov_quit = layout["quit"].collidepoint(mouse_pos)
        self.quit_button.draw(
            surface,
            layout["quit"],
            self.body_font,
            self.theme,
            hov_quit,
            hov_quit and mouse_down,
        )
