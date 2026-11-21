#!/usr/bin/env python3
"""
slide_canvas.py
1280x720 SVG-Flavored Python Canvas Engine -> 100% Native OpenXML (.pptx).
LLM writes concise Python using familiar SVG/Canvas mental models (1280x720 viewBox,
loops, polar(), text_auto(), #HEX@opacity, grad(...), stroke color@op:w:dash, path d=...),
compiling straight into native editable PowerPoint OpenXML via python-pptx.
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.util import Emu, Pt

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from text_measure import wrap_and_measure_text

# ---------------------------------------------------------------------------
# Constants: Exact Integer Mapping 1280x720 px -> 16:9 Widescreen EMU
# 1 px = 9525 EMU = 0.75 pt = 0.026458333 cm
# ---------------------------------------------------------------------------
W_PX = 1280.0
H_PX = 720.0
PX_TO_EMU = 9525
PX_TO_CM = 33.8666666667 / 1280.0
CM_TO_PX = 1280.0 / 33.8666666667

_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_HEX6_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")
_NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_PATH_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtZz])|([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)")


def px(val: float) -> Emu:
    return Emu(int(round(float(val) * PX_TO_EMU)))


def polar(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    """Return (x, y) in 1280x720 canvas coords for radius r and angle deg (0=right, -90=top)."""
    rad = math.radians(deg)
    return (round(cx + r * math.cos(rad), 2), round(cy + r * math.sin(rad), 2))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _split_boxes(
    total: float, start: float, n: int, gap: float, weights: Optional[List[float]] = None
) -> List[Tuple[float, float]]:
    w_list = [float(w) for w in weights] if weights else [1.0] * max(1, n)
    w_sum = sum(w_list) or 1.0
    usable = max(10.0, total - gap * max(0, len(w_list) - 1))
    out: List[Tuple[float, float]] = []
    cur = start
    for wt in w_list:
        size = usable * (wt / w_sum)
        out.append((round(cur, 2), round(size, 2)))
        cur += size + gap
    return out


# ---------------------------------------------------------------------------
# Color, Contrast & Shorthand Parsers
# ---------------------------------------------------------------------------
def _rel_luminance(hex6: str) -> float:
    h = hex6.lstrip("#").upper()
    rgb = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    l1, l2 = _rel_luminance(hex_a), _rel_luminance(hex_b)
    return round((max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 2)


def _hex_to_rgb(hex6: str) -> RGBColor:
    h = hex6.lstrip("#").upper()
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _dash_to_prst(dash_token: str) -> str:
    s = dash_token.strip().lower()
    if s in ("", "none", "solid"):
        return "solid"
    if s in ("dash", "dot", "dashdot", "lgdash", "sysdot", "sysdash", "lgdashdot"):
        mapping = {"dashdot": "dashDot", "lgdash": "lgDash", "sysdot": "sysDot", "sysdash": "sysDash", "lgdashdot": "lgDashDot"}
        return mapping.get(s, s)
    nums = [float(x) for x in _NUM_RE.findall(s)]
    if len(nums) >= 3:
        return "dashDot"
    if len(nums) >= 1 and nums[0] <= 2.5:
        return "dot"
    if len(nums) >= 1 and nums[0] >= 8.0:
        return "lgDash"
    return "dash"


def _parse_svg_path(d: str) -> List[Tuple[str, List[Tuple[float, float]]]]:
    tokens: List[Any] = [m.group(1) if m.group(1) else float(m.group(2)) for m in _PATH_CMD_RE.finditer(d)]
    ops: List[Tuple[str, List[Tuple[float, float]]]] = []
    i = 0
    cmd = ""
    cx, cy = 0.0, 0.0
    sx, sy = 0.0, 0.0
    last_ctrl: Optional[Tuple[float, float]] = None

    def has_num() -> bool:
        return i < len(tokens) and isinstance(tokens[i], float)

    while i < len(tokens):
        if isinstance(tokens[i], str):
            cmd = tokens[i]
            i += 1
        if cmd in ("Z", "z"):
            ops.append(("Z", []))
            cx, cy = sx, sy
            last_ctrl = None
            cmd = ""
            continue
        if not has_num():
            break
        is_rel = cmd.islower()
        ucmd = cmd.upper()
        if ucmd == "M":
            first = True
            while has_num():
                x, y = tokens[i], tokens[i + 1]
                i += 2
                if is_rel:
                    x, y = cx + x, cy + y
                cx, cy = x, y
                if first:
                    sx, sy = cx, cy
                    ops.append(("M", [(cx, cy)]))
                    first = False
                else:
                    ops.append(("L", [(cx, cy)]))
            last_ctrl = None
            cmd = "l" if is_rel else "L"
        elif ucmd == "L":
            while has_num():
                x, y = tokens[i], tokens[i + 1]
                i += 2
                if is_rel:
                    x, y = cx + x, cy + y
                cx, cy = x, y
                ops.append(("L", [(cx, cy)]))
            last_ctrl = None
        elif ucmd == "H":
            while has_num():
                x = tokens[i]
                i += 1
                cx = (cx + x) if is_rel else x
                ops.append(("L", [(cx, cy)]))
            last_ctrl = None
        elif ucmd == "V":
            while has_num():
                y = tokens[i]
                i += 1
                cy = (cy + y) if is_rel else y
                ops.append(("L", [(cx, cy)]))
            last_ctrl = None
        elif ucmd == "C":
            while has_num():
                x1, y1, x2, y2, x, y = tokens[i : i + 6]
                i += 6
                if is_rel:
                    x1, y1, x2, y2, x, y = cx + x1, cy + y1, cx + x2, cy + y2, cx + x, cy + y
                ops.append(("C", [(x1, y1), (x2, y2), (x, y)]))
                last_ctrl = (x2, y2)
                cx, cy = x, y
        elif ucmd == "S":
            while has_num():
                x2, y2, x, y = tokens[i : i + 4]
                i += 4
                if is_rel:
                    x2, y2, x, y = cx + x2, cy + y2, cx + x, cy + y
                x1, y1 = (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1]) if last_ctrl else (cx, cy)
                ops.append(("C", [(x1, y1), (x2, y2), (x, y)]))
                last_ctrl = (x2, y2)
                cx, cy = x, y
        elif ucmd == "Q":
            while has_num():
                qx, qy, x, y = tokens[i : i + 4]
                i += 4
                if is_rel:
                    qx, qy, x, y = cx + qx, cy + qy, cx + x, cy + y
                c1 = (cx + (2.0 / 3.0) * (qx - cx), cy + (2.0 / 3.0) * (qy - cy))
                c2 = (x + (2.0 / 3.0) * (qx - x), y + (2.0 / 3.0) * (qy - y))
                ops.append(("C", [c1, c2, (x, y)]))
                last_ctrl = (qx, qy)
                cx, cy = x, y
        else:
            break
    return ops


# ---------------------------------------------------------------------------
# SlideCanvas Class
# ---------------------------------------------------------------------------
class SlideCanvas:
    def __init__(
        self,
        pptx_path: str = None,
        palette: Optional[Dict[str, str]] = None,
        typography: Optional[Dict[str, str]] = None,
        template_path: Optional[str] = None,
        check_contrast: bool = True,
    ):
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

        self.palette: Dict[str, str] = {}
        default_pal = {
            "bg_canvas": "F5F5F7",
            "bg_surface": "FFFFFF",
            "ink_primary": "1D1D1F",
            "ink_muted": "6E6E73",
            "border_grid": "D1D1D6",
            "accent_primary": "0071E3",
            "accent_secondary": "3A7D74",
        }
        self.set_palette({**default_pal, **(palette or {})}, check_contrast=check_contrast)

        self.typography = {
            "font_heading": "PingFang TC",
            "font_body": "PingFang TC",
            "font_mono": "Menlo",
            **(typography or {}),
        }

    def _pick_blank_layout(self):
        for lay in self.prs.slide_layouts:
            if "blank" in lay.name.lower() or len(lay.placeholders) == 0:
                return lay
        return self.prs.slide_layouts[min(6, len(self.prs.slide_layouts) - 1)]

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def set_palette(self, pal: Dict[str, str], check_contrast: bool = True):
        clean: Dict[str, str] = {}
        for k, v in pal.items():
            clean[k] = str(v).strip().lstrip("#").upper()
        # Bi-directional aliases so LLM can use short or full role names seamlessly
        alias_pairs = [
            ("bg_canvas", "bg"),
            ("bg_surface", "surface"),
            ("ink_primary", "ink"),
            ("ink_muted", "muted"),
            ("border_grid", "border"),
            ("accent_primary", "accent"),
            ("accent_secondary", "accent2"),
        ]
        for full_k, short_k in alias_pairs:
            if full_k in clean and short_k not in clean:
                clean[short_k] = clean[full_k]
            elif short_k in clean and full_k not in clean:
                clean[full_k] = clean[short_k]
        clean.setdefault("white", "FFFFFF")
        clean.setdefault("black", "000000")
        self.palette = clean

        if check_contrast and "bg_canvas" in clean and "ink_primary" in clean:
            bg, ink = clean["bg_canvas"], clean["ink_primary"]
            if _HEX6_RE.match(bg) and _HEX6_RE.match(ink):
                cr = contrast_ratio(bg, ink)
                if cr < 4.5:
                    raise ValueError(f"WCAG Contrast Violation: bg_canvas (#{bg}) vs ink_primary (#{ink}) is {cr}:1 (< 4.5:1 minimum).")

    def resolve_hex(self, token: str, default: str = "ink") -> str:
        t = str(token or default).strip()
        if t in self.palette:
            return self.palette[t]
        tl = t.lower()
        if tl in self.palette:
            return self.palette[tl]
        named = {"white": "FFFFFF", "black": "000000", "transparent": "none", "none": "none"}
        if tl in named:
            return named[tl]
        h = t.lstrip("#").upper()
        if len(h) == 3 and all(c in "0123456789ABCDEF" for c in h):
            return "".join(c * 2 for c in h)
        if len(h) == 6 and all(c in "0123456789ABCDEF" for c in h):
            return h
        return self.palette.get(default, "1D1D1F")

    def parse_color_alpha(self, expr: Optional[str], default: str = "ink") -> Tuple[str, Optional[float]]:
        if expr is None:
            return "none", None
        s = str(expr).strip()
        if s.lower() in ("", "none", "transparent", "clear"):
            return "none", None
        if "@" in s:
            c_part, op_part = s.split("@", 1)
            return self.resolve_hex(c_part, default), max(0.0, min(1.0, float(op_part)))
        return self.resolve_hex(s, default), None

    def parse_fill(self, fill: Any) -> Dict[str, Any]:
        if fill is None:
            return {"kind": "none"}
        s = str(fill).strip()
        if s.lower() in ("", "none", "transparent", "clear"):
            return {"kind": "none"}
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
                hx, op = self.parse_color_alpha(se, "accent")
                stops.append((pos, hx, op))
            return {"kind": "grad", "angle": ang, "stops": stops}
        hx, op = self.parse_color_alpha(s, "surface")
        return {"kind": "none"} if hx == "none" else {"kind": "solid", "hex": hx, "opacity": op}

    def parse_stroke(self, stroke: Any) -> Dict[str, Any]:
        if stroke is None:
            return {"kind": "none"}
        s = str(stroke).strip()
        if s.lower() in ("", "none", "transparent", "clear"):
            return {"kind": "none"}
        parts = s.split(":")
        hx, op = self.parse_color_alpha(parts[0], "border")
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
                el = parse_xml(f'<a:solidFill {ns}><a:srgbClr val="{fill_info["hex"]}"><a:alpha val="{av}"/></a:srgbClr></a:solidFill>')
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
                f'<a:gradFill {ns} flip="none" rotWithShape="1"><a:gsLst>{"".join(gs_parts)}</a:gsLst><a:lin ang="{ang}" scaled="1"/></a:gradFill>'
            )
        insert_idx = 0
        for idx, child in enumerate(list(container_el)):
            if child.tag.split("}")[-1] in ("xfrm", "prstGeom", "custGeom"):
                insert_idx = idx + 1
        container_el.insert(insert_idx, el)

    def _apply_style(self, shp, fill: Any = "none", stroke: Any = "none"):
        sp_pr = shp._element.spPr
        self._insert_oxml_fill(sp_pr, self.parse_fill(fill))

        st = self.parse_stroke(stroke)
        if st["kind"] == "none":
            shp.line.fill.background()
        else:
            shp.line.color.rgb = _hex_to_rgb(st["hex"])
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
        size: float = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_x_px: float = 8.0,
        pad_v_px: float = 6.0,
    ):
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
        hx, _ = self.parse_color_alpha(color, "ink")
        rgb = _hex_to_rgb(hx if hx != "none" else "1D1D1F")

        lines = str(txt).split("\n")
        for idx, line_str in enumerate(lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.alignment = p_align
            run = p.add_run()
            run.text = line_str
            run.font.name = fname
            run.font.size = Pt(float(size))
            run.font.bold = bool(bold)
            run.font.color.rgb = rgb

    # -----------------------------------------------------------------------
    # Slide & Chrome Management
    # -----------------------------------------------------------------------
    def new_slide(self, bg: Optional[str] = None):
        self.slide = self.prs.slides.add_slide(self._blank_layout)
        self.slide_idx = len(self.prs.slides)
        self.set_background(bg or "bg_canvas")
        return self.slide

    def select_slide(self, slide_num: int, bg: Optional[str] = None, clear: bool = True):
        while len(self.prs.slides) < slide_num:
            self.prs.slides.add_slide(self._blank_layout)
        self.slide = self.prs.slides[slide_num - 1]
        self.slide_idx = slide_num
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
    def cols(self, n: int, x: float = 68, y: float = 166, w: float = 1144, h: float = 460, gap: float = 24, weights: Optional[List[float]] = None) -> List[Tuple[float, float, float, float]]:
        return [(cx, round(y, 2), cw, round(h, 2)) for cx, cw in _split_boxes(w, x, n, gap, weights)]

    def rows(self, n: int, x: float = 68, y: float = 166, w: float = 1144, h: float = 460, gap: float = 20, weights: Optional[List[float]] = None) -> List[Tuple[float, float, float, float]]:
        return [(round(x, 2), ry, round(w, 2), rh) for ry, rh in _split_boxes(h, y, n, gap, weights)]

    def grid(self, cols_n: int, rows_n: int, x: float = 68, y: float = 166, w: float = 1144, h: float = 460, gap_x: float = 24, gap_y: float = 20) -> List[Tuple[float, float, float, float]]:
        col_spans = _split_boxes(w, x, cols_n, gap_x)
        row_spans = _split_boxes(h, y, rows_n, gap_y)
        return [(cx, ry, cw, rh) for ry, rh in row_spans for cx, cw in col_spans]

    # -----------------------------------------------------------------------
    # Geometry & Typography Primitives (1280x720)
    # -----------------------------------------------------------------------
    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 0,
        fill: Any = "surface",
        stroke: Any = "none",
        text: str = "",
        size: float = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "center",
        valign: str = "middle",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_px: float = 10.0,
        name: Optional[str] = None,
    ):
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if rx > 0 else MSO_SHAPE.RECTANGLE
        shp = self.slide.shapes.add_shape(kind, px(x), px(y), px(max(1.0, w)), px(max(1.0, h)))
        idx = self._next_id()
        shp.name = name or (f"box_{idx}" if str(text).strip() else f"card_bg_{idx}")
        if rx > 0 and min(w, h) > 0:
            shp.adjustments[0] = min(0.49, float(rx) / min(w, h))
        self._apply_style(shp, fill=fill, stroke=stroke)
        if str(text) != "":
            self._set_text(shp, text, size=size, color=color, bold=bold, align=align, valign=valign, font=font, role=role, pad_x_px=pad_px, pad_v_px=pad_px)
        return shp

    def pill(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: Any = "accent@0.12",
        stroke: Any = "accent@0.38:1",
        text: str = "",
        size: float = 11.5,
        color: str = "accent",
        bold: bool = True,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
    ):
        return self.rect(x, y, w, h, rx=h / 2.0, fill=fill, stroke=stroke, text=text, size=size, color=color, bold=bold, align="center", valign="middle", font=font, role=role, pad_px=4, name=name or f"pill_{self._next_id()}")

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: Any = "accent",
        stroke: Any = "none",
        text: str = "",
        size: float = 13.0,
        color: str = "ink",
        bold: bool = False,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
    ):
        return self.ellipse(cx, cy, r, r, fill=fill, stroke=stroke, text=text, size=size, color=color, bold=bold, font=font, role=role, name=name)

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx_px: float,
        ry_px: float,
        fill: Any = "accent",
        stroke: Any = "none",
        text: str = "",
        size: float = 13.0,
        color: str = "ink",
        bold: bool = False,
        font: Optional[str] = None,
        role: Optional[str] = None,
        name: Optional[str] = None,
    ):
        shp = self.slide.shapes.add_shape(MSO_SHAPE.OVAL, px(cx - rx_px), px(cy - ry_px), px(2 * rx_px), px(2 * ry_px))
        idx = self._next_id()
        shp.name = name or (f"circle_{idx}" if str(text).strip() else f"dot_{idx}")
        self._apply_style(shp, fill=fill, stroke=stroke)
        if str(text) != "":
            self._set_text(shp, text, size=size, color=color, bold=bold, align="center", valign="middle", font=font, role=role, pad_x_px=4, pad_v_px=4)
        return shp

    def glow(self, cx: float, cy: float, r: float, color: str = "accent@0.09", rings: int = 2):
        """Ambient concentric soft glow circles (ignored in overlap detection)."""
        base_c, base_op = self.parse_color_alpha(color, "accent")
        base_op = base_op if base_op is not None else 0.10
        for i in range(rings):
            scale = 1.0 - (i * 0.35)
            op = round(min(0.4, base_op * (1.0 + i * 0.4)), 3)
            self.circle(cx, cy, r * scale, fill=f"#{base_c}@{op}", stroke="none", name=f"bg_glow_{self._next_id()}")

    def _build_poly(self, pts_px: List[Tuple[float, float]], closed: bool, fill: Any, stroke: Any, name: str):
        if len(pts_px) < 2:
            return None
        pts_emu = [(int(round(px(x))), int(round(px(y)))) for x, y in pts_px]
        builder = self.slide.shapes.build_freeform(pts_emu[0][0], pts_emu[0][1])
        builder.add_line_segments(pts_emu[1:], close=closed)
        shp = builder.convert_to_shape()
        shp.name = name
        self._apply_style(shp, fill=fill, stroke=stroke)
        return shp

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: Any = "border:1", name: Optional[str] = None):
        return self._build_poly([(x1, y1), (x2, y2)], False, "none", stroke, name or f"vec_line_{self._next_id()}")

    def arrow(self, x1: float, y1: float, x2: float, y2: float, stroke: Any = "accent:2", head_size: float = 9.0, name: Optional[str] = None):
        st = self.parse_stroke(stroke)
        c_expr = f"#{st['hex']}@{st['opacity']}" if st.get("opacity") is not None else f"#{st.get('hex', self.resolve_hex('accent'))}"
        ang = math.atan2(y2 - y1, x2 - x1)
        tip = (x2, y2)
        shaft_end = (x2 - head_size * 0.85 * math.cos(ang), y2 - head_size * 0.85 * math.sin(ang))
        idx = self._next_id()
        self.line(x1, y1, shaft_end[0], shaft_end[1], stroke=stroke, name=f"vec_line_{idx}_shaft")
        p1 = (x2 - head_size * math.cos(ang - math.pi / 6.5), y2 - head_size * math.sin(ang - math.pi / 6.5))
        p2 = (x2 - head_size * math.cos(ang + math.pi / 6.5), y2 - head_size * math.sin(ang + math.pi / 6.5))
        return self._build_poly([tip, p1, p2], True, fill=c_expr, stroke="none", name=name or f"vec_arrow_{idx}")

    def polyline(self, points: List[Tuple[float, float]], stroke: Any = "accent:2", fill: Any = "none", closed: bool = False, name: Optional[str] = None):
        return self._build_poly(points, closed, fill, stroke, name or f"vec_poly_{self._next_id()}")

    def bezier(self, p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], stroke: Any = "accent:2", fill: Any = "none", steps: int = 20, name: Optional[str] = None):
        pts = []
        for s in range(steps + 1):
            t = s / steps
            u = 1.0 - t
            bx = u**3 * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + t**3 * p3[0]
            by = u**3 * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + t**3 * p3[1]
            pts.append((bx, by))
        return self._build_poly(pts, False, fill, stroke, name or f"vec_poly_{self._next_id()}")

    def curve(self, points: List[Tuple[float, float]], stroke: Any = "accent:2", fill: Any = "none", closed: bool = False, tension: float = 0.5, name: Optional[str] = None):
        """Smooth Catmull-Rom spline through arbitrary control points."""
        n = len(points)
        if n < 2:
            return None
        if n == 2:
            return self.polyline(points, stroke=stroke, fill=fill, closed=closed, name=name)
        sampled: List[Tuple[float, float]] = [points[0]]
        segs = n if closed else n - 1
        for i in range(segs):
            p0 = points[(i - 1) % n] if closed else points[max(0, i - 1)]
            p1 = points[i % n]
            p2 = points[(i + 1) % n]
            p3 = points[(i + 2) % n] if closed else points[min(n - 1, i + 2)]
            for step in range(1, 13):
                t = step / 12.0
                t2, t3 = t * t, t * t * t
                x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
                y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
                sampled.append((x, y))
        return self._build_poly(sampled, closed, fill, stroke, name or f"vec_poly_{self._next_id()}")

    def path(self, d: str, x: float = 0.0, y: float = 0.0, scale: float = 1.0, stroke: Any = "accent:2", fill: Any = "none", name: Optional[str] = None):
        ops = _parse_svg_path(d)
        subpaths: List[Tuple[List[Tuple[float, float]], bool]] = []
        cur: List[Tuple[float, float]] = []
        fx, fy = 0.0, 0.0
        for kind, pts in ops:
            if kind == "M":
                if len(cur) >= 2:
                    subpaths.append((cur, False))
                fx, fy = pts[0]
                cur = [(x + fx * scale, y + fy * scale)]
            elif kind == "L":
                fx, fy = pts[0]
                cur.append((x + fx * scale, y + fy * scale))
            elif kind == "C":
                p0x, p0y = fx, fy
                (p1x, p1y), (p2x, p2y), (p3x, p3y) = pts
                for st in range(1, 17):
                    t = st / 16.0
                    u = 1.0 - t
                    bx = u**3 * p0x + 3 * (u**2) * t * p1x + 3 * u * (t**2) * p2x + t**3 * p3x
                    by = u**3 * p0y + 3 * (u**2) * t * p1y + 3 * u * (t**2) * p2y + t**3 * p3y
                    cur.append((x + bx * scale, y + by * scale))
                fx, fy = p3x, p3y
            elif kind == "Z":
                if len(cur) >= 2:
                    subpaths.append((cur, True))
                cur = []
        if len(cur) >= 2:
            subpaths.append((cur, False))
        last_shp = None
        for sp_pts, closed in subpaths:
            last_shp = self._build_poly(sp_pts, closed, fill, stroke, name or f"vec_poly_{self._next_id()}")
        return last_shp

    def arc(self, cx: float, cy: float, r: float, start_deg: float = 0, end_deg: float = 270, stroke: Any = "accent:2", fill: Any = "none", ry: Optional[float] = None, name: Optional[str] = None):
        ry_v = r if ry is None else ry
        sweep = end_deg - start_deg
        steps = max(24, int(math.ceil(abs(sweep) / 3.0)))
        pts = [(cx + r * math.cos(math.radians(start_deg + sweep * (i / steps))), cy + ry_v * math.sin(math.radians(start_deg + sweep * (i / steps)))) for i in range(steps + 1)]
        return self._build_poly(pts, False, fill, stroke, name or f"vec_arc_{self._next_id()}")

    def donut(self, cx: float, cy: float, r: float, start_deg: float = -90, end_deg: float = 180, thickness: float = 0.24, fill: Any = "accent", stroke: Any = "none", ry: Optional[float] = None, name: Optional[str] = None):
        ry_out = r if ry is None else ry
        thick = max(0.05, min(0.9, thickness))
        rx_in, ry_in = r * (1.0 - thick), ry_out * (1.0 - thick)
        sweep = end_deg - start_deg
        steps = max(24, int(math.ceil(abs(sweep) / 3.0)))
        outer = [(cx + r * math.cos(math.radians(start_deg + sweep * (i / steps))), cy + ry_out * math.sin(math.radians(start_deg + sweep * (i / steps)))) for i in range(steps + 1)]
        inner = [(cx + rx_in * math.cos(math.radians(start_deg + sweep * (i / steps))), cy + ry_in * math.sin(math.radians(start_deg + sweep * (i / steps)))) for i in range(steps, -1, -1)]
        return self._build_poly(outer + inner, True, fill, stroke, name or f"vec_arc_{self._next_id()}")

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        size: float = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        valign: str = "top",
        font: Optional[str] = None,
        role: Optional[str] = None,
        pad_px: float = 3.0,
        name: Optional[str] = None,
    ) -> float:
        tb = self.slide.shapes.add_textbox(px(x), px(y), px(max(8.0, w)), px(max(8.0, h)))
        tb.name = name or f"txt_{self._next_id()}"
        self._set_text(tb, text, size=size, color=color, bold=bold, align=align, valign=valign, font=font, role=role, pad_x_px=pad_px, pad_v_px=pad_px)
        return round(y + h, 2)

    def text_auto(
        self,
        x: float,
        y: float,
        w: float,
        text: str,
        size: float = 15.0,
        color: str = "ink",
        bold: bool = False,
        align: str = "left",
        font: Optional[str] = None,
        role: Optional[str] = None,
        line_height: float = 1.38,
        pad_px: float = 3.0,
        name: Optional[str] = None,
    ) -> float:
        """Measure wrapped CJK/Latin text height and place textbox, returning bottom_y."""
        if not text or not str(text).strip():
            return y
        w_cm = max(1.0, (w - 2 * pad_px) * PX_TO_CM)
        _, est_h_cm, _ = wrap_and_measure_text(str(text), box_w_cm=w_cm, font_size_pt=size, bold=bold, line_height=line_height, pad_v_cm=0.14)
        h_px = max(18.0, est_h_cm * CM_TO_PX + 2 * pad_px)
        self.text(x, y, w, h_px, text, size=size, color=color, bold=bold, align=align, valign="top", font=font, role=role, pad_px=pad_px, name=name)
        return round(y + h_px, 2)

    def stat(
        self,
        x: float,
        y: float,
        w: float,
        value: str,
        label: str,
        val_size: float = 46.0,
        lbl_size: float = 13.5,
        val_color: str = "accent",
        lbl_color: str = "ink",
        align: str = "left",
    ) -> float:
        y1 = self.text_auto(x, y, w, value, size=val_size, color=val_color, bold=True, align=align, role="kpi", line_height=1.18, pad_px=2, name=f"stat_val_{self._next_id()}")
        if label:
            return self.text_auto(x, y1 + 4, w, label, size=lbl_size, color=lbl_color, bold=False, align=align, role="body", line_height=1.35, pad_px=2, name=f"stat_lbl_{self._next_id()}")
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

        def style_cell(cell, txt: str, fill_hex: str, txt_hex: str, size_pt: float, is_bold: bool, font_role: str):
            cell.fill.solid()
            cell.fill.fore_color.rgb = _hex_to_rgb(fill_hex)
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
            r.font.color.rgb = _hex_to_rgb(txt_hex)

        r_ptr = 0
        if headers:
            for ci, htxt in enumerate(headers):
                style_cell(tbl.cell(0, ci), htxt, self.resolve_hex("surface"), self.resolve_hex("accent2"), 12.0, True, "mono")
            r_ptr = 1

        for ri, row_vals in enumerate(rows):
            for ci, val in enumerate(row_vals):
                hl = hl_map.get((ri, ci))
                txt_hex = self.resolve_hex(hl) if hl else self.resolve_hex("ink")
                style_cell(tbl.cell(r_ptr + ri, ci), val, self.resolve_hex("bg"), txt_hex, 13.5, bool(ci == 0 or hl), "body")
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
    palette: Optional[Dict[str, str]] = None,
    typography: Optional[Dict[str, str]] = None,
    default_out: str = "build/deck.pptx",
    template_path: Optional[str] = None,
):
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
        c = SlideCanvas(pptx_path=out_path if os.path.exists(out_path) else None, palette=palette, typography=typography, template_path=template_path)
        c.select_slide(args.slide)
        slide_funcs[args.slide - 1](c, total)
        saved = c.save(out_path)
        print(f'{{"status": "OK", "built_slide": {args.slide}, "pptx": "{saved}"}}')
    else:
        c = SlideCanvas(palette=palette, typography=typography, template_path=template_path)
        for idx, fn in enumerate(slide_funcs, start=1):
            c.new_slide()
            fn(c, total)
        saved = c.save(out_path)
        print(f'{{"status": "OK", "built_slides": {total}, "pptx": "{saved}"}}')
