# ptm-team

TGFW测试组 PTM (Product Test Management) Team 项目

## 快速安装

### Agent 一键安装

把下面这段话发给 Claude Code 即可完成全部安装：

> 请帮我完成 ptm-team 和 ptm-atomic 的安装，按以下步骤执行：
>
> 1. 检查 `uv` 是否已安装；若不存在则先执行 `curl -LsSf https://astral.sh/uv/install.sh | sh` 安装 uv
> 2. 询问我 ptm-team 存放目录，默认 `~/ptm-team`，确认后执行 `git clone git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team.git <目标目录>`，已存在则 `git pull` 更新
> 3. `cd <目标目录> && uv tool install .` — 安装 `ptm-team` 全局命令
> 4. `uv tool install git+ssh://git@<IP_ADDRESS>/<INTERNAL_GIT_PATH>/ptm-atomic.git` — 安装 `ptm-atomic` 全局命令
> 5. `ptm-atomic sync git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-atomic.git` — 同步 ptm-atomic 运行时资源
> 6. 安装完成后提示我进入目标项目目录，运行 `ptm-team install claude --agent ptm-tde` 安装 agent

### 全局命令安装（推荐）

将 `ptm-team` 注册为全局命令：

```shell
# 在项目目录下执行
uv tool install .
```

安装后可直接使用：

```shell
# 安装 agent 到 Claude Code（--agent 支持 ptm-tde / ptm-te 等）
ptm-team install claude --agent ptm-tde    # 测试设计工程师（MFQ&PPDCS 三阶段框架）
ptm-team install claude --agent ptm-te     # 测试执行工程师（设备管理 + 策略路由用例执行）

# 安装到 Codex / Qoder
ptm-team install codex --agent ptm-tde
ptm-team install qoder --agent ptm-te

# 预览安装内容（不实际修改文件）
ptm-team install claude --agent ptm-te --dry-run

# 交互式选择安装 skill
ptm-team install claude --skill

# 模糊匹配安装 skill
ptm-team install claude --skill checkpoint

# 列出已安装内容
ptm-team install claude --list

# 卸载
ptm-team uninstall claude

# 重装（先卸载再安装，清理残留并保持 manifest 不膨胀）
ptm-team reinstall claude --agent ptm-tde
ptm-team reinstall claude --agent ptm-te   # --agent 支持别名（te / tde）
ptm-team reinstall claude --agent ptm-tde --dry-run
```

> **⚠️ 更新后必须重装**：`ptm-team` 通过 `uv tool` 安装到隔离环境，源代码修改不会自动生效。以下情况必须重新安装：
>
> - 拉取最新代码后
> - 修改了 `script/ptm_team/` 下的任何代码
> - 安装结果与预期不符（如 skill 数量、resource 数量、因子库缺失等）
>
> ```shell
> cd /home/hyde/projects/ptm-team   # 或你的 ptm-team 项目路径
> uv tool install . --reinstall
> ```

安装 `ptm-tde` agent 时会同步安装它关联的公共 resources。公共因子库归档在仓库 `resource/factor-libraries/`，默认安装到 `~/.ptm-team/resource/factor-libraries/`，可通过 `PTM_TEAM_RESOURCE_HOME` 指向团队共享资源目录。安装 `ptm-te` agent 时同步安装其 3 个关联 skill（device-management / device-connection / policy-route-execution），详见 `docs/ptm-te/README.md`。

### 开发模式安装

如果需要修改代码，可以使用开发模式：

```shell
uv pip install -e .
```

### 直接使用脚本

也可以直接运行脚本：

```shell
uv run python script/install.py install claude --agent ptm-tde
```

## agents

Claude Code 使用的 Agents 集合

### 详细使用帮助

详细使用帮助详见: [agent 使用帮助](agents/README.md)

## script

可使用的单文件工具，详细使用帮助详见： [script 使用帮助](script/README.md)

## skills

项目所有的 skills 工具

### 激活方法

#### 使用安装工具（推荐）

使用 `ptm-team install` 命令安装 skills：

```shell
# 交互式选择安装
ptm-team install claude --skill

# 模糊匹配安装
ptm-team install claude --skill checkpoint
```

#### 使用 Skills 管理工具

执行以下命令使用 Skills 管理工具，选择激活指定的 skills 或套餐

```shell
uv run script/skills_manager.py
```

### 详细使用帮助

详细使用帮助详见： [Skills 使用帮助](skills/README.md)
