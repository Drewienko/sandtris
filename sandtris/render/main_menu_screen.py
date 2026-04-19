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
        self.vs_button = PixelButton("VS AI")
        self.settings_button = PixelButton("SETTINGS")
        self.scores_button = PixelButton("HIGH SCORES")
        self.help_button = PixelButton("HOW TO PLAY")
        self.quit_button = PixelButton("QUIT")
        self.yes_button = PixelButton("YES")
        self.no_button = PixelButton("NO")
        self.confirming_quit = False

    def get_layout(
        self, surface_rect: pygame.Rect, show_vs: bool = True
    ) -> dict[str, pygame.Rect]:
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

        n_buttons = 6 if show_vs else 5
        panel_h = 100 + step * n_buttons + 20
        panel = pygame.Rect(0, 0, 320, panel_h)
        panel.center = surface_rect.center

        layout: dict[str, pygame.Rect] = {"panel": panel}
        buttons = ["play", "settings", "scores", "help", "quit"]
        if show_vs:
            buttons.insert(1, "vs")
        for i, key in enumerate(buttons):
            layout[key] = pygame.Rect(
                panel.left + margin,
                panel.top + 100 + step * i,
                panel.width - margin * 2,
                btn_h,
            )
        return layout

    def play_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect, show_vs)["play"].collidepoint(pos)

    def vs_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit or not show_vs:
            return False
        return self.get_layout(surface_rect, show_vs)["vs"].collidepoint(pos)

    def settings_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect, show_vs)["settings"].collidepoint(pos)

    def scores_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect, show_vs)["scores"].collidepoint(pos)

    def help_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect, show_vs)["help"].collidepoint(pos)

    def quit_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int], show_vs: bool = True
    ) -> bool:
        if self.confirming_quit:
            return False
        return self.get_layout(surface_rect, show_vs)["quit"].collidepoint(pos)

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
        show_vs: bool = True,
    ) -> None:
        surface.fill(self.theme.screen_bg)

        layout = self.get_layout(surface.get_rect(), show_vs)
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

        all_buttons = [
            ("play", self.play_button),
            ("vs", self.vs_button),
            ("settings", self.settings_button),
            ("scores", self.scores_button),
            ("help", self.help_button),
            ("quit", self.quit_button),
        ]
        visible = [(k, b) for k, b in all_buttons if k != "vs" or show_vs]
        for idx, (key, btn) in enumerate(visible):
            mouse_hov = layout[key].collidepoint(mouse_pos)
            hov = mouse_hov or focused_idx == idx
            btn.draw(surface, layout[key], self.body_font, self.theme,
                     hov, mouse_hov and mouse_down)
