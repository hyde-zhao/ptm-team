# ptm-team

TGFW测试组 PTM (Product Test Management) Team 项目

## 快速安装

### 全局命令安装（推荐）

将 `ptm-team` 注册为全局命令：

```shell
# 在项目目录下执行
uv tool install .
```

安装后可直接使用：

```shell
# 安装 ptm-tde agent 及其所有 skills 到 Claude Code
ptm-team install claude --agent ptm-tde

# 安装到 Codex
ptm-team install codex --agent ptm-tde

# 预览安装内容（不实际修改文件）
ptm-team install claude --agent ptm-tde --dry-run

# 交互式选择安装 skill
ptm-team install claude --skill

# 模糊匹配安装 skill
ptm-team install claude --skill checkpoint

# 列出已安装内容
ptm-team install claude --list

# 卸载
ptm-team uninstall claude
```

安装 `ptm-tde` agent 时会同步安装它关联的公共 resources。公共因子库归档在仓库 `resource/factor-libraries/`，默认安装到 `~/.ptm-team/resource/factor-libraries/`，可通过 `PTM_TEAM_RESOURCE_HOME` 指向团队共享资源目录。

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
