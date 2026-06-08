---
dispatch:
  agent_role: meta-dev
  story_id: STORY-011-03
  story_slug: gate-self-check-enhancement
  workflow_id: WF-PTM-TEAM-20260520-001
  change_id: CR-011-ptm-tde-kym-phase
  wave_id: Wave-B
  mode: subagent
  tool_name: lld-designer
  semantic: lld-generation
  status: completed
  agent_id: meta-dev-lld-011-03
  tool_name: lld-designer
  spawned_at: "2026-06-02T15:45:00+08:00"
  completed_at: "2026-06-02T15:55:00+08:00"
  created_at: "2026-06-02T15:15:00+08:00"
---

# Handoff: STORY-011-03 — Gate 自检增强

## Story 摘要

增强 GATE-1 Entry Gate 和 GATE-2 KYM Exit Gate 的检查项，补充使命理解相关自检和人工确认项，并同步 checkpoint-manager SKILL.md 的 Gate 描述。

## 关键设计决策（来自 HLD v1.1 §12）

**GATE-1 新增**：
- #8: KYM 产物目录就绪（自检，`kym/mission-understanding/` 目录可创建且可写入）
- #9: mission-statement 模板可访问（自检，kym Skill 模板可被读取）

**GATE-2 新增**：
- N1: 使命文档存在（自检，`kym/mission-understanding/mission-statement.md` 可读且非空）
- N2: 启发式探索已执行（自检，≥2 个 CIDTESTD 维度已覆盖）
- N3: 范围边界已界定（自检+人工，scope 和 dont_test 声明）
- N4: 待澄清问题已收集（自检+人工，confirmation_gaps 状态）

**GATE-2 人工确认项新增**：
- 使命声明（做什么/为什么做/为谁做）
- 测试关注点优先级
- 范围边界
- 启发式探索覆盖

## 涉及文件

| 文件 | 变更类型 | 预计行数 |
|------|----------|----------|
| `docs/ptm-tde/gate-spec.md` | 修改 | +40 行 |
| `skills/checkpoint-manager/SKILL.md` | 修改 | +20 行 |

## 参考上下文

- HLD: `process/HLD-CR-011.md` §12（门控设计）
- gate-spec 源文件: `docs/ptm-tde/gate-spec.md`（GATE-1 和 GATE-2 章节）
- checkpoint-manager 源文件: `skills/checkpoint-manager/SKILL.md`（GATE-1/GATE-2 描述）

LLD 输出路径：`process/stories/STORY-011-03-gate-self-check-enhancement-LLD.md`
CP5 预检路径：`process/checks/CP5-STORY-011-03-gate-self-check-enhancement-LLD-IMPLEMENTABILITY.md`
