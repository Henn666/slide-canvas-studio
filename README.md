# slide-canvas-studio

An AI-agent skill for building **100% natively editable PowerPoint (`.pptx`) presentations** using a **1280×720 SVG-flavored Python `SlideCanvas` API** that compiles straight to OpenXML via `python-pptx`.

- **SVG Mental Model, Low Token Cost**: Express layouts with Python loops, `polar()`, `c.cols()`, `c.bezier()`, `c.curve()`, `c.donut()`, `#HEX@opacity`, and `grad(...)` with minimal token overhead.
- **Pure Python OpenXML Generation**: Compiles directly to 100% native, editable PowerPoint shapes via `python-pptx` with zero external CLI tools required.
- **CJK-Aware Typography (`text_measure.py`)**: Automatic Chinese/English line-wrapping, forbidden line-start/end punctuation rules, and `c.text_auto()` returning exact `bottom_y` so elements never collide.
- **Dual Verification Gate**:
  1. `dump_slide_layout.py`: Reads raw `.pptx` EMU geometry, detects out-of-bounds, unexpected overlaps, text overflow risks, and checks real `<p:bgPr>` background-to-text WCAG contrast.
  2. `render_single_slide.py`: Headless single-slide PNG rendering via LibreOffice + PyMuPDF (or macOS QuickLook fallback) for visual inspection.

---

## Installation

### 1. Clone into your Agent Skills directory
```bash
git clone https://github.com/<your-username>/slide-canvas-studio.git ~/.gemini/config/skills/slide-canvas-studio
cd ~/.gemini/config/skills/slide-canvas-studio
```

### 2. Create Python virtual environment & install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Optional Renderer (for PNG visual verification)
- **Cross-platform (Recommended)**: Install LibreOffice (`brew install --cask libreoffice` on macOS, or `sudo apt install libreoffice` on Linux).
- **macOS Fallback**: Built-in `qlmanage` works out of the box if LibreOffice is not installed.

---

## Quick Usage

```bash
# 1. Initialize a presentation project
python3 scripts/init_project.py --project ./my_deck

# 2. Edit ./my_deck/design/build_deck.py with SlideCanvas 1280x720 API, then build:
python3 ./my_deck/design/build_deck.py --all --out ./my_deck/build/deck.pptx

# 3. Verify geometry, contrast, and render slide PNGs:
python3 scripts/dump_slide_layout.py --pptx ./my_deck/build/deck.pptx --slide 1
python3 scripts/render_single_slide.py --pptx ./my_deck/build/deck.pptx --slide 1
```

---

## Directory Structure

```text
slide-canvas-studio/
├── SKILL.md                  # Agent skill entry point & workflow rules
├── README.md
├── LICENSE
├── requirements.txt          # Minimal: python-pptx, Pillow, pymupdf
├── design-framework/         # Guardrails & 1280x720 SlideCanvas API reference
├── styles/                   # Optional reference style profiles & sample .pptx template
└── scripts/
    ├── slide_canvas.py       # 1280x720 SVG-flavored OpenXML canvas engine
    ├── text_measure.py       # CJK + Latin wrapping & height estimator
    ├── dump_slide_layout.py  # Raw EMU bounds, overlap, overflow & contrast checker
    ├── render_single_slide.py# LibreOffice / QuickLook single-slide PNG renderer
    ├── init_project.py       # Project scaffolder
    ├── fit_visual_asset.py   # Aspect-ratio image cropper/resizer
    └── inspect_template.py   # Corporate .pptx master layout inspector
```
