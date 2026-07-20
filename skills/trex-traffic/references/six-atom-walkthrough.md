# TRex 六原子操作实操手册

本文档用一组可复制粘贴的命令，带你完整跑一遍 TRex 流量测试的六个原子操作，
并解释每一步在远端**实际发生了什么、能在哪里验证生效**。

- 适用环境：TRex v3.08 + trex-api 已在 TG host（`<IP_ADDRESS>`）以 systemd 常驻运行。
- 执行位置：**本机即可**（见下文「前置：本机执行 vs 远端执行」）。
- 6 步官方顺序：`config -> apply -> start -> verify -> stop -> delete-template`。

---

## 0. 前置知识

### 0.1 整体链路

```
本机 (curl / tg CLI)
   │  HTTP JSON
   ▼
trex-api (:8000, systemd 常驻)          ← FastAPI，进程内持有一个常驻 TRex client
   │  TRex Python API (RPC)
   ▼
t-rex-64 (:4500/:4501, systemd 常驻)    ← DPDK，真正发包收包
   │
   ▼
物理网卡 port0 / port1
```

关键认知：

- **常驻 TRex client 在 trex-api 进程内存里，不在你的本机。** 本机执行只是把
  HTTP 请求的发出地从 `127.0.0.1` 换成本机 IP，请求照样打到同一个 trex-api 进程，
  共享同一个常驻 client、共享同一套端口计数基线。所以本机跑和上机跑对 TRex 完全等价。
- TRex v3.08 的端口计数器是**相对 client session** 的：`start` 里 `clear_stats`
  建立基线（清零），`verify` 里读的是相对基线的增量。这也是为什么
  start/verify/stop 必须由同一个常驻 trex-api 进程完成——重启 trex-api 会丢基线。

### 0.2 真实端口参数（来自 `ssh环境.txt`）

| TRex 端口 | PCI | 本机 IP | 网关 | 链路 |
|---|---|---|---|---|
| port 0 | 05:00.0 | <IP_ADDRESS> | <IP_ADDRESS> | UP |
| port 1 | 05:00.1 | 20.1.1.2 | 20.1.1.1 | UP |

这份 IP 同时也写死在 TRex 平台配置文件里（见 1.3），本例的 IP/网关都用这套值。

### 0.3 本机执行 vs 远端执行

**本机就能跑，不必 ssh 上 TG host。** 实测：本机直连 `<IP_ADDRESS>:8000/health`
返回 `{"status":"ok"}`，因为本机与 TG host 同管理网段，请求包从 TG host 的 `Admin`
接口进来，命中线上 `iptables -i Admin --dport 8000 -j ACCEPT` 规则。

本机唯一要做的事——告诉 CLI 去连哪：

```bash
export TREX_API_URL=http://<IP_ADDRESS>:8000
```

不设的话，CLI 默认连 `127.0.0.1:8000`（`src/trex_api/cli.py:15`），本机没有 trex-api，
会连不上。`curl` 不受这个变量影响，每次都要在 URL 里写全 `<IP_ADDRESS>:8000`。

### 0.4 在哪个文件夹执行

**随便哪个文件夹都行，`tg` 不依赖工作目录。**

原因：`tg` 是 `pip install` 装的全局命令（`tg.exe` 在 Python Scripts 目录、已加入 PATH），
它的全部工作就是把参数拼成 JSON 发 HTTP 给 trex-api，**不读取任何本地配置文件、不依赖
当前目录**（`src/trex_api/cli.py` 源码里没有任何 `open()/read`/cwd 读取）。

- **本机执行**：任意文件夹。推荐在 Git Bash 里 `cd ~` 或就停在当前目录都行，先
  `export TREX_API_URL=...`（环境变量是 shell 级的，对当前 shell 所有目录有效）。
- **远端执行**：ssh 进 TG host 后默认在 `/root`，也能在任意目录执行。`/opt/trex-api`、
  `/opt/trex/v3.08` 是服务/二进制所在目录，**只是供你看日志和文件用，不是执行目录**。

验证（在任意目录执行都应成功）：

```bash
# 本机，任意文件夹
tg --help                                    # 能打印命令列表说明 tg 全局可用
curl -s --noproxy '*' http://<IP_ADDRESS>:8000/health   # 连通性
```

### 0.5 验证服务可用

```bash
# 本机执行
curl -s -m 8 --noproxy '*' http://<IP_ADDRESS>:8000/health
# 期望: {"status":"ok"}
```

> curl 的 `--noproxy '*'` 防止本机设过 HTTP 代理时被拦截。本机若无代理环境变量可省略。

---

## 1. tg_config_interface —— 配置接口并学习网关 MAC

### 1.1 这一步在做什么

把端口 0/1 切到 L3 模式，并让 TRex 替你向网关发 **ARP**，学回网关的真实 MAC。
这个网关 MAC 会在第 ③ 步 `tg_start_traffic_stream` 里被当作报文的**目的 MAC**。

代码位置：`src/trex_api/service.py:36`（编排）+ `src/trex_api/trex/api_client.py:89`
（`TrexPythonApiClient.configure_interfaces`）。真实调用链：

```
client.acquire(ports=[0,1], force=True)       # 抢占端口
client.set_service_mode(ports=[0,1], True)    # 进入 service 模式（L3/ARP 需要）
for 每个端口:
    client.set_l3_mode(port, src_ipv4=本口IP, dst_ipv4=网关)
        → TRex 自动发 ARP 请求网关
    client.get_port_info(ports=[port])[0]      # 取回 arp 字段 = 网关 MAC
client.set_service_mode(ports=[0,1], False)   # 退出 service 模式
client.release(ports=[0,1])
```

### 1.2 执行命令

CLI（本机，已 `export TREX_API_URL`）：

```bash
tg tg_config_interface --interfaces '[{"port":"2_1","ip":"<IP_ADDRESS>","gateway":"<IP_ADDRESS>"},{"port":"2_2","ip":"20.1.1.2","gateway":"20.1.1.1"}]'
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_config_interface \
  -H 'Content-Type: application/json' \
  -d '{
    "interfaces": [
      {"port":"2_1","ip":"<IP_ADDRESS>","gateway":"<IP_ADDRESS>"},
      {"port":"2_2","ip":"20.1.1.2","gateway":"20.1.1.1"}
    ]
  }'
```

`--interfaces` 的值是一个 JSON 数组字符串，每个对象字段：

| 字段 | 必填 | 说明 |
|---|---|---|
| `port` | 是 | TRex 端口号，字符串 `"0"`/`"1"` |
| `ip` | 是 | 本端口 IP |
| `gateway` | 是 | 网关 IP，必须与 `ip` 同版本（IPv4/IPv6） |
| `mac` | 否 | 本端口 MAC（IPv6 ND 时作源 MAC） |
| `peer_mac` | 否 | 对端 MAC（模拟后端用，real 后端会忽略） |
| `vlan` | 否 | VLAN tag |

### 1.3 预期返回

```json
{
  "op_id": "tg_config_interface",
  "status": "success",
  "data": {
    "status": "configured",
    "interfaces": [
      {
        "port": "0",
        "ip": "<IP_ADDRESS>",
        "gateway": "<IP_ADDRESS>",
        "mac": null,
        "peer_mac": null,
        "vlan": null,
        "ip_version": "ipv4",
        "gateway_mac": "aa:bb:cc:dd:ee:ff",
        "neighbor_protocol": "arp",
        "neighbor_learned": true,
        "arp_learned": true,
        "nd_learned": false,
        "neighbor_state": "REACHABLE"
      },
      { "port": "1", "...": "同上，gateway_mac 为 20.1.1.1 的 MAC" }
    ]
  },
  "error_type": "NONE",
  "diag_snapshot_ref": ""
}
```

重点看每个端口的：

- `gateway_mac`：TRex 用 ARP 学到的真实网关 MAC（非空才算成功）。
- `neighbor_learned: true` / `neighbor_state: "REACHABLE"`：网关可达。
- 若 `neighbor_learned: false`，trex-api 会返回 `status:"failed"` +
  `error_type:"STATE_MISMATCH"`，并在 `data.failed_ports` 列出失败的端口
  （`service.py:45`）。通常是网关不通或链路 down。

### 1.4 怎么在远端验证生效（重点）

> **常见误解：以为这一步会写文件。实际不写任何文件。**
> `set_l3_mode` 是 TRex 的运行时 RPC，把 IP/网关下发给 t-rex-64 进程内存，不落盘。
> 所以 `ls /opt/...` 看不到任何新增文件——这是正常的，不是没生效。

生效证据要看三个地方：

**(a) 平台配置文件里本就写死了这套 IP（对照确认）**

```bash
# 远端执行
cat /opt/trex/v3.08/cfg/trex_l3_0500.yaml
```

你会看到 `port_info` 里已经写死了和本例一致的 IP/网关——这是 `t-rex-64 --cfg`
启动时读的平台配置，`tg_config_interface` 是在运行时把同一套 IP 再下发确认一次
并触发 ARP：

```yaml
port_info:
  - ip: <IP_ADDRESS>
    default_gw: <IP_ADDRESS>
  - ip: 20.1.1.2
    default_gw: 20.1.1.1
```

**(b) 返回 JSON 里的 `gateway_mac` 非空**

这是最直接的生效证据——能学到 MAC 说明 ARP 成功、L3 模式生效。

**(c) TRex server 的端口信息输出**

```bash
# 远端执行
journalctl -u trex-stl -n 50 --no-pager | grep -iE 'arp|gateway|10.1.1'
```

或在 t-rex-64 交互端 `trex-console` 里 `port -a` 查看端口属性，能看到 L3 mode
和学到的 ARP 表项。

### 1.5 学到的 MAC 存在哪

trex-api 把每个端口学到的 `gateway_mac` 存在**进程内存**的
`TrexPythonApiClient.interfaces` 字典里（`api_client.py:138`），key 是端口号。
第 ③ 步构造报文时会从这里取目的 MAC。所以：**第 ① 步和第 ③ 步之间不要重启
trex-api**，否则内存里学到的 MAC 丢失，第 ③ 步拿不到目的 MAC。

---

## 2. tg_apply_traffic_template —— 生成 TRex 原生 YAML

### 2.1 这一步在做什么

把请求字段渲染成 TRex 能直接加载的 YAML 模板文件，写到磁盘。**这一步完全不碰 TRex，
不打流量**，是纯文件操作。代码位置：`src/trex_api/service.py:57` +
`src/trex_api/trex/template_renderer.py`。

### 2.2 执行命令

CLI：

```bash
tg tg_apply_traffic_template \
  --template udp-demo \
  --tx-port 2_1 --rx-port 2_2 \
  --ip-version ipv4 --l4-protocol udp \
  --l4-sport 1234 --l4-dport 5678 \
  --traffic-mode count --rate 100pps --count 500
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_apply_traffic_template \
  -H 'Content-Type: application/json' \
  -d '{
    "template":"udp-demo",
    "tx_port":"0","rx_port":"1",
    "ip_version":"ipv4","l4_protocol":"udp",
    "l4_sport":1234,"l4_dport":5678,
    "traffic_mode":"count","rate":"100pps","count":500
  }'
```

参数说明（schema 在 `src/trex_api/schemas.py:34` `ApplyTrafficTemplateRequest`）：

| 参数 | 必填 | 校验规则 |
|---|---|---|
| `template` | 是 | 只能 `^[a-z0-9_-]+$`（小写字母数字下划线连字符） |
| `tx_port` / `rx_port` | 是 | 发包口 / 收包口 |
| `ip_version` | 否 | `ipv4`（默认）/`ipv6`；选 ipv6 必须同时给 `src_ip`+`dst_ip` |
| `l4_protocol` | 是 | `tcp`/`udp` |
| `l4_sport` / `l4_dport` | 是 | 0–65535 |
| `traffic_mode` | 是 | `count`（发定量包）/`continuous`（持续发直到 stop） |
| `rate` | 是 | TRex 风格，如 `100pps`、`10mbps`、`1gbps`（正则 `^[1-9][0-9]*(pps\|kbps\|mbps\|gbps)`） |
| `count` | mode=count 时必填 | 正整数，发多少包 |
| `frame_size` | 否 | ≥64，默认 128 |
| `vlan` / `src_ip` / `dst_ip` / `src_mac` / `dst_mac` | 否 | 可选覆盖 |

> 本例用 `count` + 500 包 + 100pps：500÷100 = 5 秒发完，短平快、适合学习。

### 2.3 预期返回

```json
{
  "op_id": "tg_apply_traffic_template",
  "status": "success",
  "data": {
    "template": "udp-demo",
    "template_path": "/opt/trex/v3.08/trex_template/udp-demo.yaml",
    "status": "applied",
    "updated": true
  },
  "error_type": "NONE"
}
```

### 2.4 在远端验证文件真的生成了（重点）

这一步**真的写文件**，和第 ① 步不同，可以直接看：

```bash
# 远端执行：看文件是否出现
ls -l /opt/trex/v3.08/trex_template/

# 期望看到:
# -rw-r--r-- 1 root root  xxx  udp-demo.yaml
```

```bash
# 远端执行：看渲染出的 TRex 原生 YAML 内容
cat /opt/trex/v3.08/trex_template/udp-demo.yaml
```

期望内容（由 `render_template_payload` 生成，`template_renderer.py:11`）：

```yaml
template: udp-demo
template_type: stl
ports:
  tx_port: '0'
  rx_port: '1'
packet:
  ip_version: ipv4
  l4_protocol: udp
  l4_sport: 1234
  l4_dport: 5678
traffic:
  mode: count
  count: 500
  rate: 100pps
```

> 注意：这个 YAML 里**没有** `src_ip`/`dst_ip`/`src_mac`/`dst_mac`，因为本例没传。
> 这些值会在第 ③ 步 `start` 时由 trex-api 从「第 ① 步学到的网关 MAC」和
> 「平台配置的端口 IP」动态补齐（见 `api_client.py:_build_packet`）。

trex-api 还会把文件路径记进进程内存 `RuntimeStore.templates`（`service.py:66`），
供后续步骤查路径用。

---

## 3. tg_start_traffic_stream —— 加载流、清计数、发包

### 3.1 这一步在做什么

读模板 YAML → 抢占端口 → 清旧流 → 用第 ① 步的网关 MAC 拼出
`Ether/IP/UDP/payload` 报文 → 注册 stream → **清零计数器建基线** → start。
代码位置：`src/trex_api/service.py:77` + `src/trex_api/trex/api_client.py:145`。

调用链：

```
读模板 YAML
client.acquire(ports, force=True)
client.stop([tx_port])                    # 先停掉旧流
client.remove_all_streams([tx_port])     # 清旧 stream
get_port_info([tx, rx])                   # 取端口 IP/MAC
_build_packet(...)                        # 用第①步 gateway_mac 当目的 MAC
api.STLStream(name=..., packet=..., mode=...)
client.add_streams(stream, [tx_port])
client.clear_stats(ports)                 # ← 关键：建立计数基线（清零）
client.get_stats(ports, sync_now=True)    # 同步基线
client.start([tx_port], force=True)
if mode == count:
    client.wait_on_traffic(timeout=60)   # ← 等这 500 包发完，会阻塞约 5 秒
```

### 3.2 执行命令

CLI：

```bash
tg tg_start_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --template udp-demo --name stream-1
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_start_traffic_stream \
  -H 'Content-Type: application/json' \
  -d '{
    "ports":["0","1"],"txport":"0","rxport":"1",
    "template":"udp-demo","name":"stream-1"
  }'
```

参数（schema `schemas.py:88`）：

| 参数 | 必填 | 说明 |
|---|---|---|
| `ports` | 是 | 涉及的端口列表，CLI 用逗号分隔字符串 `"0,1"` |
| `txport` | 是 | 发包口，必须在 `ports` 里 |
| `rxport` | 是 | 收包口，必须在 `ports` 里，且 ≠ txport |
| `template` | 是 | 第 ② 步创建的模板名 |
| `name` | 是 | 本次流的运行实例名，verify/stop 用它定位 |

### 3.3 ⚠️ 这一步会阻塞约 5 秒，不是卡死

因为 `traffic_mode=count` 且 500 包，`api_client.py:172` 会调
`wait_on_traffic(timeout=60)` 等发完才返回。500 包 ÷ 100pps ≈ 5s。CLI 的 httpx
超时 30s（`cli.py:30`），够用。**别中途 Ctrl-C**。

### 3.4 预期返回

```json
{
  "op_id": "tg_start_traffic_stream",
  "status": "success",
  "data": {
    "name": "stream-1",
    "template": "udp-demo",
    "txport": "0",
    "rxport": "1",
    "state": "running"
  },
  "error_type": "NONE"
}
```

### 3.5 在远端验证生效（重点）

这一步的「生效」是**运行时打流**，证据在 TRex server 输出里，不在文件里。

**(a) TRex 实时统计**

```bash
# 远端执行，实时看 TX/RX
journalctl -u trex-stl -f
# 打流时能看到 Total-Tx / Total-Rx 不为 0、PPS 上来
```

**(b) trex-api 日志看到请求**

```bash
# 远端执行
journalctl -u trex-api -f
# 能看到 "POST /api/v1/ops/tg_start_traffic_stream HTTP/1.1" 200
```

**(c) 端口计数器已被清零**

第 ④ 步 verify 读到的 `tx_packets` 就是从这个清零点开始的增量——所以如果第 ③ 步
没真正执行 `clear_stats`，第 ④ 步会读到 0 或脏数据。

---

## 4. tg_verify_traffic_loss —— 取计数、算丢包

### 4.1 这一步在做什么

先 `sleep 3` 秒（`TREX_VERIFY_SAMPLE_SECONDS`，给收包留时间），再读两个端口的
计数器，取 **txport 的 `opackets`（发包数）** 和 **rxport 的 `ipackets`（收包数）**，
算丢包。代码位置：`src/trex_api/service.py:99` + `src/trex_api/trex/stats_parser.py`。

```
await asyncio.sleep(3)                    # 等 3 秒让包收完
stats = client.get_stats(ports)
tx_packets = stats[txport]["opackets"]   # 发了多少
rx_packets = stats[rxport]["ipackets"]    # 收了多少
loss = tx_packets - rx_packets
loss_ratio = loss / tx_packets
passed = (loss_ratio <= max_loss) and (tx_packets > 0)
```

### 4.2 执行命令

CLI：

```bash
tg tg_verify_traffic_loss --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1 --max-loss 0
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_verify_traffic_loss \
  -H 'Content-Type: application/json' \
  -d '{
    "ports":["0","1"],"txport":"0","rxport":"1",
    "name":"stream-1","max_loss":0
  }'
```

参数（schema `schemas.py:111`）：

| 参数 | 必填 | 说明 |
|---|---|---|
| `ports`/`txport`/`rxport` | 是 | 同 start，必须一致 |
| `name` | 是 | 要验证的流实例名，必须先 start 过 |
| `max_loss` | 是 | 允许的丢包比例阈值（0–N，0 表示零丢包） |

> `max_loss` 是**比例**不是绝对包数。`0` = 不允许任何丢包；`0.01` = 允许 1%。

### 4.3 预期返回

```json
{
  "op_id": "tg_verify_traffic_loss",
  "status": "success",
  "data": {
    "passed": true,
    "tx_packets": 500,
    "rx_packets": 500,
    "loss": 0,
    "loss_ratio": 0.0,
    "max_loss": 0
  },
  "error_type": "NONE"
}
```

判失败的情形（`service.py:126`）：

- `tx_packets <= 0`：返回 `STATE_MISMATCH`，附 `reason:"no transmitted packets were observed"`。
- `loss_ratio > max_loss`：返回 `STATE_MISMATCH`，`passed:false`。
- `name` 没 start 过：返回 `RESOURCE_NOT_FOUND`。

### 4.4 在远端验证生效

```bash
# 远端执行：trex-api 日志能看到这次 verify 请求，以及前面 start 后 3 秒才发
journalctl -u trex-api -n 20 --no-pager | grep verify
```

返回 JSON 里的 `tx_packets:500 rx_packets:500` 就是铁证——说明第 ③ 步真的发了 500 包、
port1 真的收到了 500 包。

---

## 5. tg_stop_traffic_stream —— 停流并清理

### 5.1 这一步在做什么

抢占端口 → 停 txport 发包 → 清掉 txport 上的所有 stream → 释放端口。
代码位置：`src/trex_api/service.py:134` + `api_client.py:185`。

```
client.acquire(ports, force=True)
client.stop([txport])
client.remove_all_streams([txport])
client.release(ports)
```

### 5.2 执行命令

CLI：

```bash
tg tg_stop_traffic_stream --ports "2_1,2_2" --txport 2_1 --rxport 2_2 --name stream-1
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_stop_traffic_stream \
  -H 'Content-Type: application/json' \
  -d '{
    "ports":["0","1"],"txport":"0","rxport":"1",
    "name":"stream-1"
  }'
```

### 5.3 预期返回

```json
{
  "op_id": "tg_stop_traffic_stream",
  "status": "success",
  "data": {
    "name": "stream-1",
    "stopped": true,
    "cleaned": true
  },
  "error_type": "NONE"
}
```

### 5.4 为什么这一步必须做

trex-api 内存里 `RuntimeStore.streams` 记录了哪些 stream 还在运行，并据此判断模板
是否「被引用」（`service.py:157` `template_in_use`）。**不 stop 直接删模板**，
第 ⑥ 步会返回 `RESOURCE_CONFLICT`。所以 ⑤ 是 ⑥ 的前置。

---

## 6. tg_delete_traffic_template —— 删除模板 YAML

### 6.1 这一步在做什么

检查模板是否还被 running stream 引用 → 没有 → `unlink` 删掉磁盘上的 YAML 文件 →
从内存 store 移除路径记录。代码位置：`src/trex_api/service.py:151`。

### 6.2 执行命令

CLI：

```bash
tg tg_delete_traffic_template --template udp-demo
```

等价 curl：

```bash
curl -s --noproxy '*' -X POST http://<IP_ADDRESS>:8000/api/v1/ops/tg_delete_traffic_template \
  -H 'Content-Type: application/json' \
  -d '{"template":"udp-demo"}'
```

### 6.3 预期返回

```json
{
  "op_id": "tg_delete_traffic_template",
  "status": "success",
  "data": {
    "template": "udp-demo",
    "deleted": true
  },
  "error_type": "NONE"
}
```

### 6.4 在远端验证文件真的删了（重点）

```bash
# 远端执行
ls -l /opt/trex/v3.08/trex_template/
# 期望: udp-demo.yaml 不见了（只剩之前可能存在的其他文件）
```

返回 `RESOURCE_CONFLICT` 说明第 ⑤ 步没做或没成功；返回 `RESOURCE_NOT_FOUND`
说明文件本来就不在（可能第 ② 步没成功或已被删过）。

---

## 7. 一键脚本（可选）

把 6 步打包，带分隔回显，适合反复练习。在 TG host 上 `bash demo.sh` 运行：

```bash
#!/usr/bin/env bash
set -euo pipefail
API="${TREX_API_URL:-http://127.0.0.1:8000}"
post() {  # op_id  json
  curl -s --noproxy '*' -X POST "$API/api/v1/ops/$1" -H 'Content-Type: application/json' -d "$2"; echo
}
step() { echo; echo "==================== $1 ===================="; }

step "1/6 tg_config_interface"
post tg_config_interface '{"interfaces":[{"port":"2_1","ip":"<IP_ADDRESS>","gateway":"<IP_ADDRESS>"},{"port":"2_2","ip":"20.1.1.2","gateway":"20.1.1.1"}]}'

step "2/6 tg_apply_traffic_template"
post tg_apply_traffic_template '{"template":"udp-demo","tx_port":"0","rx_port":"1","ip_version":"ipv4","l4_protocol":"udp","l4_sport":1234,"l4_dport":5678,"traffic_mode":"count","rate":"100pps","count":500}'

step "3/6 tg_start_traffic_stream (会等约5秒)"
post tg_start_traffic_stream '{"ports":["0","1"],"txport":"0","rxport":"1","template":"udp-demo","name":"stream-1"}'

step "4/6 tg_verify_traffic_loss (内部先sleep 3s)"
post tg_verify_traffic_loss '{"ports":["0","1"],"txport":"0","rxport":"1","name":"stream-1","max_loss":0}'

step "5/6 tg_stop_traffic_stream"
post tg_stop_traffic_stream '{"ports":["0","1"],"txport":"0","rxport":"1","name":"stream-1"}'

step "6/6 tg_delete_traffic_template"
post tg_delete_traffic_template '{"template":"udp-demo"}'

echo; echo "==================== done ===================="
```

脚本说明：

- `post` 函数封装了 `curl` + JSON body，末尾 `echo` 让输出换行。
- 本机运行时把第一行 `API` 改成 `http://<IP_ADDRESS>:8000`（或先
  `export TREX_API_URL=http://<IP_ADDRESS>:8000`，脚本会自动读取）。
- `set -euo pipefail` 任一步 curl 失败即整体退出，便于定位。
- 如需保存每步返回，把 `post` 调用改成 `post ... | tee step1.json`。

---

## 8. 边跑边看的三个窗口（强烈建议）

在 TG host 上另开两个 ssh 终端，边在本机跑 6 步边盯：

| 窗口 | 命令 | 看什么 |
|---|---|---|
| TRex 实时打流 | `journalctl -u trex-stl -f` | 第 ③ 步时 Total-Tx/Rx、PPS 不为 0 |
| trex-api 请求日志 | `journalctl -u trex-api -f` | 每步的 `POST /api/v1/ops/... 200` |
| 模板文件生灭 | `watch -n1 'ls -l /opt/trex/v3.08/trex_template/'` | 第 ② 步出现、第 ⑥ 步消失 |

这样能同时看到「HTTP 请求 → trex-api 处理 → TRex 打包收包 → 文件变化」四条线，
整个链路就清楚了。

---

## 9. 常见坑

| 现象 | 原因 | 解决 |
|---|---|---|
| 第 ① 步返回 `STATE_MISMATCH`、`neighbor_learned:false` | 网关不通或链路 down | 检查物理链路、网关是否真的存在 |
| 第 ③ 步卡住 | 不是卡死，count 模式在等发完 | 等 5 秒；或改用 `continuous` 模式 |
| 第 ③ 步返回 `RESOURCE_NOT_FOUND` | 模板名不对或第 ② 步没成功 | 确认 `--template` 与第 ② 步一致 |
| 第 ④ 步 `tx_packets:0` | 第 ③ 步 `clear_stats` 后没真正发包，或 trex-api 被重启丢基线 | 不要中途重启 trex-api；重跑 ③④ |
| 第 ④ 步 `tx_packets:0` 但设备实际在发包 | `t-rex-64` 的 `get_stats` 返回的端口计数以**物理端口号 int** 为 key，但代码用逻辑名 `"2_3"` 查；旧实现 fallback `int("2_3")` 在 Python 3.6+ 把下划线当数字分隔符，返回 `23` 而非报错，于是读到不存在的端口 23，静默返回 0 | 已修复：`stats_parser` 改为先 `resolve_port("2_3") -> 2` 再查 stats；升级 `trex-api` 后重跑 ③④ |
| 第 ⑥ 步 `RESOURCE_CONFLICT` | 没先 stop | 先执行第 ⑤ 步 |
| 本机 CLI 连不上 | 没设 `TREX_API_URL` | `export TREX_API_URL=http://<IP_ADDRESS>:8000` |
| 本机 curl 走了代理 | 设过 `http_proxy` | 加 `--noproxy '*'` 或 `unset http_proxy https_proxy` |
| 重复执行报端口占用 | 上次没 stop 干净 | 跑一遍第 ⑤ 步，或重启 trex-stl（会丢计数基线） |

---

## 10. 附：进阶变体

把第 ② 步换成下面任一，其余步骤的 `template` 名相应替换即可：

**continuous 持续流**（不指定 count，靠第 ⑤ 步 stop 停）：

```bash
tg tg_apply_traffic_template --template cont-demo --tx-port 2_1 --rx-port 2_2 \
  --ip-version ipv4 --l4-protocol udp --l4-sport 1234 --l4-dport 5678 \
  --traffic-mode continuous --rate 100pps
```

**IPv6 流**（必须给 src_ip/dst_ip，第 ① 步也要用 IPv6 网关触发 ND）：

```bash
tg tg_apply_traffic_template --template ipv6-demo --tx-port 2_1 --rx-port 2_2 \
  --ip-version ipv6 --l4-protocol udp --l4-sport 1234 --l4-dport 5678 \
  --traffic-mode count --rate 100pps --count 500 \
  --src-ip 2001:db8::1 --dst-ip 2001:db8::2
```

> IPv6 的网关 MAC 不走 ARP，走 TRex 的 `ServiceIPv6ND`（发 NS 收 NA），
> 第 ① 步的 `neighbor_protocol` 会是 `"nd"`。见 `api_client.py:109`。
```
