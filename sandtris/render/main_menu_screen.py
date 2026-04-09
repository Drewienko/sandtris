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
        self.scores_button = PixelButton("HIGH SCORES")
        self.help_button = PixelButton("HOW TO PLAY")
        self.quit_button = PixelButton("QUIT")
        self.yes_button = PixelButton("YES")
        self.no_button = PixelButton("NO")
        self.confirming_quit = False

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        btn_h = self.dims.modal_button_height
        margin = self.dims.modal_button_margin
        step = self.dims.modal_button_step

        if self.confirming_quit:
            panel = pygame.Rect(0, 0, 320, 200)
            panel.center = surface_rect.center
            half = (panel.width - margin * 2 - 20) // 2
            return {
                "panel": panel,
                "yes": pygame.Rect(
                    panel.left + margin, panel.top + 100, half, btn_h
                ),
                "no": pygame.Rect(
                    panel.right - margin - half, panel.top + 100, half, btn_h
                ),
            }

        panel = pygame.Rect(0, 0, 320, 420)
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
            "scores": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * 2,
                panel.width - margin * 2,
                btn_h,
            ),
            "help": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * 3,
                panel.width - margin * 2,
                btn_h,
            ),
            "quit": pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * 4,
                panel.width - margin * 2,
                btn_h,
            ),
        }

    def play_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["play"].collidepoint(pos)

    def settings_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["settings"].collidepoint(pos)

    def scores_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["scores"].collidepoint(pos)

    def help_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["help"].collidepoint(pos)

    def quit_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["quit"].collidepoint(pos)

    def yes_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if not self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["yes"].collidepoint(pos)

    def no_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if not self.confirming_quit:
            return False
        return self.get_layout(surface_rect)["no"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: tuple[int, int],
        mouse_down: bool,
        focused_idx: int = -1,
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

        title_str = "QUIT?" if self.confirming_quit else "SANDTRIS"
        title = self.title_font.render(title_str, True, self.theme.title_text)
        title_rect = title.get_rect(center=(panel.centerx, panel.top + 46))
        surface.blit(title, title_rect)

        if self.confirming_quit:
            hov_yes = layout["yes"].collidepoint(mouse_pos)
            self.yes_button.draw(
                surface,
                layout["yes"],
                self.body_font,
                self.theme,
                hov_yes,
                hov_yes and mouse_down,
            )
            hov_no = layout["no"].collidepoint(mouse_pos)
            self.no_button.draw(
                surface,
                layout["no"],
                self.body_font,
                self.theme,
                hov_no,
                hov_no and mouse_down,
            )
            return

        for idx, (key, btn) in enumerate([
            ("play", self.play_button),
            ("settings", self.settings_button),
            ("scores", self.scores_button),
            ("help", self.help_button),
            ("quit", self.quit_button),
        ]):
            mouse_hov = layout[key].collidepoint(mouse_pos)
            hov = mouse_hov or focused_idx == idx
            btn.draw(surface, layout[key], self.body_font, self.theme,
                     hov, mouse_hov and mouse_down)
