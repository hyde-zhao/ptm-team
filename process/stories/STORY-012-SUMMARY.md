---
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
total_stories: 8
total_waves: 4
created_at: "2026-06-02T23:00:00+08:00"
source_hld: process/HLD-CR-012.md
source_hld_version: "1.1"
source_hld_status: confirmed
design_doc: /home/hyde/projects/llm-wiki/llm-wiki/work/studies/ptm-team/team-design/ptm-tde/mfq-analysis-step-by-step.md
design_doc_version: "v3.0"
---

# STORY-012-SUMMARY：CR-012 ptm-tde MFQ 阶段改造 Story 分解

## 1. DAG 依赖图

```
Wave A（并行，tier=S，无上游依赖）
  ├── STORY-012-01：MFQ 路径迁移（5 Skill ~70 处）
  │     └── 产出：5 个 Skill 文件中旧路径零残留
  │
  └── STORY-012-02：MFQ Exit Gate 增强（gate-spec.md + checkpoint-manager）
        └── 产出：GATE-3 Checklist 编号 M1-M7+W1-W2，HARD-STOP 标记
         ◆
         │  (012-01 和 012-02 并行，无文件冲突)
         ▼
Wave B（tier=M，依赖 Wave A 012-01）
  └── STORY-012-03：M 分析器 v3.0 重写（357→~500 行，7→10 步）
        └── 产出：覆盖矩阵 + 步骤标签 + TSP + 候选列表 (M)
         ◆
         ├──────────────────┬──────────────────┐
         ▼                  ▼                  ▼
Wave C（并行，tier=M，依赖 Wave B 012-03）
  ├── STORY-012-04：F 分析器 v3.0 重写（314→~450 行，8→9 步，消费 [F→] 标签）
  │     └── 产出：耦合测试点 + 耦合因子候选列表 (F)
  │
  └── STORY-012-05：Q 分析器 v3.0 重写（257→~370 行，5→6 步，消费 [Q→] 标签）
        └── 产出：质量测试点 + 质量因子候选列表 (Q)
         ◆
         └──────────────────┘
         ▼
Wave D（m-tier=M/S，依赖 Wave C 012-04+012-05）
  ├── STORY-012-06：上下游 Skill 适配（test-point-integrator + design-planner）
  │     └── 产出：integrator 消费覆盖矩阵+TSP 新格式；planner 消费 covered_segments
  │      ◆
  │      ▼
  ├── STORY-012-07：候选汇总 + skill-references 更新 + STOP 协议落地
  │     └── 产出：test-point-integrator 新增候选汇总步骤；skill-references.md v3.0
  │      ◆
  │      ▼
  └── STORY-012-08：文档更新（CR-INDEX + STATE.md + agents/ptm-tde.md + CR-012 close）
        └── 产出：CR-012 标记 closed，MFQ 阶段文档更新完成
```

### 依赖关系矩阵

| Story | 依赖 | 被依赖 | 并行组 |
|-------|------|--------|--------|
| 012-01 | — | 012-03, 012-04, 012-05, 012-06, 012-07 | Wave A |
| 012-02 | — | — | Wave A |
| 012-03 | 012-01 | 012-04, 012-05, 012-06 | Wave B |
| 012-04 | 012-01, 012-03 | 012-06 | Wave C / fq-analyzers |
| 012-05 | 012-01, 012-03 | 012-06 | Wave C / fq-analyzers |
| 012-06 | 012-01, 012-03, 012-04, 012-05 | 012-07 | Wave D |
| 012-07 | 012-06 | 012-08 | Wave D |
| 012-08 | 012-07 | — | Wave D |

## 2. Wave 分组

### Wave A（tier=S，可并行）

| Story | 名称 | 文件 | 改动量 |
|-------|------|------|:---:|
| STORY-012-01 | MFQ 路径迁移 | skills/{m,f,q}-analyzer/SKILL.md, skills/test-point-integrator/SKILL.md, skills/design-planner/SKILL.md | ~70 处 |
| STORY-012-02 | MFQ Exit Gate 增强 | docs/ptm-tde/gate-spec.md, skills/checkpoint-manager/SKILL.md | ~30 行 |

**里程碑**：旧路径零残留 + Gate 编号统一

### Wave B（tier=M，串行）

| Story | 名称 | 文件 | 改动量 |
|-------|------|------|:---:|
| STORY-012-03 | M 分析器 v3.0 重写 | skills/m-analyzer/SKILL.md | ~200 行 |

**里程碑**：M 分析 10 步完成，12 项验收标准 PASS

### Wave C（tier=M，并行组 fq-analyzers）

| Story | 名称 | 文件 | 改动量 |
|-------|------|------|:---:|
| STORY-012-04 | F 分析器 v3.0 重写 | skills/f-analyzer/SKILL.md | ~150 行 |
| STORY-012-05 | Q 分析器 v3.0 重写 | skills/q-analyzer/SKILL.md | ~120 行 |

**里程碑**：F/Q 分析器逐 TSP 驱动模式完成

### Wave D（tier=M/S，串行）

| Story | 名称 | 文件 | 改动量 |
|-------|------|------|:---:|
| STORY-012-06 | 上下游 Skill 适配 | skills/test-point-integrator/SKILL.md, skills/design-planner/SKILL.md | ~50 行 |
| STORY-012-07 | 候选汇总 + skill-references + STOP 协议 | skills/test-point-integrator/SKILL.md, docs/ptm-tde/skill-references.md | ~50 行 |
| STORY-012-08 | 文档更新 | process/changes/CR-INDEX.yaml, process/STATE.md, agents/ptm-tde.md, process/changes/CR-012-ptm-tde-mfq-phase.md | ~30 行 |

**里程碑**：CR-012 closed，全部 MFQ 阶段 v3.0 文档就绪

## 3. 文件所有权

| 文件 | 拥有 Story | 冲突类型 |
|------|-----------|----------|
| `skills/m-analyzer/SKILL.md` | 012-01（路径）, 012-03（重写） | Wave 顺序隔离（A→B） |
| `skills/f-analyzer/SKILL.md` | 012-01（路径）, 012-04（重写） | Wave 顺序隔离（A→C） |
| `skills/q-analyzer/SKILL.md` | 012-01（路径）, 012-05（重写） | Wave 顺序隔离（A→C） |
| `skills/test-point-integrator/SKILL.md` | 012-01（路径）, 012-06（适配）, 012-07（候选汇总） | Wave 顺序隔离（A→D→D） |
| `skills/design-planner/SKILL.md` | 012-01（路径）, 012-06（适配） | Wave 顺序隔离（A→D） |
| `docs/ptm-tde/gate-spec.md` | 012-02（Gate 增强） | 唯一 owner |
| `skills/checkpoint-manager/SKILL.md` | 012-02（Gate 增强） | 唯一 owner |
| `docs/ptm-tde/skill-references.md` | 012-07（更新） | 唯一 owner |
| `process/changes/CR-INDEX.yaml` | 012-08（close） | 唯一 owner |
| `process/STATE.md` | 012-08（close） | 唯一 owner |
| `agents/ptm-tde.md` | 012-08（close） | 唯一 owner |

**文件冲突说明**：test-point-integrator/SKILL.md 被 012-01、012-06、012-07 三个 Story 修改，但通过 Wave 顺序隔离（A→D 串行），不会产生冲突。

## 4. 工作量统计

| Wave | Story 数 | 类别 | 改动量 | 类型 |
|------|:---:|------|:---:|------|
| A | 2 | 路径迁移 + Gate 增强 | ~100 行 | S |
| B | 1 | M 分析器重写 | ~200 行 | M |
| C | 2 | F/Q 分析器重写 | ~270 行 | M |
| D | 3 | 适配 + 候选汇总 + 文档 | ~130 行 | S-M |
| **合计** | **8** | | **~700 行** | |

## 5. 关键风险与缓解

| 风险 | 影响 Story | 缓解措施 |
|------|-----------|----------|
| 012-03 M 分析器重写遗漏旧版隐性知识 | 012-03, 012-04, 012-05 | 重写时逐章检查旧版；保留旧版直到 CP7 通过 |
| 012-06 test-point-integrator 新旧格式不兼容 | 012-06, 012-07 | graceful degradation：新字段缺失时退化为旧版行为 |
| test-point-integrator 三个 Story 修改同一文件（012-01+06+07） | 012-06, 012-07 | Wave 顺序隔离（A→D→D），每次在前一个 Story 基础上修改 |

## 6. Story 卡片文件清单

| Story ID | 文件路径 |
|----------|----------|
| STORY-012-01 | `process/stories/STORY-012-01-mfq-path-migration.md` |
| STORY-012-02 | `process/stories/STORY-012-02-mfq-exit-gate-enhance.md` |
| STORY-012-03 | `process/stories/STORY-012-03-m-analyzer-v3-rewrite.md` |
| STORY-012-04 | `process/stories/STORY-012-04-f-analyzer-v3-rewrite.md` |
| STORY-012-05 | `process/stories/STORY-012-05-q-analyzer-v3-rewrite.md` |
| STORY-012-06 | `process/stories/STORY-012-06-upstream-downstream-adapt.md` |
| STORY-012-07 | `process/stories/STORY-012-07-candidate-summary-stop-protocol.md` |
| STORY-012-08 | `process/stories/STORY-012-08-documentation-update.md` |

## 7. 全局验收标准（CR-012 整体完成判定）

在所有 Story 完成后，执行以下全局验证：

1. **路径残留**：`grep -rn "analysis/" skills/{m,f,q}-analyzer/ skills/test-point-integrator/ skills/design-planner/` 返回 0
2. **Gate 编号**：`grep -c "M[1-7]\|W[1-2]" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md` 每个文件 >= 9
3. **M 分析 v3.0**：`skills/m-analyzer/SKILL.md` 包含覆盖矩阵 + 步骤标签 + 候选列表
4. **F 分析 v3.0**：`skills/f-analyzer/SKILL.md` 包含 `[F→]` 标签消费 + 逐 TSP 驱动
5. **Q 分析 v3.0**：`skills/q-analyzer/SKILL.md` 包含 `[Q→]` 标签消费 + 逐 TSP 驱动
6. **候选汇总**：`skills/test-point-integrator/SKILL.md` 包含候选去重合并 + 用户确认步骤
7. **STOP 协议**：`grep -rn "HARD.STOP\|禁止.*自行" skills/{m,f,q}-analyzer/ skills/test-point-integrator/ skills/checkpoint-manager/ docs/ptm-tde/gate-spec.md` 返回 >= 3
8. **文档一致性**：CR-INDEX.yaml 中 CR-012 状态为 closed
