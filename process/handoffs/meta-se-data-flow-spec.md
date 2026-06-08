---
from_agent: meta-po
to_agent: meta-se
semantic: stage-dispatch
status: handoff-created
created_at: "2026-06-02T12:00:00+08:00"
workflow_id: WF-PTM-TEAM-20260520-001
active_change: CR-011-ptm-tde-kym-phase
current_phase: story-execution
task: 编写 ptm-tde 全流程数据实体信息流转文档
output_path: docs/ptm-tde/data-flow-spec.md
reuse_key:
  role: meta-se
  workflow_id: WF-PTM-TEAM-20260520-001
  change_id: CR-011-ptm-tde-kym-phase
  story_id: n/a
  wave_id: n/a

dispatch:
  required: true
  semantic: stage-dispatch
  mode: subagent
  platform: claude
  agent_role: meta-se
  agent_path: ""
  tool_name: ""
  agent_id: ""
  agent_name: ""
  thread_id: ""
  spawned_at: ""
  resumed_at: ""
  completed_at: ""
  evidence: ""
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# meta-se Handoff：编写 ptm-tde 数据实体信息流转文档

## 任务描述

在进入 CR-011 Phase 3 LLD 并行设计之前，编写一份 `docs/ptm-tde/data-flow-spec.md`，覆盖 ptm-tde 全流程中所有数据实体的生产→消费链路。

## 输出要求

- **输出路径**：`/home/hyde/projects/ptm-team/docs/ptm-tde/data-flow-spec.md`
- **必须标注**：每个字段/消费关系标注「已实现」（CR-010/011 基线已存在）或「设计前瞻」（归属 CR-012/013）

## 覆盖的 8 个数据实体

| 实体 | 生产阶段 | 生产方 | 消费阶段 | 消费方 |
|------|---------|--------|---------|--------|
| KYM 产出 (mission-statement.md) | KYM | kym Skill | KYM / MFQ / PPDCS | feature-parser, scenario-discovery, m-analyzer, f-analyzer, q-analyzer, design-planner, design-ppdcs-analyzer, deliverable-renderer |
| 用户场景 (confirmed-scenarios.md) | KYM | scenario-discovery | MFQ / PPDCS | m-analyzer (topology_role_refs), test-point-integrator (topology_bindings), PC (物化回链) |
| TSP | MFQ (M 分析) | m-analyzer | MFQ / PPDCS | PPDCS 特征选择, LC 组装 |
| CAE-R | MFQ→PPDCS | m-analyzer(雏形) → design-ppdcs-analyzer(完整) | PPDCS / 执行层 | coverage-verifier, PC 生成, ptm-te/ptm-tae |
| 测试因子 (Factor) | MFQ | m-analyzer (定义) + 公共因子库 | MFQ / PPDCS | test-point-integrator (factor_bindings), PPDCS design Skills (组合), CAE-R (实例化), coverage-verifier |
| 逻辑用例 (LC) | MFQ→PPDCS 边界 | test-point-integrator + design-ppdcs-analyzer | PPDCS | 5 design Skills, PC 生成, coverage-verifier |
| 物理用例 (PC) | PPDCS | PC 生成 (从 CAE-R × 因子值) | 执行层 | ptm-te/ptm-tae (原子操作映射), deliverable-renderer |
| 原子操作 (Atomic Ops) | 贯穿全流程 | 全局 atomic-ops 命令 | KYM / MFQ / PPDCS / 执行 | scenario-discovery (action_source_ref), CAE (A 字段), PC (steps), ptm-te/ptm-tae (execute_ops) |

## 每个实体文档结构

对每个实体，说明：
1. **谁生产**：哪个 Skill / 哪个阶段
2. **何时生产**：在流程的哪个步骤
3. **生产格式**：数据结构/字段定义（引用已有定义，不重复）
4. **谁消费**：下游哪些 Skill / 阶段消费
5. **如何消费**：消费的具体字段、用途
6. **消费时机**：在消费方流程的哪个步骤读取
7. **缺失行为**：如果该实体不存在，消费方如何处理

## 必须加载的上下文文件

### 核心设计文件

| 文件 | 用途 |
|------|------|
| `process/HLD-CR-011.md` | §8 完整三阶段数据流（含 mermaid 图和前瞻标注）、§9 模块职责与输入/输出、§12 信息消费链路（字段级）、§4 推荐方案总览（module-capability map）|
| `agents/ptm-tde.md` | §追踪链（SR→TP→LC→PC）、§运行时工作目录（kym/mfq/ppdcs 产物路径）、§测试因子/拓扑角色/真实组网对象分层（三条并行链路）、§Skill 触发词映射（19 个 Skill 与阶段归属）、§公共因子库（factor_id/sample_id/binding 格式）|
| `process/HLD-ptm-tde.md` | §3.7 场景组网建模（Topology/Device/Port/Link 四级对象模型）、§1 问题定义中的 CAE 三元组定义（C: Condition, A: Action, E: Effect）|

### CR 范围文件

| 文件 | 用途 |
|------|------|
| `process/changes/CR-011-ptm-tde-kym-phase.md` | KYM 阶段实现范围：kym Skill、mission-statement.md、路径迁移。标注为「已实现」|
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | MFQ 阶段设计前瞻范围：TSP 实体、CAE→CAE-R 雏形、因子格式演进。标注为「设计前瞻」|
| `process/changes/CR-013-ptm-tde-ppdcs-phase.md` | PPDCS 阶段设计前瞻范围：CAE-R 完整形态、LC 建模、PC 生成。标注为「设计前瞻」|

### 运行状态

| 文件 | 用途 |
|------|------|
| `process/STATE.md` | 当前阶段 story-execution、active_change=CR-011、source_baseline 指向 ptm-tde 已 delivered 基线 |

## 明确禁止加载的内容

- 历史 CR（CR-003 ~ CR-009）：与当前数据实体定义无关
- 旧 Story LLD（`process/stories/story-01-ptm-tde.md` 至 `story-09-ptm-tde.md`）：已实现基线的实现细节，meta-se 只需知道产物存在
- CP3 讨论日志（`process/discussions/CP3-HLD-DISCUSSION-LOG.md`）：架构灰区讨论过程，不影响实体定义
- CR-010 全文：三阶段框架已通过 CR-011 HLD 完全吸收
- `process/REQUIREMENTS-ptm-tde.md` / `process/USE-CASES-ptm-tde.md`：需求级文档，对数据实体定义帮助有限
- `docs/ptm-tde/` 下已有文档（README/USER-MANUAL/gate-spec 等）：作为上下文参考但不作为主要输入

## 标注约定

文档中每个实体的字段/消费关系必须使用以下标注：

- `[已实现]`：在当前 ptm-tde 基线（CR-010 三阶段框架 + CR-011 KYM 阶段）中已存在的实体、字段或消费关系
- `[前瞻 CR-012]`：MFQ 阶段待实现的实体/字段/消费关系
- `[前瞻 CR-013]`：PPDCS 阶段待实现的实体/字段/消费关系
- `[前瞻 CR-012/013]`：跨两个 CR 协同实现的实体

## meta-po 位置决策

文档位置已确定为 `docs/ptm-tde/data-flow-spec.md`。理由：
1. 永久设计参考，与 gate-spec.md 同级
2. 跨 CR-011/012/013 边界，不属于单一 CR 的 HLD
3. HLD-CR-011 已 1092 行，不宜再追加
4. process/ 是运行时产物目录，不适合设计参考文档

## 输出后动作

meta-se 完成文档编写后：
1. 更新 `docs/ptm-tde/skill-references.md`，在文档索引中增加 `data-flow-spec.md` 条目
2. 确认文档 frontmatter 包含 `version`、`status`、`created_by`、`created_at` 字段
3. 交还控制权给 meta-po
