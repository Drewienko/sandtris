import pygame

from sandtris.render.ui import (
    SAND_PALETTE_PRESETS,
    THEME_PRESETS,
    PixelButton,
    ThemeColors,
    UIDimensions,
    draw_panel,
)


class SettingsScreen:
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
        self.name_field_active = False

    def get_layout(self, surface_rect: pygame.Rect) -> dict[str, pygame.Rect]:
        margin = self.dims.margin * 2
        gap = self.dims.gap
        panel = surface_rect.inflate(-margin * 2, -margin * 2)
        title_height = 80
        name_row_height = 56
        back_height = self.dims.modal_button_height + gap * 2
        sections_top = panel.top + title_height + name_row_height + gap * 2
        sections_height = panel.height - title_height - name_row_height - back_height - gap * 3
        section_width = (panel.width - gap) // 2

        name_row = pygame.Rect(
            panel.left + gap,
            panel.top + title_height,
            panel.width - gap * 2,
            name_row_height,
        )
        theme_section = pygame.Rect(
            panel.left + gap,
            sections_top,
            section_width - gap,
            sections_height,
        )
        sand_section = pygame.Rect(
            theme_section.right + gap,
            sections_top,
            panel.width - section_width - gap * 2,
            sections_height,
        )
        back_rect = pygame.Rect(
            panel.left + gap,
            panel.bottom - self.dims.modal_button_height - gap,
            panel.width - gap * 2,
            self.dims.modal_button_height,
        )

        return {
            "panel": panel,
            "name_row": name_row,
            "theme_section": theme_section,
            "sand_section": sand_section,
            "back": back_rect,
        }

    def name_field_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        layout = self.get_layout(surface_rect)
        field_rect = self._name_field_rect(layout["name_row"])
        return field_rect.collidepoint(pos)

    def _name_field_rect(self, name_row: pygame.Rect) -> pygame.Rect:
        field_width = name_row.width // 2
        return pygame.Rect(
            name_row.right - field_width,
            name_row.top + 8,
            field_width,
            name_row.height - 16,
        )

    def back_button_contains(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> bool:
        return self.get_layout(surface_rect)["back"].collidepoint(pos)

    def get_theme_hitboxes(
        self, surface_rect: pygame.Rect
    ) -> dict[str, pygame.Rect]:
        layout = self.get_layout(surface_rect)
        section = layout["theme_section"]
        margin = self.dims.margin
        gap = self.dims.gap
        card_height = 92
        hitboxes: dict[str, pygame.Rect] = {}
        for index, name in enumerate(THEME_PRESETS):
            hitboxes[name] = pygame.Rect(
                section.left + margin,
                section.top + 44 + index * (card_height + gap),
                section.width - margin * 2,
                card_height,
            )
        return hitboxes

    def get_sand_hitboxes(
        self, surface_rect: pygame.Rect
    ) -> dict[str, pygame.Rect]:
        layout = self.get_layout(surface_rect)
        section = layout["sand_section"]
        margin = self.dims.margin
        gap = self.dims.gap
        card_height = 92
        hitboxes: dict[str, pygame.Rect] = {}
        for index, name in enumerate(SAND_PALETTE_PRESETS):
            hitboxes[name] = pygame.Rect(
                section.left + margin,
                section.top + 44 + index * (card_height + gap),
                section.width - margin * 2,
                card_height,
            )
        return hitboxes

    def theme_at(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> str | None:
        for name, rect in self.get_theme_hitboxes(surface_rect).items():
            if rect.collidepoint(pos):
                return name
        return None

    def sand_palette_at(
        self, surface_rect: pygame.Rect, pos: tuple[int, int]
    ) -> str | None:
        for name, rect in self.get_sand_hitboxes(surface_rect).items():
            if rect.collidepoint(pos):
                return name
        return None

    def _draw_palette_preview(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        colors: dict[int, tuple[int, int, int]],
    ) -> None:
        swatch_size = min(18, max(10, rect.height // 4))
        start_x = rect.right - swatch_size * 4 - self.dims.margin
        start_y = rect.centery - swatch_size
        for index, color in enumerate(colors.values()):
            swatch_rect = pygame.Rect(
                start_x + (index % 4) * swatch_size,
                start_y + (index // 4) * swatch_size,
                swatch_size,
                swatch_size,
            )
            pygame.draw.rect(surface, color, swatch_rect)

    def draw(
        self,
        surface: pygame.Surface,
        selected_theme: str,
        selected_sand_palette: str,
        player_name: str,
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
            self.dims,
        )

        title = self.title_font.render("SETTINGS", True, self.theme.title_text)
        surface.blit(
            title, title.get_rect(center=(panel.centerx, panel.top + 36))
        )

        name_row = layout["name_row"]
        label = self.body_font.render("PLAYER NAME", True, self.theme.body_text)
        surface.blit(
            label,
            label.get_rect(left=name_row.left + self.dims.margin, centery=name_row.centery),
        )
        field_rect = self._name_field_rect(name_row)
        border_color = (
            self.theme.panel_border_bright
            if self.name_field_active
            else self.theme.panel_border
        )
        pygame.draw.rect(
            surface, self.theme.panel_bg_alt, field_rect, border_radius=3
        )
        pygame.draw.rect(
            surface, border_color, field_rect, 2, border_radius=3
        )
        display = f"{player_name}_" if self.name_field_active else player_name
        name_surf = self.body_font.render(display, True, self.theme.title_text)
        surface.blit(
            name_surf,
            name_surf.get_rect(
                left=field_rect.left + 8, centery=field_rect.centery
            ),
        )

        theme_section = layout["theme_section"]
        sand_section = layout["sand_section"]
        draw_panel(
            surface,
            theme_section,
            self.theme.panel_bg_alt,
            self.theme.panel_border,
            self.theme.panel_border_bright,
            self.dims,
        )
        draw_panel(
            surface,
            sand_section,
            self.theme.panel_bg_alt,
            self.theme.panel_border,
            self.theme.panel_border_bright,
            self.dims,
        )

        theme_title = self.body_font.render(
            "THEMES", True, self.theme.title_text
        )
        sand_title = self.body_font.render(
            "SAND COLORS", True, self.theme.title_text
        )
        surface.blit(
            theme_title,
            (theme_section.left + self.dims.margin, theme_section.top + 12),
        )
        surface.blit(
            sand_title,
            (sand_section.left + self.dims.margin, sand_section.top + 12),
        )

        for name, rect in self.get_theme_hitboxes(surface.get_rect()).items():
            preview_theme = THEME_PRESETS[name]
            border = preview_theme.panel_border_bright
            trim = preview_theme.title_text
            if name != selected_theme:
                border = self.theme.panel_border
                trim = self.theme.panel_border_bright
            draw_panel(
                surface, rect, preview_theme.panel_bg, border, trim, self.dims
            )
            label = self.body_font.render(
                name.upper(), True, preview_theme.body_text
            )
            surface.blit(
                label,
                label.get_rect(left=rect.left + 14, centery=rect.centery),
            )
            accent_rect = pygame.Rect(rect.right - 58, rect.centery - 18, 36, 36)
            pygame.draw.rect(surface, preview_theme.accent_panel, accent_rect)
            pygame.draw.rect(surface, preview_theme.title_text, accent_rect, 2)

        for name, rect in self.get_sand_hitboxes(surface.get_rect()).items():
            border = (
                self.theme.panel_border_bright
                if name == selected_sand_palette
                else self.theme.panel_border
            )
            draw_panel(
                surface,
                rect,
                self.theme.panel_bg,
                border,
                self.theme.panel_border_bright,
                self.dims,
            )
            label = self.body_font.render(
                name.upper(), True, self.theme.body_text
            )
            surface.blit(
                label,
                label.get_rect(left=rect.left + 14, centery=rect.centery),
            )
            self._draw_palette_preview(
                surface, rect, SAND_PALETTE_PRESETS[name]
            )

        back_rect = layout["back"]
        hovered = back_rect.collidepoint(mouse_pos)
        self.back_button.draw(
            surface,
            back_rect,
            self.body_font,
            self.theme,
            hovered,
            hovered and mouse_down,
        )
