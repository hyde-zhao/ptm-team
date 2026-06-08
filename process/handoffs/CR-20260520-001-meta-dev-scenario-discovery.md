---
handoff_id: HOFF-CR-20260520-001-META-DEV
from_agent: meta-po
to_agent: meta-dev
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-20260520-001
story_id: CR-20260520-001
wave_id: wave-change
status: completed
created_at: "2026-05-20T14:43:38+08:00"
dispatch:
  required: true
  mode: "subagent"
  platform: "codex"
  agent_role: "meta-dev"
  agent_path: ".codex/agents/meta-dev.toml"
  tool_name: "spawn_agent"
  agent_id: "019e4423-fea7-7132-9196-32197e7882b3"
  agent_name: "dev-kong"
  thread_id: "019e4423-fea7-7132-9196-32197e7882b3"
  spawned_at: "2026-05-20T14:49:00+08:00"
  resumed_at: ""
  completed_at: "2026-05-20T14:53:29+08:00"
  evidence: "Parent session spawned native meta-dev agent 019e4423-fea7-7132-9196-32197e7882b3 (dev-kong). Agent modified skills/scenario-discovery/SKILL.md, left skills/README.md unchanged with rationale, and reported verification commands passed. Earlier codex exec subprocess was stopped at 2026-05-20T14:48:28+08:00 before product-file diffs."
  fallback_reason: ""
  approved_by: ""
  approved_at: ""
---

# Meta-Dev Handoff - Scenario Discovery Skill Rediscovery Change

## Task

Modify `skills/scenario-discovery/SKILL.md` so functional scenario seeds are not treated as final scenarios. The Skill must explicitly rediscover, brainstorm, restructure, and converge deployment-oriented scenario artifacts.

## Minimal Context

Read:

- `process/STATE.md`
- `process/changes/CR-20260520-001.md`
- `skills/scenario-discovery/SKILL.md`
- `skills/README.md`
- If present: `analysis/scenarios/scenario-deployment-policy-route.md`
- If present: `input/TGFW测试组网图集合.md`
- If present: `analysis/scenarios/scenario-analysis.md`

Useful external reference found during orchestration:

- `/home/hyde/projects/tcs/policy_route/analysis/scenarios/scenario-analysis.md`
- `/home/hyde/projects/tcs/policy_route/input/TGFW测试组网图集合.md`

Do not load full process history or unrelated skills.

## Required Changes

- Add input document type recognition:
  - raw requirement
  - functional scenario seed
  - deployment scenario draft
  - confirmed scenario artifact
- Make functional scenario seed enter scenario rediscovery; it must not become final output directly.
- Add rediscovery and brainstorming dimensions:
  - primary scenario
  - extended scenario
  - lifecycle
  - reliability
  - performance
  - usability
  - configuration order
  - abnormal operation
  - TOPO
  - interface shape
  - exit action
- Add scope convergence rules from explicit user constraints or project memory, for example IPv6 moves to `out_of_scope_candidates` when user says only IPv4.
- Add project target-shape learning:
  - if project-confirmed `analysis/scenarios/scenario-deployment-policy-route.md` exists, learn its structure first.
  - preferred structure includes document positioning, ptm-tde deliverable statement, scenario dimension overview, Topology model, scenario list, topology source mapping, scenario details, structured supplement, atomic operation summary, atomic-ops, Knowledge References, Existing Tool Usage Seed, Tool Abstraction Draft, Confirmation Gaps.
- Add functional scenario to deployment scenario merge rules and require Seed-to-Scenario Mapping.
- Add TGFW topology input rules:
  - if `input/TGFW测试组网图集合.md` exists, read it and prioritize its topologies.
  - output Topology Catalog and topology source mapping.
  - each scenario includes `topology_ref`, source, Mermaid, device/port/link tables.
  - do not invent topology unless listed in `confirmation_gaps`.
  - default policy route topology selection:
    - basic/match/order/maintenance/abnormal: `node2_dut1_tg1_link3`
    - HA: `node4_dut2_tg1_sw2_link7`
    - performance/capacity: `node2_dut1_tg1_link5`
    - PPPoE egress: `node3_dut1_tg1_pppoe_link4` as extension suggestion.
- Add atomic-ops rules:
  - if project confirms atomic-ops as atomic-ops, use `source_type=atomic-ops`.
  - `action_source_ref` directly references `op_id`.
  - do not invent middle identifiers such as `AS-CLI-001`.
  - `capability_status=ready/gap/unknown`.
  - output fields: `action_source_ref | source_type | capability_status | invoke_contract | observe_contract | scenario_refs`.
- Add two-layer output:
  - scenario details
  - ptm-tde scenario discovery structured supplement
- Add policy route brainstorming dimensions:
  - match dimensions
  - ingress interface shape
  - forwarding action
  - egress mode/interface type
  - risk dimensions
- Add hard rules:
  - functional drafts cannot directly become final scenarios.
  - seed one-to-one rewriting is forbidden.
- Add output quality checklist covering:
  - input type recognition
  - rediscovery
  - mapping
  - out_of_scope
  - TGFW topology collection
  - topology_ref/Mermaid
  - normal/abnormal paths
  - deployment/capacity expansion/maintenance/reliability/performance/usability/configuration order
  - atomic-ops
  - tool gaps
  - Knowledge Reference three states
  - confirmation_gaps

## Output Ownership

- Primary: `skills/scenario-discovery/SKILL.md`
- Secondary only if needed: `skills/README.md`

## Acceptance

- Markdown has coherent headings and no unclosed code fences.
- Required key rules are searchable with `rg`.
- README update decision is recorded in CR or final report.

## Dispatch Completion

| Field | Value |
|---|---|
| implementation_status | completed |
| implementation_agent | `meta-dev` / `dev-kong` |
| implementation_agent_id | `019e4423-fea7-7132-9196-32197e7882b3` |
| product_files_changed | `skills/scenario-discovery/SKILL.md` |
| secondary_files_changed | none |
| readme_decision | `skills/README.md` unchanged because it currently contains only placeholder help text and no stable Skill index or invocation contract section. |

Verification reported by `meta-dev` and rechecked by parent session:

| Command | Result |
|---|---|
| `rg -n "输入文档类型识别|场景再发现|Seed-to-Scenario|TGFW测试组网图集合|atomic-ops|功能初稿不可直接|输出质量检查" skills/scenario-discovery/SKILL.md` | passed |
| `git diff --check -- skills/scenario-discovery/SKILL.md skills/README.md` | passed |
| `rg -n '```' skills/scenario-discovery/SKILL.md` | no matches |

## Operation Path Follow-up Review - 2026-05-21T09:50:06+08:00

用户要求复核 CR-20260520-001 后续反馈：补强 ptm-tde scenario-discovery 的 Operation Path / normal_path / abnormal_path / CP02 检查和文档一致性。

本轮复核结论：completed。

Dispatch evidence:

| Field | Value |
|---|---|
| dispatch_mode | subagent |
| tool_name | spawn_agent |
| agent_role | meta-dev |
| agent_id | `019e4837-a8be-7ac3-9b0c-8099d5370b76` |
| thread_id | `019e4837-a8be-7ac3-9b0c-8099d5370b76` |
| started_at | 2026-05-21T09:48:42+08:00 |
| completed_at | 2026-05-21T09:50:06+08:00 |

本轮纳入 CP6 的产品文件：

| File | Review result |
|---|---|
| `skills/scenario-discovery/SKILL.md` | Operation Path、normal_path、abnormal_path、选择语义和输出质量检查已覆盖。 |
| `skills/checkpoint-manager/SKILL.md` | CP02 自检已覆盖正常路径可追溯、选择组完整、异常路径可追溯和最小逻辑链一致性。 |
| `docs/ptm-tde/checkpoint-spec.md` | CP02 自动/人工检查项已同步 Operation Path 和 Abnormal Path。 |
| `docs/ptm-tde/README.md` | 主流程、CP02 自动自检和人工确认项已同步。 |
| `docs/ptm-tde/USER-MANUAL.md` | 用户侧 scenario-discovery 字段契约已同步。 |
| `docs/ptm-tde/runtime-artifacts.md` | 运行产物字段契约已同步。 |
| `docs/ptm-tde/component-manual.md` | 组件流程职责已同步。 |
| `docs/ptm-tde/skill-references.md` | Skill 引用说明已同步。 |
| `agents/ptm-tde.md` | scenario 阶段和 CP02 确认点已同步。 |

Verification:

| Command | Result |
|---|---|
| `rg -n "Operation Path|操作路径|normal_path|abnormal_path|related_normal_steps|necessity|至少选择一项|minimal_logic_chain|Seed-to-Scenario|CP02|atomic-ops 唯一" skills/scenario-discovery/SKILL.md skills/checkpoint-manager/SKILL.md docs/ptm-tde/checkpoint-spec.md docs/ptm-tde/README.md docs/ptm-tde/USER-MANUAL.md docs/ptm-tde/runtime-artifacts.md docs/ptm-tde/component-manual.md docs/ptm-tde/skill-references.md agents/ptm-tde.md` | passed |
| `git diff --check -- skills/scenario-discovery/SKILL.md skills/checkpoint-manager/SKILL.md docs/ptm-tde/checkpoint-spec.md docs/ptm-tde/README.md docs/ptm-tde/USER-MANUAL.md docs/ptm-tde/runtime-artifacts.md docs/ptm-tde/component-manual.md docs/ptm-tde/skill-references.md agents/ptm-tde.md` | passed |
| `awk 'FNR==1{if(NR>1 && c%2){print prev ": odd " c} c=0; prev=FILENAME} /^ {0,3}```/{c++} END{if(c%2){print prev ": odd " c}}' skills/scenario-discovery/SKILL.md skills/checkpoint-manager/SKILL.md docs/ptm-tde/checkpoint-spec.md docs/ptm-tde/README.md docs/ptm-tde/USER-MANUAL.md docs/ptm-tde/runtime-artifacts.md docs/ptm-tde/component-manual.md docs/ptm-tde/skill-references.md agents/ptm-tde.md` | passed; no output |
| `test -f scripts/check_delivery_guardrails.py && printf yes || printf no` | `no`; guardrail script not present in this workspace |
