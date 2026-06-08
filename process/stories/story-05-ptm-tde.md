---
story_id: "STORY-05"
title: "Design Planner — CAE→PPDCS 完整推断与设计计划"
milestone: "M3"
wave: "W3"
priority: "P0"
status: "verified"
size: "M"
depends_on: ["STORY-04"]
requirements: ["REQ-012"]
lld_file: "process/stories/story-05-lld.md"
---

# STORY-05：Design Planner — CAE→PPDCS 完整推断与设计计划

## 目标

让 `design-planner` 输出完整 reasoning：主信号、候选特征、排除理由、推荐方法及其与场景链的对应关系。

## 范围边界

- **包含**：`design-planner` 输出结构、reasoning 文件、确认输入
- **不包含**：五类设计 Skill 的具体专化实现（移交 STORY-06/07）

## 需求映射

- REQ-012

## 产出物

- `skills/design-planner/SKILL.md`
- `agents/ptm-tde.md`

## 依赖与 Wave

- Wave：W3
- 依赖：STORY-04
- 后续依赖方：STORY-06、STORY-07

## 开发上下文

- reasoning 需要兼顾人类审阅与下游 Skill 消费。
- 混合特征必须显式写主 / 辅，不得模糊归类。

## 验证上下文

- 每条 LC 都应给出可审计的推断过程。
- 场景链与推荐方法之间要存在显式映射字段。

## 量化验收标准

1. 每条 LC 都有 reasoning。
2. reasoning 至少包含主信号、候选项、排除理由、推荐方法。
3. 输出可直接作为 STORY-06/07 的输入。
