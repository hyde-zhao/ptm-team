---
story_id: "STORY-09"
title: "Feedback Adaptation — 变更影响与问题单适配新模型"
milestone: "M6"
wave: "W6"
priority: "P1"
status: "verified"
size: "M"
depends_on: ["STORY-04", "STORY-08"]
requirements: ["REQ-020", "REQ-021"]
lld_file: "process/stories/story-09-lld.md"
---

# STORY-09：Feedback Adaptation — 变更影响与问题单适配新模型

## 目标

让 `change-impact-analyzer` 和 `bug-gap-analyzer` 能消费 v6 的 `Scenario Chain / Action Source / Knowledge Reference / CASE-INDEX`。

## 范围边界

- **包含**：增量范围识别、问题单盲区定位、回链字段、补齐建议
- **不包含**：新的检索能力和交付渲染（由 STORY-08 负责）

## 需求映射

- REQ-020
- REQ-021

## 产出物

- `skills/change-impact-analyzer/SKILL.md`
- `skills/bug-gap-analyzer/SKILL.md`

## 依赖与 Wave

- Wave：W6
- 依赖：STORY-04、STORY-08
- 后续依赖方：开发与验证阶段

## 开发上下文

- 变更分析要识别最小影响范围；
- 问题单分析要能定位遗漏发生在场景、MFQ、设计还是交付环节。

## 验证上下文

- 输出必须能回链到新模型中的对象，而不是只给文本建议。
- 不允许改动未受影响资产。

## 量化验收标准

1. 变更影响输出受影响模块、场景链、LC/PC 范围。
2. 问题单分析输出遗漏环节和补齐资产建议。
3. 两个 Skill 都能消费 `case-index.yaml` 的 trace refs。
