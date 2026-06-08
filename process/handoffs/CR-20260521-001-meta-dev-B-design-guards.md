---
handoff_id: CR-20260521-001-meta-dev-B-design-guards
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-20260521-001
target_role: meta-dev
target_agent_id: 019e4963-ffd1-7bf2-9799-58fc4e0b715d
status: completed
created_at: "2026-05-21T15:16:16+08:00"
---

# Handoff - Design Skill Guardrail Rework

## Dispatch

| Field | Value |
|---|---|
| mode | spawn_agent |
| agent_id | 019e4963-ffd1-7bf2-9799-58fc4e0b715d |
| tool_name | spawn_agent |
| spawned_at | 2026-05-21T15:16:16+08:00 |
| completed_at | 2026-05-21T15:26:46+08:00 |

## Scope

Update PPDCS method Skills and F/Q analyzers so topology roles and real TOPO instances cannot be misused as factor values or Pairwise parameters.

## Owned Files

- `skills/parameter-design/SKILL.md`
- `skills/combination-design/SKILL.md`
- `skills/process-design/SKILL.md`
- `skills/data-design/SKILL.md`
- `skills/state-design/SKILL.md`
- `skills/f-analyzer/SKILL.md`
- `skills/q-analyzer/SKILL.md`

## Completion Summary

- Added PPDCS method guardrails so topology objects cannot enter factor/data/state/Pairwise value spaces.
- Added F/Q guardrails for real topology object references.
- Preserved trace chain v6 and public factor-library consumption rules.

