---
dispatch:
  agent_role: meta-dev
  story_id: STORY-011-04
  story_slug: agent-flow-update
  workflow_id: WF-PTM-TEAM-20260520-001
  change_id: CR-011-ptm-tde-kym-phase
  wave_id: Wave-B
  mode: subagent
  tool_name: lld-designer
  semantic: lld-generation
  status: completed
  agent_id: meta-dev-lld-011-04
  tool_name: lld-designer
  spawned_at: "2026-06-02T16:00:00+08:00"
  completed_at: "2026-06-02T16:10:00+08:00"
  created_at: "2026-06-02T15:30:00+08:00"
---

# Handoff: STORY-011-04 — Agent 流程更新（新顺序）

## Story 摘要

更新 `agents/ptm-tde.md`，将 KYM 阶段的步骤顺序改为：feature-parser（1.1）→ kym Skill（1.2）→ scenario-discovery（1.3）。初始化流程创建 `kym/mission-understanding/` 目录。追踪链注释标注 v2 前瞻方向。

## 关键设计决策（来自 HLD v1.1）

1. **执行顺序重设计**：feature-parser 先完成结构化需求解析（1.1），kym Skill 消费其产物执行使命理解访谈（1.2），scenario-discovery 消费 kym 产出进行场景发现（1.3）
2. **HARD-GATE 原则**：主 Agent 按固定步骤顺序（1.1 → 1.2 → 1.3）强制执行，防止用户跳过 kym Skill 直接进入 scenario-discovery。GATE-2 N1 检查 mission-statement.md 存在性作为第二道防线。
3. **初始化流程增强**：KYM 阶段初始化时创建 `kym/mission-understanding/` 目录（配合 GATE-1 #8 检查）
4. **追踪链注释**：在现有追踪链下方添加 v2 方向注释（◇ 标记），标注 KYM 前置节点（需求文档 → KYM → 场景发现）、TSP 节点、CAE-R 节点
5. **skill-references 更新**：如果 `docs/ptm-tde/skill-references.md` 中存在 KYM 阶段的 Skill 列表，需要反映新顺序

## 涉及文件

| 文件 | 变更类型 | 预计行数 |
|------|----------|----------||
| `agents/ptm-tde.md` | 修改 | +25 行 |

**具体修改点**：
- KYM 阶段步骤描述（§三阶段框架）：`feature-parser → scenario-discovery` → `feature-parser → kym Skill → scenario-discovery`
- 阶段总览表（§阶段与 Gate 总览）：KYM 行新增 kym Skill
- 运行时工作目录（§运行时工作目录）：`kym/` 描述新增 `mission-understanding/` 子目录
- 追踪链章节：在现有追踪链下方添加 v2 方向注释
- 初始化流程：新增创建 `kym/mission-understanding/` 目录的说明

## 参考上下文

- HLD: `process/HLD-CR-011.md` §14.1（KYM 阶段完整流程）、§11.4（完整追踪链）、§9（模块职责）
- 源文件: `agents/ptm-tde.md`（当前 KYM 阶段步骤顺序 + 追踪链）
- data-flow-spec: `docs/ptm-tde/data-flow-spec.md`（数据实体流转关系）
- Story 011-01 LLD: `process/stories/STORY-011-01-kym-skill-LLD.md`（kym Skill 的设计细节，用于参考集成点）
- Story 011-02 LLD: `process/stories/STORY-011-02-kym-path-migration-LLD.md`（路径迁移后的目录结构）

## LLD 14 章节要求

1. Goal / 2. Requirements / 3. Module Split / 4. Code Structure & File Impact / 5. Data Model / 6. API/Interface Design / 7. Core Processing Flow / 8. Technical Design Details / 9. Safety & Performance / 10. Test Design / 11. Implementation Steps / 12. Risks & Challenges / 13. Rollback & Release / 14. Definition of Done

## 输出路径

- LLD 文档: `process/stories/STORY-011-04-agent-flow-update-LLD.md`
- CP5 自动预检: `process/checks/CP5-STORY-011-04-agent-flow-update-LLD-IMPLEMENTABILITY.md`
