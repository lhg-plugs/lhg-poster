---
description: 海报自检：15 条确定性规则查文字溢出/安全边距/字号下限/对比度/占位符残留，输出手机端可读性报告。
argument-hint: <spec所在目录>
---

# /lhg-poster:poster-audit —— 海报自检

用户输入在 `$ARGUMENTS` 中：`<spec 所在目录>`（含 `poster_spec.json`）。

加载 `lhg-poster-mobile`（手机端可读性标准）。

## 流程

### 1. 跑确定性审计
```text
python3 scripts/audit/poster_audit.py --target <目录> --format text
```
15 条规则，秒级出结果。blocker 必须修，warning 建议修，nit 看情况。

### 2. 人工手机端评审（机器查不出的）
- 把渲染图缩到手机宽度（~390px CSS 像素）看 3 秒：标题能不能一秒读懂？
- 遮住品牌名还能认出是谁家的吗？（品牌识别度）
- CTA（扫码/电话/链接）在缩略图里找得到吗？

### 3. 输出报告
- 审计结果 + 人工评审结论 + 修改清单（按 blocker→warning 排序）。
- 全部通过才算"可交付"。

## 硬规则
- 审计有 blocker 时不许说"差不多能用"，必须修完重跑。
- 人工评审 3 秒测试没过，版式打回重做，不许靠"调字号"硬救。
