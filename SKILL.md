---
name: slide-canvas-studio
description: Build high-craft, 100% natively editable PowerPoint (.pptx) presentations using the 1280x720 SVG-flavored Python SlideCanvas engine, CJK-aware text_measure wrapping, optional reference styles, selective visual slots, and deterministic Python EMU + PNG visual inspection. Use whenever creating, designing, or refining presentations or technical architecture decks.
---

# slide-canvas-studio (SVG 思維 Python Canvas 簡報引擎)

本 Skill 採用 **「1280×720 SVG 設計心智 ＋ 極簡 Python `SlideCanvas` 繪圖腳本直出原生 OpenXML ＋ Python EMU / PNG 雙重驗收」** 的高內聚架構：
- **零 YAML 模板、零座標心算瓶頸**：LLM 以熟悉的 `1280×720` SVG 設計師視角思考構圖比例、負空間與層次，直接使用 Python `for` 迴圈、`polar()`、`c.cols()`、`c.text_auto()`、貝茲曲線與 `#HEX@opacity` / `grad(...)` 簡寫語法直出原生可編輯 `.pptx`，兼具 SVG 美學上限與極低 Token 消耗。
- **最低限度護欄**：`styles/` 僅在**使用者明確指定風格時才載入**；否則由 LLM 依簡報主題自由設計色票與構圖重心，僅由 `SlideCanvas.set_palette()` 確保 WCAG ≥ 4.5:1 對比度與安全留白。

---

## 一、 核心防呆鐵律

1. **按需載入（On-Demand Loading）**：依目前階段僅讀取對應指南，避免無意義塞滿上下文。
2. **用 `text_auto()` 與 `cols()` / `polar()` 杜絕碰撞**：不靠心算估算文字行高與三欄寬度，垂直堆疊一律使用 `y = c.text_auto(...) + gap` 動態推進座標。
3. **100% 原生直出 + 單頁秒級迭代**：簡報腳本（`design/build_deck.py`）每頁寫為獨立函式 `def slide_N(c, total):`，需要微調第 `N` 頁時直接執行 `python3 design/build_deck.py --slide N` 局部重建。
4. **雙重驗收閉環**：建置完成後執行 `scripts/dump_slide_layout.py`（Python 原始 EMU 越界/重疊/溢框檢查）＋ `scripts/render_single_slide.py`（macOS QuickLook 單頁轉 PNG，並以讀圖實際視覺審計，最多收斂 2 輪）。

---

## 二、 階段流程與按需讀取索引

| 階段 | 核心任務 | 按需讀取檔案 | 執行腳本 |
| :--- | :--- | :--- | :--- |
| **Phase 0** | 初始化專案目錄與 `design/build_deck.py` | `design-framework/workflow-phases.md` | `python3 <skill>/scripts/init_project.py --project <dir>` |
| **Phase 1** | 濃縮敘事脈絡為 `source/brief.md` | `design-framework/content-density-rules.md` | （撰寫 `<project>/source/brief.md`） |
| **Phase 2** | 設計色票/版面並撰寫 `design/build_deck.py` | 1. **僅使用者指定時**：`styles/<style>/style.md`<br>2. `design-framework/color-and-type-constraints.md`<br>3. `design-framework/layout-and-grid-rules.md`<br>4. `design-framework/native-vs-visual-policy.md` | 若套用 `.pptx` 企業母片：<br>`inspect_template.py --pptx <path>` |
| **Phase 3** | 校準外部圖片（若有）+ 執行建置 `.pptx` | （無） | `fit_visual_asset.py`（選用）＋ `python3 <project>/design/build_deck.py --all` |
| **Phase 4** | EMU 幾何檢查 + PNG 視覺驗收 → 按需 `--slide N` 重繪 | `design-framework/critique-rubric.md` | `dump_slide_layout.py` + `render_single_slide.py` |

---

## 三、 Skill 目錄結構

- `design-framework/`：6 份極簡通用設計護欄（與 `SlideCanvas` 1280×720 API 參考）。
- `styles/`：參考風格目錄（**僅使用者明確指定時參考**）。
- `scripts/`：7 支單一職責腳本：
  - `slide_canvas.py`：核心 `1280×720` SVG 風格繪圖 API（OpenXML 直出、`#HEX@opacity`、`grad(...)`、`path()`、`curve()`、`donut()`、`text_auto()`）。
  - `text_measure.py`：CJK 混排禁則與行高估算引擎。
  - `dump_slide_layout.py` & `render_single_slide.py`：雙重驗收工具。
  - `init_project.py`、`fit_visual_asset.py`、`inspect_template.py`。
