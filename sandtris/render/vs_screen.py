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
        self.help_button = PixelButton("?")
        self.restart_button = PixelButton("RESTART")
        self.menu_button = PixelButton("MAIN MENU")
        self._render_cache: dict[tuple, pygame.Surface] = {}
        self._scaled_board_surf: pygame.Surface | None = None

    def _cached_render(
        self, font: pygame.font.Font, text: str, color: tuple
    ) -> pygame.Surface:
        key = (id(font), text, color)
        if key not in self._render_cache:
            self._render_cache[key] = font.render(text, True, color)
        return self._render_cache[key]

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        m = self.dims.margin
        g = self.dims.gap
        hud_h = self.dims.hud_height
        btn_h = self.dims.button_height
        center_w = self.dims.side_min_width
        content_top = m + hud_h + g
        content_h = surface_rect.height - content_top - m
        board_w = (surface_rect.width - m * 2 - center_w - g * 2) // 2

        hud = pygame.Rect(m, m, surface_rect.width - m * 2, hud_h)
        player_area = pygame.Rect(m, content_top, board_w, content_h)
        center_area = pygame.Rect(player_area.right + g, content_top, center_w, content_h)
        ai_area = pygame.Rect(center_area.right + g, content_top, board_w, content_h)

        next_rect = pygame.Rect(
            center_area.left + m,
            center_area.top + m,
            center_w - m * 2,
            self.dims.next_panel_height,
        )
        pause_rect = pygame.Rect(
            center_area.left + m,
            center_area.bottom - btn_h - m,
            center_w - m * 2,
            btn_h,
        )
        quit_rect = pygame.Rect(
            center_area.left + m,
            pause_rect.top - btn_h - g,
            center_w - m * 2,
            btn_h,
        )
        help_rect = pygame.Rect(
            center_area.left + m,
            quit_rect.top - btn_h - g,
            center_w - m * 2,
            btn_h,
        )

        return {
            "hud": hud,
            "player": player_area,
            "center": center_area,
            "ai": ai_area,
            "next": next_rect,
            "pause": pause_rect,
            "quit": quit_rect,
            "help": help_rect,
        }

    def get_result_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        modal = pygame.Rect(
            0, 0,
            min(320, surface_rect.width - 40),
            min(290, surface_rect.height - 40),
        )
        modal.center = surface_rect.center
        margin = self.dims.modal_button_margin
        btn_h = self.dims.modal_button_height
        gap = 10
        btn_y = modal.bottom - margin - btn_h * 2 - gap
        return {
            "modal": modal,
            "restart": pygame.Rect(
                modal.left + margin, btn_y, modal.width - margin * 2, btn_h
            ),
            "menu": pygame.Rect(
                modal.left + margin, btn_y + btn_h + gap, modal.width - margin * 2, btn_h
            ),
        }

    def pause_button_contains(self, surface_rect: pygame.Rect, pos: tuple[int, int]) -> bool:
        return self.get_layout(surface_rect)["pause"].collidepoint(pos)

    def quit_button_contains(self, surface_rect: pygame.Rect, pos: tuple[int, int]) -> bool:
        return self.get_layout(surface_rect)["quit"].collidepoint(pos)

    def help_button_contains(self, surface_rect: pygame.Rect, pos: tuple[int, int]) -> bool:
        return self.get_layout(surface_rect)["help"].collidepoint(pos)

    def restart_button_contains(self, surface_rect: pygame.Rect, pos: tuple[int, int]) -> bool:
        return self.get_result_layout(surface_rect)["restart"].collidepoint(pos)

    def menu_button_contains(self, surface_rect: pygame.Rect, pos: tuple[int, int]) -> bool:
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
        ai_dead: bool = False,
        fps: int = 0,
        next_shape_name: str | None = None,
        next_color_id: int | None = None,
        scale: int = 8,
        color_palette: dict[int, tuple[int, int, int]] | None = None,
        player_combo: int = 1,
        player_combo_timer_ms: float = 0.0,
        level_up_timer_ms: float = 0.0,
    ) -> None:
        surface.fill(self.theme.screen_bg)
        rect = surface.get_rect()
        layout = self.get_layout(rect)

        # HUD — two rows
        draw_panel(surface, layout["hud"], self.theme.panel_bg,
                   self.theme.panel_border, self.theme.panel_border_bright)
        hud = layout["hud"]
        row1_y = hud.top + 26
        row2_y = hud.top + 58

        player_text = self._cached_render(
            self.body_font,
            f"{player_name}  {player_score} pts",
            self.theme.body_text,
        )
        surface.blit(player_text, player_text.get_rect(left=hud.left + 24, centery=row1_y))

        level_text = self._cached_render(
            self.body_font, f"Lv.{player_level}", self.theme.body_text,
        )
        surface.blit(level_text, level_text.get_rect(left=hud.left + 24, centery=row2_y))

        if player_combo > 1:
            combo_text = self._cached_render(
                self.body_font, f"COMBO {player_combo}x", self.theme.accent_panel,
            )
            surface.blit(combo_text, combo_text.get_rect(left=hud.left + 120, centery=row2_y))

        vs_title = self._cached_render(self.title_font, "VS AI", self.theme.title_text)
        surface.blit(vs_title, vs_title.get_rect(centerx=rect.centerx, centery=hud.centery))

        fps_text = self.body_font.render(f"FPS {fps}", True, self.theme.accent_text)
        fps_rect = fps_text.get_rect(right=hud.right - 24, centery=row1_y)
        surface.blit(fps_text, fps_rect)

        ai_score_text = self._cached_render(
            self.body_font, f"{ai_score} pts  Lv.{ai_level}  AI", self.theme.accent_text,
        )
        surface.blit(ai_score_text, ai_score_text.get_rect(
            right=hud.right - 24, centery=row2_y
        ))

        # Combo timer bar under HUD
        if player_combo_timer_ms > 0:
            bar_h = 4
            bar_y = hud.bottom - bar_h - 2
            bar_max_w = hud.width // 2 - 48
            bar_x = hud.left + 24
            max_timer = max(2000.0, 6000.0 / max(player_level, 1))
            fill_w = int(bar_max_w * (player_combo_timer_ms / max_timer))
            pygame.draw.rect(surface, self.theme.panel_border,
                             (bar_x, bar_y, bar_max_w, bar_h), border_radius=2)
            if fill_w > 0:
                pygame.draw.rect(surface, self.theme.accent_panel,
                                 (bar_x, bar_y, fill_w, bar_h), border_radius=2)

        # Player board
        draw_panel(surface, layout["player"], self.theme.panel_bg,
                   self.theme.panel_border, self.theme.panel_border_bright)
        self._blit_board(surface, player_surf, layout["player"])

        # AI board
        draw_panel(surface, layout["ai"], self.theme.panel_bg,
                   self.theme.panel_border, self.theme.panel_border)
        self._blit_board(surface, ai_surf, layout["ai"])
        if ai_dead:
            overlay = pygame.Surface(layout["ai"].size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            surface.blit(overlay, layout["ai"].topleft)
            dead_surf = self.title_font.render("AI LOST", True, self.theme.title_text)
            surface.blit(dead_surf, dead_surf.get_rect(center=layout["ai"].center))

        # Center panel
        draw_panel(surface, layout["center"], self.theme.panel_bg,
                   self.theme.panel_border, self.theme.accent_panel)

        # Next piece
        draw_panel(surface, layout["next"], self.theme.panel_bg_alt,
                   self.theme.panel_border, self.theme.panel_border_bright)
        next_label = self._cached_render(self.body_font, "NEXT", self.theme.title_text)
        surface.blit(next_label, next_label.get_rect(
            centerx=layout["next"].centerx, top=layout["next"].top + 20
        ))
        if next_shape_name and next_color_id and color_palette:
            self._draw_next_preview(
                surface, layout["next"], next_shape_name, next_color_id, scale, color_palette
            )

        # Buttons
        for key, btn in [("help", self.help_button), ("quit", self.quit_button),
                         ("pause", self.pause_button)]:
            hov = layout[key].collidepoint(mouse_pos)
            btn.draw(surface, layout[key], self.body_font, self.theme, hov, hov and mouse_down)

        # Level-up flash over player board
        if level_up_timer_ms > 0:
            t = level_up_timer_ms
            alpha = int(min((2000.0 - t) / 300.0, t / 400.0, 1.0) * 255)
            lv_surf = self.title_font.render(
                f"LEVEL {player_level}!", True, (255, 255, 255)
            )
            lv_surf.set_alpha(alpha)
            surface.blit(lv_surf, lv_surf.get_rect(center=layout["player"].center))

        # Result modal
        if result is not None:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill(self.theme.overlay)
            surface.blit(overlay, (0, 0))

            result_layout = self.get_result_layout(rect)
            modal = result_layout["modal"]
            draw_panel(surface, modal, self.theme.panel_bg,
                       self.theme.panel_border, self.theme.panel_border_bright)
            result_surf = self.title_font.render(result, True, self.theme.title_text)
            surface.blit(result_surf, result_surf.get_rect(
                center=(modal.centerx, modal.top + 52)
            ))
            score_surf = self.body_font.render(
                f"You: {player_score}    AI: {ai_score}", True, self.theme.body_text
            )
            surface.blit(score_surf, score_surf.get_rect(
                center=(modal.centerx, modal.top + 110)
            ))
            for idx, (key, btn) in enumerate(
                [("restart", self.restart_button), ("menu", self.menu_button)]
            ):
                mouse_hov = result_layout[key].collidepoint(mouse_pos)
                hov = mouse_hov or focused_idx == idx
                btn.draw(surface, result_layout[key], self.body_font, self.theme,
                         hov, mouse_hov and mouse_down)

    def _draw_next_preview(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        shape_name: str,
        color_id: int,
        scale: int,
        color_palette: dict[int, tuple[int, int, int]],
    ) -> None:
        from sandtris.core.pieces import Tetromino
        piece = Tetromino(shape_name, 0, 0, color_id, scale=scale)
        inner = rect.inflate(-24, -40)
        cols = piece.shape.shape[1]
        rows = piece.shape.shape[0]
        max_grid = 4 * scale
        cell_size = min(inner.width // max_grid, inner.height // max_grid)
        if cell_size <= 0:
            return
        offset_x = inner.left + (inner.width - cols * cell_size) // 2
        offset_y = inner.top + (inner.height - rows * cell_size) // 2
        for row in range(rows):
            for col in range(cols):
                if piece.shape[row, col] == 0:
                    continue
                pygame.draw.rect(
                    surface, color_palette[piece.color_matrix[row, col]],
                    pygame.Rect(
                        offset_x + col * cell_size,
                        offset_y + row * cell_size,
                        cell_size, cell_size,
                    ),
                )

    def _blit_board(
        self, surface: pygame.Surface, board_surf: pygame.Surface, area: pygame.Rect
    ) -> None:
        inner = area.inflate(-12, -12)
        bw, bh = board_surf.get_size()
        cell = min(inner.width // bw, inner.height // bh)
        if cell <= 0:
            return
        target = (bw * cell, bh * cell)
        if self._scaled_board_surf is None or self._scaled_board_surf.get_size() != target:
            self._scaled_board_surf = pygame.Surface(target, 0, 24)
        pygame.transform.scale(board_surf, target, self._scaled_board_surf)
        rw, rh = target
        surface.blit(self._scaled_board_surf, (
            inner.left + (inner.width - rw) // 2,
            inner.top + (inner.height - rh) // 2,
        ))
