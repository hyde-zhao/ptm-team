# NGFW 策略路由因子组

## 因子组总览

| group_id | group_name | 主要因子 | 推荐设计方法 | 覆盖目标 |
|---|---|---|---|---|
| L3_EGRESS_NEXT_HOP | 下一跳模式三层转发接口覆盖 | FAC-L3-EGRESS-MODE, FAC-L3-NH-IF-TYPE, FAC-L3-IF-CAPABILITY, FAC-L3-REACHABILITY, FAC-L3-EXPECTED-FWD-PATH | C-Combination, S-State | 下一跳模式下每类有效接口至少覆盖一次，并验证不可达/恢复代表场景 |
| L3_EGRESS_OUT_INTERFACE | 出接口模式三层转发接口覆盖 | FAC-L3-EGRESS-MODE, FAC-L3-OUTIF-TYPE, FAC-L3-IF-CAPABILITY, FAC-L3-REACHABILITY, FAC-L3-EXPECTED-FWD-PATH | C-Combination, S-State | 隧道口和 PPPoE 出接口均覆盖，验证出接口模式转发结果 |
| L3_EGRESS_FAILOVER | 出口不可达和故障恢复 | FAC-L3-EGRESS-MODE, FAC-L3-REACHABILITY, FAC-L3-FAIL-DETECT-METHOD, FAC-L3-EXPECTED-FWD-PATH | S-State, P-Parameter | 可达、不可达、恢复，以及 IP-LINK / 接口 Down 失效方式 |
| TRAFFIC_MATCHING | 策略路由业务流量匹配性 | FAC-TRAFFIC-LAYER-TYPE, FAC-TRAFFIC-IP-MATCH, FAC-TRAFFIC-SERVICE-MATCH, FAC-TRAFFIC-APP-MATCH, FAC-EXPECTED-MATCH-RESULT | P-Parameter, C-Combination | 功能正向流量命中、功能反向流量不命中 |
| CONFIG_FIELD_VALIDITY | 策略路由配置字段合法性 | FAC-CONFIG-NAME, FAC-PR-RULE-SRC-IP, FAC-PR-RULE-DST-IP, FAC-PR-RULE-PROTOCOL, FAC-PR-RULE-SRC-PORT, FAC-PR-RULE-DST-PORT, FAC-L3-NH-WEIGHT | D-Data | 配置字段 accepted/rejected 样本覆盖，accepted 样本可作为功能前置 |
| POLICY_RULE_ORDER | 策略路由重叠规则命中判定 | FAC-PR-RULE-ORDER, FAC-PR-RULE-SCOPE, FAC-PR-RULE-STATE, FAC-PR-EXPECTED-HIT-RULE | P-Parameter | 规则顺序、范围、启用状态与预期命中规则 |
| DFX_COUNTER | 命中计数展示和清零 | FAC-COUNTER-TARGET, FAC-COUNTER-ACTION, FAC-COUNTER-DELTA | D-Data | 查看、单条清零、全部清零、清零后重新增加 |
| DFX_LOG_AUDIT | 操作日志审计 | FAC-LOG-OP-TYPE, FAC-LOG-FIELD-COMPLETENESS | D-Data | 新增、修改、启用、禁用、删除及日志字段完整性 |
| HA_POLICY_ROUTE | 策略路由HA同步与切换 | FAC-HA-ROLE, FAC-HA-SYNC-STATE, FAC-HA-FAILOVER-ACTION, FAC-HA-EXPECTED-ACTIVE-DEVICE | S-State | 主备同步、主故障切换、恢复与回切 |

## 出口模式对比

| 维度 | 下一跳模式 | 出接口模式 |
|---|---|---|
| 固定因子 | `FAC-L3-EGRESS-MODE=next-hop` | `FAC-L3-EGRESS-MODE=out-interface` |
| 接口类型因子 | `FAC-L3-NH-IF-TYPE` | `FAC-L3-OUTIF-TYPE` |
| 有效接口类型 | physical, sub-interface, aggregate, bvi, tunnel | tunnel, pppoe |
| 主要 oracle | policy-next-hop | policy-out-interface |
| 典型异常 | 下一跳不可达、IP-LINK 失败、接口 Down | 出接口 Down、隧道/PPPoE 状态异常 |
| 禁止混用 | 禁止 `FAC-L3-OUTIF-TYPE` | 禁止 `FAC-L3-NH-IF-TYPE` |

## 业务流量样本分组

| 类型 | sample_id | 预期 | 说明 |
|---|---|---|---|
| 正向 | TRAFFIC_L2_NON_IP_MATCH | hit | 二层非 IP 流命中 |
| 正向 | TRAFFIC_IP_MATCH | hit | 源/目的 IP 均匹配 |
| 正向 | TRAFFIC_TCP_MATCH | hit | TCP 服务和端口均匹配 |
| 正向 | TRAFFIC_UDP_MATCH | hit | UDP 服务和端口均匹配 |
| 正向 | TRAFFIC_FTP_MATCH | hit | FTP 应用匹配 |
| 正向 | TRAFFIC_HTTP_MATCH | hit | HTTP 应用匹配 |
| 正向 | TRAFFIC_OTHER_APP_MATCH | hit | 其他应用匹配 |
| 反向 | TRAFFIC_SRC_IP_MISMATCH | miss | 源 IP 不匹配 |
| 反向 | TRAFFIC_DST_IP_MISMATCH | miss | 目的 IP 不匹配 |
| 反向 | TRAFFIC_SERVICE_TYPE_MISMATCH | miss | 服务类型不匹配 |
| 反向 | TRAFFIC_SRC_PORT_MISMATCH | miss | 源端口不匹配 |
| 反向 | TRAFFIC_DST_PORT_MISMATCH | miss | 目的端口不匹配 |
| 反向 | TRAFFIC_APP_MISMATCH | miss | 应用不匹配 |

## 配置与功能样本边界

| 场景 | 可用样本 | 禁止样本 | 原因 |
|---|---|---|---|
| 配置字段正向 | `FAC-PR-RULE-*` / `FAC-CONFIG-*` / 其他配置对象因子的 accepted config samples | `FAC-PKT-*`、negative_function | 报文运行时输入不是配置字段 |
| 配置字段反向 | `FAC-PR-RULE-*` / `FAC-CONFIG-*` / 其他配置对象因子的 rejected config samples | `FAC-PKT-*`、positive_function | 只验证配置下发拒绝 |
| 功能正向 | positive_function + accepted precondition | rejected config samples | 非法配置无法作为功能前置 |
| 功能反向 | negative_function + accepted precondition | rejected config samples | 反向流量必须可执行 |
| 故障恢复 | reachability / fail-detect / expected path | 配置非法样本 | 故障场景验证状态变化，不验证字段合法性 |

## 配置字段与报文字段分工

| 需求问题 | 配置字段因子 | 报文运行时因子 | 处理规则 |
|---|---|---|---|
| 源 IP 字段是否合法 | FAC-PR-RULE-SRC-IP | FAC-PKT-SRC-IP | 配置 accepted/rejected 查规则字段；流量 match/mismatch 查报文字段 |
| 目的 IP 字段是否合法 | FAC-PR-RULE-DST-IP | FAC-PKT-DST-IP | 配置 accepted/rejected 查规则字段；流量 match/mismatch 查报文字段 |
| 服务协议是否合法 | FAC-PR-RULE-PROTOCOL | FAC-PKT-PROTOCOL | 配置非法协议不得进入功能前置 |
| 源端口字段是否合法 | FAC-PR-RULE-SRC-PORT | FAC-PKT-SRC-PORT | 0/65536 属于规则配置拒绝样本，不属于报文反向流量 |
| 目的端口字段是否合法 | FAC-PR-RULE-DST-PORT | FAC-PKT-DST-PORT | 0/65536 属于规则配置拒绝样本，不属于报文反向流量 |
