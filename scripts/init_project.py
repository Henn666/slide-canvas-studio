#!/usr/bin/env python3
"""
init_project.py
單一職責：建立目標簡報專案 5 大工作目錄 (source/, design/, assets/, build/, preview/) 與極簡 SlideCanvas 腳本起手式 design/build_deck.py。
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import json
from datetime import datetime


def init_project(project_dir: str, style_name: str = "custom", force: bool = False) -> dict:
    project_dir = os.path.abspath(project_dir)
    subdirs = [
        "source",
        "design",
        "assets",
        "build",
        "preview",
    ]
    for sub in subdirs:
        os.makedirs(os.path.join(project_dir, sub), exist_ok=True)

    script_dst = os.path.join(project_dir, "design", "build_deck.py")
    created_script = False
    if not os.path.exists(script_dst) or force:
        starter_code = f'''#!/usr/bin/env python3
"""Deck Builder using 1280x720 SVG-Flavored SlideCanvas API."""
import os
import sys

SKILL_SCRIPTS = "{os.path.join(_SKILL_ROOT, 'scripts')}"
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from slide_canvas import SlideCanvas, polar, lerp, run_cli

PALETTE = {{
    "bg_canvas": "F5F5F7",
    "bg_surface": "FFFFFF",
    "ink_primary": "1D1D1F",
    "ink_muted": "6E6E73",
    "border_grid": "D1D1D6",
    "accent_primary": "0071E3",
    "accent_secondary": "3A7D74",
}}

TYPOGRAPHY = {{
    "font_heading": "PingFang TC",
    "font_body": "PingFang TC",
    "font_mono": "Menlo",
}}


def slide_1(c: SlideCanvas, total: int):
    c.text_auto(68, 220, 1144, "Presentation Title", size=40, bold=True, role="heading")
    c.footer("Title Slide", slide_num=1, total_slides=total)


SLIDES = [slide_1]

if __name__ == "__main__":
    default_out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "deck.pptx")
    run_cli(SLIDES, palette=PALETTE, typography=TYPOGRAPHY, default_out=default_out)
'''
        with open(script_dst, "w", encoding="utf-8") as f:
            f.write(starter_code)
        created_script = True

    brief_dst = os.path.join(project_dir, "source", "brief.md")
    created_brief = False
    if not os.path.exists(brief_dst) or force:
        with open(brief_dst, "w", encoding="utf-8") as f:
            f.write(
                f"# Presentation Content Brief\n"
                f"- Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"- Style Mode: `{style_name}` (freeform creative unless specified)\n\n"
                f"## Slide-by-Slide Narrative Plan\n\n"
                f"### Slide 1\n"
                f"- **Key Conclusion**: [Core thesis of the deck]\n"
                f"- **Visual Metaphor**: [SVG/Canvas composition concept]\n"
            )
        created_brief = True

    return {
        "status": "OK",
        "project_dir": project_dir,
        "directories_created": subdirs,
        "build_script": script_dst,
        "created_script": created_script,
        "brief_path": brief_dst,
        "created_brief": created_brief,
    }


def main():
    parser = argparse.ArgumentParser(description="Initialize a slide-canvas-studio presentation project.")
    parser.add_argument("--project", "-p", required=True, help="Target project directory path")
    parser.add_argument("--style", "-s", default="custom", help="Optional reference style profile (default: custom freeform)")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing build_deck.py and brief.md")
    args = parser.parse_args()
    print(json.dumps(init_project(args.project, args.style, args.force), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
