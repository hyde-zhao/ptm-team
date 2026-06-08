---
dispatch:
  agent_role: meta-dev
  story_id: STORY-011-02
  story_slug: kym-path-migration
  workflow_id: WF-PTM-TEAM-20260520-001
  change_id: CR-011-ptm-tde-kym-phase
  wave_id: Wave-A
  mode: subagent
  tool_name: lld-designer
  semantic: lld-generation
  status: ready
  created_at: "2026-06-02T14:30:00+08:00"
---

# Handoff: STORY-011-02 — KYM 阶段路径迁移

## Story 摘要

将 KYM 阶段两个 Skill（feature-parser、scenario-discovery）的输出路径从旧 `analysis/` 迁至新 `kym/`，一次完成无过渡期。

## 关键设计决策（来自 HLD v1.1 §18.3）

1. **一次完成，无过渡期**：ptm-tde 为独立运行时项目，无外部消费者依赖旧路径
2. **严格 KYM 边界**：只迁移 KYM 阶段路径（`analysis/feature-input/` → `kym/feature-input/`、`analysis/scenarios/` → `kym/scenarios/`），不触碰 MFQ/PPDCS 路径（`analysis/m-analysis/`、`analysis/f-analysis/`、`design/ppdcs/`）
3. 旧目录不主动删除（保留 git 历史），但后续不再写入

## 路径迁移映射

| 旧路径 | 新路径 | 出现位置 |
|--------|--------|----------|
| `analysis/feature-input/` | `kym/feature-input/` | feature-parser SKILL.md ~5 处、scenario-discovery SKILL.md 输入引用 |
| `analysis/scenarios/` | `kym/scenarios/` | scenario-discovery SKILL.md ~7 处（输出路径 + 示例 + 说明引用）|
| `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` | scenario-discovery SKILL.md |

## 不迁移的路径（MFQ/PPDCS 归属后续 CR）

- `analysis/m-analysis/` → CR-012
- `analysis/f-analysis/` → CR-012
- `design/ppdcs/` → CR-013

## 涉及文件

| 文件 | 变更类型 | 预计行数 |
|------|----------|----------|
| `skills/feature-parser/SKILL.md` | 修改 | ±5 行 |
| `skills/scenario-discovery/SKILL.md` | 修改 | ±7 行 |

## 参考上下文

- HLD: `process/HLD-CR-011.md` §18.3（路径迁移最终状态）、§20（受影响文件矩阵）
- feature-parser 源文件: `skills/feature-parser/SKILL.md`（找到所有 `analysis/feature-input/` 引用）
- scenario-discovery 源文件: `skills/scenario-discovery/SKILL.md`（找到所有 `analysis/` 引用，区分 KYM vs MFQ/PPDCS）

## 验证方法

```bash
grep -rn "analysis/feature-input\|analysis/scenarios" skills/feature-parser/SKILL.md skills/scenario-discovery/SKILL.md
```
预期返回 0 结果。

## LLD 14 章节要求

1. Goal / 2. Requirements / 3. Module Split / 4. Code Structure & File Impact / 5. Data Model / 6. API/Interface Design / 7. Core Processing Flow / 8. Technical Design Details / 9. Safety & Performance / 10. Test Design / 11. Implementation Steps / 12. Risks & Challenges / 13. Rollback & Release / 14. Definition of Done

## 输出路径

- LLD 文档: `process/stories/STORY-011-02-kym-path-migration-LLD.md`
- CP5 自动预检: `process/checks/CP5-STORY-011-02-kym-path-migration-LLD-IMPLEMENTABILITY.md`
