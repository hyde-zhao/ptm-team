from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
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
    m = mock.Mock()
    m.stdout = json.dumps(envelope_dict)
    m.stderr = ""
    m.returncode = 0
    return m


class WriteReadStepRefTests(unittest.TestCase):
    """step-refs 落盘与读取。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_writeref_test")
        self.tmp = tempfile.mkdtemp()

    def test_write_then_read(self):
        env = {"status": "success", "data": {"policy_route_id": 42}}
        self.op_mapper._write_step_ref(
            self.tmp, "STEP-001", "fw_config_policy_route", {"type": "ipv4"}, env
        )
        ref = self.op_mapper._read_step_ref(self.tmp, "STEP-001")
        self.assertIsNotNone(ref)
        self.assertEqual(ref["step_id"], "STEP-001")
        self.assertEqual(ref["op_id"], "fw_config_policy_route")
        self.assertEqual(ref["envelope"]["data"]["policy_route_id"], 42)

    def test_read_missing_returns_none(self):
        self.assertIsNone(self.op_mapper._read_step_ref(self.tmp, "STEP-999"))

    def test_write_skips_empty_step_id(self):
        self.op_mapper._write_step_ref(self.tmp, "", "fw_x", {}, {})
        self.assertEqual(len(list(Path(self.tmp).iterdir())), 0)


class ResolveStepRefsTests(unittest.TestCase):
    """resolve_step_refs ${STEP-N.id} / ${STEP-N.<field>} 插值。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_resolvestep_test")
        self.tmp = tempfile.mkdtemp()
        # 前序 STEP-001：policy_route config，返回 policy_route_id=42
        env = {"status": "success", "data": {"policy_route_id": 42, "created": True}}
        self.op_mapper._write_step_ref(
            self.tmp, "STEP-001", "fw_config_policy_route", {"type": "ipv4"}, env
        )

    def test_interpolate_id_via_decl(self):
        """${STEP-001.id} 按 id_source=response 声明解析为 42。"""
        decl = {"rollback_strategy": {"id_source": "response", "id_field": "policy_route_id"}}
        args = {"id": "${STEP-001.id}"}
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            resolved = self.op_mapper.resolve_step_refs(args, self.tmp)
        self.assertEqual(resolved["id"], 42)

    def test_interpolate_field_from_envelope_data(self):
        """${STEP-001.policy_route_id} 取被引 step envelope.data.policy_route_id。"""
        args = {"source_network": "${STEP-001.policy_route_id}"}
        resolved = self.op_mapper.resolve_step_refs(args, self.tmp)
        self.assertEqual(resolved["source_network"], 42)

    def test_no_step_refs_dir_passthrough(self):
        """无 step_refs_dir -> 原样返回（向后兼容）。"""
        args = {"id": "${STEP-001.id}"}
        self.assertEqual(self.op_mapper.resolve_step_refs(args, None), args)

    def test_no_placeholder_passthrough(self):
        """无占位符 -> 原样。"""
        args = {"id": "42", "type": "ipv4"}
        self.assertEqual(self.op_mapper.resolve_step_refs(args, self.tmp), args)

    def test_missing_ref_raises(self):
        """被引 step-ref 不存在 -> ValueError。"""
        with self.assertRaises(ValueError):
            self.op_mapper.resolve_step_refs({"id": "${STEP-999.id}"}, self.tmp)

    def test_unresolvable_id_raises(self):
        """被引 op 无 id_source 声明 -> ${STEP-N.id} 解析失败抛 ValueError。"""
        decl = {"rollback_strategy": {}}  # 旧 atom 无 id_source
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            with self.assertRaises(ValueError):
                self.op_mapper.resolve_step_refs({"id": "${STEP-001.id}"}, self.tmp)


class ExecuteOpStepRefsTests(unittest.TestCase):
    """execute_op 端到端：插值 ${STEP-N.id} + 落盘 step-ref。"""

    def setUp(self):
        self.op_mapper = load_module(OP_MAPPER_PATH, "op_mapper_execstep_test")
        self.tmp = tempfile.mkdtemp()
        env = {"status": "success", "data": {"policy_route_id": 42}}
        self.op_mapper._write_step_ref(
            self.tmp, "STEP-001", "fw_config_policy_route", {"type": "ipv4"}, env
        )

    def test_execute_interpolates_and_writes_ref(self):
        """STEP-002 引用 ${STEP-001.id} -> 插值为 42，且 STEP-002 落盘。"""
        decl = {"rollback_strategy": {"id_source": "response", "id_field": "policy_route_id"}}
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_proc({"status": "success", "data": {}, "error_type": "NONE"})

        with mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(self.op_mapper, "_load_op_decl", return_value=decl):
            self.op_mapper.execute_op(
                "fw_delete_policy_route",
                {"id": "${STEP-001.id}", "type": "ipv4"},
                "https://x", "/tmp/s.json",
                step_id="STEP-002", step_refs_dir=self.tmp,
                authorized=True, dry_run=False,
            )
        # 插值：cmd 含 --id 42
        cmd = captured["cmd"]
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "42")
        # 落盘：STEP-002.json 已写
        ref2 = self.op_mapper._read_step_ref(self.tmp, "STEP-002")
        self.assertIsNotNone(ref2)
        self.assertEqual(ref2["op_id"], "fw_delete_policy_route")

    def test_execute_no_step_refs_dir_no_interpolation(self):
        """无 step_refs_dir -> 不插值，${STEP-001.id} 原样进命令（向后兼容）。"""
        captured: dict = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            return _mock_proc({"status": "success", "data": {}, "error_type": "NONE"})

        with mock.patch.object(self.op_mapper.subprocess, "run", side_effect=fake_run):
            self.op_mapper.execute_op(
                "fw_delete_policy_route",
                {"id": "${STEP-001.id}", "type": "ipv4"},
                "https://x", "/tmp/s.json", authorized=True, dry_run=False,
            )
        cmd = captured["cmd"]
        idx = cmd.index("--id")
        self.assertEqual(cmd[idx + 1], "${STEP-001.id}")  # 未插值

    def test_execute_unresolvable_ref_returns_validation_failed(self):
        """无法解析的 ${STEP-N.id} -> VALIDATION_FAILED envelope（不抛到外层）。"""
        with mock.patch.object(self.op_mapper, "_load_op_decl", return_value=None):
            env = self.op_mapper.execute_op(
                "fw_delete_policy_route",
                {"id": "${STEP-999.id}", "type": "ipv4"},
                "https://x", "/tmp/s.json",
                step_id="STEP-002", step_refs_dir=self.tmp,
                authorized=True, dry_run=False,
            )
        self.assertEqual(env["status"], "error")
        self.assertEqual(env["error_type"], "VALIDATION_FAILED")


if __name__ == "__main__":
    unittest.main()
