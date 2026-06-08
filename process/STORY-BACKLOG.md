---
status: confirmed
version: "1.1"
total_stories: 9
total_waves: 6
created_by: "meta-se"
created_at: "2026-04-23T20:18:07+08:00"
hld_version: "7.1"
confirmed_by: "user (implicit via continuing testing and delivery after CR-008 HLD refresh)"
confirmed_at: "2026-04-24T14:20:28+08:00"
---

# Story Backlog v1.1 — ptm-tde v7.1

> 基于 `process/HLD.md` v7.1、`process/ARCHITECTURE-DECISION.md` v6.0 维护。  
> CR-008 为 **Topology Modeling 最小增量**：经评估可由既有 STORY-03（场景建模）与 STORY-08（交付口径）吸收，不额外开启新 Wave。

## Story 总览

| Story ID | 标题 | Wave | 优先级 | 需求 | 依赖 | 说明 |
|---|---|---|---|---|---|---|
| STORY-01 | Installer 基线 — Claude/Codex project scope 投影 | W1 | P0 | REQ-001 | 无 | 收敛平台范围并稳定 project scope 安装 |
| STORY-02 | Installer 用户级安装 — `CLAUDE.md` / `AGENTS.md` 合并 | W2 | P1 | REQ-001 | STORY-01 | 实现 user scope marker merge 和 merge report |
| STORY-03 | Scenario Foundation — 场景链 / 动作源 / 只读 MCP | W1 | P0 | REQ-005~007, REQ-023~026, REQ-028 | 无 | 形成原子操作、动作源、知识引用、Topology 建模和工具抽象基础 |
| STORY-04 | MFQ Trace Chain — M/F/Q/Integrator 贯通新模型 | W2 | P0 | REQ-009~011 | STORY-03 | 让 TP/LC 可以消费 Scenario Chain 与 Action Source |
| STORY-05 | Design Planner — CAE→PPDCS 完整推断与设计计划 | W3 | P0 | REQ-012 | STORY-04 | 输出完整 reasoning，而不是只给方法结果 |
| STORY-06 | Graph Design Pack — `process-design` + `state-design` | W4 | P0 | REQ-013, REQ-017 | STORY-05 | 图形链方法完整化 |
| STORY-07 | Rule/Data Design Pack — `parameter`/`data`/`combination` | W4 | P0 | REQ-014~016 | STORY-05 | 规则与数据链方法完整化 |
| STORY-08 | Delivery & Retrieval — 覆盖、交付、标签检索 | W5 | P0 | REQ-018, REQ-019, REQ-022 | STORY-06, STORY-07 | 收尾交付与轻量检索闭环 |
| STORY-09 | Feedback Adaptation — 变更影响与问题单适配新模型 | W6 | P1 | REQ-020, REQ-021 | STORY-04, STORY-08 | 让增量分析消费场景链 / 动作源 / 索引 |

## Wave 划分

### W1 — 安装基线 + 场景基础（并行）

- **目标**：稳定 project scope 安装，同时完成场景链、Topology 建模、动作源和只读知识查询基础。
- **Stories**：`STORY-01`、`STORY-03`

### W2 — user scope 安装 + MFQ 贯通（并行）

- **目标**：补齐 user scope 合并策略，并把新场景模型贯通到 M/F/Q/Integrator。
- **Stories**：`STORY-02`、`STORY-04`

### W3 — 设计计划层（串行）

- **目标**：让 design-planner 输出完整 CAE→PPDCS 推断过程。
- **Stories**：`STORY-05`

### W4 — 五类设计方法成组落地（并行）

- **目标**：按两组共享建模方式完成全部五类设计 Skill 的过程输出。
- **Stories**：`STORY-06`、`STORY-07`

### W5 — 覆盖、交付与检索（串行）

- **目标**：产出覆盖报告、交付物、标签索引与检索入口，并在交付说明中保留 `topology_ref` 口径。
- **Stories**：`STORY-08`

## CR-008 增量吸收说明

| 变更项 | 吸收位置 | 处理方式 |
|---|---|---|
| `REQ-028` Topology Modeling | STORY-03 | 扩展 `scenario-discovery` 契约与场景确认模板，新增 Mermaid/YAML 组网产物和三张清单表 |
| `topology_ref` 交付口径 | STORY-08 | 在交付说明、用户手册与 renderer 契约中保留组网回链说明 |
| Topology 校验器（可选） | 暂不独立成 Story | 先并入 `scenario-discovery` 的确认与静态校验口径；后续若规则复杂度上升，再单独拆 Story |

### W6 — 反馈驱动链路（串行）

- **目标**：让 change-impact / bug-gap 适配新的追踪链和索引模型。
- **Stories**：`STORY-09`

## 进入开发前的门控

1. 所有 Story 卡片必须完整。
2. 所有 `story-*-lld.md` 必须生成完毕。
3. 所有 Story 状态必须推进到 `ready-for-lld-review`。
4. 用户确认 LLD 前，不进入开发实现。
