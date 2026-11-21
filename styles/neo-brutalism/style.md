# Style Profile: Neo-Brutalism (`neo-brutalism`)

**適用場景**：Web3 與新創科技品牌、潮流服飾與創意行銷提案、獨立開發者工具（DevTools）、針對年輕受眾的叛逆高張力簡報。

---

## 一、 風格色票與字體設定（`PALETTE`）

```python
PALETTE = {
    "bg": "#FFFDF5",        # 高明度奶油米白底（讓螢光撞色更跳脫）
    "surface": "#FFFFFF",   # 純白卡片底色
    "ink": "#000000",       # 100% 純黑文字與粗邊框
    "muted": "#3F3F46",     # 深鐵灰副標（在粗黑風格中仍須維持高對比）
    "border": "#000000",    # 必備純黑實線粗邊框（2.5pt~3.5pt）
    "accent": "#FFDE00",    # 螢光亮黃（High-voltage Yellow）
    "accent2": "#3B82F6",   # 電光藍（Electric Blue，亦可替換為亮粉紅 #FF4D8D）
    "font_heading": "Arial Black",  # 或 PingFang TC Bold / Impact
    "font_body": "PingFang TC",
    "font_mono": "Menlo",           # 等寬字體用於標籤、數據與強調標記
}
```

---

## 二、 核心視覺規則（SlideCanvas 實作要點）

1. **粗黑框 ＋ 零模糊純黑硬陰影（Thick Border + Hard Shadow）**：
   - 在 `SlideCanvas` 中，任何卡片或按鈕都先畫一個向右下偏移 `(+6, +6)` 的純黑矩形作為硬陰影：
     ```python
     c.rect(x + 6, y + 6, w, h, rx=0, fill="#000000", stroke="none")
     c.rect(x, y, w, h, rx=0, fill="accent", stroke="#000000:3")
     ```
   - 陰影必須是 **100% 不透明純黑、零模糊、銳利邊緣**。
2. **高飽和撞色區塊（High-Saturation Color Blocking）**：
   - 卡片底色直接大膽使用螢光黃 `#FFDE00`、亮粉 `#FF88D1`、薄荷電光綠 `#80FF72` 或電光藍 `#3B82F6`（搭配深色時注意字色改為純白 `#FFFFFF`，亮色底一律配純黑 `#000000` 字以保高對比）。
3. **等寬字體徽章與尖銳直角**：
   - 標籤使用直角矩形（`rx=0` 或極微 `rx=4`）搭配 `font_mono` 全大寫文字，營造街頭海報與獨立工具的直接感。

---

## 三、 `SlideCanvas` 完整單頁範例

```python
def _brutal_card(c, x, y, w, h, fill="surface", offset=6, border_w=3):
    """Draw a Neo-Brutalism card with a crisp offset hard shadow and thick black border."""
    c.rect(x + offset, y + offset, w, h, rx=0, fill="#000000", stroke="none")
    c.rect(x, y, w, h, rx=0, fill=fill, stroke=f"#000000:{border_w}")


def slide_neo_brutalism(c, total):
    c.new_slide(bg="bg")

    # 頂部螢光黃衝擊標籤
    _brutal_card(c, 68, 38, 220, 32, fill="accent", offset=4, border_w=2.5)
    c.text(68, 38, 220, 32, "BUILD_FAST // V2.0", size=12, bold=True, color="#000000", align="center", valign="middle", role="mono")

    c.text_auto(68, 86, 1144, "拒絕平庸：高張力硬陰影與撞色視覺系統", size=34, bold=True, color="ink")

    # 三欄撞色便當卡片
    cards = c.cols(3, y=175, h=430, gap=28)
    card_specs = [
        ("#FFDE00", "#000000", "01 / 零模糊硬陰影", "6px 純黑偏移陰影搭配 3pt 實線粗框，讓每個模組像實體貼紙一樣彈出畫面。", "300%"),
        ("#FF4D8D", "#000000", "02 / 飽和霓虹撞色", "跳脫企業藍灰安全區，大膽運用電光粉、亮黃與電光藍搶佔年輕受眾注意力。", "0.4s"),
        ("#3B82F6", "#FFFFFF", "03 / 叛逆等寬排版", "結合街頭海報的粗體標題與 Monospace 系統標籤，直接傳達開發者工具個性。", "100%"),
    ]

    for (cx, cy, cw, ch), (bg_hex, txt_hex, title, desc, metric) in zip(cards, card_specs):
        _brutal_card(c, cx, cy, cw, ch, fill=bg_hex, offset=7, border_w=3)
        yt = c.text_auto(cx + 24, cy + 28, cw - 48, title, size=20, bold=True, color=txt_hex, role="mono")
        c.line(cx, yt + 14, cx + cw, yt + 14, stroke="#000000:2.5")
        c.text_auto(cx + 24, yt + 30, cw - 48, desc, size=14.5, bold=False, color=txt_hex, line_height=1.5)

        # 底部數據徽章
        _brutal_card(c, cx + 24, cy + ch - 110, cw - 48, 80, fill="#FFFFFF", offset=4, border_w=2.5)
        c.text(cx + 24, cy + ch - 110, cw - 48, 80, metric, size=34, bold=True, color="#000000", align="center", valign="middle", role="mono")

    c.footer("NEO-BRUTALISM SYSTEM • NO BLUR, NO MERCY", slide_num=1, total_slides=total)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"neo-brutalism graphic design aesthetic on warm cream background #FFFDF5, bold thick 4px black borders #000000, sharp offset black hard shadows with zero blur, vibrant neon yellow #FFDE00, hot pink #FF4D8D and electric blue #3B82F6 flat color blocks, retro terminal UI stickers, no random text"`
