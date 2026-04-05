from dataclasses import dataclass

import pygame


from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


@dataclass(frozen=True)
class ScreenLayout:
    hud_rect: pygame.Rect
    board_rect: pygame.Rect
    side_rect: pygame.Rect
    next_rect: pygame.Rect
    pause_rect: pygame.Rect


class GameplayScreen:
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

    def get_layout(self, surface_rect: pygame.Rect) -> ScreenLayout:
        m = self.dims.margin
        g = self.dims.gap
        side_width = max(self.dims.side_min_width, surface_rect.width // 4)

        hud_rect = pygame.Rect(
            m,
            m,
            surface_rect.width - m * 2,
            self.dims.hud_height,
        )
        content_top = hud_rect.bottom + g
        content_height = surface_rect.height - content_top - m
        board_width = surface_rect.width - m * 2 - side_width - g

        board_rect = pygame.Rect(m, content_top, board_width, content_height)
        side_rect = pygame.Rect(
            board_rect.right + g, content_top, side_width, content_height
        )
        next_rect = pygame.Rect(
            side_rect.left + m,
            side_rect.top + m,
            side_rect.width - m * 2,
            self.dims.next_panel_height,
        )
        pause_rect = pygame.Rect(
            side_rect.left + m,
            side_rect.bottom - self.dims.button_height - m,
            side_rect.width - m * 2,
            self.dims.button_height,
        )

        return ScreenLayout(
            hud_rect=hud_rect,
            board_rect=board_rect,
            side_rect=side_rect,
            next_rect=next_rect,
            pause_rect=pause_rect,
        )

    def pause_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect).pause_rect.collidepoint(pos)

    def _draw_next_preview(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        shape_name: str | None,
        color_id: int | None,
        scale: int,
        color_palette: dict[int, tuple[int, int, int]],
    ) -> None:
        if shape_name is None or color_id is None:
            return

        from sandtris.core.pieces import Tetromino

        piece = Tetromino(shape_name, 0, 0, color_id, scale=scale)

        inner = rect.inflate(-24, -40)

        cols = piece.shape.shape[1]
        rows = piece.shape.shape[0]

        max_grid = 4 * scale
        cell_size = min(inner.width // max_grid, inner.height // max_grid)
        if cell_size <= 0:
            return

        preview_width = cols * cell_size
        preview_height = rows * cell_size
        offset_x = inner.left + (inner.width - preview_width) // 2
        offset_y = inner.top + (inner.height - preview_height) // 2

        for row in range(rows):
            for col in range(cols):
                if piece.shape[row, col] == 0:
                    continue
                color_val = piece.color_matrix[row, col]
                actual_color = color_palette[color_val]
                cell_rect = pygame.Rect(
                    offset_x + col * cell_size,
                    offset_y + row * cell_size,
                    cell_size,
                    cell_size,
                )
                pygame.draw.rect(surface, actual_color, cell_rect)

    def draw(
        self,
        surface: pygame.Surface,
        board_surface: pygame.Surface,
        score: int,
        level: int,
        combo: int,
        fps: int,
        next_shape_name: str | None,
        next_color_id: int | None,
        scale: int,
        color_palette: dict[int, tuple[int, int, int]],
        mouse_pos: tuple[int, int],
        mouse_down: bool,
    ) -> None:
        surface.fill(self.theme.screen_bg)
        layout = self.get_layout(surface.get_rect())

        draw_panel(
            surface,
            layout.hud_rect,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )
        draw_panel(
            surface,
            layout.board_rect,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )
        draw_panel(
            surface,
            layout.side_rect,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.accent_panel,
        )

        board_inner = layout.board_rect.inflate(-16, -16)
        board_w, board_h = board_surface.get_size()

        cell_size = min(
            board_inner.width // board_w, board_inner.height // board_h
        )
        if cell_size > 0:
            render_w = board_w * cell_size
            render_h = board_h * cell_size
            scaled_board = pygame.transform.scale(
                board_surface, (render_w, render_h)
            )
            center_x = board_inner.left + (board_inner.width - render_w) // 2
            center_y = board_inner.top + (board_inner.height - render_h) // 2
            surface.blit(scaled_board, (center_x, center_y))

        title = self.title_font.render("SANDTRIS", True, self.theme.title_text)
        title_rect = title.get_rect(
            left=layout.hud_rect.left + 24, centery=layout.hud_rect.top + 32
        )
        surface.blit(title, title_rect)

        score_text = self.body_font.render(
            f"Score {score}", True, self.theme.body_text
        )
        level_text = self.body_font.render(
            f"Level {level}", True, self.theme.body_text
        )
        combo_text = self.body_font.render(
            f"Combo {combo}x", True, self.theme.body_text
        )
        fps_text = self.body_font.render(
            f"FPS {fps}", True, self.theme.accent_text
        )

        score_rect = score_text.get_rect(
            centerx=layout.hud_rect.centerx, centery=layout.hud_rect.top + 32
        )
        combo_rect = combo_text.get_rect(
            centerx=layout.hud_rect.centerx, centery=layout.hud_rect.top + 64
        )
        level_rect = level_text.get_rect(
            left=layout.hud_rect.left + 24, centery=layout.hud_rect.top + 64
        )
        fps_rect = fps_text.get_rect(
            right=layout.hud_rect.right - 24, centery=layout.hud_rect.top + 64
        )

        surface.blit(score_text, score_rect)
        surface.blit(level_text, level_rect)
        surface.blit(combo_text, combo_rect)
        surface.blit(fps_text, fps_rect)

        draw_panel(
            surface,
            layout.next_rect,
            self.theme.panel_bg_alt,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )
        next_title = self.body_font.render("NEXT", True, self.theme.title_text)
        next_title_rect = next_title.get_rect(
            centerx=layout.next_rect.centerx, top=layout.next_rect.top + 20
        )
        surface.blit(next_title, next_title_rect)
        self._draw_next_preview(
            surface,
            layout.next_rect,
            next_shape_name,
            next_color_id,
            scale,
            color_palette,
        )

        hovered = layout.pause_rect.collidepoint(mouse_pos)
        self.pause_button.draw(
            surface,
            layout.pause_rect,
            self.body_font,
            self.theme,
            hovered,
            hovered and mouse_down,
        )
