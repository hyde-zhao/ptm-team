---
story_id: STORY-013-03
name: design-ppdcs-analyzer + deliverable-renderer 路径迁移
tier: M
wave: B
change_id: CR-013-ptm-tde-ppdcs-phase
workflow_id: WF-PTM-TEAM-20260520-001
status: ready-for-verification
depends_on: [STORY-013-01, STORY-013-02]
blocks: []
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-03：design-ppdcs-analyzer + deliverable-renderer 路径迁移

## 目标

对 PPDCS 协调器和交付物渲染器执行路径迁移。这两个 Skill 消费 Wave A 中已完成迁移的 5 设计 Skill 和 coverage-verifier 的产出路径。

## 受影响文件

| 文件 | 改动量 | 说明 |
|------|:---:|------|
| `skills/design-ppdcs-analyzer/SKILL.md` | ~19 处 | PPDCS 协调器，匹配 LC→设计 Skill，拓扑绑定校验 |
| `skills/deliverable-renderer/SKILL.md` | ~16 处 | 交付物生成，消费所有阶段产出 |

## 路径迁移映射

### design-ppdcs-analyzer（~19 处）

| 旧路径 | 新路径 |
|--------|--------|
| `analysis/integration/` | `mfq/integration/` |
| `analysis/plan/` | `process/plan/` |
| `analysis/scenarios/` | `kym/scenarios/` |
| `analysis/m-analysis/` | `mfq/m-analysis/` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |

### deliverable-renderer（~16 处）

| 旧路径 | 新路径 |
|--------|--------|
| `analysis/scenarios/` | `kym/scenarios/` |
| `analysis/integration/` | `mfq/integration/` |
| `analysis/coverage/` | `ppdcs/coverage/` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |
| `delivery/` | `ppdcs/delivery/` |

## 依赖说明

- **runtime 依赖 STORY-013-01**：协调器引用的 5 设计 Skill 产出路径（`ppdcs/ppdcs/`、`ppdcs/pc/`）需 Wave A 先完成迁移
- **runtime 依赖 STORY-013-02**：deliverable-renderer 引用的覆盖率报告路径（`ppdcs/coverage/`）需 coverage-verifier 先完成迁移

## 验收标准

- [ ] design-ppdcs-analyzer 所有旧路径替换无误（~19 处）
- [ ] deliverable-renderer 所有旧路径替换无误（~16 处）
- [ ] deliverable-renderer 的 `delivery/` → `ppdcs/delivery/` 是关键变更
- [ ] 两个文件的原始执行流程和契约保持不变
- [ ] 跨文件一致性：analyzer 引用的路径与 Wave A 已迁移的 5 设计 Skill 产出一致
