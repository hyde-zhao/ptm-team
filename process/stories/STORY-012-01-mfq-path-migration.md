---
story_id: STORY-012-01
story_name: MFQ 路径迁移
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: S
wave: A
depends_on: []
blocks: [STORY-012-03, STORY-012-04, STORY-012-05, STORY-012-06, STORY-012-07]
status: ready-for-verification
file_ownership:
  - skills/m-analyzer/SKILL.md
  - skills/f-analyzer/SKILL.md
  - skills/q-analyzer/SKILL.md
  - skills/test-point-integrator/SKILL.md
  - skills/design-planner/SKILL.md
parallel_safe: true
---

# STORY-012-01：MFQ 路径迁移

## 1. 目标

将 5 个 MFQ Skill 文件中所有硬编码的 `analysis/` 路径前缀替换为 CR-010 建立的三阶段目录结构（`kym/` / `mfq/` / `process/plan/`），旧路径零残留。

## 2. 范围

- **修改文件**：5 个 Skill 文件，全部使用 `sed` 类精确替换
- **改动量**：~70 处路径引用更新，~0 行净增（纯替换，不增删行）
- **不改动**：Skill 的业务逻辑、步骤编号、方法论内容

### 路径迁移映射

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `analysis/feature-input/` | `kym/feature-input/` | 跨阶段读取 KYM 产出 |
| `analysis/scenarios/` | `kym/scenarios/` | 跨阶段读取 KYM 产出 |
| `analysis/m-analysis/` | `mfq/m-analysis/` | MFQ 阶段内部 |
| `analysis/f-analysis/` | `mfq/f-analysis/` | MFQ 阶段内部 |
| `analysis/q-analysis/` | `mfq/q-analysis/` | MFQ 阶段内部 |
| `analysis/integration/` | `mfq/integration/` | MFQ 阶段内部 |
| `analysis/factor-usage/` | `mfq/factor-usage/` | MFQ 阶段内部 |
| `analysis/plan/` | `process/plan/` | 跨阶段边界产物 |

## 3. 验收标准

- [ ] **AC01**：`grep -rn "analysis/" skills/m-analyzer/SKILL.md skills/f-analyzer/SKILL.md skills/q-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` 返回 0 结果（零残留）
- [ ] **AC02**：`grep -rn "analysis/m-analysis\|analysis/f-analysis\|analysis/q-analysis\|analysis/integration\|analysis/factor-usage" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/ skills/design-planner/` 返回 0 结果
- [ ] **AC03**：`grep -rn "analysis/scenarios\|analysis/feature-input" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/` 返回 0 结果
- [ ] **AC04**：每个 Skill 文件至少包含对应新路径引用（`grep -c "mfq/" skills/m-analyzer/SKILL.md` > 0 等）
- [ ] **AC05**：`design-planner/SKILL.md` 中 `process/plan/` 替代了 `analysis/plan/`
- [ ] **AC06**：5 个 Skill 文件的 YAML frontmatter 和 description 字段未因路径替换而损坏（`grep "^---$" skills/{m,f,q}-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md | wc -l` 返回 10，即每个文件恰好 2 个 `---`）
- [ ] **AC07**：`grep -rn "analysis/" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/ skills/design-planner/ | grep -v "analysis/"` 结果只有注释区或路径说明性文本，不存在旧路径文件名引用
- [ ] **AC08**：`wc -l` 行数变化 ≤ ±5 行（纯替换不增删行）

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 | ~旧路径出现次数 |
|------|----------|----------|:---:|
| `skills/m-analyzer/SKILL.md` | 修改 | `analysis/` → `kym/` / `mfq/`（含 `scripts/excel_coupling_tool.py` 输出路径） | 18 |
| `skills/f-analyzer/SKILL.md` | 修改 | `analysis/` → `kym/` / `mfq/`（含工具脚本输出路径） | 16 |
| `skills/q-analyzer/SKILL.md` | 修改 | `analysis/` → `kym/` / `mfq/` | 7 |
| `skills/test-point-integrator/SKILL.md` | 修改 | `analysis/` → `kym/` / `mfq/`（含全部 M/F/Q 读取路径和 integrator 输出路径） | 11 |
| `skills/design-planner/SKILL.md` | 修改 | `analysis/` → `mfq/` / `process/plan/`（plan 输出跨阶段边界） | 17 |

## 5. 依赖关系

- **上游**：无（Wave A 并行，不依赖其他 Story）
- **下游**：STORY-012-03（M 分析器重写需基于迁移后路径）、STORY-012-04、STORY-012-05、STORY-012-06、STORY-012-07（均消费迁移后路径）

## 6. 实施注意事项

- **精确替换**：使用 `sed` 逐目录替换，不要用全局正则。例如先替换 `analysis/m-analysis/` → `mfq/m-analysis/`，再替换 `analysis/scenarios/` → `kym/scenarios/`。替换顺序不重要（目标路径不重叠）。
- **路径上下文敏感**：注意段落路径（如 `analysis/m-analysis/` 作为前缀）和完整文件路径（如 `analysis/m-analysis/test-points.md`）两者都要覆盖。
- **禁止手动 mkdir**：本 Story 只做 Skill 文件内的路径替换，不创建目录。目录结构已由 CR-010 建立。
- **禁止修改方法论**：只做路径文本替换，不触碰步骤编号、流程逻辑、PPDCS 特征定义等内容。如有路径替换导致句子语法错误（罕见），只修正语法，不改语义。
- **design-planner 特殊处理**：`analysis/plan/` → `process/plan/` 是跨阶段边界替换，确保替换后引用 `process/plan/design-plan.md` 而非 `mfq/plan/`。
- **并行安全**：本 Story 与 STORY-012-02 无文件冲突（后者改 gate-spec.md + checkpoint-manager），可并行执行。
- **验证后不提交**：替换完成后执行 AC01-AC08 全部 grep 验证，PASS 后标记完成。不在此 Story 中 commit（由 Wave 统一管理）。
