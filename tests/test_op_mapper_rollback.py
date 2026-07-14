from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


OP_MAPPER_PATH = REPO_ROOT / "skills/policy-route-execution/scripts/op_mapper.py"


def _mock_proc(envelope_dict):
    """构造 subprocess.run 的 mock 返回值。"""
    m = mock.Mock()
    m.stdout = json.dumps(envelope_dict)
    m.stderr = ""
    m.returncode = 0
    return m


class ExtractInverseIdTests(unittest.TestCase):
    """_extract_inverse_id 从 config 返回 envelope.data 提取 id（CR-029 修复核心）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_extract_test")

    def test_policy_route_id_preferred(self):
        env = {"data": {"policy_route_id": 15, "id": 99}}
        self.assertEqual(self.op_mapper._extract_inverse_id(env, "fw_config_policy_route"), 15)

    def test_interface_id(self):
        env = {"data": {"interface_id": 7}}
        self.assertEqual(self.op_mapper._extract_inverse_id(env, "fw_config_interface"), 7)

    def test_id_fallback(self):
        env = {"data": {"id": 3}}
        self.assertEqual(self.op_mapper._extract_inverse_id(env, "fw_config_policy_route"), 3)

    def test_skip_placeholder_zero(self):
        env = {"data": {"policy_route_id": 0, "id": 5}}
        self.assertEqual(self.op_mapper._extract_inverse_id(env, "fw_config_policy_route"), 5)

    def test_skip_empty_string(self):
        env = {"data": {"policy_route_id": "", "id": 5}}
        self.assertEqual(self.op_mapper._extract_inverse_id(env, "fw_config_policy_route"), 5)

    def test_none_envelope(self):
        self.assertIsNone(self.op_mapper._extract_inverse_id(None, "fw_config_policy_route"))

    def test_non_dict_envelope(self):
        self.assertIsNone(self.op_mapper._extract_inverse_id("not dict", "fw_config_policy_route"))

    def test_no_id_in_data(self):
        self.assertIsNone(self.op_mapper._extract_inverse_id({"data": {}}, "fw_config_policy_route"))

    def test_data_not_dict(self):
        self.assertIsNone(self.op_mapper._extract_inverse_id({"data": "x"}, "fw_config_policy_route"))


class HandleRollbackInverseOpTests(unittest.TestCase):
    """handle_rollback inverse_op 分支优先从 result_envelope 取 id，兜底 args['id']。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_rollback_test")

    def _patch_run_capturing(self):
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_proc({"status": "success", "data": {}, "error_type": "NONE"})

        patcher = mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run)
        captured["patcher"] = patcher
        return captured

    def test_uses_policy_route_id_from_result_envelope(self):
        """config 回滚用 result_envelope.data.policy_route_id 作 delete 的 --id。"""
        captured = self._patch_run_capturing()
        with captured["patcher"]:
            env = self.op_mapper.handle_rollback(
                "fw_config_policy_route",
                {"source_network": "OBJ-SRC", "in_interface": "GE0_1", "type": "ipv4"},
                "https://<IP_ADDRESS>",
                "/tmp/session.json",
                authorized=True,
                result_envelope={"status": "success", "data": {"policy_route_id": 42, "created": True}},
            )
        cmd = captured["cmd"]
        self.assertIn("--id", cmd)
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "42")
        self.assertEqual(env["status"], "success")
        # 命令应为 delete（config 的 inverse_op），带 --execute
        self.assertIn("delete", cmd)
        self.assertIn("--execute", cmd)

    def test_fallback_args_id_when_no_result_envelope(self):
        """缺 result_envelope 时兜底 args['id']（保持向后兼容）。"""
        captured = self._patch_run_capturing()
        with captured["patcher"]:
            self.op_mapper.handle_rollback(
                "fw_config_policy_route",
                {"id": 8, "type": "ipv4"},
                "https://<IP_ADDRESS>",
                "/tmp/session.json",
                authorized=True,
            )
        cmd = captured["cmd"]
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "8")

    def test_result_envelope_overrides_args(self):
        """result_envelope 的 policy_route_id 优先于 args['id']。"""
        captured = self._patch_run_capturing()
        with captured["patcher"]:
            self.op_mapper.handle_rollback(
                "fw_config_policy_route",
                {"id": 999, "type": "ipv4"},
                "https://<IP_ADDRESS>",
                "/tmp/session.json",
                authorized=True,
                result_envelope={"status": "success", "data": {"policy_route_id": 77}},
            )
        cmd = captured["cmd"]
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "77")  # 用 77 不是 999


class HandleRollbackOtherTypesTests(unittest.TestCase):
    """restore_snapshot / irreversible / none 行为不变（回归保护）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_other_test")

    def test_irreversible_returns_waived(self):
        env = self.op_mapper.handle_rollback(
            "fw_reset_policy_route_hitcount",
            {"id": 5, "type": "ipv4"},
            "https://x", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["status"], "success")
        self.assertEqual(env["data"]["rollback"], "waived")

    def test_none_returns_not_required(self):
        env = self.op_mapper.handle_rollback(
            "fw_verify_policy_route",
            {"type": "ipv4"},
            "https://x", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["data"]["rollback"], "not_required")

    def test_op_not_in_strategy(self):
        env = self.op_mapper.handle_rollback("fw_unknown", {}, "https://x", "/tmp/s.json")
        self.assertEqual(env["status"], "error")
        self.assertEqual(env["error_type"], "OP_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
