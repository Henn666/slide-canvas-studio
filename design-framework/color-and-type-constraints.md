# Color, Contrast & Typography Baselines (`color-and-type-constraints.md`)

**單一職責**：只規範「最低限度的可讀性與焦點克制底線」，保留配色風格與字體氛圍給 LLM 依主題自由創意發揮。

---

## 一、 色彩最低底線（由 `SlideCanvas.set_palette()` 自動把關）

除非使用者指定 `styles/<style>/style.md`，否則 **LLM 可依簡報主題自由設計色票**（深色科技、淺色雜誌、暖色研究或品牌色皆可），僅須遵守 3 條基本規則：

1. **對比度底線**：`bg_canvas` 與主文字 `ink_primary` 的 WCAG 對比度 **必須 ≥ 4.5:1**（標題建議 ≥ 7.0:1）；次要文字 `ink_muted` 建議 ≥ 3.0:1。
2. **結構色階清楚**：定義一組一致的 `palette` Tokens（`bg_canvas`, `bg_surface`, `ink_primary`, `ink_muted`, `border_grid`, `accent_primary`, `accent_secondary`）。
3. **焦點單一法則（Focal Restraint）**：單頁內最多 **1–2 個核心元素**使用高飽和 `accent_primary`（強調色總面積建議控制在 **≤ 10%**）；其餘區域保持中性沉穩，避免彩虹拼盤分散視線。

---

## 二、 可讀字級階梯（16:9 投影閱讀基準）

在 16:9 簡報畫布上，避免使用 11–12pt 的微弱字級，採用清晰層級拉開閱讀節奏：

| 層級角色 | 建議基準 (`pt`) | 允許彈性範圍 | 用途說明 |
| :--- | :---: | :---: | :--- |
| **`kpi_hero`** | `56 pt` | `44 ~ 72 pt` | 巨型數據指標、倍數與核心百分比 |
| **`title`** | `30 pt` | `26 ~ 38 pt` | 單頁核心結論大標（Action Title） |
| **`subtitle`** | `17 pt` | `15 ~ 20 pt` | 副標題、區塊標題與引導句 |
| **`body`** | `15.5 pt` | `14 ~ 18 pt` | 一般內文、卡片與條列（維持清晰大器易讀度） |
| **`eyebrow`** | `11.5 pt` | `10.5 ~ 13 pt` | 頁首章節定位標籤（推薦配合 `font_mono`） |
| **`caption`** | `10.5 pt` | `9.5 ~ 12 pt` | 頁尾出處、頁碼與座標軸刻度 |

---

## 三、 版面清潔最小準則

- **最小欄寬原則**：若水平分欄後單欄文字過窄（每行容納少於 ~15–20 字），應改採垂直堆疊（`stack_v`）或精簡字句，避免文字碎裂換行。
- **去框化（De-boxing）**：當留白、字級對比或單一條細線（`line`）已足以建立層次時，**不應為每段文字強加邊框卡片**。
- **跨平台安全字型**：優先選用本機與常見系統具備的無襯線/等寬配對（如 `PingFang TC` / `Arial` / `Helvetica Neue` 搭配 `Menlo` / `Consolas`），並由 `text_measure.py` 執行中英混排高度估算與避頭尾處理。
