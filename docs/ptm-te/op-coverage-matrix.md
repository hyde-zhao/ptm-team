---
title: ptm-te op_mapper 覆盖矩阵
version: v1.0
created_at: 2026-07-13
change_ref: CR-028-ptm-te-v2-op-mapper-extension
truth_source: ptm-atomic atoms/fw/*.yaml（118 op）+ 安装版 ptm-atomic 0.1.0 CLI
---

# ptm-te op_mapper 覆盖矩阵

## 概览

ptm-atomic 共 **118 个 op**（`atoms/fw/*.yaml`），分布在 16 个族。ptm-te 的 `op_mapper.py` 当前覆盖情况：

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ mapped | 15 | 已在 `OP_ID_TO_SUBCOMMAND`，op_mapper 可翻译执行 |
| ⚠️ gap | 6 | 源码已定义，但 CLI 安装版未暴露或无 CLI 子命令 |
| ⬜ unmapped | 97 | 未覆盖，按实战需求后续 CR 扩展 |
| **合计** | **118** | |

真相源日期：2026-07-13（`ptm-atomic list` + `atoms/fw/` + 安装版 CLI `--help` 实测）。

## ✅ mapped（15 个，5 族）

| 族 | op_id | CLI 子命令 | 来源 |
|----|-------|-----------|------|
| auth | `fw_login_web_management` | `auth login` | CR-024 v1 |
| policy-route | `fw_config_policy_route` | `policy-route config` | CR-024 v1 |
| policy-route | `fw_update_policy_route` | `policy-route update` | CR-024 v1 |
| policy-route | `fw_delete_policy_route` | `policy-route delete` | CR-024 v1 |
| policy-route | `fw_verify_policy_route` | `policy-route verify` | CR-024 v1 |
| policy-route | `fw_update_policy_route_priority` | `policy-route priority` | CR-024 v1 |
| policy-route | `fw_reset_policy_route_hitcount` | `policy-route reset-hitcount` | CR-024 v1 |
| policy-route | `fw_verify_policy_route_hitcount` | `policy-route verify-hitcount` | CR-024 v1 |
| operation-log | `fw_capture_operation_log` | `operation-log capture` | CR-028 |
| object | `fw_config_object` | `object config` | CR-028 |
| interface | `fw_config_interface` | `interface create`（op_id 含 config 但 action 是 create） | CR-028 |
| interface | `fw_update_interface` | `interface update` | CR-028 |
| interface | `fw_delete_interface` | `interface delete` | CR-028 |
| interface | `fw_delete_batch_interface` | `interface delete-batch` | CR-028 |
| interface | `fw_verify_interface` | `interface verify` | CR-028 |

## ⚠️ gap（6 个，源码有但暂不可用）

| op_id | 族 | 原因 | 激活条件 |
|-------|----|------|---------|
| `fw_update_object` | object | 安装版 ptm-atomic 0.1.0 的 object 族仅暴露 config，update/delete/delete-batch/verify 报 `invalid choice`（源码 `run_object.py build_subtree()` 已定义 5 子命令） | ptm-atomic 升级安装版到匹配源码 |
| `fw_delete_object` | object | 同上 | 同上 |
| `fw_delete_batch_object` | object | 同上 | 同上 |
| `fw_verify_object` | object | 同上 | 同上 |
| `fw_config_batch_object` | object | 无 CLI 子命令（多设备批量配置契约，含 `device_inventory_ref`/`batch_ref`，`run_object.py build_subtree()` 未暴露） | 新增多设备 CLI 入口 |
| `fw_config_batch_interface` | interface | 无 CLI 子命令（同上，多设备批量） | 新增多设备 CLI 入口 |

> object 族 gap 影响 `fw_config_object` 的回滚：其 inverse_op 是 `fw_delete_object`，安装版未暴露，故 `ROLLBACK_STRATEGY.type=none`，回滚待 ptm-atomic 升级。

## ⬜ unmapped（97 个，未覆盖）

按族汇总（未列全量 op_id，按实战需求在后续 CR 扩展）：

| 族 | op 数 | 说明 |
|----|-------|------|
| hainterface | 4 | HA 接口（config/delete_batch/delete/verify） |
| ospfv2_interface | 4 | OSPFv2 接口 |
| ospfv3_interface | 4 | OSPFv3 接口 |
| ospfv2_network | 3 | OSPFv2 网络 |
| ospfv3_network | 3 | OSPFv3 网络 |
| ospfv2_redistribution / ospfv3_redistribution | 4 | OSPF 重分发 |
| ospfv2_global / ospfv3_global | 4 | OSPF 全局 |
| halinkgroup | 3 | HA 链路组 |
| haiplink | 3 | HA IP 链路 |
| iplink / iplink_group | 8 | IP 链路 |
| iptun | 4 | IP 隧道 |
| havrrp | 4 | HA VRRP |
| static_route | 2 | 静态路由 |
| ssl_vpn | 2 | SSL VPN |
| 其余（policy_route_hitcount 细分 / export-file / import-file / reboot 等） | ~52 | 零散或独立功能 |

## 扩展优先级与 follow-up

| 优先级 | 范围 | 触发 | CR |
|--------|------|------|----|
| 已完成 | auth + policy-route + operation-log + object(config) + interface | CR-024/028 | ✅ |
| P2 | object 族 4 gap（update/delete/delete-batch/verify） | ptm-atomic 升级 | CR-029 候选 |
| P2 | hainterface + ospf_interface | HA/OSPF 接口实战需求 | CR-030 候选 |
| P3 | iplink / iptun / static_route / ssl_vpn | 按需 | 视需求 |

## 真相源说明

- **op_id 清单**：`/home/hyde/projects/ptm-atomic/atoms/fw/*.yaml`（118 个）
- **CLI 子命令**：安装版 `ptm-atomic run <family> --help`（runtime 真相源，非源码）
- **op 元数据**（side_effect/rollback/idempotent）：`atoms/fw/<op_id>.yaml`
- **安装版 vs 源码差异**：安装版 0.1.0 的 object 族仅 config，源码已有 5 子命令。op_mapper 按**安装版**扩展（runtime 真相源），源码多的进 gap。
- **`ptm-atomic show` 不可信**：与 yaml 不同步（返回"未识别，建议 sync"），扩展时以 yaml + `build_subtree()` 代码为准。

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|---------|
| v1.0 | 2026-07-13 | host-orchestrator（CR-028） | 创建；mapped 15 / gap 6 / unmapped 97 / total 118 |
| v1.1 | 2026-07-14 | host-orchestrator | 注：`fw_update_policy_route` 的 `--id` 已于 ptm-atomic 0.1.0 注册可用（原 SKILL Gotcha #9 / O-08 风险消除）；update 仍在 mapped，非 gap。 |
