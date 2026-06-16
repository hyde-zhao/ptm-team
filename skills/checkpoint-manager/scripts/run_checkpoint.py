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
import re
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
STANDARD_PC_COLUMNS: tuple[str, ...] = (
    "三级目录",
    "四级目录",
    "五级目录",
    "用例名称*",
    "用例编号",
    "用例级别*",
    "组网描述*",
    "组网约束",
    "预置条件",
    "测试步骤*",
    "预期结果*",
    "首次创建版本*",
    "最后变更版本",
    "关键词",
    "测试类型*",
    "是否自动化*",
)
TEST_STEPS_COLUMN = STANDARD_PC_COLUMNS.index("测试步骤*")
REF_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")
NORMAL_PATH_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "step_id": ("step_id", "step-id", "步骤编号", "步骤ID", "步骤"),
    "sub_step_ids": ("sub_step_ids", "sub-step-ids", "子步骤编号", "子步骤"),
    "operation": ("operation", "操作", "动作"),
    "necessity": ("necessity", "必要性", "是否必要"),
    "action_source_refs": (
        "action_source_refs",
        "action_source_ref",
        "atomic_op",
        "atomic_op.op_id",
        "op_id",
        "原子操作",
    ),
    "description": ("description", "描述", "说明"),
}
NORMAL_PATH_NECESSITY_VALUES = ("必要", "可选", "至少选择一项")
ABNORMAL_PATH_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "abnormal_item": ("abnormal_item", "abnormal-item", "异常项", "异常操作"),
    "related_normal_steps": ("related_normal_steps", "related-normal-steps", "关联正常步骤", "关联步骤"),
    "input_or_state": ("input_or_state", "input-or-state", "异常输入", "输入状态", "输入/状态"),
    "action_source_refs": (
        "action_source_refs",
        "action_source_ref",
        "atomic_op",
        "atomic_op.op_id",
        "op_id",
        "原子操作",
    ),
    "expected_handling": ("expected_handling", "expected-handling", "预期处理", "预期行为"),
}
ABNORMAL_PATH_NA_MARKERS = ("N/A", "n/a", "not applicable", "不适用", "无异常路径", "无需异常路径")
ABNORMAL_PATH_NA_REASON_MARKERS = ("reason", "理由", "原因", "说明", "because", "由于", "因为")
STEP_ATOMIC_REF_KEYS = ("action_source_ref", "action_source_refs", "atomic_op", "op_id", "原子操作")
NEW_ATOMIC_CANDIDATE_MARKERS = (
    "new_atomic",
    "candidate_atomic",
    "candidate-ptm-atomic",
    "candidate_ptm_atomic",
    "new-candidate",
    "新增原子操作",
    "候选原子操作",
    "Tool Abstraction Draft",
    "tool_abstraction_draft",
)
CANDIDATE_ITEM_MARKERS = (
    "candidate_id",
    "candidate:",
    "new-candidate",
    "候选ID",
    "候选因子",
    "候选原子操作",
    "候选列表汇总",
)
CANDIDATE_CONFIRMATION_MARKERS = (
    "decision",
    "confirmed",
    "rejected",
    "modified",
    "用户确认",
    "确认结果",
    "已确认",
    "已拒绝",
    "已修改",
    "全部确认",
    "逐项确认",
)
FINAL_CANDIDATE_DECISION_MARKERS = (
    "decision=confirmed",
    "decision: confirmed",
    "decision：confirmed",
    "decision=rejected",
    "decision= rejected",
    "decision: rejected",
    "decision：rejected",
    "decision=modified",
    "decision: modified",
    "decision：modified",
    "| confirmed |",
    "| rejected |",
    "| modified |",
    "decision=已确认",
    "decision: 已确认",
    "decision：已确认",
    "decision=已拒绝",
    "decision: 已拒绝",
    "decision：已拒绝",
    "decision=已修改",
    "decision: 已修改",
    "decision：已修改",
    "已确认",
    "已拒绝",
    "已修改",
    "确认结果: confirmed",
    "确认结果：confirmed",
    "确认结果: rejected",
    "确认结果：rejected",
    "确认结果: modified",
    "确认结果：modified",
)
PENDING_CANDIDATE_DECISION_MARKERS = (
    "pending-review",
    "pending review",
    "pending_review",
    "decision=pending",
    "decision: pending",
    "decision：pending",
    "decision=pending-review",
    "decision: pending-review",
    "decision：pending-review",
    "| pending |",
    "| pending-review |",
    "待评审",
    "待确认",
    "未确认",
    "待用户确认",
    "需人工确认",
    "todo",
    "tbd",
)
SCENARIO_BLOCK_MARKERS = (
    "scenario_id",
    "scenario_goal",
    "review_status",
    "normal_path",
    "abnormal_path",
    "minimal_logic_chain",
    "场景编号",
    "场景目标",
    "正常路径",
    "异常路径",
    "最小逻辑链",
)

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
    "kym/mission-understanding",
    "kym/scenarios",
    "mfq/m-analysis",
    "mfq/f-analysis",
    "mfq/q-analysis",
    "mfq/integration",
    "mfq/candidates",
    "mfq/factor-usage",
    "process/plan",
    "ppdcs/ppdcs",
    "ppdcs/pc",
    "ppdcs/coverage",
    "ppdcs/delivery",
    "process/checkpoints",
    "process/execution",
]

IGNORED_INPUT_SEARCH_DIRS = {
    ".agents",
    ".claude",
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


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


def discover_input_dirs(root: Path) -> list[Path]:
    """Find `.input` directories below root while skipping generated/vendor trees."""
    if not root.is_dir():
        return []
    hits: list[Path] = []
    for current, dirnames, _filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames
            if name not in IGNORED_INPUT_SEARCH_DIRS
        ]
        current_path = Path(current)
        if current_path.name == ".input":
            hits.append(current_path)
            dirnames[:] = []
    return sorted(path.resolve() for path in hits)


def input_dir_from_requirement(requirement: str) -> Path | None:
    """Return the containing `.input` directory when a requirement path proves it."""
    if not requirement:
        return None
    req_path = Path(requirement).expanduser()
    try:
        resolved = req_path.resolve()
    except OSError:
        resolved = req_path.absolute()
    for parent in (resolved, *resolved.parents):
        if parent.name == ".input":
            return parent
    return None


def resolve_feature_workspace(args: argparse.Namespace) -> tuple[Path, Path]:
    """Resolve feature workspace root and input root from CLI arguments.

    `.input` is the canonical input directory. Its parent is always the
    feature_workspace_root; all runtime output must be written there.
    """
    raw_requested_root = Path(args.project_root).expanduser()
    requested_root = raw_requested_root.resolve()
    explicit_input = getattr(args, "input_dir", "")

    if explicit_input:
        raw_input_root = Path(explicit_input).expanduser()
        input_root_candidate = raw_input_root if raw_input_root.is_absolute() else requested_root / raw_input_root
        if input_root_candidate.name != ".input":
            print(f"--input-dir 必须指向 .input 目录: {input_root_candidate}", file=sys.stderr)
            raise SystemExit(2)
        return input_root_candidate.parent.resolve(), input_root_candidate.resolve()

    requirement_input = input_dir_from_requirement(getattr(args, "requirement", ""))
    if requirement_input is not None:
        return requirement_input.parent, requirement_input

    if raw_requested_root.name == ".input":
        return raw_requested_root.parent.resolve(), requested_root

    direct_input = requested_root / ".input"
    if direct_input.is_dir():
        return requested_root, direct_input

    nested_inputs = discover_input_dirs(requested_root)
    if len(nested_inputs) == 1:
        input_root = nested_inputs[0]
        return input_root.parent, input_root
    if len(nested_inputs) > 1:
        joined = "\n".join(f"  - {path}" for path in nested_inputs)
        print(
            "发现多个 .input 目录，请使用 --project-root 指定特性目录或 "
            "--input-dir 指定目标输入目录:\n" + joined,
            file=sys.stderr,
        )
        raise SystemExit(2)

    legacy_input = requested_root / "input"
    if legacy_input.is_dir():
        return requested_root, legacy_input

    return requested_root, direct_input


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


def probe_ptm_atomic() -> tuple[bool, str]:
    """Check whether the global `ptm-atomic` command is available."""
    executable = shutil.which("ptm-atomic")
    if not executable:
        return False, "global command ptm-atomic not found"
    try:
        completed = subprocess.run(
            [executable, "list", "--format", "json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"ptm-atomic command failed: {exc}"
    if completed.returncode == 0:
        return True, f"ptm-atomic list --format json ok: {executable}"
    stderr = completed.stderr.strip() or completed.stdout.strip()
    return False, f"ptm-atomic returned {completed.returncode}: {stderr}"


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


def _find_factor_library_root() -> Path | None:
    """Find the factor-libraries directory using the standard lookup order.

    Returns the first accessible directory, or None.
    """
    env_home = os.environ.get("PTM_TEAM_RESOURCE_HOME")
    if env_home:
        p = Path(env_home) / "factor-libraries"
        if p.is_dir():
            return p
    p = Path.home() / ".ptm-team" / "resource" / "factor-libraries"
    if p.is_dir():
        return p
    p = Path.cwd() / "resource" / "factor-libraries"
    if p.is_dir():
        return p
    return None


def _strip_yaml_value(value: str) -> str:
    """Strip a simple YAML scalar value."""
    return value.strip().strip('"').strip("'")


def probe_factor_library_content() -> tuple[bool, str, list[str]]:
    """Verify that factor libraries referenced in index.yaml actually exist on disk.

    Returns (ok, evidence, missing_list).
      - ok: True if all referenced libraries exist, False if any are missing.
      - evidence: human-readable summary.
      - missing_list: list of missing library_id (empty if all present).
    """
    root = _find_factor_library_root()
    if root is None:
        return False, "factor-libraries 目录不可访问", []

    index_path = root / "index.yaml"
    if not index_path.is_file():
        return False, f"index.yaml 不存在: {index_path}", []

    # Parse index.yaml — simple line-by-line YAML subset
    libraries: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    current_id = ""
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- library_id:"):
            current_id = _strip_yaml_value(line.split(":", 1)[1])
            current = {"library_id": current_id}
            libraries[current_id] = current
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = _strip_yaml_value(value)

    if not libraries:
        return True, "index.yaml 存在但未声明任何因子库", []

    # Verify each library's content
    present: list[str] = []
    missing: list[tuple[str, str]] = []
    for lib_id, meta in libraries.items():
        rel_path = meta.get("path", f"{lib_id}/factor-library.yaml")
        lib_file = root / rel_path
        if lib_file.is_file():
            present.append(lib_id)
        else:
            missing.append((lib_id, str(lib_file)))

    if missing:
        missing_ids = [m[0] for m in missing]
        missing_paths = "; ".join(f"{m[0]} -> {m[1]}" for m in missing)
        evidence = (
            f"index 声明 {len(libraries)} 个因子库，"
            f"已存在 {len(present)} 个，"
            f"缺失 {len(missing)} 个: {missing_paths}"
        )
        return False, evidence, missing_ids

    evidence = f"index 声明 {len(libraries)} 个因子库，全部存在: {', '.join(present)}"
    return True, evidence, []


def _find_coupling_matrix_root() -> Path | None:
    """Find the coupling-matrix directory using the standard lookup order."""
    env_home = os.environ.get("PTM_TEAM_RESOURCE_HOME")
    if env_home:
        p = Path(env_home) / "coupling-matrix"
        if p.is_dir():
            return p
    p = Path.home() / ".ptm-team" / "resource" / "coupling-matrix"
    if p.is_dir():
        return p
    p = Path.cwd() / "resource" / "coupling-matrix"
    if p.is_dir():
        return p
    return None


def probe_coupling_matrix_content() -> tuple[bool, str]:
    """Verify that coupling matrix files referenced in index.yaml actually exist.

    Returns (ok, evidence).
      - ok: True if all referenced files exist, False if any are missing.
      - evidence: human-readable summary including missing file paths.
    """
    root = _find_coupling_matrix_root()
    if root is None:
        return True, "coupling-matrix 目录不可访问（无可用耦合矩阵资源，不阻断）"

    index_path = root / "index.yaml"
    if not index_path.is_file():
        return True, f"index.yaml 不存在: {index_path}（无可校验的索引，不阻断）"

    # Parse index.yaml
    matrices: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    current_id = ""
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- matrix_id:"):
            current_id = _strip_yaml_value(line.split(":", 1)[1])
            current = {"matrix_id": current_id}
            matrices[current_id] = current
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = _strip_yaml_value(value)

    if not matrices:
        return True, "index.yaml 存在但未声明任何耦合矩阵"

    # Verify each matrix's source and feature_tree files
    present: list[str] = []
    missing_files: list[str] = []
    for mid, meta in matrices.items():
        all_ok = True
        for field in ("source", "feature_tree"):
            rel = meta.get(field, "")
            if not rel:
                continue
            file_path = root / rel
            if file_path.is_file():
                continue
            missing_files.append(f"{mid}:{field} -> {file_path}")
            all_ok = False
        if all_ok:
            present.append(mid)

    if missing_files:
        evidence = (
            f"index 声明 {len(matrices)} 个耦合矩阵，"
            f"完整存在 {len(present)} 个，"
            f"缺失文件 {len(missing_files)} 处: {'; '.join(missing_files)}"
        )
        return False, evidence

    evidence = f"index 声明 {len(matrices)} 个耦合矩阵，全部文件存在: {', '.join(present)}"
    return True, evidence


def _resource_candidates(resource_subdir: str) -> list[Path]:
    """Return candidate paths for a shared resource subdirectory.

    Lookup order:
      1. $PTM_TEAM_RESOURCE_HOME/<subdir>
      2. ~/.ptm-team/resource/<subdir>
      3. cwd/resource/<subdir> (dev mode)
    """
    candidates: list[Path] = []
    env_home = os.environ.get("PTM_TEAM_RESOURCE_HOME")
    if env_home:
        candidates.append(Path(env_home).expanduser() / resource_subdir)
    candidates.append(Path.home() / ".ptm-team" / "resource" / resource_subdir)
    candidates.append(Path.cwd() / "resource" / resource_subdir)
    return candidates


def find_resource_files(resource_subdir: str, glob_pattern: str) -> list[Path]:
    """Search for resource files across shared resource directories.

    Returns list of matching file paths (may be empty).
    """
    hits: list[Path] = []
    for candidate in _resource_candidates(resource_subdir):
        if candidate.is_dir():
            for matched in sorted(candidate.glob(glob_pattern)):
                if matched.is_file():
                    hits.append(matched)
    return hits


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
    input_root: Path | None = None,
) -> None:
    """Write / update process/STATE.yaml with current phase, step, gate."""
    process_dir = project_root / "process"
    process_dir.mkdir(parents=True, exist_ok=True)
    state_path = process_dir / "STATE.yaml"
    resolved_input_root = input_root or project_root / ".input"
    # Gate checks are machine baselines. Human gates (GATE-2/3/4) must not
    # advance current_phase just because the auto check passed.
    phase_after_auto_pass = {
        "GATE-1": "kym",
        "GATE-2": "kym",
        "GATE-3": "mfq",
        "GATE-4": "ppdcs",
        "GATE-5": "completed",
    }
    phase_when_blocked = {
        "GATE-1": "kym",
        "GATE-2": "kym",
        "GATE-3": "mfq",
        "GATE-4": "ppdcs",
        "GATE-5": "delivery",
    }
    current_phase = (
        phase_after_auto_pass.get(gate, "kym")
        if gate_status == "PASS"
        else phase_when_blocked.get(gate, "kym")
    )
    content = (
        f'current_phase: "{current_phase}"\n'
        f'current_step: "{current_step}"\n'
        f'current_gate: "{gate}"\n'
        f'feature_name: "{feature_name}"\n'
        'runtime_root: "."\n'
        f'feature_workspace_root: "{project_root}"\n'
        f'input_root: "{resolved_input_root}"\n'
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


def nonempty_file(path: Path) -> bool:
    """Return True when path is an existing non-empty file."""
    return path.is_file() and path.stat().st_size > 0


def read_text(path: Path) -> str:
    """Read text safely for lightweight marker checks."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def find_nonempty_files(root: Path, suffixes: tuple[str, ...] = (".md", ".yaml", ".yml", ".json")) -> list[Path]:
    """Return non-empty product files under a directory."""
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes and path.stat().st_size > 0
    )


def first_existing(root: Path, relative_paths: list[str]) -> Path | None:
    """Return the first existing non-empty file from candidate relative paths."""
    for rel in relative_paths:
        path = root / rel
        if nonempty_file(path):
            return path
    return None


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def contains_all(text: str, markers: tuple[str, ...]) -> bool:
    return all(marker in text for marker in markers)


def add_file_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    path: Path | None,
    status_if_missing: str = "BLOCKING",
) -> bool:
    ok = path is not None and nonempty_file(path)
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        str(path) if ok else "缺失或为空",
    ))
    return ok


def add_marker_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    path: Path,
    markers: tuple[str, ...],
    mode: str = "any",
    status_if_missing: str = "BLOCKING",
) -> bool:
    text = read_text(path)
    ok = contains_all(text, markers) if mode == "all" else contains_any(text, markers)
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        str(path) if ok else f"缺少关键字段/标记: {', '.join(markers)}",
    ))
    return ok


def add_required_fields_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    path: Path | None,
    required_fields: dict[str, tuple[str, ...]],
    status_if_missing: str = "BLOCKING",
) -> bool:
    """Check that a text artifact contains every required logical field.

    Each logical field can define multiple marker aliases; at least one alias
    must be present.
    """
    if path is None or not nonempty_file(path):
        checks.append((
            len(checks) + 1,
            label,
            status_if_missing,
            "缺失或为空",
        ))
        return False

    text = read_text(path)
    missing = [
        field for field, markers in required_fields.items()
        if not contains_any(text, markers)
    ]
    ok = not missing
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        str(path) if ok else f"缺少字段: {', '.join(missing)}",
    ))
    return ok


def contains_any_ci(text: str, markers: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


def missing_logical_fields(text: str, required_fields: dict[str, tuple[str, ...]]) -> list[str]:
    return [
        field for field, markers in required_fields.items()
        if not contains_any_ci(text, markers)
    ]


def extract_confirmed_scenario_blocks(text: str) -> list[tuple[str, str]]:
    """Split confirmed-scenarios text into scenario-sized blocks.

    The artifact is markdown-first, but generated variants may be YAML-like.
    Prefer explicit scenario_id lines, then scenario headings, and finally a
    single document block only when scenario-like fields are present.
    """
    id_matches = list(re.finditer(
        r"(?im)^\s*(?:-\s*)?(?:scenario_id|scenario-id|场景编号)\s*[:：]\s*(.+?)\s*$",
        text,
    ))
    if id_matches:
        blocks: list[tuple[str, str]] = []
        for index, match in enumerate(id_matches):
            end = id_matches[index + 1].start() if index + 1 < len(id_matches) else len(text)
            label = match.group(1).strip().strip("`'\"") or f"scenario-{index + 1}"
            blocks.append((label, text[match.start():end]))
        return blocks

    heading_matches = [
        match for match in re.finditer(r"(?im)^#{2,6}\s+(.+?)\s*$", text)
        if re.search(
            r"(SCN[-_\w]*|Scenario\s*\d+|场景\s*[A-Za-z0-9一二三四五六七八九十]+|\bS\d+\b)",
            match.group(1),
            re.I,
        )
    ]
    if heading_matches:
        blocks = []
        for index, match in enumerate(heading_matches):
            end = heading_matches[index + 1].start() if index + 1 < len(heading_matches) else len(text)
            label = match.group(1).strip() or f"scenario-{index + 1}"
            blocks.append((label, text[match.start():end]))
        return blocks

    if contains_any_ci(text, SCENARIO_BLOCK_MARKERS):
        return [("document", text)]
    return []


def abnormal_path_has_explicit_na_reason(block: str) -> bool:
    return (
        contains_any_ci(block, ABNORMAL_PATH_NA_MARKERS)
        and contains_any_ci(block, ABNORMAL_PATH_NA_REASON_MARKERS)
    )


def extract_yaml_like_section(block: str, key_aliases: tuple[str, ...]) -> str:
    """Extract a markdown/YAML section body by key alias."""
    lines = block.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        is_heading = stripped.startswith("#")
        matched = False
        for alias in key_aliases:
            alias_re = re.escape(alias)
            if re.match(rf"(?i)^\s*{alias_re}\s*[:：]\s*(.*)$", line):
                matched = True
                break
            if is_heading and alias.casefold() in stripped.casefold():
                matched = True
                break
        if not matched:
            continue

        base_indent = len(line) - len(line.lstrip())
        section_lines = [line]
        for current in lines[index + 1:]:
            current_stripped = current.strip()
            if not current_stripped:
                section_lines.append(current)
                continue
            current_indent = len(current) - len(current.lstrip())
            if current_stripped.startswith("#") and is_heading:
                break
            if (
                current_indent <= base_indent
                and re.match(r"[\w.-]+\s*[:：]\s*", current_stripped)
                and not current_stripped.startswith("-")
            ):
                break
            section_lines.append(current)
        return "\n".join(section_lines)
    return ""


def split_yaml_list_items(section: str) -> list[str]:
    """Split a YAML-like list section into list item blocks."""
    lines = section.splitlines()
    item_starts = [
        index for index, line in enumerate(lines)
        if re.match(r"^\s*-\s+\S", line)
    ]
    if not item_starts:
        return []

    items: list[str] = []
    for position, start in enumerate(item_starts):
        end = item_starts[position + 1] if position + 1 < len(item_starts) else len(lines)
        items.append("\n".join(lines[start:end]))
    return items


def extract_step_atomic_refs(item: str) -> set[str]:
    refs: set[str] = set()
    for key in ("action_source_ref", "action_source_refs", "op_id", "atomic_op"):
        refs.update(extract_key_values(item, key))
    return {
        ref for ref in refs
        if ref not in {"action_source_ref", "action_source_refs", "op_id", "atomic_op"}
    }


def extract_explicit_key_values(text: str, key: str) -> set[str]:
    """Extract values from explicit YAML-like key lines or two-column field tables."""
    values: set[str] = set()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("|"):
            continue
        if not re.search(rf"\b{re.escape(key)}\b\s*[:：]", stripped):
            continue
        base_indent = len(line) - len(line.lstrip())
        after_key = stripped.split(":", 1)[1] if ":" in stripped else stripped.split("：", 1)[1]
        values.update(REF_TOKEN_RE.findall(after_key))

        cursor = index + 1
        while cursor < len(lines):
            current = lines[cursor]
            current_stripped = current.strip()
            if not current_stripped:
                cursor += 1
                continue
            if current_stripped.startswith("|"):
                break
            indent = len(current) - len(current.lstrip())
            if indent <= base_indent and re.match(r"[A-Za-z_][\w-]*\s*[:：]", current_stripped):
                break
            if current_stripped.startswith("-") or indent > base_indent:
                values.update(REF_TOKEN_RE.findall(current_stripped))
                cursor += 1
                continue
            break
    return {
        value for value in values
        if value not in {"action_source_refs", "action_source_ref", "op_id", "atomic_op"}
    }


def extract_explicit_field_table_values(text: str, key: str) -> set[str]:
    values: set[str] = set()
    for _line_no, header, rows in iter_markdown_tables(text):
        normalized_header = [normalize_table_cell(cell) for cell in header]
        if len(normalized_header) < 2:
            continue
        if normalized_header[0] not in {"字段", "field", "key"}:
            continue
        if normalized_header[1] not in {"值", "value"}:
            continue
        for _row_no, cells in rows:
            if len(cells) < 2:
                continue
            if normalize_table_cell(cells[0]).casefold() == key.casefold():
                values.update(extract_atomic_refs_from_cell(cells[1]))
    return values


def extract_explicit_scenario_refs(text: str) -> set[str]:
    refs = extract_explicit_key_values(text, "action_source_refs")
    refs.update(extract_explicit_key_values(text, "action_source_ref"))
    refs.update(extract_explicit_field_table_values(text, "action_source_refs"))
    refs.update(extract_explicit_field_table_values(text, "action_source_ref"))
    return refs


def extract_atomic_refs_from_cell(cell: str) -> set[str]:
    normalized = re.sub(r"<br\s*/?>", " ", cell, flags=re.I)
    refs = {
        token.strip("`\"'")
        for token in REF_TOKEN_RE.findall(normalized)
        if token not in {
            "action_source_refs",
            "action_source_ref",
            "atomic_op",
            "op_id",
            "source_type",
        }
    }
    return refs


def validate_markdown_path_table_refs(
    scenario_label: str,
    path_name: str,
    section: str,
    scenario_action_refs: set[str],
) -> list[str] | None:
    tables = iter_markdown_tables(section)
    path_tables: list[tuple[list[str], list[tuple[int, list[str]]], int]] = []
    for _line_no, header, rows in tables:
        normalized_header = [normalize_table_cell(cell).casefold() for cell in header]
        action_indexes = [
            index for index, cell in enumerate(normalized_header)
            if (
                "action_source" in cell
                or "atomic_op" in cell
                or "op_id" in cell
                or "原子操作" in cell
            )
        ]
        if action_indexes:
            path_tables.append((header, rows, action_indexes[0]))

    if not path_tables:
        return None

    errors: list[str] = []
    for header, rows, action_index in path_tables:
        normalized_header = [normalize_table_cell(cell) for cell in header]
        label_index = 0
        for candidate in ("step_id", "步骤", "abnormal_item", "异常项", "#"):
            if candidate in normalized_header:
                label_index = normalized_header.index(candidate)
                break
        if not rows:
            errors.append(f"{scenario_label}: {path_name} Markdown 表格无数据行")
            continue
        for _line_no, cells in rows:
            label = cells[label_index].strip() if label_index < len(cells) else "item"
            action_cell = cells[action_index] if action_index < len(cells) else ""
            refs = extract_atomic_refs_from_cell(action_cell)
            if not refs:
                errors.append(f"{scenario_label}: {path_name}.{label} 缺少原子操作引用")
            elif scenario_action_refs:
                missing = sorted(ref for ref in refs if ref not in scenario_action_refs)
                if missing:
                    errors.append(
                        f"{scenario_label}: {path_name}.{label} 原子操作未回链 action_source_refs: "
                        + ", ".join(missing)
                    )
    return errors


def validate_path_step_atomic_refs(
    scenario_label: str,
    path_name: str,
    section: str,
    scenario_action_refs: set[str],
) -> list[str]:
    errors: list[str] = []
    if not section:
        return errors

    markdown_errors = validate_markdown_path_table_refs(
        scenario_label,
        path_name,
        section,
        scenario_action_refs,
    )
    if markdown_errors is not None:
        return markdown_errors

    items = split_yaml_list_items(section)
    if not items:
        refs = extract_step_atomic_refs(section)
        if not refs:
            errors.append(f"{scenario_label}: {path_name} 未发现步骤级原子操作引用")
        return errors

    for index, item in enumerate(items, start=1):
        label = "item"
        step_id_match = re.search(r"\b(?:step_id|abnormal_item)\s*[:：]\s*([^\s,\]]+)", item)
        if step_id_match:
            label = step_id_match.group(1).strip("`'\"")
        refs = extract_step_atomic_refs(item)
        if not refs:
            errors.append(f"{scenario_label}: {path_name}.{label} 缺少原子操作引用")
        elif scenario_action_refs:
            missing = sorted(ref for ref in refs if ref not in scenario_action_refs)
            if missing:
                errors.append(
                    f"{scenario_label}: {path_name}.{label} 原子操作未回链 action_source_refs: "
                    + ", ".join(missing)
                )
    return errors


def validate_confirmed_scenarios_contract(text: str) -> list[str]:
    """Validate the per-scenario scenario-chain contract for GATE-2."""
    blocks = extract_confirmed_scenario_blocks(text)
    if not blocks:
        return ["未发现可解析的场景块: 缺少 scenario_id/场景编号 或场景标题"]

    errors: list[str] = []
    for index, (label, block) in enumerate(blocks, start=1):
        scenario_label = label or f"scenario-{index}"
        scenario_action_refs = extract_explicit_scenario_refs(block)
        if not contains_any_ci(block, ("normal_path", "正常路径")):
            errors.append(f"{scenario_label}: 缺少 normal_path/正常路径")
        else:
            normal_section = extract_yaml_like_section(block, ("normal_path", "正常路径"))
            missing_normal = missing_logical_fields(normal_section, NORMAL_PATH_REQUIRED_FIELDS)
            if missing_normal:
                errors.append(
                    f"{scenario_label}: normal_path 缺少字段 {', '.join(missing_normal)}"
                )
            if not contains_any(block, NORMAL_PATH_NECESSITY_VALUES):
                errors.append(
                    f"{scenario_label}: normal_path.necessity 缺少合法取值 "
                    "必要/可选/至少选择一项"
                )
            errors.extend(validate_path_step_atomic_refs(
                scenario_label,
                "normal_path",
                normal_section,
                scenario_action_refs,
            ))

        if not contains_any_ci(block, ("abnormal_path", "异常路径")):
            errors.append(f"{scenario_label}: 缺少 abnormal_path/异常路径")
        elif not abnormal_path_has_explicit_na_reason(block):
            abnormal_section = extract_yaml_like_section(block, ("abnormal_path", "异常路径"))
            missing_abnormal = missing_logical_fields(abnormal_section, ABNORMAL_PATH_REQUIRED_FIELDS)
            if missing_abnormal:
                errors.append(
                    f"{scenario_label}: abnormal_path 缺少字段 {', '.join(missing_abnormal)}"
                )
            errors.extend(validate_path_step_atomic_refs(
                scenario_label,
                "abnormal_path",
                abnormal_section,
                scenario_action_refs,
            ))

        if not contains_any_ci(block, ("minimal_logic_chain", "最小逻辑链")):
            errors.append(f"{scenario_label}: 缺少 minimal_logic_chain/最小逻辑链")
        if not contains_any_ci(block, ("atomic_operations", "ptm-atomic", "op_id", "原子操作")):
            errors.append(f"{scenario_label}: 缺少 atomic_operations/op_id")
        if not scenario_action_refs:
            errors.append(f"{scenario_label}: 缺少场景级 action_source_refs")
    return errors


def add_confirmed_scenarios_contract_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    path: Path | None,
    status_if_missing: str = "BLOCKING",
) -> bool:
    if path is None or not nonempty_file(path):
        checks.append((
            len(checks) + 1,
            label,
            status_if_missing,
            "缺失或为空",
        ))
        return False

    errors = validate_confirmed_scenarios_contract(read_text(path))
    ok = not errors
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        str(path) if ok else "；".join(errors[:6]),
    ))
    return ok


def collect_marker_lines(path: Path | None, markers: tuple[str, ...], limit: int = 12) -> list[str]:
    if path is None or not nonempty_file(path):
        return []
    hits: list[str] = []
    for line in read_text(path).splitlines():
        if contains_any_ci(line, markers):
            stripped = line.strip()
            if stripped:
                hits.append(stripped)
        if len(hits) >= limit:
            break
    return hits


def render_new_atomic_confirmation_section(path: Path | None) -> tuple[str, list[tuple[int, str]]]:
    hits = collect_marker_lines(path, NEW_ATOMIC_CANDIDATE_MARKERS)
    if not hits:
        return "", []

    rows = "\n".join(
        f"| {idx} | `{path}` | `{line}` | 需用户确认是否新增 / 合并 / 拒绝 |"
        for idx, line in enumerate(hits, start=1)
    )
    section = (
        "## GATE-2 新增原子操作候选确认\n\n"
        "检测到场景阶段提出新增或候选原子操作。发起 GATE-2 人工确认时必须显式展示，"
        "用户需确认每项是新增、改为复用已有 ptm-atomic、转 Tool Draft，还是拒绝。\n\n"
        "| # | 来源 | 候选线索 | 人工处理要求 |\n"
        "|---|---|---|---|\n"
        f"{rows}\n\n"
    )
    manual_items = [
        (
            2,
            f"新增/候选原子操作需显式确认（共发现 {len(hits)} 条线索，来源 `{path}`）：逐项确认新增、复用、转 Tool Draft 或拒绝",
        )
    ]
    return section, manual_items


def candidate_source_has_items(path: Path | None) -> bool:
    if path is None or not nonempty_file(path):
        return False
    text = read_text(path)
    stripped = re.sub(r"\s+", "", text)
    if not stripped or stripped in {"[]", "{}", "null", "None"}:
        return False
    return contains_any_ci(text, CANDIDATE_ITEM_MARKERS)


def candidate_confirmation_is_recorded(path: Path | None) -> bool:
    if path is None or not nonempty_file(path):
        return False
    text = read_text(path)
    return candidate_confirmation_status(path)[0]


def candidate_confirmation_status(path: Path | None) -> tuple[bool, str]:
    """Return whether a candidate summary contains final user decisions.

    A summary that only contains a `decision` column with pending states is a
    valid aggregation artifact, but it is not a GATE-3 confirmation.
    """
    if path is None or not nonempty_file(path):
        return False, "缺失或为空"
    text = read_text(path)
    has_final = contains_any_ci(text, FINAL_CANDIDATE_DECISION_MARKERS)
    has_pending = contains_any_ci(text, PENDING_CANDIDATE_DECISION_MARKERS)
    if has_final:
        return True, "已记录最终用户确认结果"
    if has_pending or contains_any_ci(text, ("decision", "确认", "候选")):
        return False, "仅记录候选汇总或 pending-review，缺少 confirmed/rejected/modified"
    return False, "缺少 decision=confirmed/rejected/modified 或等价确认结果"


def add_candidate_confirmation_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    candidate_sources: list[Path | None],
    summary_candidates: list[Path | None],
    status_if_missing: str = "BLOCKING",
) -> bool:
    active_sources = [path for path in candidate_sources if candidate_source_has_items(path)]
    summaries = [path for path in summary_candidates if path is not None and nonempty_file(path)]
    if not active_sources:
        checks.append((
            len(checks) + 1,
            label,
            "PASS",
            "未发现候选来源；人工 Gate 可确认 N/A",
        ))
        return True

    confirmed_summaries = [path for path in summaries if candidate_confirmation_is_recorded(path)]
    ok = bool(confirmed_summaries)
    summary_statuses = [
        f"{path}: {candidate_confirmation_status(path)[1]}"
        for path in summaries
    ]
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        (
            "候选来源: " + ", ".join(str(path) for path in active_sources)
            + "；确认汇总: " + ", ".join(str(path) for path in confirmed_summaries)
        ) if ok else (
            "发现候选来源但缺少最终确认汇总（缺少带 decision/确认结果的候选汇总）: "
            + ", ".join(str(path) for path in active_sources)
            + ("；已发现汇总状态: " + "；".join(summary_statuses) if summary_statuses else "")
        ),
    ))
    return ok


def render_candidate_confirmation_section(
    title: str,
    candidate_sources: list[Path | None],
    summary_candidates: list[Path | None],
) -> str:
    active_sources = [path for path in candidate_sources if candidate_source_has_items(path)]
    summaries = [path for path in summary_candidates if path is not None and nonempty_file(path)]
    if not active_sources and not summaries:
        return ""
    rows = []
    for path in active_sources:
        rows.append(f"| candidate-source | `{path}` | 需在候选汇总中逐项给出 decision |")
    for path in summaries:
        _ok, status = candidate_confirmation_status(path)
        rows.append(f"| confirmation-summary | `{path}` | {status} |")
    return (
        f"## {title}\n\n"
        "| 类型 | 路径 | 状态 |\n"
        "|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n"
    )


def split_markdown_row(line: str) -> list[str]:
    """Split a Markdown table row on unescaped pipes."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []

    body = stripped[1:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    cells.append("".join(current).strip())
    return cells


def is_separator_cells(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def normalize_table_cell(cell: str) -> str:
    return re.sub(r"\s+", "", cell.strip().strip("`"))


def is_standard_pc_header(cells: list[str]) -> bool:
    return tuple(normalize_table_cell(cell) for cell in cells) == STANDARD_PC_COLUMNS


def iter_markdown_tables(text: str) -> list[tuple[int, list[str], list[tuple[int, list[str]]]]]:
    """Return Markdown tables as (header line no, header cells, data rows)."""
    lines = text.splitlines()
    tables: list[tuple[int, list[str], list[tuple[int, list[str]]]]] = []
    index = 0
    while index < len(lines) - 1:
        header = split_markdown_row(lines[index])
        separator = split_markdown_row(lines[index + 1])
        if header and len(header) == len(separator) and is_separator_cells(separator):
            rows: list[tuple[int, list[str]]] = []
            cursor = index + 2
            while cursor < len(lines):
                cells = split_markdown_row(lines[cursor])
                if not cells:
                    break
                if not is_separator_cells(cells):
                    rows.append((cursor + 1, cells))
                cursor += 1
            tables.append((index + 1, header, rows))
            index = cursor
        else:
            index += 1
    return tables


def validate_standard_pc_tables(
    text: str,
    *,
    require_step_atomic: bool,
    require_single_table: bool = False,
) -> list[str]:
    """Validate exact 16-column PC tables and optional step atomic-op rendering."""
    standard_tables = [
        table for table in iter_markdown_tables(text)
        if is_standard_pc_header(table[1])
    ]
    errors: list[str] = []
    if not standard_tables:
        return ["未发现标准 16 列 PC 表头"]
    if require_single_table and len(standard_tables) != 1:
        errors.append(f"标准 PC 汇总表数量应为 1，实际为 {len(standard_tables)}")

    for header_line, _header, rows in standard_tables:
        if not rows:
            errors.append(f"第 {header_line} 行标准 PC 表没有数据行")
            continue
        for line_no, cells in rows:
            if len(cells) != len(STANDARD_PC_COLUMNS):
                errors.append(
                    f"第 {line_no} 行列数为 {len(cells)}，应为 {len(STANDARD_PC_COLUMNS)}"
                )
                continue
            steps = cells[TEST_STEPS_COLUMN]
            if require_step_atomic and "原子操作：" not in steps and "原子操作:" not in steps:
                errors.append(f"第 {line_no} 行测试步骤缺少 原子操作：<op_id>")
    return errors


def add_pc_table_contract_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    files: list[Path],
    *,
    require_step_atomic: bool,
    require_single_table: bool = False,
    status_if_missing: str = "BLOCKING",
) -> bool:
    """Check every artifact for exact PC table shape and step rendering."""
    if not files:
        checks.append((
            len(checks) + 1,
            label,
            status_if_missing,
            "无可检查文件",
        ))
        return False
    failures: list[str] = []
    for path in files:
        errors = validate_standard_pc_tables(
            read_text(path),
            require_step_atomic=require_step_atomic,
            require_single_table=require_single_table,
        )
        if errors:
            failures.append(f"{path}: {'; '.join(errors[:3])}")
    ok = not failures
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        f"已检查 {len(files)} 个文件" if ok else "；".join(failures[:5]),
    ))
    return ok


def extract_key_values(text: str, key: str) -> set[str]:
    """Extract simple YAML/Markdown scalar or list values following a key."""
    values: set[str] = set()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not re.search(rf"\b{re.escape(key)}\b", line):
            continue

        base_indent = len(line) - len(line.lstrip())
        after_key = line.split(key, 1)[1]
        if ":" in after_key:
            after_key = after_key.split(":", 1)[1]
        values.update(REF_TOKEN_RE.findall(after_key))

        cursor = index + 1
        while cursor < len(lines):
            current = lines[cursor]
            stripped = current.strip()
            if not stripped:
                cursor += 1
                continue
            indent = len(current) - len(current.lstrip())
            if indent <= base_indent and re.match(r"[A-Za-z_][\w-]*\s*:", stripped):
                break
            if stripped.startswith("-") or indent > base_indent:
                values.update(REF_TOKEN_RE.findall(stripped))
                cursor += 1
                continue
            break
    return values


def extract_op_ids(text: str) -> list[str]:
    return [
        match.group(1).strip("`\"'")
        for match in re.finditer(r"\bop_id\s*:\s*[`\"']?([A-Za-z][A-Za-z0-9_.:-]*)", text)
    ]


def validate_pc_step_contract(text: str) -> list[str]:
    errors: list[str] = []
    if "case_steps" not in text:
        errors.append("缺少 case_steps 结构化步骤清单")
    step_names = re.findall(r"\bstep_name\s*:", text)
    if not step_names:
        errors.append("缺少 case_steps[].step_name")
    if "atomic_op" not in text:
        errors.append("缺少 case_steps[].atomic_op")

    op_ids = extract_op_ids(text)
    if not op_ids:
        errors.append("缺少 case_steps[].atomic_op.op_id")
    elif step_names and len(step_names) != len(op_ids):
        errors.append(f"step_name 数量({len(step_names)})与 op_id 数量({len(op_ids)})不一致")

    action_refs = extract_key_values(text, "action_source_refs")
    if not action_refs:
        errors.append("缺少 action_source_refs")
    else:
        missing_refs = [op_id for op_id in op_ids if op_id not in action_refs]
        if missing_refs:
            errors.append(
                "atomic_op.op_id 未回链 action_source_refs: " + ", ".join(sorted(set(missing_refs)))
            )
    return errors


def add_pc_step_contract_check(
    checks: list[tuple[int, str, str, str]],
    label: str,
    files: list[Path],
    status_if_missing: str = "BLOCKING",
) -> bool:
    if not files:
        checks.append((
            len(checks) + 1,
            label,
            status_if_missing,
            "无可检查文件",
        ))
        return False
    failures: list[str] = []
    for path in files:
        errors = validate_pc_step_contract(read_text(path))
        if errors:
            failures.append(f"{path}: {'; '.join(errors[:4])}")
    ok = not failures
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        f"已检查 {len(files)} 个文件" if ok else "；".join(failures[:5]),
    ))
    return ok


def result_file_passed(path: Path) -> bool:
    """Check whether a prior Gate result explicitly records PASS."""
    return nonempty_file(path) and bool(re.search(r"结论[：:]\s*`?PASS`?", read_text(path)))


def yaml_scalar(value: str) -> str:
    """Render a scalar using JSON quoting, which is valid YAML."""
    import json

    return json.dumps(value or "", ensure_ascii=False)


def parse_yaml_scalar(value: str) -> str:
    """Parse the limited scalar form written by yaml_scalar."""
    import json

    value = value.strip()
    if not value:
        return ""
    try:
        parsed = json.loads(value)
        return str(parsed)
    except json.JSONDecodeError:
        return value.strip('"').strip("'")


def parse_skill_calls(path: Path) -> list[dict[str, object]]:
    """Parse the append-only SKILL-CALLS.yaml subset written by this script."""
    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_list_key = ""
    for raw in read_text(path).splitlines():
        stripped = raw.strip()
        if not stripped or stripped == "calls:":
            continue
        if stripped.startswith("- call_id:"):
            if current:
                records.append(current)
            current = {"call_id": parse_yaml_scalar(stripped.split(":", 1)[1])}
            current_list_key = ""
            continue
        if current is None:
            continue
        if stripped in ("input_refs:", "output_refs:"):
            current_list_key = stripped[:-1]
            current.setdefault(current_list_key, [])
            continue
        if stripped.startswith("- ") and current_list_key:
            values = current.setdefault(current_list_key, [])
            if isinstance(values, list):
                values.append(parse_yaml_scalar(stripped[2:]))
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_yaml_scalar(value)
            current_list_key = ""
    if current:
        records.append(current)
    return records


def render_skill_calls(records: list[dict[str, object]]) -> str:
    """Render SKILL-CALLS.yaml in a stable append-only schema."""
    lines = ["calls:"]
    for record in records:
        lines.append(f"  - call_id: {yaml_scalar(str(record.get('call_id', '')))}")
        for key in ("skill_name", "phase", "caller", "platform", "started_at", "completed_at", "status", "evidence_summary"):
            lines.append(f"    {key}: {yaml_scalar(str(record.get(key, '')))}")
        for key in ("input_refs", "output_refs"):
            lines.append(f"    {key}:")
            values = record.get(key, [])
            if isinstance(values, list) and values:
                for value in values:
                    lines.append(f"      - {yaml_scalar(str(value))}")
            else:
                lines.append('      - ""')
    return "\n".join(lines).rstrip() + "\n"


def write_skill_call(args: argparse.Namespace) -> int:
    """Append one structured Skill execution record."""
    project_root, _input_root = resolve_feature_workspace(args)
    execution_dir = project_root / "process" / "execution"
    execution_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = execution_dir / "SKILL-CALLS.yaml"
    records = parse_skill_calls(evidence_path)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    call_id = args.call_id or f"SKILL-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')}-{args.skill_name}"
    record: dict[str, object] = {
        "call_id": call_id,
        "skill_name": args.skill_name,
        "phase": args.phase,
        "caller": args.caller,
        "platform": args.platform,
        "started_at": args.started_at or now,
        "completed_at": args.completed_at or now,
        "status": args.status,
        "input_refs": args.input_ref or [],
        "output_refs": args.output_ref or [],
        "evidence_summary": args.evidence_summary,
    }
    records.append(record)
    evidence_path.write_text(render_skill_calls(records), encoding="utf-8")
    print(evidence_path)
    return 0


def add_skill_evidence_check(
    checks: list[tuple[int, str, str, str]],
    project_root: Path,
    label: str,
    required_skills: tuple[str, ...],
    status_if_missing: str = "BLOCKING",
) -> bool:
    """Check process/execution/SKILL-CALLS.yaml for required skill evidence."""
    evidence_path = project_root / "process" / "execution" / "SKILL-CALLS.yaml"
    records = parse_skill_calls(evidence_path)
    completed = {
        str(record.get("skill_name", ""))
        for record in records
        if str(record.get("status", "")).lower() == "completed"
        and record.get("output_refs")
    }
    missing = [skill for skill in required_skills if skill not in completed]
    ok = bool(records) and not missing
    checks.append((
        len(checks) + 1,
        label,
        "PASS" if ok else status_if_missing,
        str(evidence_path) if ok else f"缺少 completed Skill 执行证据或 output_refs: {', '.join(missing) or 'SKILL-CALLS.yaml'}",
    ))
    return ok


def write_skeleton_result(
    checkpoints_dir: Path,
    gate: str,
    overall: str,
    feature_name: str,
    checks: list[tuple[int, str, str, str]],
    pending_items: list[tuple[int, str]] | None = None,
    suffix: str = "",
    extra_sections: str = "",
    check_depth: str = "machine-baseline",
) -> Path:
    """Write a Gate check result Markdown file."""
    path = gate_output_path(checkpoints_dir, gate, suffix)
    name = GATE_NAMES.get(gate, gate)
    rows = "\n".join(
        f"| {idx} | {item} | {status} | {evidence} |"
        for idx, item, status, evidence in checks
    )
    pending_rows = ""
    if pending_items:
        pending_rows = "\n".join(
            f"| {idx} | {item} | MANUAL | 需人工 Gate 确认或风险接受 |"
            for idx, item in pending_items
        )
    content = (
        f"---\n"
        f"check_depth: {check_depth}\n"
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
            f"## 人工确认项\n\n"
            f"以下检查项来自 `docs/ptm-tde/gate-spec.md` §{gate} Checklist，"
            f"当前脚本仅做机器可验证的基线检查；语义质量和人工确认项仍需人工 Gate 处理。\n\n"
            f"| # | 检查项 | 状态 | 说明 |\n"
            f"|---|--------|------|------|\n"
            f"{pending_rows}\n"
        )
    path.write_text(content, encoding="utf-8")
    if pending_items and suffix == "auto":
        write_manual_gate_draft(checkpoints_dir, gate, feature_name, overall, pending_items, path)
    return path


def write_manual_gate_draft(
    checkpoints_dir: Path,
    gate: str,
    feature_name: str,
    auto_status: str,
    manual_items: list[tuple[int, str]],
    auto_path: Path,
) -> Path:
    """Write the independent manual review draft required by Gate spec."""
    path = gate_output_path(checkpoints_dir, gate, "manual")
    name = GATE_NAMES.get(gate, gate)
    rows = "\n".join(
        f"| {idx} | {item} | OPEN | 请人工确认、修改或接受风险 |"
        for idx, item in manual_items
    )
    content = (
        f"---\n"
        f"gate: {gate}\n"
        f"review_type: manual\n"
        f"auto_result: {auto_status}\n"
        f"---\n"
        f"# {gate} {name} Manual Review\n\n"
        f"- 特性名：`{feature_name}`\n"
        f"- 自动检查结果：`{auto_status}`\n"
        f"- 自动检查文件：`{auto_path}`\n"
        f"- 创建时间：`{dt.datetime.now(dt.timezone.utc).isoformat()}`\n\n"
        f"## 人工确认清单\n\n"
        f"| # | 确认项 | 状态 | 处理意见 |\n"
        f"|---|---|---|---|\n"
        f"{rows}\n\n"
        f"## 回复协议\n\n"
        f"请使用以下 exact text 之一回复：\n\n"
        f"- `approve`：接受本 Gate 的自动检查结果和人工确认项。\n"
        f"- `修改: <具体修改点>`：要求按修改点回到对应阶段修正。\n"
        f"- `reject`：拒绝进入下一阶段。\n\n"
        f"## 人工审查结果\n\n"
        f"- reviewer: \n"
        f"- reviewed_at: \n"
        f"- decision: OPEN\n"
        f"- notes: \n"
    )
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Gate handlers
# ---------------------------------------------------------------------------

def run_gate_1(args: argparse.Namespace) -> int:
    """GATE-1 Entry Gate: validate feature project input readiness."""
    project_root, input_root = resolve_feature_workspace(args)
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    requirement = Path(args.requirement).resolve() if args.requirement else None
    requirement_hits = (
        [requirement] if requirement and requirement.exists() else find_files(input_root)
    )
    topo_hits = find_files(input_root, TOPO_MARKERS)
    topo_resource_hits = find_resource_files("network-topology", "*.md")
    coupling_hits = find_files(input_root, COUPLING_MARKERS)
    coupling_resource_hits = find_resource_files("coupling-matrix", "*.yaml")
    ptm_atomic_ok, ptm_atomic_evidence = probe_ptm_atomic()
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
            "本地 .input/ 和显式路径均未找到需求文件；请提供需求文件或 wiki 需求/接口文档。",
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
        3, "ptm-atomic 可用或 wiki 兜底",
        *status_line(
            bool(ptm_atomic_ok or args.wiki_index),
            ptm_atomic_evidence if ptm_atomic_ok else wiki_note,
            "全局命令 ptm-atomic 不可用，且未提供 wiki 兜底信息。",
        ),
    ))
    topo_all = topo_hits + topo_resource_hits
    topo_evidence = ", ".join(str(p) for p in topo_all) or wiki_note
    checks.append((
        4, "防火墙 topo 可用或 wiki 兜底",
        *status_line(
            bool(topo_all or args.wiki_index), topo_evidence,
            "本地 .input/ 和 resource/network-topology/ 均未找到 topo，wiki 也未提供；请补充防火墙 topo 文件或 wiki 文档。",
        ),
    ))

    coupling_all = coupling_hits + coupling_resource_hits
    coupling_evidence = ", ".join(str(p) for p in coupling_all) or wiki_note
    checks.append((
        5, "耦合矩阵与特性树可用或 wiki 兜底",
        *status_line(
            bool(coupling_all or args.wiki_index),
            coupling_evidence,
            "本地 .input/ 和 resource/coupling-matrix/ 均未找到耦合矩阵或特性树，wiki 也未提供。两者至少一个存在即通过；缺失方将在后续步骤中由模型推理补充。",
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

    # 8: KYM 产物目录就绪
    kym_mission_dir = project_root / "kym" / "mission-understanding"
    kym_mission_ok = kym_mission_dir.is_dir()
    checks.append((
        8, "KYM 产物目录就绪",
        *status_line(
            kym_mission_ok,
            "kym/mission-understanding/ 已就绪" if kym_mission_ok else "kym/mission-understanding/ 不存在",
            "无法创建 kym/mission-understanding/（权限不足或路径被普通文件占用）",
        ),
    ))

    # 9: mission-statement 模板可访问（骨架检查：kym skill 目录存在即视为可访问）
    kym_skill_dir = Path(__file__).resolve().parent.parent.parent / "kym"
    mission_tmpl_ok = kym_skill_dir.is_dir()
    checks.append((
        9, "mission-statement 模板可访问",
        *status_line(
            mission_tmpl_ok,
            "kym skill 目录存在" if mission_tmpl_ok else "kym skill 目录不存在",
            "kym skill 模板不可访问，无法正常运行 KYM 阶段",
        ),
    ))

    # 10: 组网图资源可用
    topo_resource_ok = len(topo_resource_hits) > 0
    topo_resource_evidence = ", ".join(str(p) for p in topo_resource_hits) if topo_resource_hits else "WARNING: resource/network-topology/ 无可用文件"
    checks.append((
        10, "组网图资源可用",
        "PASS" if topo_resource_ok else "WARN",
        topo_resource_evidence,
    ))

    # 11: 公共因子库内容完整性 — 检查 index.yaml 中每个因子库的实际文件是否存在
    factor_content_ok, factor_content_evidence, factor_content_missing = probe_factor_library_content()
    checks.append((
        11, "公共因子库内容完整",
        "PASS" if factor_content_ok else "WARN",
        factor_content_evidence,
    ))

    # 12: 耦合矩阵内容完整性 — 检查 index.yaml 中每个矩阵的 source/feature_tree 文件是否存在
    coupling_content_ok, coupling_content_evidence = probe_coupling_matrix_content()
    checks.append((
        12, "耦合矩阵内容完整",
        "PASS" if coupling_content_ok else "WARN",
        coupling_content_evidence,
    ))

    overall = "PASS" if all(status in ("PASS", "WARN") for _, _, status, _ in checks) else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-1", overall, feature_name, checks,
    )
    write_state(project_root, feature_name, "GATE-1", overall, current_step="feature-parser", input_root=input_root)
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_2(args: argparse.Namespace) -> int:
    """GATE-2 KYM Exit Gate: machine-baseline check for KYM phase completion."""
    project_root, input_root = resolve_feature_workspace(args)
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

    directory_structure = first_existing(project_root, ["kym/feature-input/directory-structure.md"])
    scenarios_md = first_existing(project_root, ["kym/scenarios/confirmed-scenarios.md"])
    add_file_check(checks, "目录结构可读", directory_structure)
    add_file_check(checks, "确认场景产物存在", scenarios_md)
    if scenarios_md is not None:
        add_required_fields_check(
            checks,
            "GATE-2 字段级: 场景结构可消费",
            scenarios_md,
            {
                "input_document_classification": ("input_document_classification", "document_classification", "输入文档类型"),
                "normal_path": ("normal_path", "正常路径"),
                "abnormal_path": ("abnormal_path", "异常路径"),
                "action_source_refs": ("action_source_ref", "action_source_refs", "ptm-atomic", "op_id"),
                "confirmation_gaps": ("confirmation_gaps", "待澄清", "resolved", "accepted_as_risk"),
                "minimal_logic_chain": ("minimal_logic_chain", "最小逻辑链"),
            },
        )
        add_confirmed_scenarios_contract_check(
            checks,
            "GATE-2 字段级: confirmed-scenarios 正常/异常链完整",
            scenarios_md,
        )
        add_marker_check(
            checks,
            "Topology Catalog",
            scenarios_md,
            ("topology_ref", "topology_refs", "topology", "拓扑"),
            status_if_missing="WARN",
        )
    add_skill_evidence_check(
        checks,
        project_root,
        "KYM Skill 调用证据完整",
        ("feature-parser", "kym", "scenario-discovery"),
    )

    # N1-N4: KYM mission understanding checks
    mission_md = project_root / "kym" / "mission-understanding" / "mission-statement.md"
    n1_ok = mission_md.is_file() and mission_md.stat().st_size > 0
    checks.append((
        len(checks) + 1, "N1: 使命文档存在",
        "PASS" if n1_ok else "BLOCKING",
        str(mission_md) if n1_ok else f"缺失: {mission_md}",
    ))

    mission_text = read_text(mission_md) if n1_ok else ""
    dimension_markers = (
        "Customers", "Information", "Developers", "Equipment",
        "Schedule", "Test Items", "Deliverables", "Risks",
        "客户", "信息", "开发", "设备", "排期", "测试项", "交付", "风险",
    )
    dimensions_seen = sum(1 for marker in dimension_markers if marker in mission_text)
    checks.append((
        len(checks) + 1, "N2: 启发式探索已执行",
        "PASS" if dimensions_seen >= 2 else "BLOCKING",
        f"识别到 {dimensions_seen} 个 CIDTESTD 维度标记" if n1_ok else "N1 未通过，跳过",
    ))
    checks.append((
        len(checks) + 1, "N3: 范围边界已界定",
        "PASS" if contains_any(mission_text, ("scope", "dont_test", "测试范围", "不测试", "排除")) else "BLOCKING",
        str(mission_md) if n1_ok else "N1 未通过，跳过",
    ))
    checks.append((
        len(checks) + 1, "N4: 待澄清问题已收集",
        "PASS" if contains_any(mission_text, ("confirmation_gaps", "待澄清", "已解决", "resolved", "accepted_as_risk")) else "WARN",
        "未发现待澄清问题记录；若确无缺口可人工确认 N/A" if n1_ok else "N1 未通过，跳过",
    ))

    extra_sections = ""
    manual_items = [
        (1, "KYM 场景、目录结构、Topology、Operation Path（含正常/异常链逐步骤原子操作）和使命声明仍需人工确认"),
    ]
    new_atomic_section, new_atomic_manual_items = render_new_atomic_confirmation_section(scenarios_md)
    extra_sections += new_atomic_section
    manual_items.extend(new_atomic_manual_items)

    overall = "PASS" if all(status not in ("BLOCKING", "MISSING") for _, _, status, _ in checks) else "BLOCKED"
    # GATE-2 is auto + manual: output -auto.md first
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-2", overall, feature_name, checks,
        pending_items=manual_items, suffix="auto",
        extra_sections=extra_sections,
    )
    write_state(project_root, feature_name, "GATE-2", overall, current_step="scenario-discovery", input_root=input_root)
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_3(args: argparse.Namespace) -> int:
    """GATE-3 MFQ Exit Gate: machine-baseline check for MFQ phase completion."""
    project_root, input_root = resolve_feature_workspace(args)
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
    for label, dirpath in mfq_dirs.items():
        ok = dirpath.is_dir()
        checks.append((
            len(checks) + 1, f"Entry Criteria: {label}",
            "PASS" if ok else "BLOCKING",
            f"目录存在" if ok else f"目录不存在: {dirpath}",
        ))

    m_test_points = first_existing(project_root, ["mfq/m-analysis/test-points.md"])
    f_test_points = first_existing(project_root, ["mfq/f-analysis/coupling-test-points.md"])
    q_test_points = first_existing(project_root, ["mfq/q-analysis/quality-test-points.md"])
    logic_cases = first_existing(project_root, ["mfq/integration/logic-cases.md"])
    all_test_points = first_existing(project_root, ["mfq/integration/all-test-points.md"])
    test_data = first_existing(project_root, ["mfq/integration/test-data.md"])
    design_plan = first_existing(project_root, ["process/plan/design-plan.md", "mfq/integration/design-plan.md"])
    design_reasoning = first_existing(project_root, ["process/plan/design-planner-reasoning.md"])
    factor_lock = first_existing(project_root, ["mfq/factor-usage/factor-library-lock.yaml"])
    factor_report = first_existing(project_root, ["mfq/m-analysis/factor-resolution-report.md"])
    factor_candidates = first_existing(project_root, ["mfq/m-analysis/candidate-factor-proposals.yaml"])
    atomic_candidates = first_existing(project_root, ["mfq/m-analysis/candidate-ptm-atomic.yaml"])
    factor_candidate_summary = first_existing(project_root, [
        "mfq/candidates/factor-candidates.md",
        "mfq/candidates/test-factor-candidates.md",
    ])
    atomic_candidate_summary = first_existing(project_root, [
        "mfq/candidates/ptm-atomic-candidates.md",
        "mfq/candidates/atomic-op-candidates.md",
    ])

    add_file_check(checks, "M1: M 分析输出完整", m_test_points)
    add_file_check(checks, "M2: F 分析输出完整", f_test_points)
    add_file_check(checks, "M3: Q 分析输出完整", q_test_points)
    add_file_check(checks, "M4: 全量测试点整合存在", all_test_points)
    add_file_check(checks, "M4: 逻辑用例整合存在", logic_cases)
    add_file_check(checks, "M4: 测试数据整合存在", test_data, status_if_missing="WARN")
    add_file_check(checks, "M6: 设计计划存在", design_plan)
    add_file_check(checks, "M6: 设计推理存在", design_reasoning)
    add_file_check(checks, "M7: 公共因子库 lock 有效", factor_lock)
    add_file_check(checks, "M8: 因子库扫描报告存在", factor_report)
    add_file_check(checks, "M9: 原子操作候选匹配存在", atomic_candidates, status_if_missing="WARN")
    add_candidate_confirmation_check(
        checks,
        "M10: 候选测试因子显式确认状态",
        [factor_candidates, f_test_points, q_test_points],
        [factor_candidate_summary],
    )
    add_candidate_confirmation_check(
        checks,
        "M11: 候选原子操作显式确认状态",
        [atomic_candidates],
        [atomic_candidate_summary],
    )

    add_required_fields_check(
        checks,
        "M1: M 分析 CAE/trace 字段完整",
        m_test_points,
        {
            "C": ("C（Condition）", "Condition", "| C |", "前置"),
            "A": ("A（Action）", "Action", "| A |", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "预期"),
            "trace": ("trace_refs", "scenario_refs", "source_refs"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        },
    )
    add_required_fields_check(
        checks,
        "M2: F 分析 CAE/耦合字段完整",
        f_test_points,
        {
            "C": ("C（Condition）", "Condition", "| C |", "C 条件", "前置"),
            "A": ("A（Action）", "Action", "| A |", "A 动作", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "E 预期", "预期"),
            "coupling": ("coupling", "耦合", "coupling_refs"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        },
    )
    add_required_fields_check(
        checks,
        "M3: Q 分析 CAE/质量字段完整",
        q_test_points,
        {
            "C": ("C（Condition）", "Condition", "| C |", "C 条件", "前置"),
            "A": ("A（Action）", "Action", "| A |", "A 动作", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "E 预期", "预期"),
            "quality": ("quality_dimension", "质量", "HTSM"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        },
    )
    add_required_fields_check(
        checks,
        "M4/M5: LC trace/binding 字段完整",
        logic_cases,
        {
            "LC-ID": ("LC-ID", "logic_case_id", "LC-"),
            "source_tp_ids": ("source_tp_ids", "source_tp_id", "TP-"),
            "factor_bindings": ("factor_bindings", "factor_refs", "因子"),
            "topology_bindings": ("topology_bindings", "topology_role_refs", "组网绑定", "拓扑"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        },
    )
    add_required_fields_check(
        checks,
        "M6: 设计计划 PPDCS 字段完整",
        design_plan,
        {
            "logic_case": ("logic_case_id", "LC-ID", "LC-"),
            "ppdcs": ("PPDCS", "P-Process", "P-Parameter", "D-Data", "C-Combination", "S-State"),
            "method": ("recommended_method", "method", "设计方法"),
        },
    )
    if logic_cases is not None:
        add_marker_check(checks, "M4: LC factor_bindings 保留", logic_cases, ("factor_bindings", "factor_refs", "因子"), status_if_missing="WARN")
        add_marker_check(checks, "M5: LC topology_bindings 保留", logic_cases, ("topology_bindings", "topology_role_refs", "组网绑定", "拓扑"), status_if_missing="WARN")
    if factor_report is not None:
        add_marker_check(checks, "M8: N_scanned 已记录", factor_report, ("N_scanned", "扫描库数", "index.yaml"), status_if_missing="BLOCKING")
    if atomic_candidates is not None:
        add_marker_check(checks, "M9: match_attempt 已记录", atomic_candidates, ("match_attempt", "L1", "score"), status_if_missing="WARN")
    add_skill_evidence_check(
        checks,
        project_root,
        "MFQ Skill 调用证据完整",
        ("m-analyzer", "f-analyzer", "q-analyzer", "test-point-integrator", "design-planner"),
    )

    warnings = (
        "## 上下游 Warning（非阻断）\n\n"
        "| # | 检查项 | 状态 | 说明 |\n"
        "|---|--------|------|------|\n"
        "| W1 | KYM 场景下游可消费 | WARNING | 机器基线仅验证 MFQ 产物存在和关键字段，语义消费质量需人工确认 |\n"
        "| W2 | PPDCS 可消费 plan | WARNING | 设计计划语义正确性需在 GATE-3 人工确认和 GATE-4 二次检查中确认 |\n"
    )
    candidate_confirmation_sections = (
        render_candidate_confirmation_section(
            "GATE-3 候选测试因子确认摘要",
            [factor_candidates, f_test_points, q_test_points],
            [factor_candidate_summary],
        )
        + render_candidate_confirmation_section(
            "GATE-3 候选原子操作确认摘要",
            [atomic_candidates],
            [atomic_candidate_summary],
        )
    )

    manual_items = [
        (1, "M/F/Q 分析质量、LC 整合一致性、设计计划和公共因子消费仍需人工确认"),
        (2, "候选测试因子和候选原子操作必须显式展示并由用户确认；存在候选时不得由 Agent 自行判定全部确认或跳过"),
    ]

    overall = "PASS" if all(status not in ("BLOCKING", "MISSING") for _, _, status, _ in checks) else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-3", overall, feature_name, checks,
        pending_items=manual_items, suffix="auto",
        extra_sections=warnings + candidate_confirmation_sections,
    )
    gate3_step = "mfq-exit" if overall == "PASS" else "test-point-integrator"
    write_state(project_root, feature_name, "GATE-3", overall, current_step=gate3_step, input_root=input_root)
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_4(args: argparse.Namespace) -> int:
    """GATE-4 PPDCS Exit Gate: machine-baseline check for PPDCS phase completion."""
    project_root, input_root = resolve_feature_workspace(args)
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: PPDCS directories
    ppdcs_dirs = {
        "ppdcs/ppdcs": project_root / "ppdcs" / "ppdcs",
        "ppdcs/pc": project_root / "ppdcs" / "pc",
        "ppdcs/coverage": project_root / "ppdcs" / "coverage",
        "ppdcs/delivery": project_root / "ppdcs" / "delivery",
    }
    checks: list[tuple[int, str, str, str]] = []
    for label, dirpath in ppdcs_dirs.items():
        ok = dirpath.is_dir()
        checks.append((
            len(checks) + 1, f"Entry Criteria: {label}",
            "PASS" if ok else "BLOCKING",
            f"目录存在" if ok else f"目录不存在: {dirpath}",
        ))

    design_files = find_nonempty_files(project_root / "ppdcs" / "ppdcs", (".md",))
    pc_files = find_nonempty_files(project_root / "ppdcs" / "pc", (".md",))
    coverage_summary = first_existing(project_root, ["ppdcs/coverage/coverage-summary.md"])
    requirement_coverage = first_existing(project_root, ["ppdcs/coverage/requirement-coverage.md"])
    test_point_coverage = first_existing(project_root, ["ppdcs/coverage/test-point-coverage.md"])
    delivery_files = find_nonempty_files(project_root / "ppdcs" / "delivery", (".md",))

    checks.append((
        len(checks) + 1, "P1: PPDCS 设计过程完整",
        "PASS" if design_files else "BLOCKING",
        ", ".join(str(path) for path in design_files[:5]) if design_files else "ppdcs/ppdcs/ 下无非空 Markdown 设计过程文件",
    ))
    checks.append((
        len(checks) + 1, "P2: PC 文件完整",
        "PASS" if pc_files else "BLOCKING",
        ", ".join(str(path) for path in pc_files[:5]) if pc_files else "ppdcs/pc/ 下无非空 Markdown PC 文件",
    ))
    add_file_check(checks, "P4: 覆盖率摘要存在", coverage_summary)
    add_file_check(checks, "P4: 需求覆盖报告存在", requirement_coverage, status_if_missing="WARN")
    add_file_check(checks, "P4: 测试点覆盖报告存在", test_point_coverage, status_if_missing="WARN")
    if pc_files:
        combined_pc = "\n".join(read_text(path) for path in pc_files)
        add_pc_table_contract_check(
            checks,
            "P2: PC 16 列严格格式检查",
            pc_files,
            require_step_atomic=True,
        )
        add_pc_step_contract_check(
            checks,
            "P2: PC case_steps 原子操作回链检查",
            pc_files,
        )
        checks.append((
            len(checks) + 1, "P3: PC 拓扑绑定字段保留",
            "PASS" if contains_any(combined_pc, ("topology_bindings", "topology_role", "组网", "拓扑")) else "WARN",
            "PC 文件中发现拓扑绑定字段" if contains_any(combined_pc, ("topology_bindings", "topology_role", "组网", "拓扑")) else "PC 文件缺少 topology_bindings/topology_role 标记",
        ))
        checks.append((
            len(checks) + 1, "P7: fact_status 字段保留",
            "PASS" if contains_any(combined_pc, ("fact_status", "needs-confirmation", "confirmed")) else "WARN",
            "PC 文件中发现事实状态字段" if contains_any(combined_pc, ("fact_status", "needs-confirmation", "confirmed")) else "PC 文件缺少 fact_status 标记",
        ))
    checks.append((
        len(checks) + 1, "P6: 交付物预检",
        "PASS" if len(delivery_files) >= 2 else "BLOCKING",
        ", ".join(str(path) for path in delivery_files) if delivery_files else "ppdcs/delivery/ 下无交付 Markdown",
    ))
    if delivery_files:
        combined_delivery = "\n".join(read_text(path) for path in delivery_files)
        case_delivery_files = [
            path for path in delivery_files
            if "测试用例" in path.name or "case" in path.name.lower()
        ]
        add_pc_table_contract_check(
            checks,
            "P6: 交付测试用例 16 列汇总表检查",
            case_delivery_files,
            require_step_atomic=True,
            require_single_table=True,
        )
        checks.append((
            len(checks) + 1, "P6/P7: 交付 trace 字段完整",
            "PASS" if contains_all(combined_delivery, ("logic_case_id", "physical_case_id", "case_steps", "action_source_refs")) and contains_any(combined_delivery, ("trace_refs", "scenario_refs", "topology_bindings", "fact_status")) else "BLOCKING",
            "交付物包含 logic/physical case、case_steps、action_source_refs 与 trace 字段" if contains_all(combined_delivery, ("logic_case_id", "physical_case_id", "case_steps", "action_source_refs")) and contains_any(combined_delivery, ("trace_refs", "scenario_refs", "topology_bindings", "fact_status")) else "交付物缺少 logic_case_id/physical_case_id/case_steps/action_source_refs/trace 字段",
        ))
    add_skill_evidence_check(
        checks,
        project_root,
        "PPDCS Skill 调用证据完整",
        ("design-ppdcs-analyzer", "coverage-verifier", "deliverable-renderer"),
    )

    manual_items = [
        (1, "PPDCS 设计方法、物理用例质量、覆盖率结果和拓扑绑定仍需人工确认"),
    ]

    overall = "PASS" if all(status not in ("BLOCKING", "MISSING") for _, _, status, _ in checks) else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-4", overall, feature_name, checks,
        pending_items=manual_items, suffix="auto",
    )
    write_state(project_root, feature_name, "GATE-4", overall, current_step="design-ppdcs", input_root=input_root)
    print(result_path)
    return 0 if overall == "PASS" else 2


def run_gate_5(args: argparse.Namespace) -> int:
    """GATE-5 Exit Gate: machine-baseline check for final delivery readiness."""
    project_root, input_root = resolve_feature_workspace(args)
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    feature_name = args.feature_name or project_root.name

    # Entry Criteria: GATE-4 result exists, delivery dir exists
    checks: list[tuple[int, str, str, str]] = []
    gate4_result = project_root / "process" / "checkpoints" / "GATE-4-PPDCS-Exit-auto.md"
    gate4_ok = result_file_passed(gate4_result)
    checks.append((
        1, "GATE-4 已通过",
        "PASS" if gate4_ok else "BLOCKING",
        f"GATE-4 结果为 PASS: {gate4_result}" if gate4_ok else f"GATE-4 未通过或结果文件不存在: {gate4_result}",
    ))

    delivery_dir = project_root / "ppdcs" / "delivery"
    ok = delivery_dir.is_dir()
    checks.append((
        2, "交付物目录存在",
        "PASS" if ok else "BLOCKING",
        f"目录存在" if ok else f"目录不存在: {delivery_dir}",
    ))

    delivery_files = find_nonempty_files(delivery_dir, (".md",))
    plan_files = [path for path in delivery_files if "测试方案" in path.name]
    case_files = [path for path in delivery_files if "测试用例" in path.name]
    checks.append((
        len(checks) + 1, "交付物完整: 测试方案",
        "PASS" if plan_files else "BLOCKING",
        ", ".join(str(path) for path in plan_files) if plan_files else "缺少 <特性名>特性测试方案.md",
    ))
    checks.append((
        len(checks) + 1, "交付物完整: 测试用例",
        "PASS" if case_files else "BLOCKING",
        ", ".join(str(path) for path in case_files) if case_files else "缺少 <特性名>特性测试用例.md",
    ))
    candidate_files = [
        path for path in delivery_files
        if "候选" in path.name or "candidate" in path.name.lower()
    ]
    checks.append((
        len(checks) + 1, "候选对比表处理",
        "PASS" if candidate_files else "WARN",
        ", ".join(str(path) for path in candidate_files) if candidate_files else "未发现候选对比表；若无候选应在交付物中说明",
    ))
    combined_delivery = "\n".join(read_text(path) for path in delivery_files)
    checks.append((
        len(checks) + 1, "交付字段保留",
        "PASS" if contains_any(combined_delivery, ("topology_bindings", "topology_role", "fact_status", "source")) else "BLOCKING",
        "交付物保留 topology/fact/source 字段" if contains_any(combined_delivery, ("topology_bindings", "topology_role", "fact_status", "source")) else "交付物缺少 topology_bindings/topology_role/source/fact_status 标记",
    ))
    checks.append((
        len(checks) + 1, "公共库记录",
        "PASS" if contains_any(combined_delivery, ("library_id", "factor-library", "因子库", "checksum", "version")) else "WARN",
        "交付物包含公共库记录" if contains_any(combined_delivery, ("library_id", "factor-library", "因子库", "checksum", "version")) else "未发现公共库记录；若未使用公共库需人工确认 N/A",
    ))
    checks.append((
        len(checks) + 1, "不可提升状态",
        "PASS" if "needs-confirmation" in combined_delivery or "待确认" in combined_delivery or "fact_status" in combined_delivery else "WARN",
        "发现 fact_status / needs-confirmation 状态保留证据" if combined_delivery else "交付物为空或缺少状态字段",
    ))

    manual_items = [
        (1, "最终交付质量、候选对比表 N/A 和风险接受仍需人工确认"),
    ]

    overall = "PASS" if all(status not in ("BLOCKING", "MISSING") for _, _, status, _ in checks) else "BLOCKED"
    result_path = write_skeleton_result(
        checkpoints_dir, "GATE-5", overall, feature_name, checks,
        pending_items=manual_items,
    )
    write_state(project_root, feature_name, "GATE-5", overall, current_step="completed", input_root=input_root)
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

    Internal checks validate the target product directory plus the minimum
    machine-readable contract for the corresponding stage.
    """
    project_root, _input_root = resolve_feature_workspace(args)
    checkpoints_dir = project_root / "process" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    phase = "MFQ" if target.startswith("MFQ-INTERNAL-") else "PPDCS"
    print(f"[{cp}] {phase} 阶段内滚动自检: {target}")

    target_rel = INTERNAL_DIR_MAP.get(target)
    if not target_rel:
        print(f"  {cp} 未知内部检查目标: {target}")
        return 2

    checks: list[tuple[int, str, str, str]] = []
    target_dir = project_root / target_rel
    checks.append((
        len(checks) + 1,
        f"{target}: 产物目录存在",
        "PASS" if target_dir.is_dir() else "BLOCKING",
        str(target_dir) if target_dir.is_dir() else f"目录不存在: {target_dir}",
    ))

    if target == "MFQ-INTERNAL-M":
        m_test_points = first_existing(project_root, ["mfq/m-analysis/test-points.md"])
        add_required_fields_check(checks, "CP03: M CAE/trace/fact_status", m_test_points, {
            "C": ("C（Condition）", "Condition", "| C |", "前置"),
            "A": ("A（Action）", "Action", "| A |", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "预期"),
            "trace": ("trace_refs", "scenario_refs", "source_refs"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        })
        add_file_check(checks, "CP03: Scenario-TSP 覆盖矩阵存在", first_existing(project_root, ["mfq/m-analysis/scenario-tsp-coverage.md"]))
        add_file_check(checks, "CP03: PPDCS 标注存在", first_existing(project_root, ["mfq/m-analysis/ppdcs-annotation.md"]))
        add_file_check(checks, "CP03: 对象因子表存在", first_existing(project_root, ["mfq/m-analysis/test-objects-factors.md"]))
    elif target == "MFQ-INTERNAL-F":
        f_test_points = first_existing(project_root, ["mfq/f-analysis/coupling-test-points.md"])
        add_required_fields_check(checks, "CP04: F CAE/coupling/fact_status", f_test_points, {
            "C": ("C（Condition）", "Condition", "| C |", "C 条件", "前置"),
            "A": ("A（Action）", "Action", "| A |", "A 动作", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "E 预期", "预期"),
            "coupling": ("coupling", "耦合", "coupling_refs"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        })
        add_required_fields_check(checks, "CP04: F tool-analysis 字段", first_existing(project_root, ["mfq/f-analysis/tool-analysis.md"]), {
            "existing_tools": ("Existing Tool Summary", "现有工具"),
            "tool_gap": ("Tool Capability Gap", "工具能力缺口"),
        })
    elif target == "MFQ-INTERNAL-Q":
        q_test_points = first_existing(project_root, ["mfq/q-analysis/quality-test-points.md"])
        add_required_fields_check(checks, "CP05: Q CAE/quality/fact_status", q_test_points, {
            "C": ("C（Condition）", "Condition", "| C |", "C 条件", "前置"),
            "A": ("A（Action）", "Action", "| A |", "A 动作", "动作"),
            "E": ("E（Effect）", "Effect", "| E |", "E 预期", "预期"),
            "quality": ("quality_dimension", "质量", "HTSM"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        })
        add_required_fields_check(checks, "CP05: Q tool-analysis 字段", first_existing(project_root, ["mfq/q-analysis/tool-analysis.md"]), {
            "existing_tools": ("Existing Tool Summary", "现有工具"),
            "tool_gap": ("Tool Capability Gap", "工具能力缺口"),
        })
    elif target == "MFQ-INTERNAL-INTEGRATION":
        logic_cases = first_existing(project_root, ["mfq/integration/logic-cases.md"])
        add_file_check(checks, "CP06: all-test-points 存在", first_existing(project_root, ["mfq/integration/all-test-points.md"]))
        add_required_fields_check(checks, "CP06: LC trace/binding/fact_status", logic_cases, {
            "LC-ID": ("LC-ID", "logic_case_id", "LC-"),
            "source_tp_ids": ("source_tp_ids", "source_tp_id", "TP-"),
            "factor_bindings": ("factor_bindings", "factor_refs", "因子"),
            "topology_bindings": ("topology_bindings", "topology_role_refs", "组网绑定", "拓扑"),
            "fact_status": ("fact_status", "confirmed", "needs-confirmation"),
        })
        add_file_check(checks, "CP06: test-data 存在", first_existing(project_root, ["mfq/integration/test-data.md"]))
        add_file_check(checks, "CP06: 候选因子汇总存在", first_existing(project_root, ["mfq/candidates/factor-candidates.md"]), status_if_missing="WARN")
        add_file_check(checks, "CP06: 候选原子操作汇总存在", first_existing(project_root, ["mfq/candidates/ptm-atomic-candidates.md"]), status_if_missing="WARN")
    elif target == "MFQ-INTERNAL-PLAN":
        design_plan = first_existing(project_root, ["process/plan/design-plan.md", "mfq/integration/design-plan.md"])
        add_required_fields_check(checks, "CP07: 设计计划字段", design_plan, {
            "logic_case": ("logic_case_id", "LC-ID", "LC-"),
            "ppdcs": ("PPDCS", "P-Process", "P-Parameter", "D-Data", "C-Combination", "S-State"),
            "method": ("recommended_method", "method", "设计方法"),
            "gap": ("待确认", "confirmation_gap_refs", "uncertain", "fact_status"),
        })
        add_file_check(checks, "CP07: 设计推理存在", first_existing(project_root, ["process/plan/design-planner-reasoning.md"]))

    overall = "PASS" if all(status not in ("BLOCKING", "MISSING") for _, _, status, _ in checks) else "BLOCKED"
    result_path = checkpoints_dir / f"{cp}-{target}-auto.md"
    rows = "\n".join(
        f"| {idx} | {item} | {status} | {evidence} |"
        for idx, item, status, evidence in checks
    )
    result_path.write_text(
        f"---\ncheck_depth: internal-field-baseline\ncheckpoint: {cp}\ntarget: {target}\n---\n"
        f"# {cp} {target}\n\n"
        f"- 结论：`{overall}`\n"
        f"- 检查时间：`{dt.datetime.now(dt.timezone.utc).isoformat()}`\n\n"
        "| # | 检查项 | 状态 | 证据 / 处理意见 |\n"
        "|---|---|---|---|\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    print(result_path)
    return 0 if overall == "PASS" else 1


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
    mode_group.add_argument(
        "--record-skill-call",
        action="store_true",
        help="记录一次 Skill 执行证据到 process/execution/SKILL-CALLS.yaml",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--input-dir", default="", help="显式指定目标 .input 目录；其父目录作为特性工作区")
    parser.add_argument("--feature-name", default="")
    parser.add_argument("--requirement", default="")
    parser.add_argument("--wiki-index", default="")
    parser.add_argument("--skill-name", default="", help="--record-skill-call: Skill 名称")
    parser.add_argument("--phase", default="", help="--record-skill-call: kym/mfq/ppdcs/delivery 等阶段")
    parser.add_argument("--status", default="completed", choices=["completed", "blocked", "failed", "waived"], help="--record-skill-call: 执行状态")
    parser.add_argument("--input-ref", action="append", default=[], help="--record-skill-call: 输入引用，可重复")
    parser.add_argument("--output-ref", action="append", default=[], help="--record-skill-call: 输出引用，可重复")
    parser.add_argument("--evidence-summary", default="", help="--record-skill-call: 证据摘要")
    parser.add_argument("--platform", default="unknown", choices=["codex", "claude", "unknown"], help="--record-skill-call: 平台")
    parser.add_argument("--caller", default="ptm-tde", help="--record-skill-call: 调用方")
    parser.add_argument("--call-id", default="", help="--record-skill-call: 可选自定义调用 ID")
    parser.add_argument("--started-at", default="", help="--record-skill-call: 可选开始时间 ISO-8601")
    parser.add_argument("--completed-at", default="", help="--record-skill-call: 可选完成时间 ISO-8601")
    args = parser.parse_args()

    # Routing priority: --gate > --cp > positional checkpoint_id
    if args.gate:
        return dispatch_gate(args.gate, args)
    if args.cp:
        return dispatch_cp(args.cp, args)
    if args.record_skill_call:
        if not args.skill_name:
            print("--record-skill-call 需要 --skill-name", file=sys.stderr)
            return 2
        if not args.phase:
            print("--record-skill-call 需要 --phase", file=sys.stderr)
            return 2
        if args.status == "completed" and not args.output_ref:
            print("status=completed 需要至少一个 --output-ref", file=sys.stderr)
            return 2
        return write_skill_call(args)
    # Backward-compat: positional CP01
    if args.checkpoint_id:
        print(f"[legacy] 位置参数 {args.checkpoint_id} -> 路由到 GATE-1 Entry Gate")
        return run_gate_1(args)
    # Nothing specified
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
