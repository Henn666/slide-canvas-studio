# Style Profile: Bento Grid (`bento-grid`)

**適用場景**：產品功能總覽頁（Feature Overview）、個人作品集、數據儀表板（Dashboard）、高資訊密度卻保持清爽掃描感的懶人包簡報。

---

## 一、 風格色票與字體設定（`PALETTE`）

```python
PALETTE = {
    "bg": "#F4F5F7",        # 柔和中性冷灰畫布，突顯卡片邊界
    "surface": "#FFFFFF",   # 標準便當盒純白卡片底色
    "ink": "#111827",       # 深石板黑（主標題與卡片標題）
    "muted": "#6B7280",     # 輔助說明灰（標籤與副文字）
    "border": "#E5E7EB",    # 精緻卡片微邊框（1pt）
    "accent": "#2563EB",    # 亮鈷藍（主打亮點卡片與數據焦點）
    "accent2": "#10B981",   # 翡翠綠（正向成長趨勢與狀態標籤）
    "font_heading": "PingFang TC",
    "font_body": "PingFang TC",
    "font_mono": "Menlo",
}
```

---

## 二、 核心視覺規則（SlideCanvas 實作要點）

1. **不對等模組化網格（Asymmetric Modular Grid）**：
   - 利用 `c.cols(3, weights=[1.2, 1.0, 1.0])` 搭配內層 `c.rows(2, ...)` 切割出「1 大 4 小」或「2 寬 3 窄」的矩形便當盒佈局。
   - **鐵律**：所有相鄰卡片的「外框切齊線」與「間距（Gap，建議 `16px`～`20px`）」必須嚴格一致。
2. **高資訊密度但不雜亂（1 Card = 1 Core Point）**：
   - 每個便當格只傳達一個賣點（一張圖表、一組大數字、或一段 2 行以內的精簡說明）。
   - 用 1 個實心深色或高彩重點格（如 `fill="accent"` 搭配白字 `color="#FFFFFF"`）打破全白卡片單調感，引導視覺第一落點。
3. **統一圓角**：所有大中小格子統一 `rx=16`～`20`，呈現精密拼圖的秩序美。

---

## 三、 `SlideCanvas` 完整單頁範例

```python
def slide_bento_grid(c, total):
    c.new_slide(bg="bg")
    c.header(
        eyebrow="PRODUCT CAPABILITIES",
        title="一頁看懂核心能力矩陣：高密度模組化便當盒佈局",
        subtitle="以嚴格對齊的 16px 間距切割大小錯落的功能區塊，讓受眾 3 秒內完成掃描",
    )

    gap = 16
    # 外層切分為三欄：左寬欄 (42%) + 中欄 (29%) + 右欄 (29%)
    col1, col2, col3 = c.cols(3, y=172, h=465, gap=gap, weights=[1.4, 1.0, 1.0])

    # ── 左欄：1 個主打深藍焦點大盒 + 1 個底部小盒 ──
    top_l, bot_l = c.rows(2, x=col1[0], y=col1[1], w=col1[2], h=col1[3], gap=gap, weights=[1.55, 1.0])
    c.rect(*top_l, rx=18, fill="accent", stroke="none")
    c.pill(top_l[0] + 24, top_l[1] + 22, 110, 26, fill="#FFFFFF@0.20", stroke="none", text="FLAGSHIP", color="#FFFFFF")
    c.stat(top_l[0] + 24, top_l[1] + 74, top_l[2] - 48, "10×", "自動化產出效率提升", val_size=56, val_color="#FFFFFF", lbl_color="#E0E7FF")

    c.rect(*bot_l, rx=18, fill="surface", stroke="border:1")
    yb = c.text_auto(bot_l[0] + 22, bot_l[1] + 20, bot_l[2] - 44, "原生 OpenXML 匯出", size=16, bold=True, color="ink")
    c.text_auto(bot_l[0] + 22, yb + 8, bot_l[2] - 44, "100% 保留 PowerPoint 可編輯圖層與字體設定。", size=13, color="muted")

    # ── 中欄：上中下三個均分小盒（2 格合併範例：上 1 下 1）──
    top_m, bot_m = c.rows(2, x=col2[0], y=col2[1], w=col2[2], h=col2[3], gap=gap, weights=[1.0, 1.35])
    c.rect(*top_m, rx=18, fill="surface", stroke="border:1")
    c.stat(top_m[0] + 20, top_m[1] + 26, top_m[2] - 40, "99.9%", "排版零重疊通過率", val_size=38, val_color="accent2")

    c.rect(*bot_m, rx=18, fill="#111827", stroke="none")
    ym = c.text_auto(bot_m[0] + 22, bot_m[1] + 24, bot_m[2] - 44, "Dark Mode 預覽", size=16, bold=True, color="#FFFFFF")
    c.text_auto(bot_m[0] + 22, ym + 8, bot_m[2] - 44, "深色卡片反差襯托關鍵模組，強化節奏感。", size=13, color="#9CA3AF")

    # ── 右欄：上方進度環盒 + 下方列表盒 ──
    top_r, bot_r = c.rows(2, x=col3[0], y=col3[1], w=col3[2], h=col3[3], gap=gap, weights=[1.2, 1.0])
    c.rect(*top_r, rx=18, fill="surface", stroke="border:1")
    cx_r = top_r[0] + top_r[2] / 2
    cy_r = top_r[1] + 108
    c.donut(cx_r, cy_r, r=62, start_deg=0, end_deg=360, thickness=0.22, fill="border")
    c.donut(cx_r, cy_r, r=62, start_deg=-90, end_deg=190, thickness=0.22, fill="accent")
    c.text(cx_r - 45, cy_r - 18, 90, 36, "78%", size=22, bold=True, color="ink", align="center", valign="middle")
    c.text_auto(top_r[0] + 16, top_r[1] + 190, top_r[2] - 32, "Token 節省比例", size=13.5, bold=True, color="muted", align="center")

    c.rect(*bot_r, rx=18, fill="surface", stroke="border:1")
    yr = c.text_auto(bot_r[0] + 20, bot_r[1] + 22, bot_r[2] - 40, "內建安全護欄", size=16, bold=True, color="ink")
    c.text_auto(bot_r[0] + 20, yr + 8, bot_r[2] - 40, "• WCAG 對比自動檢測\n• CJK 斷行禁則保護", size=13, color="muted", line_height=1.5)

    c.footer("Bento Grid System • 16px Strict Gap", slide_num=1, total_slides=total)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"modern SaaS bento grid UI overview on soft cool gray #F4F5F7, crisp white rounded cards #FFFFFF with subtle 1px border #E5E7EB, one vibrant cobalt blue #2563EB hero tile, clean isometric 3D icon accents, ultra organized modular layout, no messy text"`
