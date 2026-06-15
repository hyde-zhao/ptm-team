# script

可使用的单文件工具

## install.py

ptm-team 安装工具，支持将 Agent 和 Skill 安装到 Claude Code 或 Codex 平台。

### 安装 Agent

```shell
# 安装 ptm-tde 及其引用的所有 skills
uv run python script/install.py install claude --agent ptm-tde
uv run python script/install.py install codex --agent tde

# 预览模式（不实际修改文件）
uv run python script/install.py install claude --agent ptm-tde --dry-run
```

安装 `ptm-tde` agent 时，安装器会同步安装 `resource/component-resource-links.yaml` 中声明的公共 resources，例如公共因子库。默认安装目标为 `~/.ptm-team/resource/`，可通过 `PTM_TEAM_RESOURCE_HOME` 覆盖。安装记录会保存 agent、skill、规则 managed block 和 resource 文件的 source / installed hash。

### 安装 Skill

```shell
# 交互式选择安装
uv run python script/install.py install claude --skill

# 模糊匹配安装
uv run python script/install.py install claude --skill checkpoint
```

### 卸载

```shell
# 卸载所有安装内容
uv run python script/install.py uninstall claude

# 卸载指定 agent 及其 skills
uv run python script/install.py uninstall claude --agent ptm-tde

# 交互式选择卸载 skill
uv run python script/install.py uninstall claude --skill

# 预览模式
uv run python script/install.py uninstall claude --dry-run
```

### 列出已安装内容

```shell
uv run python script/install.py install claude --list
```

### 检查安装漂移

```shell
uv run python script/install.py check codex --agent ptm-tde
uv run python script/install.py check claude --agent ptm-tde
```

`check` 会读取 `.ptm-team-manifest.json`，校验已安装 agent、skill、规则 managed block 和 resource 文件是否仍与 manifest 一致，并校验源仓库资产是否已变化。

### 公共资源

```shell
uv run python script/install.py resource list
uv run python script/install.py resource path
uv run python script/install.py resource validate
```

## skills_manager.py

Skills 管理工具，可以便捷的启用、禁用 Skill，以及对 Skills 组打包成独立的配置以快速切换，运行命令如下

```shell
uv run script/skills_manager.py
```

## field_feedback.py

真实发布后的现场反馈闭环工具，用于一键采集运行材料、同步到 Git/GitLab 仓库、拉取原始反馈材料、生成 RUN-EXEC、ISSUE、覆盖盲区分析和每周质量看板。

Agent 侧默认通过 `tde-feedback` Skill 调度该脚本；交付或真实运行结束后，Skill 会先询问用户是否有问题反馈，再根据授权选择 `collect / submit / publish / pull`。

仓库根目录的 `.ptm-field-feedback.yaml` 提供默认反馈仓库配置：

```yaml
feedback_repo:
  local_repo: "../ptm-team-feedback"
  remote_url: "git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git"
  branch: "main"
  dest: "tde-feedback"
  inbox_dest: "process/field-feedback/inbox/gitlab-materials"
  remote: "origin"
```

### 初始化台账

```shell
uv run python script/field_feedback.py init --root .
```

会创建：

```text
process/field-feedback/RUN-EXEC-INDEX.md
process/field-feedback/FIELD-ISSUE-REGISTER.md
process/field-feedback/runs/
process/field-feedback/gap-analysis/
process/issues/
evals/EVAL-BACKLOG.md
docs/quality/FIELD-QUALITY-DASHBOARD.md
```

### 记录一次真实使用

```shell
uv run python script/field_feedback.py run-exec \
  --root . \
  --feature policy_route \
  --platform claude \
  --workspace /home/hyde/projects/ptm-tde/test/policy_route_rt_verify \
  --result fail \
  --gate GATE-5 \
  --summary "GATE-5 PASS 后 STATE 未进入 completed" \
  --evidence process/checkpoints/GATE-5-Exit.md \
  --evidence process/STATE.yaml
```

### 一键采集运行目录

在使用者机器上执行，采集当前特性运行目录中的关键材料：

```shell
uv run python /path/to/ptm-team/script/field_feedback.py collect \
  --root /path/to/ptm-team \
  --workspace /home/user/ptm-tde/test/policy_route_rt_verify \
  --feature policy_route \
  --platform claude \
  --result fail \
  --gate GATE-4 \
  --summary "GATE-4 BLOCKED: ppdcs/coverage 缺失"
```

默认采集：

```text
process/STATE.yaml
process/checkpoints/
process/checks/
process/execution/
ppdcs/coverage/
ppdcs/delivery/
ppdcs/pc/
ppdcs/ppdcs/
```

输出示例：

```text
process/field-feedback/collections/COLLECT-20260615-policy_route-001/
  FEEDBACK.md
  MANIFEST.json
  artifacts/
```

可用 `--include <workspace-relative-path>` 追加采集路径。

### 发布采集包到 GitLab 仓库

`publish` 使用本机已有 Git 配置，不直接处理 GitLab Token。目标仓库可以是：

- `ptm-team` 自身的某个反馈分支
- 单独的反馈仓库，如 `ptm-tde-field-feedback`
- 任意已 clone 到本地的 GitLab 仓库

### 初始化默认反馈仓库

按 `.ptm-field-feedback.yaml` 初始化本地反馈仓库，并推送到默认 GitLab remote：

```shell
uv run python script/field_feedback.py repo-init --root . --push
```

等价于在 `../ptm-team-feedback` 下初始化 Git 仓库、设置 `origin` 为 `git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git`、使用 `main` 分支并执行首次 push。

发布到独立反馈仓库：

```shell
uv run python script/field_feedback.py publish \
  --collection process/field-feedback/collections/COLLECT-20260615-policy_route-001 \
  --target-repo /home/user/git/ptm-team-feedback \
  --branch main \
  --commit \
  --push
```

发布到 `ptm-team` 当前仓库的反馈分支：

```shell
uv run python script/field_feedback.py publish \
  --collection process/field-feedback/collections/COLLECT-20260615-policy_route-001 \
  --target-repo /home/user/projects/ptm-team \
  --branch main \
  --commit \
  --push
```

不想立即提交时，去掉 `--commit --push`，命令只复制文件。

使用默认配置发布时，可以省略 `--target-repo`、`--branch` 和 `--dest`：

```shell
uv run python script/field_feedback.py publish \
  --root . \
  --collection process/field-feedback/collections/COLLECT-20260615-policy_route-001 \
  --commit \
  --push
```

采集并发布可合并为一条命令：

```shell
uv run python script/field_feedback.py submit \
  --root . \
  --workspace /home/user/ptm-tde/test/policy_route_rt_verify \
  --feature policy_route \
  --platform claude \
  --result fail \
  --gate GATE-4 \
  --summary "GATE-4 BLOCKED: ppdcs/coverage 缺失" \
  --commit \
  --push
```

### 拉取 GitLab 原始反馈材料

在 `ptm-team` 分析侧执行：

```shell
uv run python script/field_feedback.py pull \
  --root . \
  --source-repo git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git \
  --branch main \
  --dest process/field-feedback/inbox/gitlab-materials
```

如果 `--dest` 已是 Git 仓库，则执行 `git pull --ff-only`；否则执行 `git clone`。

使用默认配置拉取时，可以省略 `--source-repo`、`--branch` 和 `--dest`：

```shell
uv run python script/field_feedback.py pull --root .
```

### 从失败生成 ISSUE

```shell
uv run python script/field_feedback.py issue \
  --root . \
  --run RUN-EXEC-20260615-001 \
  --feature policy_route \
  --category checkpoint \
  --severity HIGH \
  --stage GATE-5 \
  --owner checkpoint-manager \
  --summary "GATE-5 状态回写错误" \
  --expected "current_phase=completed" \
  --actual "current_phase=delivery"
```

### 生成覆盖盲区分析

```shell
uv run python script/field_feedback.py gap \
  --root . \
  --issue ISSUE-20260615-001 \
  --coverage-status covered-but-not-detected \
  --missing-stage checkpoint \
  --summary "现有 GATE-5 检查未验证 STATE phase 映射" \
  --suggested-backfill "补 checkpoint 单测并复跑 GATE-5" \
  --regression-asset tests.test_cr018_p2.test_gate5_pass_sets_completed_phase \
  --create-eval-backlog \
  --priority HIGH
```

### 刷新每周质量看板

```shell
uv run python script/field_feedback.py dashboard --root . --week 2026-W25
```
