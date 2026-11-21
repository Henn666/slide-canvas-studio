# Style Profile: Apple Minimalist & Glassmorphism (`apple-glassmorphism`)

**適用場景**：科技產品發表、SaaS 軟體介面、高階消費性電子產品展示、追求現代空間深度與光澤質感的簡報。

---

## 一、 風格色票與字體設定（`PALETTE`）

```python
PALETTE = {
    "bg": "#F5F5F7",        # Apple System Gray 6 暖淺灰基底
    "surface": "#FFFFFF",   # 純白半透明毛玻璃卡片底色（常搭配 @0.72~@0.85）
    "ink": "#1D1D1F",       # 曜石深炭黑（主標題與核心內文）
    "muted": "#6E6E73",     # 中性經典灰（眉標、圖說與註釋）
    "border": "#FFFFFF",    # 毛玻璃高光邊框（常搭配 @0.9:1.25）或 #E5E5EA:1
    "accent": "#0071E3",    # Apple 工程藍（主要強調色、CTA 與關鍵線條）
    "accent2": "#5E5CE6",   # Apple 靛藍紫（背景柔和光暈與次要焦點）
    "font_heading": "PingFang TC",  # 英文環境可用 SF Pro Display / Helvetica Neue
    "font_body": "PingFang TC",
    "font_mono": "Menlo",
}
```

---

## 二、 核心視覺規則（SlideCanvas 實作要點）

1. **擬態毛玻璃圖層（Frosted Glass Layers）**：
   - 先用 `c.glow(cx, cy, r, color="accent@0.12", rings=3)` 或柔和漸層圓形鋪在底層作為「背景光源」。
   - 上層卡片使用半透明白底 + 白色高光細框：`fill="surface@0.78", stroke="border@0.95:1.25", rx=22`，營造半透明玻璃懸浮於光源之上的立體層次。
2. **大量留白與平滑圓角（Squircle & Breathing Room）**：
   - 主內容區保留至少 35%～40% 留白；卡片圓角統一設定在 `rx=18`～`24`。
3. **字級對比與極簡排版**：
   - 標題簡潔有力（`30pt`～`34pt` Bold），內文克制（`13.5pt`～`15pt`），避免塞滿文字框。

---

## 三、 `SlideCanvas` 完整單頁範例

```python
def slide_apple_glass(c, total):
    c.new_slide(bg="bg")

    # 1. 背景柔和光源（營造毛玻璃穿透感）
    c.glow(cx=980, cy=320, r=240, color="accent@0.11", rings=3)
    c.glow(cx=340, cy=480, r=190, color="accent2@0.09", rings=3)

    # 2. 頂部留白標題區
    c.header(
        eyebrow="SPATIAL COMPUTING ARCHITECTURE",
        title="輕盈、通透，為專注而生的即時運算介面",
        subtitle="以半透明毛玻璃圖層建立清晰的視覺層級，讓資訊自然浮現於畫布之上",
    )

    # 3. 兩欄半透明毛玻璃主卡片
    cols = c.cols(2, y=195, h=410, gap=28, weights=[1.15, 0.85])
    x1, y1, w1, h1 = cols[0]
    x2, y2, w2, h2 = cols[1]

    # 左側毛玻璃大卡
    c.rect(x1, y1, w1, h1, rx=24, fill="surface@0.78", stroke="border@0.95:1.25")
    c.pill(x1 + 28, y1 + 26, 132, 28, fill="accent@0.12", stroke="accent@0.30:1", text="Core Engine", color="accent")
    y_cur = c.text_auto(x1 + 28, y1 + 72, w1 - 56, "低延遲渲染管線", size=22, bold=True, color="ink")
    c.text_auto(
        x1 + 28, y_cur + 12, w1 - 56,
        "透過獨立背景模糊層與微邊框高光對比，系統能在高密度資訊中維持極低認知負荷。",
        size=14.5, color="muted", line_height=1.5,
    )
    c.stat(x1 + 28, y1 + 265, w1 - 56, "120 Hz", "ProMotion 自適應動態更新率", val_size=48, val_color="accent")

    # 右側雙層堆疊玻璃卡片
    rows = c.rows(2, x=x2, y=y2, w=w2, h=h2, gap=20)
    for idx, (rx_x, rx_y, rx_w, rx_h) in enumerate(rows):
        c.rect(rx_x, rx_y, rx_w, rx_h, rx=22, fill="surface@0.82", stroke="#E5E5EA:1")
        title_txt = "極致留白與字體比例" if idx == 0 else "平滑圓角與微交互"
        desc_txt = "40% 畫布留白搭配銳利深炭黑字體，確保跨螢幕閱讀一致性。" if idx == 0 else "統一 22px 圓角曲率與輕量化狀態膠囊，呈現直覺空間感。"
        yt = c.text_auto(rx_x + 24, rx_y + 24, rx_w - 48, title_txt, size=17, bold=True, color="ink")
        c.text_auto(rx_x + 24, yt + 8, rx_w - 48, desc_txt, size=13.5, color="muted", line_height=1.45)

    c.footer("Source: Design System Spec v2.4", slide_num=1, total_slides=total)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"Apple flagship aesthetic on soft light gray background #F5F5F7, frosted glassmorphism floating cards with subtle white inner glow border, soft ambient blue #0071E3 and indigo #5E5CE6 diffused light spheres behind glass, smooth squircle corners, ultra clean studio product lighting, no random text"`
