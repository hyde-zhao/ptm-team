---
release: "CR-030 ptm-tse 现网问题逆向分析能力 v1.0"
checklist_type: "deployment"
release_artifact_profile: "compact"
release_decision: "READY_WITH_RISK"
validation_mode: "static-only"
---

# ptm-tse CR-030 部署检查清单

## 已完成的交付前检查

| 检查 | 结果 | 证据 |
|---|---|---|
| 14 个 Story 静态验证 | PASS | `process/checks/CP7-CR030.result.json` |
| CP7 返回包与证据索引 | PASS | `process/returns/`、`process/evidence/` 中 14 组文件 |
| Schema 编译 | PASS | `data/schema.sql` 内存 SQLite `executescript` |
| Python 语法检查 | PASS | `uv run --python 3.11 python -m py_compile data/dao.py` |
| Codex 安装 dry-run | PASS | `script/install.py install codex --agent ptm-tse --dry-run` |
| Claude 安装 dry-run | PASS | `script/install.py install claude --agent ptm-tse --dry-run` |
| Qoder 安装 dry-run | PASS | `script/install.py install qoder --agent tse --dry-run` |
| 用户文档 | PASS | `README.md`、`docs/ptm-tse/USER-MANUAL.md` |

## 安装步骤

```shell
ptm-team install <claude|codex|qoder> --agent ptm-tse
```

安装后确认 Agent 与三个 Skill 都已出现：

| 平台 | Agent 位置 | Skill 位置 |
|---|---|---|
| Claude Code | `.claude/agents/ptm-tse.md` | `.claude/skills/` |
| Codex | `.codex/agents/ptm-tse.toml` | `.agents/skills/` |
| Qoder | `.qoder/agents/ptm-tse.md` | `.qoder/skills/` |

## 运行前强制条件

- 获得独立 runtime authorization 后，才可调用 ITR allowlisted HTTP GET。
- 受控环境必须使用非生产或已批准的数据窗口；不得读取凭据，不得执行外部写入。
- 首次运行前验证 SQLite 存储权限：目录 `0700`，数据库及 `-wal` / `-shm` / `-journal` 文件 `0600`。
- 运行质量报告为 `blocked` 时停止，不创建分析运行；发生冲突时进入人工队列，不覆盖既有版本。

## 受控 smoke test 后检查

| 场景 | 期望结果 |
|---|---|
| allowlist 外 URL | 被拒绝且无网络调用 |
| S1 摄取 | 生成快照、质量报告、版本化记录和分析草案 |
| S2 更新 | 记录新增/修改/未变/冲突并输出差异报告 |
| 无可信分母 | 降级为数量、占比、Pareto/趋势，不称缺陷密度 |
| reviewer 操作 | 仅 reviewer 能确认、批准、改变正式状态或关闭 |

## 已知限制

本轮只完成静态与安装 dry-run 验证。真实网络、SQLite 写入、S1/S2 运行和 reviewer 交互尚未执行，详见 CP8 风险接受项 `CP8-DQ-CR030-01`。
