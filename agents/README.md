# agents

Claude Code 使用的 Agents 集合

## ngfw-factory-installer

用于卸载安装自动化工厂设备的 Agent，在使用之前需要先运行以下脚本加载 Agent 需要用到的 Skills

```shell
uv run script/skills_manager.py --load "自动化工厂运维"
```

然后在 Cluade Code 中可执行以下命令启动 Agent

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

## ptm-tde

MFQ&PPDCS 测试用例设计工具，基于三阶段框架（KYM → MFQ → PPDCS）+ 入口/出口门控（GATE-1 至 GATE-5）推进完整测试分析与用例设计流程。详细说明见 [docs/ptm-tde/README.md](../docs/ptm-tde/README.md)。
