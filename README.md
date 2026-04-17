# ptm-team

TGFW测试组 PTM (Product Test Management) Team 项目

## agents

Claude Code 使用的 Agents 集合

### 使用方法

在 clone 了代码之后，你还需要在你的 Code Agent 配置目录中建立软链接，它才可以正确的识别到这些 skills

对于 Claude Code 的话你可以使用以下命令创建软链接
- 先创建 Claude Code 的配置目录 `mkdir -p .claude`
- 再创建 Agents 软链接 `ln -s "$(pwd)/agents" "$(pwd)/.claude/agents"`

### ngfw-factory-installer

用于卸载安装自动化工厂的 NGFW 软件，在 Cluade Code 中可执行以下命令启动

```shell
claude --allow-dangerously-skip-permissions --agent ngfw-factory-installer
```

执行安装的提示词示例如下

<details>
<summary>点击展开提示词</summary>

```md
给以下设备卸载安装 ngfw
# 第1个设备
设备形态: C3758R
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B007/TGFW-V6R01C02B007-hg-install-release-20260411154810.tar.gz
md5sum: 6648e96ddb27e4a6c65cb15f0a7250ba
# 第2个设备
设备形态: NXP290
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-arm-install-release-20260327154239.tar.gz
md5: 9b6116c6899c864a556b0070e01aad69
# 第3个设备
设备形态: 杰伦老海光-A1500
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-hg-install-release-20260327154048-jl.tar.gz
md5sum: 915e11c579f53fb0147c953a2e70cf7d
# 第4个设备
设备形态: 新海光-乐研海光5380-A2200
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-hg-install-release-20260327160412.tar.gz
md5sum: d84b48ff3c23b27579579dd973a3bf40
# 第5个设备
设备形态：新飞腾-乐研飞腾E2000Q-A600
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-ft-install-release-20260327154345.tar.gz
md5sum: 3682c766b11460eb55af6957a7ce653f
# 第6个设备
设备形态：新飞腾-乐研飞腾E2000Q-A100
安装包: ftp://<IP_ADDRESS>/ngfw/images/V6R01C02B006/TGFW-V6R01C02B006-ft-install-release-20260327154345.tar.gz
md5sum: 3682c766b11460eb55af6957a7ce653f
```

</details>

## script

可使用的单文件工具

### skills_manager.py

Skills 管理工具，可以便捷的启用、禁用 Skill，以及对 Skills 组打包成独立的配置以快速切换，运行命令如下

```shell

```

## skills

项目所有的 skills 工具

### 使用方法

在 clone 了代码之后，你还需要在你的 Code Agent 配置目录中建立软链接，它才可以正确的识别到这些 skills

对于 Claude Code 的话你可以使用以下命令创建软链接
- 先创建 Claude Code 的配置目录 `mkdir -p .claude`
- 再创建 Skills 软链接 `ln -s "$(pwd)/skills" "$(pwd)/.claude/skills"`
