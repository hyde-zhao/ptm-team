---
story_id: "STORY-07"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "skill-pack"
shared_fragments:
  - "design-process-shared"
  - "table-design-shared"
open_items:
  - "combination fallback 需在实现时写明无外部工具时的回退路径"
depends_on:
  - "STORY-05"
---

# STORY-07 LLD：Rule/Data Design Pack — `parameter` / `data` / `combination`

## 1. 目标

让参数规则、数据范围、组合压缩三类 Skill 都输出完整表格式过程工件和 PC。该 Story 必须写清楚：**先提取因子，再做因子级数据分析，再决定组合策略，最后把因子组合和数据叠加到 LC 生成 PC。**

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-014 | 判定结构与规则分析 |
| REQ-015 | 取值范围、等价类、边界值 |
| REQ-016 | 因子范围、约束与组合策略 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `parameter-design` | 规则提取、约束、判定结构、触发组 |
| `data-design` | 因子级取值范围、等价类、边界策略、选点 |
| `combination-design` | 因子提取、组合策略判定、压缩策略、组合结果 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/parameter-design/SKILL.md` | 完整过程升级 |
| `skills/data-design/SKILL.md` | 完整过程升级 |
| `skills/combination-design/SKILL.md` | 完整过程升级 |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| factor catalog | `factor_id`, `factor_name`, `factor_type`, `source_ref`, `related_object` |
| parameter rule | `rule_id`, `constraint_refs`, `trigger_group`, `factor_refs` |
| data range | `factor_id`, `range`, `equivalence_classes`, `boundary_points` |
| combination strategy | `factor_group`, `strategy`, `constraints`, `generated_rows` |

## 6. API / Interface 设计

### 输入

- 已确认方法为 `P-Parameter / D-Data / C-Combination` 的 LC
- 上游 `factor_refs`

### 输出

- 因子表
- 因子级数据分析结果
- 组合策略说明
- 叠加到 LC 的 PC

## 7. 核心处理流程

1. 从 LC 和 `factor_refs` 中提取全部因子；
2. 对每个因子做数据分析：
   - 类型识别
   - 取值域识别
   - 等价类划分
   - 边界值识别
3. 根据因子数量、约束关系和业务规则确定组合策略：
   - 全组合
   - Pairwise / 压缩组合
   - 约束组合
4. 生成多条因子组合结果和数据行；
5. 将这些数据行叠加到 LC，形成 PC。

## 8. 技术设计细节

### 8.1 因子提取规则

- 因子优先来自 STORY-04 输出的 `factor_refs`；
- 若 `factor_refs` 不足，再从规则、输入参数、数据项中补提。

### 8.2 因子级数据分析

- 每个因子必须至少产出：
  - 取值范围
  - 等价类
  - 边界点（若适用）
- 因子分析结果必须独立保存，不能直接跳到组合。

### 8.3 组合策略判定

- 若因子间存在明确业务规则：优先走 `parameter-design`
- 若因子主要是独立数据范围：优先走 `data-design`
- 若因子需要交叉组合：走 `combination-design`
- 组合策略必须记录原因，不能只给结果。

### 8.4 数据叠加到 LC

- 组合结果以“多条数据行”的形式生成；
- 每条数据行都要映射到 LC 中的具体步骤/节点；
- 最终由 `LC + data row = PC`。

## 9. 安全与性能设计

- 不引入隐式外部工具依赖；
- 外部组合工具不可用时必须显式提示；
- 因子分析结果不得在未确认组合策略前直接合成 PC。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 因子提取 | 检查是否先形成 factor catalog |
| 因子级数据分析 | 检查是否存在等价类与边界值 |
| 组合策略输出 | 检查是否说明为何选择该策略 |
| 数据叠加到 LC | 检查是否生成多条 data row 并映射到 LC |

## 11. 实施步骤

1. 先定义 `factor catalog`；
2. 在 `data-design` 中落地因子级等价类与边界分析；
3. 在 `parameter-design` 中落地规则/约束/触发组；
4. 在 `combination-design` 中落地组合策略与数据行生成；
5. 统一“data row 叠加到 LC”骨架；
6. 对齐 PC 字段骨架。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 因子提取不全 | 先固定 factor catalog，再进入数据分析 |
| 参数规则过于复杂 | 判定结构与规则明细分层输出 |
| 组合工具不可用 | 保留显式 fallback 和人工确认 |
| 组合结果无法映射到 LC | 强制每条 data row 记录 LC 映射位置 |

## 13. 回滚与发布策略

- 三个 Skill 可单独回滚；
- shared fragment 变更需评估三者联动影响。

## 14. Definition of Done

- [ ] 先形成 factor catalog
- [ ] `parameter-design` 输出规则提取、约束、判定结构、触发组、PC
- [ ] `data-design` 输出因子级范围、等价类、边界策略、选点、PC
- [ ] `combination-design` 输出因子、约束、策略、组合结果、数据行、PC
- [ ] 明确数据如何叠加到 LC 生成 PC
