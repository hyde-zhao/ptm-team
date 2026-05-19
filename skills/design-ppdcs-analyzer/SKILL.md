---
name: design-ppdcs-analyzer
description: >-
  PPDCS 设计协调：读取设计计划并为每个逻辑用例调用对应 PPDCS 方法 Skill，
  统一输出 design/ppdcs 与 design/pc 的单文件产物。
  触发词包括：PPDCS设计、逻辑用例设计、单文件设计、design/ppdcs、design/pc。
  适用场景：MFQ design 阶段，design-planner 已确认后。
argument-hint: "可选：logic_case_id=<LC-ID>"
user-invokable: true
status: active
---

## 目标

作为 design 阶段的协调 Skill，确保五类 PPDCS 方法产物遵循统一文件布局：

- `design/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`
- `design/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`

不再使用 `design/<module>/<sub-module>/<LC-ID>/` 深目录。

## 输入

| 输入 | 路径 |
|---|---|
| 设计计划 | `analysis/integration/design-plan.md` |
| 推断明细 | `analysis/plan/design-planner-reasoning.md` |
| 逻辑用例 | `analysis/integration/logic-cases.md` |
| 测试数据 | `analysis/integration/test-data.md` |
| 场景链 | `analysis/scenarios/confirmed-scenarios.md` |

## 调用关系

| PPDCS 特征 | 调用 Skill | PPDCS 文件内容 |
|---|---|---|
| P-Process | `process-design` | 流程图、路径枚举、覆盖策略、触发数据 |
| P-Parameter | `parameter-design` | factor catalog、规则、判定表、data row |
| D-Data | `data-design` | 等价类、边界值、独立性检查、实际取值 |
| C-Combination | `combination-design` | 因子表、约束、Pairwise/正交、组合覆盖 |
| S-State | `state-design` | 状态图、迁移表、守卫条件、迁移路径 |

## 文件命名规则

文件名必须由四段组成：

```text
<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
```

规则：

1. 每段来自已确认的目录结构和 LC 标题。
2. 去除路径分隔符、控制字符和首尾空白。
3. 同名冲突时追加 `-<LC-ID>`。
4. `design/ppdcs/` 与 `design/pc/` 使用同一个 basename。

## 输出契约

### PPDCS 过程文件

`design/ppdcs/<basename>.md` 至少包含：

1. LC 基本信息与 trace；
2. design-planner 推荐与 reasoning；
3. 对应 PPDCS 方法的完整五步设计过程；
4. 未确认事实与 gap 原样透传；
5. 指向 PC 文件的相对路径。

### PC 文件

`design/pc/<basename>.md` 至少包含：

1. LC 基本信息与 trace；
2. 物理用例 16 列总表；
3. 每条 PC 回链到 `requirement_ids / logic_case_id / trace_refs / scenario_refs / action_source_refs / factor_refs / fact_status`；
4. 指向 PPDCS 过程文件的相对路径。

## Gotchas

- 五个方法 Skill 可以负责方法细节，但最终文件布局必须由本 Skill 收敛。
- 同一个 LC 只能有一个 PPDCS 文件和一个 PC 文件。
- `needs-confirmation` 不得在设计阶段被静默改成 confirmed。
- 不生成 case-index 或工具分析表；当前最终交付只保留测试方案和测试用例两份 Markdown。

## 验收标准

- [ ] 每个目标 LC 在 `design/ppdcs/` 有且只有一个过程文件
- [ ] 每个目标 LC 在 `design/pc/` 有且只有一个 PC 文件
- [ ] 文件名符合 `<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`
- [ ] 不创建 `design/<module>/<sub-module>/` 深目录
