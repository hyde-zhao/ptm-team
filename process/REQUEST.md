---
request_id: "MFQ-001"
version: "2.0"
status: "active"
submitted_at: "2026-04-24T10:11:30+08:00"
submitted_by: "user"
source: "user-direct-redesign-request + meta-flow-format-update"
target_artifact_type: "agent"
governance_mode: "conditional"
review_policy: "light"
---

## 来源上下文

| 字段 | 当前值 | 说明 |
|---|---|---|
| `target_artifact_type` | `agent` | 当前交付对象仍是供用户直接调用的 `ptm-tde` Agent |
| `governance_mode` | `conditional` | 工作流默认连续推进，但在关键对象上停留等待用户确认 |
| `review_policy` | `light` | 采用关键节点确认，不要求全程重度评审 |
| `source` | `user-direct-redesign-request + meta-flow-format-update` | 原始立项请求保持不变，本轮额外同步 meta-flow 文档格式 |

## 用户目标

基于更新后的开发流程，对 ptm-tde 工作流进行从头重新设计与更新。允许参考仓库内现有 Agent、Skill、脚本、文档和历史流程工件，但这些内容仅作为输入材料，新的工作流边界、阶段、检查点、设计对象与交付方式都需要重新定义。

## 核心范围（In Scope）

1. 重新定义 ptm-tde 的阶段模型、状态写回规则、人工检查点和回退机制。
2. 重新梳理工作流中的 Agent / Skill 分工、输入输出契约和编排边界。
3. 重新评估运行态目录、确认稿目录、交付目录及平台安装映射。
4. 从头重建 use cases、requirements、HLD、story plan 和验证/交付链路。
5. 保留现有仓库实现与历史文档作为参考样本，但不直接继承其正式结论。

## 明确排除（Out of Scope）

- 沿用旧版确认稿作为当前正式结论
- 跳过检查点直接进入实现
- 把历史流程工件直接视为新流程模板

## 交付预期

| 交付项 | 说明 |
|---|---|
| 工作流设计基线 | 一套重新规划后的 ptm-tde 工作流设计基线 |
| 正式对象 | 与新流程一致的 `USE-CASES / REQUIREMENTS / HLD / STORY-BACKLOG / DEVELOPMENT-PLAN` |
| 安装与验证策略 | 与新流程一致的安装、验证和交付策略 |
| 治理机制 | 可支持后续实现与增量变更管理的状态机和检查点机制 |

## 补充约束

1. 本次按“从头设计”处理，旧版确认稿不得直接视为已确认输入。
2. 现有仓库内容可作为参考样例，但新流程必须显式说明哪些内容保留、哪些内容淘汰。
3. 多平台安装能力、`.input/` / `.output/` 隔离规则、变更管理能力仍需在新流程中重新评估。
4. 新流程必须保留可审计的状态推进、history 记录和人工检查点机制。

## 变更记录

| 版本 | 变更摘要 | 处理人 | 时间 |
|---|---|---|---|
| 1.0 | 建立“从头重新设计”请求基线，冻结旧流程结论。 | meta-po | 2026-04-23T17:05:18+08:00 |
| 2.0 | 按更新后的 meta-flow 补齐上下文字段、范围/排除结构和交付表格式。 | meta-po | 2026-04-24T10:11:30+08:00 |
