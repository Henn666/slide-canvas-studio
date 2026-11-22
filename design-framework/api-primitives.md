# SlideCanvas API Reference: Primitives (`api-primitives.md`)

**單一職責**：收錄 `SlideTheme` 主題定義、Tailwind 設計 Token 簡寫對照表、`c.card()` 容器原語、基礎幾何形狀、自動排版文字與表格/圖片原語。

---

## 一、 全局主題設定：`SlideTheme`

在整份簡報開頭（**Step 0**）宣告單一全局 `THEME`，傳入 `run_cli(..., theme=THEME)` 或 `SlideCanvas(theme=THEME)`（亦相容 `palette=THEME`）：

```python
from slide_canvas import SlideCanvas, SlideTheme, run_cli

THEME = SlideTheme(
    name="Bio-Tech",
    canvas="teal-950",         # 預設 "slate-950"
    surface_1="teal-900/70",   # 預設 "slate-900"（支援 /NN 對 canvas 預混色）
    surface_2="emerald-900/60",# 預設 "slate-800"
    border="teal-700/50",      # 預設 "slate-800"
    text_primary="teal-50",    # 預設 "slate-50"（>= 7.0:1 自動把關）
    text_muted="teal-300",     # 預設 "slate-400"（>= 4.5:1 自動把關）
    accent="lime-400",         # 預設 "sky-400"（>= 3.5:1 自動把關）
    accent2="emerald-400",     # 預設 "emerald-400"
    radius="rounded-2xl",      # 預設 "rounded-xl"（c.card 預設圓角）
    border_pt=0.75,            # 預設 0.75 pt（default card 邊框寬度）
    font_heading="PingFang TC",# 預設 "PingFang TC"
    font_body="PingFang TC",   # 預設 "PingFang TC"
    font_mono="Menlo",         # 預設 "Menlo"
)
```

`SlideTheme.to_palette_dict()` 會自動編譯並對齊語義別名：`bg`/`bg_canvas`/`canvas`、`surface`/`bg_surface`/`surface_1`、`surface2`/`surface_2`、`ink`/`ink_primary`/`text_primary`、`muted`/`ink_muted`/`text_muted`、`border`/`border_grid`、`accent`/`accent_primary`、`accent2`/`accent_secondary`。

---

## 二、 Tailwind 簡寫 Token 對照表（`tokens.py`）

### 1. 色彩與透明度（`fill` / `stroke` / `color`）
- **支援色表**：全部 22 個 Tailwind 色系 × `{50..950}`（如 `"sky-400"`、`"teal-950"`）、`"white"`、`"black"`、`"none"`/`"transparent"`、語義色（`bg`、`surface`、`surface2`、`ink`、`muted`、`border`、`accent`、`accent2`）或 `#RRGGBB`。
- **透明度規範**：
  - `/NN` **預混色（預設優先）**：如 `"sky-500/15"`、`"accent/10"`，依局部背景預混為純色 HEX。
  - `@0.NN` **真 OpenXML Alpha（僅用於光暈/圖片上方）**：如 `"slate-950@0.75"`、`"accent@0.12"`。
- **漸層與筆畫**：
  - `fill="grad(135, accent@0.22, accent2@0.04)"`（線性漸層：`角度deg, 色站1, 色站2...`）。
  - `stroke="border/60:1"` 或 `"accent2@0.7:1.8:dash"`（語法：`顏色[/pct][@alpha][:線寬pt][:solid|dash|dot|dashDot|lgDash]`）。

### 2. 字級階梯（`TYPOGRAPHY_SCALE`，單位為 PowerPoint `pt`，絕不經 `px()` 換算）
| Token | `pt` 大小 | 預設 `line_height` | Token | `pt` 大小 | 預設 `line_height` |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `"text-xs"` | `10.0 pt` | `1.20` | `"text-xl"` | `20.0 pt` | `1.20` |
| `"text-sm"` | `12.0 pt` | `1.40` | `"text-2xl"` | `24.0 pt` | `1.15` |
| `"text-base"` | `14.0 pt` | `1.32` | `"text-3xl"` | `29.0 pt` | `1.12` |
| `"text-lg"` | `16.5 pt` | `1.25` | `"text-4xl"` | `36.0 pt` | `1.08` |
| — | — | — | `"text-5xl"` | `44.0 pt` | `1.05` |

> 所有文字與容器原語的 `size` / `title_size` / `body_size` / `val_size` / `lbl_size` 皆同時接受上述 Token 字串或數值 `pt`（如 `15.0`）。

### 3. 圓角與間距（`1280×720 px` 畫布空間）
- **圓角 `RADIUS_PX`**（可用於 `rx` 與 `SlideTheme.radius`）：
  `"rounded-none"` (`0.0 px`)、`"rounded-sm"` (`4.0 px`)、`"rounded-md"` (`7.0 px`)、`"rounded-lg"` (`10.0 px`)、`"rounded-xl"` (`12.0 px`)、`"rounded-2xl"` (`18.0 px`)、`"rounded-3xl"` (`24.0 px`)、`"rounded-full"` (`999.0 px`)。
- **間距 `resolve_spacing()`**（**1 單位 = 4 px**，可用於 `cols`/`rows`/`grid` 的 `gap` 與 `card` 的 `padding`）：
  - `gap-2` (`8 px`)、`gap-3` (`12 px`)、`gap-4` (`16 px`)、`gap-5` (`20 px`)、`gap-6` (`24 px`)、`gap-8` (`32 px`)
  - `p-3` (`12 px`)、`p-4` (`16 px`)、`p-5` (`20 px`)、`p-6` (`24 px`)、`p-8` (`32 px`)（亦支援 `px-*` / `py-*` / `m-*` 或純數值 `px`）。

---

## 三、 主題化卡片原語：`c.card(...) -> inner_box`

`c.card()` 會依區域真實背景自動預混樣式、套用 `SlideTheme.radius`、選用渲染 `kicker` / `title` / `body`，並回傳剩餘內部安全範圍 `inner_box = (ix, iy, iw, ih)`：

```python
inner_box = c.card(
    box: Tuple[float, float, float, float],
    variant: str = "default",        # "default" | "accent" | "subtle" | "dashed"
    rx: Union[float, str, None] = None,
    padding: Union[float, str] = "p-5",
    fill: Any = None,
    stroke: Any = None,
    kicker: str = "",
    kicker_color: str = "accent",
    title: str = "",
    title_size: Union[float, str] = "text-lg",
    title_color: str = "ink",
    body: str = "",
    body_size: Union[float, str] = "text-sm",
    body_color: str = "muted",
    id: Optional[str] = None,        # 支援 Node Registry，可直接傳給 c.connect()
    name: Optional[str] = None,
) -> Tuple[float, float, float, float]
```

- **4 種內建變體（`CARD_VARIANTS`）**：
  - `"default"`：`fill="surface"`、`stroke="border"`、線寬繼承 `theme.border_pt`（預設 `0.75 pt`）。
  - `"accent"`：`fill="accent/10"`、`stroke="accent/45"`、線寬 `1.25 pt`。
  - `"subtle"`：`fill="surface2/50"`、`stroke="border/50"`、線寬 `0.5 pt`。
  - `"dashed"`：`fill="none"`、`stroke="border"`、線寬 `1.0 pt` 虛線（`dash`）。

### 範例 1：單行精簡卡片（Compact Card）
```python
col_l, col_r = c.cols(2, gap="gap-6", weights=[1.2, 0.8])
c.card(col_r, variant="accent", kicker="UPTIME SLA", title="99.98%", body="Zero unplanned downtime across all edge clusters.")
```

### 範例 2：開放式容器組合（`inner_box` Open-Container Pattern）
```python
ix, iy, iw, ih = c.card(col_l, variant="default", padding="p-6", kicker="PIPELINE", title="Live Telemetry")
y_next = c.stat(ix, iy + 8, iw, "1.8 ms", "Token Resolve Latency", val_size="text-5xl", lbl_size="text-sm")
c.pill(ix, y_next + 14, 150, 26, fill="accent/15", stroke="accent/45:1", text="WCAG VERIFIED", size="text-xs")
```

---

## 四、 基礎幾何圖元與繪圖期對比度護欄

> 所有形狀預設皆編譯為 100% 原生可編輯 OpenXML 物件；傳入 **`id="..."`** 可登記進節點註冊表（供 `c.connect()` 自動連線）。繪製含文字形狀時，`_set_text()` 會自動呼叫 `TokenResolver.ensure_contrast()` 確保文字對比度（一般文字 `>= 4.5:1`，`>= 24 pt` 大字 `>= 3.0:1`）。

- **矩形**：
  `c.rect(x, y, w, h, rx=0, fill="surface", stroke="none", text="", size=15.0, color="ink", bold=False, align="center", valign="middle", font=None, role=None, pad_px=10.0, pad_v_px=None, name=None, id=None)`
- **膠囊標籤**：
  `c.pill(x, y, w, h, fill="accent@0.12", stroke="accent@0.38:1", text="", size=11.5, color="accent", bold=True, font=None, role=None, name=None, id=None)`
  - 膠囊高度建議 `26px–28px`，系統已將垂直內距歸零以確保嚴格垂直置中。
- **圓形 / 橢圓**：
  `c.circle(cx, cy, r, fill="accent", stroke="none", text="", size=13.0, color="ink", bold=False, font=None, role=None, name=None, id=None)`
  `c.ellipse(cx, cy, rx_px, ry_px, fill="accent", stroke="none", ... , id=None)`
- **背景環境光暈（裝飾層，不觸發重疊警示）**：
  `c.glow(cx, cy, r, color="accent@0.09", rings=2)`

---

## 五、 頁面標頭與排版原語

- **頁首與頁尾**：
  - `bottom_y = c.header(title, subtitle="", eyebrow="", x=68, y=42, w=1144)`
  - `c.footer(text="", slide_num=None, total_slides=None, line=True)`
- **自動測量高度文字框（推薦用於所有多行文字與標題）**：
  - `bottom_y = c.text_auto(x, y, w, text, size=15.0, color="ink", bold=False, align="left", font=None, role=None, line_height=None, pad_px=3.0, name=None)`
  - 支援 `size` 傳入 `TYPOGRAPHY_SCALE` Token（預設自動套用該 Token 的 `line_height`，數值 `pt` 預設 `1.38`），內建呼叫 `text_measure.py` 執行 CJK/拉丁斷行與高度估算，精準回傳**文字框底部 `bottom_y`**。
- **固定高度文字框（單行 KPI、置中數字）**：
  - `bottom_y = c.text(x, y, w, h, text, size=15.0, color="ink", bold=False, align="left", valign="top", font=None, role=None, pad_px=3.0, name=None, bg_hex=None)`
- **大數字統計指標（KPI Block）**：
  - `bottom_y = c.stat(x, y, w, value, label, val_size=46.0, lbl_size=13.5, val_color="accent", lbl_color="ink", align="left")`

---

## 六、 表格與外部圖片原語

- **簡約表格**：
  `c.table(x, y, w, h, headers, rows, highlight_cells=None, col_widths=None)`
  - `highlight_cells` 格式：`[{"row": row_idx, "col": col_idx, "color": "amber-400"}]`（`0`-based 資料列索引）標亮關鍵數據格，文字色會自動通過 `ensure_contrast()` 校準。
- **嵌入外部圖片**（配合 `scripts/fit_visual_asset.py` 裁切好比例）：
  `c.image(path, x, y, w, h=None, name="image_asset")`
