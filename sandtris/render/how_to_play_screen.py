import pygame

from sandtris.core.config import GameConfig
from sandtris.render.ui import (
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


def _wrap(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if font.size(candidate)[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [""]


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

    def _build_items(
        self, config: GameConfig, max_text_width: int, line_h: int
    ) -> tuple[list[tuple], int]:
        """Return (items, total_content_height). Items are render descriptors."""
        items: list[tuple] = []
        h = 0

        for raw in [
            "Pieces turn into sand on impact.",
            "Sand cascades down and settles.",
            "Clear sand by connecting a continuous path of the same color"
            " from the left wall to the right wall.",
        ]:
            for line in _wrap(self.body_font, raw, max_text_width):
                items.append(("center", line, self.theme.body_text))
                h += line_h

        items.append(("gap", line_h * 2))
        h += line_h * 2

        items.append(("center", "COMBO:", self.theme.title_text))
        h += line_h
        items.append(("gap", line_h // 2))
        h += line_h // 2

        for line in _wrap(
            self.body_font,
            "Clear again before the bar runs out"
            " to chain combos and multiply score.",
            max_text_width,
        ):
            items.append(("center", line, self.theme.body_text))
            h += line_h

        items.append(("gap", line_h * 2))
        h += line_h * 2

        items.append(("center", "CONTROLS:", self.theme.title_text))
        h += line_h
        items.append(("gap", line_h // 2))
        h += line_h // 2

        controls = [
            (config.key_left, "Move Left"),
            (config.key_right, "Move Right"),
            (config.key_up, "Rotate"),
            (config.key_down, "Soft Drop"),
            (config.key_drop, "Hard Drop"),
            (config.key_pause, "Pause"),
            (config.key_restart, "Restart when game ends"),
            (config.key_mute, "Mute / Unmute"),
        ]
        for keys, action in controls:
            keys_str = " / ".join(pygame.key.name(k).upper() for k in keys)
            items.append(("control", keys_str, action))
            h += line_h + line_h // 4

        return items, h

    def get_layout(
        self, surface_rect: pygame.Rect, config: GameConfig
    ) -> dict[str, pygame.Rect]:
        margin = self.dims.modal_button_margin
        btn_h = self.dims.modal_button_height
        panel_width = min(600, surface_rect.width - 40)
        line_h = self.body_font.get_linesize()

        _, content_h = self._build_items(config, panel_width - margin * 2, line_h)

        panel_height = min(
            100 + content_h + btn_h + margin * 2,
            surface_rect.height - 40,
        )

        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.center = surface_rect.center

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
        self,
        surface_rect: pygame.Rect,
        pos: tuple[int, int],
        config: GameConfig,
    ) -> bool:
        return self.get_layout(surface_rect, config)["back"].collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        config: GameConfig,
        mouse_pos: tuple[int, int],
        mouse_down: bool,
    ) -> None:
        surface.fill(self.theme.screen_bg)

        margin = self.dims.modal_button_margin
        line_h = self.body_font.get_linesize()
        layout = self.get_layout(surface.get_rect(), config)
        panel = layout["panel"]
        max_text_width = panel.width - margin * 2

        draw_panel(
            surface,
            panel,
            self.theme.panel_bg,
            self.theme.panel_border,
            self.theme.panel_border_bright,
        )

        title = self.title_font.render("HOW TO PLAY", True, self.theme.title_text)
        surface.blit(title, title.get_rect(center=(panel.centerx, panel.top + 46)))

        items, _ = self._build_items(config, max_text_width, line_h)
        y = panel.top + 100

        for item in items:
            kind = item[0]
            if kind == "gap":
                y += item[1]
            elif kind == "center":
                surf = self.body_font.render(item[1], True, item[2])
                surface.blit(surf, surf.get_rect(centerx=panel.centerx, top=y))
                y += line_h
            elif kind == "control":
                keys_surf = self.body_font.render(
                    item[1], True, self.theme.title_text
                )
                action_surf = self.body_font.render(
                    item[2], True, self.theme.body_text
                )
                action_x = panel.right - margin - action_surf.get_width()
                keys_right = panel.left + margin + keys_surf.get_width()
                if action_x < keys_right + line_h:
                    action_x = keys_right + line_h
                surface.blit(
                    keys_surf,
                    keys_surf.get_rect(left=panel.left + margin, top=y),
                )
                surface.blit(
                    action_surf,
                    action_surf.get_rect(left=action_x, top=y),
                )
                y += line_h + line_h // 4

        hov_back = layout["back"].collidepoint(mouse_pos)
        self.back_button.draw(
            surface,
            layout["back"],
            self.body_font,
            self.theme,
            hov_back,
            hov_back and mouse_down,
        )
