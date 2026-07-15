---
name: device-management
description: >-
  设备清单管理与型号映射查表。用于向 devices.yaml 添加设备、查询硬件系列对应的
  TGFW 型号、按名称或 IP 查找设备。触发词：添加设备、查询型号、设备对照、查找设备、
  device_type、硬件系列。本 SKILL 只做元数据管理，不含任何连接逻辑（连接由 device-connection skill 承载）。
argument-hint: "<操作> [设备信息] 如：添加设备 hg3250-51 <IP_ADDRESS>、查询型号 HG3250"
user-invokable: true
status: active
language: zh-CN
---

# 设备管理（元数据）

## 目的

管理用户工作区 `devices.yaml` 中的设备清单，并在添加或查询设备时从型号对照表查找正确的
`device_type`。

**职责边界**：本 SKILL 只做元数据管理（设备清单结构 + 型号映射查表），**不含任何连接逻辑**。
SSH/Telnet 连接、系统快照采集由 `device-connection` skill 承载。策略路由 op 执行由
`policy-route-execution` skill 承载。

## 设备型号参考

完整的硬件系列到 TGFW 型号对照表见 [reference/device-reference.md](reference/device-reference.md)。
该表覆盖 manaul 现有全部型号（HG3250/NXP1046/160pro/160/290/TG-C236/TG-J1900 等），含 CPU 平台、
内存、硬盘等型号特征用于消歧。

## 添加设备流程

当用户要求添加设备时：

1. 从用户输入中提取：设备名、硬件系列、SSH IP、Telnet IP:端口、Web IP（可选）
2. 查阅 [reference/device-reference.md](reference/device-reference.md)，根据硬件系列确定 `device_type`
3. 如果该系列有多个 TGFW 型号，根据备注中的特征（内存、有无硬盘等）匹配；无法确定时询问用户
4. 按 [templates/devices.yaml.example](templates/devices.yaml.example) 模板写入新条目到 `devices.yaml`
5. **凭据必须使用 `${ENV_VAR}` 占位**，禁止明文凭据写入 devices.yaml（见凭据安全章节）
6. 验证 YAML 语法

### devices.yaml 写入模板

```yaml
  - name: <设备名>
    description: "<设备描述>"

    firewall:
      host: <管理IP>
      role: firewall
      device_type: <TGFW型号>
      web:
        host: <Web_IP>
        port: 443
        user: admin
        password: ${FW_WEB_PASSWORD}
      telnet:
        host: <Telnet_IP>
        port: <Telnet端口>
        user: root
        password: ${FW_TELNET_PASSWORD}
      ssh:
        host: <SSH_IP>
        port: 22
        user: root
        password: ${FW_SSH_PASSWORD}
        enabled: false

    tags:
      - firewall
      - <硬件系列>
```

## 查询型号流程

1. 按硬件系列、CPU 平台或关键字在 [reference/device-reference.md](reference/device-reference.md) 中查找
2. 返回匹配行的完整信息（硬件系列 / CPU 平台 / TLS 型号 / 备注）

## 查询设备流程

1. 按设备名或 host IP 在 `devices.yaml` 中查找
2. 返回匹配条目（含连接方式、device_type、tags）

## 凭据安全（强制规则）

- 所有 `password` 字段**必须使用 `${ENV_VAR}` 占位**（正则 `^\$\{[A-Z_][A-Z0-9_]*\}$`）
- **禁止明文凭据写入 devices.yaml**（manaul devices.yaml 明文凭据 `ngfw123!@#` 是反模式，不照搬）
- 用户需在工作区 `.env` 文件中设置对应环境变量（参考 templates/.env.example 变量清单）
- `devices.yaml` 和 `.env` 必须加入工作区 `.gitignore`，不入版本控制

### 环境变量约定

| 环境变量 | 用途 |
|---------|------|
| `FW_WEB_PASSWORD` | 防火墙 Web 管理密码 |
| `FW_SSH_PASSWORD` | 防火墙 SSH 密码 |
| `FW_TELNET_PASSWORD` | 防火墙 Telnet 密码 |

## 模板

- 设备清单模板：[templates/devices.yaml.example](templates/devices.yaml.example)
- 环境变量清单：[templates/.env.example](templates/.env.example)

用户复制 `devices.yaml.example` 为工作区 `devices.yaml`，复制 `.env.example` 为 `.env`，
在 `.env` 中填入实际凭据值后使用。

## Python 版本

本 SKILL 为纯元数据，不含 Python 脚本。连接脚本（ssh_exec.py / collect_sysinfo.py）归属
`device-connection` skill，声明 `requires-python >=3.9,<3.13`（telnetlib 兼容）。
