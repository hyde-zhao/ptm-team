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

## 拓扑绑定输入契约

design-ppdcs-analyzer 必须消费 LC 中由 integrator 生成的 `topology_bindings`，不得在 design 阶段重新发明 DUT/TG/接口/link 绑定。

| 输入字段 | 来源 | 用途 |
|---|---|---|
| `topology_bindings` | `analysis/integration/logic-cases.md` 的“组网绑定（来自 confirmed-scenarios.md）”章节 | 为 PPDCS 过程和 PC 提供真实组网对象回链 |
| `topology_role_refs` | LC trace refs | 保留测试逻辑位置约束 |
| `topology_refs` | LC trace refs / confirmed-scenarios.md | 回链 TOPO 实例 |
| `topology_gap_refs` / `confirmation_gap_refs` | TP/LC 透传 | 保留缺失、不唯一或冲突绑定 |

三层概念必须保持分离：
- 测试因子 = 业务/配置/数据/报文取值，继续消费 `factor_bindings`。
- 拓扑角色 = 测试逻辑位置，只作为 PPDCS/PC 的前置与动作位置约束。
- 真实组网对象 = confirmed-scenarios.md TOPO 实例，只能通过 LC `topology_bindings` 使用。

若 LC 缺少必需拓扑绑定，或绑定状态不是 `confirmed`，PPDCS/PC 可以生成草案，但相关 PC 的 `fact_status` 必须为 `needs-confirmation`，并透传 gap。

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
5. LC `topology_bindings` 原样透传，并说明拓扑角色如何作为前置/动作位置约束；
6. 指向 PC 文件的相对路径。

### PC 文件

`design/pc/<basename>.md` 至少包含：

1. LC 基本信息与 trace；
2. 物理用例 16 列总表；
3. 每条 PC 回链到 `requirement_ids / logic_case_id / trace_refs / scenario_refs / action_source_refs / factor_bindings / factor_refs / topology_bindings / topology_role_refs / topology_refs / fact_status`；
4. 指向 PPDCS 过程文件的相对路径。

## 拓扑绑定校验

生成每个 PPDCS/PC 文件前必须执行以下校验，并把结论写入 PPDCS 过程文件：

| 检查项 | 通过条件 | 失败处理 |
|---|---|---|
| LC 绑定来源 | 每个 `topology_binding_id` 均来自 LC “组网绑定（来自 confirmed-scenarios.md）”章节 | 标记 `needs-confirmation`，写入 `confirmation_gap_refs` |
| TOPO 回链 | `topology_ref / binding_source` 可回链 `analysis/scenarios/confirmed-scenarios.md` | 不得把真实端口写入 confirmed PC；降级 `fact_status` |
| PC 端口使用 | PC 中出现的 `DUT.port* / TG.port* / link` 均能回链 LC `topology_bindings` 和 confirmed-scenarios.md | 记录拓扑绑定错误，不得静默通过 |
| 因子分层 | `factor_bindings` 不包含拓扑角色或真实组网对象 | 标记设计输入污染，相关 PC `needs-confirmation` |

PC 表中若需要展示真实端口，只能来自 `topology_bindings.bound_object`，并同时保留 `topology_binding_id`；不得从动作文本或角色名直接推断。

## Gotchas

- 五个方法 Skill 可以负责方法细节，但最终文件布局必须由本 Skill 收敛。
- 同一个 LC 只能有一个 PPDCS 文件和一个 PC 文件。
- `needs-confirmation` 不得在设计阶段被静默改成 confirmed。
- 不生成 case-index 或工具分析表；当前最终交付只保留测试方案和测试用例两份 Markdown。
- PPDCS/PC 消费 LC `topology_bindings`，不重新推断组网绑定。
- 真实端口可以出现在 PC 执行步骤中，但必须可回链到 LC 绑定和 confirmed-scenarios.md。
- 拓扑角色只约束测试位置，不是 D-Data/C-Combination/P-Parameter 的测试因子。

## 验收标准

- [ ] 每个目标 LC 在 `design/ppdcs/` 有且只有一个过程文件
- [ ] 每个目标 LC 在 `design/pc/` 有且只有一个 PC 文件
- [ ] 文件名符合 `<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`
- [ ] 不创建 `design/<module>/<sub-module>/` 深目录
- [ ] PPDCS 过程文件保留 LC `topology_bindings` 与拓扑绑定校验结论
- [ ] PC 中真实端口均可回链 LC `topology_bindings` 和 `analysis/scenarios/confirmed-scenarios.md`
- [ ] 未确认或不唯一拓扑绑定导致相关 PC `fact_status=needs-confirmation`
