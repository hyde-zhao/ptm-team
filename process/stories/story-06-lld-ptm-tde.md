---
story_id: "STORY-06"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "skill-pack"
shared_fragments:
  - "design-process-shared"
  - "graph-design-shared"
open_items:
  - "process/state 图示模板可共用 mermaid 片段"
depends_on:
  - "STORY-05"
---

# STORY-06 LLD：Graph Design Pack — `process-design` + `state-design`

## 1. 目标

让流程图法和状态图法都输出完整过程工件，而不是只给最终物理用例。该 Story 必须把**图怎么生成、路径怎么选、测试数据怎么分析、如何叠加数据生成 PC**写清楚。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-013 | `process-design` 完整流程分析 |
| REQ-017 | `state-design` 完整状态分析 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `process-design` | 流程图生成、路径枚举、覆盖策略、路径数据叠加 |
| `state-design` | 状态图生成、迁移路径选取、守卫条件分析、迁移数据叠加 |
| shared graph fragment | 统一图示与 PC 字段骨架 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/process-design/SKILL.md` | 完整过程升级 |
| `skills/state-design/SKILL.md` | 完整过程升级 |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| process node | `node_id`, `node_type`, `source_op_id`, `decision_condition`, `observation_ref` |
| process path | `path_id`, `branch_sequence`, `coverage_goal`, `trigger_data`, `data_overlay_set` |
| state node | `state_id`, `state_name`, `entry_conditions`, `exit_observations` |
| state transition | `transition_id`, `from`, `to`, `guard`, `trigger_data`, `data_overlay_set` |

## 6. API / Interface 设计

### 输入

- 已确认方法为 `P-Process / S-State` 的 LC
- 上游 `Scenario Chain`
- `test_object_refs / factor_refs`

### 输出

- 图示
- 枚举表
- 覆盖策略
- 路径/迁移数据分析结果
- 叠加数据后的 PC

## 7. 核心处理流程

### P-Process 子流程

1. 从 `minimal_logic_chain + precondition_operations` 生成流程节点；
2. 将节点分类为 `start / action / decision / observation / end`；
3. 生成流程图；
4. 枚举覆盖路径：
   - 正常主路径
   - 每个决策分支路径
   - 关键异常路径（若需求/HLD 已明确）
5. 对每条路径分析触发数据与前置条件；
6. 将测试数据叠加到路径节点，形成路径级逻辑变体；
7. 产出 PC。

### S-State 子流程

1. 从对象生命周期、前置条件和 `E（Effect）` 推导状态集合；
2. 从 `A（Action） + guard + effect` 生成迁移；
3. 生成状态图；
4. 选择迁移路径：
   - 主生命周期路径
   - 关键回退路径
   - 边界迁移路径
   - 无效迁移（若需求已定义）
5. 对每条迁移路径分析触发数据与守卫条件；
6. 将测试数据叠加到迁移节点，形成 PC；
7. 产出 PC。

## 8. 技术设计细节

### 8.1 流程图生成规则

- 节点来源：
  - `precondition_operations` → 前置准备节点
  - `atomic_operations` → 操作节点
  - `observation_points` → 观察节点
  - 条件分支 → 决策节点
- 图示生成优先使用 Mermaid flowchart。

### 8.2 覆盖路径生成规则

- 至少覆盖：
  - 主路径
  - 每个独立决策分支一次
  - 需求明确的异常/回退路径
- 路径枚举表最少字段：`path_id / node_sequence / branch_reason / coverage_goal`

### 8.3 测试数据分析与叠加

- 先根据 `factor_refs` 分析路径触发数据；
- 再根据上游等价类 / 边界值 / 组合策略选择路径叠加数据；
- `data_overlay_set` 必须能回链到路径或迁移。

### 8.4 状态图生成规则

- 状态来自对象稳定状态，不是瞬时动作；
- 迁移来自动作触发和守卫条件；
- 状态图生成优先使用 Mermaid stateDiagram。

## 9. 安全与性能设计

- 图示和表格均写入 `.output/`；
- 不因图示失败而跳过过程输出；
- 若状态集合不稳定，必须标记待确认，而不是伪造状态图。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 流程图生成 | 样例检查：节点是否来自场景链 |
| 覆盖路径枚举 | 样例检查：是否包含主路径+分支路径 |
| 路径数据分析 | 样例检查：路径是否挂载触发数据 |
| 状态图生成 | 样例检查：状态与迁移是否可解释 |
| 迁移路径选取 | 样例检查：是否覆盖主路径/回退路径/边界路径 |
| PC 回链存在 | 样例检查 |

## 11. 实施步骤

1. 定义流程节点/路径模型；
2. 在 `process-design` 中落地流程图生成规则；
3. 在 `process-design` 中落地路径枚举与数据叠加；
4. 定义状态/迁移模型；
5. 在 `state-design` 中落地状态图生成规则；
6. 在 `state-design` 中落地迁移路径选取与数据叠加；
7. 统一 PC 输出骨架。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 图示冗长 | 图示与表格分层输出 |
| 路径覆盖边界不清晰 | 先固定最小覆盖规则，再扩展异常路径 |
| 状态守卫表达不一致 | 先统一字段，再写模板 |
| 数据叠加与路径脱节 | 强制 `data_overlay_set` 回链到 path/transition |

## 13. 回滚与发布策略

- 两个 Skill 可独立回滚；
- shared fragment 回滚时需同步评估两个 Skill。

## 14. Definition of Done

- [ ] `process-design` 输出流程图、路径表、覆盖策略、路径触发数据、PC
- [ ] `process-design` 明确数据如何叠加到路径
- [ ] `state-design` 输出状态图、迁移表、守卫条件、迁移触发数据、PC
- [ ] `state-design` 明确路径如何选取、数据如何叠加到迁移
