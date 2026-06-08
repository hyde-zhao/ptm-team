---
handoff_id: CR-20260521-001-meta-dev-A-topology-core
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-20260521-001
target_role: meta-dev
target_agent_id: 019e4963-cc54-7d73-8437-6602514e9e1b
status: completed
created_at: "2026-05-21T15:16:16+08:00"
---

# Handoff - Topology Core Skill Rework

## Dispatch

| Field | Value |
|---|---|
| mode | spawn_agent |
| agent_id | 019e4963-cc54-7d73-8437-6602514e9e1b |
| tool_name | spawn_agent |
| spawned_at | 2026-05-21T15:16:16+08:00 |
| completed_at | 2026-05-21T15:26:46+08:00 |

## Scope

Update the core MFQ chain so M/CAE, LC integration, design planning, and PPDCS coordination separate test factors, topology roles, and real topology objects.

## Owned Files

- `skills/m-analyzer/SKILL.md`
- `skills/test-point-integrator/SKILL.md`
- `skills/design-ppdcs-analyzer/SKILL.md`
- `skills/design-planner/SKILL.md`

## Completion Summary

- Added CAE topology role constraints and `{{topo_role:*}}` usage.
- Added TP/LC/PPDCS topology fields and LC topology binding contract.
- Preserved `factor_bindings` as the test-factor contract and introduced `topology_bindings` as a parallel topology contract.

