import pygame

from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class GameOverScreen:
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
        self.restart_button = PixelButton("RESTART")
        self.save_button = PixelButton("SAVE SCORE")
        self.menu_button = PixelButton("MAIN MENU")

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        modal_width = 360
        btn_h = self.dims.modal_button_height
        margin = self.dims.modal_button_margin
        step = self.dims.modal_button_step

        modal = pygame.Rect(0, 0, modal_width, 410)
        modal.center = surface_rect.center

        return {
            "modal": modal,
            "restart": pygame.Rect(
                modal.left + margin,
                modal.top + 218,
                modal.width - margin * 2,
                btn_h,
            ),
            "save": pygame.Rect(
                modal.left + margin,
                modal.top + 218 + step,
                modal.width - margin * 2,
                btn_h,
            ),
            "menu": pygame.Rect(
                modal.left + margin,
                modal.top + 218 + step * 2,
                modal.width - margin * 2,
                btn_h,
            ),
        }

    def restart_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["restart"].collidepoint(pos)

    def save_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["save"].collidepoint(pos)

    def menu_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["menu"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        score: int,
        level: int,
        max_combo: int,
        status_message: str,
        player_name: str,
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

        title = self.title_font.render("GAME OVER", True, self.theme.body_text)
        title_rect = title.get_rect(center=(modal.centerx, modal.top + 36))
        surface.blit(title, title_rect)

        score_text = self.body_font.render(
            f"Score: {score}", True, self.theme.title_text
        )
        score_rect = score_text.get_rect(
            center=(modal.centerx, modal.top + 76)
        )
        surface.blit(score_text, score_rect)

        level_text = self.body_font.render(
            f"Level: {level}", True, self.theme.title_text
        )
        level_rect = level_text.get_rect(
            center=(modal.centerx, modal.top + 106)
        )
        surface.blit(level_text, level_rect)

        combo_text = self.body_font.render(
            f"Max Combo: {max_combo}x", True, self.theme.accent_text
        )
        combo_rect = combo_text.get_rect(
            center=(modal.centerx, modal.top + 136)
        )
        surface.blit(combo_text, combo_rect)

        name_row_y = modal.top + 156
        name_field_rect = pygame.Rect(
            modal.left + 20 + modal.width // 3,
            name_row_y,
            modal.width - 20 - modal.width // 3 - 20,
            32,
        )
        name_label = self.body_font.render("NAME:", True, self.theme.body_text)
        surface.blit(
            name_label,
            name_label.get_rect(
                left=modal.left + 20, centery=name_field_rect.centery
            ),
        )
        pygame.draw.rect(
            surface, self.theme.panel_bg_alt, name_field_rect, border_radius=3
        )
        pygame.draw.rect(
            surface,
            self.theme.panel_border_bright,
            name_field_rect,
            2,
            border_radius=3,
        )
        name_surf = self.body_font.render(
            f"{player_name}_", True, self.theme.title_text
        )
        surface.blit(
            name_surf,
            name_surf.get_rect(
                left=name_field_rect.left + 8,
                centery=name_field_rect.centery,
            ),
        )

        status_text = self.body_font.render(
            status_message, True, self.theme.panel_border_bright
        )
        status_rect = status_text.get_rect(
            center=(modal.centerx, modal.top + 202)
        )
        surface.blit(status_text, status_rect)

        hov_restart = layout["restart"].collidepoint(mouse_pos)
        self.restart_button.draw(
            surface,
            layout["restart"],
            self.body_font,
            self.theme,
            hov_restart,
            hov_restart and mouse_down,
        )

        hov_save = layout["save"].collidepoint(mouse_pos)
        self.save_button.draw(
            surface,
            layout["save"],
            self.body_font,
            self.theme,
            hov_save,
            hov_save and mouse_down,
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
