# ptm-team

TGFW测试组 PTM (Product Test Management) Team 项目

## agents

Claude Code 使用的 Agents 集合

### 激活方法

在 clone 了代码之后，你还需要在你的 Code Agent 配置目录中建立软链接，它才可以正确的识别到这些 skills

对于 Claude Code 的话你可以使用以下命令创建软链接
- 先创建 Claude Code 的配置目录 `mkdir -p .claude`
- 再创建 Agents 软链接 `ln -s "$(pwd)/agents" "$(pwd)/.claude/agents"`

### 详细使用帮助

详细使用帮助详见: [agent 使用帮助](agents/README.md)

## script

可使用的单文件工具，详细使用帮助详见： [script 使用帮助](script/README.md)

## skills

项目所有的 skills 工具

### 激活方法

#### 使用工具管理(推荐)

执行以下命令使用 Skills 管理工具，选择激活指定的 skills 或套餐

```shell
uv run script/skills_manager.py
```

#### 全部激活

在 clone 了代码之后，你还需要在你的 Code Agent 配置目录中建立软链接，它才可以正确的识别到这些 skills

对于 Claude Code 的话你可以使用以下命令创建软链接
- 先创建 Claude Code 的配置目录 `mkdir -p .claude`
- 再创建 Skills 软链接 `ln -s "$(pwd)/skills" "$(pwd)/.claude/skills"`

### 详细使用帮助

详细使用帮助详见： [Skills 使用帮助](skills/README.md)
