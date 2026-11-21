# Style Profile: Apple Minimal & Research System (`apple-minimal`)

**適用場景**：頂尖科技發表會、AI 科研論文架構解析、高階技術原理簡報。結合 Apple System Gray 6 極致留白美學、低飽和功能語義色與精確正交數據總線（Orthogonal Data Bus）。

---

## 一、 模板模式宣告（Template Mode）

- `use_template`: `false`（純風格自配模式）
- `background_grid`: `false`（維持高明度純淨暖淺灰 `#F5F5F7` 畫布，禁止滿版網格線，保留 40% 以上呼吸留白）
- `footer_badge_style`: `minimal_line`（底部極細分割線 ＋ 簡潔頁碼與資料來源）

---

## 二、 鎖定色票（Palette Tokens — 90-5-5 表面積比例）

| 語義角色 | HEX 色碼 | 視覺角色與使用規範 |
| :--- | :---: | :--- |
| **`bg_canvas`** | `F5F5F7` | **Apple System Gray 6** 漫反射暖淺灰基底（佔比 >90%） |
| **`bg_surface`** | `FFFFFF` | 純白懸浮微玻璃卡片底色，搭配 `0.8pt~1pt` `#E5E5EA` 髮絲邊框 |
| **`ink_primary`** | `1D1D1F` | 曜石深炭黑（對比度 `16.5:1`），主標題、卡片文字與核心數據一律純黑 |
| **`ink_muted`** | `6E6E73` | 中性經典灰，僅用於頁尾出處、圖說與軸線註釋（卡片標題與內文禁用淺灰） |
| **`border_grid`** | `E5E5EA` | 髮絲級中性邊框與極細水平分割線 |
| **`accent_primary`** | `0071E3` | **Apple 工程藍（主要強調色）**：用於資料總線（Data Bus）、關鍵架構連線與正交箭頭 |
| **`accent_secondary`** | `3A7D74` | **低飽和松石青（輔助強調色）**：用於正向驗證通過、安全放行、Auto Mode 成功路徑 |

### 延伸功能語義色票（僅限於 `custom_elements` 小面積 <5% 使用）
- **獨立階段分區底框（Discrete Stage Container）**：`ECECF0`（中性無色偏極淡灰，與純白卡片 `#FFFFFF` 區分層次）
- **風險 / 瓶頸標記（Dusty Rose / Coral）**：`A84A5C`（低飽和乾燥玫瑰）或 `FF3B30`（功能警示紅）
- **核心中樞 / 守門員（Warm Ochre / Amber）**：`9A6B2F`（暖赭金）或 `FF9500`（功能運算琥珀）
- **多 Agent 指揮 / 協作（Lavender）**：`635D94`（低飽和薰衣草紫）

---

## 三、 字體家族與排版氣質（Typography & Color Rules）

- **`font_heading`**: `PingFang TC`（或 `Arial` / SF Pro Bold，無襯線俐落粗體）
- **`font_body`**: `PingFang TC`（或 `Arial`）
- **`font_mono`**: `Menlo`（或 `Consolas` / `SF Mono`，用於 Eyebrow 編號、CLI 指令如 `/doctor`、`Exit Code 2`）
- **核心設計約束**：
  1. **嚴格禁止放射光暈（Zero Halos / No Neon Glow）**：所有卡片與標籤維持銳利封閉的實線髮絲邊界。
  2. **正交數據總線（Orthogonal Midline Alignment）**：方塊之間優先使用直角水平與垂直箭頭連接中心錨點，嚴禁跨越標題禁區。
  3. **二元對比度鐵律**：淺底（`F5F5F7` / `FFFFFF` / `ECECF0`）一律搭配 `1D1D1F` 深炭黑字；實心彩色徽章底搭配 `FFFFFF` 純白字。

---

## 四、 16:9 外部生圖風格錨點（`visual_prompt_anchor`）

> `"Apple flagship aesthetic on light gray canvas #F5F5F7, crisp floating white cards #FFFFFF with hairline border #E5E5EA, single Apple blue data bus #0071E3, clean minimalist vector precision, zero halos, no embedded text"`
