# Native Elements vs. External Visual Asset Policy (`native-vs-visual-policy.md`)

**單一職責**：明確界定哪些視覺直接由 `SlideCanvas` 原生向量繪製，哪些情境才經 `fit_visual_asset.py` 引入外部點陣圖檔 `c.image()`。

---

## 一、 原生向量優先原則（Native-First Principle）

**預設 85% 以上的版面與資訊圖表應由 `SlideCanvas` 原生 OpenXML 元件完成**（`text_auto`、`rect`、`circle`、`donut`、`arc`、`bezier`/`curve`、`path`、`table`）。

### 以下內容「嚴禁」轉為外部圖片，必須維持原生可編輯：
- 所有標題、眉標、條列文字與頁尾頁碼框。
- 數據對照表（使用 `c.table(...)` 原生極簡無直分隔線表格）。
- 巨型 KPI 數字與統計圖表（使用 `c.stat(...)` 及 Python 迴圈繪製的直條/折線/環形/極座標圖）。
- 流程圖、狀態機、架構拓撲與貝茲引導線（使用 `c.bezier`、`c.curve`、`c.path`、`c.arrow`）。

---

## 二、 何時才引入外部圖片（`c.image()`）？

僅在以下 **3 種原生幾何難以表達的情境**，才生成或嵌入外部圖片：

1. **真實產品／系統介面截圖（UI / Hardware / Photo）**：例如實際軟體畫面、硬體照片或攝影素材。
2. **高複雜度 3D / 等距視角（Isometric）或插畫風主視覺**：純概念氛圍插畫。
3. **外部既有的超大型 PNG/JPG 架構圖**。

---

## 三、 外部圖片裁切校準（`fit_visual_asset.py`）

引入外部圖片前：
1. **禁止依賴圖內文字**：生圖應保持無文字純淨視覺，所有標籤一律用 `c.text()` / `c.text_auto()` 疊加。
2. **強制比例校準**：在呼叫 `c.image(path, x, y, w, h)` 前，先執行 `scripts/fit_visual_asset.py` 將圖片裁切／縮放至目標比例，杜絕圖片被拉伸變形。
