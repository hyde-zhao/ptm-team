# TGFW IPv4路由 — 因子提取与确认计划

> 来源: `_inbox/TGFW_V60R001C00 IPv4路由特性测试用例.xlsx`
> 候选文件: `_proposals/from-tgfw-ipv4-route-candidates.yaml`
> 日期: 2026-06-03
> 最后更新: 2026-06-04

---

## 总览

从两个 Excel 中提取了 44 个候选因子。工作分两条线：

- **线 A：策略路由因子整理** — 将发布区 `ngfw-policy-routing` 的 38 个因子重新分类，策略专属的保留，公共的迁移到对应领域库，缺失的补充人读层。
- **线 B：路由专属因子提取** — 从候选因子中逐轮确认，落盘到 `ngfw-ipv4-route`。

---

## 当前库结构

```
resource/factor-libraries/
├── README.md                       # 研究区总说明
├── STANDARDS.md                    # 因子建模标准
│
├── _inbox/                         # 原始 Excel 材料
├── _templates/                     # 因子库标准模板
├── _proposals/                     # 候选因子提案
│
├── ngfw-policy-routing/            # 38 因子 → 待重新分类
├── common-network/                 # 2 因子
├── ngfw-ipv4-route/                # 3 因子
├── ngfw-interface/                 # 1 因子
└── ngfw-traffic/                   # 9 因子
```

---

## 线 A：策略路由因子整理（当前）

### A.1 现状

`ngfw-policy-routing` 从发布区同步了 38 个因子，但其中只有 13 个是策略路由真正专属的，其余 25 个属于其他领域：

### A.2 重新分配方案

#### 保留在 `ngfw-policy-routing`（13 个 — 策略路由专属）

| 因子 | 说明 |
|------|------|
| `FAC-PR-RULE-SRC-IP` | 规则源IP匹配条件 |
| `FAC-PR-RULE-DST-IP` | 规则目的IP匹配条件 |
| `FAC-PR-RULE-PROTOCOL` | 规则服务协议 |
| `FAC-PR-RULE-SRC-PORT` | 规则源端口 |
| `FAC-PR-RULE-DST-PORT` | 规则目的端口 |
| `FAC-PR-RULE-STATE` | 规则启用/禁用/删除 |
| `FAC-PR-RULE-ORDER` | 规则匹配顺序 |
| `FAC-PR-RULE-SCOPE` | 规则匹配范围 |
| `FAC-PR-EXPECTED-HIT-RULE` | 预期命中规则 oracle |
| `FAC-TRAFFIC-LAYER-TYPE` | 策略匹配流量层级 |
| `FAC-TRAFFIC-IP-MATCH` | 策略匹配 IP 匹配状态 |
| `FAC-TRAFFIC-SERVICE-MATCH` | 策略匹配服务匹配状态 |
| `FAC-TRAFFIC-APP-MATCH` | 策略匹配应用匹配状态 |
| `FAC-EXPECTED-MATCH-RESULT` | 策略命中 oracle |

#### 迁移到 `ngfw-traffic`（7 个 — 报文构造因子）

| 因子 | 说明 |
|------|------|
| `FAC-PKT-SRC-IP` | 报文源IP |
| `FAC-PKT-DST-IP` | 报文目的IP |
| `FAC-PKT-PROTOCOL` | 报文协议 |
| `FAC-PKT-SRC-PORT` | 报文源端口 |
| `FAC-PKT-DST-PORT` | 报文目的端口 |
| `FAC-PKT-APP-ID` | 报文应用标识 |
| `FAC-DOMAIN-RESOLUTION-STATE` | 域名解析状态 |

#### 迁移到 `ngfw-ipv4-route`（7 个 — L3 出口因子）

| 因子 | 说明 |
|------|------|
| `FAC-L3-EGRESS-MODE` | 已有 |
| `FAC-L3-NH-IF-TYPE` | 下一跳关联接口类型 |
| `FAC-L3-OUTIF-TYPE` | 出接口接口类型 |
| `FAC-L3-IF-CAPABILITY` | 三层转发接口能力 |
| `FAC-L3-REACHABILITY` | 三层出口可达性 |
| `FAC-L3-FAIL-DETECT-METHOD` | 失效检测方式 |
| `FAC-L3-EXPECTED-FWD-PATH` | 预期转发路径 |
| `FAC-L3-NH-WEIGHT` | 下一跳权重（与 `FAC-RT-WEIGHT` 合并） |

#### 迁移到 `common-network`（1 个 — 通用配置）

| 因子 | 说明 |
|------|------|
| `FAC-CONFIG-NAME` | 配置对象名称 |

#### 新建 `ngfw-ha`（4 个 — HA 领域）

| 因子 | 说明 |
|------|------|
| `FAC-HA-ROLE` | HA 角色 |
| `FAC-HA-SYNC-STATE` | HA 配置同步状态 |
| `FAC-HA-FAILOVER-ACTION` | HA 切换动作 |
| `FAC-HA-EXPECTED-ACTIVE-DEVICE` | 预期承载设备 oracle |

#### 新建 `ngfw-dfx`（5 个 — DFX 领域）

| 因子 | 说明 |
|------|------|
| `FAC-COUNTER-TARGET` | 命中计数操作对象 |
| `FAC-COUNTER-ACTION` | 命中计数操作 |
| `FAC-COUNTER-DELTA` | 命中计数变化 oracle |
| `FAC-LOG-OP-TYPE` | 日志操作类型 |
| `FAC-LOG-FIELD-COMPLETENESS` | 日志字段完整性 oracle |

### A.3 迁移后的库结构

| 库 | 因子数 | 说明 |
|----|--------|------|
| `ngfw-policy-routing` | 38 → **13** | 只保留策略路由专属 |
| `ngfw-traffic` | 9 → **16** | +7 报文构造 |
| `ngfw-ipv4-route` | 3 → **11** | +8 L3 出口（含合并 WEIGHT） |
| `common-network` | 2 → **3** | +1 配置名称 |
| `ngfw-ha` 🆕 | **4** | HA 独立领域 |
| `ngfw-dfx` 🆕 | **5** | DFX 独立领域 |

### A.4 配套迁移

| 源内容 | 去向 | 说明 |
|--------|------|------|
| `traffic_samples` | `ngfw-traffic` | 流量样本属于报文构造 |
| `capability_matrices` | `ngfw-ipv4-route` | 出口接口能力矩阵 |
| `constraints` (出口相关) | `ngfw-ipv4-route` | C-L3-EGRESS-* 系列 |
| `constraints` (配置/流量职责) | 各库 | 按 owner_object 分发 |
| `factor_groups` (出口) | `ngfw-ipv4-route` | L3_EGRESS_* 系列 |
| `factor_groups` (流量) | `ngfw-traffic` | TRAFFIC_MATCHING |
| `factor_groups` (配置) | `ngfw-policy-routing` | CONFIG_FIELD_VALIDITY 等 |

### A.5 执行步骤

```
1. 新建 ngfw-ha, ngfw-dfx 目录
2. 补充缺失的人读层（当前 9 个配置因子有人读层，其余 29 个仅同步了原始 YAML）
3. 从 ngfw-policy-routing 中删除已迁移的因子
4. 将迁移因子追加到目标库
5. 迁移配套的 constraints, factor_groups, traffic_samples, capability_matrices
6. 更新 ngfw-policy-routing 的库级约束和因子组
7. 验证：每个库自包含，可独立消费
```

---

## 线 B：路由专属因子提取

> 策略路由因子整理完成后，继续以下轮次。

### 第 3 轮：数值范围类（3 个）— 精简后

| # | 因子 ID | 名称 | 决策 |
|---|---------|------|------|
| 3.1 | `FAC-RT-PRIORITY` | 路由优先级 | `range` 1~255，无效 0/256 |
| 3.2 | `FAC-RT-QUERY-PAGE` | 分页查询参数 | 拆为 page + size 两个 or 合并？ |
| 3.3 | `FAC-RT-CAPACITY` | 路由容量 | 规格未定，建模为 range 但不物化 |

> `FAC-RT-WEIGHT` 已与 `FAC-L3-NH-WEIGHT` 合并，移到线 A 处理。`FAC-RT-DEFAULT-VALUE` 降级为 notes。

### 第 4 轮：配置管理（4 个）

| # | 因子 ID | 核心决策 |
|---|---------|---------|
| 4.1 | `FAC-RT-CRUD-OP` | 操作类型枚举 |
| 4.2 | `FAC-RT-MODIFY-FIELD` | 可修改字段枚举 |
| 4.3 | `FAC-RT-ROUTE-UNIQUENESS` | 独立 constraint or 组合约束？ |
| 4.4 | `FAC-RT-CONFIG-PERSIST` | 存库/升级/导入导出合并 |

> `FAC-RT-OPLOG` 由 `ngfw-dfx` 的 `FAC-LOG-OP-TYPE` 复用。

### 第 5 轮：接口状态（2 个）

| # | 因子 ID | 核心决策 |
|---|---------|---------|
| 5.1 | `FAC-RT-INTERFACE-STATE` | UP/Down/切换 state |
| 5.2 | `FAC-RT-SAME-SUBNET-IP-CHANGE` | 独立因子 or INTERFACE-STATE 子场景？ |

### 第 6 轮：FIB 状态机（4 个）

| # | 因子 ID | 核心决策 |
|---|---------|---------|
| 6.1 | `FAC-RT-NEXT-HOP-MATCH` | condition 类型，5 种匹配状态 |
| 6.2 | `FAC-RT-FIB-PATH` | process 类型，4 条路径 |
| 6.3 | `FAC-RT-FIB-DELETE-COND` | 5 种失效触发 |
| 6.4 | `FAC-RT-FIB-INTERFACE-SWITCH` | 3 种切换场景 |

### 第 7 轮：转发 + ECMP（11 个）

- 路由转发 7 个: `FWD-ROUTE-TYPE`, `LONGEST-MATCH`, `FLOAT-MODE`, `RELIABILITY-OP`, `ARP`, `HA`, `IPV6-ISOLATION`
- ECMP 4 个: `ECMP-ROUTE-TYPE`, `LOAD-BALANCE`, `LINK-CHANGE`, `ROUTE-SWITCH`

### 第 8 轮：收尾（4 个）

- `DIRECT-MULTI-IP`, `DIRECT-MEMBER-STATE`, `DIRECT-LOGIC-INTF-LIFECYCLE`, `SINGLE-ARM-INTF-PAIR`

### 第 9 轮：跨因子整理

- [ ] 全部去重确认
- [ ] factor-groups 划分
- [ ] 库级 constraints 补全
- [ ] 人读文档 (factor-library.md)
- [ ] 变更记录 (factor-change-log.md)
- [ ] `_proposals/` 状态更新

---

## 进度追踪

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 A | IP 地址/网段 (5 因子) | ✅ 完成 |
| 阶段 B | 流量因子体系 (11 因子) | ✅ 完成 |
| 阶段 C | 规范增强 | ✅ 完成 |
| **线 A** | **策略路由因子整理 (38→13)** | **⬜ 当前** |
| 线 A.1 | 新建 ngfw-ha, ngfw-dfx | ⬜ |
| 线 A.2 | 补人读层 + 迁移因子 | ⬜ |
| 线 A.3 | 迁移配套 constraints/groups | ⬜ |
| 线 B.3 | 数值范围 (3 因子) | ⬜ |
| 线 B.4 | 配置管理 (4 因子) | ⬜ |
| 线 B.5 | 接口状态 (2 因子) | ⬜ |
| 线 B.6 | FIB 状态机 (4 因子) | ⬜ |
| 线 B.7 | 转发+ECMP (11 因子) | ⬜ |
| 线 B.8 | 收尾 (4 因子) | ⬜ |
| 线 B.9 | 跨因子整理 | ⬜ |

---

## 候选因子变更记录

| 原候选 | 变更类型 | 原因 |
|--------|---------|------|
| `FAC-RT-DIRECT-INTERFACE-IP` | 删除 | 由 `FAC-IF-IPV4-ADDRESS` 替代 |
| `FAC-RT-FWD-ABNORMAL-SIP` | 删除 | 由 `FAC-PKT-L3-ABNORMAL-SIP` 替代 |
| `FAC-RT-FWD-ABNORMAL-IP-HEADER` | 删除 | 拆为 `FAC-PKT-L3-TTL` + `FAC-PKT-L3-CHECKSUM` |
| `FAC-RT-INTERFACE-TYPE` | 删除 | 由 `FAC-L3-NH-IF-TYPE` + `FAC-L3-OUTIF-TYPE` 替代 |
| `FAC-RT-FWD-DMAC-MATCH` | 删除 | 由 `FAC-PKT-L2-DMAC` 覆盖 |
| `FAC-RT-FWD-VLAN-ENCAP` | 删除 | 由 `FAC-PKT-L2-VLAN` 覆盖 |
| `FAC-RT-ECMP-RELIABILITY-OP` | 删除 | 与 `FWD-RELIABILITY-OP` 重叠 |
| `FAC-RT-ECMP-SWITCH-TIME` | 删除 | 性能指标，不建模 |
| `FAC-RT-PERFORMANCE` | 删除 | 纯 oracle，无样本定义 |
| `FAC-RT-PRIORITY-ECMP` | 删除 | 合并到 PRIORITY |
| `FAC-RT-SINGLE-ARM-POLICY` | 删除 | 策略耦合，非路由因子 |
| `FAC-RT-DEFAULT-VALUE` | 降级 | 作为 WEIGHT/PRIORITY 的 notes |
| `FAC-RT-WEIGHT` | 合并 | 与 `FAC-L3-NH-WEIGHT` 合并 |
| `FAC-RT-OPLOG` | 复用 | 由 `ngfw-dfx` 的 LOG 因子覆盖 |
