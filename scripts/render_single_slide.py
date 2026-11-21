#!/usr/bin/env python3
"""
render_single_slide.py
單一職責：固定使用無頭 LibreOffice (soffice --headless --convert-to pdf) 將 .pptx 轉為暫存 PDF，
再由 PyMuPDF (fitz) 僅切出指定單頁 (--slide N) 的高解析度 PNG 至 preview/slide_N.png。
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import json
import shutil
import subprocess
import tempfile
import fitz  # PyMuPDF


def find_soffice():
    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        os.path.expanduser("~/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def render_with_qlmanage(pptx_path: str, slide_num: int, out_png: str) -> dict:
    import pptx
    from PIL import Image

    prs = pptx.Presentation(pptx_path)
    total_pages = len(prs.slides)
    if slide_num < 1 or slide_num > total_pages:
        raise ValueError(f"Slide {slide_num} out of range (total {total_pages} slides)")

    with tempfile.TemporaryDirectory(prefix="deck_ql_") as tmp_dir:
        tmp_pptx = os.path.join(tmp_dir, f"slide_{slide_num}.pptx")
        target = slide_num - 1
        for i in range(len(prs.slides) - 1, target, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
        for i in range(target - 1, -1, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
        prs.save(tmp_pptx)

        cmd = ["qlmanage", "-t", "-s", "1920", "-o", tmp_dir, tmp_pptx]
        res = subprocess.run(cmd, capture_output=True, text=True)
        gen_png = os.path.join(tmp_dir, f"slide_{slide_num}.pptx.png")
        if not os.path.exists(gen_png):
            raise RuntimeError(f"qlmanage failed to produce thumbnail:\n{res.stderr or res.stdout}")

        os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
        shutil.copy2(gen_png, out_png)
        with Image.open(out_png) as im:
            w_px, h_px = im.size

        return {
            "status": "OK",
            "engine": "macOS QuickLook (qlmanage)",
            "pptx_path": pptx_path,
            "slide_number": slide_num,
            "total_slides": total_pages,
            "out_png": out_png,
            "dimensions": f"{w_px}x{h_px}",
        }


def render_single_slide(pptx_path: str, slide_num: int, out_png: str = None, dpi: int = 192) -> dict:
    pptx_path = os.path.abspath(pptx_path)
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

    if not out_png:
        project_dir = os.path.dirname(os.path.dirname(pptx_path))
        out_png = os.path.join(project_dir, "preview", f"slide_{slide_num}.png")
    out_png = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)

    soffice_bin = find_soffice()
    if not soffice_bin:
        if shutil.which("qlmanage"):
            return render_with_qlmanage(pptx_path, slide_num, out_png)
        raise FileNotFoundError(
            "Neither LibreOffice (soffice) nor macOS QuickLook (qlmanage) found. "
            "Please install LibreOffice: brew install --cask libreoffice"
        )

    with tempfile.TemporaryDirectory(prefix="deck_lo_") as tmp_dir:
        user_profile = os.path.join(tmp_dir, "lo_profile")
        cmd = [
            soffice_bin,
            f"-env:UserInstallation=file://{user_profile}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            tmp_dir,
            pptx_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            raise RuntimeError(f"LibreOffice PDF conversion failed:\n{res.stderr or res.stdout}")

        base_name = os.path.splitext(os.path.basename(pptx_path))[0] + ".pdf"
        pdf_path = os.path.join(tmp_dir, base_name)
        if not os.path.exists(pdf_path):
            pdfs = [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.endswith(".pdf")]
            if not pdfs:
                raise RuntimeError(f"LibreOffice did not produce a PDF in {tmp_dir}")
            pdf_path = pdfs[0]

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        if slide_num < 1 or slide_num > total_pages:
            doc.close()
            raise ValueError(f"Slide {slide_num} out of range (PDF has {total_pages} pages)")

        page = doc[slide_num - 1]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(out_png)
        width_px, height_px = pix.width, pix.height
        doc.close()

    return {
        "status": "OK",
        "engine": "LibreOffice + PyMuPDF",
        "pptx_path": pptx_path,
        "slide_number": slide_num,
        "total_slides": total_pages,
        "out_png": out_png,
        "resolution_px": [width_px, height_px],
    }


def main():
    parser = argparse.ArgumentParser(description="Render a single PPTX slide to PNG via headless LibreOffice + PyMuPDF.")
    parser.add_argument("--pptx", "-p", required=True, help="Path to build/deck.pptx")
    parser.add_argument("--slide", "-n", type=int, required=True, help="1-based slide number to render")
    parser.add_argument("--out", "-o", help="Output PNG path (defaults to <project>/preview/slide_N.png)")
    parser.add_argument("--dpi", type=int, default=192, help="Render DPI (default: 192 for crisp 16:9 inspection)")
    args = parser.parse_args()

    res = render_single_slide(args.pptx, args.slide, args.out, args.dpi)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
