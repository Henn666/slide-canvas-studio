# Style Profile: Swiss International Style (`swiss-international`)

**適用場景**：建築與藝術展覽、設計工作室介紹、時尚雜誌專題、強調客觀理性、權威感與高度視覺秩序的企業形象簡報。

---

## 一、 風格色票與字體設定（`PALETTE`）

```python
PALETTE = {
    "bg": "#F4F3EF",        # 瑞士印刷紙張米白（也可改用純白 #FFFFFF）
    "surface": "#FFFFFF",   # 純白區塊或對比區塊
    "ink": "#0A0A0A",       # 極致純黑（巨型標題與格線文字）
    "muted": "#525252",     # 中性深灰（極小尺寸說明內文與編號）
    "border": "#0A0A0A",    # 銳利純黑分割格線（0.75pt~1.5pt）
    "accent": "#E1251B",    # 瑞士國際紅（唯一高純度強調色，點燃視覺張力）
    "accent2": "#0A0A0A",   # 黑白單色輔助
    "font_heading": "Helvetica Neue",  # 或 Arial / PingFang TC
    "font_body": "Helvetica Neue",
    "font_mono": "Menlo",
}
```

---

## 二、 核心視覺規則（SlideCanvas 實作要點）

1. **嚴格數學網格與顯性分割線（Strict Grid & Hairline Rules）**：
   - 不使用任何圓角（一律 `rx=0`）、不使用陰影、不使用漸層。
   - 使用 `c.line(...)` 繪製貫穿畫布的水平與垂直黑色格線（`stroke="border:1"`），所有文字與區塊左緣嚴格對齊格線座標。
2. **極端字級張力與非對稱留白（Extreme Scale Contrast）**：
   - 左側或上方放置超大無襯線標題（`44pt`～`58pt` Bold，緊湊行距 `1.05`～`1.15`），右側或下方搭配極小精緻內文（`11.5pt`～`13pt`）。
   - 故意保留 1～2 個空白網格不填任何文字，展現建築空間感。
3. **紅、黑、白三色紀律**：
   - 95% 面積由紙白與純黑構成，僅在一個關鍵幾何色塊、巨型編號或核心結論使用瑞士紅（`#E1251B`）。

---

## 三、 `SlideCanvas` 完整單頁範例

```python
def slide_swiss_international(c, total):
    c.new_slide(bg="bg")

    # 1. 頂部貫穿式極簡索引欄
    c.text(68, 36, 400, 24, "01 / SWISS TYPOGRAPHIC GRID", size=11, bold=True, color="ink", role="mono")
    c.text(900, 36, 312, 24, "ZÜRICH — 1957 / 2026", size=11, bold=False, color="muted", align="right", role="mono")
    c.line(68, 68, 1212, 68, stroke="border:1.5")

    # 2. 嚴格 3 欄隱形網格座標（左寬右窄非對稱）
    col_l, col_m, col_r = c.cols(3, x=68, y=92, w=1144, h=540, gap=32, weights=[1.5, 1.0, 1.0])

    # 左欄：巨型非對稱標題 + 瑞士紅幾何色塊
    y_h = c.text_auto(
        col_l[0], col_l[1], col_l[2],
        "秩序、客觀\n與網格的張力",
        size=48, bold=True, color="ink", line_height=1.12,
    )
    c.rect(col_l[0], y_h + 28, 160, 160, rx=0, fill="accent", stroke="none")
    c.text(col_l[0] + 18, y_h + 132, 124, 42, "N°01", size=24, bold=True, color="#FFFFFF", role="mono")

    # 垂直分割格線
    c.line(col_m[0] - 16, 92, col_m[0] - 16, 632, stroke="border:0.75")
    c.line(col_r[0] - 16, 92, col_r[0] - 16, 632, stroke="border:0.75")

    # 中欄：上半部刻意留白，下半部放置小字號條列敘事
    c.line(col_m[0], 330, col_m[0] + col_m[2], 330, stroke="border:1")
    ym = c.text_auto(col_m[0], 346, col_m[2], "ASYMMETRIC BALANCE", size=11, bold=True, color="accent", role="mono")
    c.text_auto(
        col_m[0], ym + 10, col_m[2],
        "摒棄對稱構圖與多餘裝飾，透過嚴謹的數學比例與非對稱留白，讓視線依循字級大小自然流動。",
        size=13, color="ink", line_height=1.55,
    )

    # 右欄：數據指標對齊格線頂端與底端
    c.text_auto(col_r[0], col_r[1], col_r[2], "GRID PRECISION", size=11, bold=True, color="muted", role="mono")
    c.stat(col_r[0], col_r[1] + 28, col_r[2], "12 COL", "全域座標對齊基準", val_size=40, val_color="ink", lbl_color="muted")

    c.line(col_r[0], 330, col_r[0] + col_r[2], 330, stroke="border:1")
    yr = c.text_auto(col_r[0], 346, col_r[2], "CHROMATIC DISCIPLINE", size=11, bold=True, color="muted", role="mono")
    c.text_auto(
        col_r[0], yr + 10, col_r[2],
        "• 零圓角（0px Radius）\n• 零陰影、零漸層\n• 高對比純黑與瑞士紅",
        size=13, color="ink", line_height=1.6,
    )

    c.line(68, 650, 1212, 650, stroke="border:1")
    c.footer("INTERNATIONAL TYPOGRAPHIC STYLE", slide_num=1, total_slides=total, line=False)
```

---

## 四、 外部生圖風格錨點（`visual_prompt_anchor`）

> `"Swiss international typographic style poster art on warm off-white paper #F4F3EF, bold geometric black #0A0A0A and Swiss red #E1251B shapes, strict mathematical grid alignment, sharp 90 degree angles, Bauhaus minimalist photography aesthetic, no random text"`
