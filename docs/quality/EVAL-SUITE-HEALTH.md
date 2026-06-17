# Eval Suite Health

- status: `PASS`
- total_runs: `1`
- passed: `1`
- failed: `0`
- pass_rate: `100.00%`
- unexpected_failures: `0`
- expected_failures: `3`
- stale_cases: `0`
- uncovered_categories: `0`
- runtime_sample_count: `2`
- feedback_sample_count: `0`
- issue_to_regression_ratio: `100.00%`
- flaky_graders: `0`
- disabled_graders: `0`

## Runs By Week

| Week | Runs |
|---|---|
| `2026-W25` | 1 |

## Grader Type Distribution

| Grader Type | Count |
|---|---|
| `artifact_trace_schema` | 2 |
| `candidate_decision_integrity` | 2 |
| `case_registry_links` | 1 |
| `content_schema` | 10 |
| `deliverable_exact_schema` | 1 |
| `eval_config_non_empty` | 1 |
| `forbidden_patterns` | 2 |
| `gate_contract` | 1 |
| `hard_stop_confirmation` | 1 |
| `install_mapping` | 1 |
| `manifest_bundle_consistency` | 1 |
| `path_exists` | 1 |
| `phase_skill_chain` | 1 |
| `prompt_bundle_hashes` | 1 |
| `required_fields` | 3 |
| `runtime_artifact` | 2 |
| `state_machine` | 1 |
| `table_schema` | 1 |
| `table_structure` | 2 |

## Case Category Distribution

| Category | Count |
|---|---|
| `content-depth` | 3 |
| `content-retention` | 2 |
| `eval-contract` | 1 |
| `failure-recovery` | 1 |
| `feedback-source` | 1 |
| `field-feedback` | 4 |
| `install` | 2 |
| `negative` | 3 |
| `permission` | 1 |
| `positive` | 3 |
| `regression` | 1 |
| `release-check` | 1 |
| `runtime-artifact` | 2 |
| `runtime-sample` | 1 |
| `security` | 2 |
| `smoke` | 1 |
| `style` | 1 |
| `table-schema` | 2 |
| `workflow-skip` | 2 |

## Run Evidence

| Run | Status | Week | Path |
|---|---|---|---|
| `eval-20260617T094026Z` | `PASS` | `2026-W25` | `ptm-tde` |

## Risk Notes

- unexpected_failed_graders: `none`
- expected_fail_graders: `negative-artifact-trace-missing-fields, negative-candidate-decision-missing, negative-pc-table-column-mismatch`
- stale_cases: `none`
- uncovered_categories: `none`
- flaky_graders: `none`
- disabled_graders: `none`
