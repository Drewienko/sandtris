import pygame

from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class HighScoresScreen:
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
        w = min(560, surface_rect.width - 40)
        h = min(820, surface_rect.height - 40)
        panel = pygame.Rect(0, 0, w, h)
        panel.center = surface_rect.center
        margin = self.dims.modal_button_margin
        btn_h = self.dims.modal_button_height
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
        high_scores: list,
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
            "HIGH SCORES", True, self.theme.title_text
        )
        surface.blit(
            title, title.get_rect(center=(panel.centerx, panel.top + 46))
        )

        line_h = self.body_font.get_linesize()
        margin = self.dims.modal_button_margin

        if not high_scores:
            msg = self.body_font.render(
                "No scores yet!", True, self.theme.body_text
            )
            surface.blit(
                msg, msg.get_rect(center=(panel.centerx, panel.top + 120))
            )
        else:
            col_labels = ["#", "PLAYER", "SCORE", "LV", "COMBO", "DATE"]
            col_xs = [
                panel.left + margin,
                panel.left + margin + 28,
                panel.left + margin + 130,
                panel.left + margin + 230,
                panel.left + margin + 270,
                panel.right - margin,
            ]
            col_anchors = ["left", "left", "left", "left", "left", "right"]

            header_y = panel.top + 88
            for label, x, anchor in zip(col_labels, col_xs, col_anchors):
                surf = self.body_font.render(label, True, self.theme.body_text)
                rect = surf.get_rect(top=header_y)
                setattr(rect, anchor, x)
                surface.blit(surf, rect)

            sep_y = header_y + line_h + line_h // 4
            pygame.draw.line(
                surface,
                self.theme.panel_border,
                (panel.left + margin, sep_y),
                (panel.right - margin, sep_y),
                1,
            )

            y = sep_y + line_h // 2

            for rank, entry in enumerate(high_scores[:10], start=1):
                color = (
                    self.theme.accent_text if rank == 1 else self.theme.title_text
                )
                row = [
                    str(rank),
                    entry.get("player", "—"),
                    str(entry.get("score", 0)),
                    str(entry.get("level", 0)),
                    f"{entry.get('max_combo', 0)}x",
                    entry.get("date", "—"),
                ]
                for val, x, anchor in zip(row, col_xs, col_anchors):
                    surf = self.body_font.render(val, True, color)
                    rect = surf.get_rect(top=y)
                    setattr(rect, anchor, x)
                    surface.blit(surf, rect)
                y += line_h + line_h // 4

        hov = layout["back"].collidepoint(mouse_pos)
        self.back_button.draw(
            surface,
            layout["back"],
            self.body_font,
            self.theme,
            hov,
            hov and mouse_down,
        )
