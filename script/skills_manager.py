#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "inquirerpy>=0.3.4",
# ]
# ///
"""
skill_manager: 扫描 skills 源目录,通过交互式多选管理激活状态,并支持命名配置(profile)切换。

- 激活的 skill: 软链接到 $(pwd)/.codex/skills/<n> 和 $(pwd)/.claude/skills/<n>
- 取消激活的 skill: 从这两个目录中删除对应软链接(只删软链接,不动真实目录)
- 配置(profile): 命名的 skill 集合,保存在 <source>/conf.json,可一键切换

用法:
    python skill_manager.py                          # 默认源 ./skills,进入交互菜单
    python skill_manager.py /path/to/skills-source
    python skill_manager.py --cwd /path/to/project
    python skill_manager.py --load <profile>         # 直接加载配置并应用,跳过菜单
    python skill_manager.py --list                   # 列出所有配置后退出
    python skill_manager.py --dry-run                # 预览变更,不实际改动
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
except ImportError:
    sys.exit("请先安装 InquirerPy: pip install inquirerpy")


CONF_FILENAME = "conf.json"


# ---------- 扫描与状态检测 ----------

def find_skills(source_dir: Path) -> list[Path]:
    """返回 source_dir 下所有含 SKILL.md 的子目录,按名称排序。"""
    if not source_dir.is_dir():
        sys.exit(f"❌ 源目录不存在或不是目录: {source_dir}")
    return sorted(
        (p for p in source_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()),
        key=lambda p: p.name.lower(),
    )


def get_active_skills(target_dirs: list[Path], source_dir: Path) -> set[str]:
    """检测当前已激活(目标目录中存在指向 source_dir 内 skill 的软链接)的 skill 名。"""
    source_resolved = source_dir.resolve()
    active: set[str] = set()
    for target in target_dirs:
        if not target.is_dir():
            continue
        for entry in target.iterdir():
            if not entry.is_symlink():
                continue
            try:
                if entry.resolve().parent == source_resolved:
                    active.add(entry.name)
            except (OSError, RuntimeError):
                pass
    return active


def read_skill_description(skill_dir: Path, max_len: int = 70) -> str:
    """尝试从 SKILL.md 的 YAML frontmatter 读 description,失败返回空串。"""
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    if not content.startswith("---"):
        return ""
    end = content.find("\n---", 3)
    if end < 0:
        return ""
    for line in content[3:end].splitlines():
        line = line.strip()
        if line.lower().startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip('"\'')
            return desc[:max_len] + ("…" if len(desc) > max_len else "")
    return ""


# ---------- 配置(profile)管理 ----------

def conf_path(source_dir: Path) -> Path:
    return source_dir / CONF_FILENAME


def load_profiles(source_dir: Path) -> dict[str, list[str]]:
    path = conf_path(source_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️  无法读取 {path}: {e}")
        return {}
    profiles = data.get("profiles", {})
    return {k: sorted(set(v)) for k, v in profiles.items() if isinstance(v, list)}


def save_profiles(source_dir: Path, profiles: dict[str, list[str]]) -> None:
    path = conf_path(source_dir)
    path.write_text(
        json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# ---------- 链接管理 ----------

def activate(skill_dir: Path, target_dirs: list[Path], dry_run: bool) -> None:
    for target in target_dirs:
        link = target / skill_dir.name
        if link.is_symlink():
            try:
                if link.resolve() == skill_dir.resolve():
                    continue  # 已经正确,跳过
            except OSError:
                pass
            if not dry_run:
                link.unlink()  # 错误的软链接,重建
        elif link.exists():
            print(f"  ⚠️  跳过 {link}: 已存在且不是软链接(不会覆盖)")
            continue

        if dry_run:
            print(f"  [dry-run] 将创建: {link} → {skill_dir}")
        else:
            target.mkdir(parents=True, exist_ok=True)
            link.symlink_to(skill_dir.resolve(), target_is_directory=True)
            print(f"  ✓ 激活: {link} → {skill_dir}")


def deactivate(skill_name: str, target_dirs: list[Path], dry_run: bool) -> None:
    for target in target_dirs:
        link = target / skill_name
        if link.is_symlink():
            if dry_run:
                print(f"  [dry-run] 将删除: {link}")
            else:
                link.unlink()
                print(f"  ✗ 禁用: {link}")
        elif link.exists():
            print(f"  ⚠️  跳过 {link}: 不是软链接,不会自动删除")


def apply_selection(
    desired: list[Path],
    current_active: set[str],
    target_dirs: list[Path],
    dry_run: bool,
) -> tuple[int, int]:
    """根据期望集合调整链接,返回 (激活数, 禁用数)。activate 是幂等的。"""
    desired_names = {s.name for s in desired}
    to_deactivate = sorted(current_active - desired_names)

    for skill in desired:
        activate(skill, target_dirs, dry_run)
    for name in to_deactivate:
        deactivate(name, target_dirs, dry_run)

    return len(desired), len(to_deactivate)


def resolve_profile_skills(
    profile_names: list[str], skills_by_name: dict[str, Path]
) -> tuple[list[Path], list[str]]:
    """把 profile 中的 skill 名解析成 Path 列表,返回 (有效列表, 缺失名列表)。"""
    valid: list[Path] = []
    missing: list[str] = []
    for n in profile_names:
        if n in skills_by_name:
            valid.append(skills_by_name[n])
        else:
            missing.append(n)
    return valid, missing


# ---------- 各菜单动作 ----------

def action_edit(
    skills: list[Path],
    active: set[str],
    target_dirs: list[Path],
    source_dir: Path,
    profiles: dict[str, list[str]],
    dry_run: bool,
) -> None:
    name_width = max(len(s.name) for s in skills)
    choices = [
        Choice(
            value=skill,
            name=skill.name.ljust(name_width)
            + (f"  —  {d}" if (d := read_skill_description(skill)) else ""),
            enabled=skill.name in active,
        )
        for skill in skills
    ]

    try:
        selected: list[Path] = inquirer.checkbox(
            message="选择要激活的 skills",
            choices=choices,
            instruction="(空格选择,a全选,i反选,回车确认)",
            cycle=True,
            transformer=lambda r: f"已选 {len(r)} 个",
            keybindings={
                "toggle-all-true": [{"key": "a"}],
                "toggle-all-false": [{"key": "i"}],
            },
        ).execute()
    except KeyboardInterrupt:
        return

    if selected is None:
        return

    print(f"\n--- {'预览' if dry_run else '应用'}变更 ---")
    n_act, n_deact = apply_selection(selected, active, target_dirs, dry_run)
    if n_act == 0 and n_deact == 0:
        print("  (无变更)")
    print(f"\n完成: 激活 {n_act},禁用 {n_deact}"
          + (" (dry-run)" if dry_run else ""))

    # 顺手保存为配置
    if not dry_run and inquirer.confirm(
        message="将当前激活保存为命名配置?", default=False
    ).execute():
        save_current_as_profile(source_dir, {s.name for s in selected}, profiles)


def action_load(
    profiles: dict[str, list[str]],
    skills: list[Path],
    active: set[str],
    target_dirs: list[Path],
    dry_run: bool,
) -> None:
    if not profiles:
        print("没有已保存的配置。")
        return
    name = inquirer.select(
        message="选择要加载的配置:",
        choices=[
            Choice(value=n, name=f"{n}  ({len(lst)} 个 skill)")
            for n, lst in sorted(profiles.items())
        ],
    ).execute()
    if name is None:
        return

    skills_by_name = {s.name: s for s in skills}
    desired, missing = resolve_profile_skills(profiles[name], skills_by_name)
    if missing:
        print(f"⚠️  配置 '{name}' 中以下 skill 在源目录已不存在,忽略: {', '.join(missing)}")

    print(f"\n--- {'预览' if dry_run else '应用'}配置 '{name}' ---")
    n_act, n_deact = apply_selection(desired, active, target_dirs, dry_run)
    print(f"\n完成: 激活 {n_act},禁用 {n_deact}"
          + (" (dry-run)" if dry_run else ""))


def save_current_as_profile(
    source_dir: Path, active: set[str], profiles: dict[str, list[str]]
) -> None:
    name = inquirer.text(
        message="配置名称:",
        validate=lambda x: len(x.strip()) > 0,
        invalid_message="名称不能为空",
    ).execute()
    if name is None:
        return
    name = name.strip()

    if name in profiles:
        if not inquirer.confirm(
            message=f"配置 '{name}' 已存在,覆盖?", default=False
        ).execute():
            print("已取消保存。")
            return

    profiles[name] = sorted(active)
    save_profiles(source_dir, profiles)
    print(f"✓ 已保存配置 '{name}' ({len(active)} 个 skill) → {conf_path(source_dir)}")


def action_save(
    active: set[str], profiles: dict[str, list[str]], source_dir: Path
) -> None:
    if not active:
        if not inquirer.confirm(
            message="当前没有激活任何 skill,仍要保存空配置?", default=False
        ).execute():
            return
    save_current_as_profile(source_dir, active, profiles)


def action_delete(profiles: dict[str, list[str]], source_dir: Path) -> None:
    if not profiles:
        print("没有已保存的配置。")
        return
    name = inquirer.select(
        message="删除哪个配置?",
        choices=[
            Choice(value=n, name=f"{n}  ({len(lst)} 个 skill)")
            for n, lst in sorted(profiles.items())
        ],
    ).execute()
    if name is None:
        return
    if not inquirer.confirm(message=f"确定删除 '{name}'?", default=False).execute():
        return
    del profiles[name]
    save_profiles(source_dir, profiles)
    print(f"✓ 已删除配置 '{name}'")


# ---------- 主入口 ----------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="交互式管理 skills 的激活状态(软链接到 .codex/skills 和 .claude/skills),支持命名配置切换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        default=Path("skills"),
        help="skills 源目录;默认为当前目录下的 ./skills",
    )
    parser.add_argument(
        "--cwd", type=Path, default=Path.cwd(),
        help="工作目录(软链接根),默认为当前目录",
    )
    parser.add_argument("--dry-run", action="store_true", help="只打印将要执行的操作")
    parser.add_argument("--load", metavar="NAME", help="直接加载并应用指定配置,跳过菜单")
    parser.add_argument("--list", action="store_true", dest="list_profiles",
                        help="列出所有已保存配置后退出")
    args = parser.parse_args()

    source_dir = args.source.expanduser().resolve()
    cwd = args.cwd.expanduser().resolve()
    target_dirs = [cwd / ".codex" / "skills", cwd / ".claude" / "skills"]

    skills = find_skills(source_dir)
    if not skills:
        sys.exit(f"❌ {source_dir} 下没有找到任何 skill(含 SKILL.md 的子目录)")

    profiles = load_profiles(source_dir)

    # --list: 列出后直接退出
    if args.list_profiles:
        if not profiles:
            print("(无已保存配置)")
            return
        for name, skill_list in sorted(profiles.items()):
            print(f"\n● {name}  ({len(skill_list)} 个)")
            for s in skill_list:
                print(f"    - {s}")
        return

    active = get_active_skills(target_dirs, source_dir)

    print(f"📂 源目录: {source_dir}")
    print(f"🎯 目标:  {target_dirs[0]}")
    print(f"          {target_dirs[1]}")
    print(f"✅ 当前已激活: {len(active)} 个 | 💾 已保存配置: {len(profiles)} 个\n")

    # --load: 直接应用指定配置
    if args.load:
        if args.load not in profiles:
            available = ", ".join(sorted(profiles)) or "(无)"
            sys.exit(f"❌ 配置 '{args.load}' 不存在。可用: {available}")
        skills_by_name = {s.name: s for s in skills}
        desired, missing = resolve_profile_skills(profiles[args.load], skills_by_name)
        if missing:
            print(f"⚠️  以下 skill 在源目录已不存在,忽略: {', '.join(missing)}")
        print(f"--- {'预览' if args.dry_run else '应用'}配置 '{args.load}' ---")
        n_act, n_deact = apply_selection(desired, active, target_dirs, args.dry_run)
        print(f"\n完成: 激活 {n_act},禁用 {n_deact}"
              + (" (dry-run)" if args.dry_run else ""))
        return

    # 交互菜单
    try:
        action = inquirer.select(
            message="选择操作:",
            choices=[
                Choice(value="edit", name="📝  编辑当前激活的 skills"),
                Choice(value="load", name=f"📥  加载已保存的配置  ({len(profiles)})"),
                Choice(value="save", name="💾  将当前激活保存为新配置"),
                Choice(value="delete", name=f"🗑   删除已保存的配置  ({len(profiles)})"),
                Choice(value="quit", name="🚪  退出"),
            ],
            default="edit",
        ).execute()
    except KeyboardInterrupt:
        sys.exit("\n已取消")

    if action == "edit":
        action_edit(skills, active, target_dirs, source_dir, profiles, args.dry_run)
    elif action == "load":
        action_load(profiles, skills, active, target_dirs, args.dry_run)
    elif action == "save":
        action_save(active, profiles, source_dir)
    elif action == "delete":
        action_delete(profiles, source_dir)
    # quit: 直接结束


if __name__ == "__main__":
    main()