<!-- About 简介（推送后填写到仓库 About 栏）：
海报设计专家：一句话生成手机端可读的海报 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-poster
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, poster-design, graphic-design -->

# lhg-poster：海报设计专家

> **一句话介绍**：一句话生成手机端可读的海报——需求拆解→版式方案→Canvas 确定性绘制（规格锁死）→手机端可读性自检（文字溢出/安全边距/字号下限/对比度/占位符残留，15 条规则），交付可直接导出的规格文件。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-poster
> /plugin install lhg-poster@lhg-plugs
> ```

## 它是什么

`lhg-poster` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"要做海报、
但没有设计师"的小白设计：

- **4 个命令**（小白入口）：`poster` 一句话生成海报（需求→版式→绘制规范→自检），`poster-layout` 单独出可确认的版式方案，`poster-audit` 手机端可读性自检，`poster-export` 导出成品 PNG
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：需求拆解、版式方法论、确定性绘制规范、手机端可读性自检
- **3 个专家 agent**：版式设计师、绘制执行师、手机端质检员
- **1 个硬门 hook**：渲染/导出前自动校验 spec 合法性（可一键豁免，不骚扰）
- **15 条确定性自查规则**：文字溢出、占位符残留、安全边距、字号下限、对比度、配色数量，纯 Python、零第三方依赖，秒级出结果

**路线声明**：本插件走 **"模板 + 精确绘制"**——海报由 HTML/Canvas 按锁死的规格
确定性绘制，**不走纯 AI 生图**。纯 AI 生图的中文文字渲染弱（错字、乱码、排版失控
是常态），AI 图在本插件里只做"背景氛围图"，文字一律由绘制层压字。

工作流：`poster`（一句话全流程）或分段用 `poster-layout` → `poster-audit` → `poster-export`。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-poster:poster` | 一句话生成海报：需求→版式→绘制规范→自检 | `/lhg-poster:poster "三周年庆典海报，11月15号"` |
| `/lhg-poster:poster-layout` | 版式方案：分区/配色/字号层级，用户确认后再画 | `/lhg-poster:poster-layout "招聘海报" --style 简约` |
| `/lhg-poster:poster-audit` | 手机端可读性自检（15 条规则+3 秒测试） | `/lhg-poster:poster-audit ./poster-work/` |
| `/lhg-poster:poster-export` | 导出成品 PNG（须先过审计） | `/lhg-poster:poster-export ./poster-work/ --out 庆典.png` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/poster_audit.py`（15 条规则：规格 3、文字 3、版式 5、信息 4），零 LLM 成本；
2. 再做人工 3 秒测试：成品图缩到 390px 宽看 3 秒——标题 1 秒读懂？遮住品牌名还认得出？CTA 找得到？
3. 渲染/导出前 hook 自动拦一道 spec 合法性，被拦截就修 spec，不要关 hook（紧急放行：`LHG_POSTER_HOOKS_OFF=1`）。

```
lhg-poster/
├── .claude-plugin/          # plugin.json + marketplace.json（source "./"）
├── commands/                # poster / poster-layout / poster-audit / poster-export
├── skills/                  # 4 个平台中立 skill（150+ 行/个）
├── agents/                  # designer / renderer / qa-checker
├── hooks/                   # 渲染前 spec 校验（fail-open + 逃生开关）
├── scripts/audit/           # poster_audit.py（15 条规则，JSON/text 双输出）
├── fixtures/                # bad/good 对照 poster_spec.json
└── smoke_test.py            # 一键冒烟（全绿才发布）
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你要做一张活动/招聘/课程/促销海报，但没有设计师时 → 用 `/lhg-poster:poster`，一句话出可绘制的规格
- 你对版式没把握，想先看方案再决定画不画时 → 跑 `/lhg-poster:poster-layout`，纯文字方案可确认
- 海报画完怕翻车（手机上字太小、字被裁、对比度不够）时 → 跑 `/lhg-poster:poster-audit`，15 条规则+3 秒测试
- 你要给团队立"海报发布前必须过检"的纪律时 → 它的 hook 硬门与审计脚本开箱即用

**什么时候不用：**

- 你要的是纯艺术海报/插画风主视觉（文字很少、重创意表达）时 → 本插件是"信息型海报"专家，艺术海报请找设计师或纯 AI 生图
- 你已有设计师出稿，只想快速改几个字时 → 直接改 spec 重出，不必走全流程
- 你的海报主要投放在 PC 端大屏（如发布会背景板）时 → 本插件所有标准（字号下限/边距）都是按手机端定的，大屏场景不适用

**风险点诚实说明：**

- **不走纯 AI 生图是刻意选择**：纯 AI 生图的中文文字经常错字乱码，本插件用"模板+精确绘制"保证文字 100% 准确；代价是艺术感上限不如纯生图，背景氛围可另外用 AI 图补
- **审美有上限**：插件保证"手机端可读、不翻车"，不保证"获奖级设计"；版式方案需要用户确认，机器不代拍板
- **错别字是最高风险**：海报发出去错一个字品牌损伤不可逆，所以质检里有"电话逐位核对+脱离版式通读"两道人工关，不要跳过
- **导出依赖无头浏览器**：`poster-export` 需要本机有可用的浏览器截图能力，没有就先导出 HTML 用浏览器手动截图（spec 本身不受影响）

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-poster](https://github.com/lhg-plugs/lhg-poster) | 海报设计专家：一句话生成手机端可读的海报 | `/plugin install lhg-poster@lhg-plugs` |
| [lhg-geo](https://github.com/lhg-plugs/lhg-geo) | AI搜索优化专家：让品牌在AI搜索中被看见 | `/plugin install lhg-geo@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、15 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-poster/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 插件组织：https://github.com/lhg-plugs —— 小白专家插件矩阵
