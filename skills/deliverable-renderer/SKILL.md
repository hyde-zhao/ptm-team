---
name: deliverable-renderer
description: >-
  将 MFQ 分析、完整 PPDCS 设计过程和覆盖结果渲染为最终交付物，
  只输出测试方案和测试用例两份 Markdown。
  触发词包括：生成交付物、输出文档、测试方案、测试用例文档。
  适用场景：MFQ 分析的 delivery 阶段。
argument-hint: "特性名称"
user-invokable: true
status: active
---

## 目标

读取 `analysis/`、`design/ppdcs/`、`design/pc/`、`analysis/coverage/` 产物，输出 delivery 闭环：

1. `<特性名>特性测试方案.md`
2. `<特性名>特性测试用例.md`

渲染时必须：

- 消费 `design/ppdcs/` 和 `design/pc/` 的**每 LC 单文件过程工件**，不能只看最终 PC；
- 保留 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status`；
- 当上游存在 `topology_ref` 时，在测试方案的场景章节中保留对应组网引用与产物路径。

## 适用范围

- 适用阶段：MFQ 的 delivery 阶段
- 输入：`analysis/integration/`、`analysis/coverage/`、`design/ppdcs/`、`design/pc/`
- 输出：`delivery/`

## 前置条件

- [ ] 覆盖报告已生成
- [ ] `logic-cases.md`、`test-data.md` 已存在
- [ ] `design/ppdcs/` 与 `design/pc/` 下各 LC 单文件已存在
- [ ] 上游已保留 trace / gap / fact_status 字段

## 必须消费的输入契约

### 1. 覆盖与整合层

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `coverage-summary.md` / `requirement-coverage.md` / `test-point-coverage.md` | 覆盖统计、`requirement_gaps`, `test_point_gaps`, `feature_tags`, `trace_refs`, `fact_status` | 方案文档中的覆盖章节 |
| `all-test-points.md` | `TP-ID`, `关联SR`, `scenario_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `fact_status` | 测试点分析表 |
| `logic-cases.md` | `LC-ID`, `source_tp_ids`, `关联SR`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status`, `动作路径`, `因子-取值表`, `CAE聚合规则` | 交付主骨架 |
| `test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `trace_refs`, `confirmation_gap_refs`, `status` | 设计过程与数据回链 |

### 2. STORY-06 / STORY-07 设计层（必须全量消费）

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `design/ppdcs/<basename>.md` | 推荐方法、图/规则/等价类/组合/状态迁移、覆盖策略、触发数据、`trace_refs`, `scenario_refs`, `action_source_refs`, `confirmation_gap_refs`, `fact_status` | 渲染完整 PPDCS 设计过程 |
| `design/pc/<basename>.md` | `physical_case_id`, `logic_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status` | 渲染最终物理用例 |

> 若某 PC 缺少 `feature_tags` 或某 LC 无法回链到 `requirement_ids / trace_refs`，renderer 必须在交付物中显式暴露缺口，不得自行脑补。

## 执行流程

### 步骤 1：装配交付基线

1. 读取覆盖报告；
2. 读取 `analysis/integration/logic-cases.md`、`analysis/integration/test-data.md`；
3. 枚举 `design/ppdcs/*.md` 与 `design/pc/*.md`；
4. 按相同 basename 建立 `LC → PPDCS过程 → PC` 的完整映射；
5. 为每个 PC 汇总可直接进入交付文档的字段。

### 步骤 2：渲染 `<特性名>特性测试方案.md`

测试方案至少包含：

1. 特性概述
2. 应用场景分析
   - 若存在 Topology，列出 `topology_ref` 与 `analysis/scenarios/<scene-id>/topology.{mmd,yaml}` 引用
3. 需求分析
4. M 分析
5. F 分析
6. Q 分析
7. 测试点整合
8. 覆盖率报告

覆盖章节必须区分：

- 需求层覆盖
- 测试点层覆盖
- 未覆盖项 / `needs-confirmation` 项

### 步骤 3：渲染 `<特性名>特性测试用例.md`

按 **四级目录（H2）→ 五级目录（H3）→ 逻辑用例（H4）** 组织。

每个 LC 必须同时渲染：

1. `design/ppdcs/<basename>.md` 的推荐上下文与完整过程
2. `design/pc/<basename>.md` 的最终 PC 表

按设计 Skill 分类保留过程内容：

| 设计 Skill | 必渲染内容 |
|------------|------------|
| `process-design` | 流程图、节点清单、路径枚举、覆盖策略、触发数据 |
| `state-design` | 状态图、状态/迁移表、守卫条件、路径选择、迁移数据 |
| `parameter-design` | factor catalog、规则表、判定结构、data row |
| `data-design` | factor catalog、等价类/边界值表、独立性检查、data row |
| `combination-design` | factor catalog、约束表、压缩策略、组合表、pair coverage checklist / fallback 记录 |

## 输出文件

| 文件 | 内容 |
|------|------|
| `<特性名>特性测试方案.md` | 覆盖测试方案、场景、分析与覆盖摘要 |
| `<特性名>特性测试用例.md` | 按 LC 组织的完整设计过程 + PC |

## 渲染规则

1. **不丢过程**：必须带出 STORY-06 / STORY-07 完整设计过程
2. **不丢字段**：不得删掉 trace / gap / fact_status；若存在 `topology_ref`，不得在场景章节中丢失
3. **不扩展交付文件**：`delivery/` 只输出测试方案和测试用例两份 Markdown

## 公共因子库补充契约

- deliverable-renderer 必须读取 `analysis/factor-usage/`，在测试方案中输出“因子库与样本策略”小节。
- 小节至少包含公共库 `library_id / version / checksum`、关键 factor groups、配置/功能样本策略、物化策略。
- 最终物理用例展示 `materialized_value`；随机样本必须记录 deterministic seed。
- `factor_bindings` 是主契约，`factor_refs` 仅作兼容摘要。

## Gotchas

- `feature_tags` 若缺失，应在交付中列为 gap，而不是用模块名临时替代
- `fact_status=needs-confirmation` 的 LC / PC 条目必须原样进入交付物

## 验收标准

- [ ] 只输出测试方案、测试用例两份 Markdown
- [ ] 测试用例文档消费 STORY-06 / STORY-07 的完整过程文档，而非仅最终 PC
- [ ] 交付物保留 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_bindings`, `factor_refs`, `confirmation_gap_refs`, `fact_status`
- [ ] 不生成工具分析表或 `case-index.yaml`
