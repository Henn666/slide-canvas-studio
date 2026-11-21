# Single-Slide Verification & Critique Rubric (`critique-rubric.md`)

**單一職責**：定義原始 EMU 幾何指標（`dump_slide_layout.py`）與單頁渲染預覽圖（`render_single_slide.py` 經 macOS QuickLook 或 LibreOffice 轉出 PNG）的驗收基準。

---

## 一、 第一關：幾何座標硬性指標（`preview/slide_N_layout.json`）

1. **`out_of_bounds_count == 0`**：所有非裝飾元件皆落在 16:9 安全畫布內。
2. **`overlap_count == 0`**：任意兩個獨立語意元件之間無意外碰撞（背景光暈 `bg_glow_`、純線條/曲線 `vec_`、合法容器 `card_bg_` 除外）。
3. **`overflow_risk_count == 0`**：依 `text_measure.py` 估算的文字高度不超過文字框高度。

---

## 二、 第二關：真實預覽圖視覺審計（`preview/slide_N.png`）

透過 `read_file` 實際檢視渲染後的單頁 PNG，核對以下視覺體驗：

1. **層級與可讀性**：大標、副標與內文（≥ 14pt）一眼分明，字級與對比度清晰無灰暗模糊。
2. **向量平滑與圓角邊距**：曲線、圓弧與微圓角邊框滑順不刺眼，文字與邊框保有舒適內距。
3. **構圖呼吸感與去框節奏**：留白充足（≥ 30%），沒有滿版堆砌重疊方框；相鄰頁視覺重心明顯變化。
4. **頁尾收尾**：右下頁碼與來源無折行、不碰撞主內容區。

---

## 三、 收斂停止條件

- **一次通過**：幾何指標 `PASS` 且 PNG 視覺審計無明顯瑕疵即定稿。
- **局部微調上限（2 輪）**：若有座標或視覺微瑕，直接修改 `design/build_deck.py` 內的 `slide_N` 函式並執行 `--slide N` 重建驗證，最多收斂 2 輪。
