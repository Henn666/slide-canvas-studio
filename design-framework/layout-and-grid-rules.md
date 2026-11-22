# Layout & Grid Rules (`layout-and-grid-rules.md`)

**單一職責**：定義 1280×720 邏輯畫布安全邊界、空間切分網格器（`cols` / `rows` / `grid`）與視覺呼吸留白美學。

> **分類 API 導引（按需讀取）**：
> - 色彩簡寫、基礎形狀、文字與表格原語 → [api-primitives.md](file:///Users/user/.gemini/config/skills/slide-canvas-studio/design-framework/api-primitives.md)
> - 系統架構圖、`id` 節點註冊、`c.connect()` 自動連線與曲線/圓環圖表 → [api-diagrams-and-connectors.md](file:///Users/user/.gemini/config/skills/slide-canvas-studio/design-framework/api-diagrams-and-connectors.md)

---

## 一、 1280×720 邏輯畫布與安全邊界（1 px = 9525 EMU）

- **標準 16:9 畫布**：寬 `1280 px`（`33.867 cm`），高 `720 px`（`19.05 cm`）。
- **四邊安全留白邊界（Safe Margins）**：
  - 左右內容區：`x = 68 .. 1212`（可用寬度 `1144 px`）。
  - 頂部標題區（`c.header(...)`）：`y = 42` 起始（含眉標、結論大標、副標），`header()` 會回傳下方可用起點 `y`（約 `166`）。
  - 主內容自由畫布區：`y = 166 .. 640`（無標題時 `y = 52 .. 640`）。
  - 底部頁尾區（`c.footer(...)`）：細線 `y = 656`，頁碼文字 `y = 660`。
- **呼吸留白**：每頁至少保留 **30%～35% 負空間**，禁止滿版填滿邊框。

---

## 二、 空間網格切分器（Deterministic Grid Helpers）

撰寫版面時，**一律透過輔助器切分區域座標**，禁止自行心算多欄寬度與間距：

- `c.cols(n, x=68, y=166, w=1144, h=460, gap=24, weights=None)` → 回傳 `[(x, y, w, h), ...]`
  - 例：`col_l, col_r = c.cols(2, gap=28, weights=[1.15, 0.85])`
- `c.rows(n, x=68, y=166, w=1144, h=460, gap=20, weights=None)` → 回傳 `[(x, y, w, h), ...]`
  - 支援嵌套進某一欄內部：`r_top, r_bot = c.rows(2, x=rx, y=ry, w=rw, h=rh, gap=20)`
- `c.grid(cols_n, rows_n, x=68, y=166, w=1144, h=460, gap_x=24, gap_y=20)` → 一次產生規則 Bento 矩陣。

---

## 三、 去框美學與排版紀律

- **用動態 `bottom_y` 堆疊文字**：卡片內部元素垂直堆疊一律寫為 `yt = c.text_auto(...)` → `c.text_auto(..., yt + gap, ...)`，不寫死 Y 座標，確保內容長短變化時絕不重疊或溢框。
- **極簡輕薄邊框（Subtle Glass）**：避免高飽和厚重實線框（Neo-Brutalism 風格除外）；容器優先採低透明度填充（`@0.06 ~ @0.12`）與淡邊線（`@0.25 ~ @0.45:0.75`），或直接去框以字級與細線區隔。
- **語意驅動構圖選型（Form Follows Meaning）**：依該頁真正想傳達的語意選擇最適合的視覺形式，並避免相鄰兩頁重複完全相同的構圖：
  - **比較／矩陣** → `c.table()` 或 Bento `c.grid()`
  - **趨勢／消長** → `c.curve()` 平滑折線或填色面積圖（Filled Spline Area）
  - **流程／因果／分支** → `id=` + `c.connect()`（`ortho` / `bezier`）
  - **週期／佔比** → `c.donut()` / `polar()`
  - **核心洞察／強結論** → 開放畫布巨型 KPI（`c.stat()`）搭配細線與負空間，無需強加矩形外框
