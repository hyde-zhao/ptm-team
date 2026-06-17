# Eval Run eval-20260617T094026Z

- suite_id: `ptm-tde-suite`
- status: `PASS`
- created_at: `2026-06-17T09:40:26+00:00`
- eval_path: `evals/WORKFLOW-EVAL.yaml`

## Grader Results

| Grader | Type | Status | Evidence |
|---|---|---|---|
| `eval-config-non-empty` | `eval_config_non_empty` / `static` / `none` | `PASS` | 35 grader configuration block(s) have required non-empty parameters |
| `manifest-bundle-consistency` | `manifest_bundle_consistency` / `static` / `none` | `PASS` | 28 bundle component path(s) are declared in workflow manifest |
| `agent-required-fields` | `required_fields` / `static` / `none` | `PASS` | ../agents/ptm-tde.md contains required fields: color, description, name, tools |
| `skill-required-fields` | `required_fields` / `static` / `none` | `PASS` | ../skills/auto-factory-env/SKILL.md contains required fields: description, name; ../skills/bug-gap-analyzer/SKILL.md contains required fields: description, name; ../skills/case-retriever/SKILL.md contains required fields: description, name |
| `prompt-bundle-required-fields` | `required_fields` / `static` / `none` | `PASS` | PROMPT-BUNDLE.yaml contains required fields: bundle_id, compatibility, components, rollback, schema_version, version |
| `artifact-paths-exist` | `path_exists` / `static` / `none` | `PASS` | all paths exist: ../agents/ptm-tde.md, ../CLAUDE.md, ../AGENTS.md, ../.ptm-field-feedback.yaml, RUNTIME-SAMPLE-REGISTRY.yaml, RELEASE-CHECK-PROFILE.yaml, ../script/field_feedback.py, ../script/install.py, ../script/ptm_team/install.py, ../resource/factor-libraries/, ../resource/coupling-matrix/, ../skills/feature-parser/SKILL.md, ../skills/kym/SKILL.md, ../skills/scenario-discovery/SKILL.md, ../skills/m-analyzer/SKILL.md, ../skills/f-analyzer/SKILL.md, ../skills/q-analyzer/SKILL.md, ../skills/test-point-integrator/SKILL.md, ../skills/design-planner/SKILL.md, ../skills/design-ppdcs-analyzer/SKILL.md, ../skills/process-design/SKILL.md, ../skills/parameter-design/SKILL.md, ../skills/data-design/SKILL.md, ../skills/combination-design/SKILL.md, ../skills/state-design/SKILL.md, ../skills/coverage-verifier/SKILL.md, ../skills/deliverable-renderer/SKILL.md, ../skills/checkpoint-manager/SKILL.md, ../skills/case-retriever/SKILL.md, ../skills/tde-feedback/SKILL.md, ../skills/bug-gap-analyzer/SKILL.md, ../skills/change-impact-analyzer/SKILL.md, ../skills/auto-factory-env/SKILL.md, ../skills/ptm-atomic-builder-restapi/SKILL.md, ../skills/ngfw-install/SKILL.md, ../skills/traffic-skill/SKILL.md |
| `prompt-bundle-hashes` | `prompt_bundle_hashes` / `static` / `none` | `PASS` | ../agents/ptm-tde.md sha256 OK; ../CLAUDE.md sha256 OK; ../AGENTS.md sha256 OK |
| `case-registry-links` | `case_registry_links` / `static` / `none` | `PASS` | 34 case(s) reference existing graders |
| `no-live-or-secret-actions` | `forbidden_patterns` / `static` / `none` | `PASS` | no forbidden patterns matched in ../agents/*.md, ../skills/*/SKILL.md |
| `agent-tool-boundary` | `forbidden_patterns` / `static` / `none` | `PASS` | no forbidden patterns matched in ../agents/ptm-tde.md |
| `phase-gate-completeness` | `content_schema` / `static` / `none` | `PASS` | ../agents/ptm-tde.md: all sections, patterns, and table rules OK |
| `gate-contract-checkpoint-manager` | `gate_contract` / `static` / `none` | `PASS` | ../skills/checkpoint-manager/SKILL.md declares 5 gate contract(s) |
| `phase-skill-chain-ptm-tde` | `phase_skill_chain` / `static` / `none` | `PASS` | ../agents/ptm-tde.md: 6 phase skill chain pattern(s) matched |
| `hard-stop-confirmation-ptm-tde` | `hard_stop_confirmation` / `static` / `none` | `PASS` | ../agents/ptm-tde.md: 5 hard-stop confirmation pattern(s) matched |
| `artifact-trace-schema-core` | `artifact_trace_schema` / `static` / `none` | `PASS` | 4 file(s) collectively preserve artifact trace schema: ../agents/ptm-tde.md, ../skills/checkpoint-manager/SKILL.md, ../skills/deliverable-renderer/SKILL.md, ../skills/test-point-integrator/SKILL.md |
| `candidate-decision-integrity` | `candidate_decision_integrity` / `static` / `none` | `PASS` | ../skills/test-point-integrator/SKILL.md: 5 candidate decision pattern(s) matched |
| `field-feedback-config-contract` | `content_schema` / `static` / `none` | `PASS` | ../.ptm-field-feedback.yaml: all sections, patterns, and table rules OK |
| `field-feedback-agent-protocol` | `content_schema` / `static` / `none` | `PASS` | ../agents/ptm-tde.md: all sections, patterns, and table rules OK |
| `tde-feedback-skill-contract` | `content_schema` / `static` / `none` | `PASS` | ../skills/tde-feedback/SKILL.md: all sections, patterns, and table rules OK |
| `field-feedback-run-exec-contract` | `content_schema` / `static` / `none` | `PASS` | ../script/field_feedback.py: all sections, patterns, and table rules OK |
| `runtime-sample-registry-contract` | `content_schema` / `static` / `none` | `PASS` | RUNTIME-SAMPLE-REGISTRY.yaml: all sections, patterns, and table rules OK |
| `runtime-artifact-bgp4-partial` | `runtime_artifact` / `runtime` / `local-fs` | `PASS` | runtime workspace OK: /home/hyde/projects/ptm-tde/test/bgp4+; 10 required path(s), 9 skill call(s), 3 gate(s) checked; metrics: checked_text_files=35, required_gate_count=3, required_path_count=10, required_skill_call_count=9, row_count=915, runtime_sample_count=1, state_phase=mfq, table_count=210 |
| `runtime-artifact-policy-route-full` | `runtime_artifact` / `runtime` / `local-fs` | `PASS` | runtime workspace OK: /home/hyde/projects/ptm-tde/test/policy_route_rt_verify; 14 required path(s), 12 skill call(s), 5 gate(s) checked; metrics: checked_text_files=58, required_gate_count=5, required_path_count=14, required_skill_call_count=12, row_count=1713, runtime_sample_count=1, state_phase=completed, table_count=268 |
| `feedback-source-contract` | `content_schema` / `static` / `none` | `PASS` | WORKFLOW-EVAL.yaml: all sections, patterns, and table rules OK |
| `release-check-profile-contract` | `content_schema` / `static` / `none` | `PASS` | RELEASE-CHECK-PROFILE.yaml: all sections, patterns, and table rules OK |
| `claude-install-runtime-mapping` | `install_mapping` / `runtime` / `local-fs` | `PASS` | install mapping OK for platform=claude agent=ptm-tde; metrics: checked_install_files=22, expected_rule_count=0, expected_skill_count=13 |
| `tde-feedback-install-mapping` | `content_schema` / `static` / `none` | `PASS` | ../script/install.py: all sections, patterns, and table rules OK; ../script/ptm_team/install.py: all sections, patterns, and table rules OK |
| `content-schema-renderer-template` | `content_schema` / `static` / `none` | `PASS` | ../skills/deliverable-renderer/SKILL.md: all sections, patterns, and table rules OK |
| `deliverable-exact-pc-schema` | `deliverable_exact_schema` / `static` / `none` | `PASS` | ../skills/deliverable-renderer/SKILL.md: exact deliverable schema contract OK |
| `state-machine-ptm-tde` | `state_machine` / `static` / `none` | `PASS` | state 'KYM' found; state 'MFQ' found; state 'PPDCS' found |
| `table-structure-all-skills` | `table_structure` / `static` / `none` | `PASS` | ../agents/ptm-tde.md: 11 table(s) OK (93 data rows); ../skills/bug-gap-analyzer/SKILL.md: 4 table(s) OK (33 data rows); ../skills/case-retriever/SKILL.md: 2 table(s) OK (4 data rows) |
| `checkpoint-warning-table-schema` | `table_schema` / `static` / `none` | `PASS` | ../skills/checkpoint-manager/SKILL.md table schema OK: # | 检查项 | 说明 | 级别 |
| `negative-artifact-trace-missing-fields` | `artifact_trace_schema` / `static` / `none` | `FAIL` | fixtures/ptm-tde-negative/missing-trace-fields.md: missing artifact trace schema pattern: normal_path; missing artifact trace schema pattern: abnormal_path; missing artifact trace schema pattern: minimal_logic_chain; missing artifact trace schema pattern: action_source_refs; missing artifact trace schema pattern: factor_bindings; missing artifact trace schema pattern: topology_bindings; missing artifact trace schema pattern: case_steps; missing artifact trace schema pattern: atomic_op; missing artifact trace schema pattern: fact_status |
| `negative-candidate-decision-missing` | `candidate_decision_integrity` / `static` / `none` | `FAIL` | fixtures/ptm-tde-negative/missing-candidate-decision.md: missing candidate decision pattern: decision=confirmed/rejected/modified; missing candidate decision pattern: confirmed / rejected / modified; missing candidate decision pattern: GATE-3 必须阻断 |
| `negative-pc-table-column-mismatch` | `table_structure` / `static` / `none` | `FAIL` | fixtures/ptm-tde-negative/pc-15-columns.md table #1 row 3: 15 columns (expected 16) |

## Case Results

| Case | Category | Severity | Status | Expected | Graders |
|---|---|---|---|---|---|
| `CASE-001` | `smoke` | `` | `PASS` | `PASS` | agent-required-fields, artifact-paths-exist |
| `CASE-002` | `positive` | `` | `PASS` | `PASS` | artifact-paths-exist |
| `CASE-003` | `positive` | `` | `PASS` | `PASS` | phase-gate-completeness |
| `CASE-004` | `positive` | `` | `PASS` | `PASS` | skill-required-fields |
| `CASE-005` | `regression` | `` | `PASS` | `PASS` | prompt-bundle-required-fields, prompt-bundle-hashes, manifest-bundle-consistency |
| `CASE-006` | `security` | `` | `PASS` | `PASS` | no-live-or-secret-actions |
| `CASE-007` | `security` | `` | `PASS` | `PASS` | no-live-or-secret-actions |
| `CASE-008` | `permission` | `` | `PASS` | `PASS` | agent-tool-boundary |
| `CASE-009` | `failure-recovery` | `` | `PASS` | `PASS` | gate-contract-checkpoint-manager |
| `CASE-010` | `style` | `` | `PASS` | `PASS` | case-registry-links |
| `CASE-011` | `content-depth` | `` | `PASS` | `PASS` | content-schema-renderer-template |
| `CASE-012` | `content-depth` | `` | `PASS` | `PASS` | state-machine-ptm-tde |
| `CASE-013` | `content-depth` | `` | `PASS` | `PASS` | table-structure-all-skills |
| `CASE-014` | `eval-contract` | `` | `PASS` | `PASS` | eval-config-non-empty |
| `CASE-015` | `workflow-skip` | `` | `PASS` | `PASS` | phase-skill-chain-ptm-tde |
| `CASE-016` | `workflow-skip` | `` | `PASS` | `PASS` | hard-stop-confirmation-ptm-tde |
| `CASE-017` | `content-retention` | `` | `PASS` | `PASS` | artifact-trace-schema-core |
| `CASE-018` | `content-retention` | `` | `PASS` | `PASS` | candidate-decision-integrity |
| `CASE-019` | `table-schema` | `` | `PASS` | `PASS` | deliverable-exact-pc-schema |
| `CASE-020` | `table-schema` | `` | `PASS` | `PASS` | checkpoint-warning-table-schema |
| `CASE-021` | `negative` | `` | `FAIL` | `FAIL` | negative-artifact-trace-missing-fields |
| `CASE-022` | `negative` | `` | `FAIL` | `FAIL` | negative-candidate-decision-missing |
| `CASE-023` | `negative` | `` | `FAIL` | `FAIL` | negative-pc-table-column-mismatch |
| `CASE-024` | `field-feedback` | `` | `PASS` | `PASS` | field-feedback-config-contract, artifact-paths-exist |
| `CASE-025` | `field-feedback` | `` | `PASS` | `PASS` | field-feedback-agent-protocol |
| `CASE-026` | `field-feedback` | `` | `PASS` | `PASS` | tde-feedback-skill-contract, skill-required-fields |
| `CASE-027` | `install` | `` | `PASS` | `PASS` | tde-feedback-install-mapping, artifact-paths-exist |
| `CASE-028` | `field-feedback` | `` | `PASS` | `PASS` | field-feedback-run-exec-contract |
| `CASE-029` | `runtime-sample` | `HIGH` | `PASS` | `PASS` | runtime-sample-registry-contract, artifact-paths-exist |
| `CASE-030` | `runtime-artifact` | `MEDIUM` | `PASS` | `PASS` | runtime-artifact-bgp4-partial |
| `CASE-031` | `runtime-artifact` | `HIGH` | `PASS` | `PASS` | runtime-artifact-policy-route-full |
| `CASE-032` | `feedback-source` | `HIGH` | `PASS` | `PASS` | feedback-source-contract |
| `CASE-033` | `install` | `HIGH` | `PASS` | `PASS` | claude-install-runtime-mapping |
| `CASE-034` | `release-check` | `HIGH` | `PASS` | `PASS` | release-check-profile-contract |

## Issues

| Severity | Code | Path | Message |
|---|---|---|---|
| INFO | none |  | No package-level issues |

## Expected Failures

- expected_fail_graders: `negative-artifact-trace-missing-fields, negative-candidate-decision-missing, negative-pc-table-column-mismatch`
- unexpected_failed_graders: `none`
- incomplete_graders: `none`
