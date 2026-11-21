# Style Profile: Corporate Standard Template (`corporate-standard`)

**適用場景**：企業高層匯報（Executive Briefing）、季度業務檢討（QBR）、客戶提案、需嚴格遵循公司指定母片（Slide Master）之正式商務簡報。

---

## 一、 模板模式宣告（Template Mode）

- `use_template`: `true`
- `template_file`: `company-template.pptx`（位於同目錄 `styles/corporate-standard/company-template.pptx`）
- `reference_file`: `ref-example.pptx`（同目錄參考範例檔）
- **使用前必跑指令**：
  ```bash
  python3 scripts/inspect_template.py --pptx styles/corporate-standard/company-template.pptx
  ```
- **母片與不可更動區域限制**：
  - 保留母片右上角或左下角之企業 Logo 與底部版權聲明區（`y >= 17.8 cm` 為母片保留區）。
  - 內容元件安全高度控制在 `y = 3.8 cm` 至 `y = 17.2 cm` 之間。

---

## 二、 鎖定色票（Palette Tokens）

| 語義角色 | HEX 色碼 | 視覺角色與使用規範 |
| :--- | :---: | :--- |
| **`bg_canvas`** | `F8FAFC` | 極淺冷灰商務畫布底色（乾淨不刺眼） |
| **`bg_surface`** | `FFFFFF` | 純白資訊卡片底襯、表格偶數列底色 |
| **`ink_primary`** | `0F172A` | 深海石墨黑主標題與核心數據文字 |
| **`ink_muted`** | `475569` | 次要內文、欄位說明與頁尾來源 |
| **`border_grid`** | `CBD5E1` | 卡片外框細線（`1pt`）與表格分隔線 |
| **`accent_primary`** | `2563EB` | **企業皇家藍（主強調色）**：用於核心 KPI、卡片頂部強調條、重點文字高亮 |
| **`accent_secondary`** | `0D9488` | **商務青綠（輔助對照色）**：用於正向成長指標、對照組標示 |

---

## 三、 字體家族與排版氣質（Typography & Vibe）

- **`font_heading`**: `Arial`
- **`font_body`**: `Arial`
- **`font_mono`**: `Consolas`
- **視覺氣質**：
  - 結構化白底卡片（`bg_surface: FFFFFF`）搭配 `1pt` 淺灰邊框（`CBD5E1`）與頂部 `0.15cm` 皇家藍強調細條。
  - 數據導向、層級分明，適合三欄卡片（`three_col_cards`）、雙欄對比（`two_col_compare`）與基準表格（`data_table`）。

---

## 四、 16:9 外部生圖風格錨點（`visual_prompt_anchor`）

> `"clean corporate minimalist illustration on soft light gray background #F8FAFC, royal blue #2563EB and teal #0D9488 accents, executive business presentation style, crisp vector geometry, no clutter, no embedded text"`
