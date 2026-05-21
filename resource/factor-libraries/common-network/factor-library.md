# 通用网络因子库

## 定位

本库归档跨产品复用的网络基础因子，例如地址、端口、协议和接口状态。它是 `ptm-team` 公共 resource，不属于任何单个 Agent 或特性项目。

## 使用规则

- 公共主库位于 `resource/factor-libraries/common-network/`。
- 安装后位于 `~/.ptm-team/resource/factor-libraries/common-network/`，或 `PTM_TEAM_RESOURCE_HOME/factor-libraries/common-network/`。
- 项目运行时只记录 lock、binding 和候选提案，不回写本库。
- `atomic-ops` 是动作能力来源，不得作为测试因子。
