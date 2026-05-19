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

## skills_manager.py

Skills 管理工具，可以便捷的启用、禁用 Skill，以及对 Skills 组打包成独立的配置以快速切换，运行命令如下

```shell
uv run script/skills_manager.py
```
