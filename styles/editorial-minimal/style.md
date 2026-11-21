# Style Profile: Editorial Minimal (`editorial-minimal`)

**適用場景**：產品願景發表、設計策略提案、深度專題研究、戰略敘事（Storytelling）與顧問洞察報告。

---

## 一、 模板模式宣告（Template Mode）

- `use_template`: `false`（純風格自配模式）
- `background_grid`: `false`（不畫滿版網格，改以精緻水平分割細線與大片暖白留白營造雜誌編輯感）
- `footer_badge_style`: `minimal_line`（頂部或底部單條極細水平線 ＋ 頁碼與出處文字）

---

## 二、 鎖定色票（Palette Tokens）

| 語義角色 | HEX 色碼 | 視覺角色與使用規範 |
| :--- | :---: | :--- |
| **`bg_canvas`** | `FAF6F0` | 暖米白紙質畫布底色（Warm Editorial Paper） |
| **`bg_surface`** | `F2ECE1` | 次級引言框、表頭或柔和色塊底襯 |
| **`ink_primary`** | `1C1917` | 濃炭黑主標題與內文（極高閱讀舒適度） |
| **`ink_muted`** | `78716C` | 暖灰眉標、圖說與出處標註 |
| **`border_grid`** | `D6D0C4` | 編輯部水平分隔細線（`0.75pt`）與表格橫線 |
| **`accent_primary`** | `C2410C` | **赤陶暖橘（Terracotta 主強調色）**：用於巨型統計數字、核心轉折結論、焦點標記 |
| **`accent_secondary`** | `0F766E` | **深松綠（Deep Teal 輔助色）**：用於平衡畫面的第二維度數據或架構框線 |

---

## 三、 字體家族與排版氣質（Typography & Vibe）

- **`font_heading`**: `Georgia`（或 `Arial` Bold，兼具人文敘事感與高辨識度）
- **`font_body`**: `Arial`
- **`font_mono`**: `Consolas`
- **視覺氣質**：
  - **高留白比例（40%+ 留白）**：不用厚重外框把所有文字關進盒子裡，改用「頂部水平細線（Top Rule）＋ 對齊欄位」呈現高級雜誌排版。
  - **強烈字級反差**：`kpi_hero`（`56pt~64pt`）與 `body`（`13pt`）形成鮮明對比。

---

## 四、 16:9 外部生圖風格錨點（`visual_prompt_anchor`）

> `"editorial magazine style diagram on warm cream paper background #FAF6F0, charcoal ink lines #1C1917, terracotta #C2410C and deep teal #0F766E accents, minimalist architectural clarity, generous negative space, no text"`
