# Style Profile: Swiss Editorial & Surface Layering (`swiss-international`)

**適用場景**：商業策略簡報、高階產品發表、AI 系統架構與數據儀表板。以「背景三層明度微差（Surface Layering）」、「`0.75pt` 髮絲微光邊框」、「固定物理圓角（`rx=12`）」與「`1.4×` 寬鬆行距」取代傳統厚重框線與大圓角，建立精密儀表板與現代瑞士編輯部質感。

---

## 一、 色彩系統配方（Surface Layering & Tinted Neutrals）

> **核心鐵律**：絕對避免純黑（`#000000`）與高飽和正色（`#FF0000`、`#0000FF`）。全頁點綴主色（Accent）不超過 1～2 種。

### 選項 A：極簡瑞士紙感風（Light Editorial — 商業策略、產品簡報）
```python
PALETTE_LIGHT = {
    "bg": "#F8FAFC",        # 冷調微灰白畫布（取代刺眼純白）
    "surface": "#FFFFFF",   # 純白卡片浮於微灰白畫布上，無需陰影即有自然層次
    "ink": "#0F172A",       # 深石板黑主標題
    "muted": "#475569",     # 內文灰藍（標籤註解可用 #94A3B8）
    "border": "#E2E8F0",    # 髮絲級邊框（線寬鎖定 0.75pt）
    "accent": "#1D4ED8",    # 深邃科技藍（膠囊底色採極淺變體 #EFF6FF 配深藍字）
    "accent2": "#0F766E",   # 沉穩松石綠
    "font_heading": "Noto Sans TC",  # 英文數字可用 Inter / Segoe UI / Arial
    "font_body": "Noto Sans TC",
    "font_mono": "Menlo",
}
```

### 選項 B：現代深色科技風（Dark Bento — 技術架構、AI 系統展示）
```python
PALETTE_DARK = {
    "bg": "#0B0F19",        # 帶極微冷藍調的深炭黑畫布
    "surface": "#111827",   # 一級卡片底色（與畫布拉開 4%–6% 明度差）
    "surface2": "#1E293B",  # 二級強調卡片／內嵌子模組底色
    "ink": "#F8FAFC",       # 95% 亮白主標題（避免刺眼）
    "muted": "#94A3B8",     # 冷灰藍內文（次要標籤可用 #64748B）
    "border": "#1F2937",    # 低飽和微光髮絲邊框（或 #334155，線寬 0.75pt–1.0pt）
    "accent": "#38BDF8",    # 電光藍（關鍵指標數字、狀態膠囊、焦點連線）
    "accent2": "#34D399",   # 翡翠綠（亦可選琥珀金 #FBBF24）
    "font_heading": "Noto Sans TC",
    "font_body": "Noto Sans TC",
    "font_mono": "Menlo",
}
```

---

## 二、 字級階梯、幾何圓角與 8pt 空間配方（1280×720 像素換算）

1. **黃金字級階梯與跨平台字體**：
   - 英文／數字建議 `Inter`、`Segoe UI` 或 `Arial`；繁體中文鎖定 `Noto Sans TC` 或 `Microsoft JhengHei`。
   - **Hero KPI 巨型數字**：`40–48 pt` Bold，`line_height=1.0`。
   - **投影片主標題**：`24–28 pt` Bold，`line_height=1.15`。
   - **卡片標題**：`14–16 pt` Bold，`line_height=1.2`。
   - **內文要點**：`11–12 pt` Regular，**強制 `line_height=1.4`（`1.35–1.45`）**消除擁擠感。
   - **微型標籤（Kicker / Badge）**：`9–10 pt` Bold 英文全大寫。
2. **圓角曲率修正（維持 `~0.12 in = 12 px` 一致物理半徑）**：
   - `SlideCanvas` 的 `c.rect(..., rx=12)` 會自動依短邊動態計算 OpenXML `adjustments[0]`，確保大小卡片皆維持精緻微圓角（大卡片約 `0.03–0.04`、中卡片約 `0.05–0.06`），徹底擺脫預設 `0.16667` 的臃腫膠囊感；僅狀態標籤使用 `c.pill()`（全圓角 `0.5`）形成幾何對比。
3. **邊框與連接線規範**：
   - **卡片邊框**：嚴格鎖定 `0.75 pt` 至 `1.0 pt`（如 `stroke="border:0.75"`）。
   - **連接線（`c.connect()`）**：線寬 `1.25 pt` 至 `1.5 pt`（切忌超過 `2 pt`），非關鍵路徑使用次要灰藍（`#475569:1.25` 或 `#64748B:1.25`），箭頭採小巧精緻尺寸（`head_size=7.5`）。
4. **空間留白與 8pt 網格節奏（`13.333×7.5 in` = `1280×720 px`）**：
   - **網格間距（Gutter）**：統一 `18–21 px`（建議 `gap=20`）。
   - **卡片內距（Padding）**：標準卡片 `pad=22 px`，高密度數據卡片 `pad=16 px`。
   - **留白紅線**：純背景 ＋ 卡片內部留白須佔總畫布 **35%–45%**；若文字超過卡片高度 `75%` 應降階字級或拆分卡片。

---

## 三、 `SlideCanvas` 完整單頁範例（Light Editorial ＋ Dark Bento 通用寫法）

```python
def slide_swiss_layered(c, total):
    c.new_slide(bg="bg")
    c.header(
        eyebrow="STRATEGIC ARCHITECTURE • SURFACE LAYERING",
        title="以三層明度微差與 0.75pt 髮絲框，建立精密簡報秩序",
        subtitle="統一 12px 物理圓角、20px 呼吸通道與 1.4× 寬鬆行距，告別廉價厚框與文字擁擠",
    )

    # 三欄 Bento 佈局，統一 20px 間距（~0.21 in）
    col1, col2, col3 = c.cols(3, x=58, y=172, w=1164, h=460, gap=20, weights=[1.1, 1.0, 1.0])

    # ── 左欄：Hero KPI 主卡片（內距 22px，圓角 rx=12，邊框 0.75pt）──
    lx, ly, lw, lh = col1
    c.rect(lx, ly, lw, lh, rx=12, fill="surface", stroke="border:0.75", id="kpi_card")
    c.pill(lx + 22, ly + 22, 128, 24, fill="#EFF6FF", stroke="none", text="CORE METRIC", size=9.5, color="accent")
    c.stat(lx + 22, ly + 62, lw - 44, "42.8%", "結構化排版留白佔比", val_size=44, val_color="accent", lbl_color="muted")
    c.text_auto(
        lx + 22, ly + 178, lw - 44,
        "以冷調微灰畫布搭配純白浮動卡片，無需厚重陰影即可形成清晰視覺層次。",
        size=11.5, color="muted", line_height=1.42,
    )

    # ── 中欄 & 右欄：雙層節點自動連線示範（1.25pt 髮絲連線 + 7.5px 小箭頭）──
    mx, my, mw, mh = col2
    rx, ry, rw, rh = col3
    m_top, m_bot = c.rows(2, x=mx, y=my, w=mw, h=mh, gap=20)
    r_top, r_bot = c.rows(2, x=rx, y=ry, w=rw, h=rh, gap=20)

    c.rect(*m_top, rx=12, fill="surface", stroke="border:0.75", id="node_a")
    yt = c.text_auto(m_top[0] + 22, m_top[1] + 22, m_top[2] - 44, "1. 卡片圓角正規化", size=15, bold=True, color="ink")
    c.text_auto(m_top[0] + 22, yt + 8, m_top[2] - 44, "強制鎖定約 12px 物理圓角，消除預設膨脹膠囊感。", size=11.5, color="muted", line_height=1.42)

    c.rect(*m_bot, rx=12, fill="surface", stroke="border:0.75", id="node_b")
    yt2 = c.text_auto(m_bot[0] + 22, m_bot[1] + 22, m_bot[2] - 44, "2. 髮絲級邊框控制", size=15, bold=True, color="ink")
    c.text_auto(m_bot[0] + 22, yt2 + 8, m_bot[2] - 44, "全場邊線鎖定 0.75pt，維持精密儀表板般的俐落邊界。", size=11.5, color="muted", line_height=1.42)

    c.rect(*r_top, rx=12, fill="surface", stroke="border:0.75", id="node_c")
    yt3 = c.text_auto(r_top[0] + 22, r_top[1] + 22, r_top[2] - 44, "3. 焦點流向指引", size=15, bold=True, color="ink")
    c.text_auto(r_top[0] + 22, yt3 + 8, r_top[2] - 44, "關鍵路徑使用 1.5pt 主色箭頭，次要連線採低調灰藍。", size=11.5, color="muted", line_height=1.42)

    c.rect(*r_bot, rx=12, fill="surface", stroke="border:0.75", id="node_d")
    yt4 = c.text_auto(r_bot[0] + 22, r_bot[1] + 22, r_bot[2] - 44, "4. 跨平台字距安全", size=15, bold=True, color="ink")
    c.text_auto(r_bot[0] + 22, yt4 + 8, r_bot[2] - 44, "鎖定 Inter + Noto Sans TC，確保多平台渲染行高一致。", size=11.5, color="muted", line_height=1.42)

    c.connect("node_a", "node_c", style="ortho", stroke="accent:1.5", head_size=7.5)
    c.connect("node_b", "node_d", style="ortho", stroke="muted:1.25:dash", head_size=7.5)

    c.footer("Swiss Editorial & Surface Layering • 0.75pt Hairline System", slide_num=1, total_slides=total)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"modern Swiss editorial and Bento UI aesthetic, layered surface tones on cool off-white #F8FAFC (or deep charcoal navy #0B0F19), ultra-thin 0.75pt hairline borders #E2E8F0, subtle 12px rounded corners, crisp slate typography #0F172A, minimal cobalt blue #1D4ED8 or electric cyan #38BDF8 accents, generous whitespace, no heavy drop shadows, no random text"`
