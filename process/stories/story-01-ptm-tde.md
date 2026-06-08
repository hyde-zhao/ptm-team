---
story_id: "STORY-01"
title: "Installer 基线 — Claude/Codex project scope 投影"
milestone: "M1"
wave: "W1"
priority: "P0"
status: "verified"
size: "M"
depends_on: []
requirements: ["REQ-001"]
lld_file: "process/stories/story-01-lld.md"
---

# STORY-01：Installer 基线 — Claude/Codex project scope 投影

## 目标

把安装能力收敛到 **Claude Code / Codex**，并稳定 `project scope` 的安装、dry-run 与目录投影。

## 范围边界

- **包含**：`install.py` 平台筛选、project scope 目标路径、dry-run 输出、Claude/Codex 投影结构
- **不包含**：`user scope` 合并策略（移交 STORY-02）

## 需求映射

- REQ-001
- HLD §9 / ADR-4

## 产出物

- `scripts/install.py`
- `rules/CLAUDE.md`
- `agents/ptm-tde.md`（如需同步安装入口说明）

## 依赖与 Wave

- Wave：W1
- 依赖：无
- 后续依赖方：STORY-02

## 开发上下文

- 现有安装器已支持多平台与双 scope，需要先收缩到 v6 目标平台。
- `project scope` 是所有后续实现的基线安装路径。

## 验证上下文

- Claude Code / Codex 的 project scope dry-run 输出必须清晰展示目标文件。
- 旧平台不得再作为默认支持范围出现。

## 量化验收标准

1. 仅保留 Claude Code / Codex 为正式平台。
2. `project scope` dry-run 输出完整且可读。
3. 目录投影与 `process/PLATFORM-INSTALL-SPEC.md` 一致。
