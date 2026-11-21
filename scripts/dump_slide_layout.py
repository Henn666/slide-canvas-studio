#!/usr/bin/env python3
"""
dump_slide_layout.py
單一職責：直接用 Python (python-pptx) 讀取 .pptx 原始 EMU 座標與實際背景/文字對比度，
量測指定單頁 (--slide N) 每個元件的邊界、偵測超出畫布邊界 (out_of_bounds)、非預期重疊 (overlap_pairs) 與文字溢框風險 (overflow_risk)，
輸出 preview/slide_N_layout.json。
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import json
from pptx import Presentation

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from text_measure import wrap_and_measure_text

EMU_PER_CM = 360000.0


def emu_to_cm(val) -> float:
    if val is None:
        return 0.0
    return round(float(val) / EMU_PER_CM, 3)


def estimate_text_height_cm(text: str, font_pt: float, box_w_cm: float) -> float:
    if not text or not text.strip():
        return 0.0
    _, est_h, _ = wrap_and_measure_text(text, box_w_cm=box_w_cm, font_size_pt=font_pt, line_height=1.32, pad_v_cm=0.14)
    return est_h


def extract_shape_font_pt(shp, default_pt: float = 12.5) -> float:
    if not shp.has_text_frame:
        return default_pt
    sizes = []
    for p in shp.text_frame.paragraphs:
        if p.font and p.font.size:
            sizes.append(float(p.font.size.pt))
        for r in p.runs:
            if r.font and r.font.size:
                sizes.append(float(r.font.size.pt))
    return max(sizes) if sizes else default_pt


def is_decorative_shape(name: str, w_cm: float, h_cm: float, text: str = "") -> bool:
    lname = name.lower()
    if lname.startswith("bg_") or lname.endswith("_shaft") or lname == "footer_line":
        return True
    if not text.strip() and any(
        k in lname for k in ("_bg", "glow", "dot_", "_line", "_accent", "_poly", "_arc")
    ):
        return True
    if w_cm <= 0.36 and h_cm <= 0.36:
        return True
    if min(w_cm, h_cm) <= 0.16:
        return True
    return False


def intersection_area(a: dict, b: dict) -> float:
    ix1 = max(a["x_cm"], b["x_cm"])
    iy1 = max(a["y_cm"], b["y_cm"])
    ix2 = min(a["right_cm"], b["right_cm"])
    iy2 = min(a["bottom_cm"], b["bottom_cm"])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return round((ix2 - ix1) * (iy2 - iy1), 3)


def is_intentional_container(outer: dict, inner: dict) -> bool:
    """
    Distinguish intentional visual container cards (e.g., col_1_card or sq_outer_app)
    that enclose inner children from genuine accidental sibling overlaps.
    """
    area_outer = max(0.01, outer["w_cm"] * outer["h_cm"])
    area_inner = max(0.01, inner["w_cm"] * inner["h_cm"])
    if area_outer <= area_inner * 1.15:
        return False
    inter = intersection_area(outer, inner)
    # If >= 85% of inner lies inside outer:
    if inter / area_inner >= 0.85:
        # Container either has no text (like col_1_card) or top-aligned header text above inner
        if not outer["text"].strip():
            return True
        if inner["y_cm"] >= outer["y_cm"] + 0.9:
            return True
    return False


def dump_slide_layout(pptx_path: str, slide_num: int, out_json: str = None) -> dict:
    pptx_path = os.path.abspath(pptx_path)
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX not found: {pptx_path}")

    prs = Presentation(pptx_path)
    if slide_num < 1 or slide_num > len(prs.slides):
        raise ValueError(f"Slide {slide_num} out of range (1..{len(prs.slides)})")

    canvas_w = emu_to_cm(prs.slide_width)
    canvas_h = emu_to_cm(prs.slide_height)
    slide = prs.slides[slide_num - 1]

    elements = []
    out_of_bounds = []
    overflow_risks = []

    for idx, shp in enumerate(slide.shapes, start=1):
        x_cm = emu_to_cm(shp.left)
        y_cm = emu_to_cm(shp.top)
        w_cm = emu_to_cm(shp.width)
        h_cm = emu_to_cm(shp.height)
        right_cm = round(x_cm + w_cm, 3)
        bottom_cm = round(y_cm + h_cm, 3)

        name = shp.name or f"shape_{idx}"
        raw_text = shp.text_frame.text if shp.has_text_frame else ""
        decorative = is_decorative_shape(name, w_cm, h_cm, raw_text)

        if shp.has_table:
            el_type = "table"
            cell_texts = []
            for r in shp.table.rows:
                row_t = [c.text.strip() for c in r.cells if c.text.strip()]
                if row_t:
                    cell_texts.append(" | ".join(row_t))
            text_val = "\n".join(cell_texts)
            font_pt = 11.5
            est_h = h_cm
            is_overflow = False
        else:
            el_type = "shape"
            text_val = shp.text_frame.text if shp.has_text_frame else ""
            font_pt = extract_shape_font_pt(shp, 12.5)
            est_h = estimate_text_height_cm(text_val, font_pt, w_cm) if text_val.strip() else 0.0
            is_overflow = bool(text_val.strip() and est_h > h_cm * 1.18 and not decorative)

        is_oob = False
        if not decorative:
            if x_cm < 0.5 or y_cm < 0.4 or right_cm > canvas_w - 0.4 or bottom_cm > canvas_h - 0.3:
                is_oob = True
                out_of_bounds.append(
                    {
                        "id": shp.shape_id,
                        "name": name,
                        "bounds_cm": [x_cm, y_cm, right_cm, bottom_cm],
                        "canvas_cm": [canvas_w, canvas_h],
                    }
                )

        if is_overflow:
            overflow_risks.append(
                {
                    "id": shp.shape_id,
                    "name": name,
                    "box_h_cm": h_cm,
                    "estimated_text_h_cm": est_h,
                    "font_size_pt": font_pt,
                    "text_preview": text_val[:60],
                }
            )

        el_info = {
            "index": idx,
            "id": shp.shape_id,
            "name": name,
            "type": el_type,
            "is_decorative": decorative,
            "x_cm": x_cm,
            "y_cm": y_cm,
            "w_cm": w_cm,
            "h_cm": h_cm,
            "right_cm": right_cm,
            "bottom_cm": bottom_cm,
            "font_size_pt": font_pt,
            "text": text_val,
            "estimated_text_h_cm": est_h,
            "overflow_risk": is_overflow,
            "out_of_bounds": is_oob,
        }
        elements.append(el_info)

    # Pairwise overlap check among non-decorative elements
    overlap_pairs = []
    non_dec = [e for e in elements if not e["is_decorative"]]
    for i in range(len(non_dec)):
        for j in range(i + 1, len(non_dec)):
            a, b = non_dec[i], non_dec[j]
            inter = intersection_area(a, b)
            if inter > 0.18:
                if is_intentional_container(a, b) or is_intentional_container(b, a):
                    continue
                overlap_pairs.append(
                    {
                        "element_a": a["name"],
                        "element_b": b["name"],
                        "intersection_cm2": inter,
                        "a_bounds": [a["x_cm"], a["y_cm"], a["right_cm"], a["bottom_cm"]],
                        "b_bounds": [b["x_cm"], b["y_cm"], b["right_cm"], b["bottom_cm"]],
                    }
                )

    # Background fill & text contrast check
    _A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    _P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

    def _rel_lum(hx: str) -> float:
        rgb = [int(hx[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    def _cr(h1: str, h2: str) -> float:
        l1, l2 = _rel_lum(h1), _rel_lum(h2)
        return round((max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 2)

    bg_hex = "FFFFFF"
    bg_pr = slide.background._element.find(f"{_P_NS}bg/{_P_NS}bgPr")
    if bg_pr is not None:
        srgb = bg_pr.find(f"{_A_NS}solidFill/{_A_NS}srgbClr")
        if srgb is not None and srgb.get("val"):
            bg_hex = srgb.get("val").upper()
        else:
            gs = bg_pr.find(f"{_A_NS}gradFill/{_A_NS}gsLst/{_A_NS}gs/{_A_NS}srgbClr")
            if gs is not None and gs.get("val"):
                bg_hex = gs.get("val").upper()

    contrast_issues = []
    for shp in slide.shapes:
        if shp.has_text_frame and shp.text_frame.text.strip():
            # Only check shapes without opaque solid fill against slide background
            sp_pr = getattr(shp._element, "spPr", None)
            has_own_fill = sp_pr is not None and sp_pr.find(f"{_A_NS}solidFill/{_A_NS}srgbClr") is not None
            if not has_own_fill:
                for p in shp.text_frame.paragraphs:
                    for r in p.runs:
                        if r.text.strip() and r.font.color and r.font.color.rgb:
                            fg_hex = str(r.font.color.rgb).upper()
                            ratio = _cr(bg_hex, fg_hex)
                            if ratio < 3.0:
                                contrast_issues.append({
                                    "name": shp.name or f"shape_{shp.shape_id}",
                                    "bg_hex": bg_hex,
                                    "fg_hex": fg_hex,
                                    "contrast_ratio": ratio,
                                    "text_preview": r.text[:40],
                                })
                            break
                    break

    status = "PASS" if (len(out_of_bounds) == 0 and len(overlap_pairs) == 0 and len(overflow_risks) == 0 and len(contrast_issues) == 0) else "WARN"

    if not out_json:
        project_dir = os.path.dirname(os.path.dirname(pptx_path))
        out_json = os.path.join(project_dir, "preview", f"slide_{slide_num}_layout.json")
    out_json = os.path.abspath(out_json)
    os.makedirs(os.path.dirname(out_json), exist_ok=True)

    report = {
        "status": status,
        "pptx_path": pptx_path,
        "slide_number": slide_num,
        "canvas_cm": {"width_cm": canvas_w, "height_cm": canvas_h},
        "summary": {
            "total_elements": len(elements),
            "content_elements": len(non_dec),
            "out_of_bounds_count": len(out_of_bounds),
            "overlap_count": len(overlap_pairs),
            "overflow_risk_count": len(overflow_risks),
            "contrast_issue_count": len(contrast_issues),
        },
        "issues": {
            "out_of_bounds": out_of_bounds,
            "overlap_pairs": overlap_pairs,
            "overflow_risks": overflow_risks,
            "contrast_issues": contrast_issues,
        },
        "elements": elements,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def main():
    parser = argparse.ArgumentParser(description="Dump raw PPTX slide layout coordinates and geometry check via Python.")
    parser.add_argument("--pptx", "-p", required=True, help="Path to build/deck.pptx")
    parser.add_argument("--slide", "-n", type=int, required=True, help="1-based slide number")
    parser.add_argument("--out", "-o", help="Output JSON path (defaults to <project>/preview/slide_N_layout.json)")
    args = parser.parse_args()

    rep = dump_slide_layout(args.pptx, args.slide, args.out)
    print(
        json.dumps(
            {
                "status": rep["status"],
                "slide_number": rep["slide_number"],
                "summary": rep["summary"],
                "issues": rep["issues"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
