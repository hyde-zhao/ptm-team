---
story_id: STORY-013-02
name: coverage-verifier 路径迁移
tier: S
wave: A
change_id: CR-013-ptm-tde-ppdcs-phase
workflow_id: WF-PTM-TEAM-20260520-001
status: ready-for-verification
depends_on: []
blocks: [STORY-013-03]
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-02：coverage-verifier 路径迁移

## 目标

对 coverage-verifier Skill 执行路径迁移（~23 处），这是 PPDCS 阶段改动量最大的单个文件。

## 受影响文件

| 文件 | 改动量 | 说明 |
|------|:---:|------|
| `skills/coverage-verifier/SKILL.md` | ~23 处 | 跨阶段消费者，读 kym + mfq + ppdcs 全部阶段产出 |

## 路径迁移映射

| 旧路径 | 新路径 | 出现频率 |
|--------|--------|:---:|
| `analysis/scenarios/` | `kym/scenarios/` | ~4 处 |
| `analysis/integration/` | `mfq/integration/` | ~5 处 |
| `analysis/factor-usage/` | `mfq/factor-usage/` | ~3 处 |
| `analysis/m-analysis/` | `mfq/m-analysis/` | ~2 处 |
| `design/ppdcs/` | `ppdcs/ppdcs/` | ~3 处 |
| `design/pc/` | `ppdcs/pc/` | ~4 处 |
| `analysis/coverage/` | `ppdcs/coverage/` | ~2 处 |

## 验收标准

- [ ] 所有旧路径 `analysis/*` 替换为对应新路径
- [ ] 所有旧路径 `design/*` 替换为对应新路径
- [ ] 覆盖率报告的产出路径从 `analysis/coverage/` 改为 `ppdcs/coverage/`
- [ ] 原始执行流程和验收标准保持不变
- [ ] `grep "analysis/\|design/" skills/coverage-verifier/SKILL.md` 无残留
