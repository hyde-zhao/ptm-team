#!/usr/bin/env python3
"""Create field-feedback records for post-release ptm-tde usage.

The tool intentionally writes Markdown files only. It does not triage or fix
issues by itself; it gives every real-world run, failure, gap, and regression
asset a stable file to reference.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path


CATEGORIES = (
    "workflow",
    "artifact-schema",
    "semantic-quality",
    "checkpoint",
    "install",
    "runtime-env",
    "docs",
    "eval-gap",
)
SEVERITIES = ("BLOCKER", "HIGH", "MEDIUM", "LOW", "INFO")
RESULTS = ("pass", "fail", "blocked", "partial", "skipped")
COVERAGE_STATUS = (
    "covered-and-detected",
    "covered-but-not-detected",
    "uncovered-scenario",
    "uncovered-mfq",
    "uncovered-design",
    "uncovered-delivery",
    "environment-only",
    "needs-confirmation",
)
MISSING_STAGES = (
    "n/a",
    "scenario",
    "mfq",
    "design",
    "delivery",
    "checkpoint",
    "eval",
    "install",
    "runtime-env",
    "docs",
)
DEFAULT_COLLECT_PATHS = (
    "process/STATE.yaml",
    "process/checkpoints",
    "process/checks",
    "process/execution",
    "ppdcs/coverage",
    "ppdcs/delivery",
    "ppdcs/pc",
    "ppdcs/ppdcs",
)
CONFIG_FILES = (
    ".ptm-field-feedback.yaml",
    ".ptm-field-feedback.yml",
    ".ptm-field-feedback.json",
)
DEFAULT_FEEDBACK_CONFIG = {
    "local_repo": "../ptm-team-feedback",
    "remote_url": "",
    "branch": "main",
    "dest": "tde-feedback",
    "inbox_dest": "process/field-feedback/inbox/gitlab-materials",
    "remote": "origin",
}


def today(value: str) -> str:
    return value or dt.date.today().strftime("%Y%m%d")


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs(root: Path) -> None:
    for rel in (
        "process/field-feedback/runs",
        "process/field-feedback/collections",
        "process/field-feedback/inbox",
        "process/field-feedback/gap-analysis",
        "process/issues",
        "evals",
        "docs/quality",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)


def next_id(directory: Path, prefix: str, date_value: str) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(prefix)}-{re.escape(date_value)}-(\d{{3}})\.md$")
    max_seen = 0
    for path in directory.glob(f"{prefix}-{date_value}-*.md"):
        match = pattern.match(path.name)
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return f"{prefix}-{date_value}-{max_seen + 1:03d}"


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_unique_line(path: Path, header: str, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = header.rstrip() + "\n"
        if not line:
            path.write_text(text, encoding="utf-8")
            return
    if line not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += line.rstrip() + "\n"
        path.write_text(text, encoding="utf-8")


def md_list(values: list[str]) -> str:
    if not values:
        return "- N/A"
    return "\n".join(f"- `{value}`" for value in values)


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    normalized = normalized.strip("-._")
    return normalized or "unknown"


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def strip_scalar(value: str) -> str:
    value = value.strip()
    if "#" in value:
        before_comment = value.split("#", 1)[0].rstrip()
        if before_comment:
            value = before_comment
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_simple_yaml(text: str) -> dict[str, str]:
    """Parse the small YAML subset used by .ptm-field-feedback.yaml."""
    section = ""
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = strip_scalar(raw_value)
        if indent == 0 and not value:
            section = key
            continue
        if section == "feedback_repo" and indent > 0:
            values[key] = value
        elif indent == 0:
            values[key] = value
    return values


def load_feedback_config(root: Path) -> dict[str, str]:
    config = dict(DEFAULT_FEEDBACK_CONFIG)
    for name in CONFIG_FILES:
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                feedback_repo = parsed.get("feedback_repo", parsed)
                if isinstance(feedback_repo, dict):
                    config.update({str(k): str(v) for k, v in feedback_repo.items()})
        else:
            config.update(parse_simple_yaml(text))
        config["config_path"] = str(path)
        break
    return config


def resolve_under_root(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def configured_value(args: argparse.Namespace, name: str, config: dict[str, str], default: str = "") -> str:
    value = getattr(args, name, "")
    return value or config.get(name, default)


def copy_material(src_root: Path, rel: str, dest_root: Path) -> str:
    src = src_root / rel
    if not src.exists():
        return "missing"
    dest = dest_root / rel
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return "copied"


def collect_id(feature: str, date_value: str, root: Path) -> str:
    prefix = f"COLLECT-{date_value}-{slugify(feature)}"
    directory = root / "process/field-feedback/collections"
    directory.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d{{3}})$")
    max_seen = 0
    for path in directory.iterdir():
        if not path.is_dir():
            continue
        match = pattern.match(path.name)
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return f"{prefix}-{max_seen + 1:03d}"


def command_init(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    ensure_dirs(root)
    append_unique_line(
        root / "process/field-feedback/RUN-EXEC-INDEX.md",
        "# RUN-EXEC Index\n\n| Run | Feature | Result | Gate | Issue Count | Path |\n|---|---|---|---|---:|---|",
        "",
    )
    append_unique_line(
        root / "process/field-feedback/FIELD-ISSUE-REGISTER.md",
        "# Field Issue Register\n\n| ISSUE | Run | Feature | Category | Severity | Stage | Status | Coverage Status | Regression Asset | Path |\n|---|---|---|---|---|---|---|---|---|---|",
        "",
    )
    append_unique_line(
        root / "evals/EVAL-BACKLOG.md",
        "# Eval Backlog\n\n| Backlog ID | Source ISSUE | Defect Class | Current Coverage | Proposed Eval | Priority | Status |\n|---|---|---|---|---|---|---|",
        "",
    )
    dashboard = root / "docs/quality/FIELD-QUALITY-DASHBOARD.md"
    if not dashboard.exists():
        dashboard.write_text(
            "# Field Quality Dashboard\n\n"
            f"- generated_at: `{iso_now()}`\n"
            "- status: `initialized`\n\n"
            "Run `uv run python script/field_feedback.py dashboard --root .` to refresh weekly metrics.\n",
            encoding="utf-8",
        )
    print(f"initialized: {root / 'process/field-feedback'}")


def create_collection(args: argparse.Namespace) -> Path:
    root = Path(args.root).resolve()
    workspace = Path(args.workspace).resolve()
    ensure_dirs(root)
    if not workspace.is_dir():
        raise SystemExit(f"workspace does not exist or is not a directory: {workspace}")

    date_value = today(args.date)
    collection_id = args.collection_id or collect_id(args.feature, date_value, root)
    collection_root = root / "process/field-feedback/collections" / collection_id
    artifacts_root = collection_root / "artifacts"
    if collection_root.exists():
        raise SystemExit(f"collection already exists: {collection_root}")
    artifacts_root.mkdir(parents=True, exist_ok=True)

    rel_paths = list(DEFAULT_COLLECT_PATHS)
    rel_paths.extend(args.include)
    copied: list[dict[str, str]] = []
    for rel in rel_paths:
        status = copy_material(workspace, rel, artifacts_root)
        copied.append({"path": rel, "status": status})

    feedback = collection_root / "FEEDBACK.md"
    feedback.write_text(
        f"""# ptm-tde Field Feedback Collection

| Field | Value |
|---|---|
| collection_id | `{collection_id}` |
| feature | `{args.feature}` |
| platform | `{args.platform}` |
| workspace | `{workspace}` |
| result | `{args.result}` |
| gate | `{args.gate}` |
| collected_at | `{iso_now()}` |

## Summary

{args.summary or "TBD"}

## Expected Result

{args.expected or "TBD"}

## Actual Result

{args.actual or "TBD"}

## Command Or Entry

```text
{args.command or "N/A"}
```

## Notes

{args.notes or "N/A"}
""",
        encoding="utf-8",
    )

    manifest = {
        "collection_id": collection_id,
        "feature": args.feature,
        "platform": args.platform,
        "workspace": str(workspace),
        "result": args.result,
        "gate": args.gate,
        "summary": args.summary,
        "collected_at": iso_now(),
        "materials": copied,
    }
    (collection_root / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return collection_root


def command_collect(args: argparse.Namespace) -> None:
    collection_root = create_collection(args)
    run_exec_path = create_run_exec_for_collection(args, collection_root)
    print(collection_root)
    print(f"run_exec: {run_exec_path}")


def publish_collection(args: argparse.Namespace) -> Path:
    root = Path(getattr(args, "root", ".")).resolve()
    config = load_feedback_config(root)
    collection = Path(args.collection).resolve()
    target_repo_value = getattr(args, "target_repo", "") or config.get("local_repo", DEFAULT_FEEDBACK_CONFIG["local_repo"])
    branch = configured_value(args, "branch", config, "branch")
    dest_prefix = configured_value(args, "dest", config, "dest")
    remote = configured_value(args, "remote", config, "remote")
    target_repo = resolve_under_root(root, target_repo_value)
    if not collection.is_dir():
        raise SystemExit(f"collection does not exist: {collection}")
    if not (target_repo / ".git").is_dir():
        raise SystemExit(f"target repo is not a git repository: {target_repo}")

    if branch:
        checkout = run_git(["checkout", branch], target_repo)
        if checkout.returncode != 0:
            create = run_git(["checkout", "-B", branch], target_repo)
            if create.returncode != 0:
                raise SystemExit(create.stderr or create.stdout)

    manifest_path = collection / "MANIFEST.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        feature = slugify(str(manifest.get("feature", "unknown")))
        collection_id = str(manifest.get("collection_id", collection.name))
    else:
        feature = "unknown"
        collection_id = collection.name

    dest_rel = Path(dest_prefix) / feature / collection_id
    dest = target_repo / dest_rel
    if dest.exists() and not args.replace:
        raise SystemExit(f"destination already exists; use --replace: {dest}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(collection, dest)

    if args.commit or args.push:
        add = run_git(["add", str(dest_rel)], target_repo)
        if add.returncode != 0:
            raise SystemExit(add.stderr or add.stdout)
        commit = run_git(["commit", "-m", args.message or f"Add field feedback {collection_id}"], target_repo)
        if commit.returncode != 0 and "nothing to commit" not in (commit.stderr + commit.stdout).lower():
            raise SystemExit(commit.stderr or commit.stdout)
    if args.push:
        push_args = ["push", remote]
        if branch:
            push_args.append(branch)
        push = run_git(push_args, target_repo)
        if push.returncode != 0:
            raise SystemExit(push.stderr or push.stdout)
    return target_repo / dest_rel


def command_publish(args: argparse.Namespace) -> None:
    print(publish_collection(args))


def command_pull(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = load_feedback_config(root)
    ensure_dirs(root)
    source_repo = args.source_repo or config.get("remote_url", "")
    branch = configured_value(args, "branch", config, "branch")
    remote = configured_value(args, "remote", config, "remote")
    dest_value = args.dest or config.get("inbox_dest", "")
    dest = resolve_under_root(root, dest_value) if dest_value else root / "process/field-feedback/inbox/gitlab-materials"
    if not source_repo:
        raise SystemExit("source repo is required; pass --source-repo or configure feedback_repo.remote_url")
    if dest.exists() and (dest / ".git").is_dir():
        if branch:
            checkout = run_git(["checkout", branch], dest)
            if checkout.returncode != 0:
                raise SystemExit(checkout.stderr or checkout.stdout)
        pull = run_git(["pull", "--ff-only", remote, branch] if branch else ["pull", "--ff-only"], dest)
        if pull.returncode != 0:
            raise SystemExit(pull.stderr or pull.stdout)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        clone_args = ["clone"]
        if branch:
            clone_args.extend(["--branch", branch])
        clone_args.extend([source_repo, str(dest)])
        clone = subprocess.run(
            ["git", *clone_args],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if clone.returncode != 0:
            raise SystemExit(clone.stderr or clone.stdout)
    print(dest)


def ensure_git_identity(repo: Path) -> None:
    email = run_git(["config", "user.email"], repo)
    if email.returncode != 0 or not email.stdout.strip():
        run_git(["config", "user.email", "ptm-team-feedback@example.invalid"], repo)
    name = run_git(["config", "user.name"], repo)
    if name.returncode != 0 or not name.stdout.strip():
        run_git(["config", "user.name", "ptm-team Feedback Bot"], repo)


def command_repo_init(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    config = load_feedback_config(root)
    local_repo = resolve_under_root(root, args.local_repo or config["local_repo"])
    remote_url = args.remote_url or config.get("remote_url", "")
    branch = args.branch or config.get("branch", "main")
    remote = args.remote or config.get("remote", "origin")
    if not remote_url:
        raise SystemExit("remote url is required; pass --remote-url or configure feedback_repo.remote_url")

    local_repo.mkdir(parents=True, exist_ok=True)
    if not (local_repo / ".git").is_dir():
        init = run_git(["init"], local_repo)
        if init.returncode != 0:
            raise SystemExit(init.stderr or init.stdout)

    existing_remote = run_git(["remote", "get-url", remote], local_repo)
    if existing_remote.returncode != 0:
        add_remote = run_git(["remote", "add", remote, remote_url], local_repo)
        if add_remote.returncode != 0:
            raise SystemExit(add_remote.stderr or add_remote.stdout)
    elif existing_remote.stdout.strip() != remote_url:
        if not args.replace_remote:
            raise SystemExit(
                f"remote {remote} already points to {existing_remote.stdout.strip()}; "
                "use --replace-remote to update it"
            )
        set_remote = run_git(["remote", "set-url", remote, remote_url], local_repo)
        if set_remote.returncode != 0:
            raise SystemExit(set_remote.stderr or set_remote.stdout)

    readme = local_repo / "README.md"
    if not readme.exists():
        readme.write_text(
            "# ptm-team field feedback\n\n"
            "This repository stores ptm-tde field feedback collection packages.\n\n"
            "Directory convention:\n\n"
            "```text\n"
            "tde-feedback/<feature>/<COLLECT-ID>/\n"
            "```\n",
            encoding="utf-8",
        )

    ensure_git_identity(local_repo)
    add = run_git(["add", "README.md"], local_repo)
    if add.returncode != 0:
        raise SystemExit(add.stderr or add.stdout)
    commit = run_git(["commit", "-m", "Initialize ptm-team feedback repository"], local_repo)
    if commit.returncode != 0 and "nothing to commit" not in (commit.stderr + commit.stdout).lower():
        raise SystemExit(commit.stderr or commit.stdout)
    branch_result = run_git(["branch", "-M", branch], local_repo)
    if branch_result.returncode != 0:
        raise SystemExit(branch_result.stderr or branch_result.stdout)
    if args.push:
        push = run_git(["push", "-uf", remote, branch], local_repo)
        if push.returncode != 0:
            raise SystemExit(push.stderr or push.stdout)
    print(local_repo)


def command_submit(args: argparse.Namespace) -> None:
    collection = create_collection(args)
    args.collection = str(collection)
    published = publish_collection(args)
    run_exec_path = create_run_exec_for_collection(args, collection, published)
    print(f"collection: {collection}")
    print(f"published: {published}")
    print(f"run_exec: {run_exec_path}")


def write_run_exec_record(
    *,
    root: Path,
    date_value: str,
    run_id: str,
    feature: str,
    platform: str,
    agent_version: str,
    workspace: str,
    result: str,
    gate: str,
    summary: str,
    command: str,
    input_docs: list[str],
    evidence: list[str],
    notes: str,
    expected: str = "",
    actual: str = "",
    collection_path: str = "",
    published_path: str = "",
) -> Path:
    ensure_dirs(root)
    rel_path = Path("process/field-feedback/runs") / f"{run_id}.md"
    path = root / rel_path
    collection_value = collection_path or "N/A"
    published_value = published_path or "N/A"
    content = f"""---
run_id: "{run_id}"
feature: "{feature}"
platform: "{platform}"
agent_version: "{agent_version}"
workspace: "{workspace}"
result: "{result}"
gate_reached: "{gate}"
collection_path: "{collection_value}"
published_path: "{published_value}"
created_at: "{iso_now()}"
---

# {run_id} Field Run

## Environment Snapshot

| Field | Value |
|---|---|
| feature | `{feature}` |
| platform | `{platform}` |
| agent_version | `{agent_version}` |
| workspace | `{workspace}` |
| gate_reached | `{gate}` |
| result | `{result}` |
| collection_path | `{collection_value}` |
| published_path | `{published_value}` |

## Input Documents

{md_list(input_docs)}

## Command Or Entry

```text
{command or "N/A"}
```

## Task Results

| Task | Result | Expected Result | Actual Result | Evidence |
|---|---|---|---|---|
| {summary} | {result} | {expected or "TBD"} | {actual or "TBD"} | {", ".join(evidence) if evidence else "N/A"} |

## Feedback Collection

| Field | Value |
|---|---|
| collection_path | `{collection_value}` |
| published_path | `{published_value}` |

## Issues

| ISSUE | Category | Severity | Status |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## Evidence

{md_list(evidence)}

## Notes

{notes or "N/A"}
"""
    write_new(path, content)
    append_unique_line(
        root / "process/field-feedback/RUN-EXEC-INDEX.md",
        "# RUN-EXEC Index\n\n| Run | Feature | Result | Gate | Issue Count | Path |\n|---|---|---|---|---:|---|",
        f"| {run_id} | {feature} | {result} | {gate} | 0 | `{rel_path}` |",
    )
    return path


def update_collection_manifest(collection: Path, **fields: str) -> None:
    manifest_path = collection / "MANIFEST.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({key: value for key, value in fields.items() if value})
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def create_run_exec_for_collection(
    args: argparse.Namespace,
    collection: Path,
    published: Path | None = None,
) -> Path:
    root = Path(args.root).resolve()
    date_value = today(args.date)
    run_id = next_id(root / "process/field-feedback/runs", "RUN-EXEC", date_value)
    evidence = [str(collection)]
    if published is not None:
        evidence.append(str(published))
    run_exec_path = write_run_exec_record(
        root=root,
        date_value=date_value,
        run_id=run_id,
        feature=args.feature,
        platform=args.platform,
        agent_version=getattr(args, "agent_version", "unknown"),
        workspace=str(Path(args.workspace).resolve()),
        result=args.result,
        gate=args.gate,
        summary=args.summary,
        command=args.command,
        input_docs=[],
        evidence=evidence,
        notes=args.notes,
        expected=args.expected,
        actual=args.actual,
        collection_path=str(collection),
        published_path=str(published) if published is not None else "",
    )
    update_collection_manifest(
        collection,
        run_exec_id=run_id,
        run_exec_path=str(run_exec_path),
        published_path=str(published) if published is not None else "",
    )
    return run_exec_path


def command_run_exec(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    date_value = today(args.date)
    run_id = args.run_id or next_id(root / "process/field-feedback/runs", "RUN-EXEC", date_value)
    path = write_run_exec_record(
        root=root,
        date_value=date_value,
        run_id=run_id,
        feature=args.feature,
        platform=args.platform,
        agent_version=args.agent_version,
        workspace=args.workspace,
        result=args.result,
        gate=args.gate,
        summary=args.summary,
        command=args.command,
        input_docs=args.input_doc,
        evidence=args.evidence,
        notes=args.notes,
        expected=args.expected,
        actual=args.actual,
        collection_path=args.collection,
        published_path=args.published_path,
    )
    print(path)


def command_issue(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    ensure_dirs(root)
    date_value = today(args.date)
    issue_id = args.issue_id or next_id(root / "process/issues", "ISSUE", date_value)
    rel_path = Path("process/issues") / f"{issue_id}.md"
    path = root / rel_path
    content = f"""---
issue_id: "{issue_id}"
source_run: "{args.run}"
feature: "{args.feature}"
category: "{args.category}"
severity: "{args.severity}"
stage: "{args.stage}"
status: "new"
coverage_status: "needs-triage"
owner: "{args.owner}"
needs_cr: false
regression_required: true
created_at: "{iso_now()}"
---

# {issue_id} {args.summary}

## Symptom

{args.symptom or args.summary}

## Expected Result

{args.expected or "TBD"}

## Actual Result

{args.actual or "TBD"}

## Evidence

{md_list(args.evidence)}

## Triage

| Field | Value |
|---|---|
| category | `{args.category}` |
| severity | `{args.severity}` |
| affected_stage | `{args.stage}` |
| owner | `{args.owner}` |
| status | `new` |
| needs_cr | `false` |

## Coverage Gap Decision

| Field | Value |
|---|---|
| coverage_status | `needs-triage` |
| missing_stage | `TBD` |
| missing_asset | `TBD` |
| suggested_backfill | `TBD` |

## Regression Assets

| Asset | Status | Evidence |
|---|---|---|
| TBD | pending | TBD |

## Route Decision

TBD
"""
    write_new(path, content)
    append_unique_line(
        root / "process/field-feedback/FIELD-ISSUE-REGISTER.md",
        "# Field Issue Register\n\n| ISSUE | Run | Feature | Category | Severity | Stage | Status | Coverage Status | Regression Asset | Path |\n|---|---|---|---|---|---|---|---|---|---|",
        f"| {issue_id} | {args.run} | {args.feature} | {args.category} | {args.severity} | {args.stage} | new | needs-triage | pending | `{rel_path}` |",
    )
    print(path)


def command_gap(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    ensure_dirs(root)
    date_value = today(args.date)
    gap_id = args.gap_id or next_id(root / "process/field-feedback/gap-analysis", "GAP", date_value)
    rel_path = Path("process/field-feedback/gap-analysis") / f"{gap_id}.md"
    path = root / rel_path
    content = f"""---
gap_id: "{gap_id}"
source_issue: "{args.issue}"
coverage_status: "{args.coverage_status}"
missing_stage: "{args.missing_stage}"
regression_asset: "{args.regression_asset}"
created_at: "{iso_now()}"
---

# {gap_id} Coverage Gap Analysis

## Decision

| Field | Value |
|---|---|
| source_issue | `{args.issue}` |
| coverage_status | `{args.coverage_status}` |
| missing_stage | `{args.missing_stage}` |
| missing_asset | `{args.missing_asset}` |
| regression_asset | `{args.regression_asset}` |

## Analysis

{args.summary}

## Suggested Backfill

{args.suggested_backfill or "TBD"}

## Regression Requirement

| Asset | Required | Status |
|---|---:|---|
| {args.regression_asset or "TBD"} | yes | pending |
"""
    write_new(path, content)
    if args.create_eval_backlog:
        append_unique_line(
            root / "evals/EVAL-BACKLOG.md",
            "# Eval Backlog\n\n| Backlog ID | Source ISSUE | Defect Class | Current Coverage | Proposed Eval | Priority | Status |\n|---|---|---|---|---|---|---|",
            f"| EVAL-BL-{date_value}-{args.issue[-3:]} | {args.issue} | {args.missing_stage} | {args.coverage_status} | {args.regression_asset or 'TBD'} | {args.priority} | pending |",
        )
    print(path)


def parse_register(root: Path) -> list[dict[str, str]]:
    register = root / "process/field-feedback/FIELD-ISSUE-REGISTER.md"
    if not register.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in register.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ISSUE-"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 10:
            rows.append(
                {
                    "issue": cells[0],
                    "run": cells[1],
                    "feature": cells[2],
                    "category": cells[3],
                    "severity": cells[4],
                    "stage": cells[5],
                    "status": cells[6],
                    "coverage_status": cells[7],
                    "regression_asset": cells[8],
                    "path": cells[9],
                }
            )
    return rows


def command_dashboard(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    ensure_dirs(root)
    rows = parse_register(root)
    total = len(rows)
    blocker = sum(1 for row in rows if row["severity"] == "BLOCKER")
    high = sum(1 for row in rows if row["severity"] == "HIGH")
    open_count = sum(1 for row in rows if row["status"] not in ("closed", "verified"))
    eval_gap = sum(1 for row in rows if row["category"] == "eval-gap" or "uncovered" in row["coverage_status"])
    regression_linked = sum(1 for row in rows if row["regression_asset"] not in ("", "pending", "TBD"))
    week = args.week or dt.date.today().strftime("%G-W%V")
    lines = [
        "# Field Quality Dashboard",
        "",
        f"- week: `{week}`",
        f"- generated_at: `{iso_now()}`",
        f"- total_issues: `{total}`",
        f"- open_issues: `{open_count}`",
        f"- blocker_count: `{blocker}`",
        f"- high_count: `{high}`",
        f"- eval_gap_count: `{eval_gap}`",
        f"- issue_to_regression_count: `{regression_linked}`",
        "",
        "## Issue Register Snapshot",
        "",
        "| ISSUE | Feature | Category | Severity | Stage | Status | Coverage Status | Regression Asset |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['issue']} | {row['feature']} | {row['category']} | {row['severity']} | "
            f"{row['stage']} | {row['status']} | {row['coverage_status']} | {row['regression_asset']} |"
        )
    if not rows:
        lines.append("| N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |")
    lines.extend(
        [
            "",
            "## Required Follow-up",
            "",
            "- `BLOCKER` / `HIGH` issues require owner and next verification evidence.",
            "- `uncovered-*` issues require an eval/checkpoint/test regression asset.",
            "- `pending` regression assets mean the issue is not closed.",
            "",
        ]
    )
    out = root / "docs/quality/FIELD-QUALITY-DASHBOARD.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate field-feedback records.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create field-feedback directories and index files.")
    init.add_argument("--root", default=".")
    init.set_defaults(func=command_init)

    collect = sub.add_parser("collect", help="Collect one runtime workspace into a portable feedback package.")
    collect.add_argument("--root", default=".")
    collect.add_argument("--workspace", required=True)
    collect.add_argument("--feature", required=True)
    collect.add_argument("--platform", default="claude")
    collect.add_argument("--date", default="")
    collect.add_argument("--collection-id", default="")
    collect.add_argument("--result", choices=RESULTS, default="partial")
    collect.add_argument("--gate", default="unknown")
    collect.add_argument("--summary", default="")
    collect.add_argument("--expected", default="")
    collect.add_argument("--actual", default="")
    collect.add_argument("--command", default="")
    collect.add_argument("--notes", default="")
    collect.add_argument("--include", action="append", default=[], help="Additional workspace-relative path to collect.")
    collect.set_defaults(func=command_collect)

    publish = sub.add_parser("publish", help="Copy a collection package into a git feedback repository.")
    publish.add_argument("--root", default=".")
    publish.add_argument("--collection", required=True)
    publish.add_argument("--target-repo", default="")
    publish.add_argument("--branch", default="")
    publish.add_argument("--dest", default="")
    publish.add_argument("--replace", action="store_true")
    publish.add_argument("--commit", action="store_true")
    publish.add_argument("--message", default="")
    publish.add_argument("--push", action="store_true")
    publish.add_argument("--remote", default="")
    publish.set_defaults(func=command_publish)

    pull = sub.add_parser("pull", help="Clone or pull raw feedback materials from a git repository into ptm-team inbox.")
    pull.add_argument("--root", default=".")
    pull.add_argument("--source-repo", default="")
    pull.add_argument("--dest", default="")
    pull.add_argument("--branch", default="")
    pull.add_argument("--remote", default="")
    pull.set_defaults(func=command_pull)

    repo_init = sub.add_parser("repo-init", help="Initialize the configured Git feedback repository.")
    repo_init.add_argument("--root", default=".")
    repo_init.add_argument("--local-repo", default="")
    repo_init.add_argument("--remote-url", default="")
    repo_init.add_argument("--branch", default="")
    repo_init.add_argument("--remote", default="")
    repo_init.add_argument("--replace-remote", action="store_true")
    repo_init.add_argument("--push", action="store_true")
    repo_init.set_defaults(func=command_repo_init)

    submit = sub.add_parser("submit", help="Collect one runtime workspace and publish it to the configured feedback repository.")
    submit.add_argument("--root", default=".")
    submit.add_argument("--workspace", required=True)
    submit.add_argument("--feature", required=True)
    submit.add_argument("--platform", default="claude")
    submit.add_argument("--date", default="")
    submit.add_argument("--collection-id", default="")
    submit.add_argument("--result", choices=RESULTS, default="partial")
    submit.add_argument("--gate", default="unknown")
    submit.add_argument("--summary", default="")
    submit.add_argument("--expected", default="")
    submit.add_argument("--actual", default="")
    submit.add_argument("--command", default="")
    submit.add_argument("--notes", default="")
    submit.add_argument("--include", action="append", default=[], help="Additional workspace-relative path to collect.")
    submit.add_argument("--target-repo", default="")
    submit.add_argument("--branch", default="")
    submit.add_argument("--dest", default="")
    submit.add_argument("--replace", action="store_true")
    submit.add_argument("--commit", action="store_true")
    submit.add_argument("--message", default="")
    submit.add_argument("--push", action="store_true")
    submit.add_argument("--remote", default="")
    submit.set_defaults(func=command_submit)

    run_exec = sub.add_parser("run-exec", help="Create a RUN-EXEC record for one real usage run.")
    run_exec.add_argument("--root", default=".")
    run_exec.add_argument("--date", default="")
    run_exec.add_argument("--run-id", default="")
    run_exec.add_argument("--feature", required=True)
    run_exec.add_argument("--platform", default="claude")
    run_exec.add_argument("--agent-version", default="unknown")
    run_exec.add_argument("--workspace", default=".")
    run_exec.add_argument("--result", choices=RESULTS, required=True)
    run_exec.add_argument("--gate", default="unknown")
    run_exec.add_argument("--summary", required=True)
    run_exec.add_argument("--command", default="")
    run_exec.add_argument("--input-doc", action="append", default=[])
    run_exec.add_argument("--evidence", action="append", default=[])
    run_exec.add_argument("--expected", default="")
    run_exec.add_argument("--actual", default="")
    run_exec.add_argument("--collection", default="")
    run_exec.add_argument("--published-path", default="")
    run_exec.add_argument("--notes", default="")
    run_exec.set_defaults(func=command_run_exec)

    issue = sub.add_parser("issue", help="Create an ISSUE record linked to a RUN-EXEC.")
    issue.add_argument("--root", default=".")
    issue.add_argument("--date", default="")
    issue.add_argument("--issue-id", default="")
    issue.add_argument("--run", required=True)
    issue.add_argument("--feature", required=True)
    issue.add_argument("--category", choices=CATEGORIES, required=True)
    issue.add_argument("--severity", choices=SEVERITIES, required=True)
    issue.add_argument("--stage", required=True)
    issue.add_argument("--owner", default="unassigned")
    issue.add_argument("--summary", required=True)
    issue.add_argument("--symptom", default="")
    issue.add_argument("--expected", default="")
    issue.add_argument("--actual", default="")
    issue.add_argument("--evidence", action="append", default=[])
    issue.set_defaults(func=command_issue)

    gap = sub.add_parser("gap", help="Create a coverage-gap analysis record.")
    gap.add_argument("--root", default=".")
    gap.add_argument("--date", default="")
    gap.add_argument("--gap-id", default="")
    gap.add_argument("--issue", required=True)
    gap.add_argument("--coverage-status", choices=COVERAGE_STATUS, required=True)
    gap.add_argument("--missing-stage", choices=MISSING_STAGES, required=True)
    gap.add_argument("--missing-asset", default="TBD")
    gap.add_argument("--summary", required=True)
    gap.add_argument("--suggested-backfill", default="")
    gap.add_argument("--regression-asset", default="")
    gap.add_argument("--create-eval-backlog", action="store_true")
    gap.add_argument("--priority", choices=SEVERITIES, default="MEDIUM")
    gap.set_defaults(func=command_gap)

    dashboard = sub.add_parser("dashboard", help="Refresh weekly field quality dashboard.")
    dashboard.add_argument("--root", default=".")
    dashboard.add_argument("--week", default="")
    dashboard.set_defaults(func=command_dashboard)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
