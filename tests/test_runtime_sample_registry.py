from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "evals/RUNTIME-SAMPLE-REGISTRY.yaml"


def _strip(value: str) -> str:
    return value.strip().strip('"').strip("'")


def load_sample_blocks() -> dict[str, str]:
    text = REGISTRY.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    for part in re.split(r"\n\s*-\s+id:\s+", "\n" + text):
        first, _, rest = part.partition("\n")
        sample_id = _strip(first)
        if sample_id.startswith("RT-"):
            blocks[sample_id] = f'id: "{sample_id}"\n{rest}'
    return blocks


def field(block: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}:\s*(.+?)\s*$", block)
    if not match:
        raise AssertionError(f"missing field {name} in block:\n{block}")
    return _strip(match.group(1))


def list_field(block: str, name: str) -> list[str]:
    match = re.search(rf"(?m)^    {re.escape(name)}:\s*\n(?P<body>(?:      - .+\n)+)", block)
    if not match:
        return []
    values: list[str] = []
    for line in match.group("body").splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(_strip(stripped[2:]))
    return values


class RuntimeSampleRegistryTests(unittest.TestCase):
    def test_registry_declares_bgp4_and_policy_route_samples(self) -> None:
        blocks = load_sample_blocks()
        self.assertIn("RT-BGP4-PARTIAL-20260617", blocks)
        self.assertIn("RT-POLICY-ROUTE-GATE5-20260615", blocks)

    def test_declared_runtime_sample_paths_exist(self) -> None:
        for sample_id, block in load_sample_blocks().items():
            workspace = Path(field(block, "workspace"))
            self.assertTrue(workspace.is_dir(), f"{sample_id} workspace missing: {workspace}")
            self.assertTrue((workspace / field(block, "state_file")).is_file(), f"{sample_id} state missing")
            for rel_path in list_field(block, "required_workspace_paths"):
                self.assertTrue(
                    (workspace / rel_path).exists(),
                    f"{sample_id} workspace artifact missing: {workspace / rel_path}",
                )

    def test_declared_feedback_collection_paths_exist(self) -> None:
        blocks = load_sample_blocks()
        bgp4 = blocks["RT-BGP4-PARTIAL-20260617"]
        collection = REPO_ROOT / field(bgp4, "linked_collection")
        self.assertTrue(collection.is_dir(), f"collection missing: {collection}")
        for rel_path in list_field(bgp4, "required_collection_paths"):
            self.assertTrue(
                (collection / rel_path).exists(),
                f"BGP4 collection artifact missing: {collection / rel_path}",
            )

    def test_runtime_artifact_and_runner_are_not_conflated(self) -> None:
        text = REGISTRY.read_text(encoding="utf-8")
        self.assertIn("runtime_artifact_profile", text)
        self.assertIn("consumed by meta-flow runtime_artifact graders", text)
        self.assertIn("runtime_artifact_grader", text)
        self.assertNotIn("runtime-eval-runner", text)


if __name__ == "__main__":
    unittest.main()
