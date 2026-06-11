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
