---
from_agent: meta-se
to_agent: meta-po
semantic: stage-return
status: completed
created_at: "2026-06-02T12:00:00+08:00"
workflow_id: WF-PTM-TEAM-20260520-001
active_change: CR-011-ptm-tde-kym-phase
current_phase: story-execution
---

# meta-se 交还摘要：ptm-tde 数据实体信息流规格

## 产出

- **主产出**：`/home/hyde/projects/ptm-team/docs/ptm-tde/data-flow-spec.md`（~900 行）
- **索引更新**：`/home/hyde/projects/ptm-team/docs/ptm-tde/skill-references.md` — 新增"相关设计文档"节，含 `data-flow-spec.md` 条目

## 覆盖范围

8 个数据实体，每个覆盖 7 个维度（谁生产 / 何时生产 / 生产格式 / 谁消费 / 如何消费 / 消费时机 / 缺失行为）：

| # | 实体 | 状态标注 | 关键消费方 |
|---|------|---------|-----------|
| 1 | KYM 产出 (mission-statement.md) | [已实现 CR-011] | scenario-discovery, m-analyzer(◇), PPDCS(◇) |
| 2 | 用户场景 (confirmed-scenarios.md) | [已实现 CR-010] | m-analyzer, test-point-integrator, PC 生成, coverage-verifier |
| 3 | TSP | [前瞻 CR-012] | m-analyzer(PPDCS 标注), design-planner |
| 4 | 测试因子 (Factor) | [已实现 CR-010] + [前瞻 后续因子库CR] | test-point-integrator, 5 PPDCS 设计 Skill, CAE-R(◇) |
| 5 | CAE-R | [前瞻 CR-012/013] | coverage-verifier(R.coverage), ptm-te/ptm-tae(R.intent) |
| 6 | 逻辑用例 (LC) | [已实现 CR-010] + [前瞻 CR-012/013] | design-planner, 5 设计 Skill, PC 生成, coverage-verifier |
| 7 | 物理用例 (PC) | [已实现 CR-010] | coverage-verifier, deliverable-renderer, ptm-te/ptm-tae |
| 8 | 原子操作 (Atomic Ops) | [已实现 CR-010] | scenario-discovery, CAE(A), PC(steps), ptm-te/ptm-tae |

## 文档结构

```markdown
# ptm-tde 数据实体信息流规格
├── 概述（三阶段数据流 Mermaid 图 + 追踪链映射 + 路径约定）
├── 实体 1-8（每实体覆盖 7 个维度，含字段级消费卡片表格）
└── 附录
    ├── A.1 全量生产→消费关系表
    ├── A.2 实体间依赖关系图
    ├── A.3 Gate 检查项与实体关联
    ├── A.4 前瞻设计状态速查表
    └── 引用源
```

## 标注约定执行情况

- 每个字段/消费关系均标注实现状态：`[已实现 CR-010]`、`[已实现 CR-011]`、`[前瞻 CR-012]`、`[前瞻 CR-013]`、`[前瞻 CR-012/013]`、`[前瞻 后续因子库CR]`
- Mermaid 图中虚线框 + ◇ 标注前瞻实体
- 通过 `[标签]` 清晰区分"当前可工作"与"设计前瞻"的消费链路

## 关键设计决策

1. **消费关系采用 Pull 模式**：所有下游消费方通过按需读取上游产物工作，不依赖 push 传递。缺失行为优先设计为"不阻断降级"（如 scenario-discovery 无 mission-statement 时使用默认优先级）。
2. **CAE-R 渐进式超集演进**：MFQ 阶段产出雏形（R 仅可填 risk_level + intent 候选），PPDCS 阶段补全（R 全部字段）。已实现 CAE 三元组在无 R 字段时正常工作，确保 CR-010 基线兼容。
3. **因子格式渐进兼容**：当前因子格式（factor_kind / design_role / sample_definitions / usage_profiles）全部保留，v2 增强（factor_type + tags）作为可选字段，不删除任何现有自动化能力。
4. **实体间依赖显式建模**：附录 A.2 提供实体间依赖关系图，附录 A.3 提供 Gate 检查项→实体关联，确保 Gate 自检时可追溯数据来源。
5. **历史路径兼容说明**：文档中路径引用以最终目标路径为准（`kym/` / `mfq/` / `ppdcs/`），并在"文件路径约定"节说明当前 CR 状态下哪些路径已迁移、哪些仍为旧路径。

## 上下文消费清单

| 源文件 | 消费方式 |
|--------|---------|
| `process/HLD-CR-011.md` | §8 完整三阶段数据流图、§9 模块职责表、§10 集成契约字段级消费卡片、§11 前瞻实体设计（TSP/CAE-R/因子格式/追踪链）、§12 门控设计 |
| `agents/ptm-tde.md` | 三阶段框架流程、追踪链、运行时工作目录、物理用例字段规范（16 列）、Skill 触发词映射、公共因子库路径 |
| `docs/ptm-tde/gate-spec.md` | GATE-1 至 GATE-5 检查项、跨阶段拓扑绑定检查 |
| `skills/m-analyzer/SKILL.md` | CAE 格式、测试因子格式、PPDCS 特征标注、拓扑角色契约、TP 字段定义 |
| `skills/test-point-integrator/SKILL.md` | LC 结构化格式、因子-取值表、组网绑定、CAE 聚合规则、追踪矩阵 |
| `resource/factor-libraries/` | 公共因子库 schema（index.yaml + ngfw-policy-routing/factor-library.yaml） |
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | MFQ 阶段前瞻范围 |
| `process/changes/CR-013-ptm-tde-ppdcs-phase.md` | PPDCS 阶段前瞻范围 |

## 未被采纳的输入

| 输入 | 原因 |
|------|------|
| ptm-tde-workflow-v2.md | 在 wiki 和仓库中均未找到该文件。v2 全部设计内容已通过 HLD-CR-011 §11（前瞻设计）完整吸收，本文档使用 HLD-CR-011 作为 TSP/CAE-R/v2 追踪链的权威定义源 |

## 建议给 meta-po 的后续动作

1. 确认文档位置 `docs/ptm-tde/data-flow-spec.md` 和索引条目符合预期
2. 在 CR-011 Phase 3 LLD 并行设计时，各 meta-dev 应把本文档作为实体间消费契约的权威参考
3. CR-012/013 启动时，本文档的前瞻标注可指导 HLD 更新和实现范围界定
