<!-- About 简介（推送后填写到仓库 About 栏）：
海报设计专家：一句话生成手机端可读的海报——需求拆解→版式方案→确定性绘制规范→手机端可读性自检（文字溢出/安全边距/字号下限/对比度），15条审计规则。 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-poster
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, poster-design, graphic-design, poster, layout, canvas -->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="lhg-poster — 海报设计专家">
</p>

> **一句话介绍**：海报设计专家：一句话生成手机端可读的海报——需求拆解→版式方案→确定性绘制规范→手机端可读性自检（文字溢出/安全边距/字号下限/对比度），15条审计规则。

**一键安装**：在 Claude Code 里运行

```bash
/plugin marketplace add lhg-plugs/lhg-poster
/plugin install lhg-poster@lhg-plugs
```

## 它能帮你做出什么

- **冒烟全绿**：`python3 smoke_test.py` 49 项全部通过（JSON 合法、frontmatter 完整、命令/skill/agent 齐全）。

## 它是什么

`lhg-poster` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **4 个命令**（小白入口）：`poster` 海报主入口、`poster-audit` 海报自检、`poster-export` 导出成品、`poster-layout` 版式方案
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：lhg-poster-brief, lhg-poster-layout, lhg-poster-mobile, lhg-poster-render
- **3 个专家 agent**：designer, qa-checker, renderer
- **1 个 hooks**（`hooks/`：validate_spec_before_render.py），关键操作前自动把关

## 为什么是它

不是一个 prompt，而是一套互相兜底的机制：

1. **硬门，不是提醒**：hooks 在关键操作前自动拦截或警告（见 `hooks/`），而不是只在文档里写一句"请注意"。
2. **方法论沉淀在 skill 里**：流程、检查清单、口径都写在 `skills/` 的方法论里，命令只是入口；换个 agent 平台也能复用同一套做法。
3. **可验，不是可信**：`fixtures/` 备有坏/好对照用例，`smoke_test.py` 一键验证，规则有没有生效、自己跑一遍就知道。

## 快速上手

```bash
# 1. 安装（Claude Code 里运行）
/plugin marketplace add lhg-plugs/lhg-poster
/plugin install lhg-poster@lhg-plugs

# 2. 海报主入口：一句话需求→信息拆解→版式方案→绘制规范（spec.json）→手机
/lhg-poster:poster "三周年庆典海报，11月15号"
```

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-poster:poster` | 海报主入口：一句话需求→信息拆解→版式方案→绘制规范（spec.json）→手机端可读性自检，交付可绘制的规格文件。 | `/lhg-poster:poster "三周年庆典海报，11月15号"` |
| `/lhg-poster:poster-audit` | 海报自检：15 条确定性规则查文字溢出/安全边距/字号下限/对比度/占位符残留，输出手机端可读性报告。 | `/lhg-poster:poster-audit ./poster-work/` |
| `/lhg-poster:poster-export` | 导出成品：按锁死的 spec.json 用 HTML/Canvas 渲染导出 PNG（1080x1920/1080x10… | `/lhg-poster:poster-export ./poster-work/ --out 庆典.png` |
| `/lhg-poster:poster-layout` | 版式方案：按信息优先级输出分区/配色/字号层级说明，用户确认后再进绘制。 | `/lhg-poster:poster-layout "招聘海报" --style 简约` |

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你需要海报主入口时 → 用 `/lhg-poster:poster`
- 你需要海报自检时 → 用 `/lhg-poster:poster-audit`
- 你需要导出成品时 → 用 `/lhg-poster:poster-export`

**什么时候不用：**

- 你只需要其中一个零散能力时 → 本插件是成套流程，单点需求用更轻量的 skill 更合适
- 你希望 AI 完全自由发挥、不接受任何自查与硬门时 → 它的规则审计与 hooks 会介入（可关，但那就别装它）
- 你的场景不在上面命令表覆盖范围内时 → 先看命令表，没有对应命令就别硬套

## 目录结构

```
lhg-poster/
├── smoke_test.py          # 一键冒烟测试
├── ATTRIBUTION.md         # 灵感来源与许可声明
├── LICENSE                # MIT
├── README.md              # 本文件
├── .claude-plugin/
├── agents/
├── commands/
├── fixtures/
├── hooks/
├── scripts/
├── skills/
```

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（本次实测 49 项全部通过）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-poster/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

同门插件见 [lhg-plugs](https://github.com/lhg-plugs)，86 个插件的完整矩阵在 [marketplace](https://github.com/lhg-plugs/marketplace) 维护。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
