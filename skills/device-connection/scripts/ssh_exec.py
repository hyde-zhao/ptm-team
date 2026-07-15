#!/usr/bin/env python3
"""SSH 远程命令执行工具

声明: requires-python >=3.9,<3.13
依赖: paramiko

提供函数级 SSH 封装：连接 / 执行 / 关闭完整生命周期。
可独立执行（CLI），也可被 collect_sysinfo.py import 复用。

用法:
    # 独立执行单条命令（password-env 是环境变量名，不是明文密码）
    uv run python scripts/ssh_exec.py <host> <user> <password-env> <command> [--port 22] [--timeout 15]

    # 被 import 使用
    from ssh_exec import ssh_exec
    out, err = ssh_exec(host, port, user, password, command)
"""

import argparse
import os
import sys

import paramiko


def ssh_connect(
    host: str,
    port: int = 22,
    user: str = "root",
    password: str = "",
    timeout: int = 15,
) -> paramiko.SSHClient:
    """建立 SSH 连接，返回 SSHClient 实例。

    参数:
        host: 目标主机 IP
        port: SSH 端口，默认 22
        user: 登录用户名，默认 root
        password: 登录密码（运行时从环境变量解析后的明文）
        timeout: 连接超时秒数，默认 15

    返回:
        paramiko.SSHClient 已连接实例

    异常:
        paramiko.AuthenticationException: 认证失败
        paramiko.SSHException: SSH 协议错误
        socket.timeout: 连接超时
        ConnectionRefusedError: 连接被拒绝
    """
    ssh = paramiko.SSHClient()
    # 测试环境自动接受 host key；生产环境应改用 known_hosts 策略
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=timeout)
    return ssh


def ssh_exec(
    host: str,
    port: int,
    user: str,
    password: str,
    command: str,
    timeout: int = 15,
) -> tuple[str, str]:
    """通过 SSH 执行单条命令，返回 (stdout, stderr)。

    参数:
        host: 目标主机 IP
        port: SSH 端口
        user: 登录用户名
        password: 登录密码（运行时已解析）
        command: 要执行的 shell 命令
        timeout: 执行超时秒数，默认 15

    返回:
        (stdout: str, stderr: str)，均已 strip() 处理

    异常:
        paramiko.AuthenticationException: 认证失败
        paramiko.SSHException: SSH 协议错误
        socket.timeout: 连接或执行超时
        Exception: 其他连接异常（由 collect_sysinfo.py 捕获触发 Telnet 回退）

    生命周期:
        建立连接 -> exec_command -> 读取 stdout/stderr -> close
        每次调用独立连接，不复用 session
    """
    ssh = ssh_connect(host, port, user, password, timeout)
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
    finally:
        # 确保 SSH 连接关闭，防止连接泄漏
        ssh.close()
    return out.strip(), err.strip()


def resolve_password_from_env(env_var: str) -> str:
    """从环境变量解析密码。

    参数:
        env_var: 环境变量名（不含 ${} 包裹），如 FW_SSH_PASSWORD

    返回:
        环境变量值；未设置时返回空字符串

    说明:
        命令行入口使用 --password-env <ENV_VAR> 传入环境变量名，
        本函数从 os.environ 读取实际值，避免命令行明文密码。
    """
    return os.environ.get(env_var, "")


if __name__ == "__main__":
    # CLI 入口: ssh_exec.py <host> <user> <password-env> <command> [--port 22] [--timeout 15]
    # password-env 是环境变量名（如 FW_SSH_PASSWORD），不是明文密码
    parser = argparse.ArgumentParser(description="SSH 远程命令执行")
    parser.add_argument("host", help="目标主机 IP")
    parser.add_argument("user", help="登录用户名")
    parser.add_argument("password_env", help="密码环境变量名（如 FW_SSH_PASSWORD）")
    parser.add_argument("command", help="要执行的命令")
    parser.add_argument("--port", type=int, default=22, help="SSH 端口（默认 22）")
    parser.add_argument("--timeout", type=int, default=15, help="超时秒数（默认 15）")
    args = parser.parse_args()

    password = resolve_password_from_env(args.password_env)
    if not password:
        print(f"错误: 环境变量 {args.password_env} 未设置", file=sys.stderr)
        sys.exit(1)

    out, err = ssh_exec(args.host, args.port, args.user, password, args.command, args.timeout)
    if out:
        print(out, end="")
    if err:
        print(err, end="", file=sys.stderr)
