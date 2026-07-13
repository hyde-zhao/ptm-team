---
name: device-connection
description: >-
  设备 SSH/Telnet 双轨连接与系统快照采集。提供 SSH（paramiko 首选）/ Telnet（telnetlib 回退）
  双轨连接能力，采集设备系统信息快照（CPU/内存/磁盘/进程 4 维度），用于用例执行 before/after 对比。
  触发词：采集快照、系统信息、连接设备、snapshot、sysinfo。本 SKILL 只做连接 + 快照，不管理设备清单。
argument-hint: "<设备名> --phase <before|after> --run-id <run-id>"
user-invokable: true
status: active
language: zh-CN
---

# 设备连接与快照采集

## 目的

提供 SSH（paramiko 首选）/ Telnet（telnetlib 回退）双轨连接能力，采集设备系统信息快照
（CPU/内存/磁盘/进程 4 维度），用于用例执行 before/after 对比。

**职责边界**：本 SKILL 只做连接 + 快照采集，**不管理设备清单**（清单由 `device-management` skill 维护），
**不执行策略路由 op**（由 `policy-route-execution` skill 承载）。

## 连接模型

- **SSH 首选**（paramiko）：常态命令、系统快照首选方式
- **Telnet 回退**（telnetlib）：SSH 不通设备的兜底
- **逐命令级别回退**：SSH 在第一条命令失败后，后续命令直接用 Telnet（不重复尝试 SSH）
- **SSH + Telnet 双失败** -> 标记设备不可达，结果记录为 `ERROR: <exception>`

| 方式 | 用途 | 机制 | 失败处理 |
|------|------|------|---------|
| SSH | 系统快照（首选） | paramiko | SSH 失败回退 Telnet |
| Telnet | SSH 不通的兜底 | telnetlib（声明 `>=3.9,<3.13`） | Telnet 失败标记设备不可达 |
| Web (HTTPS) | 策略路由配置 | 归属 ptm-atomic CLI（非本 SKILL 范围） | - |

## 前置校验

采集前必须通过以下校验（HLD §6.1）：

1. **devices.yaml 存在**：不存在则报错退出
2. **${ENV_VAR} 占位符对应环境变量已设置**：未设置则标记 ENV_NOT_READY，跳过该设备
3. **设备 IP 可达**：TCP 443 端口探测（部分设备禁 ICMP，TCP 探测更可靠）；不可达则跳过

## 脚本

### scripts/ssh_exec.py - SSH 远程命令执行

函数级封装，提供连接 / 执行 / 关闭完整生命周期，可独立执行或被 import。

```bash
# 独立执行单条命令（password-env 是环境变量名，不是明文密码）
uv run python scripts/ssh_exec.py <host> <user> <password-env> <command> [--port 22] [--timeout 15]
```

函数签名：
- `ssh_connect(host, port, user, password, timeout) -> paramiko.SSHClient`
- `ssh_exec(host, port, user, password, command, timeout) -> tuple[str, str]`（返回 stdout, stderr）
- `resolve_password_from_env(env_var) -> str`

### scripts/collect_sysinfo.py - 系统信息采集 + 快照存储

从 devices.yaml 加载设备配置，SSH/Telnet 双轨采集 4 维度系统信息，输出 JSON 快照。

```bash
# 采集指定设备快照
uv run python scripts/collect_sysinfo.py <设备名> --phase before --run-id <run-id>

# 采集所有设备快照
uv run python scripts/collect_sysinfo.py --all --phase after --run-id <run-id>

# 直接指定 IP 采集（需 --password-env 传环境变量名）
uv run python scripts/collect_sysinfo.py --host <IP_ADDRESS> --password-env FW_SSH_PASSWORD --phase before --run-id <run-id>
```

## 采集命令（4 维度，全部只读）

| 维度 | 命令 | 说明 |
|------|------|------|
| cpu | `top -bn1 \| head -5` | CPU 负载 |
| memory | `free -m` | 内存使用 |
| disk | `df -h` | 磁盘使用 |
| processes | `ps -ef \| grep opt` | 进程（防火墙 opt 目录进程） |

## Python 版本

`requires-python >=3.9,<3.13`（telnetlib 在 Python 3.13 移除，脚本头 docstring 声明）。

依赖：paramiko（SSH）、telnetlib（标准库）、yaml（PyYAML）。无额外第三方依赖。

## 快照输出

快照 JSON 存储路径：

```
runs/<run-id>/snapshot-before/<device>.json   # 用例执行前快照
runs/<run-id>/snapshot-after/<device>.json    # 用例执行后快照
```

快照 JSON 结构：

```json
{
  "device": "hg3250-51",
  "phase": "before",
  "timestamp": "2026-07-10T14:30:00",
  "connection_method": "ssh",
  "cpu": "top -bn1 | head -5 的输出文本",
  "memory": "free -m 的输出文本",
  "disk": "df -h 的输出文本",
  "processes": "ps -ef | grep opt 的输出文本"
}
```

`connection_method` 字段记录实际使用的连接方式（`ssh` / `telnet` / `none`），用于审计追溯。
采集失败时对应维度值为 `ERROR: <exception>`。

## 凭据安全（强制规则）

- 密码从环境变量读取，CLI 用 `--password-env <ENV_VAR>` 传入环境变量名（不是明文密码）
- **禁止命令行 `--password` 明文密码参数**
- devices.yaml 中凭据用 `${ENV_VAR}` 占位（由 device-management skill 维护）
- 运行时由 `resolve_env_var()` 从 `os.environ` 解析实际值

## 错误处理

| 场景 | 行为 |
|------|------|
| devices.yaml 不存在 | 报错退出（exit 1） |
| 环境变量未设置 | 警告 + 跳过该设备 |
| 设备 IP 不可达 | 警告 + 跳过该设备 |
| SSH 连接失败 | 自动回退 Telnet |
| Telnet 也失败 | 结果记录 `ERROR: <exception>`，不崩溃 |
| 未知设备名 | 报错 + 列出可选设备 |

## Gotchas

1. **telnetlib 是标准库但在 3.13 移除**：Python 3.13+ 运行会 ImportError，必须用 `>=3.9,<3.13`
2. **paramiko AutoAddPolicy 不验证 host key**：测试环境可接受，生产环境应改用 known_hosts
3. **SSH 逐命令回退不是逐设备回退**：第一条命令 SSH 失败后，后续命令直接用 Telnet
4. **--password-env 传的是变量名不是密码**：如 `FW_SSH_PASSWORD`，脚本内部 `os.environ.get()` 读取
5. **快照路径含 run-id**：`--run-id` 是必填参数，快照不存固定 `snapshots/` 目录
6. **check_reachable 用 TCP 443 不是 ping**：部分设备禁 ICMP，TCP 端口探测更可靠
7. **ssh.enabled=false 不阻止 SSH 尝试**：是信息标志，仍会尝试 SSH（预期失败后回退 Telnet）
8. **Telnet 输出需清理回显和提示符**：Telnet 回显输入命令，末尾有 shell 提示符，脚本自动清理
