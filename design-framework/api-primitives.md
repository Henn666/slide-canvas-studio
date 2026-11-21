# SlideCanvas API Reference: Primitives (`api-primitives.md`)

**單一職責**：收錄 `SlideCanvas` 的色彩筆畫簡寫、基礎幾何容器、自動排版文字與表格/圖片原語。

---

## 一、 CSS/SVG 樣式簡寫字串

- **語義色 Token**（對應 `set_palette()`）：`bg` (`bg_canvas`)、`surface` (`bg_surface`)、`ink` (`ink_primary`)、`muted` (`ink_muted`)、`border` (`border_grid`)、`accent` (`accent_primary`)、`accent2` (`accent_secondary`)。
- **填色 `fill`**：
  - `"none"`、`"#38BDF8"`、`"accent@0.12"`（語義色或 6 碼 HEX 接 `@透明度`）。
  - `"grad(135, accent@0.22, accent2@0.04)"`（線性漸層：`角度deg, 色站1, 色站2...`）。
- **邊框 `stroke`**：
  - `"none"`、`"border@0.45:1"`、`"accent2@0.7:1.8:dash"`（語法：`顏色[@透明度][:線寬pt][:solid|dash|dot|dashDot|6,4]`）。

---

## 二、 容器與基礎幾何圖元

> 所有形狀預設皆編譯為 100% 原生可編輯 OpenXML 物件；傳入可選參數 **`id="..."`** 可將元件外框登記進節點註冊表（供 `c.connect()` 自動連線使用）。

- **矩形 / 卡片**：
  `c.rect(x, y, w, h, rx=0, fill="surface", stroke="none", text="", size=15.0, color="ink", bold=False, align="center", valign="middle", pad_px=10.0, pad_v_px=None, name=None, id=None)`
- **膠囊標籤**：
  `c.pill(x, y, w, h, fill="accent@0.12", stroke="accent@0.38:1", text="", size=11.5, color="accent", bold=True, name=None, id=None)`
  - 膠囊高度建議 `26px–28px`，系統已將垂直內距歸零以確保嚴格垂直置中。
- **圓形 / 橢圓**：
  `c.circle(cx, cy, r, fill="accent", stroke="none", text="", size=13.0, color="ink", bold=False, name=None, id=None)`
  `c.ellipse(cx, cy, rx_px, ry_px, fill="accent", stroke="none", ... , id=None)`
- **背景環境光暈（裝飾層，不觸發重疊警示）**：
  `c.glow(cx, cy, r, color="accent@0.09", rings=2)`

---

## 三、 頁面標頭與排版原語

- **頁首與頁尾**：
  - `bottom_y = c.header(title, subtitle="", eyebrow="", x=68, y=42, w=1144)`
  - `c.footer(text="", slide_num=None, total_slides=None, line=True)`
- **自動測量高度文字框（推薦用於所有多行文字與標題）**：
  - `bottom_y = c.text_auto(x, y, w, text, size=15.0, color="ink", bold=False, align="left", font=None, role=None, line_height=1.38, pad_px=3.0, name=None)`
  - 內建呼叫 `text_measure.py` 執行 CJK/拉丁斷行與行高估算，並精準回傳**文字框底部 `bottom_y`**。
- **固定高度文字框（單行 KPI、置中數字）**：
  - `c.text(x, y, w, h, text, size=15.0, color="ink", bold=False, align="left", valign="top", role=None, pad_px=3.0)`
- **大數字統計指標（KPI Block）**：
  - `bottom_y = c.stat(x, y, w, value, label, val_size=46.0, lbl_size=13.5, val_color="accent", lbl_color="ink", align="left")`

---

## 四、 表格與外部圖片原語

- **簡約表格**：
  `c.table(x, y, w, h, headers, rows, highlight_cells=None, col_widths=None, header_fill="surface", header_color="ink", alt_fill="bg")`
  - `highlight_cells` 格式：`{(row_idx, col_idx): "#F59E0B"}` 標亮關鍵數據格。
- **嵌入外部圖片**（配合 `scripts/fit_visual_asset.py` 裁切好比例）：
  `c.image(path, x, y, w, h=None, name="image_asset")`
