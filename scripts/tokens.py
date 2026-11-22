#!/usr/bin/env python3
"""
tokens.py
Tailwind CSS Semantic Token System & Draw-Time WCAG 2.1 Contrast Guard for SlideCanvas (1280x720 px).

Conventions:
- Color hex values returned by `clean_hex6`, `rgb_to_hex`, `blend_alpha`,
  `TokenResolver.resolve_color_alpha`, `TokenResolver.ensure_contrast`, and
  `SlideTheme.to_palette_dict` are 6-character uppercase hex without `#`
  (e.g. `"0F172A"`), or `"NONE"` for transparent/empty fills (matching OpenXML
  `srgbClr/@val` expected by `slide_canvas.py`).
- All color helpers accept hex inputs with or without a leading `#` (3- or 6-char).
- `TYPOGRAPHY_SCALE` entries are explicitly `(font_size_pt, line_height_multiplier)`
  in PowerPoint points (`pt`) and must NEVER be converted through `px()`.
- `RADIUS_PX` and `TokenResolver.resolve_spacing()` values are in 1280x720 canvas `px`.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, FrozenSet, Optional, Tuple

SHADE_STEPS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]

# Canonical 22 Tailwind CSS v3.4 color families x 11 shades (50..950)
_TAILWIND_FAMILIES: Dict[str, Tuple[str, ...]] = {
    "slate":   ("#F8FAFC", "#F1F5F9", "#E2E8F0", "#CBD5E1", "#94A3B8", "#64748B", "#475569", "#334155", "#1E293B", "#0F172A", "#020617"),
    "gray":    ("#F9FAFB", "#F3F4F6", "#E5E7EB", "#D1D5DB", "#9CA3AF", "#6B7280", "#4B5563", "#374151", "#1F2937", "#111827", "#030712"),
    "zinc":    ("#FAFAFA", "#F4F4F5", "#E4E4E7", "#D4D4D8", "#A1A1AA", "#71717A", "#52525B", "#3F3F46", "#27272A", "#18181B", "#09090B"),
    "neutral": ("#FAFAFA", "#F5F5F5", "#E5E5E5", "#D4D4D4", "#A3A3A3", "#737373", "#525252", "#404040", "#262626", "#171717", "#0A0A0A"),
    "stone":   ("#FAFAF9", "#F5F5F4", "#E7E5E4", "#D6D3D1", "#A8A29E", "#78716C", "#57534E", "#44403C", "#292524", "#1C1917", "#0C0A09"),
    "red":     ("#FEF2F2", "#FEE2E2", "#FECACA", "#FCA5A5", "#F87171", "#EF4444", "#DC2626", "#B91C1C", "#991B1B", "#7F1D1D", "#450A0A"),
    "orange":  ("#FFF7ED", "#FFEDD5", "#FED7AA", "#FDBA74", "#FB923C", "#F97316", "#EA580C", "#C2410C", "#9A3412", "#7C2D12", "#431407"),
    "amber":   ("#FFFBEB", "#FEF3C7", "#FDE68A", "#FCD34D", "#FBBF24", "#F59E0B", "#D97706", "#B45309", "#92400E", "#78350F", "#451A03"),
    "yellow":  ("#FEFCE8", "#FEF9C3", "#FEF08A", "#FDE047", "#FACC15", "#EAB308", "#CA8A04", "#A16207", "#854D0E", "#713F12", "#422006"),
    "lime":    ("#F7FEE7", "#ECFCCB", "#D9F99D", "#BEF264", "#A3E635", "#84CC16", "#65A30D", "#4D7C0F", "#3F6212", "#365314", "#1A2E05"),
    "green":   ("#F0FDF4", "#DCFCE7", "#BBF7D0", "#86EFAC", "#4ADE80", "#22C55E", "#16A34A", "#15803D", "#166534", "#14532D", "#052E16"),
    "emerald": ("#ECFDF5", "#D1FAE5", "#A7F3D0", "#6EE7B7", "#34D399", "#10B981", "#059669", "#047857", "#065F46", "#064E3B", "#022C22"),
    "teal":    ("#F0FDFA", "#CCFBF1", "#99F6E4", "#5EEAD4", "#2DD4BF", "#14B8A6", "#0D9488", "#0F766E", "#115E59", "#134E4A", "#042F2E"),
    "cyan":    ("#ECFEFF", "#CFFAFE", "#A5F3FC", "#67E8F9", "#22D3EE", "#06B6D4", "#0891B2", "#0E7490", "#155E75", "#164E63", "#083344"),
    "sky":     ("#F0F9FF", "#E0F2FE", "#BAE6FD", "#7DD3FC", "#38BDF8", "#0EA5E9", "#0284C7", "#0369A1", "#075985", "#0C4A6E", "#082F49"),
    "blue":    ("#EFF6FF", "#DBEAFE", "#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8", "#1E40AF", "#1E3A8A", "#172554"),
    "indigo":  ("#EEF2FF", "#E0E7FF", "#C7D2FE", "#A5B4FC", "#818CF8", "#6366F1", "#4F46E5", "#4338CA", "#3730A3", "#312E81", "#1E1B4B"),
    "violet":  ("#F5F3FF", "#EDE9FE", "#DDD6FE", "#C4B5FD", "#A78BFA", "#8B5CF6", "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95", "#2E1065"),
    "purple":  ("#FAF5FF", "#F3E8FF", "#E9D5FF", "#D8B4FE", "#C084FC", "#A855F7", "#9333EA", "#7E22CE", "#6B21A8", "#581C87", "#3B0764"),
    "fuchsia": ("#FDF4FF", "#FAE8FF", "#F5D0FE", "#F0ABFC", "#E879F9", "#D946EF", "#C026D3", "#A21CAF", "#86198F", "#701A75", "#4A044E"),
    "pink":    ("#FDF2F8", "#FCE7F3", "#FBCFE8", "#F9A8D4", "#F472B6", "#EC4899", "#DB2777", "#BE185D", "#9D174D", "#831843", "#500724"),
    "rose":    ("#FFF1F2", "#FFE4E6", "#FECDD3", "#FDA4AF", "#FB7185", "#F43F5E", "#E11D48", "#BE123C", "#9F1239", "#881337", "#4C0519"),
}

TAILWIND_PALETTE: Dict[str, str] = {
    f"{family}-{shade}": hex_val
    for family, shades in _TAILWIND_FAMILIES.items()
    for shade, hex_val in zip(SHADE_STEPS, shades)
}
TAILWIND_PALETTE["white"] = "#FFFFFF"
TAILWIND_PALETTE["black"] = "#000000"
TAILWIND_PALETTE["transparent"] = "NONE"

# Reverse map from 6-char hex -> (family, shade) for semantic accent shade stepping
_HEX_TO_TAILWIND: Dict[str, Tuple[str, int]] = {}
for _fam, _shades in _TAILWIND_FAMILIES.items():
    for _shade, _hx in zip(SHADE_STEPS, _shades):
        _HEX_TO_TAILWIND.setdefault(_hx.lstrip("#").upper(), (_fam, _shade))

# PowerPoint typography scale: (pt_size, line_height) — NEVER pass pt_size into px()
TYPOGRAPHY_SCALE: Dict[str, Tuple[float, float]] = {
    "text-xs": (10.0, 1.20),
    "text-sm": (12.0, 1.40),
    "text-base": (14.0, 1.32),
    "text-lg": (16.5, 1.25),
    "text-xl": (20.0, 1.20),
    "text-2xl": (24.0, 1.15),
    "text-3xl": (29.0, 1.12),
    "text-4xl": (36.0, 1.08),
    "text-5xl": (44.0, 1.05),
}

# Corner radius tokens in 1280x720 px space
RADIUS_PX: Dict[str, float] = {
    "rounded-none": 0.0,
    "rounded-sm": 4.0,
    "rounded-md": 7.0,
    "rounded-lg": 10.0,
    "rounded-xl": 12.0,
    "rounded-2xl": 18.0,
    "rounded-3xl": 24.0,
    "rounded-full": 999.0,
}

# Card visual variants resolved at draw time against effective local background
CARD_VARIANTS: Dict[str, Dict[str, Any]] = {
    "default": {
        "fill": "surface",
        "stroke": "border",
        "border_pt": 0.75,
        "dash": "solid",
    },
    "accent": {
        "fill": "accent/10",
        "stroke": "accent/45",
        "border_pt": 1.25,
        "dash": "solid",
    },
    "subtle": {
        "fill": "surface2/50",
        "stroke": "border/50",
        "border_pt": 0.5,
        "dash": "solid",
    },
    "dashed": {
        "fill": "none",
        "stroke": "border",
        "border_pt": 1.0,
        "dash": "dash",
    },
}

_HEX_CHARS = frozenset("0123456789ABCDEF")
_TW_TOKEN_RE = re.compile(r"^([a-z]+)-(\d+)$")
_SPACING_RE = re.compile(r"^(?:gap|p|px|py|m)?-?(\d+(?:\.\d+)?)$")
_NONE_TOKENS = frozenset(("", "none", "transparent", "clear"))
_PRIMARY_INK_ALIASES = frozenset(("ink", "ink_primary", "text_primary"))


# ---------------------------------------------------------------------------
# Color Math Helpers (6-char uppercase hex without `#`, or `"NONE"`)
# ---------------------------------------------------------------------------
def clean_hex6(h: Optional[str]) -> str:
    """Normalize a hex color string to 6-char uppercase hex without `#`, or `"NONE"`."""
    if h is None:
        return "NONE"
    s = str(h).strip()
    if s.lower() in _NONE_TOKENS:
        return "NONE"
    raw = s.lstrip("#").upper()
    if len(raw) == 3 and all(ch in _HEX_CHARS for ch in raw):
        return "".join(ch * 2 for ch in raw)
    if len(raw) == 6 and all(ch in _HEX_CHARS for ch in raw):
        return raw
    raise ValueError(f"Invalid hex color: {h!r}")


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    """Convert a 3- or 6-char hex string (with or without `#`) to `(r, g, b)` ints in 0..255."""
    hx = clean_hex6(h)
    if hx == "NONE":
        raise ValueError(f"Cannot convert transparent color {h!r} to RGB")
    return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert `(r, g, b)` integers in 0..255 to 6-char uppercase hex without `#`."""
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb)
    return f"{r:02X}{g:02X}{b:02X}"


def relative_luminance(h: str) -> float:
    """Compute WCAG 2.1 relative luminance in `[0.0, 1.0]` for a hex color."""
    r, g, b = hex_to_rgb(h)
    lin = []
    for channel in (r, g, b):
        c = channel / 255.0
        lin.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _raw_contrast_ratio(h1: str, h2: str) -> float:
    l1 = relative_luminance(h1)
    l2 = relative_luminance(h2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


def contrast_ratio(h1: str, h2: str) -> float:
    """Compute WCAG contrast ratio (rounded to 2 decimals) between two hex colors."""
    return round(_raw_contrast_ratio(h1, h2), 2)


def blend_alpha(fg_hex: str, bg_hex: str, alpha: float) -> str:
    """Alpha-composite `fg_hex` over `bg_hex` and return 6-char uppercase hex without `#`."""
    fg = clean_hex6(fg_hex)
    bg = clean_hex6(bg_hex)
    if fg == "NONE":
        return bg
    if bg == "NONE":
        return fg
    a = max(0.0, min(1.0, float(alpha)))
    fr, fg_c, fb = hex_to_rgb(fg)
    br, bg_c, bb = hex_to_rgb(bg)
    return rgb_to_hex(
        (
            round(fr * a + br * (1.0 - a)),
            round(fg_c * a + bg_c * (1.0 - a)),
            round(fb * a + bb * (1.0 - a)),
        )
    )


# ---------------------------------------------------------------------------
# TokenResolver & SlideTheme
# ---------------------------------------------------------------------------
def _split_color_modifiers(expr: str) -> Tuple[str, Optional[float], Optional[float]]:
    """Split `<base>[/<pct>][@<alpha>]` (in either order) into `(base, slash_alpha, at_alpha)`."""
    s = expr.strip()
    slash_str: Optional[str] = None
    at_str: Optional[str] = None

    if "@" in s:
        left, right = s.split("@", 1)
        if "/" in left:
            base, slash_str = left.split("/", 1)
            at_str = right
        elif "/" in right:
            base = left
            at_str, slash_str = right.split("/", 1)
        else:
            base, at_str = left, right
    elif "/" in s:
        base, slash_str = s.split("/", 1)
    else:
        base = s

    slash_alpha: Optional[float] = None
    if slash_str is not None and slash_str.strip():
        st = slash_str.strip()
        try:
            val = float(st)
            slash_alpha = val if st.startswith(("0.", ".")) and val <= 1.0 else val / 100.0
            slash_alpha = max(0.0, min(1.0, slash_alpha))
        except ValueError:
            slash_alpha = None

    at_alpha: Optional[float] = None
    if at_str is not None and at_str.strip():
        try:
            at_alpha = max(0.0, min(1.0, float(at_str.strip())))
        except ValueError:
            at_alpha = None

    return base.strip(), slash_alpha, at_alpha


def _lookup_palette(token: str, palette: Optional[Dict[str, str]]) -> Optional[str]:
    if not palette:
        return None
    if token in palette:
        return str(palette[token])
    tl = token.lower()
    if tl in palette:
        return str(palette[tl])
    return None


class TokenResolver:
    """Stateless resolver for Tailwind colors, semantic roles, spacing, radii, typography, and WCAG contrast."""

    @classmethod
    def parse_color_family(cls, expr: Any) -> Tuple[Optional[str], Optional[int]]:
        """Return `(family, shade)` if `expr` is a Tailwind `{family}-{shade}` token, else `(None, None)`."""
        if expr is None:
            return (None, None)
        s = str(expr).strip().lower()
        m = _TW_TOKEN_RE.match(s)
        if not m:
            return (None, None)
        family, shade = m.group(1), int(m.group(2))
        if family in _TAILWIND_FAMILIES and shade in SHADE_STEPS:
            return (family, shade)
        return (None, None)

    @classmethod
    def _resolve_base_hex(
        cls,
        token: str,
        base_bg_hex: str,
        palette: Optional[Dict[str, str]],
        default: Optional[str],
        seen: FrozenSet[str],
    ) -> Tuple[str, Optional[float]]:
        tl = token.lower()
        if tl in _NONE_TOKENS:
            return ("NONE", None)

        pal_val = _lookup_palette(token, palette)
        if pal_val is not None and tl not in seen:
            return cls._resolve_color_alpha_impl(
                pal_val,
                base_bg_hex=base_bg_hex,
                palette=palette,
                default=default,
                seen=seen | {tl},
            )

        if tl in TAILWIND_PALETTE:
            return (clean_hex6(TAILWIND_PALETTE[tl]), None)

        try:
            return (clean_hex6(token), None)
        except ValueError:
            pass

        if default is not None and default.lower() not in seen:
            return cls._resolve_color_alpha_impl(
                default,
                base_bg_hex=base_bg_hex,
                palette=palette,
                default=None,
                seen=seen | {tl},
            )
        raise ValueError(f"Unrecognized color token or hex value: {token!r}")

    @classmethod
    def _normalize_bg_hex(cls, base_bg_hex: Optional[str], palette: Optional[Dict[str, str]]) -> str:
        if base_bg_hex is None:
            return "0F172A"
        s = str(base_bg_hex).strip()
        if s.lower() in _NONE_TOKENS:
            return "NONE"
        try:
            return clean_hex6(s)
        except ValueError:
            hx, _ = cls._resolve_color_alpha_impl(s, base_bg_hex="0F172A", palette=palette, default="0F172A", seen=frozenset())
            return hx

    @classmethod
    def _resolve_color_alpha_impl(
        cls,
        expr: Optional[str],
        base_bg_hex: str,
        palette: Optional[Dict[str, str]],
        default: Optional[str],
        seen: FrozenSet[str],
    ) -> Tuple[str, Optional[float]]:
        if expr is None:
            return ("NONE", None)
        raw = str(expr).strip()
        if raw.lower() in _NONE_TOKENS:
            return ("NONE", None)

        base_token, slash_alpha, at_alpha = _split_color_modifiers(raw)
        if base_token.lower() in _NONE_TOKENS:
            return ("NONE", None)

        resolved_hex, inherited_alpha = cls._resolve_base_hex(base_token, base_bg_hex, palette, default, seen)
        if resolved_hex == "NONE":
            return ("NONE", None)

        # Combine inherited OpenXML alpha (if palette value carried @alpha) with explicit @alpha
        eff_at = at_alpha
        if inherited_alpha is not None:
            eff_at = inherited_alpha if eff_at is None else round(inherited_alpha * eff_at, 6)

        if slash_alpha is not None and eff_at is not None:
            # Defensive combination when both /NN and @0.NN appear
            return (resolved_hex, round(slash_alpha * eff_at, 6))

        if slash_alpha is not None:
            bg_clean = cls._normalize_bg_hex(base_bg_hex, palette)
            if bg_clean == "NONE":
                return (resolved_hex, slash_alpha)
            return (blend_alpha(resolved_hex, bg_clean, slash_alpha), None)

        return (resolved_hex, eff_at)

    @classmethod
    def resolve_color_alpha(
        cls,
        expr: Optional[str],
        base_bg_hex: str = "0F172A",
        palette: Optional[Dict[str, str]] = None,
        default: Optional[str] = None,
    ) -> Tuple[str, Optional[float]]:
        """
        Resolve semantic token, Tailwind color, or `#HEX` with `/NN` (pre-blended) or `@0.NN` (OpenXML alpha).

        Returns `(hex6_uppercase_no_hash, openxml_alpha)` or `("NONE", None)`.
        When both `/NN` and `@0.NN` appear (e.g. `"sky-500/20@0.5"`), multiplies both alphas defensively.
        """
        return cls._resolve_color_alpha_impl(
            expr,
            base_bg_hex=base_bg_hex,
            palette=palette,
            default=default,
            seen=frozenset(),
        )

    @classmethod
    def _resolve_family_for_contrast(
        cls,
        base_token: str,
        palette: Optional[Dict[str, str]],
    ) -> Tuple[Optional[str], Optional[int]]:
        fam, shade = cls.parse_color_family(base_token)
        if fam is not None:
            return (fam, shade)

        # Primary ink semantic tokens should snap cleanly to crisp light/dark fallbacks,
        # not step through mid-gray slate shades on inverted surfaces.
        if base_token.lower() in _PRIMARY_INK_ALIASES:
            return (None, None)

        pal_val = _lookup_palette(base_token, palette)
        if pal_val is not None:
            pal_base, _, _ = _split_color_modifiers(pal_val)
            fam, shade = cls.parse_color_family(pal_base)
            if fam is not None:
                return (fam, shade)
            try:
                pal_hex = clean_hex6(pal_base)
                if pal_hex in _HEX_TO_TAILWIND:
                    return _HEX_TO_TAILWIND[pal_hex]
            except ValueError:
                pass
        return (None, None)

    @classmethod
    def ensure_contrast(
        cls,
        fg_expr: str,
        bg_hex: str,
        palette: Optional[Dict[str, str]] = None,
        min_ratio: float = 4.5,
    ) -> str:
        """
        Ensure `fg_expr` meets `min_ratio` WCAG contrast against `bg_hex`.

        Returns 6-char uppercase hex without `#`. If `fg_expr` fails contrast and maps
        to a Tailwind color family, selects the closest readable shade along `SHADE_STEPS`;
        otherwise falls back to `"F8FAFC"` (dark bg) or `"0F172A"` (light bg).
        """
        bg_clean = cls._normalize_bg_hex(bg_hex, palette)
        fg_hex, alpha = cls.resolve_color_alpha(
            fg_expr,
            base_bg_hex=bg_clean,
            palette=palette,
            default="ink" if palette and "ink" in palette else "F8FAFC",
        )
        if fg_hex == "NONE" or bg_clean == "NONE":
            return fg_hex

        effective_fg = blend_alpha(fg_hex, bg_clean, alpha) if alpha is not None else fg_hex
        if _raw_contrast_ratio(effective_fg, bg_clean) >= min_ratio:
            return fg_hex

        is_dark_bg = relative_luminance(bg_clean) < 0.25
        base_token, _, _ = _split_color_modifiers(str(fg_expr))
        family, orig_shade = cls._resolve_family_for_contrast(base_token, palette)

        if family is not None:
            ordered_steps = SHADE_STEPS if is_dark_bg else list(reversed(SHADE_STEPS))
            readable = [
                step
                for step in ordered_steps
                if _raw_contrast_ratio(TAILWIND_PALETTE[f"{family}-{step}"], bg_clean) >= min_ratio
            ]
            if readable:
                chosen_step = (
                    min(readable, key=lambda s: abs(s - orig_shade))
                    if orig_shade is not None
                    else readable[0]
                )
                return clean_hex6(TAILWIND_PALETTE[f"{family}-{chosen_step}"])

        return "F8FAFC" if is_dark_bg else "0F172A"

    @classmethod
    def resolve_spacing(cls, token: Any, default: float = 20.0) -> float:
        """Resolve numeric px or Tailwind spacing token (`gap-5`, `p-6`, `px-4`, `py-3`, `m-2`) to 1280x720 px."""
        if token is None:
            return float(default)
        if isinstance(token, (int, float)) and not isinstance(token, bool):
            return float(token)
        s = str(token).strip().lower()
        m = _SPACING_RE.match(s)
        if m:
            return round(float(m.group(1)) * 4.0, 2)
        return float(default)

    @classmethod
    def resolve_radius(cls, token: Any, default: float = 12.0) -> float:
        """Resolve numeric px or `RADIUS_PX` token (e.g. `rounded-xl`) to 1280x720 corner radius px."""
        if token is None:
            return float(default)
        if isinstance(token, (int, float)) and not isinstance(token, bool):
            return float(token)
        s = str(token).strip().lower()
        if s in RADIUS_PX:
            return RADIUS_PX[s]
        if f"rounded-{s}" in RADIUS_PX:
            return RADIUS_PX[f"rounded-{s}"]
        try:
            return float(s)
        except ValueError:
            return float(default)

    @classmethod
    def resolve_typography(cls, token: Any, default_lh: float = 1.38) -> Tuple[float, float]:
        """Resolve numeric pt or `TYPOGRAPHY_SCALE` token (e.g. `text-lg`) to `(pt_size, line_height)`."""
        if token is None:
            return (15.0, float(default_lh))
        if isinstance(token, (int, float)) and not isinstance(token, bool):
            return (float(token), float(default_lh))
        s = str(token).strip().lower()
        if s in TYPOGRAPHY_SCALE:
            return TYPOGRAPHY_SCALE[s]
        if f"text-{s}" in TYPOGRAPHY_SCALE:
            return TYPOGRAPHY_SCALE[f"text-{s}"]
        try:
            return (float(s), float(default_lh))
        except ValueError:
            return (15.0, float(default_lh))


@dataclass
class SlideTheme:
    """Declarative Tailwind theme specification compiled into a WCAG-verified SlideCanvas palette dict."""

    name: str = "Custom"
    canvas: str = "slate-950"
    surface_1: str = "slate-900"
    surface_2: str = "slate-800"
    border: str = "slate-800"
    text_primary: str = "slate-50"
    text_muted: str = "slate-400"
    accent: str = "sky-400"
    accent2: str = "emerald-400"
    radius: str = "rounded-xl"
    border_pt: float = 0.75
    font_heading: str = "PingFang TC"
    font_body: str = "PingFang TC"
    font_mono: str = "Menlo"

    def to_palette_dict(self) -> Dict[str, str]:
        """Resolve all surface, border, and WCAG-guarded foreground colors plus all semantic aliases."""
        canvas_hex, _ = TokenResolver.resolve_color_alpha(self.canvas, base_bg_hex="0F172A")
        if canvas_hex == "NONE":
            canvas_hex = "020617"

        surface_1_hex, _ = TokenResolver.resolve_color_alpha(self.surface_1, base_bg_hex=canvas_hex)
        surface_2_hex, _ = TokenResolver.resolve_color_alpha(
            self.surface_2,
            base_bg_hex=surface_1_hex if surface_1_hex != "NONE" else canvas_hex,
        )
        border_hex, _ = TokenResolver.resolve_color_alpha(self.border, base_bg_hex=canvas_hex)

        text_primary_hex = TokenResolver.ensure_contrast(self.text_primary, canvas_hex, min_ratio=7.0)
        text_muted_hex = TokenResolver.ensure_contrast(self.text_muted, canvas_hex, min_ratio=4.5)
        accent_hex = TokenResolver.ensure_contrast(self.accent, canvas_hex, min_ratio=3.5)
        accent2_hex = TokenResolver.ensure_contrast(self.accent2, canvas_hex, min_ratio=3.5)

        return {
            "bg": canvas_hex,
            "bg_canvas": canvas_hex,
            "canvas": canvas_hex,
            "surface": surface_1_hex,
            "bg_surface": surface_1_hex,
            "surface_1": surface_1_hex,
            "surface2": surface_2_hex,
            "surface_2": surface_2_hex,
            "ink": text_primary_hex,
            "ink_primary": text_primary_hex,
            "text_primary": text_primary_hex,
            "muted": text_muted_hex,
            "ink_muted": text_muted_hex,
            "text_muted": text_muted_hex,
            "border": border_hex,
            "border_grid": border_hex,
            "accent": accent_hex,
            "accent_primary": accent_hex,
            "accent2": accent2_hex,
            "accent_secondary": accent2_hex,
            "radius": str(self.radius),
            "border_pt": str(self.border_pt),
            "font_heading": self.font_heading,
            "font_body": self.font_body,
            "font_mono": self.font_mono,
        }


__all__ = [
    "SHADE_STEPS",
    "TAILWIND_PALETTE",
    "TYPOGRAPHY_SCALE",
    "RADIUS_PX",
    "CARD_VARIANTS",
    "clean_hex6",
    "hex_to_rgb",
    "rgb_to_hex",
    "relative_luminance",
    "contrast_ratio",
    "blend_alpha",
    "TokenResolver",
    "SlideTheme",
]
