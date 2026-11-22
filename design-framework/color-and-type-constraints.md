# Color, Contrast & Typography Baselines (`color-and-type-constraints.md`)

**單一職責**：規範 **Step 0 全局藝術指導（Art Direction）**、Tailwind 設計 Token 與透明語法契約、繪圖期 WCAG 自動對比度護欄，以及 16:9 投影可讀字級階梯。

---

## Step 0：Deck-Level Art Direction Synthesis（整份簡報開頭僅執行一次）

除非使用者明確指定 `styles/<style>/style.md`，否則在撰寫任何投影片前，請先根據簡報主題與受眾執行一次 **Step 0**，於 `design/build_deck.py` 頂層宣告單一全局 `THEME = SlideTheme(...)`：

1. **Domain-to-Hue 領域色相映射**（避免千篇一律使用預設藍，善用 22 個 Tailwind 色系建立領域辨識度）：
   - **AI / Cloud / 開發者工具**：深石板／深鋅色（`slate-950` / `zinc-950`）搭配 `sky-400`、`indigo-400` 或 `cyan-400`。
   - **Bio-Tech / 生醫 / 潔淨能源**：深青綠（`teal-950` / `emerald-950`）搭配 `lime-400`、`emerald-400`（或淺石色 `stone-50` 搭配 `emerald-600`）。
   - **FinTech / 企業策略 / 高階簡報**：極簡淺灰白（`slate-50` / `neutral-50`）搭配 `blue-600`、`indigo-600`，或深沉 `slate-950` 搭配 `amber-400`。
   - **設計 / 媒體 / 品牌敘事**：暖炭黑（`stone-950` / `zinc-950`）搭配 `rose-400`、`fuchsia-400`、`violet-400`，或暖白 `stone-50` 搭配 `orange-600`。
   - **硬體 / 資安 / 工業系統**：純暗中性灰（`neutral-950`）搭配 `amber-400`、`orange-400` 或 `red-500`。
2. **Surface & Geometry 材質與幾何語氣**：
   - 依品牌調性決定全局圓角 `radius`（嚴謹工程 `rounded-md` / `rounded-lg`、現代科技 `rounded-xl` / `rounded-2xl`、硬派風格 `rounded-none`）、邊框線寬 `border_pt`（輕薄 `0.5~0.75 pt` 或明確 `1.0~1.25 pt`）與字型組合（`font_heading` / `font_body` / `font_mono`）。
   - 主色與輔色維持焦點克制（**Focal Restraint**）：單頁內高飽和強調色 `accent` 總面積建議控制在 **≤ 10%**，避免彩虹拼盤分散視線。
3. **Anti-Monotony 跨頁防單調鐵律（Never Switch Color Themes Mid-Deck）**：
   - **整份簡報嚴禁中途更換主色票或反轉深淺主題**（全份共用同一個 `THEME`）。
   - 跨頁視覺節奏應透過 **不對稱 `c.cols(..., weights=...)` 欄位比例**（如 `[1.25, 0.75]` 交替 `[0.7, 1.3]`）、**`c.card(variant=...)`（`"default"` / `"accent"` / `"subtle"` / `"dashed"`）層次切換**、**向量圖表（`donut` / `curve` / `connect`）** 與 **負空間留白節奏** 來創造變化。

---

## 一、 Tailwind 全光譜 Token 與透明度優先契約（`tokens.py`）

1. **全光譜色票支援（245 個內建 Token）**：
   - 支援完整 **22 個 Tailwind 色系**（`slate`, `gray`, `zinc`, `neutral`, `stone`, `red`, `orange`, `amber`, `yellow`, `lime`, `green`, `emerald`, `teal`, `cyan`, `sky`, `blue`, `indigo`, `violet`, `purple`, `fuchsia`, `pink`, `rose`）× **11 階色階**（`50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950`，共 242 色）。
   - 支援 `"white"`（`#FFFFFF`）、`"black"`（`#000000`）、`"transparent"` / `"none"`、語義色（`bg`/`canvas`、`surface`/`surface_1`、`surface2`/`surface_2`、`ink`/`text_primary`、`muted`/`text_muted`、`border`、`accent`、`accent2`）及 `#RRGGBB` HEX。
2. **透明度語法優先合約（`/` 預混色 vs `@` 真 Alpha）**：
   - **預設一律使用 `/` 預混色（Pre-blending）**：例如 `"sky-500/15"`、`"accent/10"`、`"surface2/50"`。`TokenResolver.resolve_color_alpha()` 會在繪圖期將前景色依比例預混至目前所在局部底色（`base_bg_hex`）輸出純色 HEX，在 PowerPoint / Keynote / LibreOffice 中渲染最銳利、絕不因半透明疊層變髒。
   - **僅在特殊疊層上方才使用 `@0.NN` 真 OpenXML Alpha**：只有將元素疊加於 `c.glow()` 光暈或 `c.image()` 攝影底圖上方時，才使用 `"slate-950@0.75"` 或 `"accent@0.12"` 保留原生 `<a:alpha>` 透明通道。
   - 若同時混寫 `/` 與 `@`（如 `"sky-500/20@0.5"`），引擎會防禦性將兩者透明度相乘處理而不崩潰，但應避免混寫。
   - **嚴禁不支援的 CSS 類別**：禁止使用 CSS 動畫/轉場（`animate-*`, `transition-*`）、CSS 陰影（`shadow-*`）或響應式/互動前綴（`md:`, `hover:`, `dark:`）。

---

## 二、 繪圖期 WCAG 自動對比度護欄（Draw-Time Auto-Contrast Guard）

`SlideCanvas` 不只在初始化 `SlideTheme.to_palette_dict()` / `set_palette()` 時驗證全域對比度（`text_primary >= 7.0:1`、`text_muted >= 4.5:1`、`accent >= 3.5:1`），更在**實際繪製每一塊文字與容器時即時檢查背景堆疊（`_bg_stack`）**：

- **局部底色追蹤（`_effective_bg_at()`）**：每當繪製不透明實心背景的 `card`、`rect`、`pill`、`circle`、`ellipse`（不含 `bg_glow_` 裝飾光暈），引擎會記錄其覆蓋範圍與實心色碼；換頁時自動清空。
- **即時自動修色（`TokenResolver.ensure_contrast()`）**：在 `c.pill()`、`c.rect()`、`c.circle()`、`c.text()`、`c.text_auto()`、`c.card()` 與 `c.table()` 寫入文字時，自動比對文字色與所處局部底色的 WCAG 對比度（一般文字要求 `≥ 4.5:1`，`≥ 24 pt` 大標題放寬為 `≥ 3.0:1`）：
  - 若發生「亮黃膠囊配白字（如 `fill="amber-400", color="white"`）」或「深青卡片配深青字（如 `fill="teal-900", color="teal-900"`）」等低對比陷阱，`ensure_contrast()` 會**自動沿著該色系的 `SHADE_STEPS`（`50..950`）尋找最接近且達標的色階**，若無對應色系或皆不達標則安全退回高對比色（深底 `"F8FAFC"` / 淺底 `"0F172A"`）。

---

## 三、 可讀字級階梯（16:9 投影閱讀基準）

在 16:9 簡報畫布上，內文應避免低於 `12 pt` 的微弱字級，並可直接使用 `TYPOGRAPHY_SCALE` 簡寫 Token（`text-xs`..`text-5xl`，數值單位皆為 PowerPoint `pt`）：

| 層級角色 | 建議基準 (`pt`) | 對應 Tailwind Token | 允許彈性範圍 | 用途說明 |
| :--- | :---: | :---: | :---: | :--- |
| **`kpi_hero`** | `44 ~ 56 pt` | `text-5xl` (`44 pt`) | `44 ~ 72 pt` | 巨型數據指標、倍數與核心百分比 |
| **`title`** | `29 ~ 36 pt` | `text-3xl` (`29 pt`) / `text-4xl` (`36 pt`) | `26 ~ 44 pt` | 單頁核心結論大標（Action Title） |
| **`subtitle`** | `16.5 ~ 20 pt` | `text-lg` (`16.5 pt`) / `text-xl` (`20 pt`) | `15 ~ 24 pt` | 副標題、區塊標題與卡片主標 |
| **`body`** | `14 ~ 16.5 pt` | `text-base` (`14 pt`) / `text-lg` (`16.5 pt`) | `14 ~ 18 pt` | 一般內文與條列（維持大器易讀度） |
| **`card_body`** | `12 ~ 14 pt` | `text-sm` (`12 pt`) / `text-base` (`14 pt`) | `12 ~ 16 pt` | 卡片說明文字與表格內容 |
| **`eyebrow / caption`** | `10 ~ 12 pt` | `text-xs` (`10 pt`) / `text-sm` (`12 pt`) | `9.5 ~ 13 pt` | 眉標（配合 `font_mono`）、頁尾出處與頁碼 |

---

## 四、 版面清潔最小準則

- **最小欄寬原則**：若水平分欄後單欄文字過窄（每行容納少於 ~15–20 字），應改採垂直堆疊（`rows`）或精簡字句，避免文字碎裂換行。
- **去框化（De-boxing）**：當留白、字級對比或單一條細線（`line`）已足以建立層次時，**不應為每段文字強加邊框卡片**；必須分組時善用 `c.card(variant="subtle")` 或 `variant="dashed"` 降低視覺噪音。
- **跨平台安全字型**：優先選用本機與常見系統具備的無襯線/等寬配對（如 `PingFang TC` / `Arial` / `Helvetica Neue` 搭配 `Menlo` / `Consolas`），並由 `text_measure.py` 執行中英混排高度估算與避頭尾處理。
