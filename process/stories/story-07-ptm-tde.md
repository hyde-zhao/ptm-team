---
story_id: "STORY-07"
title: "Rule/Data Design Pack — parameter/data/combination"
milestone: "M4"
wave: "W4"
priority: "P0"
status: "verified"
size: "XL"
depends_on: ["STORY-05"]
requirements: ["REQ-014", "REQ-015", "REQ-016"]
lld_file: "process/stories/story-07-lld.md"
---

# STORY-07：Rule/Data Design Pack — `parameter` / `data` / `combination`

## 目标

把参数规则、数据范围、组合压缩三类设计 Skill 升级为完整过程输出，并统一表格式骨架。

## 范围边界

- **包含**：`parameter-design`、`data-design`、`combination-design`
- **不包含**：图形链方法（移交 STORY-06）

## 需求映射

- REQ-014~016

## 产出物

- `skills/parameter-design/SKILL.md`
- `skills/data-design/SKILL.md`
- `skills/combination-design/SKILL.md`

## 依赖与 Wave

- Wave：W4
- 依赖：STORY-05
- 后续依赖方：STORY-08

## 开发上下文

- 三个 Skill 都要补齐“输入分析 → 过程表 → 数据/组合策略 → PC”链路。
- `combination-design` 需要保留外部工具不可用时的明确回退。

## 验证上下文

- 判定表、等价类/边界值、因子组合结果都必须可追溯。
- 输出不能只给最终物理用例。

## 量化验收标准

1. `parameter-design` 输出规则提取、约束关系、判定结构、触发参数组、PC。
2. `data-design` 输出取值范围、等价类、边界策略、选点策略、PC。
3. `combination-design` 输出因子范围、压缩策略、约束条件、组合结果、PC。
