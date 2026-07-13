#!/usr/bin/env python3
"""采集防火墙设备系统信息快照（before/after 对比用）

声明: requires-python >=3.9,<3.13
依赖: paramiko, telnetlib(标准库), yaml(PyYAML)

采集维度: CPU (top)、内存 (free)、磁盘 (df)、进程 (ps -ef | grep opt)
连接模型: SSH（paramiko 首选）失败回退 Telnet（telnetlib）
快照存储: runs/<run-id>/snapshot-{phase}/<device>.json

用法:
    # 采集指定设备快照
    uv run python scripts/collect_sysinfo.py <设备名> --phase before --run-id <run-id>
    # 采集所有设备快照
    uv run python scripts/collect_sysinfo.py --all --phase after --run-id <run-id>
    # 直接指定 IP 采集（--password-env 传环境变量名，不是明文密码）
    uv run python scripts/collect_sysinfo.py --host <IP_ADDRESS> --password-env FW_SSH_PASSWORD --phase before --run-id <run-id>
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import paramiko
import telnetlib
import yaml

# 采集命令定义（4 维度，全部只读，不修改设备状态）
COLLECT_COMMANDS = {
    "cpu": "top -bn1 | head -5",
    "memory": "free -m",
    "disk": "df -h",
    "processes": "ps -ef | grep opt",
}

# ${ENV_VAR} 占位符正则（仅匹配全大写下划线变量名）
ENV_VAR_PATTERN = re.compile(r"^\$\{([A-Z_][A-Z0-9_]*)\}$")


def resolve_env_var(value: str) -> str:
    """解析 ${ENV_VAR} 占位符为环境变量实际值。

    参数:
        value: 原始值，可能为 "${FW_SSH_PASSWORD}" 或明文

    返回:
        环境变量值（占位符情况）或原值（非占位符情况）
        环境变量未设置时返回空字符串

    异常:
        无。环境变量未设置时返回空字符串，由调用方判定 ENV_NOT_READY
    """
    match = ENV_VAR_PATTERN.match(value)
    if match:
        env_var = match.group(1)
        return os.environ.get(env_var, "")
    return value


def check_env_var_set(value: str) -> bool:
    """检查 ${ENV_VAR} 占位符对应的环境变量是否已设置。

    参数:
        value: 原始值

    返回:
        True 如果值非占位符，或占位符对应环境变量已设置且非空
        False 如果占位符对应环境变量未设置或为空
    """
    match = ENV_VAR_PATTERN.match(value)
    if match:
        env_var = match.group(1)
        return bool(os.environ.get(env_var, ""))
    # 非占位符视为已就绪（兼容历史明文，但 SKILL 规则要求占位）
    return True


def load_devices(yaml_path: Path) -> dict[str, dict]:
    """从 devices.yaml 加载设备配置，解析 ${ENV_VAR} 占位凭据。

    参数:
        yaml_path: devices.yaml 文件路径

    返回:
        devices dict: {设备组名: {ssh_host, ssh_port, ssh_enabled, telnet_host,
        telnet_port, user, password, password_raw, env_ready}}

    异常:
        FileNotFoundError: yaml_path 不存在
        yaml.YAMLError: YAML 语法错误

    说明:
        - password 字段自动解析 ${ENV_VAR} 占位符
        - 不修改原始 devices.yaml 文件
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"设备配置文件不存在: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    devices = {}
    for group in data.get("device_groups", []):
        name = group.get("name", "")
        fw = group.get("firewall")
        if not fw:
            continue

        telnet = fw.get("telnet", {})
        ssh = fw.get("ssh", {})
        # SSH 密码优先，其次 firewall 级别密码
        password_raw = ssh.get("password", fw.get("password", ""))
        password = resolve_env_var(password_raw)

        devices[name] = {
            "ssh_host": ssh.get("host", fw.get("host", "")),
            "ssh_port": ssh.get("port", 22),
            "ssh_enabled": ssh.get("enabled", False),
            "telnet_host": telnet.get("host", ""),
            "telnet_port": telnet.get("port", 23),
            "user": ssh.get("user", fw.get("user", "root")),
            "password": password,
            "password_raw": password_raw,
            "env_ready": check_env_var_set(password_raw),
        }

    return devices


def check_reachable(host: str, port: int = 443, timeout: int = 5) -> bool:
    """检查设备 IP 可达性（TCP 端口探测）。

    参数:
        host: 目标 IP
        port: 探测端口，默认 443（Web 管理端口，部分设备禁 ICMP 用 TCP 更可靠）
        timeout: 超时秒数，默认 5

    返回:
        True 如果 TCP 连接成功
        False 如果连接失败或超时
    """
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def ssh_exec(
    host: str,
    port: int,
    user: str,
    password: str,
    command: str,
    timeout: int = 15,
) -> tuple[str, str]:
    """SSH 执行单条命令（优先 import ssh_exec.py，fallback 内联实现）。

    参数与返回值同 ssh_exec.py 的 ssh_exec 函数。
    本函数签名与 ssh_exec.py 保持一致，collect_sysinfo.py 优先 import；
    若 import 失败则使用内联实现保证脚本独立可执行。

    返回:
        (stdout: str, stderr: str)，均已 strip() 处理

    异常:
        paramiko 异常 / socket 异常（由 collect_from_device 捕获触发 Telnet 回退）
    """
    # 优先复用 ssh_exec.py 的实现（同目录模块）
    try:
        from ssh_exec import ssh_exec as _ssh_exec
        return _ssh_exec(host, port, user, password, command, timeout)
    except ImportError:
        pass

    # fallback 内联实现
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=timeout)
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
    finally:
        ssh.close()
    return out.strip(), err.strip()


def telnet_exec(
    host: str,
    port: int,
    user: str,
    password: str,
    command: str,
    wait: int = 3,
) -> tuple[str, str]:
    """通过 Telnet 执行单条命令，返回 (stdout, "")。

    参数:
        host: Telnet 主机 IP
        port: Telnet 端口
        user: 登录用户名
        password: 登录密码（运行时已解析）
        command: 要执行的命令
        wait: 命令执行后等待秒数，默认 3

    返回:
        (output: str, "")：Telnet 无 stderr 概念，固定返回空字符串

    异常:
        EOFError: 连接意外关闭
        socket.timeout: 超时
        Exception: 其他 Telnet 异常

    说明:
        流程: 连接 -> login 提示 -> 用户名 -> Password 提示 -> 密码
              -> 清空缓冲 -> 发送命令 -> 等待 -> 读取输出 -> 关闭
        清理: 去掉首行命令回显 + 末尾 shell 提示符
    """
    tn = telnetlib.Telnet(host, port, timeout=10)
    tn.read_until(b"login:", timeout=10)
    tn.write(user.encode() + b"\r\n")
    time.sleep(1)
    tn.read_until(b"Password:", timeout=5)
    tn.write(password.encode() + b"\r\n")
    time.sleep(2)
    # 清空登录后的欢迎信息缓冲
    tn.read_very_eager()
    tn.write(command.encode() + b"\r\n")
    time.sleep(wait)
    output = tn.read_very_eager().decode(errors="replace")
    tn.close()
    # 清理命令回显和末尾 shell 提示符
    lines = output.strip().splitlines()
    if lines and command in lines[0]:
        lines = lines[1:]
    while lines and re.match(r"^[#\[$]", lines[-1].strip()):
        lines.pop()
    return "\n".join(lines).strip(), ""


def collect_from_device(
    name: str,
    config: dict,
) -> tuple[dict, str]:
    """采集设备系统信息，SSH 首选 -> Telnet 回退。

    参数:
        name: 设备组名
        config: 设备配置 dict（含 ssh_host/ssh_port/telnet_host/telnet_port/user/password）

    返回:
        (results: dict, connection_method: str)
        results: {cpu: str, memory: str, disk: str, processes: str}
        connection_method: "ssh" | "telnet" | "none"

    说明:
        - 逐命令级别回退：SSH 在第一条命令失败后，后续命令直接使用 Telnet
        - SSH/Telnet 双失败时结果为 "ERROR: <exception>"
        - connection_method 记录实际使用的连接方式
    """
    results = {}
    use_ssh = True
    connection_method = "none"

    for key, cmd in COLLECT_COMMANDS.items():
        try:
            if use_ssh:
                out, err = ssh_exec(
                    config["ssh_host"], config["ssh_port"],
                    config["user"], config["password"], cmd
                )
                connection_method = "ssh"
                results[key] = out if out else err
            else:
                out, err = telnet_exec(
                    config["telnet_host"], config["telnet_port"],
                    config["user"], config["password"], cmd
                )
                connection_method = "telnet"
                results[key] = out if out else err
        except Exception as e:
            if use_ssh:
                # SSH 失败，回退到 Telnet（逐命令级别）
                print(f"  SSH 失败 ({e})，回退到 Telnet...")
                use_ssh = False
                try:
                    out, err = telnet_exec(
                        config["telnet_host"], config["telnet_port"],
                        config["user"], config["password"], cmd
                    )
                    connection_method = "telnet"
                    results[key] = out if out else err
                except Exception as e2:
                    print(f"  Telnet 也失败: {e2}")
                    connection_method = "none"
                    results[key] = f"ERROR: {e2}"
            else:
                print(f"  Telnet 失败: {e}")
                connection_method = "none"
                results[key] = f"ERROR: {e}"

    return results, connection_method


def save_snapshot(
    device: str,
    phase: str,
    data: dict,
    connection_method: str,
    run_id: str,
    workspace: Path,
) -> Path:
    """保存快照到 runs/<run-id>/snapshot-{phase}/<device>.json。

    参数:
        device: 设备组名
        phase: "before" 或 "after"
        data: 采集结果 dict（cpu/memory/disk/processes）
        connection_method: "ssh" | "telnet" | "none"
        run_id: 运行 ID（如 20260710-143000）
        workspace: 工作区根目录 Path

    返回:
        快照文件路径 Path

    说明:
        - 自动创建目录 runs/<run-id>/snapshot-{phase}/
        - JSON 格式: ensure_ascii=False, indent=2
        - 含元数据: device / phase / timestamp / connection_method
    """
    snapshot_dir = workspace / "runs" / run_id / f"snapshot-{phase}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    filepath = snapshot_dir / f"{device}.json"

    snapshot = {
        "device": device,
        "phase": phase,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "connection_method": connection_method,
        **data,
    }
    filepath.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath


def main() -> None:
    """CLI 入口函数。

    参数:
        device: 设备名（位置参数，可选，与 --all / --host 三选一）
        --phase: 采集阶段 before|after（必填）
        --all: 采集所有设备
        --host: 直接指定 IP
        --port: SSH 端口（默认 22）
        --user: 登录用户（默认 root）
        --password-env: 密码环境变量名（--host 模式必填）
        --telnet-host: Telnet 主机（回退用）
        --telnet-port: Telnet 端口（默认 23）
        --config: devices.yaml 路径（默认工作区根目录）
        --run-id: 运行 ID（必填，用于快照存储路径）
        --workspace: 工作区根目录（默认当前目录）

    退出码:
        0: 成功
        1: 错误（设备未找到、配置缺失、环境变量未设置等）
    """
    parser = argparse.ArgumentParser(description="采集防火墙系统信息快照")
    parser.add_argument("device", nargs="?", help="设备名（如 hg3250-51）")
    parser.add_argument("--phase", required=True, choices=["before", "after"], help="采集阶段")
    parser.add_argument("--all", action="store_true", help="采集所有设备")
    parser.add_argument("--host", help="直接指定设备 IP")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口（默认 22）")
    parser.add_argument("--user", default="root", help="登录用户（默认 root）")
    parser.add_argument("--password-env", help="密码环境变量名（--host 模式必填）")
    parser.add_argument("--telnet-host", help="Telnet 主机（回退用）")
    parser.add_argument("--telnet-port", type=int, default=23, help="Telnet 端口（默认 23）")
    parser.add_argument("--config", default="devices.yaml", help="设备配置文件路径")
    parser.add_argument("--run-id", required=True, help="运行 ID（快照存储路径用）")
    parser.add_argument("--workspace", default=".", help="工作区根目录（默认当前目录）")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    config_path = (
        Path(args.config) if Path(args.config).is_absolute()
        else workspace / args.config
    )

    # --host 直接指定 IP 模式（不依赖 devices.yaml）
    if args.host:
        if not args.password_env:
            parser.error("--host 模式需要 --password-env 参数")
        password = os.environ.get(args.password_env, "")
        if not password:
            print(f"错误: 环境变量 {args.password_env} 未设置", file=sys.stderr)
            sys.exit(1)
        config = {
            "ssh_host": args.host,
            "ssh_port": args.port,
            "ssh_enabled": True,
            "telnet_host": args.telnet_host or args.host,
            "telnet_port": args.telnet_port,
            "user": args.user,
            "password": password,
            "env_ready": True,
        }
        name = args.device or args.host
        targets = {name: config}
    else:
        # 从 devices.yaml 加载设备配置
        try:
            devices = load_devices(config_path)
        except FileNotFoundError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

        if args.all:
            if not devices:
                print("错误: 未找到设备配置，请检查 devices.yaml", file=sys.stderr)
                sys.exit(1)
            targets = devices
        elif args.device:
            # 不区分大小写匹配设备名
            device_key = None
            for key in devices:
                if key.upper() == args.device.upper():
                    device_key = key
                    break
            if device_key:
                targets = {device_key: devices[device_key]}
            else:
                print(f"错误: 未知设备 '{args.device}'", file=sys.stderr)
                print(f"可选设备: {', '.join(devices.keys())}", file=sys.stderr)
                sys.exit(1)
        else:
            parser.error("请指定设备名、使用 --all 或 --host")

    # 逐设备采集（串行，避免连接数膨胀）
    for name, config in targets.items():
        # 前置校验: 环境变量就绪
        if not config.get("env_ready", True):
            print(f"警告: 设备 {name} 环境变量未设置，跳过", file=sys.stderr)
            continue

        # 前置校验: IP 可达（TCP 443 探测）
        if not check_reachable(config["ssh_host"]):
            print(f"警告: 设备 {name} ({config['ssh_host']}) 不可达，跳过", file=sys.stderr)
            continue

        print(f"\n{'='*50}")
        print(f"采集设备: {name} ({args.phase})")
        print(f"连接地址: {config['ssh_host']}:{config['ssh_port']}")
        print(f"{'='*50}")

        data, conn_method = collect_from_device(name, config)
        filepath = save_snapshot(name, args.phase, data, conn_method, args.run_id, workspace)

        print(f"\n采集结果 (连接方式: {conn_method}):")
        for key, value in data.items():
            preview = value[:80].replace("\n", " | ") if value else "(空)"
            print(f"  {key}: {preview}...")
        print(f"\n快照已保存: {filepath}")


if __name__ == "__main__":
    main()
