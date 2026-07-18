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


def _mock_proc(envelope_dict, returncode: int = 0):
    """构造 subprocess.run 的 mock 返回值。"""
    m = mock.Mock()
    m.stdout = json.dumps(envelope_dict)
    m.stderr = ""
    m.returncode = returncode
    return m


# tg_start_traffic_stream 的 rollback_strategy 声明（真相源 atoms/tg/tg_start_traffic_stream.yaml）
TG_START_DECL = {
    "rollback_strategy": {
        "type": "inverse_op",
        "op_id": "tg_stop_traffic_stream",
        "snapshot_required": False,
        "required_inputs": ["ports", "txport", "rxport", "name"],
        "notes": "Stop cleans the runtime stream and does not preserve final statistics.",
    }
}


class BuildTgCommandTests(unittest.TestCase):
    """tg 族 6 op 命令构造：三层 tg trex <action> + flag + list 序列化。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_build_test")

    def _cmd(self, op_id, args):
        return self.op_mapper.build_command(op_id, args, "http://<IP_ADDRESS>:8000",
                                            "/tmp/s.json", dry_run=True)

    def test_start_stream_three_level(self):
        """tg_start 命令含三层 tg trex start-stream + ports 逗号串。"""
        cmd = self._cmd("tg_start_traffic_stream", {
            "ports": ["0", "1"], "txport": "0", "rxport": "1",
            "template": "udp-demo", "name": "stream-1",
        })
        self.assertIn("tg", cmd)
        idx_tg = cmd.index("tg")
        # 紧随 tg 的是 trex，再后是 action
        self.assertEqual(cmd[idx_tg + 1], "trex")
        self.assertEqual(cmd[idx_tg + 2], "start-stream")
        # ports list -> 逗号串
        self.assertIn("--ports", cmd)
        self.assertEqual(cmd[cmd.index("--ports") + 1], "0,1")

    def test_apply_template_hyphen_flags(self):
        """tg_apply 用 --tx-port/--rx-port/--l4-sport（连字符）。"""
        cmd = self._cmd("tg_apply_traffic_template", {
            "template": "udp-demo", "tx_port": "2_1", "rx_port": "2_2",
            "l4_protocol": "udp", "l4_sport": 1234, "l4_dport": 5678,
            "traffic_mode": "count", "rate": "100pps", "count": 500,
        })
        self.assertIn("--tx-port", cmd)
        self.assertIn("--rx-port", cmd)
        self.assertIn("--l4-sport", cmd)
        self.assertEqual(cmd[cmd.index("--tx-port") + 1], "2_1")
        self.assertEqual(cmd[cmd.index("--l4-sport") + 1], "1234")

    def test_config_interface_interfaces_to_json(self):
        """tg_config_interface 的 interfaces list -> JSON 串。"""
        ifaces = [{"port": "2_1", "ip": "<IP_ADDRESS>", "gateway": "<IP_ADDRESS>"}]
        cmd = self._cmd("tg_config_interface", {"interfaces": ifaces})
        self.assertIn("--interfaces", cmd)
        val = cmd[cmd.index("--interfaces") + 1]
        self.assertEqual(json.loads(val), ifaces)  # 可反序列化回原 list

    def test_verify_loss_max_loss_flag(self):
        """tg_verify 含 --max-loss。"""
        cmd = self._cmd("tg_verify_traffic_loss", {
            "ports": ["0", "1"], "txport": "0", "rxport": "1",
            "name": "stream-1", "max_loss": 0,
        })
        self.assertIn("--max-loss", cmd)

    def test_delete_template_command(self):
        """tg_delete_traffic_template -> tg trex delete-template --template。"""
        cmd = self._cmd("tg_delete_traffic_template", {"template": "udp-demo"})
        idx_tg = cmd.index("tg")
        self.assertEqual(cmd[idx_tg + 2], "delete-template")
        self.assertIn("--template", cmd)

    def test_execute_appends_no_execute_in_dry_run(self):
        """dry_run=True 时 tg 命令不含 --execute。"""
        cmd = self._cmd("tg_start_traffic_stream", {
            "ports": ["0", "1"], "txport": "0", "rxport": "1",
            "template": "t", "name": "n",
        })
        self.assertNotIn("--execute", cmd)

    def test_execute_adds_execute_flag(self):
        """dry_run=False 时 tg 命令含 --execute。"""
        cmd = self.op_mapper.build_command(
            "tg_stop_traffic_stream",
            {"ports": ["0", "1"], "txport": "0", "rxport": "1", "name": "n"},
            "http://x:8000", "/tmp/s.json", dry_run=False,
        )
        self.assertIn("--execute", cmd)


class TgRequiredFlagsTests(unittest.TestCase):
    """tg 族 required flag 校验（缺失抛 ValueError）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_req_test")

    def test_start_missing_name(self):
        with self.assertRaises(ValueError):
            self.op_mapper.build_command(
                "tg_start_traffic_stream",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1", "template": "t"},
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )

    def test_apply_missing_required(self):
        with self.assertRaises(ValueError):
            self.op_mapper.build_command(
                "tg_apply_traffic_template",
                {"template": "t", "tx_port": "2_1"},  # 缺 rx_port/l4-protocol 等
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )

    def test_verify_missing_max_loss(self):
        with self.assertRaises(ValueError):
            self.op_mapper.build_command(
                "tg_verify_traffic_loss",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1", "name": "n"},
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )


class TgValidateConsistencyTests(unittest.TestCase):
    """validate_mapping_consistency 覆盖 21 op（15 fw + 6 tg）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_validate_test")

    def test_pass_21_ops(self):
        result = self.op_mapper.validate_mapping_consistency()
        self.assertTrue(result.passed, f"校验失败: {result.mismatches}")
        self.assertEqual(self.op_mapper.EXPECTED_OP_COUNT, 21)
        # 6 个 tg op 在四表
        for op in ("tg_config_interface", "tg_apply_traffic_template",
                   "tg_delete_traffic_template", "tg_start_traffic_stream",
                   "tg_stop_traffic_stream", "tg_verify_traffic_loss"):
            self.assertIn(op, self.op_mapper.OP_ID_TO_SUBCOMMAND)
            self.assertIn(op, self.op_mapper.ARGS_TO_FLAGS)
            self.assertIn(op, self.op_mapper.ROLLBACK_STRATEGY)
            self.assertIn(op, self.op_mapper.OP_METADATA)

    def test_tg_family_six_actions(self):
        """tg 族 6 个 action（config-interface/apply-template/...）。"""
        actions = {a for (f, a) in self.op_mapper.OP_ID_TO_SUBCOMMAND.values() if f == "tg"}
        self.assertEqual(actions, {
            "config-interface", "apply-template", "delete-template",
            "start-stream", "stop-stream", "verify-loss",
        })


class TgBuildInverseArgsModeETests(unittest.TestCase):
    """build_inverse_args mode E：tg 族 required_inputs（无 id_source）。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_mode_e_test")

    def test_mode_e_required_inputs(self):
        """tg_start 回滚 args 按 required_inputs 从 forward_args 取字段。"""
        forward_args = {
            "ports": ["0", "1"], "txport": "0", "rxport": "1",
            "template": "udp-demo", "name": "stream-1",
        }
        ia = self.op_mapper.build_inverse_args(
            "tg_start_traffic_stream", None, forward_args, TG_START_DECL,
        )
        self.assertEqual(ia["ports"], ["0", "1"])
        self.assertEqual(ia["txport"], "0")
        self.assertEqual(ia["rxport"], "1")
        self.assertEqual(ia["name"], "stream-1")
        # template 不在 required_inputs，不携带
        self.assertNotIn("template", ia)

    def test_mode_e_skips_none_fields(self):
        """required_inputs 中 None 字段跳过。"""
        forward_args = {"ports": ["0", "1"], "txport": "0", "rxport": None, "name": "n"}
        ia = self.op_mapper.build_inverse_args(
            "tg_start_traffic_stream", None, forward_args, TG_START_DECL,
        )
        self.assertNotIn("rxport", ia)

    def test_no_required_inputs_returns_empty(self):
        """无 required_inputs 且无 id_source -> 空 dict（回退路径）。"""
        decl = {"rollback_strategy": {"type": "none"}}
        self.assertEqual(self.op_mapper.build_inverse_args("tg_x", None, {}, decl), {})


class TgHandleRollbackTests(unittest.TestCase):
    """handle_rollback：tg_start -> tg_stop（mode E）；manual_required；none。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_rollback_test")

    def _patch_run_capturing(self):
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_proc({"status": "success", "data": {}, "error_type": "NONE"})

        patcher = mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run)
        captured["patcher"] = patcher
        return captured

    def test_start_rollback_calls_stop_with_mode_e_args(self):
        """tg_start 回滚执行 tg_stop_traffic_stream，args 按 required_inputs 携带。"""
        captured = self._patch_run_capturing()
        with captured["patcher"], \
                mock.patch.object(self.op_mapper, "_load_op_decl", return_value=TG_START_DECL):
            self.op_mapper.handle_rollback(
                "tg_start_traffic_stream",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1",
                 "template": "udp-demo", "name": "stream-1"},
                "http://x:8000", "/tmp/s.json", authorized=True,
                result_envelope={"status": "success", "data": {"name": "stream-1"}},
            )
        cmd = captured["cmd"]
        # 三层命令 tg trex stop-stream
        idx_tg = cmd.index("tg")
        self.assertEqual(cmd[idx_tg + 1], "trex")
        self.assertEqual(cmd[idx_tg + 2], "stop-stream")
        # mode E args：ports/txport/rxport/name 携带，template 不携带
        self.assertEqual(cmd[cmd.index("--name") + 1], "stream-1")
        self.assertEqual(cmd[cmd.index("--ports") + 1], "0,1")
        self.assertNotIn("--template", cmd)
        # execute 模式（回滚真实执行）
        self.assertIn("--execute", cmd)

    def test_stop_manual_required_returns_waived(self):
        """tg_stop 的 manual_required 类型不自动回滚，返回 manual_required。"""
        env = self.op_mapper.handle_rollback(
            "tg_stop_traffic_stream",
            {"ports": ["0", "1"], "txport": "0", "rxport": "1", "name": "n"},
            "http://x:8000", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["status"], "success")
        self.assertEqual(env["data"]["rollback"], "manual_required")

    def test_verify_none_not_required(self):
        env = self.op_mapper.handle_rollback(
            "tg_verify_traffic_loss",
            {"ports": ["0", "1"], "txport": "0", "rxport": "1", "name": "n", "max_loss": 0},
            "http://x:8000", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["data"]["rollback"], "not_required")

    def test_apply_none_not_required(self):
        """tg_apply 无 rollback_strategy -> none。"""
        env = self.op_mapper.handle_rollback(
            "tg_apply_traffic_template",
            {"template": "t", "tx_port": "2_1", "rx_port": "2_2",
             "l4_protocol": "udp", "l4_sport": 1, "l4_dport": 2,
             "traffic_mode": "count", "rate": "100pps", "count": 10},
            "http://x:8000", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["data"]["rollback"], "not_required")

    def test_delete_none_not_required(self):
        env = self.op_mapper.handle_rollback(
            "tg_delete_traffic_template",
            {"template": "t"},
            "http://x:8000", "/tmp/s.json", authorized=True,
        )
        self.assertEqual(env["data"]["rollback"], "not_required")


class TgExecuteOpTests(unittest.TestCase):
    """execute_op 对 tg op：解析 envelope / STATE_MISMATCH / DEVICE_UNREACHABLE / 超时。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_tg_exec_test")

    def _patch_run(self, envelope_or_exc):
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            if isinstance(envelope_or_exc, Exception):
                raise envelope_or_exc
            return _mock_proc(envelope_or_exc)

        patcher = mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run)
        captured["patcher"] = patcher
        return captured

    def test_execute_success(self):
        captured = self._patch_run(
            {"status": "success", "data": {"name": "stream-1", "state": "running"},
             "error_type": "NONE"}
        )
        with captured["patcher"]:
            env = self.op_mapper.execute_op(
                "tg_start_traffic_stream",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1",
                 "template": "udp-demo", "name": "stream-1"},
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )
        self.assertEqual(env["status"], "success")
        self.assertEqual(env["error_type"], "NONE")
        # 命令含三层 tg trex start-stream
        self.assertIn("start-stream", captured["cmd"])

    def test_execute_state_mismatch(self):
        """tg_verify 丢包超阈值 -> STATE_MISMATCH（不触发 STATE_INVALID 重连）。"""
        captured = self._patch_run(
            {"status": "error", "data": {"passed": False, "loss_ratio": 0.5, "max_loss": 0},
             "error_type": "STATE_MISMATCH"}
        )
        with captured["patcher"]:
            env = self.op_mapper.execute_op(
                "tg_verify_traffic_loss",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1",
                 "name": "n", "max_loss": 0},
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )
        self.assertEqual(env["error_type"], "STATE_MISMATCH")
        self.assertEqual(env["status"], "error")

    def test_execute_device_unreachable(self):
        """trex-api 不可达 -> DEVICE_UNREACHABLE。"""
        captured = self._patch_run(
            {"status": "error", "data": {}, "error_type": "DEVICE_UNREACHABLE"}
        )
        with captured["patcher"]:
            env = self.op_mapper.execute_op(
                "tg_config_interface",
                {"interfaces": [{"port": "2_1", "ip": "<IP_ADDRESS>", "gateway": "<IP_ADDRESS>"}]},
                "http://x:8000", "/tmp/s.json", dry_run=True,
            )
        self.assertEqual(env["error_type"], "DEVICE_UNREACHABLE")

    def test_execute_timeout_returns_exec_failed(self):
        """count 模式超时 -> EXEC_FAILED（subprocess TimeoutExpired）。"""
        captured = self._patch_run(
            self.op_mapper.subprocess.TimeoutExpired(["ptm-atomic"], 30)
        )
        with captured["patcher"]:
            env = self.op_mapper.execute_op(
                "tg_start_traffic_stream",
                {"ports": ["0", "1"], "txport": "0", "rxport": "1",
                 "template": "t", "name": "n"},
                "http://x:8000", "/tmp/s.json", dry_run=False, authorized=True, timeout=30,
            )
        self.assertEqual(env["error_type"], "EXEC_FAILED")
        self.assertIn("超时", env["data"]["reason"])


if __name__ == "__main__":
    unittest.main()
