---
name: tde-feedback
description: >-
  ptm-tde 真实使用反馈采集与同步：当用户要求收集反馈、上传反馈、推送反馈、
  同步到 GitLab、拉取反馈材料、基于真实运行反馈做评估、生成 RUN-EXEC /
  ISSUE / coverage gap，或在交付/真实运行结束后需要询问“是否有问题反馈”时使用。
  通过 ptm-team/script/field_feedback.py 和 .ptm-field-feedback.yaml 生成 COLLECT
  采集包、推送到 ptm-team-feedback GitLab 仓库，或从反馈仓库拉取材料供评估分析。
---

# TDE Feedback

## 目标

把 ptm-tde 真实使用中的问题、阻断、异常输出和运行证据标准化为 `COLLECT-*` 采集包，并通过默认 GitLab 反馈仓库同步给 ptm-team 评估侧。

## 必问入口

在以下场景结束时，必须先询问用户是否有问题反馈，不得默认无问题：

- GATE-4 / GATE-5 后；
- 最终测试方案或测试用例交付后；
- 用户完成一次 Claude / Codex TUI 真实运行后；
- 用户要求“继续验证”并给出通过、失败或阻断结论后；
- 用户要求“评估真实使用效果”前。

Claude Code 环境且 `AskUserQuestion` 可用时，必须使用结构化选项卡：

- question: "本次 ptm-tde 使用是否有问题需要反馈？"
- header: "TDE feedback"
- multiSelect: false
- options:
  1. label: "无问题反馈", description: "本次运行无需生成 COLLECT 包，也不推送 GitLab"
  2. label: "有问题，仅采集", description: "生成 COLLECT 包；不提交、不推送"
  3. label: "有问题，采集并上传", description: "生成 COLLECT 包，提交并 push 到默认反馈仓库 origin/main"
  4. label: "上传已有采集包", description: "使用已有 COLLECT-* 路径，提交并 push 到默认反馈仓库 origin/main"

Codex 或 `AskUserQuestion` 不可用时，回退到 exact 文本选项：

```text
【单选】本次 ptm-tde 使用是否有问题需要反馈？

A. 无问题反馈 — 不生成 COLLECT 包，不推送 GitLab
B. 有问题，仅采集 — 生成 COLLECT 包，不提交、不推送
C. 有问题，采集并上传 — 生成 COLLECT 包，提交并 push 到默认反馈仓库 origin/main
D. 上传已有采集包 — 使用已有 COLLECT-* 路径，提交并 push 到默认反馈仓库 origin/main

如果选择 B/C，请同时提供 feature、工作区路径、到达的 Gate、结果（pass/fail/blocked/partial/skipped）、期望结果、实际结果和一句摘要。
如果选择 D，请提供 COLLECT-* 路径。
```

用户选择“无问题反馈”时，只记录对话结论，不生成采集包，不推送。
用户选择“有问题，采集并上传”或“上传已有采集包”时，视为已明确授权 `--push`。
用户选择“有问题，仅采集”时，不得执行 `publish` 或 `push`。

## 默认配置

读取 `<ptm-team-root>/.ptm-field-feedback.yaml`：

| 字段 | 默认值 |
|---|---|
| local_repo | `../ptm-team-feedback` |
| remote_url | `git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git` |
| branch | `main` |
| dest | `tde-feedback` |
| inbox_dest | `process/field-feedback/inbox/gitlab-materials` |

## 权限边界

- 不得修改 `.input/`。
- 不得修改 ptm-team 代码仓库的 `origin`。
- 不得把反馈仓库 remote 设置为 HTTP；必须使用 SSH remote。
- 不得保存、打印或要求用户粘贴 GitLab token、密码、SSH 私钥。
- 执行 `--push` 前必须从用户请求中获得明确授权。
- 没有 push 授权时，只允许 `collect`，或本地 `publish --commit` 且不 `--push`。
- `pull` 只能用于拉取反馈材料；不得向反馈仓库写入。

## 命令选择

### 只采集

用户有问题反馈但未授权上传时执行：

```bash
uv run python <ptm-team-root>/script/field_feedback.py collect \
  --root <ptm-team-root> \
  --workspace <feature-workspace-root> \
  --feature <feature-name> \
  --platform claude \
  --result <pass|fail|blocked|partial|skipped> \
  --gate <GATE-N> \
  --summary "<一句摘要>" \
  --expected "<期望结果>" \
  --actual "<实际结果>"
```

`collect` 成功后必须同时生成：

- `process/field-feedback/collections/COLLECT-*`
- `process/field-feedback/runs/RUN-EXEC-*`
- `RUN-EXEC-INDEX.md` 索引行

`RUN-EXEC` 必须记录 `collection_path`，并在 `COLLECT-*/MANIFEST.json` 中回写 `run_exec_id` 和 `run_exec_path`。

### 采集并上传

用户明确授权 `push` 时执行：

```bash
uv run python <ptm-team-root>/script/field_feedback.py submit \
  --root <ptm-team-root> \
  --workspace <feature-workspace-root> \
  --feature <feature-name> \
  --platform claude \
  --result <pass|fail|blocked|partial|skipped> \
  --gate <GATE-N> \
  --summary "<一句摘要>" \
  --expected "<期望结果>" \
  --actual "<实际结果>" \
  --commit \
  --push
```

`submit` 成功后必须同时生成 `COLLECT-*`、`RUN-EXEC-*` 并推送采集包；`RUN-EXEC` 必须记录 `collection_path` 和 `published_path`，`MANIFEST.json` 必须回写 `run_exec_path` 和 `published_path`。

### 上传已有采集包

用户给出 `COLLECT-*` 路径且明确授权 `push` 时执行：

```bash
uv run python <ptm-team-root>/script/field_feedback.py publish \
  --root <ptm-team-root> \
  --collection <COLLECT-PATH> \
  --commit \
  --push
```

### 拉取反馈材料

评估侧需要消费 GitLab 反馈材料时执行：

```bash
uv run python <ptm-team-root>/script/field_feedback.py pull --root <ptm-team-root>
```

拉取后列出新增或更新的 `COLLECT-*` 包，并建议哪些包需要生成 `RUN-EXEC`、`ISSUE`、`coverage_status`、`regression_asset` 和 `FIELD-QUALITY-DASHBOARD`。

## 完成报告

每次执行后必须报告：

- 是否询问用户“是否有问题反馈”；
- 用户是否确认有问题反馈；
- 生成或处理的 `COLLECT-*` 路径；
- 自动登记的 `RUN-EXEC-*` 路径；
- `RUN-EXEC` 是否包含 `collection_path` / `published_path`；
- GitLab 目标仓库、分支和目录；
- 是否执行 `push`；
- `push` / `pull` 是否成功；
- 失败时的关键 stderr/stdout。

## Gotchas

- 用户只说“上传反馈”但没有明确 `feature_workspace_root` 时，先询问工作区路径，不要猜。
- 用户没有明确授权 `--push` 时，不得推送。
- HTTP remote 曾导致认证失败；默认和修复都必须使用 SSH remote。
- 反馈采集包是运行证据，不等同于 ISSUE；`collect` / `submit` 会自动登记 `RUN-EXEC`，但后续仍需按问题生成 `ISSUE` 和覆盖盲区分析。

## 验收标准

- [ ] 交付或真实运行结束后先询问是否有问题反馈
- [ ] 支持 `collect / submit / publish / pull` 四类动作
- [ ] `collect / submit` 自动生成 `RUN-EXEC` 并绑定 `collection_path`
- [ ] `submit` 生成的 `RUN-EXEC` 绑定 `published_path`
- [ ] 使用 `.ptm-field-feedback.yaml` 默认配置
- [ ] 默认远端为 SSH `git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git`
- [ ] `--push` 前必须有明确授权
- [ ] 不修改 `.input/`
- [ ] 不修改 ptm-team 代码仓库 `origin`
