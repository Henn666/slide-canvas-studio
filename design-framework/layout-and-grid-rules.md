# Layout, Grid & 1280×720 `SlideCanvas` API (`layout-and-grid-rules.md`)

**單一職責**：定義 1280×720 邏輯畫布安全邊界，以及 SVG 風格 Python 繪圖引擎 `scripts/slide_canvas.py` 的設計語彙，讓 LLM 直接用程式控制流、迴圈、三角函數與 CSS/SVG 簡寫創作 100% 原生簡報。

---

## 一、 1280×720 邏輯畫布與安全邊界（1 px = 9525 EMU）

- **標準 16:9 畫布**：寬 `1280 px`（`33.867 cm`），高 `720 px`（`19.05 cm`）。
- **四邊安全留白邊界（Safe Margins）**：
  - 左右內容區：`x = 68 .. 1212`（可用寬度 `1144 px`）。
  - 頂部標題區（`c.header(...)`）：`y = 42` 起始（含眉標、結論大標、副標），`header()` 會自動回傳下方可用起點 `y`（約 `166`）。
  - 主內容自由畫布區：`y = 166 .. 640`（無標題時 `y = 52 .. 640`）。
  - 底部頁尾區（`c.footer(...)`）：細線 `y = 656`，頁碼文字 `y = 660`。
- **呼吸留白**：每頁至少保留 **30%～35% 負空間**，禁止滿版填滿邊框。

---

## 二、 SVG 設計心智 × Python `SlideCanvas` API 速查

撰寫 `design/build_deck.py` 時，直接以 **1280×720 SVG 平面設計師的圖層思維**思考（背景微光暈層 → 裝飾引導曲線層 → 無框數據與視覺隱喻層），呼叫以下極簡語彙：

### 1. CSS/SVG 顏色與筆畫簡寫字串
- **填色 `fill`**：`"none"`、`"#38BDF8"`、`"accent@0.12"`（語義色或 6 碼 HEX 接 `@透明度`）、`"grad(135, accent@0.22, accent2@0.04)"`（單行多站點線性漸層）。
- **邊框 `stroke`**：`"none"`、`"border@0.45:1"`、`"accent2@0.7:1.8:dash"`（`顏色[@透明度][:線寬pt][:solid|dash|dot|dashDot|6,4]`）。
- **常用語義色簡寫**：`bg` (`bg_canvas`)、`surface` (`bg_surface`)、`ink` (`ink_primary`)、`muted` (`ink_muted`)、`border` (`border_grid`)、`accent` (`accent_primary`)、`accent2` (`accent_secondary`)。

### 2. 核心繪圖與排版原語
- **自動排版輔助器**：
  - `bottom_y = c.text_auto(x, y, w, text, size=15, color="ink", bold=False, align="left", role="body")`: 呼叫 `text_measure.py` 實測行高並建立文字框，**回傳實際底緣 `bottom_y`**。
  - `c.cols(n, x=68, y=166, w=1144, h=460, gap=24, weights=None)` / `c.rows(...)` / `c.grid(cols, rows, ...)`: 確定性切分等分或權重區塊 `(x, y, w, h)`。
  - `polar(cx, cy, r, deg)` / `lerp(a, b, t)`: 精準計算環狀、極座標或時間軸分佈點。
- **向量圖元**：
  - `c.rect(x, y, w, h, rx=0, fill="surface", stroke="none", text="", size=15, color="ink", bold=False, align="center", valign="middle")`
  - `c.pill(x, y, w, h, fill="accent@0.12", stroke="accent@0.38:1", text="", size=11.5, color="accent")`
  - `c.circle(cx, cy, r, fill=..., stroke=..., text="", size=13)` / `c.ellipse(cx, cy, rx_px, ry_px, ...)`
  - `c.glow(cx, cy, r, color="accent@0.09", rings=2)`（純背景環境光暈，不參與重疊檢查）
  - `c.line(x1, y1, x2, y2, stroke="border:1")` / `c.arrow(x1, y1, x2, y2, stroke="accent:2", head_size=9)`
  - `c.polyline(points, stroke=..., fill=..., closed=False)`
  - `c.bezier(p0, p1, p2, p3, stroke=..., fill="none")` / `c.curve(points, stroke=..., closed=False)`
  - `c.path(d, x=0, y=0, scale=1.0, stroke=..., fill="none")`（支援 SVG `M/L/H/V/C/S/Q/Z` 路徑語法）
  - `c.arc(cx, cy, r, start_deg=0, end_deg=270, stroke=...)` / `c.donut(cx, cy, r, start_deg=-90, end_deg=180, thickness=0.24, fill=...)`
  - `c.stat(x, y, w, value, label, val_size=46, lbl_size=13.5, val_color="accent")`
  - `c.table(x, y, w, h, headers, rows, highlight_cells=None, col_widths=None)`
  - `c.image(path, x, y, w, h=None)`

---

## 三、 美學自由度與去框紀律

- **用迴圈與曲線取代重複矩形**：數據長條圖、時間軸、環形架構與座標刻度，應直接使用 Python `for` 迴圈搭配 `polar()` / `curve()` / `donut()` 繪製，徹底擺脫單調卡片模板。
- **極簡輕薄邊框（Subtle Glass）**：避免高飽和厚重實線框；容器優先採低透明度填充（`@0.06 ~ @0.12`）與淡邊線（`@0.25 ~ @0.45:0.75`），或直接去框以字級與細線區隔。
