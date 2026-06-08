---
change_id: CR-011-ptm-tde-kym-phase
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-01T12:00:00+08:00"
created_by: meta-po
status: closed
approved_at: "2026-06-02T00:00:00+08:00"
approved_by: user
closed_at: "2026-06-02T19:00:00+08:00"
closed_by: meta-po（CP8 交付就绪）
impact_level: medium
rollback_to: story-execution
approval_source: user-request
depends_on: CR-010-ptm-tde三阶段框架改造
followed_by: n/a
---

# CR-011 — ptm-tde KYM 阶段改造（内容层）

## 变更请求摘要

完成 KYM 阶段的全部内容层改造：新建 `kym` Skill（使命理解 + 启发式探索 + 使命澄清），迁移 KYM 阶段相关 Skill 的路径引用（`analysis/` → `kym/`），并补充 KYM Exit Gate 的阶段专属检查项。

**依赖**：CR-010（框架改造）必须已完成——`agents/ptm-tde.md` 已包含三阶段框架，`gate-spec.md` 已定义 KYM Exit Gate。

## 背景

### KYM 阶段在框架中的位置

```
Entry Gate → [KYM Phase] → KYM Exit Gate → MFQ Phase → ...
                 │
                 ├─ 子步骤 1.1: kym Skill（本 CR 新建）
                 ├─ 子步骤 1.2: feature-parser
                 └─ 子步骤 1.3: scenario-discovery
```

### 本 CR 的三项工作

1. **新建 `skills/kym/SKILL.md`**：任务理解 + 启发式探索 + 使命澄清
2. **路径迁移**：KYM 阶段涉及的 3 个 Skill 的 `analysis/` 路径 → `kym/` 路径
3. **KYM Exit Gate 增强**：补充使命理解相关的自检和人工检查项

## 一、新建 kym Skill

### 文件

**新建 `skills/kym/SKILL.md`**

### Skill 框架

```yaml
name: kym
description: >-
  Know Your Mission — 理解测试任务的使命、上下文和边界，产出使命文档。
  通过启发式探索引导用户明确测试目标、关注点和范围。
argument-hint: "特性名称或输入材料路径"
user-invokable: true
status: active
```

### 执行步骤

| 步骤 | 名称 | 产出 |
|------|------|------|
| 1 | 任务上下文收集 | 读取 `input/` 需求文件，识别项目类型、产品领域、技术栈、利益相关者 |
| 2 | 启发式探索 | **用户补充维度和问题**（见下方占位框架） |
| 3 | 使命澄清与范围界定 | 使命声明（做什么/为什么/为谁做）、测试关注点优先级、范围边界和排除项 |
| 4 | 输出使命文档 | `kym/mission-understanding/mission-statement.md` + `confirmation_gaps` |

### 启发式探索占位框架

> 以下维度和问题为占位模板。用户将补充具体的启发式维度、引导问题和分析方法。

```markdown
### 启发式探索维度（用户可定制）

> 以下维度用于引导使命理解。用户可根据项目特点和领域知识补充具体维度和问题。

#### 维度 1：[待用户命名]
**引导问题**：
- [待用户补充]
- ...

#### 维度 2：[待用户命名]
**引导问题**：
- [待用户补充]
- ...

（更多维度按用户需要添加）
```

### 输出

`kym/mission-understanding/mission-statement.md`，包含：
- 使命声明（目标、理由、受益者）
- 测试关注点优先级
- 范围边界和排除项
- confirmation_gaps（待澄清问题）
- Deferred Ideas（超出当前范围但有价值的想法）

### 下游消费

`feature-parser` 和 `scenario-discovery` 读取 `kym/mission-understanding/mission-statement.md` 作为输入上下文。

## 二、路径迁移

### 受影响 Skill 文件

| Skill 文件 | 路径引用更新 | 改动量 |
|-----------|-------------|--------|
| `skills/kym/SKILL.md` | 新建，使用 `kym/mission-understanding/` | 新文件 |
| `skills/feature-parser/SKILL.md` | `analysis/feature-input/` → `kym/feature-input/`（~5 处） | ~5 |
| `skills/scenario-discovery/SKILL.md` | `analysis/scenarios/` → `kym/scenarios/`、`analysis/feature-input/` → `kym/feature-input/`（~7 处） | ~7 |

### 路径迁移映射（KYM 阶段专用）

| 旧路径 | 新路径 |
|--------|--------|
| `analysis/feature-input/` | `kym/feature-input/` |
| `analysis/scenarios/` | `kym/scenarios/` |
| `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` |

### 跨阶段路径引用（KYM Skill 不修改，只读取）

`skills/scenario-discovery/SKILL.md` 中引用了以下路径（本 CR 不修改这些路径，由对应 CR 负责）：
- `analysis/m-analysis/` → 由 CR-012 处理
- `analysis/f-analysis/` → 由 CR-012 处理
- `design/ppdcs/` → 由 CR-013 处理

**注意**：`scenario-discovery` 被多个下游 Skill 引用，且自身引用 `confirmed-scenarios.md`。本 CR 只迁移 KYM 阶段内的路径（`analysis/feature-input/` 和 `analysis/scenarios/`），不触碰 MFQ/PPDCS 路径。

## 三、KYM Exit Gate 增强

### 更新文件

| 文件 | 改动 |
|------|------|
| `docs/ptm-tde/gate-spec.md` | KYM Exit Gate 增加：使命文档完整性自检项 + 使命澄清人工确认项 |
| `skills/checkpoint-manager/SKILL.md` | 增加 KYM 使命理解相关的自检和人工检查项 |
| `agents/ptm-tde.md` | KYM 阶段步骤 1.1 加入 kym Skill，初始化流程更新 |

### KYM Exit Gate 新增自检项

| # | 检查项 | 通过条件 |
|---|--------|----------|
| N1 | 使命文档存在 | `kym/mission-understanding/mission-statement.md` 可读 |
| N2 | 启发式探索已执行 | 使命文档包含至少 2 个启发式维度的分析记录 |
| N3 | 范围边界已界定 | 使命文档包含明确的范围边界和排除项 |
| N4 | 待澄清问题已收集 | `confirmation_gaps` 非空或已全部 resolved |

### KYM Exit Gate 新增人工确认项

| 确认项 | 说明 |
|--------|------|
| 使命声明 | 做什么、为什么做、为谁做是否准确反映用户意图 |
| 测试关注点优先级 | 排序是否符合项目实际 |
| 范围边界 | 排除项是否合理，是否有遗漏 |
| 启发式探索覆盖 | 维度是否足够，问题是否到位 |

## 四、注册与文档更新

| 文件 | 改动 |
|------|------|
| `skills/README.md` | 注册 kym Skill |
| `docs/ptm-tde/skill-references.md` | 添加 kym Skill 条目（KYM 阶段） |

## 受影响文件汇总

| 文件 | 变更类型 |
|------|----------|
| `skills/kym/SKILL.md` | **新建** |
| `skills/feature-parser/SKILL.md` | 路径更新 |
| `skills/scenario-discovery/SKILL.md` | 路径更新 |
| `agents/ptm-tde.md` | KYM 阶段步骤 1.1 加入 kym Skill |
| `docs/ptm-tde/gate-spec.md` | KYM Exit Gate 增加检查项 |
| `skills/checkpoint-manager/SKILL.md` | 增加使命理解检查项 |
| `skills/README.md` | 注册 kym Skill |
| `docs/ptm-tde/skill-references.md` | 添加 kym Skill 条目 |

## 验证方法

1. `skills/kym/SKILL.md` 存在且包含使命理解、启发式探索占位、使命澄清章节
2. `grep -rn "analysis/feature-input\|analysis/scenarios" skills/feature-parser/SKILL.md skills/scenario-discovery/SKILL.md` 返回 0 结果（旧路径已全部迁移）
3. `agents/ptm-tde.md` 中 KYM 阶段包含 kym Skill 作为步骤 1.1
4. `docs/ptm-tde/gate-spec.md` 中 KYM Exit Gate 包含使命理解相关自检和人工检查项
5. `skills/README.md` 列出 kym Skill

## Story 分解

| Story ID | 名称 | Wave | Tier | 涉及文件 | 依赖 |
|----------|------|------|------|---------|------|
| STORY-011-01 | 创建 kym Skill 并注册 | A | S | `skills/kym/SKILL.md` (NEW), `skills/README.md`, `docs/ptm-tde/skill-references.md` | 无 |
| STORY-011-02 | KYM 阶段路径迁移 | A | S | `skills/feature-parser/SKILL.md`, `skills/scenario-discovery/SKILL.md` | 无 |
| STORY-011-03 | Gate 自检增强 (GATE-1 + GATE-2) | B | M | `docs/ptm-tde/gate-spec.md`, `skills/checkpoint-manager/SKILL.md` | Wave A |
| STORY-011-04 | Agent 流程更新 (kym 集成) | B | S | `agents/ptm-tde.md` | Wave A |

## 实施记录

| 时间 | 事件 |
|------|------|
| 2026-06-01 | CR 创建，状态 draft |
| 2026-06-02 00:00 | CR approved，Story 分解完成（4 Stories in 2 Waves），进入 Phase 2 HLD 设计 |
| 2026-06-02 09:00 | CP3 HLD 人工确认通过（含修正1-删除过渡期 + 修正2-feature-parser/kym 顺序重设计） |
| 2026-06-02 12:00 | 数据流规格文档 `docs/ptm-tde/data-flow-spec.md` 委托 meta-se 完成 |
| 2026-06-02 14:30 | Phase 3 LLD 并行设计启动，4 Stories LLD 全部完成（14 章节 14/14 完整） |
| 2026-06-02 16:30 | CP5 自动预检全部完成（24/24 PASS），CP4 汇入 CP5 Decision Brief |
| 2026-06-02 18:00 | CP5 人工确认 approved：全部 3 项决策（DQ-01/02/03）通过，全部 4 Story LLD 进入 lld-approved |
| 2026-06-02 18:15 | Wave A 并行实施完成：STORY-011-01（kym Skill 新建 450 行）CP6 PASS + STORY-011-02（路径迁移 12 处替换）CP6 PASS |
| 2026-06-02 18:30 | Wave B 并行实施完成：STORY-011-03（Gate 增强 +18 行）CP6 PASS + STORY-011-04（Agent 更新 8 处修改）CP6 PASS |
| 2026-06-02 18:35 | CP7 全局验证完成：10 项 grep 验证全部 PASS，4 Stories 全部 verified |
| 2026-06-02 19:00 | CP8 交付就绪：自动预检 20 项 PASS，人工终验通过，CR 关闭。后续跟踪台账已创建（T-01 断点恢复 + T-02 关键词调优） |
