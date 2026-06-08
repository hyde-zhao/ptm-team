---
story_id: "STORY-02"
title: "Installer 用户级安装 — CLAUDE.md / AGENTS.md 合并"
milestone: "M1"
wave: "W2"
priority: "P1"
status: "verified"
size: "M"
depends_on: ["STORY-01"]
requirements: ["REQ-001"]
lld_file: "process/stories/story-02-lld.md"
---

# STORY-02：Installer 用户级安装 — `CLAUDE.md` / `AGENTS.md` 合并

## 目标

为 `user scope` 安装提供 marker section 合并策略、merge report 和冲突保护。

## 范围边界

- **包含**：`user scope` 目标根路径、规则文件检测、marker merge、merge report、失败回退
- **不包含**：project scope 基线（已由 STORY-01 负责）

## 需求映射

- REQ-001
- HLD §8.5 / §10.6 / ADR-4

## 产出物

- `scripts/install.py`
- `rules/CLAUDE.md`
- `process/PLATFORM-INSTALL-SPEC.md`（如需补充 merge 约束）

## 依赖与 Wave

- Wave：W2
- 依赖：STORY-01
- 后续依赖方：无硬依赖，但作为 user scope 上线路径前置

## 开发上下文

- `user scope` 不允许静默覆盖用户已有全局规则文件。
- 合并策略必须可 dry-run 预览。

## 验证上下文

- 命中既有 `CLAUDE.md` / `AGENTS.md` 时必须产生 merge report。
- merge 失败必须显式 blocked，不得写入半成品。

## 量化验收标准

1. `user scope` 安装支持 marker merge。
2. dry-run 能显示 `direct-write / marker-merge / blocked` 三种处理模式。
3. 现有规则文件不会被整文件覆盖。
