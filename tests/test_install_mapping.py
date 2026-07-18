from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class InstallMappingTests(unittest.TestCase):
    def test_ptm_tde_installs_tde_feedback_skill(self) -> None:
        script_install = load_module(REPO_ROOT / "script/install.py", "script_install")
        package_install = load_module(REPO_ROOT / "script/ptm_team/install.py", "package_install")

        script_skills = script_install.get_agent_skills("ptm-tde")
        package_skills = package_install.get_agent_skills("ptm-tde")

        self.assertIn("tde-feedback", script_skills)
        self.assertIn("tde-feedback", package_skills)
        self.assertEqual(script_skills, package_skills)
        self.assertTrue((REPO_ROOT / "skills/tde-feedback/SKILL.md").is_file())

    def test_qoder_platform_supported(self) -> None:
        for mod_path, mod_name in [
            (REPO_ROOT / "script/install.py", "script_install"),
            (REPO_ROOT / "script/ptm_team/install.py", "package_install"),
        ]:
            mod = load_module(mod_path, mod_name)
            self.assertIn("qoder", mod.VALID_PLATFORMS)
            self.assertEqual(mod.PLATFORM_DIRS["qoder"]["agents"], ".qoder/agents")
            self.assertEqual(mod.PLATFORM_DIRS["qoder"]["skills"], ".qoder/skills")
            self.assertEqual(mod.PTM_TDE_RULE_FILES["qoder"], "AGENTS.md")

    def test_render_qoder_agent_format(self) -> None:
        mod = load_module(REPO_ROOT / "script/install.py", "script_install")
        rendered = mod.render_qoder_agent(
            name="test-agent",
            description="Test description",
            instructions="Test instructions body.",
            commit="abc123",
            generated="2026-06-29T10:00:00Z",
            color="blue",
            tools="Read, Write",
            effort="medium",
        )
        self.assertIn("name: \"test-agent\"", rendered)
        self.assertIn("description: \"Test description\"", rendered)
        self.assertIn("effort: medium", rendered)
        self.assertIn("color: \"blue\"", rendered)
        self.assertIn("tools: Read, Write", rendered)
        self.assertIn("Test instructions body.", rendered)

    def test_render_qoder_agent_without_effort(self) -> None:
        mod = load_module(REPO_ROOT / "script/install.py", "script_install")
        rendered = mod.render_qoder_agent(
            name="test-agent",
            description="Test",
            instructions="Body.",
            commit="abc",
            generated="2026-06-29T10:00:00Z",
        )
        self.assertNotIn("effort:", rendered)
        self.assertIn("name: \"test-agent\"", rendered)

    def test_shared_rule_block_for_codex_and_qoder(self) -> None:
        mod = load_module(REPO_ROOT / "script/install.py", "script_install")
        # Codex and Qoder share the same rule file (AGENTS.md) and the same block ID
        self.assertEqual(mod.PTM_TDE_RULE_FILES["codex"], mod.PTM_TDE_RULE_FILES["qoder"])
        # Rule body for codex and qoder should be identical (same combined label)
        body_codex = mod.render_ptm_tde_rule_body("codex")
        body_qoder = mod.render_ptm_tde_rule_body("qoder")
        self.assertEqual(body_codex, body_qoder)
        # Combined label includes both platforms
        self.assertIn("Codex", body_codex)
        self.assertIn("Qoder", body_codex)
        # Claude uses its own rule file and label
        body_claude = mod.render_ptm_tde_rule_body("claude")
        self.assertIn("Claude Code", body_claude)
        self.assertNotIn("Codex", body_claude)

    def test_has_other_platform_rule(self) -> None:
        mod = load_module(REPO_ROOT / "script/install.py", "script_install")
        # When codex has a rule entry, qoder uninstall should detect it
        manifest = {
            "installs": [
                {
                    "platform": "codex",
                    "scope": "project",
                    "status": "installed",
                    "entries": [
                        {"kind": "rule", "name": "ptm-tde:ptm-tde-workflow", "installed_for": ["ptm-tde"]},
                    ],
                },
            ],
        }
        self.assertTrue(mod.has_other_platform_rule(manifest, "qoder", "ptm-tde"))
        self.assertFalse(mod.has_other_platform_rule(manifest, "claude", "ptm-tde"))
        # Empty manifest
        self.assertFalse(mod.has_other_platform_rule({"installs": []}, "qoder", "ptm-tde"))


class PtmTeRuleBlockTests(unittest.TestCase):
    """ptm-te 规则块（CR-029 新增）：两 install.py 一致 + registry + rule body。"""

    def _both_modules(self):
        return [
            load_module(REPO_ROOT / "script/install.py", "script_install_te"),
            load_module(REPO_ROOT / "script/ptm_team/install.py", "package_install_te"),
        ]

    def test_ptm_te_skills_consistent(self) -> None:
        for mod in self._both_modules():
            skills = mod.get_agent_skills("ptm-te")
            self.assertEqual(skills, ["device-management", "device-connection", "policy-route-execution", "trex-traffic"])

    def test_ptm_te_rule_block_registry(self) -> None:
        for mod in self._both_modules():
            self.assertEqual(mod.AGENT_RULE_BLOCK["ptm-te"], "ptm-te-workflow")
            self.assertIn("ptm-te-workflow", mod.RULE_BLOCK_RENDERERS)
            self.assertEqual(mod.PTM_TE_RULE_BLOCK_ID, "ptm-te-workflow")

    def test_render_ptm_te_rule_body_contains_key_rules(self) -> None:
        mod = load_module(REPO_ROOT / "script/install.py", "script_install_te_body")
        body = mod.render_ptm_te_rule_body("claude")
        self.assertIn("ptm-te 工作流程规则", body)
        self.assertIn("dry-run 默认门", body)
        self.assertIn("policy_route_id", body)
        self.assertIn("Claude Code", body)
        body_codex = mod.render_ptm_te_rule_body("codex")
        self.assertIn("Codex", body_codex)
        self.assertIn("Qoder", body_codex)

    def test_ptm_te_rule_file_same_as_tde(self) -> None:
        """ptm-te 与 ptm-tde 共用同一规则文件（CLAUDE.md/AGENTS.md）。"""
        mod = load_module(REPO_ROOT / "script/install.py", "script_install_te_file")
        self.assertEqual(mod.RULE_FILES["claude"], "CLAUDE.md")
        self.assertEqual(mod.RULE_FILES["codex"], "AGENTS.md")
        self.assertEqual(mod.PTM_TDE_RULE_FILES, mod.RULE_FILES)


if __name__ == "__main__":
    unittest.main()
