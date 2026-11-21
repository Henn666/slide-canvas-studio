#!/usr/bin/env python3
"""
fit_visual_asset.py
單一職責：使用 Pillow 將外部視覺圖依槽位尺寸 (w_cm, h_cm) 裁切 (cover) 或留白填充 (contain) 至精準比例，杜絕圖片進入 PPTX 後變形。
"""
import os
import sys

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_VENV_PY = os.path.join(_SKILL_ROOT, ".venv", "bin", "python")
if os.path.exists(_VENV_PY) and os.path.abspath(sys.prefix) != os.path.abspath(os.path.join(_SKILL_ROOT, ".venv")):
    os.execv(_VENV_PY, [_VENV_PY] + sys.argv)

import argparse
import json
from PIL import Image, ImageOps


def hex_to_rgb(hex_str: str):
    h = hex_str.strip().lstrip("#")
    if len(h) != 6:
        return (13, 33, 55)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def fit_visual(
    src_path: str,
    out_path: str,
    w_cm: float = 16.0,
    h_cm: float = 9.0,
    mode: str = "cover",
    bg_hex: str = "0D2137",
    px_per_cm: int = 60,
) -> dict:
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source image not found: {src_path}")

    target_w = max(64, int(round(w_cm * px_per_cm)))
    target_h = max(64, int(round(h_cm * px_per_cm)))

    img = Image.open(src_path).convert("RGBA")
    orig_w, orig_h = img.size

    if mode == "cover":
        fitted = ImageOps.fit(img, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    else:
        bg_rgb = hex_to_rgb(bg_hex) + (255,)
        canvas = Image.new("RGBA", (target_w, target_h), bg_rgb)
        contained = ImageOps.contain(img, (target_w, target_h), method=Image.Resampling.LANCZOS)
        offset_x = (target_w - contained.size[0]) // 2
        offset_y = (target_h - contained.size[1]) // 2
        canvas.paste(contained, (offset_x, offset_y), contained)
        fitted = canvas

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fitted.convert("RGB").save(out_path, format="PNG", optimize=True)

    return {
        "status": "OK",
        "src_path": os.path.abspath(src_path),
        "out_path": os.path.abspath(out_path),
        "mode": mode,
        "original_px": [orig_w, orig_h],
        "target_cm": [w_cm, h_cm],
        "output_px": [target_w, target_h],
    }


def main():
    parser = argparse.ArgumentParser(description="Crop or pad a visual asset to exact PPTX slot proportions.")
    parser.add_argument("--src", required=True, help="Input image path")
    parser.add_argument("--out", required=True, help="Calibrated output PNG path")
    parser.add_argument("--w-cm", type=float, default=16.0, help="Slot width in cm (default: 16.0)")
    parser.add_argument("--h-cm", type=float, default=9.0, help="Slot height in cm (default: 9.0)")
    parser.add_argument("--mode", choices=["cover", "contain"], default="cover", help="Resize mode")
    parser.add_argument("--bg", default="0D2137", help="Background fill HEX when mode=contain")
    args = parser.parse_args()

    res = fit_visual(args.src, args.out, args.w_cm, args.h_cm, args.mode, args.bg)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
