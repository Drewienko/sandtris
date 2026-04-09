import pygame

from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class VsScreen:
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
        self.pause_button = PixelButton("PAUSE")
        self.quit_button = PixelButton("GIVE UP")
        self.restart_button = PixelButton("RESTART")
        self.menu_button = PixelButton("MAIN MENU")

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        hud_h = 80
        pad = self.dims.gap
        m = self.dims.margin
        btn_h = self.dims.button_height
        center_w = self.dims.side_min_width
        board_w = (surface_rect.width - pad * 4 - center_w) // 2
        board_h = surface_rect.height - hud_h - pad * 2

        player_area = pygame.Rect(pad, hud_h + pad, board_w, board_h)
        center_area = pygame.Rect(player_area.right + pad, hud_h + pad, center_w, board_h)
        ai_area = pygame.Rect(center_area.right + pad, hud_h + pad, board_w, board_h)

        quit_rect = pygame.Rect(
            center_area.left + m,
            center_area.bottom - btn_h - m,
            center_w - m * 2,
            btn_h,
        )
        pause_rect = pygame.Rect(
            center_area.left + m,
            quit_rect.top - btn_h - self.dims.gap,
            center_w - m * 2,
            btn_h,
        )

        return {
            "hud": pygame.Rect(0, 0, surface_rect.width, hud_h),
            "player": player_area,
            "center": center_area,
            "ai": ai_area,
            "pause": pause_rect,
            "quit": quit_rect,
        }

    def get_result_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        modal = pygame.Rect(0, 0, 320, 250)
        modal.center = surface_rect.center
        margin = self.dims.modal_button_margin
        step = self.dims.modal_button_step
        btn_h = self.dims.modal_button_height
        return {
            "modal": modal,
            "restart": pygame.Rect(
                modal.left + margin, modal.top + 140, modal.width - margin * 2, btn_h
            ),
            "menu": pygame.Rect(
                modal.left + margin,
                modal.top + 140 + step,
                modal.width - margin * 2,
                btn_h,
            ),
        }

    def pause_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["pause"].collidepoint(pos)

    def quit_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["quit"].collidepoint(pos)

    def restart_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_result_layout(surface_rect)["restart"].collidepoint(pos)

    def menu_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_result_layout(surface_rect)["menu"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        player_surf: pygame.Surface,
        ai_surf: pygame.Surface,
        player_score: int,
        ai_score: int,
        player_level: int,
        ai_level: int,
        player_name: str,
        result: str | None,
        mouse_pos: tuple[int, int],
        mouse_down: bool,
        focused_idx: int = -1,
    ) -> None:
        surface.fill(self.theme.screen_bg)
        rect = surface.get_rect()
        layout = self.get_layout(rect)

        draw_panel(
            surface,
            layout["hud"],
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )

        w = rect.width
        hud_h = layout["hud"].height
        vs_title = self.title_font.render("VS AI", True, self.theme.title_text)
        surface.blit(vs_title, vs_title.get_rect(center=(w // 2, hud_h // 2 - 8)))

        pad = self.dims.gap
        p_info = self.body_font.render(
            f"{player_name}  Lv.{player_level}  {player_score} pts",
            True,
            self.theme.body_text,
        )
        surface.blit(p_info, p_info.get_rect(left=pad + 8, centery=hud_h // 2 + 8))

        ai_info = self.body_font.render(
            f"{ai_score} pts  Lv.{ai_level}  AI",
            True,
            self.theme.accent_text,
        )
        surface.blit(ai_info, ai_info.get_rect(right=w - pad - 8, centery=hud_h // 2 + 8))

        draw_panel(
            surface,
            layout["player"],
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )
        self._blit_board(surface, player_surf, layout["player"])

        draw_panel(
            surface,
            layout["ai"],
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.accent_panel,
        )
        self._blit_board(surface, ai_surf, layout["ai"])

        draw_panel(
            surface,
            layout["center"],
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )

        hov_pause = layout["pause"].collidepoint(mouse_pos)
        self.pause_button.draw(
            surface,
            layout["pause"],
            self.body_font,
            self.theme,
            hov_pause,
            hov_pause and mouse_down,
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

        if result is not None:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill(self.theme.overlay)
            surface.blit(overlay, (0, 0))

            result_layout = self.get_result_layout(rect)
            modal = result_layout["modal"]
            draw_panel(
                surface,
                modal,
                self.theme.panel_bg,
                self.theme.panel_border,
                self.theme.panel_border_bright,
            )
            result_surf = self.title_font.render(result, True, self.theme.title_text)
            surface.blit(
                result_surf, result_surf.get_rect(center=(modal.centerx, modal.top + 46))
            )
            score_surf = self.body_font.render(
                f"You: {player_score}    AI: {ai_score}",
                True,
                self.theme.body_text,
            )
            surface.blit(
                score_surf,
                score_surf.get_rect(center=(modal.centerx, modal.top + 96)),
            )
            for idx, (key, btn) in enumerate(
                [("restart", self.restart_button), ("menu", self.menu_button)]
            ):
                mouse_hov = result_layout[key].collidepoint(mouse_pos)
                hov = mouse_hov or focused_idx == idx
                btn.draw(
                    surface,
                    result_layout[key],
                    self.body_font,
                    self.theme,
                    hov,
                    mouse_hov and mouse_down,
                )

    def _blit_board(
        self, surface: pygame.Surface, board_surf: pygame.Surface, area: pygame.Rect
    ) -> None:
        inner = area.inflate(-12, -12)
        bw, bh = board_surf.get_size()
        cell = min(inner.width // bw, inner.height // bh)
        if cell <= 0:
            return
        scaled = pygame.transform.scale(board_surf, (bw * cell, bh * cell))
        rw, rh = scaled.get_size()
        surface.blit(
            scaled,
            (
                inner.left + (inner.width - rw) // 2,
                inner.top + (inner.height - rh) // 2,
            ),
        )
