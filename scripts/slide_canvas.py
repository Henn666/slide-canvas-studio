#!/usr/bin/env python3
"""
slide_canvas.py
1280x720 SVG-Flavored Python Canvas Engine -> 100% Native OpenXML (.pptx).
Slim orchestrator combining Tailwind semantic tokens + draw-time WCAG contrast guard
(`tokens.py`) with vector/connector primitives (`vector_primitives.py`).
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.util import Pt

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from text_measure import wrap_and_measure_text
from tokens import (
    CARD_VARIANTS,
    TAILWIND_PALETTE,
    SlideTheme,
    TokenResolver,
    blend_alpha,
    clean_hex6,
    contrast_ratio,
    hex_to_rgb,
    relative_luminance,
)
from vector_primitives import (
    CM_TO_PX,
    H_PX,
    PX_TO_CM,
    PX_TO_EMU,
    W_PX,
    VectorPrimitivesMixin,
    _dash_to_prst,
    _parse_svg_path,
    _split_boxes,
    lerp,
    polar,
    px,
)

__all__ = [
    "SlideCanvas",
    "SlideTheme",
    "TokenResolver",
    "TAILWIND_PALETTE",
    "CARD_VARIANTS",
    "contrast_ratio",
    "relative_luminance",
    "W_PX",
    "H_PX",
    "PX_TO_EMU",
    "PX_TO_CM",
    "CM_TO_PX",
    "px",
    "polar",
    "lerp",
    "run_cli",
]

_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_META_PALETTE_KEYS = frozenset(("font_heading", "font_body", "font_mono", "radius", "border_pt"))

_DEFAULT_PALETTE: Dict[str, str] = {
    "bg_canvas": "F5F5F7",
    "bg_surface": "FFFFFF",
    "ink_primary": "1D1D1F",
    "ink_muted": "6E6E73",
    "border_grid": "D1D1D6",
    "accent_primary": "0071E3",
    "accent_secondary": "3A7D74",
}

_PALETTE_ALIAS_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("bg_canvas", "bg"),
    ("bg_surface", "surface"),
    ("surface_2", "surface2"),
    ("ink_primary", "ink"),
    ("ink_muted", "muted"),
    ("border_grid", "border"),
    ("accent_primary", "accent"),
    ("accent_secondary", "accent2"),
)


def _oxml_rgb(hex6: str) -> RGBColor:
    """Convert a 6-char hex string to a python-pptx RGBColor."""
    r, g, b = hex_to_rgb(hex6)
    return RGBColor(r, g, b)


# ---------------------------------------------------------------------------
# SlideCanvas Orchestrator
# ---------------------------------------------------------------------------
class SlideCanvas(VectorPrimitivesMixin):
    """1280x720 SVG-flavored OpenXML presentation builder with Tailwind tokens & WCAG guard."""

    def __init__(
        self,
        pptx_path: Optional[str] = None,
        palette: Optional[Union[Dict[str, str], SlideTheme]] = None,
        typography: Optional[Dict[str, str]] = None,
        template_path: Optional[str] = None,
        check_contrast: bool = True,
        theme: Optional[SlideTheme] = None,
    ):
        if isinstance(palette, SlideTheme):
            if theme is None:
                theme = palette
            palette = None

        self.pptx_path = pptx_path
        if pptx_path and os.path.exists(pptx_path) and not template_path:
            self.prs = Presentation(pptx_path)
        elif template_path and os.path.exists(template_path):
            self.prs = Presentation(template_path)
        else:
            self.prs = Presentation()
            self.prs.slide_width = px(W_PX)
            self.prs.slide_height = px(H_PX)

        self._blank_layout = self._pick_blank_layout()
        self.slide = None
        self.slide_idx = 0
        self._id_counter = 0
        self._nodes: Dict[str, Dict[str, float]] = {}
        self._port_counts: Dict[Tuple[str, str], int] = {}

        self.theme: Optional[SlideTheme] = theme
        self.default_rx: Union[str, float] = theme.radius if theme is not None else "rounded-xl"
        self.default_border_pt: float = float(theme.border_pt) if theme is not None else 0.75

        pal_dict = theme.to_palette_dict() if theme is not None else dict(palette or {})
        if theme is not None and palette:
            pal_dict = {**pal_dict, **palette}

        self.palette: Dict[str, str] = {}
        self._current_bg_hex: str = "F5F5F7"
        self._bg_stack: List[Tuple[float, float, float, float, str]] = []
        self.set_palette(pal_dict, check_contrast=check_contrast)

        base_typo = {
            "font_heading": theme.font_heading if theme is not None else "PingFang TC",
            "font_body": theme.font_body if theme is not None else "PingFang TC",
            "font_mono": theme.font_mono if theme is not None else "Menlo",
        }
        for fk in ("font_heading", "font_body", "font_mono"):
            if fk in self.palette and self.palette[fk]:
                base_typo[fk] = self.palette[fk]
        self.typography: Dict[str, str] = {**base_typo, **(typography or {})}

    def _pick_blank_layout(self):
        for lay in self.prs.slide_layouts:
            if "blank" in lay.name.lower() or len(lay.placeholders) == 0:
                return lay
        return self.prs.slide_layouts[min(6, len(self.prs.slide_layouts) - 1)]

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def set_palette(self, pal: Union[Dict[str, str], SlideTheme], check_contrast: bool = True):
        """Normalize a palette dict or SlideTheme, sync role aliases, and verify canvas contrast."""
        if isinstance(pal, SlideTheme):
            self.theme = pal
            self.default_rx = pal.radius
            self.default_border_pt = float(pal.border_pt)
            pal = pal.to_palette_dict()

        clean: Dict[str, str] = {}
        for k, v in pal.items():
            sval = str(v).strip()
            if k in _META_PALETTE_KEYS:
                clean[k] = sval
            else:
                try:
                    hx = clean_hex6(sval)
                    clean[k] = "none" if hx == "NONE" else hx
                except ValueError:
                    clean[k] = sval

        def _sync_aliases(target: Dict[str, str]) -> None:
            for full_k, short_k in _PALETTE_ALIAS_PAIRS:
                if full_k in target and short_k not in target:
                    target[short_k] = target[full_k]
                elif short_k in target and full_k not in target:
                    target[full_k] = target[short_k]

        _sync_aliases(clean)
        for def_k, def_v in _DEFAULT_PALETTE.items():
            clean.setdefault(def_k, def_v)
        _sync_aliases(clean)

        if "surface_2" not in clean and "surface2" not in clean:
            try:
                surf_hx, _ = TokenResolver.resolve_color_alpha(clean["bg_surface"], base_bg_hex="F5F5F7", palette=clean)
                ink_hx, _ = TokenResolver.resolve_color_alpha(clean["ink_primary"], base_bg_hex=surf_hx, palette=clean)
                s2 = blend_alpha(ink_hx, surf_hx, 0.06) if surf_hx != "NONE" and ink_hx != "NONE" else "E5E5EA"
            except ValueError:
                s2 = "E5E5EA"
            clean["surface_2"] = s2
            clean["surface2"] = s2

        clean.setdefault("white", "FFFFFF")
        clean.setdefault("black", "000000")
        self.palette = clean

        if hasattr(self, "typography"):
            for fk in ("font_heading", "font_body", "font_mono"):
                if fk in clean and clean[fk]:
                    self.typography[fk] = clean[fk]

        bg_hx, _ = TokenResolver.resolve_color_alpha(
            "bg_canvas", base_bg_hex="F5F5F7", palette=clean, default="F5F5F7"
        )
        self._current_bg_hex = bg_hx if bg_hx != "NONE" else "F5F5F7"

        if check_contrast and "bg_canvas" in clean and "ink_primary" in clean:
            ink_hx, _ = TokenResolver.resolve_color_alpha(
                "ink_primary", base_bg_hex=self._current_bg_hex, palette=clean, default="1D1D1F"
            )
            if self._current_bg_hex != "NONE" and ink_hx != "NONE":
                cr = contrast_ratio(self._current_bg_hex, ink_hx)
                if cr < 4.5:
                    raise ValueError(
                        f"WCAG Contrast Violation: bg_canvas (#{self._current_bg_hex}) vs "
                        f"ink_primary (#{ink_hx}) is {cr}:1 (< 4.5:1 minimum)."
                    )

    # -----------------------------------------------------------------------
    # Background Stack & Token Parsers
    # -----------------------------------------------------------------------
    def _effective_bg_at(self, x: float, y: float, w: float, h: float) -> str:
        """Return topmost opaque solid background hex enclosing center `(x+w/2, y+h/2)`."""
        cx = float(x) + float(w) / 2.0
        cy = float(y) + float(h) / 2.0
        for bx, by, bw, bh, bg_hx in reversed(self._bg_stack):
            if bx <= cx <= bx + bw and by <= cy <= by + bh:
                return bg_hx
        return self._current_bg_hex

    def resolve_hex(
        self,
        token: Optional[str],
        default: str = "ink",
        base_bg_hex: Optional[str] = None,
    ) -> str:
        """Resolve a semantic, Tailwind, or hex color token to 6-char uppercase hex (or `'none'`)."""
        if token is None:
            return "none"
        bg = base_bg_hex or self._current_bg_hex
        try:
            hx, _ = TokenResolver.resolve_color_alpha(
                str(token), base_bg_hex=bg, palette=self.palette, default=default
            )
        except ValueError:
            hx, _ = TokenResolver.resolve_color_alpha(
                default, base_bg_hex=bg, palette=self.palette, default="1D1D1F"
            )
        return "none" if hx == "NONE" else hx

    def parse_color_alpha(
        self,
        expr: Optional[str],
        default: str = "ink",
        base_bg_hex: Optional[str] = None,
    ) -> Tuple[str, Optional[float]]:
        """Resolve `<token>[/pct][@alpha]` -> `(hex6, openxml_alpha)` or `('none', None)`."""
        if expr is None:
            return "none", None
        bg = base_bg_hex or self._current_bg_hex
        try:
            hx, op = TokenResolver.resolve_color_alpha(
                expr, base_bg_hex=bg, palette=self.palette, default=default
            )
        except ValueError:
            hx, op = TokenResolver.resolve_color_alpha(
                default, base_bg_hex=bg, palette=self.palette, default="1D1D1F"
            )
        if hx == "NONE":
            return "none", None
        return hx, op

    def parse_fill(self, fill: Any, base_bg_hex: Optional[str] = None) -> Dict[str, Any]:
        """Parse solid, transparent, or `grad(...)` fill into normalized OpenXML metadata."""
        if fill is None:
            return {"kind": "none"}
        s = str(fill).strip()
        if s.lower() in ("", "none", "transparent", "clear"):
            return {"kind": "none"}
        bg = base_bg_hex or self._current_bg_hex
        if s.lower().startswith("grad(") and s.endswith(")"):
            inner = s[5:-1]
            parts = [p.strip() for p in inner.split(",") if p.strip()]
            ang = 135.0
            if parts and _NUM_RE.fullmatch(parts[0]):
                ang = float(parts[0])
                stop_exprs = parts[1:]
            else:
                stop_exprs = parts
            if not stop_exprs:
                stop_exprs = ["accent@0.2", "accent2@0.05"]
            stops = []
            for idx, se in enumerate(stop_exprs):
                pos = int(round((idx / max(1, len(stop_exprs) - 1)) * 100000))
                hx, op = self.parse_color_alpha(se, "accent", base_bg_hex=bg)
                if hx == "none":
                    hx = self.resolve_hex("accent", base_bg_hex=bg)
                stops.append((pos, hx, op))
            return {"kind": "grad", "angle": ang, "stops": stops}
        hx, op = self.parse_color_alpha(s, "surface", base_bg_hex=bg)
        return {"kind": "none"} if hx == "none" else {"kind": "solid", "hex": hx, "opacity": op}

    def parse_stroke(self, stroke: Any, base_bg_hex: Optional[str] = None) -> Dict[str, Any]:
        """Parse `color[/pct][@op]:width_pt:dash` stroke shorthand."""
        if stroke is None:
            return {"kind": "none"}
        s = str(stroke).strip()
        if s.lower() in ("", "none", "transparent", "clear"):
            return {"kind": "none"}
        bg = base_bg_hex or self._current_bg_hex
        parts = s.split(":")
        hx, op = self.parse_color_alpha(parts[0], "border", base_bg_hex=bg)
        if hx == "none":
            return {"kind": "none"}
        width_pt = 1.25
        dash = "solid"
        for p in parts[1:]:
            pt = p.strip()
            if not pt:
                continue
            if _NUM_RE.fullmatch(pt):
                width_pt = float(pt)
            else:
                dash = _dash_to_prst(pt)
        return {"kind": "solid", "hex": hx, "opacity": op, "width_pt": width_pt, "dash": dash}

    def _insert_oxml_fill(self, container_el, fill_info: Dict[str, Any]):
        ns = nsdecls("a")
        for tag in ("noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill"):
            for old in container_el.findall(f"{_A_NS}{tag}"):
                container_el.remove(old)
        if fill_info["kind"] == "none":
            el = parse_xml(f"<a:noFill {ns}/>")
        elif fill_info["kind"] == "solid":
            if fill_info.get("opacity") is not None:
                av = int(round(fill_info["opacity"] * 100000))
                el = parse_xml(
                    f'<a:solidFill {ns}><a:srgbClr val="{fill_info["hex"]}">'
                    f'<a:alpha val="{av}"/></a:srgbClr></a:solidFill>'
                )
            else:
                el = parse_xml(f'<a:solidFill {ns}><a:srgbClr val="{fill_info["hex"]}"/></a:solidFill>')
        else:
            ang = int(round((fill_info["angle"] % 360.0) * 60000.0))
            gs_parts = []
            for pos, hx, op in fill_info["stops"]:
                if op is not None:
                    av = int(round(op * 100000))
                    gs_parts.append(f'<a:gs pos="{pos}"><a:srgbClr val="{hx}"><a:alpha val="{av}"/></a:srgbClr></a:gs>')
                else:
                    gs_parts.append(f'<a:gs pos="{pos}"><a:srgbClr val="{hx}"/></a:gs>')
            el = parse_xml(
                f'<a:gradFill {ns} flip="none" rotWithShape="1">'
                f'<a:gsLst>{"".join(gs_parts)}</a:gsLst><a:lin ang="{ang}" scaled="1"/></a:gradFill>'
            )
        insert_idx = 0
        for idx, child in enumerate(list(container_el)):
            if child.tag.split("}")[-1] in ("xfrm", "prstGeom", "custGeom"):
                insert_idx = idx + 1
        container_el.insert(insert_idx, el)

    def _apply_style(
        self,
        shp,
        fill: Any = "none",
        stroke: Any = "none",
        base_bg_hex: Optional[str] = None,
    ):
        sp_pr = shp._element.spPr
        self._insert_oxml_fill(sp_pr, self.parse_fill(fill, base_bg_hex=base_bg_hex))

        st = self.parse_stroke(stroke, base_bg_hex=base_bg_hex)
        if st["kind"] == "none":
            shp.line.fill.background()
        else:
            shp.line.color.rgb = _oxml_rgb(st["hex"])
            shp.line.width = Pt(max(0.2, st["width_pt"]))
            ln = sp_pr.find(f"{_A_NS}ln")
            if ln is not None:
                ns = nsdecls("a")
                if st.get("opacity") is not None:
                    srgb = ln.find(f"{_A_NS}solidFill/{_A_NS}srgbClr")
                    if srgb is not None:
                        av = int(round(st["opacity"] * 100000))
                        for old in srgb.findall(f"{_A_NS}alpha"):
                            srgb.remove(old)
                        srgb.append(parse_xml(f'<a:alpha {ns} val="{av}"/>'))
                if st["dash"] != "solid":
                    for old in ln.findall(f"{_A_NS}prstDash"):
                        ln.remove(old)
                    dash_el = parse_xml(f'<a:prstDash {ns} val="{st["dash"]}"/>')
                    insert_idx = len(ln)
                    for idx, child in enumerate(list(ln)):
                        if child.tag.split("}")[-1] in ("round", "miter", "bevel", "headEnd", "tailEnd"):
                            insert_idx = idx
                            break
                    ln.insert(insert_idx, dash_el)

    def _resolve_font(self, font: Optional[str] = None, role: Optional[str] = None) -> str:
        if font:
            if font in ("heading", "title", "subtitle", "kpi"):
                return self.typography["font_heading"]
            if font == "mono":
                return self.typography["font_mono"]
            if font == "body":
                return self.typography["font_body"]
            return font
        if role == "mono":
            return self.typography["font_mono"]
        if role in ("heading", "title", "subtitle", "kpi", "kpi_hero"):
            return self.typography["font_heading"]
        return self.typography["font_body"]

    def _set_text(
        self,
        shp,
        txt: str,
        size: Union[float, str] = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_x_px: float = 8.0,
        pad_v_px: float = 6.0,
        bg_hex: Optional[str] = None,
    ):
        pt_size, _ = TokenResolver.resolve_typography(size)
        tf = shp.text_frame
        tf.word_wrap = True
        tf.margin_left = px(pad_x_px)
        tf.margin_right = px(pad_x_px)
        tf.margin_top = px(pad_v_px)
        tf.margin_bottom = px(pad_v_px)
        valign_map = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "center": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}
        tf.vertical_anchor = valign_map.get(valign.lower(), MSO_ANCHOR.TOP)

        align_map = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT, "justify": PP_ALIGN.JUSTIFY}
        p_align = align_map.get(align.lower(), PP_ALIGN.LEFT)
        fname = self._resolve_font(font, role)

        actual_bg = bg_hex or self._current_bg_hex
        if actual_bg and str(actual_bg).lower() != "none":
            min_cr = 3.0 if pt_size >= 24.0 else 4.5
            hx = TokenResolver.ensure_contrast(color, actual_bg, palette=self.palette, min_ratio=min_cr)
        else:
            hx, _ = self.parse_color_alpha(color, "ink")
        if hx in ("none", "NONE", ""):
            hx = "1D1D1F"
        rgb = _oxml_rgb(hx)

        lines = str(txt).split("\n")
        for idx, line_str in enumerate(lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.alignment = p_align
            p.space_before = Pt(0)
            p.space_after = Pt(0)
            run = p.add_run()
            run.text = line_str
            run.font.name = fname
            run.font.size = Pt(float(pt_size))
            run.font.bold = bool(bold)
            run.font.color.rgb = rgb
            rPr = run._r.get_or_add_rPr()
            if rPr.find(f"{_A_NS}ea") is None:
                rPr.append(parse_xml(f'<a:ea {nsdecls("a")} typeface="{fname}"/>'))

    # -----------------------------------------------------------------------
    # Slide & Chrome Management
    # -----------------------------------------------------------------------
    def new_slide(self, bg: Optional[str] = None):
        self.slide = self.prs.slides.add_slide(self._blank_layout)
        self.slide_idx = len(self.prs.slides)
        self._nodes = {}
        self._port_counts = {}
        self._bg_stack = []
        self.set_background(bg or "bg_canvas")
        return self.slide

    def select_slide(self, slide_num: int, bg: Optional[str] = None, clear: bool = True):
        while len(self.prs.slides) < slide_num:
            self.prs.slides.add_slide(self._blank_layout)
        self.slide = self.prs.slides[slide_num - 1]
        self.slide_idx = slide_num
        self._nodes = {}
        self._port_counts = {}
        self._bg_stack = []
        if clear:
            sp_tree = self.slide.shapes._spTree
            for child in list(sp_tree):
                local = child.tag.split("}")[-1]
                if local not in ("nvGrpSpPr", "grpSpPr"):
                    sp_tree.remove(child)
        self.set_background(bg or "bg_canvas")
        return self.slide

    def set_background(self, bg: str):
        fill_info = self.parse_fill(bg)
        if fill_info["kind"] == "solid" and fill_info["hex"] != "none":
            self._current_bg_hex = fill_info["hex"]
        elif fill_info["kind"] == "grad" and fill_info.get("stops"):
            self._current_bg_hex = fill_info["stops"][0][1]

        bg_pr = self.slide.background._element.find(f"{_P_NS}bg/{_P_NS}bgPr")
        if bg_pr is None:
            self.slide.background.fill.solid()
            bg_pr = self.slide.background._element.find(f"{_P_NS}bg/{_P_NS}bgPr")
        if bg_pr is not None:
            self._insert_oxml_fill(bg_pr, fill_info)

    def header(self, title: str, subtitle: str = "", eyebrow: str = "", x: float = 68, y: float = 42, w: float = 1144) -> float:
        cur_y = y
        if eyebrow:
            self.text(x, cur_y, w, 26, eyebrow, size=11.5, color="accent2", bold=True, role="mono", pad_px=2, name="eyebrow")
            cur_y += 28
        if title:
            cur_y = self.text_auto(x, cur_y, w, title, size=29, color="ink", bold=True, role="heading", line_height=1.32, pad_px=2, name="title") + 4
        if subtitle:
            cur_y = self.text_auto(x, cur_y, w, subtitle, size=15.5, color="muted", bold=False, role="body", line_height=1.32, pad_px=2, name="subtitle") + 8
        return round(cur_y, 2)

    def footer(self, text: str = "", slide_num: Optional[int] = None, total_slides: Optional[int] = None, line: bool = True):
        s_num = slide_num or self.slide_idx
        if total_slides:
            code = f"SHT {s_num:02d}/{total_slides:02d}"
            full = f"{code}   |   {text}" if text else code
        else:
            full = text or f"SHT {s_num:02d}"
        if line:
            self.line(68, 656, 1212, 656, stroke="border:0.75", name="footer_line")
        self.text(220, 660, 992, 30, full, size=10.5, color="muted", align="right", role="mono", pad_px=2, name="footer_text")

    # -----------------------------------------------------------------------
    # Grid & Layout Helpers
    # -----------------------------------------------------------------------
    def cols(
        self,
        n: int,
        x: float = 68,
        y: float = 166,
        w: float = 1144,
        h: float = 460,
        gap: Union[float, str] = 24,
        weights: Optional[List[float]] = None,
    ) -> List[Tuple[float, float, float, float]]:
        gap_px = TokenResolver.resolve_spacing(gap, 24.0)
        return [(cx, round(y, 2), cw, round(h, 2)) for cx, cw in _split_boxes(w, x, n, gap_px, weights)]

    def rows(
        self,
        n: int,
        x: float = 68,
        y: float = 166,
        w: float = 1144,
        h: float = 460,
        gap: Union[float, str] = 20,
        weights: Optional[List[float]] = None,
    ) -> List[Tuple[float, float, float, float]]:
        gap_px = TokenResolver.resolve_spacing(gap, 20.0)
        return [(round(x, 2), ry, round(w, 2), rh) for ry, rh in _split_boxes(h, y, n, gap_px, weights)]

    def grid(
        self,
        cols_n: int,
        rows_n: int,
        x: float = 68,
        y: float = 166,
        w: float = 1144,
        h: float = 460,
        gap_x: Union[float, str] = 24,
        gap_y: Union[float, str] = 20,
    ) -> List[Tuple[float, float, float, float]]:
        gx = TokenResolver.resolve_spacing(gap_x, 24.0)
        gy = TokenResolver.resolve_spacing(gap_y, 20.0)
        col_spans = _split_boxes(w, x, cols_n, gx)
        row_spans = _split_boxes(h, y, rows_n, gy)
        return [(cx, ry, cw, rh) for ry, rh in row_spans for cx, cw in col_spans]

    # -----------------------------------------------------------------------
    # Shape, Card & Typography Primitives (1280x720)
    # -----------------------------------------------------------------------
    def _finalize_shape_fill_and_text(
        self,
        shp,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Any,
        stroke: Any,
        text: str,
        size: Union[float, str],
        color: str,
        bold: bool,
        align: str,
        valign: str,
        font: Optional[str],
        role: Optional[str],
        pad_x_px: float,
        pad_v_px: float,
        node_id: Optional[str],
    ):
        enclosing_bg = self._effective_bg_at(x, y, w, h)
        fill_info = self.parse_fill(fill, base_bg_hex=enclosing_bg)
        self._apply_style(shp, fill=fill, stroke=stroke, base_bg_hex=enclosing_bg)

        is_opaque = fill_info["kind"] == "solid" and (
            fill_info.get("opacity") is None or fill_info["opacity"] >= 0.5
        )
        if str(text) != "":
            text_bg = fill_info["hex"] if is_opaque else enclosing_bg
            self._set_text(
                shp,
                text,
                size=size,
                color=color,
                bold=bold,
                align=align,
                valign=valign,
                font=font,
                role=role,
                pad_x_px=pad_x_px,
                pad_v_px=pad_v_px,
                bg_hex=text_bg,
            )

        if is_opaque and not shp.name.startswith("bg_glow_"):
            self._bg_stack.append((float(x), float(y), max(1.0, float(w)), max(1.0, float(h)), fill_info["hex"]))
        self._register_node(node_id, x, y, w, h)
        return shp

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: Union[float, str] = 0,
        fill: Any = "surface",
        stroke: Any = "none",
        text: str = "",
        size: Union[float, str] = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "center",
        valign: str = "middle",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_px: float = 10.0,
        pad_v_px: Optional[float] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        rx_px = TokenResolver.resolve_radius(rx, 0.0)
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if rx_px > 0 else MSO_SHAPE.RECTANGLE
        shp = self.slide.shapes.add_shape(kind, px(x), px(y), px(max(1.0, w)), px(max(1.0, h)))
        idx = self._next_id()
        shp.name = name or (f"box_{idx}" if str(text).strip() else f"card_bg_{idx}")
        if rx_px > 0 and min(w, h) > 0:
            shp.adjustments[0] = min(0.49, float(rx_px) / min(w, h))
        v_pad = pad_px if pad_v_px is None else pad_v_px
        return self._finalize_shape_fill_and_text(
            shp, x, y, w, h, fill, stroke, text, size, color, bold, align, valign, font, role, pad_px, v_pad, id
        )

    def pill(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Any = "accent@0.12",
        stroke: Any = "accent@0.38:1",
        text: str = "",
        size: Union[float, str] = 11.5,
        color: str = "accent",
        bold: bool = True,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        return self.rect(
            x, y, w, h, rx=h / 2.0, fill=fill, stroke=stroke, text=text, size=size,
            color=color, bold=bold, align="center", valign="middle", font=font, role=role,
            pad_px=6, pad_v_px=0, name=name or f"pill_{self._next_id()}", id=id,
        )

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: Any = "accent",
        stroke: Any = "none",
        text: str = "",
        size: Union[float, str] = 13.0,
        color: str = "ink",
        bold: bool = False,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        return self.ellipse(cx, cy, r, r, fill=fill, stroke=stroke, text=text, size=size, color=color, bold=bold, font=font, role=role, name=name, id=id)

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx_px: float,
        ry_px: float,
        fill: Any = "accent",
        stroke: Any = "none",
        text: str = "",
        size: Union[float, str] = 13.0,
        color: str = "ink",
        bold: bool = False,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        bx, by = cx - rx_px, cy - ry_px
        bw, bh = max(1.0, 2.0 * rx_px), max(1.0, 2.0 * ry_px)
        shp = self.slide.shapes.add_shape(MSO_SHAPE.OVAL, px(bx), px(by), px(bw), px(bh))
        idx = self._next_id()
        shp.name = name or (f"circle_{idx}" if str(text).strip() else f"dot_{idx}")
        return self._finalize_shape_fill_and_text(
            shp, bx, by, bw, bh, fill, stroke, text, size, color, bold, "center", "middle", font, role, 4.0, 4.0, id
        )

    def glow(self, cx: float, cy: float, r: float, color: str = "accent@0.09", rings: int = 2):
        """Ambient concentric soft glow circles (ignored in overlap detection)."""
        base_c, base_op = self.parse_color_alpha(color, "accent")
        if base_c == "none":
            return
        base_op = base_op if base_op is not None else 0.10
        for i in range(rings):
            scale = 1.0 - (i * 0.35)
            op = round(min(0.4, base_op * (1.0 + i * 0.4)), 3)
            self.circle(cx, cy, r * scale, fill=f"#{base_c}@{op}", stroke="none", name=f"bg_glow_{self._next_id()}")

    def card(
        self,
        box: Tuple[float, float, float, float],
        variant: str = "default",
        rx: Union[float, str, None] = None,
        padding: Union[float, str] = "p-5",
        fill: Any = None,
        stroke: Any = None,
        kicker: str = "",
        kicker_color: str = "accent",
        title: str = "",
        title_size: Union[float, str] = "text-lg",
        title_color: str = "ink",
        body: str = "",
        body_size: Union[float, str] = "text-sm",
        body_color: str = "muted",
        id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[float, float, float, float]:
        """
        Draw a themed container card and return remaining `(x, y, w, h)` inner box.

        Supports variants `'default'`, `'accent'`, `'subtle'`, `'dashed'` blended against
        the local background, optional `kicker`/`title`/`body`, and returns the inset content rect.
        """
        bx, by, bw, bh = box
        cfg = CARD_VARIANTS.get(variant, CARD_VARIANTS["default"])
        local_bg = self._effective_bg_at(bx, by, bw, bh)
        use_rx = self.default_rx if rx is None else rx

        if fill is not None:
            use_fill = fill
        else:
            f_hx, f_op = self.parse_color_alpha(cfg["fill"], default="surface", base_bg_hex=local_bg)
            if f_hx == "none":
                use_fill = "none"
            elif f_op is not None:
                use_fill = f"#{f_hx}@{f_op}"
            else:
                use_fill = f"#{f_hx}"

        if stroke is not None:
            use_stroke = stroke
        else:
            s_hx, s_op = self.parse_color_alpha(cfg["stroke"], default="border", base_bg_hex=local_bg)
            if s_hx == "none":
                use_stroke = "none"
            else:
                b_pt = self.default_border_pt if variant == "default" else cfg.get("border_pt", self.default_border_pt)
                dash = cfg.get("dash", "solid")
                c_part = f"#{s_hx}@{s_op}" if s_op is not None else f"#{s_hx}"
                use_stroke = f"{c_part}:{b_pt}:{dash}" if dash != "solid" else f"{c_part}:{b_pt}"

        self.rect(bx, by, bw, bh, rx=use_rx, fill=use_fill, stroke=use_stroke, id=id, name=name)

        pad = TokenResolver.resolve_spacing(padding, 20.0)
        ix = bx + pad
        iw = max(20.0, bw - 2.0 * pad)
        cur_y = by + pad

        if kicker and str(kicker).strip():
            cur_y = self.text_auto(ix, cur_y, iw, kicker, size="text-xs", color=kicker_color, bold=True, role="mono") + 6.0
        if title and str(title).strip():
            cur_y = self.text_auto(ix, cur_y, iw, title, size=title_size, color=title_color, bold=True, role="heading") + 6.0
        if body and str(body).strip():
            cur_y = self.text_auto(ix, cur_y, iw, body, size=body_size, color=body_color, line_height=1.4, role="body") + 8.0

        return (round(ix, 2), round(cur_y, 2), round(iw, 2), round(max(0.0, by + bh - pad - cur_y), 2))

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        size: Union[float, str] = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_px: float = 3.0,
        name: Optional[str] = None,
        bg_hex: Optional[str] = None,
    ) -> float:
        tb = self.slide.shapes.add_textbox(px(x), px(y), px(max(8.0, w)), px(max(8.0, h)))
        tb.name = name or f"txt_{self._next_id()}"
        eff_bg = bg_hex or self._effective_bg_at(x, y, w, h)
        self._set_text(
            tb, text, size=size, color=color, bold=bold, align=align, valign=valign,
            font=font, role=role, pad_x_px=pad_px, pad_v_px=pad_px, bg_hex=eff_bg,
        )
        return round(y + h, 2)

    def text_auto(
        self,
        x: float,
        y: float,
        w: float,
        text: str,
        size: Union[float, str] = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        font: Optional[str] = None,
        role: Optional[str] = None,
        line_height: Optional[float] = None,
        pad_px: float = 3.0,
        name: Optional[str] = None,
    ) -> float:
        """Measure wrapped CJK/Latin text height and place textbox, returning bottom_y."""
        if not text or not str(text).strip():
            return y
        pt_size, default_lh = TokenResolver.resolve_typography(size, default_lh=1.38)
        eff_lh = float(line_height) if line_height is not None else default_lh
        w_cm = max(1.0, (w - 2 * pad_px) * PX_TO_CM)
        _, est_h_cm, _ = wrap_and_measure_text(
            str(text), box_w_cm=w_cm, font_size_pt=pt_size, bold=bold, line_height=eff_lh, pad_v_cm=0.14
        )
        h_px = max(18.0, est_h_cm * CM_TO_PX + 2 * pad_px)
        self.text(
            x, y, w, h_px, text, size=pt_size, color=color, bold=bold, align=align,
            valign="top", font=font, role=role, pad_px=pad_px, name=name,
        )
        return round(y + h_px, 2)

    def stat(
        self,
        x: float,
        y: float,
        w: float,
        value: str,
        label: str,
        val_size: Union[float, str] = 46.0,
        lbl_size: Union[float, str] = 13.5,
        val_color: str = "accent",
        lbl_color: str = "ink",
        align: str = "left",
    ) -> float:
        val_pt, _ = TokenResolver.resolve_typography(val_size)
        lbl_pt, _ = TokenResolver.resolve_typography(lbl_size)
        y1 = self.text_auto(
            x, y, w, value, size=val_pt, color=val_color, bold=True, align=align,
            role="kpi", line_height=1.18, pad_px=2, name=f"stat_val_{self._next_id()}",
        )
        if label:
            return self.text_auto(
                x, y1 + 4, w, label, size=lbl_pt, color=lbl_color, bold=False, align=align,
                role="body", line_height=1.35, pad_px=2, name=f"stat_lbl_{self._next_id()}",
            )
        return y1

    def table(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        headers: List[str],
        rows: List[List[str]],
        highlight_cells: Optional[List[Dict[str, Any]]] = None,
        col_widths: Optional[List[float]] = None,
    ):
        total_rows = (1 if headers else 0) + len(rows)
        total_cols = len(headers) if headers else (len(rows[0]) if rows else 1)
        gf = self.slide.shapes.add_table(total_rows, total_cols, px(x), px(y), px(w), px(h))
        gf.name = "data_table"
        tbl = gf.table

        if col_widths:
            w_sum = sum(col_widths) or 1.0
            for ci, cw in enumerate(col_widths):
                tbl.columns[ci].width = px(w * (cw / w_sum))

        hl_map = {(int(hc.get("row", -1)), int(hc.get("col", -1))): hc.get("color", "accent") for hc in (highlight_cells or [])}
        border_hex = self.resolve_hex("border_grid")
        if border_hex == "none":
            border_hex = "D1D1D6"

        def style_cell(cell, txt: str, fill_hex: str, txt_hex: str, size_pt: float, is_bold: bool, font_role: str):
            cell.fill.solid()
            cell.fill.fore_color.rgb = _oxml_rgb(fill_hex)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = px(10)
            cell.margin_right = px(10)
            cell.margin_top = px(6)
            cell.margin_bottom = px(6)
            tc_pr = cell._tc.get_or_add_tcPr()
            ns = nsdecls("a")
            for b_tag in ("lnL", "lnR", "lnT", "lnB"):
                for old in tc_pr.findall(f"{_A_NS}{b_tag}"):
                    tc_pr.remove(old)
            tc_pr.append(parse_xml(f'<a:lnL {ns} w="0"><a:noFill/></a:lnL>'))
            tc_pr.append(parse_xml(f'<a:lnR {ns} w="0"><a:noFill/></a:lnR>'))
            tc_pr.append(parse_xml(f'<a:lnT {ns} w="9525"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:lnT>'))
            tc_pr.append(parse_xml(f'<a:lnB {ns} w="9525"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:lnB>'))
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(txt)
            r.font.name = self._resolve_font(role=font_role)
            r.font.size = Pt(size_pt)
            r.font.bold = is_bold
            r.font.color.rgb = _oxml_rgb(txt_hex)

        r_ptr = 0
        if headers:
            hdr_fill = self.resolve_hex("surface")
            if hdr_fill == "none":
                hdr_fill = "FFFFFF"
            hdr_txt = TokenResolver.ensure_contrast("accent2", hdr_fill, palette=self.palette, min_ratio=4.5)
            for ci, htxt in enumerate(headers):
                style_cell(tbl.cell(0, ci), htxt, hdr_fill, hdr_txt, 12.0, True, "mono")
            r_ptr = 1

        row_fill = self.resolve_hex("bg")
        if row_fill == "none":
            row_fill = self._current_bg_hex
        for ri, row_vals in enumerate(rows):
            for ci, val in enumerate(row_vals):
                hl = hl_map.get((ri, ci))
                txt_hex = TokenResolver.ensure_contrast(hl if hl else "ink", row_fill, palette=self.palette, min_ratio=4.5)
                style_cell(tbl.cell(r_ptr + ri, ci), val, row_fill, txt_hex, 13.5, bool(ci == 0 or hl), "body")
        return gf

    def image(self, path: str, x: float, y: float, w: float, h: Optional[float] = None, name: str = "image_asset"):
        if h is not None:
            pic = self.slide.shapes.add_picture(path, px(x), px(y), px(w), px(h))
        else:
            pic = self.slide.shapes.add_picture(path, px(x), px(y), width=px(w))
        pic.name = name
        return pic

    def save(self, out_path: Optional[str] = None) -> str:
        target = out_path or self.pptx_path
        if not target:
            raise ValueError("Specify out_path to save deck.pptx")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        self.prs.save(target)
        return os.path.abspath(target)


def run_cli(
    slide_funcs: List[Callable[[SlideCanvas, int], None]],
    palette: Optional[Union[Dict[str, str], SlideTheme]] = None,
    typography: Optional[Dict[str, str]] = None,
    default_out: str = "build/deck.pptx",
    template_path: Optional[str] = None,
    theme: Optional[SlideTheme] = None,
):
    """CLI entrypoint for building all slides or rebuilding a single slide."""
    if isinstance(palette, SlideTheme):
        if theme is None:
            theme = palette
        palette = None

    parser = argparse.ArgumentParser(description="Build presentation via SlideCanvas 1280x720 API.")
    parser.add_argument("--all", action="store_true", help="Build all slides from scratch")
    parser.add_argument("--slide", "-n", type=int, help="Rebuild single 1-based slide")
    parser.add_argument("--out", "-o", default=default_out, help="Target .pptx path")
    args = parser.parse_args()

    total = len(slide_funcs)
    out_path = os.path.abspath(args.out)

    if args.slide:
        if args.slide < 1 or args.slide > total:
            raise ValueError(f"Slide {args.slide} out of range (1..{total})")
        c = SlideCanvas(
            pptx_path=out_path if os.path.exists(out_path) else None,
            palette=palette,
            typography=typography,
            template_path=template_path,
            theme=theme,
        )
        c.select_slide(args.slide)
        slide_funcs[args.slide - 1](c, total)
        saved = c.save(out_path)
        print(f'{{"status": "OK", "built_slide": {args.slide}, "pptx": "{saved}"}}')
    else:
        c = SlideCanvas(palette=palette, typography=typography, template_path=template_path, theme=theme)
        for fn in slide_funcs:
            c.new_slide()
            fn(c, total)
        saved = c.save(out_path)
        print(f'{{"status": "OK", "built_slides": {total}, "pptx": "{saved}"}}')
