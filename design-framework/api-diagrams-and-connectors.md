# SlideCanvas API Reference: Diagrams, Connectors & Vectors (`api-diagrams-and-connectors.md`)

**單一職責**：專供**系統架構圖、流程拓樸圖與自訂向量圖表**按需讀取。涵蓋節點註冊表（Node Registry）、智慧自動連線（`c.connect()`）與極座標/貝茲/SVG Path 原語。

---

## 一、 Node Registry ＋ 智慧自動連線（`c.connect()`）

繪製系統架構與流程圖時，**禁止手算箭頭起終點座標**！請為節點傳入 `id="..."`，再直接以 ID 連線：

1. **宣告並註冊節點**（支援 `rect`、`pill`、`circle`、`ellipse`，每頁開始時會自動重置註冊表）：
   ```python
   c.rect(100, 220, 220, 90, rx=14, fill="surface", stroke="border:1", text="Ingest", id="ingest")
   c.rect(480, 180, 220, 90, rx=14, fill="surface", stroke="accent:1.5", text="Parser", id="parser")
   c.rect(480, 320, 220, 90, rx=14, fill="surface", stroke="border:1", text="Archive", id="archive")
   ```

2. **呼叫 `c.connect()` 自動選邊與繞線**：
   ```python
   c.connect(
       src_id="ingest",
       dst_id="parser",
       style="ortho",          # "ortho"（正交折線）| "bezier"（三次貝茲曲線）| "straight"（直線）
       from_port="auto",       # "auto" | "top" | "bottom" | "left" | "right"
       to_port="auto",         # "auto" | "top" | "bottom" | "left" | "right"
       stroke="accent:2",      # 支援實線與 "muted:1.5:dash" 虛線
       head_size=9.0,
       label="Raw Stream",     # 可選：自動於中點產生含底襯的標籤膠囊，不壓線
       label_fill="bg",
       arrow=True,
       spread_px=14.0,         # 同一側有多條線時自動微幅錯位防重疊
   )
   ```

- **`ortho` 正交折線行為**：
  - 水平對接（如 `right → left`）：自動算出 3 段式 Z 字折線，並以一體成型實心多邊形渲染，轉角與箭頭絕對置中對齊。
  - 垂直轉水平（如 `bottom → left`）：自動計算 L 型正交折線。
- **`bezier` 平滑曲線行為**：
  - 依出口與入口的法線方向自動推算控制點，適合節點錯落或架構回饋迴路（Feedback Loop）。

---

## 二、 自由向量與極座標圖元（Charts & Custom Visuals）

* **座標輔助**：
  * `polar(cx, cy, r, deg)` → 回傳 `(x, y)` 浮點座標（0° 為正右方，-90° 為正上方 12 點鐘方向）。
  * `lerp(a, b, t)` → 線性內插座標，適合時間軸與等距刻度。
* **基礎線段與手繪箭頭**：
  * `c.line(x1, y1, x2, y2, stroke="border:1")`
  * `c.arrow(x1, y1, x2, y2, stroke="accent:2", head_size=9.0)`（實心一體成型多邊形箭頭）
  * `c.polyline(points, stroke="accent:2", fill="none", closed=False)`
* **曲線與 SVG 路徑**：
  * `c.bezier(p0, p1, p2, p3, stroke="accent:2", fill="none", steps=20)`
  * `c.curve(points, stroke="accent:2", fill="none", closed=False, tension=0.5)`（Catmull-Rom 平滑通過所有控制點）
  * `c.path(d, x=0, y=0, scale=1.0, stroke="accent:2", fill="none")`（支援 SVG `M / L / H / V / C / S / Q / Z` 路徑指令）
* **圓弧與環形圖（Donut Charts / Gauges）**：
  * `c.arc(cx, cy, r, start_deg=0, end_deg=270, stroke="accent:2", fill="none", ry=None)`
  * `c.donut(cx, cy, r, start_deg=-90, end_deg=180, thickness=0.24, fill="accent", stroke="none", ry=None)`

---

## 三、 經典架構圖寫法範例

```python
# 用 cols() 切分 3 階段欄位，再用 id + connect() 串聯
stages = c.cols(3, y=190, h=420, gap=90)
c.rect(stages[0][0], 240, stages[0][2], 90, rx=14, text="API Gateway", id="gw")
c.rect(stages[1][0], 190, stages[1][2], 90, rx=14, text="Auth Worker", id="auth", stroke="accent:1.5")
c.rect(stages[1][0], 330, stages[1][2], 90, rx=14, text="Rate Limiter", id="rl")
c.rect(stages[2][0], 260, stages[2][2], 90, rx=14, text="Core Service", id="core", fill="accent@0.08")

c.connect("gw", "auth", style="ortho", label="JWT")
c.connect("gw", "rl", style="ortho", stroke="muted:1.5:dash", label="Quota")
c.connect("auth", "core", style="bezier", stroke="accent:2")
c.connect("rl", "core", style="bezier", stroke="accent2:2")
```
