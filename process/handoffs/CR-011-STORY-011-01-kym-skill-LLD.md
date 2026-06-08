---
dispatch:
  agent_role: meta-dev
  story_id: STORY-011-01
  story_slug: kym-skill-creation
  workflow_id: WF-PTM-TEAM-20260520-001
  change_id: CR-011-ptm-tde-kym-phase
  wave_id: Wave-A
  mode: subagent
  tool_name: lld-designer
  semantic: lld-generation
  status: ready
  created_at: "2026-06-02T14:30:00+08:00"
---

# Handoff: STORY-011-01 — 创建 kym Skill 并注册

## Story 摘要

新建 `skills/kym/SKILL.md`（CIDTESTD 8 维度五阶段流程），并在 `skills/README.md` 和 `docs/ptm-tde/skill-references.md` 中注册。

## 关键设计决策（来自 HLD v1.1）

1. **五阶段流程**：阶段零（上下文预加载 feature-parser 产物）→ 阶段一（初始化）→ 阶段二（维度扫描 CIDTESTD 8 维度地图）→ 阶段三（深度访谈逐维度一问一答）→ 阶段四（文档化 mission-statement.md）
2. **CIDTESTD 8 维度**：C(Customers) / I(Information) / D(Developers) / E(Equipment) / S(Schedule) / T(Test Items) / D(Deliverables) / R(Risks)
3. **上下文预加载**：阶段零读取 `kym/feature-input/` 中 feature-parser 产物，自动预填 I/T 维度信息
4. **范畴守卫**：kym Skill 只收集信息，禁止编写测试用例
5. **risks 格式**：`{area, likelihood, impact, action}` 结构化格式
6. **HARD-GATE**：KYM 确认前禁止进入测试设计

## 涉及文件

| 文件 | 变更类型 | 预计行数 |
|------|----------|----------|
| `skills/kym/SKILL.md` | 新建 | ~400 行 |
| `skills/README.md` | 修改 | +5 行 |
| `docs/ptm-tde/skill-references.md` | 修改 | +8 行 |

## 参考上下文

- HLD: `process/HLD-CR-011.md` §9（模块职责）、§10（集成契约）、§14（关键流程）、§21（Gotchas）
- 数据流规格: `docs/ptm-tde/data-flow-spec.md` 实体 1（KYM 产出 mission-statement.md）
- feature-parser 参考: `skills/feature-parser/SKILL.md`（了解现有 Skill 格式 + feature-parser 输入输出）
- 现有 Skill 格式参考: `skills/scenario-discovery/SKILL.md`

## LLD 14 章节要求

1. Goal / 2. Requirements / 3. Module Split / 4. Code Structure & File Impact / 5. Data Model / 6. API/Interface Design / 7. Core Processing Flow / 8. Technical Design Details / 9. Safety & Performance / 10. Test Design / 11. Implementation Steps / 12. Risks & Challenges / 13. Rollback & Release / 14. Definition of Done

## 输出路径

- LLD 文档: `process/stories/STORY-011-01-kym-skill-LLD.md`
- CP5 自动预检: `process/checks/CP5-STORY-011-01-kym-skill-LLD-IMPLEMENTABILITY.md`
