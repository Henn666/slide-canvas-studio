# Workflow Phases & Decision Tree (`workflow-phases.md`)

**單一職責**：定義專案工作目錄、標準/快速流程切換與單頁驗證微調決策樹。

---

## 一、 專案工作目錄結構（由 `init_project.py` 建立）

- `source/`：大綱規劃 `brief.md` 與原始參考資料。
- `design/`：核心繪圖腳本 `build_deck.py`（呼叫 `SlideCanvas` 1280×720 API）。
- `assets/`：經 `fit_visual_asset.py` 校準後的外部圖片資產（若有）。
- `build/`：產出的 `deck.pptx`。
- `preview/`：單頁渲染圖 `slide_N.png` 與幾何報告 `slide_N_layout.json`。

---

## 二、 標準模式 vs. 快速模式（Quick Mode）

- **標準模式（預設）**：適用於正式簡報或 5 頁以上簡報 → `init_project` → `brief.md` → 撰寫 `design/build_deck.py` → `--all` 建置 → 雙重驗收（`dump_slide_layout` + `render_single_slide`）。
- **快速模式**：適用於 3 頁以內草稿或使用者已提供精確每頁文案 → 可跳過 `source/brief.md`，直接撰寫 `design/build_deck.py` 並執行雙重驗收。

---

## 三、 單頁驗收閉環與快速微調決策樹

建構完成後，執行 `dump_slide_layout.py --slide N` 與 `render_single_slide.py --slide N`：

| 檢測訊號 | 根因分類 | 修復動作 |
| :--- | :--- | :--- |
| `overflow_risk` 非空 | 文字框高小於行高估算 | 改用 `c.text_auto(...)`、加寬 `w` 或精簡文案，再執行 `python3 design/build_deck.py --slide N`（秒級重建該頁）。 |
| `overlap_pairs` 非空 | 兩個獨立語意元件相交 | 調整該函式內的 `y` 推算（串接 `bottom_y`）或調整 `cols(..., gap=...)`，重跑 `--slide N`。 |
| `out_of_bounds` 非空 | 元件侵入安全邊界外 | 收回 `x: 68..1212, y: 42..650` 範圍並重跑 `--slide N`。 |
| `slide_N.png` 視覺失衡或單調 | 全頁堆滿同質卡片或連頁構圖重複 | 依該頁語意切換視覺形式（如開放畫布去框留白、趨勢面積曲線、分支架構連線、對比表格或環狀圖），重跑 `--slide N`。 |
