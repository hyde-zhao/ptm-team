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
  uv run python script/install.py check codex --agent ptm-tde
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
VALID_PLATFORMS = ("claude", "codex", "qoder")
MANAGED_VERSION = "1.0.0"
MANIFEST_FILENAME = ".ptm-team-manifest.json"
RESOURCE_HOME_ENV = "PTM_TEAM_RESOURCE_HOME"
DEFAULT_RESOURCE_HOME = Path.home() / ".ptm-team" / "resource"
PTM_TDE_RULE_BLOCK_ID = "ptm-tde-workflow"
PTM_TE_RULE_BLOCK_ID = "ptm-te-workflow"
# 平台 -> 规则文件名映射（ptm-tde 与 ptm-te 共用同一文件）
RULE_FILES = {
    "claude": "CLAUDE.md",
    "codex": "AGENTS.md",
    "qoder": "AGENTS.md",
}
PTM_TDE_RULE_FILES = RULE_FILES  # legacy 兼容别名

# Agent aliases
AGENT_ALIASES = {
    "tde": "ptm-tde",
    "ptm-tde": "ptm-tde",
    "te": "ptm-te",
    "ptm-te": "ptm-te",
}

# ptm-tde referenced skills (from docs/ptm-tde/skill-references.md)
PMT_TDE_SKILLS = [
    # Main flow skills
    "checkpoint-manager",
    "kym",
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
    # Post-delivery skills
    "case-retriever",
    "tde-feedback",
    # Extension skills
    "change-impact-analyzer",
    "bug-gap-analyzer",
]

# ptm-te referenced skills（设备管理 + 策略路由执行）
PTM_TE_SKILLS = [
    "device-management",
    "device-connection",
    "policy-route-execution",
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
    "qoder": {
        "agents": ".qoder/agents",
        "skills": ".qoder/skills",
    },
}

FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


@dataclass
class ManifestEntry:
    kind: str  # "agent", "skill", "resource", or "rule"
    name: str
    path: str
    remove_path: str
    resource_type: str = ""
    managed_block_id: str = ""
    source_hash: str = ""
    installed_hash: str = ""
    installed_for: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    resource_files: list[str] = field(default_factory=list)


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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_directory(root: Path) -> str:
    """Hash a directory deterministically by relative path and file content."""
    h = hashlib.sha256()
    if not root.is_dir():
        return ""
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def sha256_file_set(root: Path, relative_files: list[str]) -> str:
    """Hash a stable set of files under root by relative path and content."""
    h = hashlib.sha256()
    for rel in sorted(set(relative_files)):
        path = root / rel
        if not path.is_file():
            return ""
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def relative_files_under(root: Path) -> list[str]:
    """Return relative file paths below root, or one file name when root is a file."""
    if root.is_file():
        return [root.name]
    if not root.is_dir():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse YAML frontmatter from markdown content.

    Handles YAML block scalars (``>-`` folded, ``|`` literal) so multi-line
    descriptions survive the round-trip without turning into bare ``>-``.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content

    raw = match.group(1)
    lines = raw.splitlines()

    fields: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue

        key, sep, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Detect YAML block scalar indicators (|, |-, |+, >, >-, >+)
        block_indicators = frozenset(("|", "|-", "|+", ">", ">-", ">+"))
        if value in block_indicators:
            # Collect indented continuation lines
            parts: list[str] = []
            while i < len(lines):
                cont = lines[i]
                if not cont or cont.startswith("#"):
                    i += 1
                    continue
                # Stop at a non-indented line that looks like a new key
                if not cont[0].isspace() and ":" in cont:
                    break
                parts.append(cont.strip())
                i += 1
            fields[key] = " ".join(parts) if value.startswith(">") else "\n".join(parts)
        else:
            # Simple scalar — strip surrounding quotes
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
    tools: str = "",
) -> str:
    """Render agent content in Claude Code format (.md)."""
    frontmatter = [
        "---",
        f"name: {yaml_scalar(name)}",
        f"description: {yaml_scalar(description)}",
    ]
    if color:
        frontmatter.append(f"color: {yaml_scalar(color)}")
    if tools:
        frontmatter.append(f"tools: {tools}")
    frontmatter.append("---")

    audit = f"<!-- ptm-team-managed: version={MANAGED_VERSION} canonical-commit={commit} generated={generated} -->"
    return "\n".join(frontmatter) + f"\n{audit}\n\n{instructions.rstrip()}\n"


def render_qoder_agent(
    name: str,
    description: str,
    instructions: str,
    commit: str,
    generated: str,
    color: str = "",
    tools: str = "",
    effort: str = "",
) -> str:
    """Render agent content in Qoder format (.md with YAML frontmatter)."""
    frontmatter = [
        "---",
        f"name: {yaml_scalar(name)}",
        f"description: {yaml_scalar(description)}",
    ]
    if effort:
        frontmatter.append(f"effort: {effort}")
    if color:
        frontmatter.append(f"color: {yaml_scalar(color)}")
    if tools:
        frontmatter.append(f"tools: {tools}")
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
    color: str = "",
    tools_raw: str = "",
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
    if color:
        lines.append(f"color = {toml_string(color)}")
    if tools_raw:
        # Codex tools format: same list syntax as Claude
        lines.append(f"tools = {tools_raw}")
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
    if agent_name == "ptm-te":
        return PTM_TE_SKILLS
    return []


def render_ptm_tde_rule_body(platform: str) -> str:
    """Render the short platform rule block installed with ptm-tde."""
    rule_file = PTM_TDE_RULE_FILES[platform]
    sharing = sorted(p for p, f in PTM_TDE_RULE_FILES.items() if f == rule_file)
    labels = {"claude": "Claude Code", "codex": "Codex", "qoder": "Qoder"}
    platform_label = " / ".join(labels[p] for p in sharing)
    return f"""## ptm-tde 工作流程规则

本项目安装了 `ptm-tde` 测试设计 Agent。{platform_label} 中触发 `ptm-tde` / `tde` 相关工作时必须遵守以下流程：

1. **入口识别**：先定位特性工作区。标准输入目录为 `.input/`；若 `.input/` 不在项目根目录，则其父目录是本次特性的 `feature_workspace_root`。
2. **输出隔离**：所有分析产物、运行状态和检查点必须写入 `feature_workspace_root` 下的 `kym/`、`mfq/`、`ppdcs/`、`process/` 等同级目录，不得默认写到仓库根目录。
3. **状态隔离**：每个 `feature_workspace_root/process/STATE.yaml` 只记录该特性的状态；不同 `.input/` 目录之间不得共享或覆盖状态。
4. **多输入保护**：同一仓库发现多个 `.input/` 且用户未指定目标时，必须暂停并要求用户选择，不得用任意启发式默认选择。
5. **阶段顺序**：必须按 `feature-parser → kym → scenario-discovery → MFQ → PPDCS → delivery` 推进，并在 GATE-1 至 GATE-5 通过后再进入下一阶段。
6. **Skill 证据**：声明某个 Skill 已执行时，必须更新 `feature_workspace_root/process/execution/SKILL-CALLS.yaml`，记录 `skill_name / input_refs / output_refs / status=completed / evidence_summary`；只创建 handoff 文件不等于目标 Skill 已完成。
7. **人工确认**：遇到 Gate / 用户确认点时，按当前平台可用交互方式发起确认；无法使用结构化选择时，使用明确文本选项 `approve`、`修改: <具体修改点>`、`reject`。
"""


def render_ptm_te_rule_body(platform: str) -> str:
    """Render the short platform rule block installed with ptm-te."""
    rule_file = RULE_FILES[platform]
    sharing = sorted(p for p, f in RULE_FILES.items() if f == rule_file)
    labels = {"claude": "Claude Code", "codex": "Codex", "qoder": "Qoder"}
    platform_label = " / ".join(labels[p] for p in sharing)
    return f"""## ptm-te 工作流程规则

本项目安装了 `ptm-te` 测试执行工程师 Agent。{platform_label} 中执行 `ptm-te` / `te` 相关工作时必须遵守以下规则：

1. **dry-run 默认门**：默认 `--dry-run`，不修改真实设备；`--execute` 写操作必须经用户单次授权（DQ-01），作为 `runtime_authorization` 决策项独立确认，设计通过不等于运行授权。
2. **凭据安全**：`devices.yaml` 凭据用 `${{ENV_VAR}}` 占位，禁止明文入库；Web 密码经 `--password-env FW_WEB_PASSWORD` 传环境变量名，禁止命令行明文密码。
3. **session 路径**：`--session-file` 必须写入 `~/.local/state/ptm-atomic/` 下，禁止写入仓库目录（ptm-atomic 拒绝 `RUNNER_SESSION_INVALID`）。
4. **执行入口**：用例从 `cases/upload/<特性名>特性测试用例.md` 读取，不直接读 ptm-tde 的 `ppdcs/delivery/`。
5. **op_id 未识别阻塞**：op_mapper 无映射时阻塞，`error_type=OP_NOT_FOUND`，不得跳过或猜测映射，反馈 ptm-tae。
6. **id 来源**：`config` 创建策略路由的响应 `data.policy_route_id` 直接返回 id，`update`/`delete`/`reset-hitcount` 的 `--id` 优先从 config 响应取，verify 查询仅作兜底。
7. **清理回滚**：`config` 的 inverse_op=`delete` 用 config 返回的 `policy_route_id` 清理；`irreversible` 类（reset-hitcount）不回滚，由用例设计接受；不得凭 op 名字推断 rollback 类型。
"""


# block_id -> render 函数（install/uninstall/check 通用，单点扩展）
RULE_BLOCK_RENDERERS = {
    PTM_TDE_RULE_BLOCK_ID: render_ptm_tde_rule_body,
    PTM_TE_RULE_BLOCK_ID: render_ptm_te_rule_body,
}
# agent_name -> rule block_id
AGENT_RULE_BLOCK = {
    "ptm-tde": PTM_TDE_RULE_BLOCK_ID,
    "ptm-te": PTM_TE_RULE_BLOCK_ID,
}


def managed_block_markers(block_id: str, commit: str, generated: str) -> tuple[str, str]:
    start = (
        f"<!-- ptm-team:managed:{block_id}:begin "
        f"v={MANAGED_VERSION} commit={commit} generated={generated} -->"
    )
    end = f"<!-- ptm-team:managed:{block_id}:end -->"
    return start, end


def managed_block_pattern(block_id: str) -> re.Pattern[str]:
    escaped = re.escape(block_id)
    return re.compile(
        rf"<!-- ptm-team:managed:{escaped}:begin\b[^>]*-->.*?"
        rf"<!-- ptm-team:managed:{escaped}:end -->",
        re.DOTALL,
    )


def upsert_managed_rule_block(
    path: Path,
    block_id: str,
    body: str,
    commit: str,
    generated: str,
    dry_run: bool,
) -> None:
    """Create or replace one managed block in a platform rules file."""
    start, end = managed_block_markers(block_id, commit, generated)
    block = f"{start}\n\n{body.rstrip()}\n\n{end}\n"
    old = path.read_text(encoding="utf-8") if path.is_file() else ""
    pattern = managed_block_pattern(block_id)
    if pattern.search(old):
        new = pattern.sub(block.rstrip(), old).rstrip() + "\n"
        action = "更新"
    else:
        prefix = old.rstrip()
        new = f"{prefix}\n\n{block}" if prefix else block
        action = "创建" if not path.exists() else "追加"

    if dry_run:
        print(f"  [DryRun] {action}规则托管块: {path}")
        return
    ensure_directory(path.parent)
    path.write_text(new, encoding="utf-8")
    print(f"  ✓ {action}规则托管块: {path}")


def remove_managed_rule_block(path: Path, block_id: str, dry_run: bool) -> None:
    """Remove one managed block while preserving the rest of the rules file."""
    if not path.is_file():
        return
    old = path.read_text(encoding="utf-8")
    pattern = managed_block_pattern(block_id)
    if not pattern.search(old):
        return
    new = pattern.sub("", old).strip() + "\n"
    if dry_run:
        print(f"  [DryRun] 删除规则托管块: {path}")
        return
    path.write_text(new, encoding="utf-8")
    print(f"  ✓ 删除规则托管块: {path}")


def extract_managed_rule_body(path: Path, block_id: str) -> str | None:
    """Return the normalized body of a managed rule block.

    The block markers include generated timestamps, so drift checks compare only
    the managed body that carries the actual workflow rules.
    """
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8")
    match = managed_block_pattern(block_id).search(content)
    if not match:
        return None
    lines = match.group(0).splitlines()
    if len(lines) < 2:
        return ""
    body = "\n".join(lines[1:-1]).strip()
    return f"{body}\n" if body else ""


def strip_yaml_value(value: str) -> str:
    """Strip a simple YAML scalar value."""
    return value.strip().strip('"').strip("'")


def resource_home() -> Path:
    """Return the shared ptm-team resource home."""
    configured = os.environ.get(RESOURCE_HOME_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_RESOURCE_HOME.expanduser().resolve()


def parse_resource_index(source_dir: Path, resource_type: str = "factor-library") -> dict[str, dict[str, str]]:
    """Parse resource index.yaml for a given resource type.

    Returns a dict keyed by resource identifier (library_id / matrix_id / topo_id).
    """
    # Map resource_type to directory name
    type_to_dir = {
        "factor-library": "factor-libraries",
        "coupling-matrix": "coupling-matrix",
        "network-topology": "network-topology",
    }
    dir_name = type_to_dir.get(resource_type)
    if not dir_name:
        return {}

    index_path = source_dir / "resource" / dir_name / "index.yaml"
    if not index_path.is_file():
        return {}

    items: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    current_id = ""

    # Determine the key field based on resource type
    key_fields = {
        "factor-library": "library_id",
        "coupling-matrix": "matrix_id",
        "network-topology": "topo_id",
    }
    key_field = key_fields.get(resource_type, "library_id")

    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(f"- {key_field}:"):
            current_id = strip_yaml_value(line.split(":", 1)[1])
            current = {key_field: current_id}
            items[current_id] = current
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = strip_yaml_value(value)
    return items


def parse_component_resource_links(source_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Parse resource/component-resource-links.yaml for component resources."""
    links_path = source_dir / "resource" / "component-resource-links.yaml"
    if not links_path.is_file():
        return {}

    links: dict[str, list[dict[str, str]]] = {}
    current_component = ""
    current_resource: dict[str, str] | None = None
    for raw_line in links_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- component_id:"):
            current_component = strip_yaml_value(line.split(":", 1)[1])
            links.setdefault(current_component, [])
            current_resource = None
        elif current_component and line.startswith("- resource_type:"):
            current_resource = {"resource_type": strip_yaml_value(line.split(":", 1)[1])}
            links[current_component].append(current_resource)
        elif current_component and current_resource is not None and ":" in line:
            key, value = line.split(":", 1)
            current_resource[key.strip()] = strip_yaml_value(value)
    return links


def get_component_resources(
    source_dir: Path,
    component_id: str,
    include_recommended: bool = True,
    explicit_resources: list[str] | None = None,
) -> list[dict[str, str]]:
    """Get resources associated with a component.

    Supports resource types: factor-library, coupling-matrix, network-topology.
    When id field is "all", expands to every entry in the type's index.
    """
    links = parse_component_resource_links(source_dir)
    resources = links.get(component_id, [])
    explicit = set(explicit_resources or [])
    selected: list[dict[str, str]] = []

    # Key field mapping per resource type
    type_key = {
        "factor-library": "library_id",
        "coupling-matrix": "matrix_id",
        "network-topology": "topo_id",
    }

    for resource in resources:
        rtype = resource.get("resource_type", "")
        if rtype not in type_key:
            continue
        key_field = type_key[rtype]
        rid = resource.get(key_field, "")
        policy = resource.get("install_policy", "optional")

        # "all" → expand to every entry in the type's index
        if rid == "all":
            index = parse_resource_index(source_dir, rtype)
            for item_id in sorted(index.keys()):
                selected.append({
                    "resource_type": rtype,
                    key_field: item_id,
                    "install_policy": policy,
                })
            continue

        # Handle YAML list syntax like "[tgfw-coupling, tgfw-platform-diff]"
        if isinstance(rid, str) and rid.strip().startswith("["):
            import re
            rid_clean = re.sub(r"[\[\]]", "", str(rid))
            id_list = [x.strip() for x in rid_clean.split(",") if x.strip()]
            index = parse_resource_index(source_dir, rtype)
            for item_id in id_list:
                if item_id in index:
                    selected.append({
                        "resource_type": rtype,
                        key_field: item_id,
                        "install_policy": policy,
                    })
            continue

        if policy == "required" or (policy == "recommended" and include_recommended) or rid in explicit:
            selected.append(resource)

    known = {r.get(type_key.get(r.get("resource_type", ""), "library_id"), "") for r in resources}
    for rid in explicit - known:
        selected.append({
            "resource_type": "factor-library",
            "library_id": rid,
            "install_policy": "explicit",
        })
    return selected


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


def manifest_entry_key(entry: dict) -> tuple[str, str, str, str]:
    """Stable identity for replacing repeated installs of the same asset."""
    return (
        str(entry.get("kind", "")),
        str(entry.get("name", "")),
        str(entry.get("path", "")),
        str(entry.get("managed_block_id", "")),
    )


def replace_manifest_entries(record: dict, new_entries: list[dict]) -> None:
    """Replace existing entries touched by this install, preserving unrelated assets."""
    new_keys = {manifest_entry_key(entry) for entry in new_entries}
    record["entries"] = [
        entry for entry in record.get("entries", [])
        if manifest_entry_key(entry) not in new_keys
    ]
    record["entries"].extend(new_entries)


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


def copy_resource_tree(src_dir: Path, dest_dir: Path, dry_run: bool) -> None:
    """Copy a shared resource tree."""
    if dry_run:
        print(f"  [DryRun] 复制 resource: {src_dir.name} -> {dest_dir}")
        return

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir)
    print(f"  ✓ 安装 resource: {src_dir.name}")


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


def remove_installed_entry(entry: dict, workspace_root: Path, dry_run: bool) -> None:
    """Remove one manifest entry without deleting shared resources by accident."""
    path = workspace_root / entry["remove_path"]
    if entry["kind"] == "rule":
        remove_managed_rule_block(path, entry.get("managed_block_id", ""), dry_run)
    elif entry["kind"] == "resource":
        resource_type = entry.get("resource_type", "resource")
        name = entry.get("name", "")
        print(f"  ✓ 保留共享 resource: {resource_type}:{name} ({path})")
    else:
        remove_path(path, dry_run)


def install_agent(
    platform: str,
    agent_name: str,
    source_dir: Path,
    workspace_root: Path,
    commit: str,
    generated: str,
    dry_run: bool,
    include_recommended_resources: bool = True,
    explicit_resources: list[str] | None = None,
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
    tools = fields.get("tools", "")
    effort = fields.get("effort", "")

    # Render for platform
    agents_dir = workspace_root / PLATFORM_DIRS[platform]["agents"]
    if platform == "claude":
        dest = agents_dir / f"{agent_name}.md"
        rendered = render_claude_agent(agent_name, description, body, commit, generated, color, tools)
    elif platform == "qoder":
        dest = agents_dir / f"{agent_name}.md"
        rendered = render_qoder_agent(agent_name, description, body, commit, generated,
                                      color=color, tools=tools, effort=effort)
    else:
        dest = agents_dir / f"{agent_name}.toml"
        rendered = render_codex_agent(agent_name, description, body, commit, generated,
                                       color=color, tools_raw=tools)

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
        source_hash=sha256_text(content),
        installed_hash=sha256_text(rendered),
    ))

    rule_block_id = AGENT_RULE_BLOCK.get(agent_name)
    if rule_block_id:
        rule_file = workspace_root / RULE_FILES[platform]
        rule_body = RULE_BLOCK_RENDERERS[rule_block_id](platform)
        upsert_managed_rule_block(
            rule_file,
            rule_block_id,
            rule_body,
            commit,
            generated,
            dry_run,
        )
        entries.append(ManifestEntry(
            kind="rule",
            name=f"{agent_name}:{rule_block_id}",
            path=str(rule_file.relative_to(workspace_root)),
            remove_path=str(rule_file.relative_to(workspace_root)),
            managed_block_id=rule_block_id,
            source_hash=sha256_text(rule_body),
            installed_hash=sha256_text(rule_body),
            installed_for=[agent_name],
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
                source_hash=sha256_directory(skill_src),
                installed_hash=sha256_directory(skill_src),
            ))

    # Install associated shared resources.
    resources = get_component_resources(
        source_dir,
        agent_name,
        include_recommended=include_recommended_resources,
        explicit_resources=explicit_resources,
    )
    if resources:
        print(f"\n安装 {agent_name} 关联的 {len(resources)} 个公共 resources:")

        links_src = source_dir / "resource" / "component-resource-links.yaml"
        links_dest_root = resource_home()
        links_dest = links_dest_root / "component-resource-links.yaml"
        if dry_run:
            print(f"  [DryRun] 复制 component-resource-links: {links_src} -> {links_dest}")
        elif links_src.is_file():
            ensure_directory(links_dest_root)
            shutil.copy2(links_src, links_dest)
            print("  ✓ 复制 component-resource-links")
        if links_src.is_file():
            links_hash = sha256_file_set(source_dir / "resource", ["component-resource-links.yaml"])
            entries.append(ManifestEntry(
                kind="resource",
                name="component-resource-links",
                path=str(links_dest_root),
                remove_path=str(links_dest_root),
                resource_type="resource-root",
                source_hash=links_hash,
                installed_hash=links_hash if dry_run else sha256_file_set(links_dest_root, ["component-resource-links.yaml"]),
                installed_for=[agent_name],
                source_files=["component-resource-links.yaml"],
                resource_files=["component-resource-links.yaml"],
            ))

        # Group resources by type
        by_type: dict[str, list[dict[str, str]]] = {}
        for r in resources:
            rtype = r.get("resource_type", "factor-library")
            by_type.setdefault(rtype, []).append(r)

        # Resource type → directory name mapping
        type_dir = {
            "factor-library": "factor-libraries",
            "coupling-matrix": "coupling-matrix",
            "network-topology": "network-topology",
        }
        # Resource type → key field mapping
        type_key = {
            "factor-library": "library_id",
            "coupling-matrix": "matrix_id",
            "network-topology": "topo_id",
        }

        for rtype, rlist in by_type.items():
            if rtype not in type_dir:
                continue
            key_field = type_key[rtype]
            dir_name = type_dir[rtype]
            index = parse_resource_index(source_dir, rtype)

            src_root = source_dir / "resource" / dir_name
            dest_root = resource_home() / dir_name

            # Copy index.yaml
            index_src = src_root / "index.yaml"
            index_dest = dest_root / "index.yaml"
            if dry_run:
                print(f"  [DryRun] 复制 {rtype} index: {index_src} -> {index_dest}")
            else:
                ensure_directory(dest_root)
                if index_src.is_file():
                    shutil.copy2(index_src, index_dest)
                    print(f"  ✓ 复制 {rtype} index")

            for resource in rlist:
                rid = resource.get(key_field, "")
                if not rid:
                    continue
                meta = index.get(rid, {})
                source_files: list[str] = []
                installed_files: list[str] = []

                if rtype == "factor-library":
                    # Existing: copy individual library subdirectory
                    lib_file = meta.get("path", f"{rid}/factor-library.yaml")
                    lib_dir = src_root / Path(lib_file).parts[0]
                    if not lib_dir.is_dir():
                        fail(f"公共因子库不存在: {rid} ({lib_dir})")
                    dest = dest_root / lib_dir.name
                    source_files = [
                        (lib_dir / rel).relative_to(src_root).as_posix()
                        for rel in relative_files_under(lib_dir)
                    ]
                    installed_files = [
                        (dest / rel).relative_to(dest_root).as_posix()
                        for rel in relative_files_under(lib_dir)
                    ]
                    copy_resource_tree(lib_dir, dest, dry_run)
                elif rtype == "coupling-matrix":
                    # Copy individual YAML files listed in index source field
                    src_file = meta.get("source", "")
                    if src_file:
                        src_path = src_root / src_file
                        if src_path.is_file():
                            dest = dest_root / src_file
                            source_files.append(src_file)
                            installed_files.append(src_file)
                            if dry_run:
                                print(f"  [DryRun] 复制: {src_path} -> {dest}")
                            else:
                                shutil.copy2(src_path, dest)
                                print(f"  ✓ 安装 coupling-matrix: {src_file}")
                    # Also copy feature_tree if referenced
                    ft_file = meta.get("feature_tree", "")
                    if ft_file:
                        ft_path = src_root / ft_file
                        if ft_path.is_file():
                            dest = dest_root / ft_file
                            source_files.append(ft_file)
                            installed_files.append(ft_file)
                            if dry_run:
                                print(f"  [DryRun] 复制: {ft_path} -> {dest}")
                            else:
                                shutil.copy2(ft_path, dest)
                elif rtype == "network-topology":
                    # Copy markdown files listed in index source field
                    for field in ("source", "spec", "collection"):
                        src_file = meta.get(field, "")
                        if src_file:
                            src_path = src_root / src_file
                            if src_path.is_file():
                                dest = dest_root / src_file
                                source_files.append(src_file)
                                installed_files.append(src_file)
                                if dry_run:
                                    print(f"  [DryRun] 复制: {src_path} -> {dest}")
                                else:
                                    shutil.copy2(src_path, dest)
                                    print(f"  ✓ 安装 network-topology: {src_file}")

                source_hash = sha256_file_set(src_root, source_files) if source_files else ""
                installed_hash = (
                    source_hash if dry_run else sha256_file_set(dest_root, installed_files)
                ) if installed_files else ""

                entries.append(ManifestEntry(
                    kind="resource",
                    name=rid,
                    path=str(dest_root),
                    remove_path=str(dest_root),
                    resource_type=rtype,
                    source_hash=source_hash,
                    installed_hash=installed_hash,
                    installed_for=[agent_name],
                    source_files=source_files,
                    resource_files=installed_files,
                ))

    return entries


def manifest_entry_to_dict(entry: ManifestEntry) -> dict:
    payload = {
        "kind": entry.kind,
        "name": entry.name,
        "path": entry.path,
        "remove_path": entry.remove_path,
    }
    if entry.resource_type:
        payload["resource_type"] = entry.resource_type
    if entry.managed_block_id:
        payload["managed_block_id"] = entry.managed_block_id
    if entry.source_hash:
        payload["source_hash"] = entry.source_hash
    if entry.installed_hash:
        payload["installed_hash"] = entry.installed_hash
    if entry.installed_for:
        payload["installed_for"] = entry.installed_for
    if entry.source_files:
        payload["source_files"] = entry.source_files
    if entry.resource_files:
        payload["resource_files"] = entry.resource_files
    return payload


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
                    source_hash=sha256_directory(skill_src),
                    installed_hash=sha256_directory(skill_src),
                ))
        else:
            print("没有新的 skill 需要安装")
    else:
        print("未选择任何 skill")

    return entries


def has_other_platform_rule(manifest: dict, platform: str, agent_name: str) -> bool:
    """Check if another platform sharing the same rule file still has the rule installed."""
    rule_file = PTM_TDE_RULE_FILES[platform]
    sharing = [p for p, f in PTM_TDE_RULE_FILES.items() if f == rule_file and p != platform]
    for other in sharing:
        other_record = find_install_record(manifest, other)
        if other_record:
            for entry in other_record.get("entries", []):
                if entry.get("kind") == "rule" and agent_name in entry.get("installed_for", []):
                    return True
    return False


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

    # Filter entries for this agent, its skills, and resources installed for it.
    entries_to_remove = []
    remaining_entries = []

    for entry in record.get("entries", []):
        if entry["kind"] == "agent" and entry["name"] == agent_name:
            entries_to_remove.append(entry)
        elif entry["kind"] == "skill" and entry["name"] in get_agent_skills(agent_name):
            entries_to_remove.append(entry)
        elif entry["kind"] == "resource" and agent_name in entry.get("installed_for", []):
            installed_for = [x for x in entry.get("installed_for", []) if x != agent_name]
            if installed_for:
                updated = dict(entry)
                updated["installed_for"] = installed_for
                remaining_entries.append(updated)
            else:
                entries_to_remove.append(entry)
        elif entry["kind"] == "rule" and agent_name in entry.get("installed_for", []):
            if has_other_platform_rule(manifest, platform, agent_name):
                print(f"  ✓ 保留共享规则块: {entry.get('managed_block_id', '')} (其他平台仍在使用)")
            else:
                entries_to_remove.append(entry)
        else:
            remaining_entries.append(entry)

    if not entries_to_remove:
        fail(f"未找到 agent {agent_name} 的安装记录")

    # Remove files
    print(f"卸载 agent {agent_name} 及其 skills:")
    for entry in entries_to_remove:
        remove_installed_entry(entry, workspace_root, dry_run)

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
        remove_installed_entry(entry, workspace_root, dry_run)

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
    resources = [e for e in record.get("entries", []) if e["kind"] == "resource"]
    rules = [e for e in record.get("entries", []) if e["kind"] == "rule"]

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

    if resources:
        print(f"\n  Resources ({len(resources)}):")
        for r in resources:
            resource_type = r.get("resource_type", "resource")
            installed_for = ", ".join(r.get("installed_for", [])) or "unknown"
            print(f"    - {resource_type}:{r['name']} (installed_for={installed_for})")

    if rules:
        print(f"\n  Rules ({len(rules)}):")
        for r in rules:
            print(f"    - {r['name']} -> {r['path']}")


def current_source_hash(entry: dict, source_dir: Path, platform: str) -> str | None:
    """Compute the current source-side hash for drift checks."""
    kind = entry.get("kind", "")
    name = entry.get("name", "")
    if kind == "agent":
        source = source_dir / "agents" / f"{name}.md"
        return sha256_text(source.read_text(encoding="utf-8")) if source.is_file() else None
    if kind == "skill":
        source = source_dir / "skills" / name
        return sha256_directory(source) if source.is_dir() else None
    if kind == "rule":
        block_id = entry.get("managed_block_id", "")
        renderer = RULE_BLOCK_RENDERERS.get(block_id)
        if renderer:
            return sha256_text(renderer(platform))
        return None
    if kind == "resource":
        type_dir = {
            "factor-library": "factor-libraries",
            "coupling-matrix": "coupling-matrix",
            "network-topology": "network-topology",
        }
        resource_type = entry.get("resource_type", "")
        root = source_dir / "resource" / type_dir.get(resource_type, "")
        source_files = entry.get("source_files", [])
        if not root.is_dir() or not isinstance(source_files, list) or not source_files:
            return None
        digest = sha256_file_set(root, [str(path) for path in source_files])
        return digest or None
    return None


def current_installed_hash(entry: dict, workspace_root: Path) -> str | None:
    """Compute the installed-side hash for drift checks."""
    kind = entry.get("kind", "")
    path = workspace_root / entry.get("path", "")
    if kind == "skill":
        return sha256_directory(path) if path.is_dir() else None
    if kind == "rule":
        body = extract_managed_rule_body(path, entry.get("managed_block_id", ""))
        return sha256_text(body) if body is not None else None
    if kind == "resource":
        resource_files = entry.get("resource_files", [])
        if not path.is_dir() or not isinstance(resource_files, list) or not resource_files:
            return None
        digest = sha256_file_set(path, [str(item) for item in resource_files])
        return digest or None
    if path.is_file():
        return sha256_file(path)
    return None


def check_installed_drift(
    platform: str,
    source_dir: Path,
    workspace_root: Path,
    manifest: dict,
    agent_name: str = "",
) -> None:
    """Check manifest, source, installed files, and managed rule blocks for drift."""
    record = find_install_record(manifest, platform)
    if record is None:
        fail(f"未找到 {platform} 的安装记录")

    entries = record.get("entries", [])
    if agent_name:
        agent_skills = set(get_agent_skills(agent_name))
        entries = [
            entry for entry in entries
            if (entry.get("kind") == "agent" and entry.get("name") == agent_name)
            or (entry.get("kind") == "skill" and entry.get("name") in agent_skills)
            or (entry.get("kind") == "rule" and agent_name in entry.get("installed_for", []))
            or (entry.get("kind") == "resource" and agent_name in entry.get("installed_for", []))
        ]

    if not entries:
        fail(f"未找到 {platform} 的可检查安装条目")

    issues = 0
    print(f"{platform} 安装漂移检查:")
    for entry in entries:
        kind = entry.get("kind", "")
        name = entry.get("name", "")
        label = f"{kind}:{name}"

        expected_installed = entry.get("installed_hash", "")
        actual_installed = current_installed_hash(entry, workspace_root)
        if actual_installed is None:
            print(f"  MISSING {label} - 目标文件、目录、managed block 或 resource_files 不存在: {entry.get('path', '')}")
            issues += 1
            continue
        if not expected_installed:
            print(f"  MISSING_HASH {label} - manifest 缺少 installed_hash")
            issues += 1
        elif actual_installed != expected_installed:
            print(f"  INSTALLED_DRIFT {label} - 已安装内容与 manifest installed_hash 不一致")
            issues += 1

        expected_source = entry.get("source_hash", "")
        actual_source = current_source_hash(entry, source_dir, platform)
        if actual_source is None:
            print(f"  SOURCE_MISSING {label} - 源资产不存在或不可检查")
            issues += 1
        elif expected_source and actual_source != expected_source:
            print(f"  SOURCE_DRIFT {label} - 源资产已变化，建议重新 install")
            issues += 1
        elif not expected_source:
            print(f"  MISSING_HASH {label} - manifest 缺少 source_hash")
            issues += 1

        if issues == 0 or (
            expected_installed and actual_installed == expected_installed
            and expected_source and actual_source == expected_source
        ):
            print(f"  OK {label}")

    if issues:
        print(f"\n检查完成: 发现 {issues} 个漂移/缺失问题")
        raise SystemExit(2)
    print("\n检查完成: 未发现漂移")


def list_resources(source_dir: Path) -> None:
    """List source resource libraries."""
    for rtype, label, dir_name in [
        ("factor-library", "公共因子库", "factor-libraries"),
        ("coupling-matrix", "耦合矩阵", "coupling-matrix"),
        ("network-topology", "测试组网图", "network-topology"),
    ]:
        items = parse_resource_index(source_dir, rtype)
        if not items:
            continue
        print(f"{label}:")
        for rid, meta in sorted(items.items()):
            print(f"  - {rid}: {meta.get('display_name', '')} ({meta.get('version', 'unknown')})")


def validate_resources(source_dir: Path) -> None:
    """Validate resource index and component links for all resource types."""
    errors: list[str] = []

    # Validate each resource type
    type_configs = [
        ("factor-library", "factor-libraries", "library_id", "factor-library.yaml"),
        ("coupling-matrix", "coupling-matrix", "matrix_id", ""),
        ("network-topology", "network-topology", "topo_id", ""),
    ]

    all_ids: dict[str, set[str]] = {}

    for rtype, dir_name, key_field, default_file in type_configs:
        items = parse_resource_index(source_dir, rtype)
        all_ids[rtype] = set(items.keys())
        if not items:
            continue

        root = source_dir / "resource" / dir_name
        for rid, meta in items.items():
            # Validate source file
            if rtype == "factor-library":
                rel_path = meta.get("path", f"{rid}/{default_file}")
                lib_file = root / rel_path
                if not lib_file.is_file():
                    errors.append(f"{rtype}/{rid}: 缺少 {lib_file}")
                for doc_key in ("library_doc", "groups_doc", "change_log"):
                    doc_rel = meta.get(doc_key, "")
                    if doc_rel and not (root / doc_rel).is_file():
                        errors.append(f"{rtype}/{rid}: 缺少文档 {root / doc_rel}")
            elif rtype in ("coupling-matrix", "network-topology"):
                src_file = meta.get("source", "")
                if src_file and not (root / src_file).is_file():
                    errors.append(f"{rtype}/{rid}: 缺少 {root / src_file}")
                # Also check feature_tree for coupling-matrix
                if rtype == "coupling-matrix":
                    ft = meta.get("feature_tree", "")
                    if ft and not (root / ft).is_file():
                        errors.append(f"{rtype}/{rid}: 缺少特性树 {root / ft}")

    # Validate component-resource-links references
    links = parse_component_resource_links(source_dir)
    for component_id, resources in links.items():
        for resource in resources:
            rtype = resource.get("resource_type", "")
            key_field = {
                "factor-library": "library_id",
                "coupling-matrix": "matrix_id",
                "network-topology": "topo_id",
            }.get(rtype, "library_id")
            rid = resource.get(key_field, "")
            # Skip special keywords
            if str(rid).strip().lower() == "all":
                continue
            if rtype in all_ids:
                # Check YAML list expansion
                import re
                rid_clean = re.sub(r"[\[\]]", "", str(rid))
                id_list = [x.strip() for x in rid_clean.split(",") if x.strip()]
                for item_id in id_list:
                    if item_id not in all_ids.get(rtype, set()):
                        errors.append(f"{component_id}: 未知 {rtype} {item_id}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}", file=sys.stderr)
        raise SystemExit(1)
    print("公共资源校验通过")


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
    install_parser.add_argument("--no-recommended-resources", action="store_true", help="安装 agent 时跳过 recommended resources")
    install_parser.add_argument("--resource", action="append", default=[], help="安装 agent 时额外指定 resource id")

    # uninstall subcommand
    uninstall_parser = subparsers.add_parser("uninstall", help="卸载 agent 或 skill")
    uninstall_parser.add_argument("platform", choices=VALID_PLATFORMS, help="目标平台")
    uninstall_parser.add_argument("--agent", nargs="?", const="", help="卸载 agent")
    uninstall_parser.add_argument("--skill", action="store_true", help="卸载 skill (交互式)")
    uninstall_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    # reinstall subcommand: 先卸载再安装
    reinstall_parser = subparsers.add_parser("reinstall", help="先卸载再安装 agent")
    reinstall_parser.add_argument("platform", choices=VALID_PLATFORMS, help="目标平台")
    reinstall_parser.add_argument("--agent", nargs="?", const="", help="reinstall agent (可指定名称)")
    reinstall_parser.add_argument("--dry-run", action="store_true", help="预览模式")
    reinstall_parser.add_argument("--no-recommended-resources", action="store_true", help="安装 agent 时跳过 recommended resources")
    reinstall_parser.add_argument("--resource", action="append", default=[], help="安装 agent 时额外指定 resource id")

    # check subcommand
    check_parser = subparsers.add_parser("check", help="检查已安装资产是否漂移")
    check_parser.add_argument("platform", choices=VALID_PLATFORMS, help="目标平台")
    check_parser.add_argument("--agent", nargs="?", const="", help="仅检查指定 agent 及其关联资产")

    # resource subcommand
    resource_parser = subparsers.add_parser("resource", help="查询或校验公共资源")
    resource_subparsers = resource_parser.add_subparsers(dest="resource_command", help="resource 命令")
    resource_subparsers.add_parser("list", help="列出源目录中的公共资源")
    resource_subparsers.add_parser("path", help="显示用户级公共资源目录")
    resource_subparsers.add_parser("validate", help="校验源目录中的公共资源索引和关联")

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
    if hasattr(args, "platform"):
        print(f"平台: {args.platform}")
    print()

    if args.command == "resource":
        if args.resource_command == "list":
            list_resources(source_dir)
        elif args.resource_command == "path":
            print(resource_home())
        elif args.resource_command == "validate":
            validate_resources(source_dir)
        else:
            fail("请指定 resource 子命令: list、path 或 validate")
        return

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
                include_recommended_resources=not args.no_recommended_resources,
                explicit_resources=args.resource,
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
                replace_manifest_entries(record, [manifest_entry_to_dict(e) for e in entries])
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
                replace_manifest_entries(record, [manifest_entry_to_dict(e) for e in entries])
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

    elif args.command == "reinstall":
        # reinstall = 卸载（若已安装）+ 安装
        if args.agent is None:
            fail("reinstall 目前仅支持 --agent，请指定 --agent <名称>")

        agent_name = args.agent if args.agent else "ptm-tde"
        agent_name = resolve_agent_name(agent_name)

        # 1. 卸载：仅当该 agent 已安装时执行，避免 uninstall_agent 对"未找到记录"fail
        existing = find_install_record(manifest, args.platform)
        if existing and existing.get("status") == "installed" and any(
            e.get("kind") == "agent" and e.get("name") == agent_name
            for e in existing.get("entries", [])
        ):
            print(f"\n=== reinstall: 卸载 {agent_name} ===")
            uninstall_agent(args.platform, agent_name, workspace_root, manifest, args.dry_run)
        else:
            print(f"未安装 {agent_name}，跳过卸载，直接安装")

        # 2. 安装
        print(f"\n=== reinstall: 安装 {agent_name} ===")
        entries = install_agent(
            args.platform, agent_name, source_dir, workspace_root,
            commit, generated, args.dry_run,
            include_recommended_resources=not args.no_recommended_resources,
            explicit_resources=args.resource,
        )

        # 3. 更新 manifest（与 install 分支一致）
        if not args.dry_run and entries:
            record = find_install_record(manifest, args.platform) or {
                "platform": args.platform,
                "scope": "project",
                "status": "installed",
                "installed_at": generated,
                "workspace_root": str(workspace_root),
                "entries": [],
            }
            record["entries"].extend([manifest_entry_to_dict(e) for e in entries])
            upsert_install_record(manifest, record)
            save_manifest(manifest_path, manifest)
        return

    elif args.command == "check":
        agent_name = ""
        if args.agent is not None:
            agent_name = args.agent if args.agent else "ptm-tde"
            agent_name = resolve_agent_name(agent_name)
        check_installed_drift(args.platform, source_dir, workspace_root, manifest, agent_name)


if __name__ == "__main__":
    main()
