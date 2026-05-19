---
name: traffic-skill
description: 操作 traffic-skill Ixia-C 发流 agent。用于通过 traffic CLI 发起 L2-L4 流量、收集统计、校验丢包率、停止和删除流量，并按 ptm-atomic TG 原子操作规范消费结果。
---

# traffic-skill

本 skill 用于通过 Ixia-C 测试仪发起 L2-L4 流量、收集流量统计、校验丢包率、停止和删除流配置，并让这些能力遵循 `ptm-atomic` 的 TG 原子操作规范。

## 能做什么

- 启动一条 Ixia-C 流量流：`traffic send`
- 查看一条或多条流的统计：`traffic result`
- 校验 RX 是否收包、丢包率是否满足阈值：`traffic check`
- 停止指定流或全部流：`traffic stop`
- 删除指定流配置：`traffic clear`
- 以 JSON envelope 输出结果，供自动化编排或 `ptm-atomic` 风格消费者读取。

Atom 与 CLI 映射：

| ptm-atomic atom | traffic CLI |
|---|---|
| `tg_start_traffic_stream` | `traffic send` |
| `tg_capture_traffic_result` | `traffic result` |
| `tg_verify_traffic_loss` | `traffic check` |
| `tg_stop_traffic_stream` | `traffic stop` |
| `tg_delete_traffic_stream` | `traffic clear` |

## 典型测试流程

常规使用顺序是：

```text
send -> result -> check -> stop -> clear
```

示例：

```powershell
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --count 10 --pps 10 --l4 udp --src-port 8888 --dst-port 8888 --format json
traffic result --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
traffic check --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --max-loss 0.01 --format json
traffic stop --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
traffic clear --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
```

人工查看时可以省略 `--format json`，默认输出文本或表格。自动化调用时使用 `--format json`。

## 安全约束

- 不要输出、复制或记录 `configs/node2_tg_dut.yml` 中的真实账号、密码或实验室敏感信息。
- 文档和示例优先使用脱敏拓扑：`configs/topology_example.yaml`。
- 不要提交 `.venv/`、缓存、`traffic_config.json`、压缩包或真实联调日志。
- 真实 Ixia-C 联调会访问实验室设备；只有在明确需要硬件验证时才执行。
- JSON 成功结果写 stdout；失败结果和 snappi/Ixia-C warning 写 stderr。自动化程序应只把 stdout 当作成功数据源。

## 限制与边界

- `traffic send --continuous` 不能和自定义 `--count` 同时使用。
- `traffic send` 必须指定 `--name`。
- `traffic clear` 必须指定 `--name`，不支持清空全部流。
- `traffic result`、`traffic check`、`traffic stop` 的 `--name` 可选；不指定时作用于所有流。
- `traffic check` 只校验统计结果，不会自动停止流量。
- 单流统计中如果 flow TX 非 0 但 flow RX 为 0，会尝试使用 RX 端口统计回退；多流场景不做该回退。
- 第一版不支持从 atom YAML 自动生成 CLI 命令。
- 第一版不支持抓包、IxNetwork、TRex 或信而泰执行器。

## 运行入口

调用者需要先进入已部署的 `traffic-skill` 项目根目录，或使用绝对路径传入拓扑文件。项目根目录通常应包含：

```text
configs/
atoms/
packages/
```

调用前确认 `traffic` 命令已经安装并在当前 shell 的 `PATH` 中。最小检查方式：

```powershell
traffic --help
traffic send --help
```

推荐调用方式是在 `traffic-skill` 项目根目录下使用相对拓扑路径：

```powershell
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --count 10 --format json
```

如果调用者不在项目根目录下执行命令，`--topology` 必须传入可访问的绝对路径或相对当前目录正确的路径。

## 参数速查

通用参数：

| 参数 | 必填 | 适用命令 | 说明 |
|---|---:|---|---|
| `--topology` | 是 | 全部 | 拓扑 YAML 文件路径。 |
| `--tx` | 是 | 全部 | 发包侧 link 名称。 |
| `--rx` | 是 | 全部 | 收包侧 link 名称。 |
| `--name` | send/clear 必填；其他可选 | 全部 | 流名称。result/check/stop 不填时作用于所有流。 |
| `--format` | 否 | 全部 | `table` 或 `json`，默认 `table`。 |

`send` 专用参数：

| 参数 | 说明 |
|---|---|
| `--count` | 固定发送帧数，默认 `100`。 |
| `--continuous` | 持续发流；不能和自定义 `--count` 同时使用。 |
| `--pps` | 每秒包数，默认 `10000`。 |
| `--frame-size` | 帧长，默认 `128`。 |
| `--l3` | `ipv4`、`ipv6` 或 `arp`，默认 `ipv4`。 |
| `--l4` | `tcp`、`udp`、`icmp` 或 `icmpv6`。 |
| `--src-ip` / `--dst-ip` | 覆盖默认源/目的 IP。 |
| `--src-mac` / `--dst-mac` | 覆盖默认源/目的 MAC。 |
| `--src-port` / `--dst-port` | TCP/UDP 端口。 |
| `--vlan` | VLAN ID 或逗号分隔 VLAN 栈，例如 `100` 或 `100,200`。 |

`check` 专用参数：

| 参数 | 说明 |
|---|---|
| `--max-loss` | 最大允许丢包率，默认 `0.01`。 |

## 方法说明

### 1. 启动流量

ptm-atomic atom：

```text
tg_start_traffic_stream
```

CLI：

```powershell
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --count 10 --pps 10 --l4 udp --src-port 8888 --dst-port 8888 --format json
```

行为：

- 创建或覆盖同名流。
- 分配 Ixia-C 端口。
- 配置 TG 接口 IP。
- 预热邻居。
- 启动发流。
- 支持 IPv4、IPv6、ARP。
- 支持 TCP、UDP、ICMP、ICMPv6。
- 支持覆盖源/目的 IP、MAC、TCP/UDP 端口、VLAN、帧长、速率和发送方式。

常见变化：

```powershell
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name tcp_demo --l4 tcp --src-port 12345 --dst-port 80 --count 100 --format json
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name vlan_demo --vlan 100,200 --l4 udp --dst-port 4789 --count 100 --format json
traffic send --topology configs\topology_example.yaml --tx link1 --rx link2 --name continuous_demo --continuous --pps 1000 --format json
```

JSON `data` 示例：

```json
{
  "flow_name": "demo",
  "tx_link": "link1",
  "rx_link": "link2",
  "l3": "ipv4",
  "l4": "udp",
  "count": 10,
  "continuous": false,
  "pps": 10,
  "frame_size": 128
}
```

### 2. 查看结果

ptm-atomic atom：

```text
tg_capture_traffic_result
```

CLI：

```powershell
traffic result --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
```

行为：

- 查询指定流统计。
- 不传 `--name` 时查询所有流。

JSON `data`：

```json
{
  "flows": [
    {
      "name": "demo",
      "frames_tx": 10,
      "frames_rx": 10,
      "loss": 0.0,
      "frames_tx_rate": 0,
      "frames_rx_rate": 0,
      "state": "stopped"
    }
  ]
}
```

### 3. 校验丢包

ptm-atomic atom：

```text
tg_verify_traffic_loss
```

CLI：

```powershell
traffic check --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --max-loss 0.01 --format json
```

行为：

- 校验 `frames_rx > 0`。
- 校验丢包率 `loss <= --max-loss`。
- 单流场景下，如果 flow RX 为 0 且 flow TX 非 0，会尝试使用 RX 端口统计作为回退。
- 校验通过退出码为 `0`；校验失败退出码为 `1`。
- `check` 只判断结果，不会自动停止流量。

JSON `data` 示例：

```json
{
  "passed": true,
  "max_loss": 0.01,
  "failures": [],
  "flows": [
    {
      "name": "demo",
      "frames_tx": 10,
      "frames_rx": 10,
      "loss": 0.0,
      "frames_tx_rate": 0,
      "frames_rx_rate": 0,
      "state": "stopped"
    }
  ]
}
```

### 4. 停止流量

ptm-atomic atom：

```text
tg_stop_traffic_stream
```

CLI：

```powershell
traffic stop --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
```

行为：

- 传 `--name` 时停止指定流。
- 不传 `--name` 时停止所有流。

JSON `data`：

```json
{
  "stopped": "demo"
}
```

停止所有流时：

```json
{
  "stopped": "all"
}
```

### 5. 删除流量

ptm-atomic atom：

```text
tg_delete_traffic_stream
```

CLI：

```powershell
traffic clear --topology configs\topology_example.yaml --tx link1 --rx link2 --name demo --format json
```

行为：

- 删除指定流配置。
- `--name` 必填，避免误删全部流。

JSON `data`：

```json
{
  "deleted": "demo"
}
```

## JSON 返回契约

成功：

```json
{
  "status": "success",
  "data": {},
  "error_type": "",
  "diag_snapshot_ref": ""
}
```

失败：

```json
{
  "status": "failed",
  "data": {},
  "error_type": "INVALID_PARAM",
  "diag_snapshot_ref": "",
  "message": "failure summary"
}
```

## 错误处理指南

| error_type | 常见原因 | 处理建议 |
|---|---|---|
| `INVALID_PARAM` | 参数缺失、link 不存在、拓扑字段缺失、VLAN 越界、`--count` 与 `--continuous` 冲突 | 检查命令参数、拓扑文件路径、link 名称和 VLAN 范围。 |
| `DEVICE_UNREACHABLE` | SSH、snappi 或 Ixia-C API 连接失败 | 检查测试仪 IP、API server、SSH 端口、网络连通性和实验室设备状态。 |
| `TIMEOUT` | SSH、snappi 或 Ixia-C API 超时 | 确认设备是否忙碌，稍后重试；必要时检查 API 服务健康状态。 |
| `RESOURCE_NOT_FOUND` | 指定流不存在或没有统计 | 先执行 `result` 查看现有流；确认 `--name` 是否拼写正确；必要时重新 `send`。 |
| `STATE_MISMATCH` | `check` 发现 RX 为 0 或丢包率超阈值 | 查看 `result` 统计；检查链路、DUT 转发、ACL/策略、MAC/IP/VLAN 配置。 |
| `INTERNAL_ERROR` | 未分类异常 | 保留命令、stdout/stderr 和拓扑上下文，按调试流程定位根因。 |
