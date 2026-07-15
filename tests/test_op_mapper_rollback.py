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


class ResolveIdTests(unittest.TestCase):
    """resolve_id 按 id_source 4 模式解析（声明经 _load_op_decl mock）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_resolve_id_test")

    def test_mode_response(self):
        """模式 A：id 取自 envelope.data[id_field]。"""
        decl = {"rollback_strategy": {"id_source": "response", "id_field": "policy_route_id"}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            rid = self.op_mapper.resolve_id(
                "fw_config_policy_route", {"data": {"policy_route_id": 42}}, {}
            )
        self.assertEqual(rid, 42)

    def test_mode_args(self):
        """模式 B：id 取自 args[id_field]（id 即 name）。"""
        decl = {"rollback_strategy": {"id_source": "args", "id_field": "object_name"}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            rid = self.op_mapper.resolve_id("fw_config_object", None, {"object_name": "OBJ1"})
        self.assertEqual(rid, "OBJ1")

    def test_mode_query(self):
        """模式 C：执行 query_op，在 data.full_config 按 query_match 匹配取 id_field。"""
        decl = {"rollback_strategy": {
            "id_source": "query", "id_field": "id",
            "query_op": "fw_verify_acl_policy", "query_match": "name",
            "query_match_source": "args",
        }}
        fake_qenv = {"data": {"full_config": [{"id": 7, "name": "pol1"}]}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl), \
                mock.patch.object(self.op_mapper, "execute_op", return_value=fake_qenv):
            rid = self.op_mapper.resolve_id(
                "fw_config_acl_policy", None, {"name": "pol1"},
                base_url="https://x", session_file="/tmp/s.json",
            )
        self.assertEqual(rid, 7)

    def test_mode_placeholder(self):
        """模式 D：id 取自 inputs.params.id（占位 "1"）。"""
        decl = {"rollback_strategy": {"id_source": "placeholder", "id_field": "old_name"},
                "inputs": {"params": {"id": "1"}}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            rid = self.op_mapper.resolve_id(
                "fw_update_acl_policy_group", None, {"old_name": "a", "new_name": "b"}
            )
        self.assertEqual(rid, "1")

    def test_no_decl_returns_none(self):
        """无声明（_load_op_decl 返回 None）-> None，调用方回退旧逻辑。"""
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=None):
            rid = self.op_mapper.resolve_id(
                "fw_config_policy_route", {"data": {"policy_route_id": 42}}, {}
            )
        self.assertIsNone(rid)

    def test_no_id_source_returns_none(self):
        """旧 atom 无 id_source 字段 -> None（回退 _extract_inverse_id）。"""
        decl = {"rollback_strategy": {}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            rid = self.op_mapper.resolve_id(
                "fw_config_interface", {"data": {"interface_id": 7}}, {}
            )
        self.assertIsNone(rid)

    def test_response_skips_placeholder_zero(self):
        """模式 A：id_field 值为占位（0）时返回 None（声明驱动，不做字段回退链）。

        旧 _extract_inverse_id 的 policy_route_id->id 回退链仅用于无声明的 op（回退路径）；
        有声明的 op 严格按 id_field 解析，占位即未解析。
        """
        decl = {"rollback_strategy": {"id_source": "response", "id_field": "policy_route_id"}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            rid = self.op_mapper.resolve_id(
                "fw_config_policy_route", {"data": {"policy_route_id": 0, "id": 5}}, {}
            )
        self.assertIsNone(rid)


class BuildInverseArgsTests(unittest.TestCase):
    """build_inverse_args 4 模式构造 inverse_args（mode D arg 互换）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_build_inv_test")

    def test_mode_a_response(self):
        decl = {"rollback_strategy": {"id_source": "response", "id_field": "policy_route_id"}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            ia = self.op_mapper.build_inverse_args(
                "fw_config_policy_route", {"data": {"policy_route_id": 42}},
                {"type": "ipv4"}, decl,
            )
        self.assertEqual(ia["id"], 42)
        self.assertEqual(ia["type"], "ipv4")

    def test_mode_b_args(self):
        decl = {"rollback_strategy": {"id_source": "args", "id_field": "object_name"}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            ia = self.op_mapper.build_inverse_args(
                "fw_config_object", None, {"object_name": "OBJ1"}, decl,
            )
        self.assertEqual(ia["id"], "OBJ1")

    def test_mode_d_placeholder_arg_swap(self):
        """mode D rename-back：old_name <-> new_name 互换。"""
        decl = {"rollback_strategy": {"id_source": "placeholder", "id_field": "old_name"},
                "inputs": {"params": {"id": "1"}}}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            ia = self.op_mapper.build_inverse_args(
                "fw_update_acl_policy_group", None,
                {"policy_type": "ipv4", "old_name": "a", "new_name": "b"}, decl,
            )
        self.assertEqual(ia["id"], "1")
        self.assertEqual(ia["old_name"], "b")  # rollback.old_name = 前向 new_name
        self.assertEqual(ia["new_name"], "a")  # rollback.new_name = 前向 old_name
        self.assertEqual(ia["policy_type"], "ipv4")

    def test_no_decl_returns_empty(self):
        self.assertEqual(self.op_mapper.build_inverse_args("fw_x", None, {}, None), {})


class HandleRollbackDeclDrivenTests(unittest.TestCase):
    """handle_rollback 声明优先：有 id_source 声明走 build_inverse_args（声明驱动）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_rb_decl_test")

    def _patch_run_capturing(self):
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_proc({"status": "success", "data": {}, "error_type": "NONE"})

        patcher = mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run)
        captured["patcher"] = patcher
        return captured

    def test_decl_args_path_overrides_legacy(self):
        """id_source=args 声明时，id 取自 args[id_field]，不取 envelope.data（区别于回退路径）。

        回退路径（_extract_inverse_id）会取 result_envelope.data.policy_route_id=999；
        声明路径取 args.object_name=OBJ1。断言 OBJ1 证明走声明路径。
        """
        decl = {"rollback_strategy": {
            "id_source": "args", "id_field": "object_name",
            "op_id": "fw_delete_policy_route", "type": "inverse_op",
        }}
        captured = self._patch_run_capturing()
        with captured["patcher"], \
                mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            self.op_mapper.handle_rollback(
                "fw_config_policy_route",
                {"object_name": "OBJ1", "type": "ipv4"},
                "https://x", "/tmp/s.json", authorized=True,
                result_envelope={"data": {"policy_route_id": 999}},
            )
        cmd = captured["cmd"]
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "OBJ1")  # 声明路径，非 999


if __name__ == "__main__":
    unittest.main()
