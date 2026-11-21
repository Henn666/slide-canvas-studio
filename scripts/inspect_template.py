#!/usr/bin/env python3
"""
inspect_template.py
單一職責：以 Python (python-pptx) 直接解析指定 .pptx 模板的畫布尺寸、母片 (Slide Masters)、版面名稱 (Layouts) 與佔位符清單 (Placeholders)。
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

EMU_PER_CM = 360000.0


def emu_to_cm(val):
    if val is None:
        return None
    return round(float(val) / EMU_PER_CM, 3)


def inspect_pptx(pptx_path: str) -> dict:
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"Template file not found: {pptx_path}")

    prs = Presentation(pptx_path)
    width_cm = emu_to_cm(prs.slide_width)
    height_cm = emu_to_cm(prs.slide_height)

    masters_info = []
    for m_idx, master in enumerate(prs.slide_masters):
        layouts = []
        for l_idx, layout in enumerate(master.slide_layouts):
            phs = []
            for ph in layout.placeholders:
                phs.append(
                    {
                        "idx": ph.placeholder_format.idx,
                        "type": str(ph.placeholder_format.type),
                        "name": ph.name,
                        "x_cm": emu_to_cm(ph.left),
                        "y_cm": emu_to_cm(ph.top),
                        "w_cm": emu_to_cm(ph.width),
                        "h_cm": emu_to_cm(ph.height),
                    }
                )
            layouts.append(
                {
                    "layout_index": l_idx,
                    "name": layout.name,
                    "placeholder_count": len(phs),
                    "placeholders": phs,
                }
            )
        masters_info.append(
            {
                "master_index": m_idx,
                "layout_count": len(layouts),
                "layouts": layouts,
            }
        )

    existing_slides = []
    for s_idx, slide in enumerate(prs.slides, start=1):
        existing_slides.append(
            {
                "slide_number": s_idx,
                "layout_name": slide.slide_layout.name if slide.slide_layout else None,
                "shape_count": len(slide.shapes),
            }
        )

    return {
        "template_path": os.path.abspath(pptx_path),
        "canvas": {
            "width_cm": width_cm,
            "height_cm": height_cm,
            "is_16_9": abs(width_cm / height_cm - 16.0 / 9.0) < 0.05 if (width_cm and height_cm) else False,
        },
        "master_count": len(masters_info),
        "masters": masters_info,
        "existing_slide_count": len(existing_slides),
        "existing_slides": existing_slides,
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect a PowerPoint (.pptx) template structure.")
    parser.add_argument("--pptx", required=True, help="Path to the .pptx template")
    parser.add_argument("--out", "-o", help="Optional JSON output file path")
    args = parser.parse_args()

    info = inspect_pptx(args.pptx)
    text = json.dumps(info, indent=2, ensure_ascii=False)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
