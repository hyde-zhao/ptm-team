#!/usr/bin/env python3
"""Run ptm-tde runtime checkpoints for a feature project."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
from pathlib import Path


REQ_SUFFIXES = {".md", ".markdown", ".docx", ".xlsx", ".xls", ".pdf", ".txt"}
TOPO_MARKERS = ("topo", "topology", "组网", "拓扑")
COUPLING_MARKERS = ("coupling", "matrix", "耦合", "矩阵")


def find_files(root: Path, markers: tuple[str, ...] | None = None) -> list[Path]:
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
    if ok:
        return "PASS", evidence
    return "BLOCKING", blocked_hint or evidence


def probe_atomic_ops() -> tuple[bool, str]:
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


def write_state(project_root: Path, feature_name: str, cp_status: str) -> None:
    doc_dir = project_root / "doc"
    doc_dir.mkdir(parents=True, exist_ok=True)
    state_path = doc_dir / "STATE.yaml"
    content = (
        'current_step: "input"\n'
        f'feature_name: "{feature_name}"\n'
        'runtime_root: "."\n'
        f'cp01_status: "{cp_status}"\n'
        f'updated_at: "{dt.datetime.now(dt.timezone.utc).isoformat()}"\n'
    )
    state_path.write_text(content, encoding="utf-8")


def run_cp01(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    input_root = project_root / "input"
    checkpoints_dir = project_root / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    requirement = Path(args.requirement).resolve() if args.requirement else None
    requirement_hits = [requirement] if requirement and requirement.exists() else find_files(input_root)
    topo_hits = find_files(input_root, TOPO_MARKERS)
    coupling_hits = find_files(input_root, COUPLING_MARKERS)
    atomic_ok, atomic_evidence = probe_atomic_ops()

    title = read_title(requirement_hits[0]) if requirement_hits else ""
    feature_name = args.feature_name or title or project_root.name

    required_dirs = [
        project_root / "analysis" / "feature-input",
        project_root / "analysis" / "scenarios",
        project_root / "analysis" / "m-analysis",
        project_root / "analysis" / "f-analysis",
        project_root / "analysis" / "q-analysis",
        project_root / "analysis" / "integration",
        project_root / "analysis" / "plan",
        project_root / "analysis" / "coverage",
        project_root / "design" / "ppdcs",
        project_root / "design" / "pc",
        project_root / "delivery",
        project_root / "doc",
    ]

    dir_errors: list[str] = []
    for directory in required_dirs:
        try:
            if directory.exists() and not directory.is_dir():
                dir_errors.append(f"{directory} is not a directory")
            else:
                directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            dir_errors.append(f"{directory}: {exc}")

    wiki_note = f"wiki index provided: {args.wiki_index}" if args.wiki_index else "wiki lookup required if local evidence is missing"
    checks: list[tuple[str, str, str, str]] = []
    requirement_evidence = ", ".join(str(p) for p in requirement_hits) or wiki_note
    checks.append(("需求文件存在", *status_line(bool(requirement_hits or args.wiki_index), requirement_evidence, "本地 input/ 和显式路径均未找到需求文件；请提供需求文件或 wiki 需求/接口文档。")))
    checks.append(("特性名可确定", *status_line(bool(feature_name), feature_name, "无法确定特性名；请显式提供 --feature-name。")))
    checks.append(("atomic-ops 可用或 wiki 兜底", *status_line(bool(atomic_ok or args.wiki_index), atomic_evidence if atomic_ok else wiki_note, "全局命令 atomic-ops 不可用，且未提供 wiki 兜底信息。")))
    checks.append(("防火墙 topo 可用或 wiki 兜底", *status_line(bool(topo_hits or args.wiki_index), ", ".join(str(p) for p in topo_hits) or wiki_note, "本地 input/ 未找到 topo，wiki 也未提供；请补充防火墙 topo 文件或 wiki 文档。")))
    checks.append(("耦合矩阵可用或 wiki 兜底", *status_line(bool(coupling_hits or args.wiki_index), ", ".join(str(p) for p in coupling_hits) or wiki_note, "本地 input/ 未找到耦合矩阵，wiki 也未提供；请补充耦合矩阵或 wiki 文档。")))
    checks.append(("输出目录就绪", *status_line(not dir_errors, "runtime directories created", "; ".join(dir_errors))))

    overall = "PASS" if all(status == "PASS" for _, status, _ in checks) else "BLOCKED"
    result_path = checkpoints_dir / "CP01_input_auto.md"
    rows = "\n".join(f"| {idx} | {name} | {status} | {evidence} |" for idx, (name, status, evidence) in enumerate(checks, start=1))
    result_path.write_text(
        "# CP01 Input 自检\n\n"
        f"- 结论：`{overall}`\n"
        f"- 特性名：`{feature_name}`\n"
        f"- 检查时间：`{dt.datetime.now(dt.timezone.utc).isoformat()}`\n\n"
        "| # | 检查项 | 状态 | 证据 / 处理意见 |\n"
        "|---|---|---|---|\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    write_state(project_root, feature_name, overall)
    print(result_path)
    return 0 if overall == "PASS" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", choices=["CP01"])
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--feature-name", default="")
    parser.add_argument("--requirement", default="")
    parser.add_argument("--wiki-index", default="")
    args = parser.parse_args()
    if args.checkpoint == "CP01":
        return run_cp01(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
