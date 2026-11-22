"""
vector_primitives.py
1280x720 SVG-flavored geometry helpers, vector drawing primitives,
Node Registry, and auto-routing connectors for SlideCanvas.
"""
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from pptx.enum.shapes import MSO_CONNECTOR
from pptx.util import Emu

# ---------------------------------------------------------------------------
# Constants: Exact Integer Mapping 1280x720 px -> 16:9 Widescreen EMU
# 1 px = 9525 EMU = 0.75 pt = 0.026458333 cm
# ---------------------------------------------------------------------------
W_PX: float = 1280.0
H_PX: float = 720.0
PX_TO_EMU: int = 9525
PX_TO_CM: float = 33.8666666667 / 1280.0
CM_TO_PX: float = 1280.0 / 33.8666666667

_NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
_PATH_CMD_RE = re.compile(
    r"([MmLlHhVvCcSsQqTtZz])|([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)"
)

__all__ = [
    "W_PX",
    "H_PX",
    "PX_TO_EMU",
    "PX_TO_CM",
    "CM_TO_PX",
    "px",
    "polar",
    "lerp",
    "_split_boxes",
    "_dash_to_prst",
    "_parse_svg_path",
    "VectorPrimitivesMixin",
]


def px(val: float) -> Emu:
    """Convert 1280x720 canvas pixel value to OpenXML EMU."""
    return Emu(int(round(float(val) * PX_TO_EMU)))


def polar(cx: float, cy: float, r: float, deg: float) -> Tuple[float, float]:
    """Return (x, y) in 1280x720 canvas coords for radius r and angle deg (0=right, -90=top)."""
    rad = math.radians(deg)
    return (round(cx + r * math.cos(rad), 2), round(cy + r * math.sin(rad), 2))


def lerp(a: float, b: float, t: float) -> float:
    """Linearly interpolate between a and b by factor t."""
    return a + (b - a) * t


def _split_boxes(
    total: float,
    start: float,
    count: int,
    gap: float,
    weights: Optional[List[float]] = None,
) -> List[Tuple[float, float]]:
    """Split a linear span into evenly or weighted segments separated by gap."""
    w_list = [float(w) for w in weights] if weights else [1.0] * max(1, count)
    w_sum = sum(w_list) or 1.0
    usable = max(10.0, total - gap * max(0, len(w_list) - 1))
    out: List[Tuple[float, float]] = []
    cur = start
    for wt in w_list:
        size = usable * (wt / w_sum)
        out.append((round(cur, 2), round(size, 2)))
        cur += size + gap
    return out


def _dash_to_prst(dash_token: str) -> str:
    """Map a stroke dash token or numeric dasharray to an OpenXML prstDash value."""
    s = dash_token.strip().lower()
    if s in ("", "none", "solid"):
        return "solid"
    if s in ("dash", "dot", "dashdot", "lgdash", "sysdot", "sysdash", "lgdashdot"):
        mapping = {
            "dashdot": "dashDot",
            "lgdash": "lgDash",
            "sysdot": "sysDot",
            "sysdash": "sysDash",
            "lgdashdot": "lgDashDot",
        }
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
    """Parse an SVG path 'd' string into normalized absolute (cmd, points) ops."""
    tokens: List[Any] = [
        m.group(1) if m.group(1) else float(m.group(2))
        for m in _PATH_CMD_RE.finditer(d)
    ]
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
                    x1, y1, x2, y2, x, y = (
                        cx + x1,
                        cy + y1,
                        cx + x2,
                        cy + y2,
                        cx + x,
                        cy + y,
                    )
                ops.append(("C", [(x1, y1), (x2, y2), (x, y)]))
                last_ctrl = (x2, y2)
                cx, cy = x, y
        elif ucmd == "S":
            while has_num():
                x2, y2, x, y = tokens[i : i + 4]
                i += 4
                if is_rel:
                    x2, y2, x, y = cx + x2, cy + y2, cx + x, cy + y
                x1, y1 = (
                    (2 * cx - last_ctrl[0], 2 * cy - last_ctrl[1])
                    if last_ctrl
                    else (cx, cy)
                )
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


def _sample_cubic_bezier(
    p0: Tuple[float, float],
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    steps: int,
    include_start: bool = True,
) -> List[Tuple[float, float]]:
    """Sample a cubic Bezier curve into canvas coordinate points."""
    start = 0 if include_start else 1
    pts: List[Tuple[float, float]] = []
    for s in range(start, steps + 1):
        t = s / steps
        u = 1.0 - t
        bx = u**3 * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + t**3 * p3[0]
        by = u**3 * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + t**3 * p3[1]
        pts.append((bx, by))
    return pts


def _sample_elliptical_arc(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_deg: float,
    sweep_deg: float,
    steps: int,
    reverse: bool = False,
) -> List[Tuple[float, float]]:
    """Sample an elliptical arc between start_deg and start_deg + sweep_deg."""
    indices = range(steps, -1, -1) if reverse else range(steps + 1)
    return [
        (
            cx + rx * math.cos(math.radians(start_deg + sweep_deg * (i / steps))),
            cy + ry * math.sin(math.radians(start_deg + sweep_deg * (i / steps))),
        )
        for i in indices
    ]


def _arrow_head_metrics(seg_len: float, half_w: float, head_size: float) -> Tuple[float, float]:
    """Compute arrowhead length and half-wing width in canvas px."""
    head_len = min(head_size * 0.9, seg_len * 0.65)
    head_half_w = max(half_w + 1.5, head_size * math.sin(math.pi / 6.5))
    return head_len, head_half_w


class VectorPrimitivesMixin:
    """
    Mixin providing Node Registry, auto-routed connectors, extruded arrows,
    and freeform vector primitives (polyline, bezier, curve, path, arc, donut).

    Expects the subclass (`SlideCanvas`) to provide:
      `self.slide`, `self._nodes`, `self._port_counts`, `self._id_counter`,
      `self._next_id()`, `self.parse_stroke()`, `self.resolve_hex()`,
      `self._apply_style()`, `self.circle()`, and `self.pill()`.
    """

    def _register_node(
        self, node_id: Optional[str], x: float, y: float, w: float, h: float
    ) -> None:
        """Record a named node bounding box and center in the slide node registry."""
        if node_id:
            self._nodes[str(node_id)] = {
                "x": float(x),
                "y": float(y),
                "w": float(w),
                "h": float(h),
                "cx": float(x + w / 2.0),
                "cy": float(y + h / 2.0),
            }

    def _build_poly(
        self,
        pts_px: List[Tuple[float, float]],
        closed: bool,
        fill: Any,
        stroke: Any,
        name: str,
    ) -> Any:
        """Build and style an OpenXML freeform polygon/polyline shape."""
        if len(pts_px) < 2:
            return None
        pts_emu = [(int(round(px(x))), int(round(px(y)))) for x, y in pts_px]
        builder = self.slide.shapes.build_freeform(pts_emu[0][0], pts_emu[0][1])
        builder.add_line_segments(pts_emu[1:], close=closed)
        shp = builder.convert_to_shape()
        shp.name = name
        self._apply_style(shp, fill=fill, stroke=stroke)
        return shp

    def _resolve_arrow_stroke(
        self, stroke: Any
    ) -> Tuple[Dict[str, Any], str, float]:
        """Parse stroke spec into (stroke_dict, fill_color_expr, half_width_px)."""
        st = self.parse_stroke(stroke)
        c_expr = (
            f"#{st['hex']}@{st['opacity']}"
            if st.get("opacity") is not None
            else f"#{st.get('hex', self.resolve_hex('accent'))}"
        )
        width_pt = float(st.get("width_pt", st.get("width", 2.0)))
        half_w = max(0.75, (width_pt * (4.0 / 3.0)) / 2.0)
        return st, c_expr, half_w

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: Any = "border:1",
        name: Optional[str] = None,
    ) -> Any:
        """Draw a straight stroked line segment via native OpenXML connector (handles all quadrants)."""
        shp = self.slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, px(x1), px(y1), px(x2), px(y2)
        )
        shp.name = name or f"vec_line_{self._next_id()}"
        self._apply_style(shp, fill="none", stroke=stroke)
        return shp

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: Any = "accent:2",
        head_size: float = 9.0,
        name: Optional[str] = None,
    ) -> Any:
        """Draw a single-piece 7-point filled polygon arrow from (x1, y1) to (x2, y2)."""
        _, c_expr, half_w = self._resolve_arrow_stroke(stroke)
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 1e-3:
            return None
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux  # unit normal perpendicular to shaft

        head_len, head_half_w = _arrow_head_metrics(dist, half_w, head_size)
        bx = x2 - ux * head_len
        by = y2 - uy * head_len

        pts = [
            (x1 + nx * half_w, y1 + ny * half_w),
            (bx + nx * half_w, by + ny * half_w),
            (bx + nx * head_half_w, by + ny * head_half_w),
            (x2, y2),
            (bx - nx * head_half_w, by - ny * head_half_w),
            (bx - nx * half_w, by - ny * half_w),
            (x1 - nx * half_w, y1 - ny * half_w),
        ]
        return self._build_poly(
            pts, True, fill=c_expr, stroke="none", name=name or f"vec_arrow_{self._next_id()}"
        )

    def _extrude_arrow_poly(
        self,
        pts: List[Tuple[float, float]],
        half_w: float,
        head_size: float,
        arrow: bool,
        fill_expr: str,
        name: str,
    ) -> Any:
        """Extrude a multi-point centerline into a unified filled shaft+arrowhead polygon."""
        clean: List[Tuple[float, float]] = []
        for p in pts:
            if not clean or math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) > 1e-2:
                clean.append((float(p[0]), float(p[1])))
        if len(clean) < 2:
            return None

        tip = clean[-1]
        prev = clean[-2]
        seg_dx, seg_dy = tip[0] - prev[0], tip[1] - prev[1]
        seg_len = math.hypot(seg_dx, seg_dy)
        if seg_len < 1e-3:
            return None

        head_len, head_half_w = _arrow_head_metrics(seg_len, half_w, head_size)
        shaft_pts = list(clean)
        if arrow:
            ux_last, uy_last = seg_dx / seg_len, seg_dy / seg_len
            bx = tip[0] - ux_last * head_len
            by = tip[1] - uy_last * head_len
            shaft_pts[-1] = (bx, by)

        # Compute unit direction and left normal (+90 deg in screen coords) for each segment
        segs = []
        for i in range(len(shaft_pts) - 1):
            dx = shaft_pts[i + 1][0] - shaft_pts[i][0]
            dy = shaft_pts[i + 1][1] - shaft_pts[i][1]
            d = math.hypot(dx, dy)
            if d > 1e-3:
                ux, uy = dx / d, dy / d
                segs.append((ux, uy, -uy, ux))
        if not segs:
            return None

        left_side: List[Tuple[float, float]] = []
        right_side: List[Tuple[float, float]] = []
        n_pts = len(shaft_pts)
        for i, pt in enumerate(shaft_pts):
            if i == 0:
                _, _, nx, ny = segs[0]
                mx, my = nx * half_w, ny * half_w
            elif i == n_pts - 1:
                _, _, nx, ny = segs[-1]
                mx, my = nx * half_w, ny * half_w
            else:
                _, _, nx0, ny0 = segs[min(i - 1, len(segs) - 1)]
                _, _, nx1, ny1 = segs[min(i, len(segs) - 1)]
                rx, ry = nx0 + nx1, ny0 + ny1
                norm2 = rx * rx + ry * ry
                if norm2 < 0.25:
                    mx, my = nx1 * half_w, ny1 * half_w
                else:
                    norm = math.sqrt(norm2)
                    scale = min(2.5 * half_w / norm, 2.0 * half_w / norm2)
                    mx, my = rx * scale, ry * scale
            left_side.append((pt[0] + mx, pt[1] + my))
            right_side.append((pt[0] - mx, pt[1] - my))

        if arrow:
            _, _, nkx, nky = segs[-1]
            bpt = shaft_pts[-1]
            wing_l = (bpt[0] + nkx * head_half_w, bpt[1] + nky * head_half_w)
            wing_r = (bpt[0] - nkx * head_half_w, bpt[1] - nky * head_half_w)
            poly_pts = left_side + [wing_l, tip, wing_r] + list(reversed(right_side))
        else:
            poly_pts = left_side + list(reversed(right_side))

        return self._build_poly(poly_pts, True, fill=fill_expr, stroke="none", name=name)

    def _port_point_and_normal(
        self, node_id: str, port: str, spread_px: float
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Compute an anchor point and outward unit normal on a node edge, spreading parallel edges."""
        node = self._nodes[node_id]
        x, y, w, h, cx, cy = (
            node["x"],
            node["y"],
            node["w"],
            node["h"],
            node["cx"],
            node["cy"],
        )
        key = (node_id, port)
        k = self._port_counts.get(key, 0)
        self._port_counts[key] = k + 1
        # Deterministic alternating offset sequence: 0, +1, -1, +2, -2, ...
        if k == 0:
            step = 0
        else:
            step = ((k + 1) // 2) * (1 if k % 2 == 1 else -1)

        if port == "top":
            off = max(-0.3 * w, min(0.3 * w, step * spread_px))
            return (cx + off, y), (0.0, -1.0)
        if port == "bottom":
            off = max(-0.3 * w, min(0.3 * w, step * spread_px))
            return (cx + off, y + h), (0.0, 1.0)
        if port == "left":
            off = max(-0.3 * h, min(0.3 * h, step * spread_px))
            return (x, cy + off), (-1.0, 0.0)
        if port == "right":
            off = max(-0.3 * h, min(0.3 * h, step * spread_px))
            return (x + w, cy + off), (1.0, 0.0)
        raise ValueError(
            f"Unsupported port '{port}' (expected 'top', 'bottom', 'left', or 'right')"
        )

    def connect(
        self,
        src_id: str,
        dst_id: str,
        style: str = "ortho",
        from_port: str = "auto",
        to_port: str = "auto",
        stroke: Any = "accent:2",
        head_size: float = 9.0,
        label: str = "",
        label_fill: str = "bg",
        arrow: bool = True,
        spread_px: float = 14.0,
        name: Optional[str] = None,
    ) -> Any:
        """Connect two registered nodes (by id) with auto-port routing ('ortho', 'bezier', 'straight')."""
        if src_id not in self._nodes:
            raise KeyError(
                f"Unknown source node id '{src_id}'. Pass id='{src_id}' when creating rect/pill/circle/ellipse."
            )
        if dst_id not in self._nodes:
            raise KeyError(
                f"Unknown destination node id '{dst_id}'. Pass id='{dst_id}' when creating rect/pill/circle/ellipse."
            )

        src = self._nodes[src_id]
        dst = self._nodes[dst_id]
        dx = dst["cx"] - src["cx"]
        dy = dst["cy"] - src["cy"]

        if abs(dx) >= abs(dy):
            auto_from, auto_to = ("right", "left") if dx >= 0 else ("left", "right")
        else:
            auto_from, auto_to = ("bottom", "top") if dy >= 0 else ("top", "bottom")

        fp = auto_from if from_port == "auto" else from_port.lower()
        tp = auto_to if to_port == "auto" else to_port.lower()

        (x1, y1), (nx1, ny1) = self._port_point_and_normal(src_id, fp, spread_px)
        (x2, y2), (nx2, ny2) = self._port_point_and_normal(dst_id, tp, spread_px)

        st, c_expr, half_w = self._resolve_arrow_stroke(stroke)

        mode = style.lower()
        if mode == "straight":
            pts = [(x1, y1), (x2, y2)]
        elif mode == "bezier":
            dist = max(40.0, math.hypot(x2 - x1, y2 - y1) * 0.42)
            c1 = (x1 + nx1 * dist, y1 + ny1 * dist)
            c2 = (x2 + nx2 * dist, y2 + ny2 * dist)
            pts = _sample_cubic_bezier((x1, y1), c1, c2, (x2, y2), steps=20, include_start=True)
        else:  # "ortho"
            h_from = fp in ("left", "right")
            h_to = tp in ("left", "right")
            if h_from and h_to:
                mid_x = (x1 + x2) / 2.0
                pts = [(x1, y1), (mid_x, y1), (mid_x, y2), (x2, y2)]
            elif (not h_from) and (not h_to):
                mid_y = (y1 + y2) / 2.0
                pts = [(x1, y1), (x1, mid_y), (x2, mid_y), (x2, y2)]
            elif h_from and (not h_to):
                pts = [(x1, y1), (x2, y1), (x2, y2)]
            else:
                pts = [(x1, y1), (x1, y2), (x2, y2)]

        conn_name = name or f"vec_conn_{self._next_id()}"
        is_dashed = st.get("dash", "solid") != "solid"
        if is_dashed:
            # Draw dashed path and optionally attach a solid arrowhead at the tip
            path_pts = list(pts)
            if arrow and len(path_pts) >= 2:
                tx, ty = path_pts[-1]
                px_p, py_p = path_pts[-2]
                sd = math.hypot(tx - px_p, ty - py_p)
                if sd > 1e-3:
                    ux, uy = (tx - px_p) / sd, (ty - py_p) / sd
                    hlen, hhw = _arrow_head_metrics(sd, half_w, head_size)
                    bx, by = tx - ux * hlen, ty - uy * hlen
                    path_pts[-1] = (bx, by)
                    self.polyline(path_pts, stroke=stroke, name=conn_name)
                    nx_u, ny_u = -uy, ux
                    shp = self._build_poly(
                        [
                            (tx, ty),
                            (bx + nx_u * hhw, by + ny_u * hhw),
                            (bx - nx_u * hhw, by - ny_u * hhw),
                        ],
                        True,
                        fill=c_expr,
                        stroke="none",
                        name=f"{conn_name}_head",
                    )
                else:
                    shp = self.polyline(path_pts, stroke=stroke, name=conn_name)
            else:
                shp = self.polyline(path_pts, stroke=stroke, name=conn_name)
        else:
            shp = self._extrude_arrow_poly(pts, half_w, head_size, arrow, c_expr, conn_name)

        if label:
            # Compute geometric arc-length midpoint of path
            if len(pts) == 2:
                mx, my = (pts[0][0] + pts[1][0]) / 2.0, (pts[0][1] + pts[1][1]) / 2.0
            else:
                seg_lens = [
                    math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                    for i in range(len(pts) - 1)
                ]
                total_len = sum(seg_lens)
                half_len = total_len / 2.0
                acc = 0.0
                mx, my = pts[len(pts) // 2]
                for i, sl in enumerate(seg_lens):
                    if acc + sl >= half_len and sl > 1e-3:
                        t = (half_len - acc) / sl
                        mx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                        my = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                        break
                    acc += sl
            lw = max(56.0, len(str(label)) * 7.5 + 20.0)
            lh = 22.0
            self.pill(
                mx - lw / 2.0,
                my - lh / 2.0,
                lw,
                lh,
                fill=label_fill,
                stroke="border:0.75",
                text=str(label),
                size=9.5,
                color="muted",
                bold=True,
                name=f"conn_lbl_{self._next_id()}",
            )
        return shp

    def polyline(
        self,
        points: List[Tuple[float, float]],
        stroke: Any = "accent:2",
        fill: Any = "none",
        closed: bool = False,
        name: Optional[str] = None,
    ) -> Any:
        """Draw an open or closed polyline through the given canvas points."""
        return self._build_poly(
            points, closed, fill, stroke, name or f"vec_poly_{self._next_id()}"
        )

    def bezier(
        self,
        p0: Tuple[float, float],
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        stroke: Any = "accent:2",
        fill: Any = "none",
        steps: int = 20,
        name: Optional[str] = None,
    ) -> Any:
        """Draw a sampled cubic Bezier curve from p0 to p3 with control points p1, p2."""
        pts = _sample_cubic_bezier(p0, p1, p2, p3, steps=steps, include_start=True)
        return self._build_poly(
            pts, False, fill, stroke, name or f"vec_poly_{self._next_id()}"
        )

    def curve(
        self,
        points: List[Tuple[float, float]],
        stroke: Any = "accent:2",
        fill: Any = "none",
        closed: bool = False,
        tension: float = 0.5,
        name: Optional[str] = None,
    ) -> Any:
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
                x = 0.5 * (
                    (2 * p1[0])
                    + (-p0[0] + p2[0]) * t
                    + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                    + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                )
                y = 0.5 * (
                    (2 * p1[1])
                    + (-p0[1] + p2[1]) * t
                    + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                    + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                )
                sampled.append((x, y))
        return self._build_poly(
            sampled, closed, fill, stroke, name or f"vec_poly_{self._next_id()}"
        )

    def path(
        self,
        d: str,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        stroke: Any = "accent:2",
        fill: Any = "none",
        name: Optional[str] = None,
    ) -> Any:
        """Render an SVG path string (M, L, H, V, C, S, Q, Z) at offset (x, y) and scale."""
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
                p1, p2, p3 = pts
                for bx, by in _sample_cubic_bezier(
                    (fx, fy), p1, p2, p3, steps=16, include_start=False
                ):
                    cur.append((x + bx * scale, y + by * scale))
                fx, fy = p3
            elif kind == "Z":
                if len(cur) >= 2:
                    subpaths.append((cur, True))
                cur = []
        if len(cur) >= 2:
            subpaths.append((cur, False))
        last_shp = None
        for sp_pts, closed in subpaths:
            last_shp = self._build_poly(
                sp_pts, closed, fill, stroke, name or f"vec_poly_{self._next_id()}"
            )
        return last_shp

    def arc(
        self,
        cx: float,
        cy: float,
        r: float,
        start_deg: float = 0,
        end_deg: float = 270,
        stroke: Any = "accent:2",
        fill: Any = "none",
        ry: Optional[float] = None,
        name: Optional[str] = None,
    ) -> Any:
        """Draw a circular or elliptical arc from start_deg to end_deg."""
        ry_v = r if ry is None else ry
        sweep = end_deg - start_deg
        steps = max(24, int(math.ceil(abs(sweep) / 3.0)))
        pts = _sample_elliptical_arc(cx, cy, r, ry_v, start_deg, sweep, steps)
        return self._build_poly(
            pts, False, fill, stroke, name or f"vec_arc_{self._next_id()}"
        )

    def donut(
        self,
        cx: float,
        cy: float,
        r: float,
        start_deg: float = -90,
        end_deg: float = 180,
        thickness: float = 0.24,
        fill: Any = "accent",
        stroke: Any = "none",
        ry: Optional[float] = None,
        name: Optional[str] = None,
    ) -> Any:
        """Draw a closed circular or elliptical ring sector (donut gauge/chart)."""
        ry_out = r if ry is None else ry
        thick = max(0.05, min(0.9, thickness))
        rx_in, ry_in = r * (1.0 - thick), ry_out * (1.0 - thick)
        sweep = end_deg - start_deg
        steps = max(24, int(math.ceil(abs(sweep) / 3.0)))
        outer = _sample_elliptical_arc(cx, cy, r, ry_out, start_deg, sweep, steps)
        inner = _sample_elliptical_arc(
            cx, cy, rx_in, ry_in, start_deg, sweep, steps, reverse=True
        )
        return self._build_poly(
            outer + inner, True, fill, stroke, name or f"vec_arc_{self._next_id()}"
        )
