---
story_id: STORY-012-08
story_name: 文档更新（CR-INDEX + STATE.md + agents/ptm-tde.md + CR-012 close）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: S
wave: D
depends_on: [STORY-012-07]
blocks: []
status: ready-for-verification
file_ownership:
  - process/changes/CR-INDEX.yaml
  - process/STATE.md
  - agents/ptm-tde.md
  - process/changes/CR-012-ptm-tde-mfq-phase.md
parallel_safe: false
---

# STORY-012-08：文档更新

## 1. 目标

在全部实现 Story（012-01 ~ 012-07）完成并通过验证后，更新 CR-INDEX.yaml、STATE.md、agents/ptm-tde.md 和 CR-012 变更文件，将 CR-012 标记为 closed，反映 MFQ 阶段 v3.0 改造的最终状态。

## 2. 范围

- **修改文件**：4 个
- **改动量**：~30 行
- **不改动**：其他 CR 记录；其他 STATE.md 字段（如 `active_change` 以外的 current_phase 等）

### 更新内容

| 文件 | 更新项 | 说明 |
|------|--------|------|
| `process/changes/CR-INDEX.yaml` | CR-012 记录 | `status: active` → `closed`；`phase: story-execution` → `delivered`；`closed` 字段添加日期；`notes` 追加完成摘要 |
| `process/STATE.md` | `active_change` | 如果 `active_change` 指向 CR-012，更新为下一个待启动 CR（CR-013）或清空 |
| `agents/ptm-tde.md` | MFQ 阶段描述 | 更新 MFQ 阶段 Skill 流程描述，反映 m/f/q-analyzer v3.0 的步骤数和方法论变化 |
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | 实施记录 | 追加一行关闭记录（时间 + 事件） |

## 3. 验收标准

- [ ] **AC01**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `status: closed`
- [ ] **AC02**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `phase: delivered`
- [ ] **AC03**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `closed` 字段存在且格式为 `YYYY-MM-DD`
- [ ] **AC04**：`process/STATE.md` 中 `active_change` 不再指向 `CR-012-ptm-tde-mfq-phase`
- [ ] **AC05**：`agents/ptm-tde.md` 中 MFQ 阶段描述包含 `v3.0` 或 `场景步骤驱动` 或 `覆盖矩阵`
- [ ] **AC06**：`process/changes/CR-012-ptm-tde-mfq-phase.md` 的实施记录表末尾追加了一行关闭记录
- [ ] **AC07**：`process/changes/CR-INDEX.yaml` 仍为有效 YAML（`python -c "import yaml; yaml.safe_load(open('process/changes/CR-INDEX.yaml'))"` 通过）
- [ ] **AC08**：`process/STATE.md` 仍为有效 Markdown，frontmatter 完整

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `process/changes/CR-INDEX.yaml` | 修改 | CR-012 条目：status → closed，phase → delivered，添加 closed 日期，notes 追加完成摘要（Story 数、Waves、net_lines 等） |
| `process/STATE.md` | 修改 | `active_change` 字段更新：若指向 CR-012 则切换为 CR-013 或空；MFQ 阶段状态更新 |
| `agents/ptm-tde.md` | 修改 | MFQ Phase 段落更新：m-analyzer 10 步（场景步骤驱动）、f-analyzer 9 步（逐 TSP 驱动）、q-analyzer 6 步（逐 TSP 驱动）；新增覆盖矩阵和候选汇总说明 |
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | 修改 | 实施记录表追加关闭记录 |

## 5. 依赖关系

- **上游**：STORY-012-07（候选汇总 + skill-references 更新完成，文档引用的内容已稳定）
- **下游**：无（CR-012 的最后一步）

## 6. 实施注意事项

### CR-INDEX.yaml 更新模板
```yaml
- change_id: "CR-012-ptm-tde-mfq-phase"
  name: "ptm-tde MFQ 阶段改造（扩展范围）"
  status: "closed"
  workflow_id: "WF-PTM-TEAM-20260520-001"
  created: "2026-06-01"
  approved: "2026-06-02T21:00:00+08:00"
  closed: "2026-06-02"
  phase: "delivered"
  depends_on: "CR-010-ptm-tde-三阶段框架改造"
  stories: 8
  impact_level: "high"
  notes: "扩展范围：纳入 mfq-analysis-step-by-step.md v3.0 全部方法论。8 Stories / 4 Waves 完成。M 分析 v3.0 10步（场景步骤驱动）+ F 分析 v3.0 9步 + Q 分析 v3.0 6步（逐 TSP 驱动）+ 候选汇总 + GATE-3 HARD-STOP。"
```

### STATE.md 更新要点
- 检查 `active_change` 字段：如果当前值指向 `CR-012-ptm-tde-mfq-phase`，更新为 `CR-013-ptm-tde-ppdcs-phase`（如果 `CR-013` 状态为 pending 或 approved）
- 注意保护 STATE.md 的 frontmatter 和其他字段不被损坏
- MFQ 阶段相关状态更新为 `completed`

### agents/ptm-tde.md 更新要点
- MFQ Phase 段落修改示例：
  ```
  MFQ Phase: m-analyzer (v3.0, 10步, 场景步骤驱动, 产出覆盖矩阵+标签)
    → f-analyzer (v3.0, 9步, 逐 TSP 驱动, 消费 [F→] 标签)
    → q-analyzer (v3.0, 6步, 逐 TSP 驱动, 消费 [Q→] 标签)
    → test-point-integrator (含候选汇总)
    → design-planner (适配 TSP.covered_scenario_segments)
  ```
- 在三阶段框架图中增加候选汇总和覆盖矩阵的简要说明

### 执行时机
- 本 Story 必须在 STORY-012-01 ~ 012-07 全部完成并通过各自的验收标准后执行
- 建议在本 Story 执行前先做一次全局 grep 验证（AC01-AC08 的汇总版本），确认无遗漏
