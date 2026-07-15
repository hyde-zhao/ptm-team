#!/usr/bin/env python3
"""op_mapper.py - 策略路由双层映射 + 执行 + 回滚。

真相源锁定三处：
1. run_policy_route.py build_subtree() - 子命令名（config/update/delete/verify/reset-hitcount/verify-hitcount/priority）
2. op yaml inputs.params - 参数名（source_network/dst_network/next_hop_ip/in_interface/type/id）
3. ptm-atomic run ... --help - CLI flag（--source-network 等）

CLI 调用格式（嵌套子命令，非扁平）：
    ptm-atomic run --base-url <url> [--session-file <path>] [--format json] <family> <action> [flags] [--execute]

对应 HLD-CR-024 §4 三层映射 + §9 回滚策略。
LLD: process/stories/STORY-024-03-policy-route-execution-LLD.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


# ===== 异常与类型定义 =====


class OpNotFoundError(Exception):
    """op_id 未在映射表中。"""


class ValidationResult:
    """映射表一致性校验结果。"""

    def __init__(self, passed: bool, mismatches: List[str]):
        self.passed = passed
        self.mismatches = mismatches

    def __str__(self) -> str:
        if self.passed:
            return f"ValidationResult: PASS ({EXPECTED_OP_COUNT} op_id 全覆盖，三表一致)"
        lines = ["ValidationResult: FAIL"]
        for m in self.mismatches:
            lines.append(f"  - {m}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"passed": self.passed, "mismatch_count": len(self.mismatches), "mismatches": self.mismatches}


# ===== 映射表常量（模块级真相源，单点维护） =====

# 第一层映射：op_id -> (family, action) CLI 子命令
# 真相源：run_policy_route.py / run_auth.py / run_object.py / run_interface.py / run_operation_log.py build_subtree()
# 共 15 个 op_id（1 auth + 7 policy-route + 1 operation-log + 1 object + 5 interface）
# 注：安装版 ptm-atomic 0.1.0 的 object 族仅暴露 config；update/delete/delete-batch/verify 源码已定义但安装版未暴露，
#     记入 op 覆盖矩阵 gap（docs/ptm-te/op-coverage-matrix.md），ptm-atomic 升级后可激活。
OP_ID_TO_SUBCOMMAND: Dict[str, Tuple[str, str]] = {
    # auth 族（来源 run_auth.py）
    "fw_login_web_management": ("auth", "login"),
    # policy-route 族（来源 run_policy_route.py build_subtree()，7 个）
    "fw_config_policy_route": ("policy-route", "config"),
    "fw_update_policy_route": ("policy-route", "update"),
    "fw_delete_policy_route": ("policy-route", "delete"),
    "fw_verify_policy_route": ("policy-route", "verify"),
    "fw_update_policy_route_priority": ("policy-route", "priority"),
    "fw_reset_policy_route_hitcount": ("policy-route", "reset-hitcount"),
    "fw_verify_policy_route_hitcount": ("policy-route", "verify-hitcount"),
    # operation-log 族（来源 run_operation_log.py，1 个）
    "fw_capture_operation_log": ("operation-log", "capture"),
    # object 族（来源 run_object.py；安装版 0.1.0 仅 config 可用）
    "fw_config_object": ("object", "config"),
    # interface 族（来源 run_interface.py，5 个）
    # 注意：fw_config_interface 的 op_id 含 "config" 但 CLI action 是 "create"（run_interface.py _run_create 确认）
    "fw_config_interface": ("interface", "create"),
    "fw_update_interface": ("interface", "update"),
    "fw_delete_interface": ("interface", "delete"),
    "fw_delete_batch_interface": ("interface", "delete-batch"),
    "fw_verify_interface": ("interface", "verify"),
}

# 第二层映射：args key -> CLI flag（per op_id）
# 三层命名翻译 centralize 在此：ptm-tde PC args -> op yaml params -> CLI flag
# 真相源：run_policy_route.py _add_*_args() + op yaml inputs.params + CLI --help
ARGS_TO_FLAGS: Dict[str, Dict[str, str]] = {
    "fw_login_web_management": {
        # login 签名：--username + --password-env（禁止明文密码，HLD §7）
        "username": "--username",
        "password_env": "--password-env",  # 默认值 "FW_WEB_PASSWORD"
    },
    "fw_config_policy_route": {
        # config 使用 _add_common_args
        # CR-025 后 args key 对齐 op yaml params（source_network 等），三层退化为两层
        "source_network": "--source-network",
        "dst_network": "--dst-network",
        "next_hop_ip": "--next-hop-ip",
        "in_interface": "--in-interface",  # params 与 flag 仅连字符差异
        "type": "--policy-route-type",  # flag 加前缀，需显式
    },
    "fw_update_policy_route": {
        # update 使用 _add_common_args + _require_arg(id)
        # 与 config 相同的 5 个 flag + 额外 --id（从 verify 查询获取目标策略路由 id）
        "source_network": "--source-network",
        "dst_network": "--dst-network",
        "next_hop_ip": "--next-hop-ip",
        "in_interface": "--in-interface",
        "type": "--policy-route-type",
        "id": "--id",  # 注意：CLI help 未暴露 --id（O-08 风险，见 Gotcha #10）
    },
    "fw_delete_policy_route": {
        # delete 使用 _add_delete_args
        "id": "--id",
        "type": "--policy-route-type",
    },
    "fw_verify_policy_route": {
        # verify 使用 _add_verify_args（无 required）
        "type": "--policy-route-type",
        "page": "--page",
        "size": "--size",
    },
    "fw_update_policy_route_priority": {
        # priority 使用 _add_priority_args
        "type": "--policy-route-type",
        "moveid": "--moveid",
        "targetid": "--targetid",
        "targetsite": "--targetsite",
    },
    "fw_reset_policy_route_hitcount": {
        # reset-hitcount 使用 _add_delete_args
        "id": "--id",
        "type": "--policy-route-type",
    },
    "fw_verify_policy_route_hitcount": {
        # verify-hitcount 使用 _add_verify_args（无 required）
        "type": "--policy-route-type",
        "page": "--page",
        "size": "--size",
    },
    # operation-log 族（fw_capture_operation_log）
    # args key 对齐 op yaml params：page/size/timetype/starttime/endtime
    "fw_capture_operation_log": {
        "page": "--page",
        "size": "--size",
        "timetype": "--timetype",
        "starttime": "--starttime",
        "endtime": "--endtime",
    },
    # object 族（fw_config_object，安装版 0.1.0 仅 config 可用）
    # args key 对齐 op yaml params：object_name/ipaddr/mask/object_desc
    "fw_config_object": {
        "object_name": "--object-name",
        "ipaddr": "--ipaddr",
        "mask": "--mask",
        "object_desc": "--object-desc",
    },
    # interface 族
    # 注：op yaml params 是嵌套 val.{name,type,mode,ip_addresses}，CLI flag 是扁平 --name/--interface-kind/--mode/--ip-address
    # args key 采用 CLI flag 的 snake_case（interface_kind/ip_address），对应 params.val.type / params.val.ip_addresses
    # 已知限制：params.val.type 是数字（如 14=bvi），--interface-kind 是枚举 {bvi,sub,physical,bond,tunnel}，
    #           ptm-tde 产出 PC 时应直接给枚举字符串；布尔 flag（--interface-enabled/--interface-disabled）留 follow-up
    "fw_config_interface": {
        "id": "--id",
        "interface_kind": "--interface-kind",
        "mode": "--mode",
        "name": "--name",
        "desc": "--desc",
        "ip_address": "--ip-address",
        "parent_name": "--parent-name",
        "sub_id": "--sub-id",
        "bvi_instance": "--bvi-instance",
        "bond_id": "--bond-id",
        "bond_member": "--bond-member",
    },
    "fw_update_interface": {
        # update 与 create 共享参数集
        "id": "--id",
        "interface_kind": "--interface-kind",
        "mode": "--mode",
        "name": "--name",
        "desc": "--desc",
        "ip_address": "--ip-address",
        "parent_name": "--parent-name",
        "sub_id": "--sub-id",
        "bvi_instance": "--bvi-instance",
        "bond_id": "--bond-id",
        "bond_member": "--bond-member",
    },
    "fw_delete_interface": {
        # delete 使用 _add_delete_args：--id 或 --payload-file/--payload-json
        "id": "--id",
        "payload_file": "--payload-file",
        "payload_json": "--payload-json",
    },
    "fw_delete_batch_interface": {
        "id": "--id",
        "payload_file": "--payload-file",
        "payload_json": "--payload-json",
    },
    "fw_verify_interface": {
        "id": "--id",
    },
}

# required flag 校验表（来源 run_policy_route.py _add_*_args 的 required=True）
# build_command 时校验，缺失则抛 ValueError
REQUIRED_FLAGS: Dict[str, List[str]] = {
    "fw_login_web_management": [],
    "fw_config_policy_route": ["--source-network", "--in-interface"],
    "fw_update_policy_route": ["--source-network", "--in-interface", "--id"],
    "fw_delete_policy_route": ["--id"],
    "fw_verify_policy_route": [],
    "fw_update_policy_route_priority": ["--targetsite", "--targetid", "--moveid"],
    "fw_reset_policy_route_hitcount": ["--id"],
    "fw_verify_policy_route_hitcount": [],
    # operation-log / object / interface 族（CR-028 扩展）
    "fw_capture_operation_log": ["--page", "--size", "--timetype"],
    "fw_config_object": ["--object-name", "--ipaddr", "--mask"],
    "fw_config_interface": ["--interface-kind"],
    "fw_update_interface": ["--id", "--interface-kind"],
    "fw_delete_interface": ["--id"],
    "fw_delete_batch_interface": ["--id"],
    "fw_verify_interface": ["--id"],
}

# 回滚策略表（真相源：ptm-atomic list 2026-07-10 实测 rollback 字段）
# ROLLBACK_STRATEGY.type 与 OP_METADATA.rollback 交叉一致
ROLLBACK_STRATEGY: Dict[str, Dict[str, Any]] = {
    "fw_login_web_management": {
        "type": "none",
        "reason": "observation，只读，建立 session，不回滚",
    },
    "fw_config_policy_route": {
        "type": "inverse_op",
        "inverse_op_id": "fw_delete_policy_route",
        "inverse_args_key": "id",  # 从 config 返回 data.policy_route_id 取 id
        "snapshot_required": False,
    },
    "fw_update_policy_route": {
        "type": "restore_snapshot",
        "snapshot_source": "full_config",
        "restore_op_id": "fw_update_policy_route",
        "snapshot_required": True,
    },
    "fw_delete_policy_route": {
        "type": "restore_snapshot",
        "snapshot_source": "full_config",
        "restore_op_id": "fw_config_policy_route",
        "snapshot_required": True,
        "as_cleanup_skip": True,  # 作为 config 清理动作时不触发回滚
    },
    "fw_verify_policy_route": {
        "type": "none",
        "reason": "observation，只读，不回滚",
    },
    "fw_update_policy_route_priority": {
        "type": "none",
        "reason": "无 rollback 元数据，由用例设计决定是否恢复原优先级",
    },
    "fw_reset_policy_route_hitcount": {
        "type": "irreversible",
        "reason": "命中计数清零不可恢复，不回滚",
    },
    "fw_verify_policy_route_hitcount": {
        "type": "none",
        "reason": "observation，只读，不回滚",
    },
    # operation-log 族（CR-028 扩展）
    "fw_capture_operation_log": {
        "type": "none",
        "reason": "observation，只读查询，不回滚",
    },
    # object 族
    # ptm-atomic 已补 fw_delete_object（id_source=args，id 即 object_name）；
    # ptm-te op 覆盖扩展（OP_ID_TO_SUBCOMMAND 增 fw_delete_object）后可翻转为 inverse_op，
    # 届时回滚经 resolve_id 模式 B 自动解析。当前未映射，保持 none 避免回滚触发 OP_NOT_FOUND。
    "fw_config_object": {
        "type": "none",
        "reason": "fw_delete_object 未在 ptm-te op 覆盖内，待扩展后翻转为 inverse_op（mode B）",
    },
    # acl_policy 族 / acl_policy_group：id_source 声明已在 ptm-atomic（mode C query / mode D placeholder），
    # 经 `ptm-atomic show` 由 resolve_id/build_inverse_args 声明驱动解析；
    # 端到端回滚待 ptm-te op 覆盖扩展（config/update/delete/verify 映射）后激活。
    # interface 族
    "fw_config_interface": {
        "type": "inverse_op",
        "inverse_op_id": "fw_delete_interface",
        "inverse_args_key": "id",
        "snapshot_required": False,
    },
    "fw_update_interface": {
        "type": "restore_snapshot",
        "snapshot_source": "full_config",
        "restore_op_id": "fw_update_interface",
        "snapshot_required": True,
    },
    "fw_delete_interface": {
        "type": "none",
        "reason": "fw_delete_interface.yaml 无 rollback_strategy 字段（源码未定义，2026-07-13 实测），由用例设计承担；作为 config 清理动作时不触发回滚",
        "as_cleanup_skip": True,
    },
    "fw_delete_batch_interface": {
        "type": "irreversible",
        "reason": "批量删除，无 rollback 元数据，由用例设计承担",
    },
    "fw_verify_interface": {
        "type": "none",
        "reason": "observation，只读，不回滚",
    },
}

# OP 元数据缓存（来源 ptm-atomic list 实测，2026-07-10）
# 字段名与 ptm-atomic list 输出一致：side_effect / rollback / idempotent
OP_METADATA: Dict[str, Dict[str, Any]] = {
    "fw_config_policy_route": {
        "side_effect": "state_mutation",
        "rollback": "inverse_op:fw_delete_policy_route",
        "idempotent": True,
    },
    "fw_update_policy_route": {
        "side_effect": "state_mutation",
        "rollback": "restore_snapshot",
        "idempotent": True,
    },
    "fw_delete_policy_route": {
        "side_effect": "destructive",
        "rollback": "restore_snapshot",
        "idempotent": False,
    },
    "fw_verify_policy_route": {
        "side_effect": "observation",
        "rollback": "",
        "idempotent": True,
    },
    "fw_update_policy_route_priority": {
        "side_effect": "",
        "rollback": "",
        "idempotent": True,
    },
    "fw_reset_policy_route_hitcount": {
        "side_effect": "state_mutation",
        "rollback": "irreversible",
        "idempotent": True,
    },
    "fw_verify_policy_route_hitcount": {
        "side_effect": "observation",
        "rollback": "",
        "idempotent": True,
    },
    "fw_login_web_management": {
        "side_effect": "observation",
        "rollback": "",
        "idempotent": True,
    },
    # operation-log 族（CR-028 扩展，真相源 atoms/fw/ yaml）
    "fw_capture_operation_log": {
        "side_effect": "observation",
        "rollback": "",
        "idempotent": True,
    },
    # object 族
    "fw_config_object": {
        "side_effect": "state_mutation",
        "rollback": "",  # fw_delete_object 未在 ptm-te op 覆盖内，待扩展后标 inverse_op:fw_delete_object
        "idempotent": True,
    },
    # interface 族
    "fw_config_interface": {
        "side_effect": "state_mutation",
        "rollback": "inverse_op:fw_delete_interface",
        "idempotent": True,
    },
    "fw_update_interface": {
        "side_effect": "state_mutation",
        "rollback": "restore_snapshot",
        "idempotent": True,
    },
    "fw_delete_interface": {
        "side_effect": "destructive",
        "rollback": "",  # yaml 无 rollback_strategy 字段（2026-07-13 实测）
        "idempotent": False,
    },
    "fw_delete_batch_interface": {
        "side_effect": "destructive",
        "rollback": "irreversible",
        "idempotent": False,
    },
    "fw_verify_interface": {
        "side_effect": "observation",
        "rollback": "",
        "idempotent": True,
    },
}

# 预期 op_id 总数（校验基准）：8（v1）+ 7（CR-028 新增 operation-log/object/interface）= 15
EXPECTED_OP_COUNT = 15


# ===== 第一层映射 =====


def map_op_id_to_subcommand(op_id: str) -> Tuple[str, str]:
    """第一层映射：op_id -> (family, action) CLI 子命令。

    Args:
        op_id: ptm-tde PC 中的 atomic_op.op_id，如 "fw_config_policy_route"

    Returns:
        (family, action) 元组，如 ("policy-route", "config")

    Raises:
        OpNotFoundError: op_id 不在 OP_ID_TO_SUBCOMMAND 中时抛出
    """
    if op_id not in OP_ID_TO_SUBCOMMAND:
        raise OpNotFoundError(
            f"未识别的 op_id: {op_id}，当前映射表覆盖 {len(OP_ID_TO_SUBCOMMAND)} 个 op_id。"
            f"请反馈 ptm-tae 检查工具覆盖。"
        )
    return OP_ID_TO_SUBCOMMAND[op_id]


# ===== 第二层映射 =====


def map_args_to_flags(op_id: str, args: dict) -> List[str]:
    """第二层映射：args dict -> CLI flag 列表。

    三层命名翻译 centralize 在此：args key -> flag name 取自 ARGS_TO_FLAGS[op_id]。
    args 中多余 key 忽略并记录 warning 到 stderr。

    Args:
        op_id: 原子操作 ID
        args: ptm-tde PC 的 atomic_op.args dict

    Returns:
        CLI flag 列表，如 ["--source-network", "<IP_ADDRESS>/24", "--in-interface", "GE0_12"]

    Raises:
        OpNotFoundError: op_id 不在 ARGS_TO_FLAGS 中
    """
    if op_id not in ARGS_TO_FLAGS:
        raise OpNotFoundError(f"op_id {op_id} 无 args->flag 映射表")
    flag_map = ARGS_TO_FLAGS[op_id]
    result: List[str] = []
    for args_key, cli_flag in flag_map.items():
        if args_key in args and args[args_key] is not None:
            value = args[args_key]
            # password_env 特殊处理：空值时默认 FW_WEB_PASSWORD
            if args_key == "password_env" and not value:
                value = "FW_WEB_PASSWORD"
            result.append(cli_flag)
            result.append(str(value))
        elif args_key == "password_env" and op_id == "fw_login_web_management":
            # login 的 password_env 默认值补全
            result.append(cli_flag)
            result.append("FW_WEB_PASSWORD")
    # 检查多余 key，记录 warning
    for key in args:
        if key not in flag_map:
            print(
                f"[op_mapper] WARNING: args key '{key}' 不在 {op_id} 映射表中，已忽略",
                file=sys.stderr,
            )
    return result


# ===== required flag 校验 =====


def _check_required_flags(op_id: str, flag_list: List[str]) -> None:
    """校验 required flag 是否存在（如 config 的 --source-network / --in-interface）。

    Args:
        op_id: 原子操作 ID
        flag_list: 已生成的 flag 列表（含值，如 ["--source-network", "<IP_ADDRESS>/24", ...]）

    Raises:
        ValueError: required flag 缺失
    """
    required = REQUIRED_FLAGS.get(op_id, [])
    # flag_list 是 [flag, value, flag, value, ...] 交替格式
    # 只取偶数索引位置（flag 名）
    present_flags = set(flag_list[::2])
    for req in required:
        if req not in present_flags:
            raise ValueError(
                f"op_id {op_id} 缺少 required flag: {req}。" f"当前 flag 列表: {flag_list}"
            )


# ===== 参数合法性预检（P2-11）=====


class ValidationError(Exception):
    """参数合法性预检失败（error_type=PARAM_INVALID）。"""


# 占位符正则：<xxx> / TBD / N/A / 待补 / 占位（不区分大小写）
_PLACEHOLDER_RE = re.compile(r"^(<[^>]*>|TBD|N/?A|待补|占位)$", re.IGNORECASE)
# 对象名正则：字母开头 + 字母/数字/下划线
_OBJ_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _is_ipv4(val: str) -> bool:
    """粗判是否为 IPv4 地址（x.x.x.x）。"""
    parts = val.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def validate_args(op_id: str, args: dict) -> None:
    """参数合法性预检（build_command 前调用）。

    预检维度（静态格式，不触网）：
    - 占位符检测：值非 <xxx>/TBD/N/A/待补/占位（需具体值）
    - 对象名格式：source_network/dst_network 若非 CIDR/IP 则视为对象名，校验命名规范
    - IP 格式：next_hop_ip 需为合法 IPv4

    预检失败抛 ValidationError，调用方转为 envelope error_type=PARAM_INVALID。
    引用对象存在性（config 前 verify 查询对象是否存在）留 v2，此处只做静态格式预检。

    Args:
        op_id: 原子操作 ID
        args: ptm-tde PC 的 atomic_op.args dict

    Raises:
        ValidationError: 参数格式非法或占位
    """
    if not isinstance(args, dict):
        raise ValidationError(f"args 不是 dict: {type(args).__name__}")

    for key, value in args.items():
        if value is None or not isinstance(value, str):
            continue
        val = value.strip()
        if _PLACEHOLDER_RE.match(val):
            raise ValidationError(
                f"op_id {op_id} 参数 '{key}' 值 '{val}' 是占位符，需填具体值"
            )

    # 对象名参数格式校验（source_network/dst_network 若非 CIDR/IP 视为对象名）
    for key in ("source_network", "dst_network"):
        if key in args and isinstance(args[key], str):
            val = args[key].strip()
            if not val:
                continue
            if "/" in val or _is_ipv4(val):
                continue  # CIDR/IP 跳过对象名校验
            if not _OBJ_NAME_RE.match(val):
                raise ValidationError(
                    f"op_id {op_id} 参数 '{key}' 值 '{val}' 非合法对象名"
                    f"（需字母开头标识符）也非 CIDR/IP"
                )

    # next_hop_ip 格式校验
    if "next_hop_ip" in args and isinstance(args["next_hop_ip"], str):
        val = args["next_hop_ip"].strip()
        if val and not _is_ipv4(val):
            raise ValidationError(
                f"op_id {op_id} 参数 'next_hop_ip' 值 '{val}' 非合法 IPv4"
            )


# ===== 命令构建 =====


def build_command(
    op_id: str,
    args: dict,
    base_url: str,
    session_file: str,
    *,
    dry_run: bool = True,
) -> List[str]:
    """组装完整的 ptm-atomic run 嵌套子命令列表。

    命令格式（嵌套子命令，非扁平）：
        ptm-atomic run --base-url <url> [--session-file <path>] --format json <family> <action> [flags] [--execute]

    dry_run=True 时不加 --execute（默认干跑）。
    dry_run=False 时加 --execute。

    Args:
        op_id: 原子操作 ID
        args: 参数 dict
        base_url: 设备 Web 管理地址，如 "https://<IP_ADDRESS>"
        session_file: session-<run-id>.json 路径
        dry_run: 是否干跑模式（默认 True）

    Returns:
        命令列表

    Raises:
        OpNotFoundError: op_id 未识别
        ValueError: required flag 缺失
    """
    family, action = map_op_id_to_subcommand(op_id)
    flags = map_args_to_flags(op_id, args)
    _check_required_flags(op_id, flags)
    validate_args(op_id, args)  # P2-11 参数合法性预检
    command: List[str] = [
        "ptm-atomic",
        "run",
        "--base-url",
        base_url,
        "--session-file",
        session_file,
        "--format",
        "json",  # 统一 JSON 输出便于解析
        family,
        action,
        *flags,
    ]
    if not dry_run:
        command.append("--execute")
    return command


# ===== 工具函数 =====


def _build_envelope(
    op_id: str,
    step_name: str,
    status: str,
    data: dict,
    error_type: str,
    diag_snapshot_ref: str = "",
    runtime_authorization: Optional[dict] = None,
) -> dict:
    """构建标准 envelope dict。

    envelope 字段：op_id / step_name / status / data / error_type / diag_snapshot_ref
    P2-9: dry_run=False 时附加 runtime_authorization（who/scope/authorized_at/reason）用于审计。
    """
    envelope = {
        "op_id": op_id,
        "step_name": step_name,
        "status": status,
        "data": data,
        "error_type": error_type,
        "diag_snapshot_ref": diag_snapshot_ref,
    }
    if runtime_authorization is not None:
        envelope["runtime_authorization"] = runtime_authorization
    return envelope


def _build_exec_env(base_url: str) -> dict:
    """构建 subprocess 环境变量，确保设备直连不走代理（P2-12）。

    WSL2 等代理环境下，ptm-atomic 的 HTTPS 调用可能误走 HTTP_PROXY/HTTPS_PROXY。
    本函数从 base_url 提取设备 IP/主机，加入 NO_PROXY，保留其他环境变量。

    Args:
        base_url: 设备 Web 管理地址，如 "https://<IP_ADDRESS>"

    Returns:
        env dict（os.environ 副本 + NO_PROXY 含设备 IP）
    """
    env = dict(os.environ)
    # 从 base_url 提取主机（去协议和端口）
    host = base_url
    for prefix in ("https://", "http://"):
        if host.startswith(prefix):
            host = host[len(prefix):]
            break
    host = host.split("/")[0].split(":")[0]
    # 合并到 NO_PROXY（保留已有值）
    existing_no_proxy = env.get("NO_PROXY", "")
    no_proxy_parts = [p.strip() for p in existing_no_proxy.split(",") if p.strip()]
    if host not in no_proxy_parts:
        no_proxy_parts.append(host)
    env["NO_PROXY"] = ",".join(no_proxy_parts)
    return env


def _append_exec_log(log_path: str, record: dict) -> None:
    """向 exec-log.jsonl 追加一条记录（JSON Lines 格式）。

    Args:
        log_path: exec-log.jsonl 文件路径
        record: 日志记录 dict
    """
    try:
        # 确保目录存在
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[op_mapper] WARNING: 写入 exec-log 失败: {e}", file=sys.stderr)


# ===== 步骤间引用（step-refs + ${STEP-N.id} 插值）=====
#
# 替代 LLM 手动从 envelope.data.policy_route_id 提取 id 填入下一步 args["id"]。
# 每个 step 执行后落盘 step-refs/<step_id>.json = {step_id, op_id, args, envelope}；
# 后续 step 的 args 可用 ${STEP-N.id}（或 ${STEP-N.<field>}）引用前序 step 的值，
# execute_op 在 build_command 前按被引 step op 的 id_source 声明自动插值。


_STEP_REF_RE = re.compile(r"^\$\{(STEP-[A-Za-z0-9_-]+)\.([A-Za-z0-9_]+)\}$")


def _write_step_ref(
    step_refs_dir: str,
    step_id: str,
    op_id: str,
    args: dict,
    envelope: dict,
) -> None:
    """落盘单个 step 的引用数据包到 <step_refs_dir>/<step_id>.json（仅成功 step）。"""
    if not step_id:
        return
    try:
        if not os.path.isdir(step_refs_dir):
            os.makedirs(step_refs_dir, exist_ok=True)
        record = {
            "step_id": step_id,
            "op_id": op_id,
            "args": args,
            "envelope": envelope,
        }
        path = os.path.join(step_refs_dir, f"{step_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, indent=2))
    except OSError as e:
        print(f"[op_mapper] WARNING: 写入 step-ref 失败: {e}", file=sys.stderr)


def _read_step_ref(step_refs_dir: str, ref_step_id: str) -> Optional[dict]:
    """读取前序 step 的引用数据包。"""
    path = os.path.join(step_refs_dir, f"{ref_step_id}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def resolve_step_refs(
    args: dict,
    step_refs_dir: Optional[str],
    *,
    base_url: str = "",
    session_file: str = "",
    authorized: bool = False,
    timeout: int = 30,
) -> dict:
    """扫描 args 值中的 ${STEP-N.<field>} 占位符，从前序 step-ref 解析并替换。

    支持：
      ${STEP-001.id}      -> 被引 step 的 id（按其 op 的 id_source 声明经 resolve_id 解析）
      ${STEP-001.<field>} -> 被引 step envelope.data[<field>]，缺失则 args[<field>]
    无 step_refs_dir 或无匹配占位符 -> 原样返回（向后兼容，LLM 仍可手动传 id）。
    占位符无法解析 -> 抛 ValueError（execute_op 捕获为 VALIDATION_FAILED envelope）。
    """
    if not step_refs_dir or not isinstance(args, dict):
        return args
    resolved: dict = {}
    for key, val in args.items():
        if not isinstance(val, str):
            resolved[key] = val
            continue
        m = _STEP_REF_RE.match(val.strip())
        if not m:
            resolved[key] = val
            continue
        ref_step_id, field = m.group(1), m.group(2)
        ref = _read_step_ref(step_refs_dir, ref_step_id)
        if ref is None:
            raise ValueError(
                f"步骤引用 {val} 无法解析：step-refs/{ref_step_id}.json 不存在"
            )
        if field == "id":
            v = resolve_id(
                ref.get("op_id"), ref.get("envelope"), ref.get("args", {}) or {},
                base_url=base_url, session_file=session_file,
                authorized=authorized, timeout=timeout,
            )
            if v in (None, "", 0):
                raise ValueError(
                    f"步骤引用 {val} 未解析（被引 op 无 id_source 声明或解析失败）"
                )
            resolved[key] = v
        else:
            env = ref.get("envelope") if isinstance(ref.get("envelope"), dict) else {}
            data = env.get("data") if isinstance(env.get("data"), dict) else {}
            v = data.get(field)
            if v in (None, "", 0):
                v = (ref.get("args") or {}).get(field)
            if v in (None, "", 0):
                raise ValueError(f"步骤引用 {val} 字段 '{field}' 在被引 step 中不存在")
            resolved[key] = v
    return resolved


def _parse_atomic_output(stdout: str) -> Optional[dict]:
    """解析 ptm-atomic CLI 输出（JSON 或 YAML）为 dict。

    op_mapper 统一使用 --format json，优先 json.loads。
    若 JSON 解析失败，尝试 YAML（兼容 ptm-atomic 默认 yaml 输出场景）。

    Args:
        stdout: ptm-atomic CLI 的标准输出

    Returns:
        解析后的 dict，解析失败返回 None
    """
    if not stdout or not stdout.strip():
        return None
    # 优先 JSON 解析
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        pass
    # 兼容 YAML（ptm-atomic 默认 --format yaml）
    try:
        import yaml  # type: ignore[import-untyped]

        return yaml.safe_load(stdout)
    except ImportError:
        # yaml 不可用时，尝试简单提取（不依赖第三方包）
        return None
    except Exception:
        return None


# ===== session 重连 =====


def _reconnect_and_retry(
    base_url: str,
    session_file: str,
    username: str,
    password_env: str,
    retry_command: List[str],
    timeout: int,
) -> dict:
    """STATE_INVALID 自动重连：重新 auth login 后重试原命令。

    流程：
    1. 执行 auth login（--username --password-env --session-file --execute）
    2. login 成功 -> 重试原 retry_command
    3. login 失败 -> 返回 error_type=AUTH_FAILED，不重试原命令
    4. 重试上限：1 次（避免无限循环）

    Args:
        base_url: 设备 Web 管理地址
        session_file: session-<run-id>.json 路径
        username: 登录用户名
        password_env: 密码环境变量名
        retry_command: 待重试的完整命令列表
        timeout: 超时秒数

    Returns:
        重试后的 envelope dict
    """
    # [1] 重新 login
    login_cmd: List[str] = [
        "ptm-atomic",
        "run",
        "--base-url",
        base_url,
        "--session-file",
        session_file,
        "--format",
        "json",
        "auth",
        "login",
        "--username",
        username,
        "--password-env",
        password_env,
        "--execute",
    ]
    try:
        login_proc = subprocess.run(
            login_cmd, capture_output=True, text=True, timeout=timeout,
            env=_build_exec_env(base_url),
        )
        login_envelope = _parse_atomic_output(login_proc.stdout)
        if login_envelope is None or login_envelope.get("status") != "success":
            return _build_envelope(
                "",
                "",
                "error",
                {
                    "reason": "重连登录失败",
                    "login_stdout": login_proc.stdout[:500],
                    "login_stderr": login_proc.stderr[:500],
                },
                "AUTH_FAILED",
                "",
            )
    except subprocess.TimeoutExpired:
        return _build_envelope(
            "", "", "error", {"reason": "重连登录超时"}, "AUTH_FAILED", ""
        )

    # [2] 重试原命令
    try:
        proc = subprocess.run(
            retry_command, capture_output=True, text=True, timeout=timeout,
            env=_build_exec_env(base_url),
        )
        envelope = _parse_atomic_output(proc.stdout)
        if envelope is None:
            return _build_envelope(
                "",
                "",
                "error",
                {
                    "reason": "重试后仍无法解析输出",
                    "stdout": proc.stdout[:500],
                    "stderr": proc.stderr[:500],
                },
                "UNKNOWN_ERROR",
                "",
            )
        return envelope
    except subprocess.TimeoutExpired:
        return _build_envelope(
            "", "", "error", {"reason": "重试执行超时"}, "EXEC_FAILED", ""
        )


# ===== 执行 =====


def execute_op(
    op_id: str,
    args: dict,
    base_url: str,
    session_file: str,
    *,
    step_name: str = "",
    dry_run: bool = True,
    authorized: bool = False,
    timeout: int = 30,
    username: str = "admin",
    password_env: str = "FW_WEB_PASSWORD",
    exec_log_path: Optional[str] = None,
    diag_snapshot_ref: str = "",
    step_id: str = "",
    step_refs_dir: Optional[str] = None,
) -> dict:
    """执行单条原子操作，返回 envelope dict。

    流程：
    1. （若 step_refs_dir）resolve_step_refs 插值 args 中的 ${STEP-N.id} 引用
    2. build_command 组装命令
    3. dry_run=False 且 authorized=False 时拒绝执行（返回 error_type=EXEC_FAILED）
    4. subprocess 调用 ptm-atomic CLI
    5. 解析输出为 envelope
    6. 检测 STATE_INVALID -> _reconnect_and_retry（最多 1 次）
    7. 写入 exec-log.jsonl（若 exec_log_path 提供）
    8. 写入 step-refs/<step_id>.json（若 step_refs_dir + step_id + 成功）

    Args:
        op_id: 原子操作 ID
        args: 参数 dict（值可含 ${STEP-N.id} 占位符，由 resolve_step_refs 插值）
        base_url: 设备 Web 管理地址
        session_file: session-<run-id>.json 路径
        step_name: 用例步骤名（写入 envelope）
        dry_run: 是否干跑（默认 True）
        authorized: --execute 写操作授权标记（dry_run=False 时必须为 True）
        timeout: 超时秒数（默认 30，与 op yaml timeout_ms 一致）
        username: 登录用户名（STATE_INVALID 重连用）
        password_env: 密码环境变量名（STATE_INVALID 重连用）
        exec_log_path: 执行日志路径（None 则不写日志）
        diag_snapshot_ref: 诊断快照引用路径
        step_id: 步骤 ID（如 STEP-001），用于 step-refs 落盘与跨步引用
        step_refs_dir: step-refs 目录（runs/<run-id>/step-refs/，None 则不落盘不插值）

    Returns:
        envelope dict，含 op_id/step_name/status/data/error_type/diag_snapshot_ref
    """
    # [1] 步骤引用插值 + 构建命令
    try:
        if step_refs_dir:
            # 插值 args 中的 ${STEP-N.id}（按被引 step op 的 id_source 声明解析）
            args = resolve_step_refs(
                args, step_refs_dir,
                base_url=base_url, session_file=session_file,
                authorized=authorized, timeout=timeout,
            )
        command = build_command(
            op_id, args, base_url, session_file, dry_run=dry_run
        )
    except OpNotFoundError as e:
        return _build_envelope(
            op_id, step_name, "error", {"reason": str(e)}, "OP_NOT_FOUND", diag_snapshot_ref
        )
    except ValidationError as e:
        return _build_envelope(
            op_id, step_name, "error", {"reason": str(e)}, "PARAM_INVALID", diag_snapshot_ref
        )
    except ValueError as e:
        return _build_envelope(
            op_id, step_name, "error", {"reason": str(e)}, "VALIDATION_FAILED", diag_snapshot_ref
        )

    # [2] 授权检查（dry-run 默认门，ADR-04）
    if not dry_run and not authorized:
        return _build_envelope(
            op_id,
            step_name,
            "error",
            {"reason": "dry_run=False 需要 authorized=True 授权标记"},
            "EXEC_FAILED",
            diag_snapshot_ref,
        )

    # P2-9 授权落盘审计（dry_run=False 时记录 who/scope/authorized_at）
    runtime_auth = None
    if not dry_run:
        runtime_auth = {
            "who": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            "scope": f"{op_id} on {base_url}",
            "authorized_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "reason": "dry_run=False 用户单次授权（ADR-04 dry-run 默认门）",
        }

    # [3] 执行
    start_time = time.time()
    exit_code = -1
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
            env=_build_exec_env(base_url),
        )
        exit_code = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        envelope = _build_envelope(
            op_id,
            step_name,
            "error",
            {"reason": f"执行超时 ({timeout}s)", "command": command},
            "EXEC_FAILED",
            diag_snapshot_ref,
        )
        if runtime_auth is not None:
            envelope["runtime_authorization"] = runtime_auth
        if exec_log_path:
            _append_exec_log(
                exec_log_path,
                {
                    "step_name": step_name,
                    "op_id": op_id,
                    "mode": "dry-run" if dry_run else "execute",
                    "command": command,
                    "exit_code": -1,
                    "envelope": envelope,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "duration_ms": duration_ms,
                },
            )
        return envelope

    duration_ms = int((time.time() - start_time) * 1000)

    # [4] 解析输出
    envelope = _parse_atomic_output(stdout)
    if envelope is None:
        envelope = _build_envelope(
            op_id,
            step_name,
            "error",
            {
                "reason": "无法解析 ptm-atomic 输出",
                "stdout": stdout[:500],
                "stderr": stderr[:500],
                "exit_code": exit_code,
            },
            "UNKNOWN_ERROR",
            diag_snapshot_ref,
        )
    else:
        # 补全 envelope 字段
        envelope["op_id"] = op_id
        envelope["step_name"] = step_name
        if "error_type" not in envelope:
            envelope["error_type"] = "NONE" if envelope.get("status") == "success" else "UNKNOWN_ERROR"
        if "diag_snapshot_ref" not in envelope:
            envelope["diag_snapshot_ref"] = diag_snapshot_ref

    # [5] STATE_INVALID 自动重连（仅 execute 模式，最多 1 次）
    if envelope.get("error_type") == "STATE_INVALID" and not dry_run:
        envelope = _reconnect_and_retry(
            base_url, session_file, username, password_env, command, timeout
        )
        envelope["op_id"] = op_id
        envelope["step_name"] = step_name
        if "diag_snapshot_ref" not in envelope:
            envelope["diag_snapshot_ref"] = diag_snapshot_ref

    # P2-9 附加授权审计（dry_run=False 时，覆盖正常/解析失败/重连路径）
    if runtime_auth is not None and "runtime_authorization" not in envelope:
        envelope["runtime_authorization"] = runtime_auth

    # [6] 写入 exec-log
    if exec_log_path:
        record = {
            "step_name": step_name,
            "op_id": op_id,
            "mode": "dry-run" if dry_run else "execute",
            "command": command,
            "exit_code": exit_code,
            "envelope": envelope,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "duration_ms": duration_ms,
        }
        _append_exec_log(exec_log_path, record)

    # [7] 写入 step-refs（成功 step，供后续步骤 ${STEP-N.id} 引用）
    if step_refs_dir and step_id and envelope.get("status") == "success":
        _write_step_ref(step_refs_dir, step_id, op_id, args, envelope)

    return envelope


# ===== op 声明读取 + id 解析（4 模式）=====
#
# 真相源：atoms/fw/*.yaml 的 rollback_strategy.id_source（经 `ptm-atomic show` 暴露）。
# 四种 id_source 模式：
#   response    -> 从前向 op 返回 envelope.data[id_field] 取（如 policy_route_id）
#   args        -> 从前向 op args[id_field] 取（id 即 name，如 object_name）
#   query       -> 执行 query_op，在 data.full_config 记录列表按 query_match 匹配，取 id_field
#   placeholder -> id 为固定占位（如 "1"），真正定位靠 id_field（如 old_name）


_OP_DECL_CACHE: Dict[str, Optional[dict]] = {}


def _load_op_decl(op_id: str) -> Optional[dict]:
    """经 `ptm-atomic show <op_id> --format json` 读 op 声明（含 rollback_strategy.id_source）。

    单源真相：ptm-atomic atoms/fw/*.yaml -> show CLI。进程内 LRU 缓存（声明静态）。
    失败（op 不存在 / CLI 异常）返回 None，不抛异常（调用方按"无声明"回退旧逻辑）。
    """
    if op_id in _OP_DECL_CACHE:
        return _OP_DECL_CACHE[op_id]
    try:
        proc = subprocess.run(
            ["ptm-atomic", "show", op_id, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.SubprocessError, OSError):
        _OP_DECL_CACHE[op_id] = None
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        _OP_DECL_CACHE[op_id] = None
        return None
    try:
        decl = json.loads(proc.stdout)
    except json.JSONDecodeError:
        _OP_DECL_CACHE[op_id] = None
        return None
    _OP_DECL_CACHE[op_id] = decl
    return decl


def _resolve_query_id(
    query_op: str,
    query_match: str,
    match_val: Any,
    id_field: str,
    *,
    base_url: str,
    session_file: str,
    authorized: bool,
    timeout: int,
) -> Optional[Any]:
    """mode C：执行 query_op，在 data.full_config 记录列表按 query_match 匹配，取 id_field。

    full_config 可能是 list 或 JSON 字符串，防御性解析。
    查询过滤参数按约定传 query_match 字段名（如 name）；verify op 的 policy_name 过滤参数
    与记录内 name 字段的精确映射待 op 覆盖扩展时确认（mode C 端到端待 acl_policy 族映射）。
    """
    qargs = {"page": 1, "size": 100, query_match: match_val}
    qenv = execute_op(
        query_op,
        qargs,
        base_url,
        session_file,
        dry_run=True,
        authorized=authorized,
        timeout=timeout,
    )
    data = qenv.get("data") if isinstance(qenv, dict) else None
    if not isinstance(data, dict):
        return None
    records = data.get("full_config")
    if isinstance(records, str):
        try:
            records = json.loads(records)
        except json.JSONDecodeError:
            return None
    if not isinstance(records, list):
        return None
    for item in records:
        if isinstance(item, dict) and item.get(query_match) == match_val:
            val = item.get(id_field)
            if val not in (None, "", 0):
                return val
    return None


def resolve_id(
    forward_op_id: str,
    forward_envelope: Optional[dict],
    forward_args: dict,
    *,
    base_url: str = "",
    session_file: str = "",
    authorized: bool = False,
    timeout: int = 30,
) -> Optional[Any]:
    """按前向 op 声明的 rollback_strategy.id_source 解析 id（4 模式分发）。

    无声明（旧 atom 无 id_source）或解析失败 -> 返回 None（调用方回退旧逻辑）。
    供 handle_rollback（回滚）和 resolve_step_refs（步骤间 ${STEP-N.id}）共用。
    """
    decl = _load_op_decl(forward_op_id)
    if not decl or not isinstance(decl, dict):
        return None
    rs = decl.get("rollback_strategy")
    if not isinstance(rs, dict):
        return None
    id_source = rs.get("id_source")
    id_field = rs.get("id_field")
    if not id_source or not id_field:
        return None

    if id_source == "response":
        data = forward_envelope.get("data") if isinstance(forward_envelope, dict) else None
        if not isinstance(data, dict):
            return None
        val = data.get(id_field)
        return None if val in (None, "", 0) else val

    if id_source == "args":
        val = forward_args.get(id_field)
        return None if val in (None, "", 0) else val

    if id_source == "query":
        query_op = rs.get("query_op")
        query_match = rs.get("query_match")
        query_match_source = rs.get("query_match_source", "args")
        if not query_op or not query_match:
            return None
        # query_match_source=args：匹配值取自前向 op 的 args
        if query_match_source != "args":
            return None
        match_val = forward_args.get(query_match)
        if match_val in (None, "", 0):
            return None
        if not base_url or not session_file:
            return None
        return _resolve_query_id(
            query_op, query_match, match_val, id_field,
            base_url=base_url, session_file=session_file,
            authorized=authorized, timeout=timeout,
        )

    if id_source == "placeholder":
        # id 为固定占位（如 "1"），取自前向 op inputs.params.id；真正定位靠 id_field
        inputs = decl.get("inputs") if isinstance(decl, dict) else None
        params = inputs.get("params") if isinstance(inputs, dict) else None
        if not isinstance(params, dict):
            return None
        val = params.get("id")
        return None if val in (None, "") else val

    return None


def build_inverse_args(
    forward_op_id: str,
    forward_envelope: Optional[dict],
    forward_args: dict,
    decl: Optional[dict],
    *,
    base_url: str = "",
    session_file: str = "",
    authorized: bool = False,
    timeout: int = 30,
) -> dict:
    """按 id_source 模式构造 inverse_op 的 args（回滚清理用）。

    - response/args/query：{id: <解析值>}，顺带携带 type/policy_type
    - placeholder（mode D，rename-back）：id 取占位，互换 old_name <-> new_name
    无声明时返回空 dict（调用方回退旧 _extract_inverse_id 路径自行构造）。
    """
    if not decl or not isinstance(decl, dict):
        return {}
    rs = decl.get("rollback_strategy")
    if not isinstance(rs, dict) or not rs.get("id_source"):
        return {}
    id_source = rs["id_source"]
    inverse_args: dict = {}

    if id_source == "placeholder":
        # mode D：rename back。rollback 的 old_name = 前向 new_name，new_name = 前向 old_name
        rid = resolve_id(forward_op_id, forward_envelope, forward_args,
                         base_url=base_url, session_file=session_file,
                         authorized=authorized, timeout=timeout)
        if rid is not None:
            inverse_args["id"] = rid
        if "policy_type" in forward_args:
            inverse_args["policy_type"] = forward_args["policy_type"]
        inverse_args["old_name"] = forward_args.get("new_name")
        inverse_args["new_name"] = forward_args.get("old_name")
        return inverse_args

    rid = resolve_id(forward_op_id, forward_envelope, forward_args,
                     base_url=base_url, session_file=session_file,
                     authorized=authorized, timeout=timeout)
    if rid is not None:
        inverse_args["id"] = rid
    # 携带 type（policy_route ipv4/ipv6）与 policy_type（acl_policy 族）
    if "type" in forward_args:
        inverse_args["type"] = forward_args["type"]
    if "policy_type" in forward_args:
        inverse_args["policy_type"] = forward_args["policy_type"]
    return inverse_args


# ===== 回滚清理 =====


def _extract_inverse_id(result_envelope: Optional[dict], op_id: str) -> Optional[Any]:
    """【回退路径】从原操作返回 envelope.data 提取 inverse_op 所需 id。

    仅供无 rollback_strategy.id_source 声明的 op（如 interface 族）回退使用；
    有声明的 op 走 resolve_id（4 模式声明驱动）。

    真相源：atoms/fw/fw_config_policy_route.yaml returns.data.policy_route_id。
    - fw_config_policy_route -> data.policy_route_id（config execute 返回创建的策略路由 id）
    - fw_config_interface -> returns.data 无 id 字段（已知限制，兜底 args["id"]）
    查找顺序 policy_route_id -> interface_id -> id，跳过 None/""/0 占位。
    """
    if not result_envelope:
        return None
    if not isinstance(result_envelope, dict):
        return None
    data = result_envelope.get("data")
    if not isinstance(data, dict):
        return None
    for key in ("policy_route_id", "interface_id", "id"):
        val = data.get(key)
        if val not in (None, "", 0):
            return val
    return None


def handle_rollback(
    op_id: str,
    args: dict,
    base_url: str,
    session_file: str,
    *,
    pre_snapshot: Optional[dict] = None,
    authorized: bool = False,
    timeout: int = 30,
    result_envelope: Optional[dict] = None,
) -> dict:
    """按 op 的 rollback 策略执行回滚清理。

    策略路由（ROLLBACK_STRATEGY）：
    - inverse_op: 执行 inverse_op 清理（如 config -> delete）
    - restore_snapshot: 按 pre_snapshot 恢复（如 update -> 恢复原值）
    - irreversible: 不回滚，返回豁免说明 envelope
    - none: 不回滚，返回无需回滚 envelope

    Args:
        op_id: 原子操作 ID
        args: 原操作参数（inverse_op 兜底 id 来源；type 来源）
        base_url: 设备 Web 管理地址
        session_file: session-<run-id>.json 路径
        pre_snapshot: 操作前快照（restore_snapshot 类必需）
        authorized: --execute 授权标记
        timeout: 超时秒数
        result_envelope: 原操作返回 envelope（inverse_op 优先从中提取 data.policy_route_id 作 id）

    Returns:
        回滚结果 envelope dict
    """
    if op_id not in ROLLBACK_STRATEGY:
        return _build_envelope(
            op_id,
            "rollback",
            "error",
            {"reason": f"op_id {op_id} 无回滚策略"},
            "OP_NOT_FOUND",
            "",
        )

    strategy = ROLLBACK_STRATEGY[op_id]
    rtype = strategy["type"]

    if rtype == "inverse_op":
        # config -> delete 清理
        inverse_op_id = strategy["inverse_op_id"]
        inverse_args: dict = {}
        # 声明优先：若 op 经 `ptm-atomic show` 有 rollback_strategy.id_source 声明，
        # 按 4 模式（response/args/query/placeholder）构造 inverse_args；
        # 无声明（旧 atom，如 interface）-> 回退旧 _extract_inverse_id + args["id"] 逻辑。
        decl = _load_op_decl(op_id)
        inv_args = build_inverse_args(
            op_id, result_envelope, args, decl,
            base_url=base_url, session_file=session_file,
            authorized=authorized, timeout=timeout,
        )
        if inv_args:
            inverse_args = inv_args
        else:
            # 兜底：从原操作返回 envelope.data 提取 id（policy_route_id/interface_id/id），
            # 再兜底调用方 args["id"]（interface 族）。真相源 atoms/fw/*.yaml returns。
            rid = _extract_inverse_id(result_envelope, op_id)
            if rid is not None:
                inverse_args["id"] = rid
            elif "id" in args:
                inverse_args["id"] = args["id"]
            if "type" in args:
                inverse_args["type"] = args["type"]
        return execute_op(
            inverse_op_id,
            inverse_args,
            base_url,
            session_file,
            step_name=f"rollback-{op_id}",
            dry_run=False,
            authorized=authorized,
            timeout=timeout,
        )

    elif rtype == "restore_snapshot":
        # update / delete -> 按快照恢复
        if strategy.get("as_cleanup_skip"):
            # delete 作为 config 清理动作时不触发回滚
            return _build_envelope(
                op_id,
                "rollback",
                "success",
                {"rollback": "skipped", "reason": "作为清理动作不触发回滚"},
                "NONE",
                "",
            )
        if pre_snapshot is None:
            return _build_envelope(
                op_id,
                "rollback",
                "error",
                {"reason": "restore_snapshot 需要 pre_snapshot"},
                "EXEC_FAILED",
                "",
            )
        restore_op_id = strategy["restore_op_id"]
        snapshot_source = strategy.get("snapshot_source", "full_config")
        restore_args = pre_snapshot.get(snapshot_source, pre_snapshot)
        return execute_op(
            restore_op_id,
            restore_args,
            base_url,
            session_file,
            step_name=f"rollback-{op_id}",
            dry_run=False,
            authorized=authorized,
            timeout=timeout,
        )

    elif rtype == "irreversible":
        # reset-hitcount：不回滚
        return _build_envelope(
            op_id,
            "rollback",
            "success",
            {"rollback": "waived", "reason": strategy["reason"]},
            "NONE",
            "",
        )

    else:
        # none：只读或无元数据，不回滚
        return _build_envelope(
            op_id,
            "rollback",
            "success",
            {"rollback": "not_required", "reason": strategy.get("reason", "")},
            "NONE",
            "",
        )


# ===== 映射表一致性校验 =====


def validate_mapping_consistency() -> ValidationResult:
    """校验映射表与三处真相源的一致性（CP7 static 校验入口）。

    三处真相源：
    1. run_policy_route.py build_subtree() - 7 个 policy-route 子命令名
    2. op yaml inputs.params - 参数名（source_network/dst_network/next_hop_ip/in_interface/type/id）
    3. ptm-atomic run ... --help - CLI flag 名（--source-network 等）

    校验维度：
    - 15 个 op_id 在 OP_ID_TO_SUBCOMMAND / ARGS_TO_FLAGS / ROLLBACK_STRATEGY 三表全覆盖
    - op_id 数量 == 15（5 族：auth/policy-route/operation-log/object/interface）
    - flag 名格式正确（-- 前缀）
    - ROLLBACK_STRATEGY.type 与 OP_METADATA.rollback 交叉一致
    - policy-route 族子命令名与 run_policy_route.py build_subtree() 一致（嵌入式校验）
    - required flag 与 ARGS_TO_FLAGS 映射不矛盾

    Returns:
        ValidationResult: passed=True/False, mismatches=list[str]
    """
    mismatches: List[str] = []

    # [1] 三表 op_id 一致性
    ops_in_sub = set(OP_ID_TO_SUBCOMMAND.keys())
    ops_in_args = set(ARGS_TO_FLAGS.keys())
    ops_in_rollback = set(ROLLBACK_STRATEGY.keys())
    ops_in_meta = set(OP_METADATA.keys())

    if ops_in_sub != ops_in_args:
        mismatches.append(
            f"OP_ID_TO_SUBCOMMAND 与 ARGS_TO_FLAGS 的 op_id 集合不一致: "
            f"差集={ops_in_sub.symmetric_difference(ops_in_args)}"
        )
    if ops_in_sub != ops_in_rollback:
        mismatches.append(
            f"OP_ID_TO_SUBCOMMAND 与 ROLLBACK_STRATEGY 的 op_id 集合不一致: "
            f"差集={ops_in_sub.symmetric_difference(ops_in_rollback)}"
        )
    if ops_in_sub != ops_in_meta:
        mismatches.append(
            f"OP_ID_TO_SUBCOMMAND 与 OP_METADATA 的 op_id 集合不一致: "
            f"差集={ops_in_sub.symmetric_difference(ops_in_meta)}"
        )

    # [2] op_id 数量校验
    if len(ops_in_sub) != EXPECTED_OP_COUNT:
        mismatches.append(
            f"OP_ID_TO_SUBCOMMAND 应覆盖 {EXPECTED_OP_COUNT} 个 op_id，实际 {len(ops_in_sub)} 个"
        )

    # [3] flag 格式校验（所有 flag 必须以 -- 开头）
    for op_id, flag_map in ARGS_TO_FLAGS.items():
        for args_key, cli_flag in flag_map.items():
            if not cli_flag.startswith("--"):
                mismatches.append(
                    f"{op_id}.{args_key} 的 flag '{cli_flag}' 缺少 -- 前缀"
                )

    # [4] ROLLBACK_STRATEGY 与 OP_METADATA 交叉一致性校验
    for op_id, meta in OP_METADATA.items():
        strategy = ROLLBACK_STRATEGY.get(op_id, {})
        meta_rollback = meta.get("rollback", "")
        strategy_type = strategy.get("type", "")

        # inverse_op:fw_xxx -> type=inverse_op
        if meta_rollback.startswith("inverse_op:") and strategy_type != "inverse_op":
            mismatches.append(
                f"{op_id}: OP_METADATA.rollback='{meta_rollback}' "
                f"但 ROLLBACK_STRATEGY.type='{strategy_type}'"
            )
        # restore_snapshot -> type=restore_snapshot
        elif meta_rollback == "restore_snapshot" and strategy_type != "restore_snapshot":
            mismatches.append(
                f"{op_id}: OP_METADATA.rollback='restore_snapshot' "
                f"但 ROLLBACK_STRATEGY.type='{strategy_type}'"
            )
        # irreversible -> type=irreversible
        elif meta_rollback == "irreversible" and strategy_type != "irreversible":
            mismatches.append(
                f"{op_id}: OP_METADATA.rollback='irreversible' "
                f"但 ROLLBACK_STRATEGY.type='{strategy_type}'"
            )
        # 空 rollback -> type=none
        elif meta_rollback == "" and strategy_type not in ("none",):
            mismatches.append(
                f"{op_id}: OP_METADATA.rollback 为空 "
                f"但 ROLLBACK_STRATEGY.type='{strategy_type}'"
            )

    # [5] policy-route 族子命令名与 run_policy_route.py build_subtree() 一致性校验
    # build_subtree() 返回 7 个 CommandSpec: config/update/delete/verify/reset-hitcount/verify-hitcount/priority
    expected_policy_route_actions = {
        "config", "update", "delete", "verify",
        "reset-hitcount", "verify-hitcount", "priority",
    }
    actual_policy_route_actions = {
        action for (family, action) in OP_ID_TO_SUBCOMMAND.values()
        if family == "policy-route"
    }
    if actual_policy_route_actions != expected_policy_route_actions:
        missing = expected_policy_route_actions - actual_policy_route_actions
        extra = actual_policy_route_actions - expected_policy_route_actions
        if missing:
            mismatches.append(f"policy-route 子命令缺失: {missing}")
        if extra:
            mismatches.append(f"policy-route 子命令多余: {extra}")

    # [6] auth 族子命令校验
    auth_ops = {
        op_id: (f, a) for op_id, (f, a) in OP_ID_TO_SUBCOMMAND.items() if f == "auth"
    }
    if "fw_login_web_management" not in auth_ops:
        mismatches.append("缺少 fw_login_web_management -> auth login 映射")
    elif auth_ops["fw_login_web_management"] != ("auth", "login"):
        mismatches.append(
            f"fw_login_web_management 映射错误: 期望 ('auth', 'login')，"
            f"实际 {auth_ops['fw_login_web_management']}"
        )

    # [5b] operation-log 族子命令校验（CR-028）
    expected_operation_log_actions = {"capture"}
    actual_operation_log_actions = {
        action for (family, action) in OP_ID_TO_SUBCOMMAND.values()
        if family == "operation-log"
    }
    if actual_operation_log_actions != expected_operation_log_actions:
        mismatches.append(f"operation-log 子命令不一致: {actual_operation_log_actions} != {expected_operation_log_actions}")

    # [5c] object 族子命令校验（安装版 0.1.0 仅 config；update/delete/delete-batch/verify 源码有但未暴露，记 gap）
    expected_object_actions = {"config"}
    actual_object_actions = {
        action for (family, action) in OP_ID_TO_SUBCOMMAND.values()
        if family == "object"
    }
    if actual_object_actions != expected_object_actions:
        mismatches.append(f"object 子命令不一致: {actual_object_actions} != {expected_object_actions}")

    # [5d] interface 族子命令校验（CR-028，5 个子命令）
    expected_interface_actions = {"create", "update", "delete", "delete-batch", "verify"}
    actual_interface_actions = {
        action for (family, action) in OP_ID_TO_SUBCOMMAND.values()
        if family == "interface"
    }
    if actual_interface_actions != expected_interface_actions:
        missing = expected_interface_actions - actual_interface_actions
        extra = actual_interface_actions - expected_interface_actions
        if missing:
            mismatches.append(f"interface 子命令缺失: {missing}")
        if extra:
            mismatches.append(f"interface 子命令多余: {extra}")

    # [7] required flag 与 ARGS_TO_FLAGS 一致性校验
    # required flag 必须在对应 op 的 ARGS_TO_FLAGS 值集合中
    for op_id, req_flags in REQUIRED_FLAGS.items():
        if op_id not in ARGS_TO_FLAGS:
            mismatches.append(f"REQUIRED_FLAGS 中的 {op_id} 不在 ARGS_TO_FLAGS 中")
            continue
        available_flags = set(ARGS_TO_FLAGS[op_id].values())
        for req in req_flags:
            if req not in available_flags:
                mismatches.append(
                    f"{op_id}: required flag '{req}' 不在 ARGS_TO_FLAGS 值集合中"
                )

    passed = len(mismatches) == 0
    return ValidationResult(passed=passed, mismatches=mismatches)


# ===== CLI 入口 =====


def _cli_main(argv: Optional[List[str]] = None) -> int:
    """op_mapper.py CLI 入口（便于测试和手动验证）。

    用法：
        python op_mapper.py validate
        python op_mapper.py map --op-id fw_config_policy_route --args '{"source_network":"<IP_ADDRESS>/24"}'
        python op_mapper.py execute --op-id fw_config_policy_route --base-url https://<IP_ADDRESS> \\
            --session-file /path/session-<run-id>.json --args '{"source_network":"<IP_ADDRESS>/24"}' --dry-run
    """
    parser = argparse.ArgumentParser(
        description="策略路由双层映射 + 执行 + 回滚（op_mapper）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # validate 子命令
    sub.add_parser("validate", help="映射表一致性校验")

    # map 子命令
    map_parser = sub.add_parser("map", help="打印映射结果（不执行）")
    map_parser.add_argument("--op-id", required=True, help="原子操作 ID")
    map_parser.add_argument(
        "--args", default="{}", help='参数 JSON，如 \'{"source_network":"<IP_ADDRESS>/24"}\''
    )
    map_parser.add_argument("--base-url", default="https://localhost")
    map_parser.add_argument(
        "--session-file", default="~/.local/state/ptm-atomic/ngfw/session-<run-id>.json"
    )
    map_parser.add_argument("--dry-run", action="store_true", default=True)
    map_parser.add_argument("--execute", dest="dry_run", action="store_false")

    # execute 子命令
    exec_parser = sub.add_parser("execute", help="执行单条原子操作")
    exec_parser.add_argument("--op-id", required=True, help="原子操作 ID")
    exec_parser.add_argument(
        "--args", default="{}", help='参数 JSON，如 \'{"source_network":"<IP_ADDRESS>/24"}\''
    )
    exec_parser.add_argument("--base-url", required=True, help="设备 Web 管理地址")
    exec_parser.add_argument("--session-file", required=True, help="session-<run-id>.json 路径")
    exec_parser.add_argument("--dry-run", action="store_true", default=True)
    exec_parser.add_argument("--execute", dest="dry_run", action="store_false")
    exec_parser.add_argument("--authorized", action="store_true", default=False)
    exec_parser.add_argument("--timeout", type=int, default=30)
    exec_parser.add_argument("--step-name", default="")
    exec_parser.add_argument("--step-id", default="", help="步骤 ID（如 STEP-001），用于 step-refs 落盘")
    exec_parser.add_argument(
        "--step-refs-dir", default=None,
        help="step-refs 目录（runs/<run-id>/step-refs/），启用 ${STEP-N.id} 插值与落盘",
    )
    exec_parser.add_argument("--exec-log-path", default=None)
    exec_parser.add_argument("--diag-snapshot-ref", default="")

    args_ns = parser.parse_args(argv)

    if args_ns.command == "validate":
        result = validate_mapping_consistency()
        print(result)
        return 0 if result.passed else 1

    elif args_ns.command == "map":
        try:
            args_dict = json.loads(args_ns.args)
        except json.JSONDecodeError as e:
            print(f"参数 JSON 解析失败: {e}", file=sys.stderr)
            return 2
        try:
            family, action = map_op_id_to_subcommand(args_ns.op_id)
            flags = map_args_to_flags(args_ns.op_id, args_dict)
            cmd = build_command(
                args_ns.op_id,
                args_dict,
                args_ns.base_url,
                args_ns.session_file,
                dry_run=args_ns.dry_run,
            )
            output = {
                "op_id": args_ns.op_id,
                "family": family,
                "action": action,
                "flags": flags,
                "command": cmd,
                "dry_run": args_ns.dry_run,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0
        except (OpNotFoundError, ValueError, ValidationError) as e:
            print(f"映射失败: {e}", file=sys.stderr)
            return 1

    elif args_ns.command == "execute":
        try:
            args_dict = json.loads(args_ns.args)
        except json.JSONDecodeError as e:
            print(f"参数 JSON 解析失败: {e}", file=sys.stderr)
            return 2
        envelope = execute_op(
            args_ns.op_id,
            args_dict,
            args_ns.base_url,
            args_ns.session_file,
            step_name=args_ns.step_name,
            dry_run=args_ns.dry_run,
            authorized=args_ns.authorized,
            timeout=args_ns.timeout,
            exec_log_path=args_ns.exec_log_path,
            diag_snapshot_ref=args_ns.diag_snapshot_ref,
            step_id=args_ns.step_id,
            step_refs_dir=args_ns.step_refs_dir,
        )
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
        return 0 if envelope.get("status") == "success" else 1

    return 0


if __name__ == "__main__":
    sys.exit(_cli_main())
