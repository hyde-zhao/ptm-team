---
checkpoint_id: "CP2"
checkpoint_name: "需求 / 场景 / 范围基线门"
type: "auto_precheck"
status: "WAIVED"
owner: "meta-pm"
created_at: "2026-06-08T02:30:00+08:00"
checked_at: "2026-06-08T02:30:00+08:00"
target:
  phase: "requirement-clarification"
  artifacts:
    - "docs/ptm-tde/REQUIREMENTS.md"
    - "docs/ptm-tde/USE-CASES.md"
manual_checkpoint: "process/checkpoints/CP2-REQUIREMENTS-BASELINE.md"
---

# CP2 需求 / 场景 / 范围基线门 自动预检结果

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CP1 通过 | WAIVED | `process/checks/CP1-USE-CASE-COMPLETENESS.md` WAIVED | gate_inheritance |
| 需求草案存在 | WAIVED | `docs/ptm-tde/REQUIREMENTS.md`（v6.2，28 条需求） | gate_inheritance |
| 工程验证场景存在或 N/A | WAIVED | SCENARIOS.yaml 和 TEST-MATRIX.md 待 P2 创建 | gate_inheritance |
| 产品规划输入存在或 N/A | WAIVED | STORY-MAP/MVP-SCOPE 待 P2 创建 | gate_inheritance |
| 非功能需求有初稿 | WAIVED | `docs/ptm-tde/TEST-STRATEGY.md` | gate_inheritance |
| 场景讨论证据或 N/A | WAIVED | CP2 讨论日志待创建（gate_inheritance） | gate_inheritance |
| 用户可见场景确认证据 | WAIVED | CR 级人工确认已覆盖场景决策 | gate_inheritance |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | 功能需求完整 | WAIVED | 28 条需求，12 步主流程 | gate_inheritance |
| 2 | 非功能需求量化 | WAIVED | TEST-STRATEGY v2.0 | gate_inheritance |
| 3 | 范围清晰 | WAIVED | `docs/ptm-team-blueprint.md` Step 1 Scope | gate_inheritance |
| 4 | 验收标准明确 | WAIVED | 每条需求有 AC | gate_inheritance |
| 5 | 约束条件记录 | WAIVED | ADR 中已记录 | gate_inheritance |
| 6 | 依赖和风险识别 | WAIVED | 蓝图 §6.1 关键风险 | gate_inheritance |
| 7 | 需求无冲突 | WAIVED | 7 条 CR 全部 closed，无未解决冲突 | gate_inheritance |
| 8 | 变更机制明确 | WAIVED | CR-INDEX.yaml + follow-up tracking | gate_inheritance |
| 9 | 追溯矩阵建立 | WAIVED | 原始请求 → 场景 → 需求可追溯 | gate_inheritance |
| 10 | Scenario Gray Areas 已处理 | WAIVED | gate_inheritance（CP2 讨论日志未生成） | gate_inheritance |
| 11 | Deferred Ideas 已隔离 | WAIVED | follow-up tracking 台账 | gate_inheritance |
| 12 | 用户可见场景确认已完成 | WAIVED | CR 级 Decision Brief 已覆盖 | gate_inheritance |
| 13 | 8 维扫描后台化 | WAIVED | gate_inheritance | gate_inheritance |
| 14 | 工程验证场景可追踪 | WAIVED | SCENARIOS.yaml 待 P2 | gate_inheritance |
| 15 | MVP 范围可确认 | WAIVED | ptm-tde 为 Step 1 三 Agent 之一 | gate_inheritance |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| P0/P1 需求通过 | WAIVED | 致命问题=0，阻塞问题=0 | gate_inheritance |
| 人工确认完成 | WAIVED | `process/checkpoints/CP2-REQUIREMENTS-BASELINE.md` 待创建 | gate_inheritance |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| REQUIREMENTS | `docs/ptm-tde/REQUIREMENTS.md` | WAIVED | gate_inheritance |
| SCENARIOS | `docs/product/SCENARIOS.yaml` | N/A | P2 待创建 |
| TEST-MATRIX | `docs/product/TEST-MATRIX.md` | N/A | P2 待创建 |
| STORY-MAP | `docs/product/STORY-MAP.md` | N/A | P2 待创建 |
| MVP-SCOPE | `docs/product/MVP-SCOPE.md` | N/A | P2 待创建 |
| RELEASE-SLICES | `docs/product/RELEASE-SLICES.md` | N/A | P2 待创建 |
| BACKLOG | `docs/product/BACKLOG.md` | N/A | P2 待创建 |
| CP2 Discussion Log | `process/discussions/CP2-SCENARIO-DISCUSSION-LOG.md` | N/A | gate_inheritance |
| CP2 Discussion Checkpoint | `process/checks/CP2-DISCUSSION-CHECKPOINT.json` | N/A | gate_inheritance |

## 结论

- 结论：`WAIVED`
- 豁免原因：ptm-tde 源仓库 CP0-CP5 门控视为已通过（`STATE.md.gate_inheritance`）
- 影响面：SCENARIOS.yaml、TEST-MATRIX.md、STORY-MAP.md 等产品规划产物未在本仓库独立生成；当前以蓝图和 CR 级产物为事实基线
- 重访条件：新 Agent 启动时或 ptm-tde 重大架构变更时，应重新执行本检查点
- 下一步：CP3 蓝图/HLD 架构评审门（CR 级已通过）
