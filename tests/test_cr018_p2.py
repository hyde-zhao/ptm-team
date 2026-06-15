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
PC_HEADER = (
    "| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | "
    "组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | "
    "首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |\n"
)
PC_SEPARATOR = (
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
)
VALID_PC_ROW = (
    "| 策略路由 | 配置管理 | 匹配条件 | 配置源地址对象 | PC-001 | P1 | "
    "单DUT | topology_binding_id=TB-001 | 已有地址对象 | "
    "1. 配置源地址对象<br>执行对象：DUT<br>原子操作：fw_config_policy_route src_addr=OBJ_SRC_WEB | "
    "规则保存成功 | V60R001C01 |  | 策略路由 | 功能 | 是 |\n"
)


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


def valid_confirmed_scenarios() -> str:
    return (
        "# Confirmed Scenarios\n\n"
        "input_document_classification: deployment_scenario_draft\n"
        "confirmation_gaps: []\n\n"
        "## Scenario SCN-001\n\n"
        "scenario_id: SCN-001\n"
        "scenario_goal: 验证策略路由匹配流量按预期转发\n"
        "review_status: confirmed\n"
        "topology_ref: TOPO-001\n"
        "normal_path:\n"
        "  - step_id: STEP-001\n"
        "    sub_step_ids: [STEP-001.1]\n"
        "    operation: 配置策略路由匹配条件\n"
        "    action_source_ref: fw_config_policy_route\n"
        "    necessity: 必要\n"
        "    description: 设置源地址对象和下一跳\n"
        "  - step_id: STEP-002\n"
        "    sub_step_ids: []\n"
        "    operation: 发送匹配流量\n"
        "    action_source_ref: tg_send_tcp_traffic\n"
        "    necessity: 必要\n"
        "    description: 从 TG 发送 TCP/443 报文\n"
        "abnormal_path:\n"
        "  - abnormal_item: ABN-001\n"
        "    related_normal_steps: [STEP-001]\n"
        "    action_source_ref: fw_config_policy_route\n"
        "    input_or_state: 下一跳地址不可达\n"
        "    expected_handling: 配置失败并提示不可达\n"
        "minimal_logic_chain:\n"
        "  - STEP-001\n"
        "  - STEP-002\n"
        "action_source_refs: [fw_config_policy_route, tg_send_tcp_traffic]\n"
        "atomic_operations:\n"
        "  - op_id: fw_config_policy_route\n"
        "    source: ptm-atomic\n"
        "  - op_id: tg_send_tcp_traffic\n"
        "    source: ptm-atomic\n"
    )


def valid_markdown_confirmed_scenarios() -> str:
    return (
        "# Confirmed Scenarios\n\n"
        "input_document_classification: deployment_scenario_draft\n"
        "confirmation_gaps: []\n\n"
        "### S1: IPv4 策略路由基础转发验证\n\n"
        "| 字段 | 值 |\n"
        "|------|-----|\n"
        "| scenario_id | S1 |\n"
        "| scenario_goal | 验证 IPv4 策略路由基本配置、策略命中与转发路径正确性 |\n"
        "| action_source_refs | fw_config_interface_ipv4, tg_send_ipv4_traffic |\n\n"
        "#### normal_path\n\n"
        "| 步骤 | 子步骤 | 操作 | 必要性 | action_source_refs / atomic_op.op_id | 说明 |\n"
        "|------|--------|------|--------|------------------------------------|------|\n"
        "| 1 | 1.1 | 配置接口 IPv4 地址 | 必要 | `fw_config_interface_ipv4` | 接口地址准备 |\n"
        "| 2 | 2.1 | 发送 IPv4 流量 | 必要 | `tg_send_ipv4_traffic` | 构造命中策略的流量 |\n\n"
        "#### abnormal_path\n\n"
        "| # | abnormal_item | related_normal_steps | input_or_state | action_source_refs / atomic_op.op_id | expected_handling |\n"
        "|---|---------------|---------------------|----------------|------------------------------------|-------------------|\n"
        "| A1 | 未匹配任何规则 | 2.1 | 源 IP 不在匹配范围内 | `tg_send_ipv4_traffic` | 策略路由命中计数不增加 |\n\n"
        "#### minimal_logic_chain\n\n"
        "| 链路节点 | 来源步骤 | necessity | action_source_refs | 说明 |\n"
        "|----------|----------|-----------|--------------------|------|\n"
        "| L1 | normal_path.1 | 必要 | `fw_config_interface_ipv4` | 接口地址准备 |\n"
        "| L2 | normal_path.2 | 必要 | `tg_send_ipv4_traffic` | 流量验证 |\n\n"
        "atomic_operations:\n"
        "  - op_id: fw_config_interface_ipv4\n"
        "    source: ptm-atomic\n"
        "  - op_id: tg_send_ipv4_traffic\n"
        "    source: ptm-atomic\n"
    )


def write_minimal_gate2_fixture(feature: Path, scenarios_text: str) -> None:
    (feature / ".input").mkdir(parents=True)
    write(feature / ".input" / "req.md", "# Feature A\n")
    write(feature / "kym" / "feature-input" / "directory-structure.md", "# Directory\n")
    write(feature / "kym" / "scenarios" / "confirmed-scenarios.md", scenarios_text)
    write(
        feature / "kym" / "mission-understanding" / "mission-statement.md",
        "# Mission\n\n"
        "Customers: 企业防火墙用户\n"
        "Information: 策略路由需求\n"
        "scope: 策略路由匹配和转发\n"
        "dont_test: 性能压测\n"
        "confirmation_gaps: resolved\n",
    )
    for skill in ("feature-parser", "kym", "scenario-discovery"):
        record_skill(feature, skill, f"fixture/{skill}.md")


def write_minimal_gate3_fixture(
    feature: Path,
    *,
    write_candidate_sources: bool,
    write_candidate_confirmations: bool,
) -> None:
    (feature / ".input").mkdir(parents=True)
    write(feature / ".input" / "req.md", "# Feature A\n")
    write(
        feature / "mfq" / "m-analysis" / "test-points.md",
        "# M\n\n| C（Condition） | A（Action） | E（Effect） | trace_refs |\n|---|---|---|---|\n| C | A | E | TP-001 |\nscenario_refs: [SCN-001]\n",
    )
    write(
        feature / "mfq" / "f-analysis" / "coupling-test-points.md",
        "# F\n\n| C 条件 | A 动作 | E 预期 | coupling_refs |\n|---|---|---|---|\n| C | A | E | CPL-001 |\n",
    )
    write(
        feature / "mfq" / "q-analysis" / "quality-test-points.md",
        "# Q\n\n| C 条件 | A 动作 | E 预期 | quality_dimension |\n|---|---|---|---|\n| C | A | E | reliability |\n",
    )
    write(feature / "mfq" / "integration" / "all-test-points.md", "TP-001\n")
    write(
        feature / "mfq" / "integration" / "logic-cases.md",
        "LC-ID: LC-001\nsource_tp_ids: [TP-001]\nfactor_bindings: [FAC-001]\ntopology_bindings: [TB-001]\n",
    )
    write(feature / "mfq" / "integration" / "test-data.md", "TD-001\n")
    write(
        feature / "process" / "plan" / "design-plan.md",
        "logic_case_id: LC-001\nrecommended_method: P-Process\nPPDCS: P-Process\n",
    )
    write(feature / "process" / "plan" / "design-planner-reasoning.md", "reasoning\n")
    write(feature / "mfq" / "factor-usage" / "factor-library-lock.yaml", "libraries: []\n")
    write(feature / "mfq" / "m-analysis" / "factor-resolution-report.md", "N_scanned: 1\nindex.yaml\n")
    if write_candidate_sources:
        write(
            feature / "mfq" / "m-analysis" / "candidate-factor-proposals.yaml",
            "candidates:\n  - candidate_id: CF-001\n    factor_name: 新增匹配模式\n",
        )
        write(
            feature / "mfq" / "m-analysis" / "candidate-ptm-atomic.yaml",
            "candidates:\n  - candidate_id: CAO-001\n    candidate_op_name: fw_config_new_match_mode\n    match_attempt: L4\n    score: 0.2\n",
        )
    if write_candidate_confirmations:
        write(
            feature / "mfq" / "candidates" / "factor-candidates.md",
            "| candidate_id | factor_name | decision |\n|---|---|---|\n| CF-001 | 新增匹配模式 | confirmed |\n",
        )
        write(
            feature / "mfq" / "candidates" / "ptm-atomic-candidates.md",
            "| candidate_id | op_name | decision |\n|---|---|---|\n| CAO-001 | fw_config_new_match_mode | modified |\n",
        )
    for skill in ("m-analyzer", "f-analyzer", "q-analyzer", "test-point-integrator", "design-planner"):
        record_skill(feature, skill, f"fixture/{skill}.md")


def valid_pc_artifact() -> str:
    return (
        "# PC-001\n\n"
        "physical_case_id: PC-001\n"
        "logic_case_id: LC-001\n"
        "trace_refs: [TP-001]\n"
        "scenario_refs: [SCN-001]\n"
        "action_source_refs:\n"
        "  - fw_config_policy_route\n"
        "topology_bindings:\n"
        "  - topology_binding_id: TB-001\n"
        "fact_status: confirmed\n\n"
        "case_steps:\n"
        "  - step_id: STEP-001\n"
        "    step_name: 配置源地址对象\n"
        "    target: DUT\n"
        "    atomic_op:\n"
        "      op_id: fw_config_policy_route\n"
        "      args:\n"
        "        src_addr: OBJ_SRC_WEB\n"
        "    expected_result: 规则保存成功\n\n"
        + PC_HEADER
        + PC_SEPARATOR
        + VALID_PC_ROW
    )


def valid_delivery_case() -> str:
    return (
        "# Feature特性测试用例\n\n"
        "logic_case_id: LC-001\n"
        "physical_case_id: PC-001\n"
        "trace_refs: [TP-001]\n"
        "scenario_refs: [SCN-001]\n"
        "action_source_refs: [fw_config_policy_route]\n"
        "topology_bindings: [TB-001]\n"
        "fact_status: confirmed\n"
        "case_steps: see PC source\n\n"
        + PC_HEADER
        + PC_SEPARATOR
        + VALID_PC_ROW
    )


def write_minimal_gate4_fixture(feature: Path, pc_text: str, delivery_case_text: str | None = None) -> None:
    (feature / ".input").mkdir(parents=True)
    write(feature / ".input" / "req.md", "# Feature A\n")
    write(feature / "ppdcs" / "ppdcs" / "LC-001.md", "design process\n")
    write(feature / "ppdcs" / "pc" / "PC-001.md", pc_text)
    write(feature / "ppdcs" / "coverage" / "coverage-summary.md", "coverage 100%\n")
    write(
        feature / "ppdcs" / "delivery" / "Feature特性测试方案.md",
        "logic_case_id physical_case_id trace_refs topology_bindings fact_status case_steps action_source_refs\n"
        "factor-library library_id=ngfw-policy-routing version=test checksum=test\n"
        "needs-confirmation\n",
    )
    write(
        feature / "ppdcs" / "delivery" / "Feature特性测试用例.md",
        delivery_case_text if delivery_case_text is not None else valid_delivery_case(),
    )
    write(
        feature / "ppdcs" / "delivery" / "Feature测试因子候选对比表.md",
        "| candidate_id | factor_name | decision |\n|---|---|---|\n| FAC-CAND-001 | 因子候选 | pending |\n",
    )
    write(
        feature / "ppdcs" / "delivery" / "Feature原子操作候选对比表.md",
        "| candidate_id | op_name | decision |\n|---|---|---|\n| AO-CAND-001 | op_candidate | pending |\n",
    )
    for skill in ("design-ppdcs-analyzer", "coverage-verifier", "deliverable-renderer"):
        record_skill(feature, skill, f"fixture/{skill}.md")


class CR018P2Tests(unittest.TestCase):
    def test_gate2_passes_with_normal_and_abnormal_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-pass-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate2_fixture(feature, valid_confirmed_scenarios())

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            state_text = (feature / "process" / "STATE.yaml").read_text(encoding="utf-8")
            self.assertIn("GATE-2 字段级: confirmed-scenarios 正常/异常链完整", text)
            self.assertIn("结论：`PASS`", text)
            self.assertIn('current_phase: "kym"', state_text)

    def test_gate2_passes_with_markdown_path_tables(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-md-table-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate2_fixture(feature, valid_markdown_confirmed_scenarios())

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("GATE-2 字段级: confirmed-scenarios 正常/异常链完整", text)
            self.assertIn("结论：`PASS`", text)

    def test_gate2_missing_minimal_logic_chain_stays_in_kym(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-no-mlc-") as tmp:
            feature = Path(tmp) / "feature-a"
            scenarios = valid_markdown_confirmed_scenarios().replace(
                "#### minimal_logic_chain\n\n"
                "| 链路节点 | 来源步骤 | necessity | action_source_refs | 说明 |\n"
                "|----------|----------|-----------|--------------------|------|\n"
                "| L1 | normal_path.1 | 必要 | `fw_config_interface_ipv4` | 接口地址准备 |\n"
                "| L2 | normal_path.2 | 必要 | `tg_send_ipv4_traffic` | 流量验证 |\n\n",
                "",
            )
            write_minimal_gate2_fixture(feature, scenarios)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            gate_text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            state_text = (feature / "process" / "STATE.yaml").read_text(encoding="utf-8")
            self.assertIn("缺少 minimal_logic_chain/最小逻辑链", gate_text)
            self.assertIn('current_phase: "kym"', state_text)

    def test_gate2_accepts_explicit_input_dir_symlink(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-symlink-") as tmp:
            feature = Path(tmp) / "feature-a"
            (feature / "input").mkdir(parents=True)
            (feature / ".input").symlink_to("input", target_is_directory=True)
            write(feature / "input" / "req.md", "# Feature A\n")
            write(feature / "kym" / "feature-input" / "directory-structure.md", "# Directory\n")
            write(feature / "kym" / "scenarios" / "confirmed-scenarios.md", valid_confirmed_scenarios())
            write(
                feature / "kym" / "mission-understanding" / "mission-statement.md",
                "# Mission\n\n"
                "Customers: 企业防火墙用户\n"
                "Information: 策略路由需求\n"
                "scope: 策略路由匹配和转发\n"
                "dont_test: 性能压测\n"
                "confirmation_gaps: resolved\n",
            )
            for skill in ("feature-parser", "kym", "scenario-discovery"):
                record_skill(feature, skill, f"fixture/{skill}.md")

            result = run_cmd(
                [
                    str(CHECKPOINT),
                    "--gate",
                    "GATE-2",
                    "--project-root",
                    str(feature),
                    "--input-dir",
                    str(feature / ".input"),
                ],
                cwd=REPO_ROOT,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("结论：`PASS`", text)

    def test_gate2_blocks_when_scenario_lacks_normal_and_abnormal_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-missing-chain-") as tmp:
            feature = Path(tmp) / "feature-a"
            scenarios = (
                "# Confirmed Scenarios\n\n"
                "input_document_classification: deployment_scenario_draft\n"
                "confirmation_gaps: []\n\n"
                "## Template Notes\n\n"
                "normal_path: see each scenario\n"
                "abnormal_path: see each scenario\n\n"
                "## Scenario SCN-001\n\n"
                "scenario_id: SCN-001\n"
                "scenario_goal: 验证策略路由\n"
                "review_status: confirmed\n"
                "minimal_logic_chain: [STEP-001]\n"
                "action_source_refs: [fw_config_policy_route]\n"
                "atomic_operations:\n"
                "  - op_id: fw_config_policy_route\n"
            )
            write_minimal_gate2_fixture(feature, scenarios)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("GATE-2 字段级: confirmed-scenarios 正常/异常链完整", text)
            self.assertIn("缺少 normal_path/正常路径", text)
            self.assertIn("缺少 abnormal_path/异常路径", text)

    def test_gate2_blocks_when_abnormal_path_lacks_related_steps(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-abnormal-") as tmp:
            feature = Path(tmp) / "feature-a"
            scenarios = valid_confirmed_scenarios().replace(
                "    related_normal_steps: [STEP-001]\n",
                "",
            )
            write_minimal_gate2_fixture(feature, scenarios)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("abnormal_path 缺少字段 related_normal_steps", text)

    def test_gate2_blocks_when_normal_step_lacks_atomic_ref(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-step-op-") as tmp:
            feature = Path(tmp) / "feature-a"
            scenarios = valid_confirmed_scenarios().replace(
                "    action_source_ref: tg_send_tcp_traffic\n",
                "",
                1,
            )
            write_minimal_gate2_fixture(feature, scenarios)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("normal_path.STEP-002 缺少原子操作引用", text)

    def test_gate2_displays_new_atomic_candidates_for_manual_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate2-new-op-") as tmp:
            feature = Path(tmp) / "feature-a"
            scenarios = (
                valid_confirmed_scenarios()
                + "\nnew_atomic_operations:\n"
                + "  - candidate_id: CAO-NEW-001\n"
                + "    candidate_op_name: fw_config_new_match_mode\n"
            )
            write_minimal_gate2_fixture(feature, scenarios)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-2", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            auto_text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-auto.md").read_text(encoding="utf-8")
            manual_text = (feature / "process" / "checkpoints" / "GATE-2-KYM-Exit-manual.md").read_text(encoding="utf-8")
            self.assertIn("GATE-2 新增原子操作候选确认", auto_text)
            self.assertIn("新增/候选原子操作需显式确认", manual_text)

    def test_gate3_blocks_when_candidates_lack_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate3-candidates-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate3_fixture(
                feature,
                write_candidate_sources=True,
                write_candidate_confirmations=False,
            )

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-3", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-3-MFQ-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("M10: 候选测试因子显式确认状态", text)
            self.assertIn("M11: 候选原子操作显式确认状态", text)
            self.assertIn("缺少带 decision/确认结果的候选汇总", text)

    def test_gate3_passes_when_candidates_have_user_confirmation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate3-confirmed-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate3_fixture(
                feature,
                write_candidate_sources=True,
                write_candidate_confirmations=True,
            )

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-3", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-3-MFQ-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("GATE-3 候选测试因子确认摘要", text)
            self.assertIn("GATE-3 候选原子操作确认摘要", text)

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

    def test_reinstall_replaces_manifest_entries_for_same_assets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-reinstall-") as tmp:
            workspace = Path(tmp)
            env = {"PTM_TEAM_RESOURCE_HOME": str(workspace / "resource")}
            for _ in range(2):
                install = run_cmd(
                    [
                        str(INSTALL),
                        "--source-dir",
                        str(REPO_ROOT),
                        "install",
                        "claude",
                        "--agent",
                        "ptm-tde",
                    ],
                    cwd=workspace,
                    env=env,
                )
                self.assertEqual(install.returncode, 0, install.stderr + install.stdout)

            manifest = json.loads((workspace / ".ptm-team-manifest.json").read_text(encoding="utf-8"))
            entries = manifest["installs"][0]["entries"]
            self.assertTrue((workspace / "resource" / "component-resource-links.yaml").is_file())
            self.assertTrue(any(
                entry.get("name") == "component-resource-links"
                and entry.get("kind") == "resource"
                for entry in entries
            ))
            keys = [
                (
                    entry.get("kind", ""),
                    entry.get("name", ""),
                    entry.get("path", ""),
                    entry.get("managed_block_id", ""),
                )
                for entry in entries
            ]
            self.assertEqual(len(keys), len(set(keys)))

            check = run_cmd(
                [
                    str(INSTALL),
                    "--source-dir",
                    str(REPO_ROOT),
                    "check",
                    "claude",
                    "--agent",
                    "ptm-tde",
                ],
                cwd=workspace,
                env=env,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

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
            write_minimal_gate4_fixture(
                feature,
                "| physical_case_id | logic_case_id |\n|---|---|\n| PC-001 | LC-001 |\n",
            )

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            gate = feature / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md"
            text = gate.read_text(encoding="utf-8")
            self.assertIn("P2: PC 16 列严格格式检查", text)
            self.assertIn("BLOCKING", text)

    def test_gate4_blocks_when_pc_step_lacks_atomic_op(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate4-step-") as tmp:
            feature = Path(tmp) / "feature-a"
            row_without_atomic = VALID_PC_ROW.replace(
                "<br>原子操作：fw_config_policy_route src_addr=OBJ_SRC_WEB",
                "",
            )
            pc_without_step_op = (
                valid_pc_artifact()
                .replace("    atomic_op:\n      op_id: fw_config_policy_route\n      args:\n        src_addr: OBJ_SRC_WEB\n", "")
                .replace(VALID_PC_ROW, row_without_atomic)
            )
            write_minimal_gate4_fixture(feature, pc_without_step_op)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("P2: PC case_steps 原子操作回链检查", text)
            self.assertIn("缺少 case_steps[].atomic_op", text)

    def test_gate4_blocks_when_pc_table_row_has_extra_column(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate4-columns-") as tmp:
            feature = Path(tmp) / "feature-a"
            drifted_row = VALID_PC_ROW.replace("策略路由 | 功能", "策略|路由 | 功能")
            pc_with_extra_column = valid_pc_artifact().replace(VALID_PC_ROW, drifted_row)
            write_minimal_gate4_fixture(feature, pc_with_extra_column)

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("P2: PC 16 列严格格式检查", text)
            self.assertIn("列数为 17", text)

    def test_gate4_passes_with_case_steps_atomic_op_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate4-pass-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate4_fixture(feature, valid_pc_artifact())

            result = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (feature / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md").read_text(encoding="utf-8")
            self.assertIn("P2: PC case_steps 原子操作回链检查", text)
            self.assertIn("结论：`PASS`", text)

    def test_gate5_pass_sets_completed_phase(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ptm-cr018-gate5-pass-") as tmp:
            feature = Path(tmp) / "feature-a"
            write_minimal_gate4_fixture(feature, valid_pc_artifact())

            gate4 = run_cmd([str(CHECKPOINT), "--gate", "GATE-4", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(gate4.returncode, 0, gate4.stdout + gate4.stderr)
            gate5 = run_cmd([str(CHECKPOINT), "--gate", "GATE-5", "--project-root", str(feature)], cwd=REPO_ROOT)
            self.assertEqual(gate5.returncode, 0, gate5.stdout + gate5.stderr)

            gate_text = (feature / "process" / "checkpoints" / "GATE-5-Exit.md").read_text(encoding="utf-8")
            state_text = (feature / "process" / "STATE.yaml").read_text(encoding="utf-8")
            self.assertIn("结论：`PASS`", gate_text)
            self.assertIn('current_phase: "completed"', state_text)
            self.assertIn('current_step: "completed"', state_text)


if __name__ == "__main__":
    unittest.main()
