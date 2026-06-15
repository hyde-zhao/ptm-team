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


if __name__ == "__main__":
    unittest.main()
