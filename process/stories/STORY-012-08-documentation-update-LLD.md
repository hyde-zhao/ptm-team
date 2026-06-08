---
story_id: "STORY-012-08"
title: "文档更新（CR-INDEX + STATE.md + agents/ptm-tde.md + CR-012 close）"
story_slug: "documentation-update"
lld_version: "1.0"
tier: "S"
status: "ready-for-review"
confirmed: false
created_by: "meta-dev"
created_at: "2026-06-02T23:00:00+08:00"
confirmed_by: ""
confirmed_at: ""
shared_fragments: []
open_items: 0
---

# LLD: STORY-012-08 — 文档更新

> 文件名格式：`STORY-012-08-documentation-update-LLD.md`，其中 `story_slug` 复用 Story 卡片中的 `documentation-update`。
>
> 本文档是 `STORY-012-08` 的低层设计（Low-Level Design），需纳入全部目标 Story 的 LLD 统一确认，并满足当前 Wave 的 `dev_gate` 后方可进入实现。
>
> 本 Story 是 CR-012 的最后一个 Story（Wave D 末尾），在 STORY-012-01 ~ 012-07 全部实现并通过验证后执行，更新索引和文档以反映 CR-012 完成状态。

## 1. Goal

修改 4 个文件（CR-INDEX.yaml、STATE.md、agents/ptm-tde.md、CR-012 变更文件），将 CR-012 标记为 `closed`，更新 `active_change` 指向 CR-013，刷新 MFQ 阶段描述反映 v3.0 方法论成果，追加关闭记录，使全流程文档与实现状态一致。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- **F01**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `status` 从 `active` 改为 `closed`
- **F02**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `phase` 从 `story-execution` 改为 `delivered`
- **F03**：`process/changes/CR-INDEX.yaml` 中 CR-012 新增 `closed` 字段，值为当天日期（`YYYY-MM-DD` 格式）
- **F04**：`process/changes/CR-INDEX.yaml` 中 CR-012 的 `notes` 字段追加完成摘要（Story 数、Waves、v3.0 方法论、候选汇总、GATE-3 HARD-STOP）
- **F05**：`process/STATE.md` 中 `active_change` 字段从 `CR-012-ptm-tde-mfq-phase` 修改为 `CR-013-ptm-tde-ppdcs-phase`
- **F06**：`process/STATE.md` 中 History 表追加 CR-012 close 事件记录
- **F07**：`process/STATE.md` 中 `pending_llds` 和 `lld_design_batch` 状态清理（若仍存在）
- **F08**：`agents/ptm-tde.md` 中 MFQ Phase 行更新为包含 v3.0 版本号、步骤数和关键特性的描述
- **F09**：`agents/ptm-tde.md` 中 GATE-3 描述增加对 CR-012 产物的引用（覆盖矩阵、候选汇总、⛔ HARD-STOP 机制）
- **F10**：`process/changes/CR-012-ptm-tde-mfq-phase.md` 中实施记录表追加一行关闭记录

### 2.2 Non-Functional

- **NF01（一致性）**：CR-INDEX.yaml 和 STATE.md 对 CR-012 的状态描述一致（均为 closed/delivered）
- **NF02（有效性）**：CR-INDEX.yaml 修改后必须为合法 YAML，可通过 `python -c "import yaml; yaml.safe_load(open(...))"` 校验
- **NF03（完整性）**：STATE.md 修改后 frontmatter 完整，不丢失任何现有字段
- **NF04（最小变更）**：不在修改范围内添加无关内容，不改动其他 CR 记录

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| CR-INDEX.yaml | CR 仓库变更跟踪索引 | 修改 CR-012 条目：status→closed，phase→delivered，加 closed 日期和完成摘要 |
| STATE.md | 工作流运行时状态 | 修改 active_change 指向，清理 LLD 批次状态，追加 History |
| agents/ptm-tde.md | ptm-tde 主 Agent 编排器 | 更新三阶段框架中的 MFQ Phase 描述行，反映 v3.0 方法论成果 |
| CR-012-ptm-tde-mfq-phase.md | CR-012 变更文件 | 在实施记录表末尾追加关闭事件 |

## 4. 代码结构与文件影响范围

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `process/changes/CR-INDEX.yaml` | CR-012 条目：`status: "active"` → `"closed"`；`phase: "story-execution"` → `"delivered"`；新增 `closed: "2026-06-02"` 字段；`stories: 8` → 保持不变；`notes` 扩展为包含完成摘要（v3.0 方法论、Waves、GATE-3 HARD-STOP、候选汇总） |
| 修改 | `process/STATE.md` | `active_change` 字段：`CR-012-ptm-tde-mfq-phase（...）` → `CR-013-ptm-tde-ppdcs-phase（pending）`；History 表追加 CR-012 close 事件行；若 `parallel_execution.lld_design_batch` 仍存在则清理 `pending_llds` 字段 |
| 修改 | `agents/ptm-tde.md` | 三阶段框架 ASCII 图中 MFQ Phase 行（约第 52 行）更新为含 v3.0 版本信息；GATE-3 描述新增覆盖矩阵 + 候选汇总 + ⛔ HARD-STOP 引用（§GATE-3 段落，约第 298 行起） |
| 修改 | `process/changes/CR-012-ptm-tde-mfq-phase.md` | 实施记录表末尾追加：`2026-06-02T23:00 \| CR-012 closed：8 Stories / 4 Waves 全部完成，MFQ 阶段 v3.0 方法论落地。STORY-012-01~012-07 全部 CP7 verified。` |

## 5. 数据模型与持久化设计

无新增数据模型 / 持久化变更。

所有修改均为现有文件内字段更新，不新增文件、不新增持久化结构。

| 文件 | 受影响字段 | 原值 | 新值 | 约束 |
|------|-----------|------|------|------|
| CR-INDEX.yaml | `changes[CR-012].status` | `active` | `closed` | 枚举：closed\|active\|pending |
| CR-INDEX.yaml | `changes[CR-012].phase` | `story-execution` | `delivered` | 枚举：draft\|story-execution\|delivered |
| CR-INDEX.yaml | `changes[CR-012].closed` | （不存在） | `2026-06-02` | `YYYY-MM-DD` |
| CR-INDEX.yaml | `changes[CR-012].notes` | `扩展范围：...` | 扩展为完成摘要 | 自由文本 |
| STATE.md | `active_change` | `CR-012-...（...）` | `CR-013-ptm-tde-ppdcs-phase（pending）` | 自由文本 |
| STATE.md | `parallel_execution.lld_design_batch.pending_llds` | `3（012-06/07/08 待设计）` | `0（全部完成）` | 非负整数 |

## 6. API / Interface 设计

本 Story 不涉及 API、Tool、MCP 或程序接口。所有文件为纯文档 / 配置文件，由以下对象消费：

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| CR-INDEX.yaml（文件读取） | 无 | YAML 结构 | meta-po、`scripts/check_cr_tracking_consistency.py`（若存在） | 供 CR 跟踪一致性查询 |
| STATE.md（文件读取） | 无 | Markdown + YAML frontmatter | meta-po、state-router Skill | 供工作流阶段路由 |
| agents/ptm-tde.md（文件读取） | 无 | Markdown | ptm-tde Agent（运行时读取自身定义） | 供 Agent 执行编排 |
| CR-012 CR 文件（文件读取） | 无 | Markdown | meta-po、审计 | 供 CR 生命周期追溯 |

## 7. 核心处理流程

本 Story 处理流程为纯顺序文本编辑，不涉及分支或异步逻辑：

1. **读取 CR-INDEX.yaml**，定位 CR-012 条目，修改 `status`、`phase`、新增 `closed`、扩展 `notes`，保存后运行 YAML 合法性校验
2. **读取 STATE.md**，修改 `active_change` 字段（frontmatter 行和 Current Work 表中行同时更新），清理 `lld_design_batch.pending_llds`，在 History 表末尾追加事件
3. **读取 agents/ptm-tde.md**，修改三阶段框架 ASCII 图中的 MFQ Phase 行（约第 52 行），在 GATE-3 段落中增加覆盖矩阵 + 候选汇总 + ⛔ HARD-STOP 引用
4. **读取 CR-012-ptm-tde-mfq-phase.md**，在实施记录表 `| 2026-06-02T21:00 | CR-012 范围更新完成...` 行之后追加关闭行
5. **验收验证**：逐项执行 AC01-AC08 的 grep/YAML/格式检查

## 8. 技术设计细节

### 8.1 CR-INDEX.yaml 修改点

目标条目当前状态（`process/changes/CR-INDEX.yaml` 第 58-68 行）：

```yaml
  - change_id: "CR-012-ptm-tde-mfq-phase"
    name: "ptm-tde MFQ 阶段改造（扩展范围）"
    status: "active"
    ...
```

修改为：

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
    notes: "扩展范围：纳入 mfq-analysis-step-by-step.md v3.0 全部方法论。8 Stories / 4 Waves 完成。M v3.0 10步（场景步骤驱动）+ F v3.0 9步 + Q v3.0 6步（逐 TSP 驱动）+ 候选汇总 + GATE-3 HARD-STOP。"
```

**关键规则**：
- 保持 YAML 缩进为 2 空格
- `closed` 字段放在 `approved` 之后、`phase` 之前（与已 closed 的 CR-010/CR-011 格式一致）
- `notes` 必须为单行字符串（与其他 CR 条目格式一致），不使用多行 YAML 字符串

### 8.2 STATE.md 修改点

**修改点 A — active_change**：

有两处需要修改：

1. **frontmatter**（第 16 行）：`active_change: CR-012-ptm-tde-mfq-phase（CP3 approved → Story 分解中）` → `active_change: CR-013-ptm-tde-ppdcs-phase（pending，下一阶段候选）`

2. **Current Work 表**（第 19 行）：对应的表格行也需要同步更新

**修改点 B — lld_design_batch 清理**：

`parallel_execution.lld_design_batch` 节（第 142-154 行）：
- `pending_llds: 3（012-06/07/08 待设计）` → `pending_llds: 0（全部完成）`
- `phase: lld-design（CP3 approved → LLD 并行写作中）` → `phase: complete（全部 8 Story LLD 已产出）`

**修改点 C — History 追加**：

在 History 表末尾（第 140 行之后）追加：
```markdown
| 2026-06-02T23:00:00+08:00 | meta-po/current session | CR-012 closed：8 Stories / 4 Waves 全部完成，MFQ v3.0 落地（M 10步 + F 9步 + Q 6步 + 候选汇总 + GATE-3 HARD-STOP），CR-INDEX.yaml 更新，STATE.md active_change 切换为 CR-013。 |
```

### 8.3 agents/ptm-tde.md 修改点

**修改点 A — MFQ Phase 行更新**：

三阶段框架 ASCII 图中（当前第 50-57 行），MFQ Phase 行：

```
      → MFQ Phase: m-analyzer → f-analyzer → q-analyzer → test-point-integrator → design-planner
```

修改为：

```
      → MFQ Phase: m-analyzer (v3.0, 10步, 场景步骤驱动, 产出覆盖矩阵+标签)
                     → f-analyzer (v3.0, 9步, 逐 TSP 驱动, 消费 [F→] 标签)
                     → q-analyzer (v3.0, 6步, 逐 TSP 驱动, 消费 [Q→] 标签)
                     → test-point-integrator (含候选汇总, ⛔ HARD-STOP 确认)
                     → design-planner (适配 TSP.covered_scenario_segments)
```

**注意**：新行比原框架缩进多 21 个空格（`→ MFQ Phase: ` 前缀），以与现有框架图中的 KYM Phase 行对齐风格。实际缩进为 `                     → `（21 空格 + `→ `）。

**修改点 B — GATE-3 描述增强**：

在 GATE-3 MFQ Exit Gate 描述（约第 298-300 行）中，现有内容：

```markdown
### GATE-3 MFQ Exit Gate（自检 + 人工确认）
**确认内容**：M/F/Q 分析质量、LC 整合一致性、设计计划、公共因子消费
**硬门控**：禁止在用户 approve 前进入 PPDCS 阶段。
```

修改为：

```markdown
### GATE-3 MFQ Exit Gate（自检 + 人工确认）
**确认内容**：M/F/Q 分析质量（v3.0 方法论）、Scenario-TSP 覆盖矩阵、步骤标签 [M]/[F→]/[Q→]、LC 整合一致性、候选汇总（⛔ HARD-STOP 确认）、设计计划、公共因子消费
**自检项编号**：M1-M7 + W1-W2（详见 `docs/ptm-tde/gate-spec.md`）
**硬门控**：禁止在用户 approve 前进入 PPDCS 阶段。
```

### 8.4 CR-012 变更文件修改点

在 `process/changes/CR-012-ptm-tde-mfq-phase.md` 第 299 行（实施记录表最后一行）之后追加：

```markdown
| 2026-06-02T23:00 | CR-012 closed：8 Stories / 4 Waves 全部完成。MFQ v3.0 方法论落地：M 分析 10 步（场景步骤驱动，产出覆盖矩阵+步骤标签）、F 分析 9 步（逐 TSP 驱动，消费 [F→] 标签）、Q 分析 6 步（逐 TSP 驱动，消费 [Q→] 标签）、候选汇总（⛔ HARD-STOP 确认）、GATE-3 增强（M1-M7+W1-W2 编号）。全部 Story CP7 verified。 |
```

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 数据完整性 | 修改后 CR-INDEX.yaml 必须通过 `yaml.safe_load()` 校验；STATE.md frontmatter 不得丢失现有字段 | AC07 + AC08：YAML 校验 + frontmatter 完整性检查 |
| 文件有效性 | 使用 `git diff` 逐文件审查修改内容，确保只修改预期行 | 人工 diff 审查 |
| 可恢复性 | Git 提供版本回退；修改前确认工作区干净 | `git status` 检查 |

本 Story 不涉及性能敏感操作（4 个文件、~30 行文本修改）。

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 | 对应 AC |
|---|---|---|---|---|---|
| CR-012 状态更新 | STORY-012-01~07 全部完成 | 修改 CR-INDEX.yaml 中 CR-012 条目的 status/phase/closed/notes | status=closed，phase=delivered，closed=YYYY-MM-DD，notes 含 v3.0 方法论摘要 | AC01：grep `status: "closed"`；AC02：grep `phase: "delivered"`；AC03：grep `closed: "2026-06-02"` | AC01/AC02/AC03 |
| CR-INDEX.yaml YAML 有效性 | 修改完成 | `python -c "import yaml; yaml.safe_load(open('process/changes/CR-INDEX.yaml'))"` | 无异常，正常解析 | AC07 命令行验证 | AC07 |
| STATE.md active_change 切换 | 修改完成 | 读取 STATE.md 的 `active_change` 字段 | 值包含 `CR-013-ptm-tde-ppdcs-phase`，不包含 `CR-012` | AC04：grep `active_change.*CR-013` | AC04 |
| STATE.md frontmatter 完整性 | 修改完成 | 读取 STATE.md frontmatter | 所有原字段保留（workflow_id/status/workflow_mode/current_phase/created_at/updated_at），active_change 已更新 | AC08：逐字段对比 | AC08 |
| agents/ptm-tde.md MFQ 描述 | 修改完成 | grep agents/ptm-tde.md 中 MFQ Phase 相关内容 | 包含 `v3.0`、`10步`、`9步`、`6步`、`场景步骤驱动`、`逐 TSP 驱动`、`覆盖矩阵`、`候选汇总` 中的至少 3 项 | AC05：grep 关键词 | AC05 |
| CR-012 关闭记录 | 修改完成 | 读取 CR-012 CR 文件的实施记录表最后一行 | 包含日期和 CR-012 closed 事件描述 | AC06：grep `CR-012 closed` | AC06 |
| 不影响其他 CR 记录 | 修改完成 | `grep -c "change_id:" process/changes/CR-INDEX.yaml` | 条目数量不变（CR 列表不增不减） | 人工确认第 2 行（第 5 行 labels 不计入） | NF04 |

## 11. 实施步骤

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| TASK-012-08-01 | 修改 | `process/changes/CR-INDEX.yaml` | 修改 CR-012 条目：status→closed，phase→delivered，新增 closed 日期，扩展 notes 为完成摘要。保持缩进和格式与其他 closed CR 一致。保存后执行 YAML 校验 | CR-012 状态更新 + YAML 有效性 |
| TASK-012-08-02 | 修改 | `process/STATE.md` | 修改 active_change（frontmatter + Current Work 表双处），清理 parallel_execution.lld_design_batch.pending_llds，History 表追加 CR-012 close 事件行 | STATE.md active_change 切换 + frontmatter 完整性 |
| TASK-012-08-03 | 修改 | `agents/ptm-tde.md` | 修改三阶段框架 ASCII 图 MFQ Phase 行（含 v3.0 版本号和步骤数），GATE-3 描述增加覆盖矩阵+候选汇总+HARD-STOP 引用 | agents/ptm-tde.md MFQ 描述 |
| TASK-012-08-04 | 修改 | `process/changes/CR-012-ptm-tde-mfq-phase.md` | 实施记录表末尾追加关闭事件行 | CR-012 关闭记录 |
| TASK-012-08-05 | 验证 | 全部 4 个文件 | 执行 AC01-AC08 全部验收标准的 grep/YAML/格式检查，确认 8 项 AC 全部通过 | 全部测试场景 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

无。本 Story 改动量小（~30 行）、范围明确（4 个文件）、无实现灰区。所有修改内容均在 Story 卡片和 HLD §15-16 中完整定义。

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| — | 无 | — | — | — | — | — |

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| STATE.md 中 current_phase 不一致 | 低（Story 范围仅修改 active_change） | current_phase 不在本 Story 范围。frontmatter 值为 `delivered`，Current Work 表为 `story-execution`，均由 CR-013 或下一次阶段推进时统一处理。本 Story 只确保不新增不一致 |
| agents/ptm-tde.md MFQ Phase 行缩进对齐 | 低（视觉不一致不影响功能） | 新行使用 21 空格缩进（匹配现有 KYM Phase 行风格） |
| CR-INDEX.yaml notes 超长行 | 低（YAML 单行字符串无长度限制） | 使用 YAML 双引号字符串，保持为一行；如需换行可改为 `>` 折叠块 |

### OPEN / Spike 跟踪

无。本 Story 无未决技术点。

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| — | — | 无 | — | — |

## 13. 回滚与发布策略

- **发布方式**：Git 单 commit（本 Story 为 CR-012 Wave D 的最后一个 Story，应与前序 Story 一起或独立提交）
- **回滚触发条件**：CR-INDEX.yaml YAML 格式错误；STATE.md frontmatter 损坏；agents/ptm-tde.md 描述与实现产物不一致
- **回滚动作**：`git revert <commit-hash>` 恢复 4 个文件到修改前状态，或直接从 Git 历史恢复原文件内容
- **回滚验证**：执行 AC07 + AC08 确认文件有效性，执行 AC01-AC06 确认回滚干净

## 14. Definition of Done

- [ ] TASK-012-08-01 至 TASK-012-08-04 全部完成（4 个文件修改到位）
- [ ] TASK-012-08-05 验收通过（8 项 AC 全部 PASS）
- [ ] CR-INDEX.yaml 通过 `yaml.safe_load()` 校验（AC07）
- [ ] STATE.md frontmatter 完好，active_change 指向 CR-013（AC04/AC08）
- [ ] agents/ptm-tde.md MFQ Phase 行含 v3.0 描述（AC05）
- [ ] CR-012 变更文件实施记录表有关闭行（AC06）
- [ ] 不修改 CR-INDEX.yaml 中其他 CR 条目
- [ ] CP6 编码完成检查通过（`process/checks/CP6-STORY-012-08-documentation-update-CODING-DONE.md`）
- [ ] `DEV-LOG.md` 已追加

## 人工确认区

> **CP5 — Story LLD 可实现性门**
> meta-dev 先写入 `process/checks/CP5-STORY-012-08-documentation-update-LLD-IMPLEMENTABILITY.md` 自动预检结果。
> meta-po 收齐全部目标 Story 的 LLD、CP4 自动预检摘要和 CP5 自动预检后，再生成并提示用户审查 `checkpoints/CP5-ALL-STORIES-LLD-BATCH.md`。
> 用户统一确认全部目标 Story 的 LLD 后，仍需满足当前 Wave、依赖门控与文件所有权门控方可进入实现。

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | 第 2 节 F01-F10 映射 8 项 AC（AC01-AC08）；第 10 节 6 个测试场景全部有 AC 对应 |
| 2 | 与 HLD / ADR 一致 | 待检查 | 第 3/4 节文件清单与 HLD §15-16 一致；GATE-3 HARD-STOP 引用与 HLD §11 STOP-01~05 一致；Story 为 CR-012 最后一步 |
| 3 | 文件影响范围明确 | 待检查 | 第 4 节：4 个文件、4 项修改、每项有具体变更内容 |
| 4 | 接口契约完整 | 待检查 | 第 6 节：4 个文件均为文档/配置文件，由 meta-po/state-router/ptm-tde Agent 消费，无 API 接口 |
| 5 | 测试与 dev_gate 可计算 | 待检查 | 第 10 节：6 个测试场景，每个有操作、预期结果、验证方式和 AC 对应；dev_gate = STORY-012-07 verified + Wave D 可执行 |
| 6 | clarification queue 已收敛 | 待检查 | 第 12.1 节：无未决项，0 OPEN/Spike |

**人工确认回复**：

请直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```

- `approve`：LLD 设计合理，允许进入实现。
- `修改: <具体修改点>`：指出具体修改点后由 meta-dev 更新重提。
- `reject`：设计方向有根本问题，需重新设计。

**人工审查结果回填**：

- 结论：`approved | changes_requested | rejected`
- 审查人：
- 审查时间：
- 修改意见：
- 风险接受项：
