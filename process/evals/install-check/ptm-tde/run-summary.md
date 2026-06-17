# Eval Run eval-20260617T094137Z

- suite_id: `ptm-tde-suite`
- status: `PASS`
- created_at: `2026-06-17T09:41:37+00:00`
- eval_path: `evals/WORKFLOW-EVAL.yaml`

## Grader Results

| Grader | Type | Status | Evidence |
|---|---|---|---|
| `claude-install-runtime-mapping` | `install_mapping` / `runtime` / `local-fs` | `PASS` | install mapping OK for platform=claude agent=ptm-tde; metrics: checked_install_files=22, expected_rule_count=0, expected_skill_count=13 |

## Case Results

| Case | Category | Severity | Status | Expected | Graders |
|---|---|---|---|---|---|
| `CASE-033` | `install` | `HIGH` | `PASS` | `PASS` | claude-install-runtime-mapping |

## Issues

| Severity | Code | Path | Message |
|---|---|---|---|
| INFO | none |  | No package-level issues |

## Expected Failures

- expected_fail_graders: `none`
- unexpected_failed_graders: `none`
- incomplete_graders: `none`
