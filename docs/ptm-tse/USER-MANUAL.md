---
title: "ptm-tse 用户手册"
version: "CR-030 v1.0"
validation_mode: "static-only"
---

# ptm-tse 用户手册

## 安装

在目标项目目录执行以下命令。安装会复制 Agent 和三个依赖 Skill，不会发起 ITR 请求。

```shell
ptm-team install claude --agent ptm-tse
ptm-team install codex --agent ptm-tse
ptm-team install qoder --agent ptm-tse
```

安装前可使用以下命令检查将要写入的文件：

```shell
ptm-team install claude --agent ptm-tse --dry-run
```

Codex 的 Agent 安装到 `.codex/agents/ptm-tse.toml`，三个 Skill 安装到 `.agents/skills/`；Claude Code 和 Qoder 的 Skill 分别安装到各自平台的 Skill 目录。

## 用户旅程

### 首次分析

向 `ptm-tse` 提交产品、日期窗口和“首次分析”意图。Agent 先使用 `itr-ticket-ingestion` 在固定 allowlist 内执行 ITR GET，保存原始快照、清洗数据并生成质量报告。质量报告为 `blocked` 时，分析会停止。数据合格后，`reverse-analysis` 生成六维分析和 RA Report 草案，`improvement-tracker` 仅生成 CA/PA 候选。

### 更新分析

提交相同范围并要求“更新分析”。Agent 重新摄取数据，识别新增、变更、未变和冲突记录，保留版本历史后重算受影响维度，输出本次与比较窗口的差异报告，并为既有措施生成刷新提示。冲突不会静默覆盖。

## 输出与人工责任

输出包括问题单逐单总结、批量趋势、根因候选、流出与漏测分析、CA/PA 草案和环比/同比差异。所有报告都区分事实、假设、证据缺口和 reviewer 确认状态。

`ptm-tse` 不会确认根因、批准或关闭措施、分发下游任务、修改 ITR 或任何外部系统。reviewer 是这些状态变更的唯一执行者。

## 运行边界

- 仅允许访问 CR-030 定义的固定 ITR allowlist，且只允许 HTTP `GET`。
- 不读取凭据，不发送外部写入请求，不执行生产操作。
- 问题单数据保存到受限 SQLite 存储；目录权限必须为 `0700`，数据库及 WAL/SHM 文件必须为 `0600`。
- 本交付仅完成静态与内存 DDL 验证。首次真实 ITR 调用、SQLite 写入、S2 重算和 reviewer 交互必须在获得独立运行授权后，在受控环境执行 smoke test。

## 常见处置

| 现象 | 行为 | 处理 |
|---|---|---|
| 数据质量报告为 `blocked` | 不创建分析运行 | 修复字段映射、关键字段完整性或批次冲突后重试 |
| 无可信分母 | 不输出“缺陷密度” | 输出数量、占比、Pareto 和趋势，并标记降级原因 |
| 无控制层证据 | 流出层仅为 candidate | 由 reviewer 补充证据后再确认 |
| 基线缺失 | 措施标记 `needs-baseline` | reviewer 建立基线；系统不会自动改正式状态 |
| 需要真实网络请求 | 停止在授权门 | 获得独立 runtime authorization 后执行受控 smoke test |

## 相关资料

- [Agent 定义](../../agents/ptm-tse.md)
- [发布说明](../release/RELEASE-NOTES.md)
- [部署检查](../release/DEPLOY-CHECKLIST.md)
- [回滚方案](../release/ROLLBACK.md)
