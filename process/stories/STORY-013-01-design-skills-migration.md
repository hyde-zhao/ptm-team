---
story_id: STORY-013-01
name: 5 设计 Skill 路径迁移 + 方法论占位
tier: M
wave: A
change_id: CR-013-ptm-tde-ppdcs-phase
workflow_id: WF-PTM-TEAM-20260520-001
status: ready-for-verification
depends_on: []
blocks: [STORY-013-03]
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-01：5 设计 Skill 路径迁移 + 方法论占位

## 目标

对 5 个 PPDCS 设计 Skill 执行路径迁移（`analysis/`/`design/` → `kym/`/`mfq/`/`ppdcs/`/`process/plan/`），并各增加方法论占位节。

## 受影响文件

| 文件 | 路径迁移量 | 方法论占位 | 总改动 |
|------|:---:|:---:|:---:|
| `skills/process-design/SKILL.md` | ~12 处 | ~15 行 | ~27 |
| `skills/parameter-design/SKILL.md` | ~11 处 | ~15 行 | ~26 |
| `skills/data-design/SKILL.md` | ~10 处 | ~15 行 | ~25 |
| `skills/combination-design/SKILL.md` | ~10 处 | ~15 行 | ~25 |
| `skills/state-design/SKILL.md` | ~13 处 | ~15 行 | ~28 |

## 路径迁移映射

| 旧路径 | 新路径 |
|--------|--------|
| `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` |
| `analysis/integration/test-data.md` | `mfq/integration/test-data.md` |
| `analysis/plan/design-plan.md` | `process/plan/design-plan.md` |
| `analysis/plan/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` |
| `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` |
| `analysis/m-analysis/ppdcs-annotation.md` | `mfq/m-analysis/ppdcs-annotation.md` |
| `analysis/factor-usage/` | `mfq/factor-usage/` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |

## 方法论占位模板

```markdown
## 方法论细则（用户可定制）

> 以下为设计方法的指导框架。用户可根据项目特点和领域知识补充具体规则。

### [方法名称] 设计步骤

**目标**：[方法解决什么设计问题]

**核心步骤**：
1. [步骤 1]
2. [步骤 2]
3. ...

**关键决策点**：
- [决策 1]
- [决策 2]

**示例**（防火墙领域）：
[具体示例]

**下游影响**：
[设计产出如何影响 PC 生成和覆盖率验证]
```

各 Skill 方法论维度见 §二。

## 验收标准

- [ ] 每个文件的 `分析/` → `mfq/` 路径替换无误
- [ ] 每个文件的 `分析/plan/` → `processing/plan/` 路径替换无误
- [ ] 每个文件的 `分析/scenarios/` → `kym/scenarios/` 路径替换无误
- [ ] 每个文件的 `design/ppdcs/` → `ppdcs/ppdcs/` 路径替换无误
- [ ] 每个文件的 `design/pc/` → `ppdcs/pc/` 路径替换无误
- [ ] 每个文件新增方法论占位节（统一模板格式）
- [ ] 原始章节和已有内容保持不变
- [ ] `grep "分析/\|design/" skills/<name>/SKILL.md` 仅保留非 ppdcs 相关的正确引用
