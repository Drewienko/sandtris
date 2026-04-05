import pygame

from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class PauseScreen:
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
        self.resume_button = PixelButton("RESUME")
        self.restart_button = PixelButton("RESTART")
        self.settings_button = PixelButton("SETTINGS")
        self.menu_button = PixelButton("MAIN MENU")

        self.yes_button = PixelButton("YES")
        self.no_button = PixelButton("NO")

        self.confirming_restart = False
        self.confirming_menu = False

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        btn_h = self.dims.modal_button_height
        margin = self.dims.modal_button_margin
        step = self.dims.modal_button_step

        if self.confirming_restart or self.confirming_menu:
            modal = pygame.Rect(0, 0, 320, 200)
            modal.center = surface_rect.center
            return {
                "modal": modal,
                "yes": pygame.Rect(
                    modal.left + margin,
                    modal.top + 100,
                    (modal.width - margin * 2 - 20) // 2,
                    btn_h,
                ),
                "no": pygame.Rect(
                    modal.right
                    - margin
                    - (modal.width - margin * 2 - 20) // 2,
                    modal.top + 100,
                    (modal.width - margin * 2 - 20) // 2,
                    btn_h,
                ),
            }

        modal = pygame.Rect(0, 0, 280, 320)
        modal.center = surface_rect.center

        return {
            "modal": modal,
            "resume": pygame.Rect(
                modal.left + margin,
                modal.top + 70,
                modal.width - margin * 2,
                btn_h,
            ),
            "restart": pygame.Rect(
                modal.left + margin,
                modal.top + 70 + step,
                modal.width - margin * 2,
                btn_h,
            ),
            "settings": pygame.Rect(
                modal.left + margin,
                modal.top + 70 + step * 2,
                modal.width - margin * 2,
                btn_h,
            ),
            "menu": pygame.Rect(
                modal.left + margin,
                modal.top + 70 + step * 3,
                modal.width - margin * 2,
                btn_h,
            ),
        }

    def resume_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_restart or self.confirming_menu:
            return False
        return self.get_layout(surface_rect)["resume"].collidepoint(pos)

    def restart_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_restart or self.confirming_menu:
            return False
        return self.get_layout(surface_rect)["restart"].collidepoint(pos)

    def settings_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_restart or self.confirming_menu:
            return False
        return self.get_layout(surface_rect)["settings"].collidepoint(pos)

    def menu_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if self.confirming_restart or self.confirming_menu:
            return False
        return self.get_layout(surface_rect)["menu"].collidepoint(pos)

    def yes_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if not (self.confirming_restart or self.confirming_menu):
            return False
        return self.get_layout(surface_rect)["yes"].collidepoint(pos)

    def no_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        if not (self.confirming_restart or self.confirming_menu):
            return False
        return self.get_layout(surface_rect)["no"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: tuple[int, int],
        mouse_down: bool,
    ) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(self.theme.overlay)
        surface.blit(overlay, (0, 0))

        layout = self.get_layout(surface.get_rect())
        modal = layout["modal"]

        draw_panel(
            surface,
            modal,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )

        title_str = "PAUSED"
        if self.confirming_restart:
            title_str = "RESTART?"
        elif self.confirming_menu:
            title_str = "QUIT?"

        title = self.title_font.render(title_str, True, self.theme.body_text)
        title_rect = title.get_rect(center=(modal.centerx, modal.top + 46))
        surface.blit(title, title_rect)

        if self.confirming_restart or self.confirming_menu:
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
        else:
            hov_resume = layout["resume"].collidepoint(mouse_pos)
            self.resume_button.draw(
                surface,
                layout["resume"],
                self.body_font,
                self.theme,
                hov_resume,
                hov_resume and mouse_down,
            )

            hov_restart = layout["restart"].collidepoint(mouse_pos)
            self.restart_button.draw(
                surface,
                layout["restart"],
                self.body_font,
                self.theme,
                hov_restart,
                hov_restart and mouse_down,
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

            hov_menu = layout["menu"].collidepoint(mouse_pos)
            self.menu_button.draw(
                surface,
                layout["menu"],
                self.body_font,
                self.theme,
                hov_menu,
                hov_menu and mouse_down,
            )
