from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL = REPO_ROOT / "script" / "install.py"
CHECKPOINT = REPO_ROOT / "skills" / "checkpoint-manager" / "scripts" / "run_checkpoint.py"


def run_cmd(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def record_skill(feature: Path, skill_name: str, output_ref: str) -> None:
    result = run_cmd(
        [
            str(CHECKPOINT),
            "--project-root",
            str(feature),
            "--record-skill-call",
            "--skill-name",
            skill_name,
            "--phase",
            "test",
            "--status",
            "completed",
            "--output-ref",
            output_ref,
            "--evidence-summary",
            f"{skill_name} fixture",
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)


class CR018P2Tests(unittest.TestCase):
    def test_install_check_reports_resource_content_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-resource-") as tmp:
            workspace = Path(tmp)
            env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}
            install = run_cmd(
                [
                    str(INSTALL),
                    "--source-dir",
                    str(REPO_ROOT),
                    "install",
                    "codex",
                    "--agent",
                    "ptm-tde",
                ],
                cwd=workspace,
                env=env,
            )
            self.assertEqual(install.returncode, 0, install.stderr + install.stdout)

            manifest = json.loads((workspace / ".ptm-team-manifest.json").read_text(encoding="utf-8"))
            record = manifest["installs"][0]
            resource_entry = next(
                entry for entry in record["entries"]
                if entry["kind"] == "resource" and entry.get("resource_files")
            )
            resource_root = Path(resource_entry["path"])
            resource_file = resource_root / resource_entry["resource_files"][0]
            resource_file.write_text(resource_file.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")

            check = run_cmd(
                [
                    str(INSTALL),
                    "--source-dir",
                    str(REPO_ROOT),
                    "check",
                    "codex",
                    "--agent",
                    "ptm-tde",
                ],
                cwd=workspace,
                env=env,
            )
            self.assertEqual(check.returncode, 2, check.stdout + check.stderr)
            self.assertIn("INSTALLED_DRIFT resource:", check.stdout)

    def test_gate3_blocks_when_m_analysis_lacks_cae_fields(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate3-") as tmp:
            feature = Path(tmp) / "feature-a"
            (feature / ".input").mkdir(parents=True)
            write(feature / ".input" / "req.md", "# Feature A\n")
            write(feature / "mfq" / "m-analysis" / "test-points.md", "# M\ntrace_refs: []\n")
            write(feature / "mfq" / "f-analysis" / "coupling-test-points.md", "C（Condition） A（Action） E（Effect） coupling_refs trace_refs\n")
            write(feature / "mfq" / "q-analysis" / "quality-test-points.md", "C（Condition） A（Action） E（Effect） quality_dimension HTSM trace_refs\n")
            write(feature / "mfq" / "integration" / "all-test-points.md", "TP-001\n")
            write(feature / "mfq" / "integration" / "logic-cases.md", "LC-ID: LC-001\nsource_tp_ids: [TP-001]\nfactor_bindings: []\ntopology_bindings: []\n")
            write(feature / "mfq" / "integration" / "test-data.md", "TD-001\n")
            write(feature / "process" / "plan" / "design-plan.md", "logic_case_id: LC-001\nrecommended_method: P-Process\nPPDCS: P-Process\n")
            write(feature / "process" / "plan" / "design-planner-reasoning.md", "reasoning\n")
            write(feature / "mfq" / "factor-usage" / "factor-library-lock.yaml", "libraries: []\n")
            write(feature / "mfq" / "m-analysis" / "factor-resolution-report.md", "N_scanned: 0\n")

            for skill in ("m-analyzer", "f-analyzer", "q-analyzer", "test-point-integrator", "design-planner"):
                record_skill(feature, skill, f"fixture/{skill}.md")

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-3", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            gate = feature / "process" / "checkpoints" / "GATE-3-MFQ-Exit-auto.md"
            self.assertIn("M1: M 分析 CAE/trace 字段完整", gate.read_text(encoding="utf-8"))
            self.assertIn("BLOCKING", gate.read_text(encoding="utf-8"))

    def test_gate4_blocks_when_pc_lacks_16_column_table(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate4-") as tmp:
            feature = Path(tmp) / "feature-a"
            (feature / ".input").mkdir(parents=True)
            write(feature / ".input" / "req.md", "# Feature A\n")
            write(feature / "ppdcs" / "ppdcs" / "LC-001.md", "design process\n")
            write(feature / "ppdcs" / "pc" / "PC-001.md", "| physical_case_id | logic_case_id |\n|---|---|\n| PC-001 | LC-001 |\n")
            write(feature / "ppdcs" / "coverage" / "coverage-summary.md", "coverage 100%\n")
            write(feature / "ppdcs" / "delivery" / "Feature特性测试方案.md", "logic_case_id physical_case_id trace_refs topology_bindings fact_status\n")
            write(feature / "ppdcs" / "delivery" / "Feature特性测试用例.md", "logic_case_id physical_case_id trace_refs topology_bindings fact_status\n")

            for skill in ("design-ppdcs-analyzer", "coverage-verifier", "deliverable-renderer"):
                record_skill(feature, skill, f"fixture/{skill}.md")

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            gate = feature / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md"
            text = gate.read_text(encoding="utf-8")
            self.assertIn("P2: PC 16 列格式检查", text)
            self.assertIn("BLOCKING", text)


if __name__ == "__main__":
    unittest.main()
