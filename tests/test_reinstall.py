"""reinstall 子命令回归测试。

验证 `reinstall = uninstall + install` 的关键不变量：
- 先 uninstall 再 install，manifest 条目不膨胀、无重复条目；
- 未安装时跳过卸载直接安装，整体幂等；
- 支持 agent 别名（如 te -> ptm-te）；
- --dry-run 不改动 manifest。

同时覆盖两个安装器入口（CLI 实际入口 `script/ptm_team/install.py`
与测试维护版 `script/install.py`），防止两份实现分叉。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLS = [
    REPO_ROOT / "script" / "ptm_team" / "install.py",  # CLI 实际入口
    REPO_ROOT / "script" / "install.py",                 # 测试维护版
]


def run_cmd(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """在指定工作目录运行安装器子命令，合并环境变量。"""
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


def entry_keys(entries: list[dict]) -> list[tuple]:
    """计算 manifest 条目的去重键（kind/name/path/managed_block_id）。"""
    return [
        (
            e.get("kind", ""),
            e.get("name", ""),
            e.get("path", ""),
            e.get("managed_block_id", ""),
        )
        for e in entries
    ]


def install_cmd(install: Path, *extra: str) -> list[str]:
    return [str(install), "--source-dir", str(REPO_ROOT), *extra]


class ReinstallTest(unittest.TestCase):
    def _workspace(self) -> tuple[tempfile.TemporaryDirectory, Path, dict[str, str]]:
        tmp = tempfile.TemporaryDirectory(prefix="ptm-reinstall-")
        workspace = Path(tmp.name)
        # 隔离公共资源目录，避免污染用户级 ~/.ptm-team
        env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}
        return tmp, workspace, env

    def _entries(self, workspace: Path) -> list[dict]:
        manifest = json.loads((workspace / ".ptm-team-manifest.json").read_text(encoding="utf-8"))
        return manifest["installs"][0]["entries"]

    def test_reinstall_does_not_duplicate_manifest_entries(self) -> None:
        """install -> reinstall：条目数不变、无重复、check 通过。"""
        for install in INSTALLS:
            with self.subTest(install=install.name):
                with tempfile.TemporaryDirectory(prefix="ptm-reinstall-dup-") as tmp:
                    workspace = Path(tmp)
                    env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}

                    # 1) 首次安装
                    r = run_cmd(
                        install_cmd(install, "install", "claude", "--agent", "ptm-tde", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    count_after_install = len(self._entries(workspace))
                    self.assertGreater(count_after_install, 0)

                    # 2) reinstall（先卸载再安装）
                    r = run_cmd(
                        install_cmd(install, "reinstall", "claude", "--agent", "ptm-tde", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    # 关键不变量：reinstall 后条目数不变（不膨胀）
                    entries = self._entries(workspace)
                    self.assertEqual(len(entries), count_after_install)

                    # 关键不变量：无重复条目
                    keys = entry_keys(entries)
                    self.assertEqual(len(keys), len(set(keys)))

                    # 3) 漂移检查通过
                    r = run_cmd(
                        install_cmd(install, "check", "claude", "--agent", "ptm-tde"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_reinstall_uninstalled_agent_skips_uninstall_and_installs(self) -> None:
        """未安装时直接 reinstall：跳过卸载、直接安装、幂等。"""
        for install in INSTALLS:
            with self.subTest(install=install.name):
                with tempfile.TemporaryDirectory(prefix="ptm-reinstall-fresh-") as tmp:
                    workspace = Path(tmp)
                    env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}

                    # 无任何先前安装，直接 reinstall
                    r = run_cmd(
                        install_cmd(install, "reinstall", "claude", "--agent", "ptm-tde", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    self.assertIn("跳过卸载", r.stdout)

                    # 安装成功：agent 文件存在
                    self.assertTrue((workspace / ".claude" / "agents" / "ptm-tde.md").is_file())

                    # 幂等：再 reinstall 一次，条目数不变
                    count_before = len(self._entries(workspace))
                    r = run_cmd(
                        install_cmd(install, "reinstall", "claude", "--agent", "ptm-tde", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    self.assertEqual(len(self._entries(workspace)), count_before)

    def test_reinstall_alias_resolves_te(self) -> None:
        """reinstall --agent te 解析为 ptm-te。"""
        for install in INSTALLS:
            with self.subTest(install=install.name):
                with tempfile.TemporaryDirectory(prefix="ptm-reinstall-alias-") as tmp:
                    workspace = Path(tmp)
                    env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}

                    r = run_cmd(
                        install_cmd(install, "reinstall", "claude", "--agent", "te", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    self.assertTrue((workspace / ".claude" / "agents" / "ptm-te.md").is_file())

    def test_reinstall_dry_run_does_not_mutate_manifest(self) -> None:
        """reinstall --dry-run 不改动 manifest、不写 agent 文件。"""
        for install in INSTALLS:
            with self.subTest(install=install.name):
                with tempfile.TemporaryDirectory(prefix="ptm-reinstall-dry-") as tmp:
                    workspace = Path(tmp)
                    env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}

                    # 先正常安装一次，建立基线
                    run_cmd(
                        install_cmd(install, "install", "claude", "--agent", "ptm-tde", "--no-recommended-resources"),
                        cwd=workspace,
                        env=env,
                    )
                    count_before = len(self._entries(workspace))
                    manifest_before = (workspace / ".ptm-team-manifest.json").read_text(encoding="utf-8")

                    # dry-run reinstall：不应改变 manifest
                    r = run_cmd(
                        install_cmd(install, "reinstall", "claude", "--agent", "ptm-tde", "--no-recommended-resources", "--dry-run"),
                        cwd=workspace,
                        env=env,
                    )
                    self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
                    self.assertEqual(len(self._entries(workspace)), count_before)
                    self.assertEqual(
                        (workspace / ".ptm-team-manifest.json").read_text(encoding="utf-8"),
                        manifest_before,
                    )


if __name__ == "__main__":
    unittest.main()
