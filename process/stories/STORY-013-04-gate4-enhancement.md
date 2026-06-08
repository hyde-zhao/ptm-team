---
story_id: STORY-013-04
name: GATE-4 增强（gate-spec.md + checkpoint-manager）
tier: M
wave: B
change_id: CR-013-ptm-tde-ppdcs-phase
workflow_id: WF-PTM-TEAM-20260520-001
status: draft
depends_on: []
blocks: []
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-04：GATE-4 增强（gate-spec.md + checkpoint-manager）

## 目标

将 PPDCS Exit Gate（GATE-4）从骨架升级为完整检查项（P1-P7 自检 + 4 项人工确认），并同步更新 checkpoint-manager 中的 GATE-4 描述。

## 受影响文件

| 文件 | 改动量 | 说明 |
|------|:---:|------|
| `docs/ptm-tde/gate-spec.md` | ~30 行 | GATE-4 增加 P1-P7 自检项 + 4 项人工确认项 |
| `skills/checkpoint-manager/SKILL.md` | ~20 处 | 路径更新（`analysis/` → 分阶段路径）+ GATE-4 检查项对齐 |

## GATE-4 增强内容

### 自检项（P1-P7）

| # | 检查项 | 通过条件 |
|---|--------|----------|
| P1 | PPDCS 设计过程完整 | `ppdcs/ppdcs/` 下每个 LC 都有设计过程文件，方法匹配 plan 推荐 |
| P2 | PC 文件完整 | `ppdcs/pc/` 下每个 LC 都有 16 列 PC 文件 |
| P3 | PC 拓扑绑定回链 | PC 中真实端口/设备/链路可回链至 LC `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` |
| P4 | 双层覆盖率验证 | `ppdcs/coverage/` 存在覆盖率报告：需求覆盖 = 100%，测试点覆盖 ≥ 95% |
| P5 | 因子覆盖验证 | 所有 `factor_bindings` 的因子在 PC 中有覆盖 |
| P6 | 交付物完整 | `ppdcs/delivery/` 含测试方案 + 测试用例两个文件 |
| P7 | 交付物字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

### 人工确认项（4 项）

| 确认项 | 说明 |
|--------|------|
| PPDCS 设计方法 | 每个 LC 的 PPDCS 方法选择是否合理，设计步骤是否完整 |
| 物理用例质量 | PC 编号、组网描述、测试步骤、预期结果是否满足标准 |
| 覆盖率结果 | 需求覆盖率、测试点覆盖率是否达标，未覆盖项是否可接受 |
| 拓扑绑定 | needs-confirmation 项是否已处理或记录为风险 |

## 依赖说明

- **无上游依赖**：GATE-4 增强不依赖任何 Skill 的路径迁移结果
- 可与 Wave A 和 STORY-013-03 并行实施

## 验收标准

- [ ] gate-spec.md GATE-4 章节包含 P1-P7 自检项（每项含通过条件）
- [ ] gate-spec.md GATE-4 章节包含 4 项人工确认项（每项含说明）
- [ ] checkpoint-manager SKILL.md 中 GATE-4 描述与 gate-spec 对齐
- [ ] checkpoint-manager SKILL.md 的旧路径引用（`analysis/` 等）已更新
- [ ] 现有 GATE-1~GATE-3 内容不被修改
- [ ] 不引入新的 Gate 编号
