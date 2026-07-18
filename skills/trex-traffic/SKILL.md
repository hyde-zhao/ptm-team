---
name: trex-traffic
description: 操作 Cisco TRex stateless 发流服务。用于通过 tg CLI 配置接口、生成流量模板、发起 L2-L4 流量、校验丢包率、停止和删除流量，并按 ptm-atomic TG 原子操作规范消费结果。是 Ixia-C 版 traffic-skill 的 TRex 替代实现。
argument-hint: "<op_id> [--format json]"
user-invokable: true
status: active
---

# trex-traffic

本 skill 用于通过 Cisco TRex stateless 测试仪发起 L2-L4 流量、收集流量统计、校验丢包率、停止流量和删除流量模板，并让这些能力遵循 `ptm-atomic` 的 TG 原子操作规范。

trex-traffic 是 Ixia-C 版 `traffic-skill` 的 TRex 替代实现：后端由 `trex-api` FastAPI 服务和常驻 TRex Python API client 组成，CLI 通过 HTTP 调用 `trex-api`，由 `trex-api` 转换为 TRex 原生 YAML 并用 TRex Python API 执行。

## 能做什么

- 配置 TG 接口并学习网关 MAC（ARP/IPv6 ND）：`tg tg_config_interface`
- 创建或更新 TRex 流量模板 YAML：`tg tg_apply_traffic_template`
- 启动一条流量流：`tg tg_start_traffic_stream`
- 校验 RX 是否收包、丢包率是否满足阈值：`tg tg_verify_traffic_loss`
- 停止指定流并清理运行时状态：`tg tg_stop_traffic_stream`
- 删除流量模板 YAML：`tg tg_delete_traffic_template`
- 以 ptm-atomic JSON envelope 输出结果，供自动化编排或 `ptm-atomic` 风格消费者读取。

Atom 与 CLI 映射：

| ptm-atomic atom | trex-traffic CLI |
|---|---|
| `tg_config_interface` | `tg tg_config_interface` |
| `tg_apply_traffic_template` | `tg tg_apply_traffic_template` |
| `tg_start_traffic_stream` | `tg tg_start_traffic_stream` |
| `tg_verify_traffic_loss` | `tg tg_verify_traffic_loss` |
| `tg_stop_traffic_stream` | `tg tg_stop_traffic_stream` |
| `tg_delete_traffic_template` | `tg tg_delete_traffic_template` |

## 典型测试流程

常规使用顺序是：

```text
config -> apply -> start -> verify -> stop -> delete-template
```

示例（PowerShell）：

```powershell
tg tg_config_interface --interfaces '[{"port":"2_1","ip":"<IP_ADDRESS>","gateway":"<IP_ADDRESS>"},{"port":"2_2","ip":"20.1.1.2","gateway":"20.1.1.1"}]'
tg tg_apply_traffic_template --template udp-demo --tx-port 2_1 --rx-port 2_2 --ip-version ipv4 --l4-protocol udp --l4-sport 1234 --l4-dport 5678 --traffic-mode count --rate 100pps --count 500
tg tg_start_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --template udp-demo --name stream-1
tg tg_verify_traffic_loss --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1 --max-loss 0
tg tg_stop_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1
tg tg_delete_traffic_template --template udp-demo
```

人工查看时输出固定为格式化 JSON。自动化调用时可加 `--format json`（第一版仅支持 json）。

## 部署形态

trex-traffic 在 TG host 上以两个 systemd 常驻服务运行：

| 服务 | 作用 |
|---|---|
| `trex-stl.service` | Cisco TRex STL server（`t-rex-64`），DPDK 打包收包，监听 4500/4501 |
| `trex-api.service` | FastAPI 服务，监听 TCP 8000，进程内持有一个常驻 TRex Python API client |

`tg` CLI 通过 HTTP 调用 `trex-api`，`trex-api` 再通过 TRex Python API 调 `t-rex-64`。`trex-api` 持有的常驻 client 贯穿 start/verify/stop 全生命周期，因为 TRex v3.08 的端口计数器相对 client session，每步必须共享同一个 client。

完整的部署形态、systemd 服务、6 原子操作逐步实操与远端验证方法见 `references/six-atom-walkthrough.md`。

## 安全约束

- 不要输出、复制或记录真实实验室的账号、密码、IP、MAC 或 `ssh环境.txt` 类敏感信息。
- 文档和示例优先使用脱敏样例。
- 不要提交 `.venv/`、`__pycache__/`、`.pytest_cache/`、`*.egg-info/`、压缩包或真实联调日志。
- 真实 TRex 联调会访问实验室设备；只有在明确需要硬件验证时才执行。
- CLI 结果以 JSON envelope 写 stdout。自动化程序应只把 stdout 当作成功数据源。

## 限制与边界

- `tg tg_apply_traffic_template` 的 `--traffic-mode count` 必须配合 `--count`；`continuous` 模式不指定 count，靠 `tg_stop_traffic_stream` 停止。
- `tg tg_start_traffic_stream` 的 `--txport` 和 `--rxport` 必须不同，且都包含在 `--ports` 中。
- `tg tg_verify_traffic_loss` 的 `--name` 必须先经 `tg_start_traffic_stream` 创建。
- `tg tg_delete_traffic_template` 必须先 `tg_stop_traffic_stream`，否则模板仍被引用会返回 `RESOURCE_CONFLICT`。
- `--rate` 使用 TRex 风格单位，如 `100pps`、`10mbps`、`1gbps`。
- IPv6 流量（`--ip-version ipv6`）必须同时提供 `--src-ip` 和 `--dst-ip`。
- 第一版不支持抓包、ASTF 有状态流量和从 atom YAML 自动生成 CLI 命令。

## 运行入口

调用前确认 `tg` 命令已经安装并在当前 shell 的 PATH 中：

```powershell
tg --help
tg tg_config_interface --help
```

`tg` CLI 默认连接 `http://127.0.0.1:8000` 的 `trex-api`。若 `tg` CLI 与 `trex-api` 不在同一台机器，用环境变量指向目标 `trex-api`：

```powershell
$env:TREX_API_URL = "http://<trex-api-host>:8000"
```

最小连通性检查：

```powershell
Invoke-WebRequest -UseBasicParsing http://<trex-api-host>:8000/health
```

## 参数速查

`tg_config_interface`：

| 参数 | 必填 | 说明 |
|---|---|---|
| `--interfaces` | 是 | JSON 数组字符串，每个对象含 `port`、`ip`、`gateway`，可选 `mac`、`peer_mac`、`vlan`。 |

`tg_apply_traffic_template`：

| 参数 | 必填 | 说明 |
|---|---|---|
| `--template` | 是 | 模板名，限 `^[a-z0-9_-]+$`。 |
| `--tx-port` / `--rx-port` | 是 | 发包口 / 收包口。 |
| `--ip-version` | 否 | `ipv4`（默认）/`ipv6`。 |
| `--l4-protocol` | 是 | `tcp`/`udp`。 |
| `--l4-sport` / `--l4-dport` | 是 | 0–65535。 |
| `--traffic-mode` | 是 | `count`/`continuous`。 |
| `--rate` | 是 | TRex 风格，如 `100pps`。 |
| `--count` | mode=count 必填 | 发包数量。 |
| `--frame-size` | 否 | ≥64，默认 128。 |
| `--vlan` | 否 | VLAN ID。 |
| `--src-ip` / `--dst-ip` | 否 | 覆盖源/目的 IP；ipv6 必填。 |
| `--src-mac` / `--dst-mac` | 否 | 覆盖源/目的 MAC。 |

`tg_start_traffic_stream` / `tg_verify_traffic_loss` / `tg_stop_traffic_stream`：

| 参数 | 必填 | 说明 |
|---|---|---|
| `--ports` | 是 | 涉及端口，逗号分隔，如 `0,1`。 |
| `--txport` / `--rxport` | 是 | 发/收包口，不同且在 `--ports` 中。 |
| `--template` | start 必填 | 引用的模板名。 |
| `--name` | 是 | 流运行实例名，verify/stop 用它定位。 |
| `--max-loss` | verify 必填 | 允许的丢包比例阈值，`0` 表示零丢包。 |

`tg_delete_traffic_template`：

| 参数 | 必填 | 说明 |
|---|---|---|
| `--template` | 是 | 要删除的模板名。 |

## 方法说明

### 1. 配置接口

ptm-atomic atom：

```text
tg_config_interface
```

CLI：

```powershell
tg tg_config_interface --interfaces '[{"port":"2_1","ip":"<IP_ADDRESS>","gateway":"<IP_ADDRESS>"},{"port":"2_2","ip":"20.1.1.2","gateway":"20.1.1.1"}]'
```

行为：

- 把端口切到 L3 模式并下发 IP/网关。
- 自动发起 ARP（IPv4）或 IPv6 ND，学习网关 MAC。
- 学到的网关 MAC 由常驻 `trex-api` client 保存，供后续 `tg_start_traffic_stream` 构造报文时作目的 MAC。
- 返回每个端口的 `gateway_mac`、`neighbor_state`（`REACHABLE` 表示网关可达）。

JSON `data` 示例：

```json
{
  "status": "configured",
  "interfaces": [
    {
      "port": "0",
      "ip": "<IP_ADDRESS>",
      "gateway": "<IP_ADDRESS>",
      "ip_version": "ipv4",
      "gateway_mac": "aa:bb:cc:dd:ee:ff",
      "neighbor_protocol": "arp",
      "neighbor_learned": true,
      "neighbor_state": "REACHABLE"
    }
  ]
}
```

### 2. 生成流量模板

ptm-atomic atom：

```text
tg_apply_traffic_template
```

CLI：

```powershell
tg tg_apply_traffic_template --template udp-demo --tx-port 2_1 --rx-port 2_2 --ip-version ipv4 --l4-protocol udp --l4-sport 1234 --l4-dport 5678 --traffic-mode count --rate 100pps --count 500
```

行为：

- 把请求字段渲染成 TRex 原生 YAML，写到 TG host 的模板目录。
- 不打流量，纯文件操作。
- 返回模板路径。

JSON `data` 示例：

```json
{
  "template": "udp-demo",
  "template_path": "/opt/trex/v3.08/trex_template/udp-demo.yaml",
  "status": "applied",
  "updated": true
}
```

### 3. 启动流量

ptm-atomic atom：

```text
tg_start_traffic_stream
```

CLI：

```powershell
tg tg_start_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --template udp-demo --name stream-1
```

行为：

- 读取模板 YAML，抢占端口，清理旧流。
- 用第 1 步学到的网关 MAC 构造 `Ether/IP/UDP/payload` 报文。
- 清零端口计数器建立基线，启动发包。
- `count` 模式会等待指定数量包发完后再返回。

JSON `data` 示例：

```json
{
  "name": "stream-1",
  "template": "udp-demo",
  "txport": "0",
  "rxport": "1",
  "state": "running"
}
```

### 4. 校验丢包

ptm-atomic atom：

```text
tg_verify_traffic_loss
```

CLI：

```powershell
tg tg_verify_traffic_loss --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1 --max-loss 0
```

行为：

- 读取 TX 端口发包数和 RX 端口收包数。
- 计算 `loss = tx - rx`、`loss_ratio = loss / tx`。
- `passed` 为 `loss_ratio <= max_loss` 且 `tx_packets > 0`。

JSON `data` 示例：

```json
{
  "passed": true,
  "tx_packets": 500,
  "rx_packets": 500,
  "loss": 0,
  "loss_ratio": 0.0,
  "max_loss": 0
}
```

### 5. 停止流量

ptm-atomic atom：

```text
tg_stop_traffic_stream
```

CLI：

```powershell
tg tg_stop_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1
```

行为：

- 停止 TX 端口发包并清除该端口上的所有 stream。
- 释放端口，从运行时状态中移除该流实例。
- 必须在 `tg_delete_traffic_template` 之前执行。

JSON `data` 示例：

```json
{
  "name": "stream-1",
  "stopped": true,
  "cleaned": true
}
```

### 6. 删除模板

ptm-atomic atom：

```text
tg_delete_traffic_template
```

CLI：

```powershell
tg tg_delete_traffic_template --template udp-demo
```

行为：

- 检查模板是否仍被运行中的流引用，被引用时返回 `RESOURCE_CONFLICT`。
- 未被引用时删除模板 YAML 文件。

JSON `data` 示例：

```json
{
  "template": "udp-demo",
  "deleted": true
}
```

## JSON 返回契约

成功：

```json
{
  "op_id": "tg_start_traffic_stream",
  "status": "success",
  "data": {},
  "error_type": "NONE",
  "diag_snapshot_ref": ""
}
```

失败：

```json
{
  "op_id": "tg_start_traffic_stream",
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
| `INVALID_PARAM` | 参数缺失、端口相同、模板名非法、`--count` 与 `traffic_mode` 不匹配、rate 单位错误、IPv6 缺 src/dst | 检查命令参数、端口配对、模板名和 rate 格式。 |
| `RESOURCE_CONFLICT` | 删除仍被运行流引用的模板 | 先执行 `tg_stop_traffic_stream` 再删除模板。 |
| `RESOURCE_NOT_FOUND` | 模板不存在或 `--name` 未创建 | 确认 `--template`/`--name` 拼写，先执行 apply/start。 |
| `STATE_MISMATCH` | verify 发现 RX 为 0 或丢包率超阈值、接口网关不可达 | 检查链路、DUT 转发、ACL/策略、MAC/IP/VLAN 配置、网关是否在线。 |
| `DEVICE_UNREACHABLE` | `trex-api` 连不上 `t-rex-64` | 检查 `trex-stl.service` 状态、4500/4501 端口、`trex-api` 与 `t-rex-64` 启动顺序。 |
| `TIMEOUT` | 操作超时 | 确认 TRex 是否忙碌，稍后重试。 |
| `INTERNAL_ERROR` | 未分类异常 | 检查 `journalctl -u trex-api`、`journalctl -u trex-stl`，保留命令和上下文定位根因。 |

## 参考文档

| 文档 | 内容 |
|---|---|
| `references/six-atom-walkthrough.md` | 6 原子操作完整实操手册（含每步背后行为、部署形态与远端验证方法）。 |

## ptm-te 编排接入（v1.5）

ptm-te 测试执行工程师通过 op_mapper 承载 tg_* 编排：

- **执行路径**：`ptm-atomic run --base-url <trex-api> [--session-file] tg trex <action> [flags] [--execute]`（`tg` CLI 也可独立用于人工/脚本直调）。
- **映射层**：`skills/policy-route-execution/scripts/op_mapper.py` 的 `OP_ID_TO_SUBCOMMAND` 等 5 张表已覆盖 6 个 tg op，命令树三层 `tg trex <action>`（action 名与 op_id 不同，如 `tg_config_interface`→`config-interface`）。
- **回滚**：`tg_start_traffic_stream` 的 inverse_op 为 `tg_stop_traffic_stream`（声明驱动 mode E：按 `required_inputs=[ports,txport,rxport,name]` 构造 args）；`tg_stop` 为 `manual_required`（不自动回滚）；其余无 rollback_strategy。
- **session**：tg 族的 `--base-url` 是 trex-api 地址（非 NGFW），`--session-file` 对 tg 无害（trex runner 忽略）。trex-api 常驻 client 与 ptm-te session 体系独立。

## Gotchas

- **`tg` CLI 默认 API URL 硬编码**：`src/trex_api/cli.py` 默认 `http://<IP_ADDRESS>:8000`，与 SKILL.md「默认 127.0.0.1:8000」不一致。ptm-te 编排经 `ptm-atomic run --base-url` 传 trex-api 地址覆盖；人工直调 `tg` 时用 `TREX_API_URL` 环境变量覆盖。
- **apply 与 start/stop/verify 的 flag 命名不同**：apply 用 `--tx-port/--rx-port`（连字符），start/stop/verify 用 `--txport/--rxport`（无连字符）。op_mapper 的 `ARGS_TO_FLAGS` 已按 `run_trex.py` 真相源精确映射。
- **count 模式阻塞**：`tg_start_traffic_stream --traffic-mode count` 会阻塞至发包完成，atom 定义 `timeout_ms=60000`；编排需预留足够超时。
- **`STATE_MISMATCH` 不等于用例 FAIL**：verify 丢包超阈值时 `error_type=STATE_MISMATCH`，但负向用例（验证 ACL 拦截）期望丢包，需与 `expected_result` 语义比对。
- **`delete-template` 前必须 `stop`**：否则返回 `RESOURCE_CONFLICT`。
- **`tg` 命令随 ptm-atomic 工具安装**：`ptm-atomic run tg trex --help` 可验证可用性；人工直调用 `tg --help`（需 `uv pip install -e skills/trex-traffic` 注册 `[project.scripts] tg`）。

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|---------|
| v1.0 | 2026-07-15 | host-orchestrator | trex-traffic skill 初始交付（6 atom + tg CLI + trex-api 服务定义） |
| v1.1 | 2026-07-17 | host-orchestrator | ptm-te 编排接入（op_mapper 扩展 tg 族，v1.5）；新增 Gotchas 章节与 ptm-te 编排接入小节 |
