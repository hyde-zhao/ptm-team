from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIELD_FEEDBACK = REPO_ROOT / "script" / "field_feedback.py"


def run_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FIELD_FEEDBACK), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class FieldFeedbackTests(unittest.TestCase):
    def test_generates_run_issue_gap_and_dashboard(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-field-feedback-") as tmp:
            root = Path(tmp)

            init = run_cmd(["init", "--root", str(root)], cwd=REPO_ROOT)
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            self.assertTrue((root / "process/field-feedback/RUN-EXEC-INDEX.md").is_file())
            self.assertTrue((root / "process/field-feedback/FIELD-ISSUE-REGISTER.md").is_file())

            run_exec = run_cmd(
                [
                    "run-exec",
                    "--root",
                    str(root),
                    "--date",
                    "20260615",
                    "--feature",
                    "policy_route",
                    "--result",
                    "fail",
                    "--gate",
                    "GATE-5",
                    "--summary",
                    "GATE-5 state mismatch",
                    "--evidence",
                    "process/STATE.yaml",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(run_exec.returncode, 0, run_exec.stderr + run_exec.stdout)
            self.assertTrue((root / "process/field-feedback/runs/RUN-EXEC-20260615-001.md").is_file())

            issue = run_cmd(
                [
                    "issue",
                    "--root",
                    str(root),
                    "--date",
                    "20260615",
                    "--run",
                    "RUN-EXEC-20260615-001",
                    "--feature",
                    "policy_route",
                    "--category",
                    "checkpoint",
                    "--severity",
                    "HIGH",
                    "--stage",
                    "GATE-5",
                    "--owner",
                    "checkpoint-manager",
                    "--summary",
                    "GATE-5 state mismatch",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(issue.returncode, 0, issue.stderr + issue.stdout)
            issue_path = root / "process/issues/ISSUE-20260615-001.md"
            self.assertTrue(issue_path.is_file())
            self.assertIn('category: "checkpoint"', issue_path.read_text(encoding="utf-8"))

            gap = run_cmd(
                [
                    "gap",
                    "--root",
                    str(root),
                    "--date",
                    "20260615",
                    "--issue",
                    "ISSUE-20260615-001",
                    "--coverage-status",
                    "covered-but-not-detected",
                    "--missing-stage",
                    "checkpoint",
                    "--summary",
                    "Existing gate missed state mapping.",
                    "--regression-asset",
                    "tests.test_cr018_p2.test_gate5_pass_sets_completed_phase",
                    "--create-eval-backlog",
                    "--priority",
                    "HIGH",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(gap.returncode, 0, gap.stderr + gap.stdout)
            self.assertTrue((root / "process/field-feedback/gap-analysis/GAP-20260615-001.md").is_file())
            self.assertIn("ISSUE-20260615-001", (root / "evals/EVAL-BACKLOG.md").read_text(encoding="utf-8"))

            dashboard = run_cmd(["dashboard", "--root", str(root), "--week", "2026-W25"], cwd=REPO_ROOT)
            self.assertEqual(dashboard.returncode, 0, dashboard.stderr + dashboard.stdout)
            dashboard_text = (root / "docs/quality/FIELD-QUALITY-DASHBOARD.md").read_text(encoding="utf-8")
            self.assertIn("total_issues: `1`", dashboard_text)
            self.assertIn("high_count: `1`", dashboard_text)

    def test_collect_publish_and_pull_feedback_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-field-sync-") as tmp:
            root = Path(tmp) / "ptm-team"
            workspace = Path(tmp) / "runtime"
            feedback_repo = Path(tmp) / "feedback-repo"
            inbox = Path(tmp) / "inbox"
            root.mkdir()
            workspace.mkdir()
            feedback_repo.mkdir()

            (workspace / "process/checkpoints").mkdir(parents=True)
            (workspace / "process/execution").mkdir(parents=True)
            (workspace / "ppdcs/delivery").mkdir(parents=True)
            (workspace / "process/STATE.yaml").write_text('current_gate: "GATE-5"\n', encoding="utf-8")
            (workspace / "process/checkpoints/GATE-5-Exit.md").write_text("- 结论：`PASS`\n", encoding="utf-8")
            (workspace / "process/execution/SKILL-CALLS.yaml").write_text("skill_calls: []\n", encoding="utf-8")
            (workspace / "ppdcs/delivery/cases.md").write_text("# cases\n", encoding="utf-8")

            init = subprocess.run(["git", "init"], cwd=feedback_repo, text=True, capture_output=True, check=False)
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=feedback_repo, check=False)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=feedback_repo, check=False)

            collect = run_cmd(
                [
                    "collect",
                    "--root",
                    str(root),
                    "--workspace",
                    str(workspace),
                    "--feature",
                    "policy_route",
                    "--result",
                    "pass",
                    "--gate",
                    "GATE-5",
                    "--summary",
                    "GATE-5 passed",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(collect.returncode, 0, collect.stderr + collect.stdout)
            collect_lines = collect.stdout.strip().splitlines()
            collection = Path(collect_lines[0])
            run_exec = Path(collect_lines[1].removeprefix("run_exec: ").strip())
            self.assertTrue((collection / "MANIFEST.json").is_file())
            self.assertTrue((collection / "artifacts/process/STATE.yaml").is_file())
            self.assertTrue((collection / "artifacts/process/checkpoints/GATE-5-Exit.md").is_file())
            self.assertTrue(run_exec.is_file())
            run_exec_text = run_exec.read_text(encoding="utf-8")
            self.assertIn(f'collection_path: "{collection}"', run_exec_text)
            self.assertIn("| published_path | `N/A` |", run_exec_text)
            manifest = json.loads((collection / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_exec_path"], str(run_exec))

            publish = run_cmd(
                [
                    "publish",
                    "--collection",
                    str(collection),
                    "--target-repo",
                    str(feedback_repo),
                    "--branch",
                    "field-feedback",
                    "--commit",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(publish.returncode, 0, publish.stderr + publish.stdout)
            self.assertTrue((feedback_repo / "tde-feedback/policy_route" / collection.name / "MANIFEST.json").is_file())

            pull = run_cmd(
                [
                    "pull",
                    "--root",
                    str(root),
                    "--source-repo",
                    str(feedback_repo),
                    "--dest",
                    str(inbox),
                    "--branch",
                    "field-feedback",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(pull.returncode, 0, pull.stderr + pull.stdout)
            self.assertTrue((inbox / "tde-feedback/policy_route" / collection.name / "MANIFEST.json").is_file())

    def test_configured_repo_init_submit_and_pull(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-field-config-") as tmp:
            root = Path(tmp) / "ptm-team"
            workspace = Path(tmp) / "runtime"
            local_repo = Path(tmp) / "ptm-team-feedback"
            remote_repo = Path(tmp) / "ptm-team-feedback.git"
            inbox = root / "process/field-feedback/inbox/gitlab-materials"
            root.mkdir()
            workspace.mkdir()

            (workspace / "process/checkpoints").mkdir(parents=True)
            (workspace / "ppdcs/coverage").mkdir(parents=True)
            (workspace / "process/STATE.yaml").write_text('current_gate: "GATE-4"\n', encoding="utf-8")
            (workspace / "process/checkpoints/GATE-4-PPDCS-Exit-auto.md").write_text(
                "- 结论：`FAIL`\n",
                encoding="utf-8",
            )
            (workspace / "ppdcs/coverage/coverage.md").write_text("# coverage\n", encoding="utf-8")

            bare = subprocess.run(["git", "init", "--bare", str(remote_repo)], text=True, capture_output=True, check=False)
            self.assertEqual(bare.returncode, 0, bare.stderr + bare.stdout)

            (root / ".ptm-field-feedback.yaml").write_text(
                "\n".join(
                    [
                        "feedback_repo:",
                        f'  local_repo: "{local_repo}"',
                        f'  remote_url: "{remote_repo}"',
                        '  branch: "main"',
                        '  dest: "tde-feedback"',
                        '  inbox_dest: "process/field-feedback/inbox/gitlab-materials"',
                        '  remote: "origin"',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            repo_init = run_cmd(["repo-init", "--root", str(root), "--push"], cwd=REPO_ROOT)
            self.assertEqual(repo_init.returncode, 0, repo_init.stderr + repo_init.stdout)
            self.assertTrue((local_repo / ".git").is_dir())

            submit = run_cmd(
                [
                    "submit",
                    "--root",
                    str(root),
                    "--workspace",
                    str(workspace),
                    "--feature",
                    "policy_route",
                    "--result",
                    "fail",
                    "--gate",
                    "GATE-4",
                    "--summary",
                    "GATE-4 coverage issue",
                    "--commit",
                    "--push",
                ],
                cwd=REPO_ROOT,
            )
            self.assertEqual(submit.returncode, 0, submit.stderr + submit.stdout)
            self.assertTrue((local_repo / "tde-feedback/policy_route").is_dir())
            submit_lines = submit.stdout.strip().splitlines()
            collection = Path(submit_lines[0].removeprefix("collection: ").strip())
            published = Path(submit_lines[1].removeprefix("published: ").strip())
            run_exec = Path(submit_lines[2].removeprefix("run_exec: ").strip())
            self.assertTrue(run_exec.is_file())
            run_exec_text = run_exec.read_text(encoding="utf-8")
            self.assertIn(f'collection_path: "{collection}"', run_exec_text)
            self.assertIn(f'published_path: "{published}"', run_exec_text)
            manifest = json.loads((collection / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["run_exec_path"], str(run_exec))
            self.assertEqual(manifest["published_path"], str(published))

            pull = run_cmd(["pull", "--root", str(root)], cwd=REPO_ROOT)
            self.assertEqual(pull.returncode, 0, pull.stderr + pull.stdout)
            pulled = list((inbox / "tde-feedback/policy_route").glob("COLLECT-*"))
            self.assertEqual(len(pulled), 1)
            self.assertTrue((pulled[0] / "MANIFEST.json").is_file())


if __name__ == "__main__":
    unittest.main()
