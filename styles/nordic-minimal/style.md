# Style Profile: Scandinavian Minimalism (`nordic-minimal`)

**適用場景**：居家生活與家具品牌、選物電商、建築與室內設計、健康生活、永續環保（ESG）與人文品牌故事簡報。

---

## 一、 風格色票與字體設定（`PALETTE`）

```python
PALETTE = {
    "bg": "#FAF8F5",        # 燕麥亞麻暖白基底（Warm Oat / Natural Light）
    "surface": "#F2EDE4",   # 淺原木與亞麻砂色卡片底襯
    "ink": "#2C2A29",       # 柔和深木炭黑（溫潤不刺眼，對比度仍達 >12:1）
    "muted": "#7A746E",     # 暖石灰（圖說與次要註解）
    "border": "#E3DCD2",    # 亞麻細線邊框（1pt）
    "accent": "#7A8C7E",    # 鼠尾草綠（Sage Green — 自然與永續焦點）
    "accent2": "#6B8299",   # 霧霾北歐藍（Fjord Blue — 平衡輔助色）
    "font_heading": "Avenir Next",  # 幾何無襯線字體（亦可用 Futura / PingFang TC）
    "font_body": "Avenir Next",
    "font_mono": "Menlo",
}
```

---

## 二、 核心視覺規則（SlideCanvas 實作要點）

1. **Hygge 溫潤通透色盤（Low-Saturation Earthy Palette）**：
   - 嚴禁任何高飽和螢光色或純黑 `#000000`。所有色彩皆帶有自然灰調（燕麥白 `#FAF8F5`、亞麻砂 `#F2EDE4`、鼠尾草綠 `#7A8C7E`、暖木炭 `#2C2A29`）。
2. **機能美學與極柔輪廓（Soft Geometry & Organic Whitespace）**：
   - 卡片採用溫和圓角（`rx=12`～`16`）搭配極淡的亞麻色塊填充或 1pt 細框，避免厚重邊線帶來的壓迫感。
   - 善用「無框留白對齊 ＋ 頂部極細水平分割線」呈現北歐雜誌的呼吸節奏。
3. **幾何無襯線字體與親和節奏**：
   - 選用比例均衡的幾何無襯線字體（`Avenir Next` / `PingFang TC`），行距略寬（`1.45`～`1.55`），傳遞平易近人的閱讀體驗。

---

## 三、 `SlideCanvas` 完整單頁範例

```python
def slide_nordic_minimal(c, total):
    c.new_slide(bg="bg")
    c.header(
        eyebrow="NORDIC FUNCTIONALISM • HYGGE",
        title="自然光感、低飽和與少即是多的生活機能",
        subtitle="以燕麥暖白與鼠尾草綠構築通透無壓迫的敘事節奏",
    )

    # 左圖右文 / 溫潤色塊對比佈局
    left_box, right_box = c.cols(2, y=188, h=430, gap=36, weights=[0.95, 1.05])

    # 左側：鼠尾草綠幾何意象卡 + 亞麻底襯疊層
    lx, ly, lw, lh = left_box
    c.rect(lx, ly, lw, lh, rx=16, fill="surface", stroke="border:1")
    c.circle(lx + lw / 2, ly + 175, r=105, fill="accent@0.20", stroke="none")
    c.circle(lx + lw / 2, ly + 175, r=72, fill="accent", stroke="none")
    c.text(lx + lw / 2 - 60, ly + 150, 120, 50, "100%", size=28, bold=True, color="#FFFFFF", align="center", valign="middle")
    c.text_auto(lx + 36, ly + 310, lw - 72, "永續再生亞麻與天然原木材質認證比例", size=14.5, color="ink", align="center", line_height=1.5)

    # 右側：無重框的開放式北歐編輯排版（以細線區隔三個原則）
    rx_x, rx_y, rx_w, rx_h = right_box
    items = [
        ("01  明亮自然光基底", "捨棄純黑與刺眼純白，以 #FAF8F5 燕麥紙色降低長時間閱讀疲勞。", "accent"),
        ("02  低彩度自然色系", "結合鼠尾草綠與霧霾藍點綴重點，營造平靜、可信賴的品牌溫度。", "accent2"),
        ("03  幾何機能排版", "去除多餘裝飾與粗邊框，以精準留白與 1pt 水平線引導視線流動。", "muted"),
    ]

    cur_y = rx_y + 12
    for idx, (heading, body, dot_color) in enumerate(items):
        c.line(rx_x, cur_y, rx_x + rx_w, cur_y, stroke="border:1")
        cur_y += 18
        c.circle(rx_x + 8, cur_y + 11, r=5, fill=dot_color, stroke="none")
        yt = c.text_auto(rx_x + 26, cur_y, rx_w - 26, heading, size=18, bold=True, color="ink")
        yb = c.text_auto(rx_x + 26, yt + 8, rx_w - 26, body, size=14, color="muted", line_height=1.5)
        cur_y = yb + 24

    c.line(rx_x, cur_y, rx_x + rx_w, cur_y, stroke="border:1")
    c.footer("Nordic Minimalism • Sustainable Design Language", slide_num=1, total_slides=total)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"Scandinavian minimalist interior and product photography on warm oat linen background #FAF8F5, natural soft morning window sunlight, sage green #7A8C7E and muted fjord blue #6B8299 ceramic accents, light birch wood texture, calm hygge atmosphere, clean architectural composition, no text"`
