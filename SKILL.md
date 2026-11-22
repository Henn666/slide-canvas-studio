---
name: slide-canvas-studio
description: Build high-craft, 100% natively editable PowerPoint (.pptx) presentations using the 1280x720 SVG-flavored Python SlideCanvas engine, CJK-aware text_measure wrapping, optional reference styles, selective visual slots, and deterministic Python EMU + PNG visual inspection. Use whenever creating, designing, or refining presentations or technical architecture decks.
---

# slide-canvas-studio (SVG 思維 Python Canvas 簡報引擎)

本 Skill 採用 **「1280×720 SVG 設計心智 ＋ 極簡 Python `SlideCanvas` 繪圖腳本直出原生 OpenXML ＋ Python EMU / PNG 雙重驗收」** 的高內聚架構：
- **零 YAML 模板、零座標心算瓶頸**：LLM 以熟悉的 `1280×720` SVG 設計師視角思考構圖比例、負空間與層次，直接使用 Python `for` 迴圈、`polar()`、`c.cols()`、`c.card()`、`c.text_auto()`、貝茲曲線與 Tailwind 設計 Token（`"sky-500/15"`、`#HEX@opacity`、`grad(...)`）直出原生可編輯 `.pptx`，兼具 SVG 美學上限與極低 Token 消耗。
- **最低限度護欄**：`styles/` 僅在**使用者明確指定風格時才載入**；否則由 LLM 於整份簡報開頭執行一次 **Step 0: Deck-Level Art Direction Synthesis** 宣告全局 `THEME = SlideTheme(...)`，並由 `SlideCanvas` 與 `TokenResolver.ensure_contrast()` 在繪圖當下自動把關 WCAG 對比度與安全留白。

---

## 一、 核心防呆鐵律

1. **Step 0 全局藝術指導（Deck-Level Art Direction Synthesis）**：每份簡報**開頭僅執行一次**，依主題領域與受眾宣告單一全局 `THEME = SlideTheme(...)`（參閱 `design-framework/color-and-type-constraints.md`）。**全份簡報嚴禁中途切換色票主題**；跨頁視覺變化應透過不對稱 `c.cols(..., weights=...)` 欄位權重、`c.card(variant=...)`（`"default"` / `"accent"` / `"subtle"` / `"dashed"`）與留白節奏來創造。
2. **按需載入（On-Demand Loading）**：依目前階段僅讀取對應指南，避免無意義塞滿上下文。
3. **用 `text_auto()`、`card()` 與 `cols()` / `polar()` 杜絕碰撞**：不靠心算估算文字行高與多欄寬度；垂直堆疊一律使用 `y = c.text_auto(...) + gap` 或 `inner = c.card(...)` 回傳的剩餘內框座標推進。
4. **100% 原生直出 + 單頁秒級迭代**：簡報腳本（`design/build_deck.py`）每頁寫為獨立函式 `def slide_N(c, total):`，需要微調第 `N` 頁時直接執行 `python3 design/build_deck.py --slide N` 局部重建。
5. **雙重驗收閉環**：建置完成後執行 `scripts/dump_slide_layout.py`（Python 原始 EMU 越界/重疊/溢框/對比度檢查）＋ `scripts/render_single_slide.py`（LibreOffice / macOS QuickLook 單頁轉 PNG，並以讀圖實際視覺審計，最多收斂 2 輪）。

---

## 二、 階段流程與按需讀取索引

| 階段 | 核心任務 | 按需讀取檔案 | 執行腳本 |
| :--- | :--- | :--- | :--- |
| **Step 0（Art Direction）** | 整份簡報**開頭僅執行一次**：依領域/受眾宣告全局 `THEME = SlideTheme(...)`（絕不中途換色）；跨頁以不對稱 `cols` 權重、`c.card(variant=...)` 與留白節奏創造變化 | `design-framework/color-and-type-constraints.md`（**僅使用者指定時才讀** `styles/<style>/style.md`） | 於 `<project>/design/build_deck.py` 頂層宣告全局 `THEME` |
| **Phase 0** | 初始化專案目錄與 `design/build_deck.py` | `design-framework/workflow-phases.md` | `python3 <skill>/scripts/init_project.py --project <dir>` |
| **Phase 1** | 濃縮敘事脈絡為 `source/brief.md` | `design-framework/content-density-rules.md` | （撰寫 `<project>/source/brief.md`） |
| **Phase 2** | 依 `THEME` 撰寫各頁版面與 `design/build_deck.py` | 1. **僅使用者指定時**：`styles/<style>/style.md`<br>2. `design-framework/color-and-type-constraints.md`<br>3. `design-framework/layout-and-grid-rules.md`<br>4. `design-framework/api-primitives.md`<br>5. **僅架構圖/向量圖表頁**：`design-framework/api-diagrams-and-connectors.md`<br>6. `design-framework/native-vs-visual-policy.md` | 若套用 `.pptx` 企業母片：<br>`inspect_template.py --pptx <path>` |
| **Phase 3** | 校準外部圖片（若有）+ 執行建置 `.pptx` | （無） | `fit_visual_asset.py`（選用）＋ `python3 <project>/design/build_deck.py --all` |
| **Phase 4** | EMU 幾何檢查 + PNG 視覺驗收 → 按需 `--slide N` 重繪 | `design-framework/critique-rubric.md` | `dump_slide_layout.py` + `render_single_slide.py` |

---

## 三、 Skill 目錄結構

- `design-framework/`：分類設計護欄與 `SlideCanvas` 按需 API 參考手冊（含基礎原語與架構連線指南）。
- `styles/`：參考風格目錄（**僅使用者明確指定時參考**）。
- `scripts/`：9 支單一職責腳本：
  - `tokens.py`：Tailwind 全光譜色票（22 色系 × 11 階）、字級/圓角/間距 Token、`SlideTheme`、`/NN` 預混色與繪圖期 WCAG `ensure_contrast()` 對比度引擎。
  - `vector_primitives.py`：1280×720 座標換算（`px`/`polar`/`lerp`）、節點註冊表、智慧連線（`connect()`）與自由向量原語（`line`/`arrow`/`polyline`/`bezier`/`curve`/`path`/`arc`/`donut`）。
  - `slide_canvas.py`：精簡核心編排器（繼承 `VectorPrimitivesMixin`，提供背景堆疊追蹤、`c.card()`、`c.rect()`、`c.pill()`、`c.text_auto()`、`c.stat()`、`c.table()`、`run_cli()`）。
  - `text_measure.py`：CJK 混排禁則與行高估算引擎。
  - `dump_slide_layout.py` & `render_single_slide.py`：雙重驗收工具（EMU 幾何/對比度檢查 + 單頁 PNG 渲染）。
  - `init_project.py`、`fit_visual_asset.py`、`inspect_template.py`：專案初始化、圖片比例裁切與企業母片解析。
