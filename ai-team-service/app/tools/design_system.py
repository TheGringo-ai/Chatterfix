"""
ChatterFix Design System
========================
Centralized design tokens and theming for consistent UI generation.

Provides:
- Color palettes (brand, semantic, grayscale)
- Typography scale
- Spacing system
- Border radii
- Shadow definitions
- Breakpoints
- Component-specific tokens
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class ColorMode(Enum):
    """Theme color modes"""
    LIGHT = "light"
    DARK = "dark"


class BreakpointSize(Enum):
    """Bootstrap breakpoint sizes"""
    XS = "xs"  # < 576px
    SM = "sm"  # >= 576px
    MD = "md"  # >= 768px
    LG = "lg"  # >= 992px
    XL = "xl"  # >= 1200px
    XXL = "xxl"  # >= 1400px


@dataclass
class ColorPalette:
    """Color palette definition"""
    primary: str
    secondary: str
    success: str
    danger: str
    warning: str
    info: str
    light: str
    dark: str

    # Extended palette
    primary_light: str = ""
    primary_dark: str = ""
    secondary_light: str = ""
    secondary_dark: str = ""

    # Grayscale
    gray_100: str = "#f8f9fa"
    gray_200: str = "#e9ecef"
    gray_300: str = "#dee2e6"
    gray_400: str = "#ced4da"
    gray_500: str = "#adb5bd"
    gray_600: str = "#6c757d"
    gray_700: str = "#495057"
    gray_800: str = "#343a40"
    gray_900: str = "#212529"

    # Semantic colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#adb5bd"
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    border: str = "#dee2e6"


@dataclass
class TypographyScale:
    """Typography definitions"""
    font_family_base: str = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    font_family_mono: str = "SFMono-Regular, Menlo, Monaco, Consolas, monospace"

    # Font sizes (rem)
    font_size_xs: str = "0.75rem"
    font_size_sm: str = "0.875rem"
    font_size_base: str = "1rem"
    font_size_lg: str = "1.125rem"
    font_size_xl: str = "1.25rem"
    font_size_2xl: str = "1.5rem"
    font_size_3xl: str = "1.875rem"
    font_size_4xl: str = "2.25rem"

    # Font weights
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_semibold: int = 600
    font_weight_bold: int = 700

    # Line heights
    line_height_tight: float = 1.25
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75


@dataclass
class SpacingScale:
    """Spacing system (based on 0.25rem = 4px base)"""
    space_0: str = "0"
    space_1: str = "0.25rem"
    space_2: str = "0.5rem"
    space_3: str = "0.75rem"
    space_4: str = "1rem"
    space_5: str = "1.25rem"
    space_6: str = "1.5rem"
    space_8: str = "2rem"
    space_10: str = "2.5rem"
    space_12: str = "3rem"


@dataclass
class BorderRadius:
    """Border radius definitions"""
    none: str = "0"
    sm: str = "0.25rem"
    base: str = "0.375rem"
    md: str = "0.5rem"
    lg: str = "0.75rem"
    xl: str = "1rem"
    full: str = "9999px"


@dataclass
class Shadows:
    """Shadow definitions"""
    none: str = "none"
    sm: str = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    base: str = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
    md: str = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    lg: str = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    xl: str = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"


@dataclass
class Breakpoints:
    """Responsive breakpoints"""
    xs: int = 0
    sm: int = 576
    md: int = 768
    lg: int = 992
    xl: int = 1200
    xxl: int = 1400


class ChatterFixTheme:
    """ChatterFix brand theme with all design tokens."""

    def __init__(self, mode: ColorMode = ColorMode.LIGHT):
        self.mode = mode
        self._init_colors()
        self.typography = TypographyScale()
        self.spacing = SpacingScale()
        self.radius = BorderRadius()
        self.shadows = Shadows()
        self.breakpoints = Breakpoints()

    def _init_colors(self):
        """Initialize color palette based on mode"""
        if self.mode == ColorMode.LIGHT:
            self.colors = ColorPalette(
                primary="#0d6efd",
                secondary="#6c757d",
                success="#198754",
                danger="#dc3545",
                warning="#ffc107",
                info="#0dcaf0",
                light="#f8f9fa",
                dark="#212529",
                primary_light="#3d8bfd",
                primary_dark="#0a58ca",
                text_primary="#212529",
                text_secondary="#6c757d",
                background="#ffffff",
                surface="#f8f9fa",
                border="#dee2e6",
            )
        else:
            self.colors = ColorPalette(
                primary="#3d8bfd",
                secondary="#adb5bd",
                success="#20c997",
                danger="#f27474",
                warning="#ffca2c",
                info="#39c0ed",
                light="#343a40",
                dark="#f8f9fa",
                primary_light="#6ea8fe",
                primary_dark="#0d6efd",
                text_primary="#f8f9fa",
                text_secondary="#adb5bd",
                background="#121212",
                surface="#1e1e1e",
                border="#343a40",
            )

    def toggle_mode(self):
        """Toggle between light and dark mode"""
        self.mode = ColorMode.DARK if self.mode == ColorMode.LIGHT else ColorMode.LIGHT
        self._init_colors()


class DesignSystem:
    """Main design system manager for UI generation."""

    def __init__(self, theme: Optional[ChatterFixTheme] = None):
        self.theme = theme or ChatterFixTheme()

    def get_css_variables(self) -> str:
        """Generate CSS custom properties from design tokens"""
        c = self.theme.colors
        t = self.theme.typography
        s = self.theme.spacing
        r = self.theme.radius

        return f""":root {{
    --cf-primary: {c.primary};
    --cf-secondary: {c.secondary};
    --cf-success: {c.success};
    --cf-danger: {c.danger};
    --cf-warning: {c.warning};
    --cf-info: {c.info};
    --cf-text-primary: {c.text_primary};
    --cf-text-secondary: {c.text_secondary};
    --cf-background: {c.background};
    --cf-surface: {c.surface};
    --cf-border: {c.border};
    --cf-font-family: {t.font_family_base};
    --cf-font-size-base: {t.font_size_base};
    --cf-space-4: {s.space_4};
    --cf-radius: {r.base};
}}"""

    def get_utility_classes(self) -> str:
        """Generate ChatterFix-specific utility classes"""
        return """.cf-status-open { color: var(--cf-info); }
.cf-status-in-progress { color: var(--cf-warning); }
.cf-status-completed { color: var(--cf-success); }
.cf-status-critical { color: var(--cf-danger); }
.cf-priority-low { border-left: 4px solid var(--cf-info); }
.cf-priority-medium { border-left: 4px solid var(--cf-warning); }
.cf-priority-high { border-left: 4px solid #fd7e14; }
.cf-priority-critical { border-left: 4px solid var(--cf-danger); }
.cf-touch-target { min-height: 44px; min-width: 44px; }
.cf-voice-active { animation: pulse 1.5s infinite; }
@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(13, 110, 253, 0); }
    100% { box-shadow: 0 0 0 0 rgba(13, 110, 253, 0); }
}"""

    def get_component_tokens(self, component: str) -> Dict[str, Any]:
        """Get design tokens for a specific component"""
        tokens = {
            "button": {
                "padding_x": self.theme.spacing.space_4,
                "padding_y": self.theme.spacing.space_2,
                "border_radius": self.theme.radius.base,
                "min_height_touch": "44px",
            },
            "card": {
                "padding": self.theme.spacing.space_4,
                "border_radius": self.theme.radius.md,
                "shadow": self.theme.shadows.base,
            },
            "input": {
                "padding": self.theme.spacing.space_3,
                "border_radius": self.theme.radius.base,
                "border_color": self.theme.colors.border,
                "min_height_touch": "44px",
            },
        }
        return tokens.get(component, {})

    def get_color_for_status(self, status: str) -> str:
        """Get appropriate color for work order status"""
        status_colors = {
            "open": self.theme.colors.info,
            "in_progress": self.theme.colors.warning,
            "completed": self.theme.colors.success,
            "critical": self.theme.colors.danger,
            "pending": self.theme.colors.secondary,
        }
        return status_colors.get(status.lower(), self.theme.colors.secondary)

    def get_color_for_priority(self, priority: str) -> str:
        """Get appropriate color for priority level"""
        priority_colors = {
            "low": self.theme.colors.info,
            "medium": self.theme.colors.warning,
            "high": "#fd7e14",
            "critical": self.theme.colors.danger,
        }
        return priority_colors.get(priority.lower(), self.theme.colors.secondary)

    def to_dict(self) -> Dict[str, Any]:
        """Export design system as dictionary"""
        return {
            "mode": self.theme.mode.value,
            "colors": {
                "primary": self.theme.colors.primary,
                "secondary": self.theme.colors.secondary,
                "success": self.theme.colors.success,
                "danger": self.theme.colors.danger,
                "warning": self.theme.colors.warning,
                "info": self.theme.colors.info,
            },
            "typography": {
                "font_family": self.theme.typography.font_family_base,
            },
            "breakpoints": {
                "sm": self.theme.breakpoints.sm,
                "md": self.theme.breakpoints.md,
                "lg": self.theme.breakpoints.lg,
            },
        }
