---
story_id: "STORY-04"
title: "MFQ Trace Chain — M/F/Q/Integrator 贯通新模型"
milestone: "M2"
wave: "W2"
priority: "P0"
status: "verified"
size: "L"
depends_on: ["STORY-03"]
requirements: ["REQ-009", "REQ-010", "REQ-011"]
lld_file: "process/stories/story-04-lld.md"
---

# STORY-04：MFQ Trace Chain — M/F/Q/Integrator 贯通新模型

## 目标

让 M/F/Q 和 `test-point-integrator` 正式消费 `Scenario Chain / Action Source / Knowledge Reference`，形成 v6 追踪链。

## 范围边界

- **包含**：`m-analyzer`、`f-analyzer`、`q-analyzer`、`test-point-integrator`
- **不包含**：方法推荐 reasoning（移交 STORY-05）

## 需求映射

- REQ-009~011
- HLD §6.4 / ADR-2

## 产出物

- `skills/m-analyzer/SKILL.md`
- `skills/f-analyzer/SKILL.md`
- `skills/q-analyzer/SKILL.md`
- `skills/test-point-integrator/SKILL.md`

## 依赖与 Wave

- Wave：W2
- 依赖：STORY-03
- 后续依赖方：STORY-05、STORY-09

## 开发上下文

- 重点不是改变 MFQ 基本方法，而是升级 trace 和输入输出契约。
- 需要确保 LC 可以回链到上游场景与动作源。

## 验证上下文

- TP 与 LC 输出都应保留 trace refs。
- F/Q 不得丢失与 Scenario Chain 的关联。

## 量化验收标准

1. TP 输出可回链到 `Scenario Chain` 与 `Action Source`。
2. LC 输出保留 M/F/Q 来源与覆盖关系。
3. 新追踪链能被 STORY-05 和 STORY-09 直接消费。
