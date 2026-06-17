from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL = REPO_ROOT / "evals/WORKFLOW-EVAL.yaml"
CASES = REPO_ROOT / "evals/CASE-REGISTRY.yaml"
RUNTIME_REGISTRY = REPO_ROOT / "evals/RUNTIME-SAMPLE-REGISTRY.yaml"
RELEASE_PROFILE = REPO_ROOT / "evals/RELEASE-CHECK-PROFILE.yaml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def case_block(case_id: str) -> str:
    text = "\n" + read(CASES)
    parts = re.split(r"\n\s*-\s+id:\s+", text)
    for part in parts:
        first, _, rest = part.partition("\n")
        if first.strip().strip('"') == case_id:
            return rest
    raise AssertionError(f"case not found: {case_id}")


class MetaFlowEvalConsumptionTests(unittest.TestCase):
    def test_workflow_eval_declares_runtime_artifact_graders(self) -> None:
        text = read(EVAL)
        self.assertIn('id: "runtime-artifact-bgp4-partial"', text)
        self.assertIn('type: "runtime_artifact"', text)
        self.assertIn('workspace: "/home/hyde/projects/ptm-tde/test/bgp4+"', text)
        self.assertIn('expected_phase: "mfq"', text)
        self.assertIn('id: "runtime-artifact-policy-route-full"', text)
        self.assertIn('workspace: "/home/hyde/projects/ptm-tde/test/policy_route_rt_verify"', text)
        self.assertIn('expected_phase: "completed"', text)
        self.assertIn('blocking_policy: "always"', text)

    def test_feedback_sources_are_declared_for_meta_flow_eval_feedback(self) -> None:
        text = read(EVAL)
        self.assertIn("feedback_sources:", text)
        self.assertIn('id: "ptm-team-feedback-local"', text)
        self.assertIn('path: "../process/field-feedback/collections"', text)
        self.assertIn('id: "ptm-team-feedback-gitlab"', text)
        self.assertIn('repo: "git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git"', text)
        self.assertIn('path: "tde-feedback"', text)

    def test_case_registry_has_release_check_metadata(self) -> None:
        for case_id in ("CASE-030", "CASE-031", "CASE-032", "CASE-033", "CASE-034"):
            block = case_block(case_id)
            self.assertIn("severity:", block)
            self.assertIn("blocking:", block)
            self.assertIn("coverage_status:", block)
            self.assertIn("regression_asset:", block)
        self.assertIn("runtime_required: true", case_block("CASE-031"))
        self.assertIn("blocking: true", case_block("CASE-031"))

    def test_runtime_registry_binds_samples_to_runtime_artifact_graders(self) -> None:
        text = read(RUNTIME_REGISTRY)
        self.assertIn('purpose: "ptm-tde domain runtime sample registry consumed by meta-flow runtime_artifact graders"', text)
        self.assertIn('runtime_artifact_grader: "runtime-artifact-bgp4-partial"', text)
        self.assertIn('runtime_artifact_grader: "runtime-artifact-policy-route-full"', text)
        self.assertNotIn("runtime-eval-runner", text)

    def test_release_profile_declares_runtime_feedback_and_issue_gates(self) -> None:
        text = read(RELEASE_PROFILE)
        self.assertIn('profile_id: "release"', text)
        self.assertIn("required_runtime_samples:", text)
        self.assertIn('RT-POLICY-ROUTE-GATE5-20260615', text)
        self.assertIn("advisory_runtime_samples:", text)
        self.assertIn('RT-BGP4-PARTIAL-20260617', text)
        self.assertIn("feedback_triage_required:", text)
        self.assertIn("regression_asset_required_for_source_issue: true", text)


if __name__ == "__main__":
    unittest.main()
