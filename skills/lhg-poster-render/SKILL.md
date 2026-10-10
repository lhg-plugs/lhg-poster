---
name: lhg-poster-render
description: 确定性绘制规范：poster_spec.json 字段定义、坐标系、字号换算、HTML/Canvas 渲染模板，规格锁死、不留模糊。
license: MIT
compatibility: 平台中立（Claude Code / 豆包 / Workbuddy 等支持 skill 的智能体均可使用）
metadata:
  version: 1.0.0
  domain: poster
---

# lhg-poster-render：确定性绘制规范

## 何时使用

- 版式方案已获用户确认，要把它翻译成机器可执行的 `poster_spec.json` 时。
- 导出 PNG 前，生成 HTML 渲染页时。

**路线红线**：本插件走"模板+精确绘制"——海报由 HTML/Canvas 按 spec 确定性绘制，
**不走纯 AI 生图**（纯 AI 生图的中文文字渲染弱：错字、乱码、排版失控是常态）。
AI 生图只许做"背景氛围图"，文字一律由绘制层压字。

## 输入输出

**输入**：用户确认的版式方案 + 需求清单。

**输出**：`poster_spec.json`（锁死的绘制规格）+ 可选的渲染 HTML 模板。

## 分步方法论

### 第 1 步：spec 字段规范

```json
{
  "canvas": {"width": 1080, "height": 1920, "background": "#FFF8F0"},
  "brand": "蓝V互助大街",
  "palette": ["#1A1A1A", "#FFF8F0", "#E63946", "#FFFFFF"],
  "info": {"title": "...", "date_time": "2026-11-15 19:00", "contact": "微信：lhgsmsw"},
  "elements": [
    {"id": "title", "type": "text", "role": "title",
     "x": 80, "y": 120, "w": 920, "h": 240,
     "text": "蓝V互助大街三周年庆典",
     "font_size": 88, "color": "#1A1A1A", "bg": "#FFF8F0", "layer": 2},
    {"id": "bgimg", "type": "image",
     "x": 0, "y": 0, "w": 1080, "h": 1920,
     "source": "自制背景（AI 氛围图 + 品牌色压暗）", "layer": 0}
  ]
}
```

字段规则：

- 坐标系：左上角原点，单位 px，x/y/w/h 全是整数。
- `role`：title（标题）/ body（正文）/ caption（注释），决定字号下限。
- `layer`：数字越大越上层；文字层必须在装饰层之上。
- `type: image` 必须写 `source`（自制/AI 生成/已购版权），无来源不许用。
- `info` 三项（title/date_time/contact）至少填两项，全空不许绘制。

### 第 2 步：字号换算

以 1080 宽画布为基准字号，换画布按比例缩放：

```text
实际字号 = 基准字号 × (canvas.width / 1080)
```

基准：标题 88、正文 44、注释 32。
红线（1080 宽）：正文 < 40px 不许绘制（手机端看不清）。

### 第 3 步：安全边距

文字元素四边距画布边缘 ≥ 4% 画布宽（1080 宽 = 43px）。
装饰性图片可铺满，但文字不行——贴边的字在手机圆角屏下会被裁。

### 第 4 步：渲染 HTML 模板

```html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  .poster { position: relative; width: 1080px; height: 1920px;
            background: #FFF8F0; overflow: hidden; }
  .el { position: absolute; }
</style></head>
<body>
<div class="poster">
  <!-- 背景图层 -->
  <img class="el" src="bg.png"
       style="left:0;top:0;width:1080px;height:1920px;z-index:0">
  <!-- 标题：spec 的 title 元素 1:1 还原 -->
  <div class="el" style="left:80px;top:120px;width:920px;height:240px;
       z-index:2;font-size:88px;color:#1A1A1A;line-height:1.35;">
    蓝V互助大街三周年庆典
  </div>
</div>
</body></html>
```

模板纪律：

1. 渲染页必须 1:1 还原 spec——**不许在渲染页上手调样式**，
   要调就回 spec 改，保证"spec 即真相"。
2. 中文必须设 `line-height: 1.35` 以上，行距太小手机端糊。
3. 导出截图宽度 = canvas.width，不许缩放导出（缩放藏问题）。

### 第 5 步：写完必自检

```text
python3 scripts/audit/poster_audit.py --target <目录> --format text
```

15 条规则全绿才交棒。有 blocker 就地修 spec，不要关 hook。

## 字号速查表（1080 宽基准）

| 用途 | 基准字号 | 红线 | 说明 |
|---|---|---|---|
| 主标题 | 88 | ≥72（warning） | 一屏只许一个 |
| 副标题 | 64 | — | 可选，没有不硬加 |
| 正文 | 44 | ≥40（blocker） | 时间/地点/卖点都算正文 |
| CTA | 48 | ≥40（blocker） | 必须 ≥ 正文，要跳出来 |
| 注释 | 32 | — | 能少则少，超过 2 处就减 |

换算 1242 宽画布：全部 ×1.15；换算 1080x1080 方形：字号不变，
但信息区砍掉一条卖点（方形高度不够）。

## AI 配图使用规范

- AI 图只做背景氛围：风景、纹理、光影，不许带文字。
- 生成提示词里加"no text, no words, no letters"（中文生图模型也尽量加）。
- AI 图上有文字残留 → 废弃重生，不许"将就用"。
- 背景图必须压暗/加罩（保证文字对比度 ≥3:1），原图直铺是大忌。

## 反模式

- ❌ 纯 AI 生图直接当成品发（错字海报发出去，品牌损伤不可逆）。
- ❌ 在渲染页上手调样式（spec 与成品分叉，下次改字全乱）。
- ❌ spec 里留 `{{占位符}}`（hook 会拦截，但就不该写进去）。
- ❌ 背景图直铺不压暗（文字对比度归零，手机强光下全瞎）。
- ❌ 导出时缩放截图（1080 的图缩成 540 导出，瑕疵全被藏起来）。

## 自检与反馈

**质检门**（spec 交付前自查）：

- [ ] 所有坐标/字号是整数，无"大概""差不多"
- [ ] 文字层 layer 高于装饰层
- [ ] image 元素都有 source 标注
- [ ] 审计脚本 15 条规则零 blocker
- [ ] spec 与渲染页 1:1 一致（无手调）

**标准冒烟用例**：用插件 `fixtures/bad/poster_spec.json` 跑审计，
应命中 PST-TEXT-001/002、PST-CONTRAST-001、PST-FONT-001 等 blocker；
用 `fixtures/good/poster_spec.json` 跑，应零 blocker。

**一键反馈**：发现渲染与 spec 不一致的新坑（如某字体行高异常），
到本仓库提 issue，标题格式 `[render] 一句话描述`，附上 spec 片段与截图。

## 出品：刘洪光

本 skill 由刘洪光出品，更多 skill 与插件见 https://github.com/lhg-skills
（插件组织：https://github.com/lhg-plugs）。
