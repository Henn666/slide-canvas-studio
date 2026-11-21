# Style Profile: Dark Engineering Blueprint (`dark-engineering`)

**適用場景**：系統架構深度解析、資料庫／編譯器／底層技術分享、基準測試（Benchmark）報告、高密度工程設計簡報。

---

## 一、 模板模式宣告（Template Mode）

- `use_template`: `false`（純風格自配模式，由 `init_deck.py` 建立乾淨 16:9 畫布並由 `build_slide.py` 自動繪製工程網格與頁尾編號框）。
- `background_grid`: `true`（啟用 12×6 細線工程背景網格，線寬 `0.5pt`，色碼 `163252`）。
- `footer_badge_style`: `blueprint_box`（右下角結構化雙格方框：`SHT NN/MM | Source: ...`）。

---

## 二、 鎖定色票（Palette Tokens）

| 語義角色 | HEX 色碼 | 視覺角色與使用規範 |
| :--- | :---: | :--- |
| **`bg_canvas`** | `0D2137` | 深海工程藍主畫布底色 |
| **`bg_surface`** | `132D4A` | 表頭底色、次要模組容器底襯 |
| **`ink_primary`** | `F8FAFC` | 冰白高對比主標題與主要文字 |
| **`ink_muted`** | `94A3B8` | 灰藍眉標、圖解輔助說明與座標標籤 |
| **`border_grid`** | `1E3A5F` | 背景工程網格線、表格水平分隔線、中線虛線 |
| **`accent_primary`** | `F59E0B` | **琥珀亮橘（全場焦點）**：用於 `590×` 巨型數據、核心模組外框（如 `SQLite library`）、強調字詞與主資料流箭頭 |
| **`accent_secondary`** | `5BC0BE` | **工程青藍（結構對照）**：用於對照組模組外框（如 `CLIENT/SERVER`）、表頭文字與大規模測試面積框 |

---

## 三、 字體家族與排版氣質（Typography & Vibe）

- **`font_heading`**: `Arial`（或 `Helvetica Neue`，乾淨銳利的無襯線粗體）
- **`font_body`**: `Arial`
- **`font_mono`**: `Consolas`（或 `Menlo` / `Courier New`，用於 `eyebrow` 編號、程式碼檔名如 `sqlite3.c`、以及右下角 `SHT 03/12` 頁碼框）
- **視覺氣質**：
  - **零花俏裝飾**：不使用柔和陰影、不使用圓滾滾的膠囊、不使用多色漸層。
  - **直角與細框**：所有架構方塊皆採用銳利直角或極微圓角矩形，線寬 `1.25pt`，以「實線框 vs 虛線框」、「青藍框 vs 琥珀橘框」建立絕對清晰的工程語義。
  - **極簡水平線表格**：表格僅保留水平分隔細線與深色表頭底襯，無垂直格線，重點數據以 `F59E0B` 亮橘粗體標示。

---

## 四、 16:9 外部生圖風格錨點（`visual_prompt_anchor`）

若該頁需透過 `c.image()` 嵌入外部視覺配圖，生圖 Prompt 建議附加以下風格錨點：
> `"dark navy blueprint background #0D2137, subtle technical grid lines #163252, clean engineering schematic vector diagram in cyan #5BC0BE and amber orange #F59E0B, flat orthographic precision, no drop shadows, no random text"`
