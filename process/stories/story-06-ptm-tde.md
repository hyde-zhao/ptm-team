---
story_id: "STORY-06"
title: "Graph Design Pack — process-design + state-design"
milestone: "M4"
wave: "W4"
priority: "P0"
status: "verified"
size: "L"
depends_on: ["STORY-05"]
requirements: ["REQ-013", "REQ-017"]
lld_file: "process/stories/story-06-lld.md"
---

# STORY-06：Graph Design Pack — `process-design` + `state-design`

## 目标

把流程图法和状态图法统一升级为 **完整过程输出**，并复用图形链共享骨架。

## 范围边界

- **包含**：`process-design`、`state-design`
- **不包含**：参数 / 数据 / 组合设计（移交 STORY-07）

## 需求映射

- REQ-013
- REQ-017

## 产出物

- `skills/process-design/SKILL.md`
- `skills/state-design/SKILL.md`

## 依赖与 Wave

- Wave：W4
- 依赖：STORY-05
- 后续依赖方：STORY-08

## 开发上下文

- 两个 Skill 都需要图示、路径枚举、覆盖策略和 PC 输出。
- 可复用 Mermaid 和路径枚举表的共享写法。

## 验证上下文

- 流程图和状态图必须都能落成中间过程产物。
- path / transition coverage 要与 PC 建立追踪。

## 量化验收标准

1. `process-design` 输出流程图、路径枚举、覆盖策略、触发数据、PC。
2. `state-design` 输出状态图、迁移表、守卫条件、触发数据、PC。
3. 两个 Skill 的物理用例字段骨架保持一致。
