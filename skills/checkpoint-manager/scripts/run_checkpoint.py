#!/usr/bin/env python3
"""Run ptm-tde checkpoints for a feature project (Gate/CP dual-mode routing).

Gate mode (--gate GATE-N): execute GATE-1 through GATE-5 checks.
CP compat mode (--cp CPxx): auto-route to corresponding Gate or internal check.
Legacy mode (positional CP01): backward-compatible GATE-1 entry.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQ_SUFFIXES = {".md", ".markdown", ".docx", ".xlsx", ".xls", ".pdf", ".txt"}
TOPO_MARKERS = ("topo", "topology", "组网", "拓扑")
COUPLING_MARKERS = ("coupling", "matrix", "耦合", "矩阵")

# CP -> Gate routing map (see docs/ptm-tde/gate-spec.md CP/Gate mapping table)
CP_TO_GATE: dict[str, str] = {
    "CP01": "GATE-1",
    "CP02": "GATE-2",
    "CP03": "MFQ-INTERNAL-M",
    "CP04": "MFQ-INTERNAL-F",
    "CP05": "MFQ-INTERNAL-Q",
    "CP06": "MFQ-INTERNAL-INTEGRATION",
    "CP07": "MFQ-INTERNAL-PLAN",
    "CP08": "PPDCS-INTERNAL-DESIGN",
    "CP09": "GATE-4",
    "CP10": "PPDCS-INTERNAL-PC",
    "CP11": "GATE-4",
    "CP12": "GATE-5",
}

# Gate display names (used in output filenames)
GATE_NAMES: dict[str, str] = {
    "GATE-1": "Entry",
    "GATE-2": "KYM-Exit",
    "GATE-3": "MFQ-Exit",
    "GATE-4": "PPDCS-Exit",
    "GATE-5": "Exit",
}

# Internal check target directories
INTERNAL_DIR_MAP: dict[str, str] = {
    "MFQ-INTERNAL-M": "mfq/m-analysis",
    "MFQ-INTERNAL-F": "mfq/f-analysis",
    "MFQ-INTERNAL-Q": "mfq/q-analysis",
    "MFQ-INTERNAL-INTEGRATION": "mfq/integration",
    "MFQ-INTERNAL-PLAN": "process/plan",
    "PPDCS-INTERNAL-DESIGN": "ppdcs/ppdcs",
    "PPDCS-INTERNAL-PC": "ppdcs/pc",
}

# Required directories for the new directory structure
REQUIRED_DIRS: list[str] = [
    "kym/feature-input",
    "kym/scenarios",
    "mfq/m-analysis",
    "mfq/f-analysis",
    "mfq/q-analysis",
    "mfq/integration",
    "mfq/factor-usage",
    "process/plan",
    "ppdcs/ppdcs",
    "ppdcs/pc",
    "ppdcs/coverage",
    "ppdcs/delivery",
    "process/checkpoints",
]


# ---------------------------------------------------------------------------
# Utility functions (kept from original)
# ---------------------------------------------------------------------------

def find_files(root: Path, markers: tuple[str, ...] | None = None) -> list[Path]:
    """Find files in *root* matching optional *markers* (case-insensitive name match).

    When *markers* is None, match any file whose suffix is in REQ_SUFFIXES.
    """
    if not root.exists() or not root.is_dir():
        return []
    hits: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if markers is None:
            if path.suffix.lower() in REQ_SUFFIXES:
                hits.append(path)
        elif any(marker.lower() in name for marker in markers):
            hits.append(path)
    return sorted(hits)


def read_title(path: Path) -> str:
    """Extract the first `# heading` line from a Markdown / text file."""
    if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
        return ""
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    except OSError:
        return ""
    return ""


def status_line(ok: bool, evidence: str, blocked_hint: str = "") -> tuple[str, str]:
    """Return (status, detail) tuple for a check item."""
    if ok:
        return "PASS", evidence
    return "BLOCKING", blocked_hint or evidence


def probe_atomic_ops() -> tuple[bool, str]:
    """Check whether the global `atomic-ops` command is available."""
    executable = shutil.which("atomic-ops")
    if not executable:
        return False, "global command atomic-ops not found"
    try:
        completed = subprocess.run(
            [executable, "list", "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"atomic-ops command failed: {exc}"
    if completed.returncode == 0:
        return True, f"atomic-ops list --format json ok: {executable}"
    stderr = completed.stderr.strip() or completed.stdout.strip()
    return False, f"atomic-ops returned {completed.returncode}: {stderr}"


def probe_factor_libraries() -> tuple[bool, str]:
    """Check whether public factor-libraries are accessible.

    Checks in order:
      1. $PTM_TEAM_RESOURCE_HOME/factor-libraries
      2. ~/.ptm-team/resource/factor-libraries
      3. resource/factor-libraries (dev mode, relative to cwd)
    """
    candidates = []
    env_home = os.environ.get("PTM_TEAM_RESOURCE_HOME")
    if env_home:
        candidates.append(Path(env_home) / "factor-libraries")
    candidates.append(Path.home() / ".ptm-team" / "resource" / "factor-libraries")
    candidates.append(Path.cwd() / "resource" / "factor-libraries")
    for p in candidates:
        if p.is_dir():
            return True, f"factor-libraries accessible at {p}"
    return False, "factor-libraries not found (checked PTM_TEAM_RESOURCE_HOME, ~/.ptm-team, cwd/resource)"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def gate_output_path(checkpoints_dir: Path, gate: str, suffix: str = "") -> Path:
    """Build output path: process/checkpoints/GATE-{N}-{Name}[-{suffix}].md"""
    name = GATE_NAMES.get(gate, gate)
    if suffix:
        return checkpoints_dir / f"{gate}-{name}-{suffix}.md"
    return checkpoints_dir / f"{gate}-{name}.md"


def write_state(
    project_root: Path,
    feature_name: str,
    gate: str,
    gate_status: str,
    current_step: str = "",
) -> None:
    """Write / update process/STATE.yaml with current phase, step, gate."""
    process_dir = project_root / "process"
    process_dir.mkdir(parents=True, exist_ok=True)
    state_path = process_dir / "STATE.yaml"
    phase_map = {
        "GATE-1": "kym",
        "GATE-2": "mfq",
        "GATE-3": "ppdcs",
        "GATE-4": "exit",
        "GATE-5": "completed",
    }
    current_phase = phase_map.get(gate, "kym")
    content = (
        f'current_phase: "{current_phase}"\n'
        f'current_step: "{current_step}"\n'
        f'current_gate: "{gate}"\n'
        f'feature_name: "{feature_name}"\n'
        'runtime_root: "."\n'
        f'gate_status: "{gate_status}"\n'
        f'updated_at: "{dt.datetime.now(dt.timezone.utc).isoformat()}"\n'
    )
    state_path.write_text(content, encoding="utf-8")


def ensure_dirs(project_root: Path) -> list[str]:
    """Create required directories; return list of errors (empty = all ok)."""
    errors: list[str] = []
    for rel in REQUIRED_DIRS:
        directory = project_root / rel
        try:
            if directory.exists() and not directory.is_dir():
                errors.append(f"{directory} is not a directory")
            else:
                directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            errors.append(f"{directory}: {exc}")
    return errors


def write_skeleton_result(
    checkpoints_dir: Path,
    gate: str,
    overall: str,
    feature_name: str,
    checks: list[tuple[int, str, str, str]],
    pending_items: list[tuple[int, str]] | None = None,
    suffix: str = "",
    extra_sections: str = "",
) -> Path:
    """Write a Gate check result Markdown file with check_depth: skeleton header."""
    path = gate_output_path(checkpoints_dir, gate, suffix)
    name = GATE_NAMES.get(gate, gate)
    rows = "\n".join(
        f"| {idx} | {item} | {status} | {evidence} |"
        for idx, item, status, evidence in checks
    )
    pending_rows = ""
    if pending_items:
        pending_rows = "\n".join(
            f"| {idx} | {item} | PENDING | 待 CR-011/012/013 激活 |"
            for idx, item in pending_items
        )
    content = (
        f"---\n"
        f"check_depth: skeleton\n"
        f"gate: {gate}\n"
        f"---\n"
        f"# {gate} {name}\n\n"
        f"- 结论：`{overall}`\n"
        f"- 特性名：`{feature_name}`\n"
        f"- 检查时间：`{dt.datetime.now(dt.timezone.utc).isoformat()}`\n\n"
        f"## 基础检查（目录存在性）\n\n"
        f"| # | 检查项 | 状态 | 证据 / 处理意见 |\n"
        f"|---|---|---|---|\n"
        f"{rows}\n\n"
    )
    if extra_sections:
        content += extra_sections
    if pending_rows:
        content += (
            f"## 详细检查（待 CR-011/012/013 激活）\n\n"
            f"以下检查项来自 `docs/ptm-tde/gate-spec.md` §{gate} Checklist，"
            f"当前版本（CR-010）仅做骨架检查。"
            f"完成路径迁移和 Skill 改造后，由对应 CR 扩展为完整逐项检查。\n\n"
            f"| # | 检查项 | 状态 | 说明 |\n"
            f"|---|--------|------|------|\n"
            f"{pending_rows}\n"
        )
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Gate handlers
# ---------------------------------------------------------------------------

def run_gate_1(args: argparse.Namespace) -> int:
    """GATE-1 Entry Gate: validate feature project input readiness."""
    project_root = Path(args.project_root).resolve()
    input_root = project_root / "input"
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    requirement = Path(args.requirement).resolve() if args.requirement else None
    requirement_hits = (
        [requirement] if requirement and requirement.exists() else find_files(input_root)
    )
    topo_hits = find_files(input_root, TOPO_MARKERS)
    coupling_hits = find_files(input_root, COUPLING_MARKERS)
    atomic_ok, atomic_evidence = probe_atomic_ops()
    factor_ok, factor_evidence = probe_factor_libraries()

    title = read_title(requirement_hits[0]) if requirement_hits else ""
    feature_name = args.feature_name or title or project_root.name

    dir_errors = ensure_dirs(project_root)

    wiki_note = (
        f"wiki index provided: {args.wiki_index}"
        if args.wiki_index
        else "wiki lookup required if local evidence is missing"
    )
    checks: list[tuple[int, str, str, str]] = []
    requirement_evidence = ", ".join(str(p) for p in requirement_hits) or wiki_note
    checks.append((
        1, "需求文件存在",
        *status_line(
            bool(requirement_hits or args.wiki_index), requirement_evidence,
            "本地 input/ 和显式路径均未找到需求文件；请提供需求文件或 wiki 需求/接口文档。",
        ),
    ))
    checks.append((
        2, "特性名可确定",
        *status_line(
            bool(feature_name), feature_name,
            "无法确定特性名；请显式提供 --feature-name。",
        ),
    ))
    checks.append((
        3, "atomic-ops 可用或 wiki 兜底",
        *status_line(
            bool(atomic_ok or args.wiki_index),
            atomic_evidence if atomic_ok else wiki_note,
            "全局命令 atomic-ops 不可用，且未提供 wiki 兜底信息。",
        ),
    ))
    checks.append((
        4, "防火墙 topo 可用或 wiki 兜底",
        *status_line(
            bool(topo_hits or args.wiki_index),
            ", ".join(str(p) for p in topo_hits) or wiki_note,
            "本地 input/ 未找到 topo，wiki 也未提供；请补充防火墙 topo 文件或 wiki 文档。",
        ),
    ))
    checks.append((
        5, "耦合矩阵可用或 wiki 兜底",
        *status_line(
            bool(coupling_hits or args.wiki_index),
            ", ".join(str(p) for p in coupling_hits) or wiki_note,
            "本地 input/ 未找到耦合矩阵，wiki 也未提供；请补充耦合矩阵或 wiki 文档。",
        ),
    ))
    checks.append((
        6, "输出目录就绪",
        *status_line(not dir_errors, "runtime directories created", "; ".join(dir_errors)),
    ))
    checks.append((
        7, "公共因子库可解析",
        *status_line(
            True, factor_evidence,
            "",
        ),
    ))
    # Override status for factor check: warn but never block
    if not factor_ok:
        checks[-1] = (7, "公共因子库可解析", "WARN", factor_evidence)

    overall = "PASS" if all(status in ("PASS", "WARN") for _, status, _, _ in checks) else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-1", overall, feature_name, checks,
    )
    write_state(project_root, feature_name, "GATE-1", overall, current_step="feature-parser")
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_2(args: argparse.Namespace) -> int:
    """GATE-2 KYM Exit Gate: skeleton check for KYM phase completion."""
    project_root = Path(args.project_root).resolve()
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: check key KYM directories exist
    kym_dirs = {
        "kym/scenarios": project_root / "kym" / "scenarios",
        "kym/feature-input": project_root / "kym" / "feature-input",
    }
    checks: list[tuple[int, str, str, str]] = []
    entry_ok = True
    for label, dirpath in kym_dirs.items():
        ok = dirpath.is_dir()
        if not ok:
            entry_ok = False
        checks.append((
            len(checks) + 1, f"Entry Criteria: {label}",
            "PASS" if ok else "BLOCKING",
            f"目录存在" if ok else f"目录不存在: {dirpath}",
        ))

    # Skeleton: basic directory existence for KYM phase deliverables
    required_dirs_map = {
        "kym/feature-input": project_root / "kym" / "feature-input",
        "kym/scenarios": project_root / "kym" / "scenarios",
        "process/checkpoints": project_root / "process" / "checkpoints",
    }
    for label, dirpath in required_dirs_map.items():
        ok = dirpath.is_dir()
        checks.append((
            len(checks) + 1, f"产物目录: {label}",
            "PASS" if ok else "MISSING",
            f"目录存在" if ok else f"目录不存在（阶段尚未执行或产物未生成）",
        ))

    # Pending detailed checks (14 items from gate-spec.md GATE-2 Checklist)
    pending_items = [
        (1, "输入文档类型识别"),
        (2, "功能种子再发现"),
        (3, "Seed-to-Scenario Mapping"),
        (4, "范围收敛"),
        (5, "Topology Catalog"),
        (6, "atomic-ops 唯一口径"),
        (7, "场景链完整"),
        (8, "正常路径可追溯"),
        (9, "选择组完整"),
        (10, "异常路径可追溯"),
        (11, "Knowledge Reference 三态"),
        (12, "Tool Gap"),
        (13, "Confirmation Gaps"),
        (14, "输出质量检查"),
    ]

    overall = "PASS" if entry_ok else "BLOCKED"
    # GATE-2 is auto + manual: output -auto.md first
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-2", overall, feature_name, checks,
        pending_items=pending_items, suffix="auto",
    )
    write_state(project_root, feature_name, "GATE-2", overall, current_step="scenario-discovery")
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_3(args: argparse.Namespace) -> int:
    """GATE-3 MFQ Exit Gate: skeleton check for MFQ phase completion."""
    project_root = Path(args.project_root).resolve()
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: MFQ directories
    mfq_dirs = {
        "mfq/m-analysis": project_root / "mfq" / "m-analysis",
        "mfq/f-analysis": project_root / "mfq" / "f-analysis",
        "mfq/q-analysis": project_root / "mfq" / "q-analysis",
        "mfq/integration": project_root / "mfq" / "integration",
        "mfq/factor-usage": project_root / "mfq" / "factor-usage",
        "process/plan": project_root / "process" / "plan",
    }
    checks: list[tuple[int, str, str, str]] = []
    entry_ok = True
    for label, dirpath in mfq_dirs.items():
        ok = dirpath.is_dir()
        if not ok:
            entry_ok = False
        checks.append((
            len(checks) + 1, f"Entry Criteria: {label}",
            "PASS" if ok else "BLOCKING",
            f"目录存在" if ok else f"目录不存在: {dirpath}",
        ))

    # Upstream/downstream Warnings (non-blocking)
    warnings = (
        "## 上下游 Warning（非阻断）\n\n"
        "| # | 检查项 | 状态 | 说明 |\n"
        "|---|--------|------|------|\n"
        "| W1 | KYM 场景下游可消费 | WARNING | 场景产物可被 MFQ 正确消费（骨架检查不验证） |\n"
        "| W2 | PPDCS 可消费 plan | WARNING | 设计计划可被 PPDCS 阶段正确读取（骨架检查不验证，PPDCS Exit Gate 二次检查） |\n"
    )

    # Pending detailed checks
    pending_items = [
        (1, "M 分析输出完整"),
        (2, "F 分析输出完整"),
        (3, "Q 分析输出完整"),
        (4, "测试点整合完整"),
        (5, "LC topology_bindings 一致"),
        (6, "设计计划存在"),
        (7, "公共因子库 lock 有效"),
        (8, "plan 存在性和格式"),
    ]

    overall = "PASS" if entry_ok else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-3", overall, feature_name, checks,
        pending_items=pending_items, suffix="auto",
        extra_sections=warnings,
    )
    write_state(project_root, feature_name, "GATE-3", overall, current_step="test-point-integrator")
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_4(args: argparse.Namespace) -> int:
    """GATE-4 PPDCS Exit Gate: skeleton check for PPDCS phase completion."""
    project_root = Path(args.project_root).resolve()
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: PPDCS directories
    ppdcs_dirs = {
        "ppdcs/ppdcs": project_root / "ppdcs" / "ppdcs",
        "ppdcs/pc": project_root / "ppdcs" / "pc",
        "ppdcs/coverage": project_root / "ppdcs" / "coverage",
    }
    checks: list[tuple[int, str, str, str]] = []
    entry_ok = True
    for label, dirpath in ppdcs_dirs.items():
        ok = dirpath.is_dir()
        if not ok:
            entry_ok = False
        checks.append((
            len(checks) + 1, f"Entry Criteria: {label}",
            "PASS" if ok else "BLOCKING",
            f"目录存在" if ok else f"目录不存在: {dirpath}",
        ))

    # Skeleton: basic directory check for delivery
    delivery_dir = project_root / "ppdcs" / "delivery"
    ok = delivery_dir.is_dir()
    checks.append((
        len(checks) + 1, "产物目录: ppdcs/delivery",
        "PASS" if ok else "MISSING",
        f"目录存在" if ok else f"目录不存在（阶段尚未执行或产物未生成）",
    ))

    # Pending detailed checks
    pending_items = [
        (1, "PPDCS 设计完整"),
        (2, "PC 生成完整"),
        (3, "PC 物化回链"),
        (4, "覆盖率验证"),
        (5, "拓扑绑定状态保持"),
        (6, "交付物预检"),
        (7, "plan 消费完整性"),
    ]

    overall = "PASS" if entry_ok else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-4", overall, feature_name, checks,
        pending_items=pending_items, suffix="auto",
    )
    write_state(project_root, feature_name, "GATE-4", overall, current_step="design-ppdcs")
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_5(args: argparse.Namespace) -> int:
    """GATE-5 Exit Gate: skeleton check for final delivery readiness."""
    project_root = Path(args.project_root).resolve()
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: GATE-4 result exists, delivery dir exists
    checks: list[tuple[int, str, str, str]] = []
    entry_ok = True
    gate4_result = project_root / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md"
    if not gate4_result.exists():
        entry_ok = False
        checks.append((
            1, "GATE-4 已通过",
            "BLOCKING",
            f"GATE-4 结果文件不存在: {gate4_result}",
        ))
    else:
        checks.append((
            1, "GATE-4 已通过",
            "PASS",
            f"GATE-4 结果文件存在: {gate4_result}",
        ))

    delivery_dir = project_root / "ppdcs" / "delivery"
    ok = delivery_dir.is_dir()
    if not ok:
        entry_ok = False
    checks.append((
        2, "交付物目录存在",
        "PASS" if ok else "BLOCKING",
        f"目录存在" if ok else f"目录不存在: {delivery_dir}",
    ))

    # Pending detailed checks
    pending_items = [
        (1, "交付物完整"),
        (2, "交付字段保留"),
        (3, "公共库记录"),
        (4, "不可提升状态"),
    ]

    overall = "PASS" if entry_ok else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-5", overall, feature_name, checks,
        pending_items=pending_items,
    )
    write_state(project_root, feature_name, "GATE-5", overall, current_step="delivery")
    print(result_path)
    return 0 if overall == "PASS" else 2


# ---------------------------------------------------------------------------
# CP compat wrapper
# ---------------------------------------------------------------------------

def run_cp01(args: argparse.Namespace) -> int:
    """CP01 compat entry: delegates to GATE-1 handler."""
    return run_gate_1(args)


# ---------------------------------------------------------------------------
# Internal check (stage-internal scrolling check)
# ---------------------------------------------------------------------------

def run_internal_check(cp: str, target: str, args: argparse.Namespace) -> int:
    """Execute a stage-internal scrolling check (CP03-CP07, CP08, CP10).

    Internal checks do not generate independent Gate output files.
    They verify the corresponding product directory exists and output
    a lightweight summary to stdout.  Detailed check logic is deferred
    to CR-012 (MFQ) and CR-013 (PPDCS).
    """
    project_root = Path(args.project_root).resolve()
    phase = "MFQ" if target.startswith("MFQ-INTERNAL-") else "PPDCS"
    print(f"[{cp}] {phase} 阶段内滚动自检: {target}")

    target_rel = INTERNAL_DIR_MAP.get(target)
    if target_rel:
        target_dir = project_root / target_rel
        if target_dir.is_dir():
            print(f"  {cp} 产物目录存在: {target_dir}")
            return 0
        else:
            print(f"  {cp} 产物目录不存在: {target_dir}（阶段尚未执行或产物未生成）")
            return 1
    print(f"  {cp} 未知内部检查目标: {target}")
    return 2


# ---------------------------------------------------------------------------
# Routing dispatchers
# ---------------------------------------------------------------------------

def dispatch_gate(gate: str, args: argparse.Namespace) -> int:
    """Route *gate* id to the corresponding handler function."""
    handlers: dict[str, callable] = {
        "GATE-1": run_gate_1,
        "GATE-2": run_gate_2,
        "GATE-3": run_gate_3,
        "GATE-4": run_gate_4,
        "GATE-5": run_gate_5,
    }
    handler = handlers.get(gate)
    if handler is None:
        print(f"Unknown gate: {gate}", file=sys.stderr)
        return 2
    return handler(args)


def dispatch_cp(cp: str, args: argparse.Namespace) -> int:
    """Route *cp* id to its Gate target or internal check via CP_TO_GATE map."""
    target = CP_TO_GATE.get(cp)
    if target is None:
        print(f"Unknown checkpoint: {cp}", file=sys.stderr)
        return 2
    if target.startswith("MFQ-INTERNAL-") or target.startswith("PPDCS-INTERNAL-"):
        return run_internal_check(cp, target, args)
    return dispatch_gate(target, args)


def dispatch_legacy(args: argparse.Namespace) -> int:
    """Backward-compat: handle positional checkpoint_id (CP01 only).

    Positional arg CP01 is mutually exclusive with --gate/--cp
    (argparse does not auto-enforce cross-arg-group mutual exclusion,
    so we rely on main() routing priority: --gate > --cp > positional).
    """
    checkpoint_id = getattr(args, "checkpoint_id", None)
    if checkpoint_id == "CP01":
        print("[legacy] 位置参数 CP01 -> 路由到 GATE-1 Entry Gate")
        return run_gate_1(args)
    if checkpoint_id is not None:
        print(f"Unknown legacy checkpoint: {checkpoint_id}", file=sys.stderr)
        return 2
    print("请指定 --gate、--cp 或位置参数 CP01", file=sys.stderr)
    return 2


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="ptm-tde 检查点脚本（Gate/CP 双模式路由）",
    )
    # Positional arg: backward-compat CP01 entry
    parser.add_argument(
        "checkpoint_id",
        nargs="?",
        choices=["CP01"],
        default=None,
        help="（向后兼容）位置参数 CP01，自动路由到 GATE-1 Entry Gate",
    )
    # --gate / --cp mutually exclusive group
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--gate",
        choices=["GATE-1", "GATE-2", "GATE-3", "GATE-4", "GATE-5"],
        default=None,
        help="Gate 模式：执行指定 Gate 检查",
    )
    mode_group.add_argument(
        "--cp",
        choices=[f"CP{str(i).zfill(2)}" for i in range(1, 13)],
        default=None,
        help="CP 兼容模式：自动路由到对应 Gate 或阶段内自检",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--feature-name", default="")
    parser.add_argument("--requirement", default="")
    parser.add_argument("--wiki-index", default="")
    args = parser.parse_args()

    # Routing priority: --gate > --cp > positional checkpoint_id
    if args.gate:
        return dispatch_gate(args.gate, args)
    if args.cp:
        return dispatch_cp(args.cp, args)
    # Backward-compat: positional CP01
    if args.checkpoint_id:
        print(f"[legacy] 位置参数 {args.checkpoint_id} -> 路由到 GATE-1 Entry Gate")
        return run_gate_1(args)
    # Nothing specified
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
