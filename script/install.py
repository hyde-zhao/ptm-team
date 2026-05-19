#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "inquirerpy>=0.3.4",
# ]
# ///
"""
ptm-team installer.

Installs workflow assets (agents and skills) into platform-specific directories.

Usage:
  uv run python script/install.py install claude --agent ptm-tde
  uv run python script/install.py install codex --agent tde
  uv run python script/install.py install claude --skill
  uv run python script/install.py install claude --skill checkpoint
  uv run python script/install.py uninstall claude --agent
  uv run python script/install.py uninstall claude --skill
  uv run python script/install.py install claude --list
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Try to import InquirerPy for interactive mode
try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
except ImportError:
    inquirer = None

# Constants
VALID_PLATFORMS = ("claude", "codex")
MANAGED_VERSION = "1.0.0"
MANIFEST_FILENAME = ".ptm-team-manifest.json"

# Agent aliases
AGENT_ALIASES = {
    "tde": "ptm-tde",
    "ptm-tde": "ptm-tde",
}

# ptm-tde referenced skills (from docs/ptm-tde/skill-references.md)
PMT_TDE_SKILLS = [
    # Main flow skills
    "checkpoint-manager",
    "feature-parser",
    "scenario-discovery",
    "m-analyzer",
    "f-analyzer",
    "q-analyzer",
    "test-point-integrator",
    "design-planner",
    "design-ppdcs-analyzer",
    "process-design",
    "parameter-design",
    "data-design",
    "combination-design",
    "state-design",
    "coverage-verifier",
    "deliverable-renderer",
    # Post-delivery skill
    "case-retriever",
    # Extension skills
    "change-impact-analyzer",
    "bug-gap-analyzer",
]

# Platform directory mapping
PLATFORM_DIRS = {
    "claude": {
        "agents": ".claude/agents",
        "skills": ".claude/skills",
    },
    "codex": {
        "agents": ".codex/agents",
        "skills": ".agents/skills",
    },
}

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


@dataclass
class ManifestEntry:
    kind: str  # "agent" or "skill"
    name: str
    path: str
    remove_path: str


@dataclass
class InstallRecord:
    platform: str
    scope: str
    status: str
    installed_at: str
    workspace_root: str
    entries: list[ManifestEntry] = field(default_factory=list)


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from markdown content."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        fields[key] = value

    body = content[match.end():].lstrip()
    return fields, body


def yaml_scalar(value: str) -> str:
    """Escape a value for YAML."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def toml_string(value: str) -> str:
    """Escape a value for TOML."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def toml_multiline(value: str) -> str:
    """Escape a value for TOML multiline string."""
    return value.replace("\\", "\\\\").replace('"""', '\\"""')


def render_claude_agent(
    name: str,
    description: str,
    instructions: str,
    commit: str,
    generated: str,
    color: str = "",
) -> str:
    """Render agent content in Claude Code format (.md)."""
    frontmatter = [
        "---",
        f"name: {yaml_scalar(name)}",
        f"description: {yaml_scalar(description)}",
    ]
    if color:
        frontmatter.append(f"color: {yaml_scalar(color)}")
    frontmatter.append("---")

    audit = f"<!-- ptm-team-managed: version={MANAGED_VERSION} canonical-commit={commit} generated={generated} -->"
    return "\n".join(frontmatter) + f"\n{audit}\n\n{instructions.rstrip()}\n"


def render_codex_agent(
    name: str,
    description: str,
    instructions: str,
    commit: str,
    generated: str,
    nicknames: list[str] | None = None,
) -> str:
    """Render agent content in Codex format (.toml)."""
    audit = f"# ptm-team-managed: version={MANAGED_VERSION} canonical-commit={commit} generated={generated}"

    lines = [
        audit,
        f"name = {toml_string(name)}",
    ]
    if nicknames:
        nickname_array = "[" + ", ".join(toml_string(n) for n in nicknames) + "]"
        lines.append(f"nickname_candidates = {nickname_array}")
    lines.extend([
        'description = """',
        toml_multiline(description),
        '"""',
        'developer_instructions = """',
        toml_multiline(instructions.rstrip()),
        '"""',
        "",
    ])
    return "\n".join(lines)


def read_skill_description(skill_dir: Path, max_len: int = 80) -> str:
    """Read description from SKILL.md frontmatter."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ""
    try:
        content = skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    fields, _ = parse_frontmatter(content)
    desc = fields.get("description", "")
    if len(desc) > max_len:
        desc = desc[:max_len] + "..."
    return desc


def find_skills(source_dir: Path) -> list[Path]:
    """Find all skill directories containing SKILL.md."""
    if not source_dir.is_dir():
        return []
    return sorted(
        (p for p in source_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()),
        key=lambda p: p.name.lower(),
    )


def fuzzy_match_skills(keyword: str, all_skills: list[str]) -> list[str]:
    """Fuzzy match skill names by substring."""
    keyword_lower = keyword.lower()
    return [s for s in all_skills if keyword_lower in s.lower()]


def resolve_agent_name(name: str) -> str:
    """Resolve agent alias to canonical name."""
    canonical = AGENT_ALIASES.get(name.lower())
    if canonical is None:
        fail(f"未知的 agent 名称: {name}。支持的 agent: {', '.join(AGENT_ALIASES.keys())}")
    return canonical


def get_agent_skills(agent_name: str) -> list[str]:
    """Get the list of skills referenced by an agent."""
    if agent_name == "ptm-tde":
        return PMT_TDE_SKILLS
    return []


def load_manifest(manifest_path: Path) -> dict:
    """Load manifest file."""
    if not manifest_path.exists():
        return {"manifest_version": 1, "installs": []}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[WARN] 无法读取 manifest: {e}")
        return {"manifest_version": 1, "installs": []}


def save_manifest(manifest_path: Path, payload: dict) -> None:
    """Save manifest file."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def find_install_record(manifest: dict, platform: str) -> Optional[dict]:
    """Find existing install record for platform."""
    for record in manifest.get("installs", []):
        if record.get("platform") == platform and record.get("status") == "installed":
            return record
    return None


def upsert_install_record(manifest: dict, record: dict) -> None:
    """Insert or update install record."""
    installs = manifest.get("installs", [])
    # Remove existing record for same platform
    installs = [r for r in installs if r.get("platform") != record["platform"]]
    installs.append(record)
    manifest["installs"] = installs


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, creating parent directories if needed."""
    path.mkdir(parents=True, exist_ok=True)


def copy_skill_tree(src_dir: Path, dest_dir: Path, dry_run: bool) -> None:
    """Copy skill directory tree."""
    if dry_run:
        print(f"  [DryRun] 复制 skill: {src_dir.name} -> {dest_dir}")
        return

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir)
    print(f"  ✓ 安装 skill: {src_dir.name}")


def remove_path(path: Path, dry_run: bool) -> None:
    """Remove file or directory."""
    if not path.exists():
        return
    if dry_run:
        print(f"  [DryRun] 删除: {path}")
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"  ✓ 删除: {path}")


def install_agent(
    platform: str,
    agent_name: str,
    source_dir: Path,
    workspace_root: Path,
    commit: str,
    generated: str,
    dry_run: bool,
) -> list[ManifestEntry]:
    """Install an agent and its referenced skills."""
    entries: list[ManifestEntry] = []

    # Resolve agent file
    agent_file = source_dir / "agents" / f"{agent_name}.md"
    if not agent_file.is_file():
        fail(f"Agent 文件不存在: {agent_file}")

    # Read agent content
    content = agent_file.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(content)
    description = fields.get("description", "")
    color = fields.get("color", "")

    # Render for platform
    agents_dir = workspace_root / PLATFORM_DIRS[platform]["agents"]
    if platform == "claude":
        dest = agents_dir / f"{agent_name}.md"
        rendered = render_claude_agent(agent_name, description, body, commit, generated, color)
    else:
        dest = agents_dir / f"{agent_name}.toml"
        rendered = render_codex_agent(agent_name, description, body, commit, generated)

    # Write agent file
    if dry_run:
        print(f"[DryRun] 安装 agent: {dest}")
    else:
        ensure_directory(agents_dir)
        dest.write_text(rendered, encoding="utf-8")
        print(f"✓ 安装 agent: {dest}")

    entries.append(ManifestEntry(
        kind="agent",
        name=agent_name,
        path=str(dest.relative_to(workspace_root)),
        remove_path=str(dest.relative_to(workspace_root)),
    ))

    # Install referenced skills
    skills = get_agent_skills(agent_name)
    if skills:
        print(f"\n安装 {agent_name} 引用的 {len(skills)} 个 skills:")
        skills_dir = source_dir / "skills"
        dest_skills_dir = workspace_root / PLATFORM_DIRS[platform]["skills"]

        for skill_name in skills:
            skill_src = skills_dir / skill_name
            if not skill_src.is_dir():
                print(f"  [WARN] Skill 目录不存在: {skill_name}")
                continue
            skill_dest = dest_skills_dir / skill_name
            copy_skill_tree(skill_src, skill_dest, dry_run)
            entries.append(ManifestEntry(
                kind="skill",
                name=skill_name,
                path=str(skill_dest.relative_to(workspace_root)),
                remove_path=str(skill_dest.relative_to(workspace_root)),
            ))

    return entries


def install_skills_interactive(
    platform: str,
    source_dir: Path,
    workspace_root: Path,
    commit: str,
    generated: str,
    dry_run: bool,
    keyword: str = "",
) -> list[ManifestEntry]:
    """Install skills with interactive selection or fuzzy match."""
    entries: list[ManifestEntry] = []

    # Find all available skills
    skills_dir = source_dir / "skills"
    all_skill_dirs = find_skills(skills_dir)
    all_skill_names = [s.name for s in all_skill_dirs]

    if not all_skill_names:
        fail("没有找到任何 skill")

    # Get currently installed skills
    dest_skills_dir = workspace_root / PLATFORM_DIRS[platform]["skills"]
    installed_skills: set[str] = set()
    if dest_skills_dir.is_dir():
        installed_skills = {
            d.name for d in dest_skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file()
        }

    # Select skills to install
    selected_skills: list[str] = []

    if keyword:
        # Fuzzy match mode
        matched = fuzzy_match_skills(keyword, all_skill_names)
        if not matched:
            fail(f"没有匹配 '{keyword}' 的 skill")
        if len(matched) == 1:
            selected_skills = matched
            print(f"匹配到 1 个 skill: {matched[0]}")
        else:
            print(f"匹配到 {len(matched)} 个 skill:")
            for s in matched:
                desc = read_skill_description(skills_dir / s)
                status = " (已安装)" if s in installed_skills else ""
                print(f"  - {s}{status}: {desc}")
            if inquirer is None:
                fail("交互式模式需要 InquirerPy，请先安装: pip install inquirerpy")
            selected = inquirer.checkbox(
                message="选择要安装的 skill:",
                choices=[
                    Choice(value=s, name=f"{s}  —  {read_skill_description(skills_dir / s)}")
                    for s in matched
                ],
                instruction="(空格选择, 回车确认)",
            ).execute()
            selected_skills = selected or []
    else:
        # Interactive mode
        if inquirer is None:
            fail("交互式模式需要 InquirerPy，请先安装: pip install inquirerpy")

        choices = []
        for skill_dir in all_skill_dirs:
            name = skill_dir.name
            desc = read_skill_description(skill_dir)
            is_installed = name in installed_skills
            label = f"{name}  —  {desc}"
            if is_installed:
                label += "  (已安装)"
            choices.append(Choice(value=name, name=label, enabled=is_installed))

        selected = inquirer.checkbox(
            message="选择要安装的 skill (已安装的默认勾选):",
            choices=choices,
            instruction="(空格选择, a全选, i反选, 回车确认)",
            keybindings={
                "toggle-all-true": [{"key": "a"}],
                "toggle-all-false": [{"key": "i"}],
            },
        ).execute()
        selected_skills = selected or []

    # Install selected skills
    if selected_skills:
        new_skills = [s for s in selected_skills if s not in installed_skills]
        if new_skills:
            print(f"\n安装 {len(new_skills)} 个新 skill:")
            for skill_name in new_skills:
                skill_src = skills_dir / skill_name
                skill_dest = dest_skills_dir / skill_name
                copy_skill_tree(skill_src, skill_dest, dry_run)
                entries.append(ManifestEntry(
                    kind="skill",
                    name=skill_name,
                    path=str(skill_dest.relative_to(workspace_root)),
                    remove_path=str(skill_dest.relative_to(workspace_root)),
                ))
        else:
            print("没有新的 skill 需要安装")
    else:
        print("未选择任何 skill")

    return entries


def uninstall_agent(
    platform: str,
    agent_name: str,
    workspace_root: Path,
    manifest: dict,
    dry_run: bool,
) -> None:
    """Uninstall agent and its skills based on manifest."""
    record = find_install_record(manifest, platform)
    if record is None:
        fail(f"未找到 {platform} 的安装记录")

    # Filter entries for this agent and its skills
    entries_to_remove = []
    remaining_entries = []

    for entry in record.get("entries", []):
        if entry["kind"] == "agent" and entry["name"] == agent_name:
            entries_to_remove.append(entry)
        elif entry["kind"] == "skill" and entry["name"] in get_agent_skills(agent_name):
            entries_to_remove.append(entry)
        else:
            remaining_entries.append(entry)

    if not entries_to_remove:
        fail(f"未找到 agent {agent_name} 的安装记录")

    # Remove files
    print(f"卸载 agent {agent_name} 及其 skills:")
    for entry in entries_to_remove:
        path = workspace_root / entry["remove_path"]
        remove_path(path, dry_run)

    # Update manifest
    record["entries"] = remaining_entries
    if not remaining_entries:
        record["status"] = "uninstalled"
        record["uninstalled_at"] = iso_now()

    if not dry_run:
        save_manifest(workspace_root / MANIFEST_FILENAME, manifest)


def uninstall_skills_interactive(
    platform: str,
    workspace_root: Path,
    manifest: dict,
    dry_run: bool,
) -> None:
    """Uninstall skills with interactive selection."""
    # Get currently installed skills
    dest_skills_dir = workspace_root / PLATFORM_DIRS[platform]["skills"]
    installed_skills: list[str] = []
    if dest_skills_dir.is_dir():
        installed_skills = sorted(
            d.name for d in dest_skills_dir.iterdir()
            if d.is_dir() and (d / "SKILL.md").is_file()
        )

    if not installed_skills:
        print("没有已安装的 skill")
        return

    # Interactive selection
    if inquirer is None:
        fail("交互式模式需要 InquirerPy，请先安装: pip install inquirerpy")

    selected = inquirer.checkbox(
        message="选择要保留的 skill (取消勾选将卸载):",
        choices=[
            Choice(value=s, name=f"{s}  —  已安装", enabled=True)
            for s in installed_skills
        ],
        instruction="(空格选择, 回车确认)",
    ).execute()

    skills_to_keep = set(selected or [])
    skills_to_uninstall = [s for s in installed_skills if s not in skills_to_keep]

    if not skills_to_uninstall:
        print("没有 skill 需要卸载")
        return

    # Uninstall skills
    print(f"\n卸载 {len(skills_to_uninstall)} 个 skill:")
    for skill_name in skills_to_uninstall:
        path = dest_skills_dir / skill_name
        remove_path(path, dry_run)

    # Update manifest
    record = find_install_record(manifest, platform)
    if record:
        record["entries"] = [
            e for e in record.get("entries", [])
            if not (e["kind"] == "skill" and e["name"] in skills_to_uninstall)
        ]
        if not dry_run:
            save_manifest(workspace_root / MANIFEST_FILENAME, manifest)


def uninstall_all(
    platform: str,
    workspace_root: Path,
    manifest: dict,
    dry_run: bool,
) -> None:
    """Uninstall all agents and skills for a platform."""
    record = find_install_record(manifest, platform)
    if record is None:
        fail(f"未找到 {platform} 的安装记录")

    entries = record.get("entries", [])
    if not entries:
        print(f"没有 {platform} 的安装内容")
        return

    print(f"卸载 {platform} 的所有安装内容:")
    for entry in entries:
        path = workspace_root / entry["remove_path"]
        remove_path(path, dry_run)

    # Update manifest
    record["status"] = "uninstalled"
    record["uninstalled_at"] = iso_now()
    record["entries"] = []

    if not dry_run:
        save_manifest(workspace_root / MANIFEST_FILENAME, manifest)


def list_installed(platform: str, workspace_root: Path, manifest: dict) -> None:
    """List installed agents and skills."""
    record = find_install_record(manifest, platform)
    if record is None:
        print(f"没有 {platform} 的安装记录")
        return

    agents = [e for e in record.get("entries", []) if e["kind"] == "agent"]
    skills = [e for e in record.get("entries", []) if e["kind"] == "skill"]

    print(f"\n{platform} 已安装内容:")
    print(f"  安装时间: {record.get('installed_at', 'unknown')}")

    if agents:
        print(f"\n  Agents ({len(agents)}):")
        for a in agents:
            print(f"    - {a['name']}")

    if skills:
        print(f"\n  Skills ({len(skills)}):")
        for s in skills:
            print(f"    - {s['name']}")


def find_source_dir() -> Path:
    """Find the ptm-team source directory containing agents/ and skills/."""
    # Try relative to the script location (development mode)
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent,  # ptm_team/../
        script_dir,  # ptm_team/
    ]

    for candidate in candidates:
        if (candidate / "agents").is_dir() and (candidate / "skills").is_dir():
            return candidate

    # Try common locations
    home = Path.home()
    candidates.extend([
        home / "projects" / "ptm-team",
        home / "ptm-team",
    ])

    for candidate in candidates:
        if candidate.is_dir() and (candidate / "agents").is_dir() and (candidate / "skills").is_dir():
            return candidate

    fail("找不到 ptm-team 源目录（包含 agents/ 和 skills/）。请设置 PTM_TEAM_DIR 环境变量。")
    return Path()  # unreachable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ptm-team workflow asset installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--source-dir", help="ptm-team 源目录路径")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # install subcommand
    install_parser = subparsers.add_parser("install", help="安装 agent 或 skill")
    install_parser.add_argument("platform", choices=VALID_PLATFORMS, help="目标平台")
    install_parser.add_argument("--agent", nargs="?", const="", help="安装 agent (可指定名称)")
    install_parser.add_argument("--skill", nargs="?", const="", help="安装 skill (可指定关键字)")
    install_parser.add_argument("--list", action="store_true", help="列出已安装内容")
    install_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    # uninstall subcommand
    uninstall_parser = subparsers.add_parser("uninstall", help="卸载 agent 或 skill")
    uninstall_parser.add_argument("platform", choices=VALID_PLATFORMS, help="目标平台")
    uninstall_parser.add_argument("--agent", nargs="?", const="", help="卸载 agent")
    uninstall_parser.add_argument("--skill", action="store_true", help="卸载 skill (交互式)")
    uninstall_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.command:
        fail("请指定命令: install 或 uninstall")

    # Determine workspace root (project directory)
    workspace_root = Path.cwd().resolve()

    # Find source directory
    if args.source_dir:
        source_dir = Path(args.source_dir).expanduser().resolve()
        if not (source_dir / "agents").is_dir() or not (source_dir / "skills").is_dir():
            fail(f"指定的源目录缺少 agents/ 或 skills/ 目录: {source_dir}")
    else:
        # Check environment variable first
        import os
        env_dir = os.environ.get("PTM_TEAM_DIR")
        if env_dir:
            source_dir = Path(env_dir).expanduser().resolve()
            if not (source_dir / "agents").is_dir() or not (source_dir / "skills").is_dir():
                fail(f"PTM_TEAM_DIR 指定的目录缺少 agents/ 或 skills/ 目录: {source_dir}")
        else:
            source_dir = find_source_dir()

    # Load manifest
    manifest_path = workspace_root / MANIFEST_FILENAME
    manifest = load_manifest(manifest_path)

    # Get commit info
    commit = canonical_commit(source_dir)
    generated = iso_now()

    print(f"工作目录: {workspace_root}")
    print(f"源目录: {source_dir}")
    print(f"平台: {args.platform}")
    print()

    if args.command == "install":
        # List mode
        if args.list:
            list_installed(args.platform, workspace_root, manifest)
            return

        # Agent install
        if args.agent is not None:
            agent_name = args.agent if args.agent else "ptm-tde"
            agent_name = resolve_agent_name(agent_name)
            entries = install_agent(
                args.platform, agent_name, source_dir, workspace_root,
                commit, generated, args.dry_run,
            )
            # Update manifest
            if not args.dry_run and entries:
                record = find_install_record(manifest, args.platform) or {
                    "platform": args.platform,
                    "scope": "project",
                    "status": "installed",
                    "installed_at": generated,
                    "workspace_root": str(workspace_root),
                    "entries": [],
                }
                record["entries"].extend([{
                    "kind": e.kind,
                    "name": e.name,
                    "path": e.path,
                    "remove_path": e.remove_path,
                } for e in entries])
                upsert_install_record(manifest, record)
                save_manifest(manifest_path, manifest)
            return

        # Skill install
        if args.skill is not None:
            keyword = args.skill
            entries = install_skills_interactive(
                args.platform, source_dir, workspace_root,
                commit, generated, args.dry_run, keyword,
            )
            # Update manifest
            if not args.dry_run and entries:
                record = find_install_record(manifest, args.platform) or {
                    "platform": args.platform,
                    "scope": "project",
                    "status": "installed",
                    "installed_at": generated,
                    "workspace_root": str(workspace_root),
                    "entries": [],
                }
                record["entries"].extend([{
                    "kind": e.kind,
                    "name": e.name,
                    "path": e.path,
                    "remove_path": e.remove_path,
                } for e in entries])
                upsert_install_record(manifest, record)
                save_manifest(manifest_path, manifest)
            return

        fail("请指定 --agent 或 --skill")

    elif args.command == "uninstall":
        # Agent uninstall
        if args.agent is not None:
            agent_name = args.agent if args.agent else ""
            if agent_name:
                agent_name = resolve_agent_name(agent_name)
                uninstall_agent(args.platform, agent_name, workspace_root, manifest, args.dry_run)
            else:
                # Uninstall all agents (and their skills)
                uninstall_all(args.platform, workspace_root, manifest, args.dry_run)
            return

        # Skill uninstall
        if args.skill:
            uninstall_skills_interactive(args.platform, workspace_root, manifest, args.dry_run)
            return

        # Uninstall all
        uninstall_all(args.platform, workspace_root, manifest, args.dry_run)


if __name__ == "__main__":
    main()
