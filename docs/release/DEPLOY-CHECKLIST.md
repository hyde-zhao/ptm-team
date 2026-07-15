# ptm-tde v1.0 部署检查清单

> 版本：v1.0 · 更新：2026-06-08 · 适用平台：Claude Code

---

## 部署概述

ptm-tde 作为 Claude Code Agent/Skill 集合，通过 `ptm-team install` 命令安装到目标项目。

---

## 安装前检查

| # | 检查项 | 预期结果 | 状态 |
|---|---|---|---|
| 1 | Claude Code 版本 | ≥ 1.0 | ☐ |
| 2 | 目标项目已初始化 CLAUDE.md | 文件存在且可读 | ☐ |
| 3 | ptm-team 命令已安装 | `ptm-team --help` 返回成功 | ☐ |
| 4 | Python 环境（uv）可用 | `uv --version` 成功 | ☐ |
| 5 | git 可用 | `git --version` 成功 | ☐ |

## 安装步骤

| # | 步骤 | 验证命令 | 状态 |
|---|---|---|---|
| 1 | 执行 `ptm-team install claude --agent ptm-tde` | 命令返回成功 | ☐ |
| 2 | 确认 `agents/ptm-tde.md` 已安装 | 文件存在 | ☐ |
| 3 | 确认 `skills/` 下 ptm-tde 专属 Skill 已安装 | 30+ Skill 文件存在 | ☐ |
| 4 | 确认 `resource/` 因子库资源已安装 | 资源文件存在 | ☐ |
| 5 | 确认目标项目 CLAUDE.md 已更新引用 | grep ptm-tde CLAUDE.md | ☐ |
| 6 | 确认 `skills/README.md` Skill 索引已更新 | 索引包含 ptm-tde Skill | ☐ |

## 安装后验证

| # | 检查项 | 验证方法 | 状态 |
|---|---|---|---|
| 1 | Agent 可识别 | Claude Code 中输入 `@ptm-tde` 可触发 | ☐ |
| 2 | KYM 阶段可用 | 输入需求文档后执行 GATE-1 → GATE-2 | ☐ |
| 3 | MFQ 阶段可用 | M/F/Q 分析 Skill 可被调用 | ☐ |
| 4 | PPDCS 阶段可用 | 8 个设计 Skill 可被调用 | ☐ |
| 5 | atomic-ops CLI 可用 | `atomic-ops list` 返回操作列表 | ☐ |
| 6 | 因子库可加载 | m-analyzer Step 1.5 无报错 | ☐ |
| 7 | 交付物可生成 | deliverable-renderer 输出测试方案和用例 | ☐ |

## 卸载步骤

| # | 步骤 | 说明 |
|---|---|---|
| 1 | 删除 `agents/ptm-tde.md` | 移除 Agent 定义 |
| 2 | 删除 ptm-tde 专属 Skill 目录 | 注意不要误删其他 Agent 的公共 Skill |
| 3 | 删除 `resource/` 下 ptm-tde 因子库 | 注意因子库可能被其他 Agent 共享 |
| 4 | 更新 CLAUDE.md 移除 ptm-tde 引用 | — |
| 5 | 更新 `skills/README.md` 移除 ptm-tde Skill | — |

## 已知问题

| # | 问题 | 影响 | 处理方式 |
|---|---|---|---|
| 1 | atomic-ops CLI 需要独立安装（`uv tool install`） | 依赖外部工具 | 安装前确认 atomic-ops 可用 |
| 2 | 因子库资源文件需要 git 同步 | 首次安装需 git clone/pull | 遵循 atomic-ops 离线优先策略 |
| 3 | Codex 平台交互模式未适配（CR-015-T-01） | AskUserQuestion 在 Codex 下行为不同 | 后续台账跟踪 |

---

*本清单覆盖 ptm-tde v1.0 Claude Code 平台部署场景。*

---

## 修订记录

| 日期 | 变更 | 处理人 |
|------|------|--------|
| 2026-07-06 | §安装前检查#3 修正误引用 meta-flow `delivery/` 路径（ptm-team 仓库无此目录，改为 `ptm-team` 命令检查）；§安装步骤#1 安装命令补 platform 位置参数 `claude` + `--agent ptm-tde`（对齐 install.py 实际 CLI，原 `ptm-team install ptm-tde` 会因 platform choices 校验失败）。 | host-orchestrator |
