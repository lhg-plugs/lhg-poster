---
description: 导出成品：按锁死的 spec.json 用 HTML/Canvas 渲染导出 PNG（1080x1920/1080x1080），附分享话术。
argument-hint: <spec所在目录> [--out 海报.png]
---

# /lhg-poster:poster-export —— 导出成品

用户输入在 `$ARGUMENTS` 中：`<spec 所在目录> [--out 海报.png]`。

前置条件：`poster-audit` 已通过（审计零 blocker + 人工 3 秒测试通过）。
没过审计不许导出——先修 spec。

## 流程

### 1. 生成渲染页
- 按 `lhg-poster-render` 第 4 节的 HTML 模板，把 `poster_spec.json`
  的每个元素翻译成绝对定位的 DOM/Canvas 绘制指令。
- 背景图（如有）只做氛围，文字全部由绘制层压字（路线红线）。

### 2. 渲染导出
- 用无头浏览器截图导出 PNG（宽度按 spec canvas 宽度，默认 1080）。
- 导出前 hook 会自动校验 spec 合法性，被拦截就修 spec，不要关 hook。

### 3. 交付
- 成品 PNG + spec.json（留档，下次改字直接改 spec 重出）。
- 附一条分享话术（标题+简介，30 字内，用户直接复制发朋友圈/小红书）。

## 硬规则
- 导出 PNG 与 spec 必须一致：不许在渲染页上手调样式，调就回 spec 改。
- 成品图放大 200% 抽查文字边缘：发虚/锯齿严重就换渲染方式重出。
