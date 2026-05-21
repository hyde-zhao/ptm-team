# NGFW 策略路由因子库

## 定位

本库归档 NGFW 策略路由领域的公共测试因子，供 `ptm-tde` 及未来其他 Agent / Skill 复用。机器可读主库为 `factor-library.yaml`；本文档用于人工评审、横向对比和维护决策。

## 本版修正

| 修正项 | 旧口径 | 新口径 | 原因 |
|---|---|---|---|
| 三层出口因子 | 粗粒度 `FAC-NH-TYPE` 或 `FAC-PR-L3-EGRESS-MODE` | `FAC-L3-EGRESS-MODE` + `FAC-L3-NH-IF-TYPE` + `FAC-L3-OUTIF-TYPE` | 区分出口选择模式、下一跳关联接口、出接口接口类型，避免组合语义混淆 |
| 业务流量因子 | 粗粒度 `FAC-FLOW-PROFILE` | `TRAFFIC_MATCHING` 因子组 | 将流量层级、IP 匹配、服务匹配、应用匹配和预期命中结果拆开，支持功能正向/反向样本 |
| 配置非法 vs 功能反向 | 混用 valid/invalid | 分离 `rejected_config_samples` 与 `negative_function` | 非法配置不能作为功能用例前置；功能反向流量是可执行但预期不命中的输入 |
| 报文输入 vs 规则配置 | `FAC-PKT-*` 同时承载功能流量和配置非法样本 | `FAC-PKT-*` 只承载运行时报文输入；`FAC-PR-RULE-*` 承载配置字段合法性 | 防止 `accepted config samples = n/a` 被误判为缺失配置覆盖 |
| 接口能力 vs 真实端口 | 把 `DUT.port1` / `TG.port1` 当成接口因子值 | 接口类型和接口能力可作为因子；真实端口和 link 实例只在 `topology_bindings` 中出现 | 防止项目拓扑实例污染公共因子库 |
| 项目归档 | 项目内主库 | 公共 resource 主库 + 项目 lock/binding/proposal | 公共库可跨项目复用，项目内只记录消费结果 |

## 因子总览

| factor_id | 因子名称 | kind | role | owner_object | domain_model | 取值摘要 | 下游方法 | 用途 |
|---|---|---|---|---|---|---|---|---|
| FAC-L3-EGRESS-MODE | 三层转发出口选择模式 | control | driver | OBJ-PR-EGRESS | enum | next-hop / out-interface | P-Parameter, C-Combination | 区分下一跳模式和出接口模式 |
| FAC-L3-NH-IF-TYPE | 下一跳关联接口类型 | data | driver | OBJ-PR-EGRESS | enum | physical / sub-interface / aggregate / bvi / tunnel | C-Combination | 下一跳模式接口覆盖 |
| FAC-L3-OUTIF-TYPE | 出接口接口类型 | data | driver | OBJ-PR-EGRESS | enum | tunnel / pppoe | C-Combination | 出接口模式接口覆盖 |
| FAC-L3-IF-CAPABILITY | 三层转发接口能力 | constraint | constraint | OBJ-PR-EGRESS | enum | l3-capable / not-l3-capable | D-Data, C-Combination | 判断接口是否支持三层转发 |
| FAC-L3-REACHABILITY | 三层出口可达性 | state | driver | OBJ-PR-EGRESS | state | reachable / unreachable / recovered | S-State, P-Parameter | 出口可达、失效、恢复 |
| FAC-L3-FAIL-DETECT-METHOD | 失效检测方式 | condition | driver | OBJ-PR-EGRESS | enum | ip-link / interface-down | P-Parameter, S-State | 不可达场景的失效触发方式 |
| FAC-L3-EXPECTED-FWD-PATH | 预期转发路径 | oracle | oracle | OBJ-PR-EGRESS | enum | policy-next-hop / policy-out-interface / fallback-route / forward-fail | oracle-design | 转发结果判定 |
| FAC-L3-NH-WEIGHT | 下一跳权重 | data | driver | OBJ-PR-EGRESS | range | int[1,255] | D-Data, C-Combination | 权重合法性与功能前置 |
| FAC-CONFIG-NAME | 配置对象名称 | data | driver | OBJ-GENERIC-CONFIG | string_pattern | 长度 1..31，指定字符集和正则 | D-Data | 名称字段合法性 |
| FAC-PR-RULE-SRC-IP | 策略路由规则源IPv4配置 | data | driver | OBJ-PR-RULE | ip_address | valid host / valid subnet / invalid IPv4 | D-Data | 源地址配置合法性 |
| FAC-PR-RULE-DST-IP | 策略路由规则目的IPv4配置 | data | driver | OBJ-PR-RULE | ip_address | valid host / valid subnet / invalid IPv4 | D-Data | 目的地址配置合法性 |
| FAC-PR-RULE-PROTOCOL | 策略路由规则服务协议配置 | data | driver | OBJ-PR-RULE | enum | ip / tcp / udp / icmp / application | D-Data | 服务协议配置合法性 |
| FAC-PR-RULE-SRC-PORT | 策略路由规则源端口配置 | data | driver | OBJ-PR-RULE | range | int[1,65535] | D-Data | 源端口配置合法性 |
| FAC-PR-RULE-DST-PORT | 策略路由规则目的端口配置 | data | driver | OBJ-PR-RULE | range | int[1,65535] | D-Data | 目的端口配置合法性 |
| FAC-TRAFFIC-LAYER-TYPE | 流量层级类型 | data | driver | OBJ-PR-TRAFFIC | enum | l2-non-ip / ip / tcp / udp / application | C-Combination | 业务流量大类 |
| FAC-TRAFFIC-IP-MATCH | IP匹配状态 | data | driver | OBJ-PR-TRAFFIC | enum | src-dst-match / src-ip-mismatch / dst-ip-mismatch / both-ip-mismatch | P-Parameter, C-Combination | 地址正向/反向匹配 |
| FAC-TRAFFIC-SERVICE-MATCH | 服务匹配状态 | data | driver | OBJ-PR-TRAFFIC | enum | service-match / service-type-mismatch / src-port-mismatch / dst-port-mismatch | P-Parameter, C-Combination | 协议端口正向/反向匹配 |
| FAC-TRAFFIC-APP-MATCH | 应用匹配状态 | data | driver | OBJ-PR-TRAFFIC | enum | ftp-match / http-match / other-app-match / app-mismatch / app-unrecognized | P-Parameter, C-Combination | 应用识别正向/反向匹配 |
| FAC-EXPECTED-MATCH-RESULT | 预期命中结果 | oracle | oracle | OBJ-PR-TRAFFIC | enum | hit / miss | oracle-design | 策略命中结果判定 |
| FAC-PKT-SRC-IP | 报文源IPv4 | data | driver | OBJ-PR-TRAFFIC | ip_address | 匹配 / 不匹配，config_test 不适用 | P-Parameter, C-Combination | 源地址流量样本物化 |
| FAC-PKT-DST-IP | 报文目的IPv4 | data | driver | OBJ-PR-TRAFFIC | ip_address | 匹配 / 不匹配，config_test 不适用 | P-Parameter, C-Combination | 目的地址流量样本物化 |
| FAC-PKT-PROTOCOL | 报文协议 | data | driver | OBJ-PR-TRAFFIC | enum | ip / tcp / udp / icmp / ftp / http / other-app | C-Combination | 协议和应用样本物化 |
| FAC-PKT-SRC-PORT | 报文源端口 | data | driver | OBJ-PR-TRAFFIC | range | 匹配 / 不匹配，config_test 不适用 | P-Parameter, C-Combination | 源端口流量样本物化 |
| FAC-PKT-DST-PORT | 报文目的端口 | data | driver | OBJ-PR-TRAFFIC | range | 匹配 / 不匹配，config_test 不适用 | P-Parameter, C-Combination | 目的端口流量样本物化 |
| FAC-PKT-APP-ID | 报文应用标识 | data | driver | OBJ-PR-TRAFFIC | enum | ftp / http / other-app / app-mismatch / app-unrecognized | P-Parameter, C-Combination | 应用样本物化 |
| FAC-DOMAIN-RESOLUTION-STATE | 域名解析状态 | state | driver | OBJ-PR-TRAFFIC | enum | resolved / unresolved / resolved-to-mismatch-ip | S-State | 域名对象状态 |
| FAC-PR-RULE-STATE | 策略路由规则状态 | state | driver | OBJ-PR-RULE | state | enabled / disabled / modified / deleted | S-State | 规则生命周期 |
| FAC-PR-RULE-ORDER | 策略路由规则顺序 | control | driver | OBJ-PR-RULE | enum | specific-before-general / general-before-specific / moved-order / default-insert-position | P-Parameter, C-Combination | 重叠规则优先级 |
| FAC-PR-RULE-SCOPE | 策略路由规则匹配范围 | control | driver | OBJ-PR-RULE | enum | specific / general / overlap | P-Parameter | 重叠范围建模 |
| FAC-PR-EXPECTED-HIT-RULE | 预期命中规则 | oracle | oracle | OBJ-PR-RULE | enum | rule-a / rule-b / none | oracle-design | 命中规则判定 |
| FAC-COUNTER-TARGET | 命中计数操作对象 | control | driver | OBJ-PR-DFX | enum | single-rule / all-rules | D-Data | 计数操作对象 |
| FAC-COUNTER-ACTION | 命中计数操作 | control | driver | OBJ-PR-DFX | enum | query / clear-single / clear-all | D-Data | 计数查看和清零动作 |
| FAC-COUNTER-DELTA | 命中计数变化 | oracle | oracle | OBJ-PR-DFX | enum | increase / no-change / single-cleared / all-cleared / re-increase | oracle-design | 计数结果判定 |
| FAC-LOG-OP-TYPE | 日志操作类型 | control | driver | OBJ-PR-DFX | enum | create / modify / enable / disable / delete | D-Data | 操作日志触发动作 |
| FAC-LOG-FIELD-COMPLETENESS | 日志字段完整性 | oracle | oracle | OBJ-PR-DFX | enum | complete / missing-* | oracle-design | 日志字段判定 |
| FAC-HA-ROLE | HA角色 | state | driver | OBJ-PR-HA | enum | primary / standby | S-State | 主备角色 |
| FAC-HA-SYNC-STATE | HA配置同步状态 | state | driver | OBJ-PR-HA | enum | synced / not-synced / partially-synced | S-State | 同步状态 |
| FAC-HA-FAILOVER-ACTION | HA切换动作 | control | driver | OBJ-PR-HA | enum | trigger-failover / recover-primary / fallback | S-State | HA切换动作 |
| FAC-HA-EXPECTED-ACTIVE-DEVICE | 预期承载设备 | oracle | oracle | OBJ-PR-HA | enum | primary-active / standby-active / unchanged | oracle-design | HA承载结果 |

## 样本对比

### 配置字段样本

| factor_id | accepted config samples | rejected config samples | function precondition | 说明 |
|---|---|---|---|---|
| FAC-L3-NH-WEIGHT | WEIGHT_MIN, WEIGHT_MAX, WEIGHT_NOMINAL | WEIGHT_BELOW_MIN, WEIGHT_ABOVE_MAX | WEIGHT_NOMINAL | 0/256 只能验证配置拒绝，不进入功能前置 |
| FAC-CONFIG-NAME | NAME_MIN_LEN, NAME_MAX_LEN, NAME_MIXED_CHARSET | NAME_EMPTY, NAME_TOO_LONG, NAME_INVALID_CHAR | NAME_MIXED_CHARSET | 功能用例优先使用混合字符合法名称 |
| FAC-PR-RULE-SRC-IP | RULE_SRC_IP_VALID_HOST, RULE_SRC_IP_VALID_SUBNET | RULE_SRC_IP_INVALID | RULE_SRC_IP_VALID_HOST, RULE_SRC_IP_VALID_SUBNET | 规则源地址配置合法性；报文源地址匹配由 `FAC-PKT-SRC-IP` 承载 |
| FAC-PR-RULE-DST-IP | RULE_DST_IP_VALID_HOST, RULE_DST_IP_VALID_SUBNET | RULE_DST_IP_INVALID | RULE_DST_IP_VALID_HOST, RULE_DST_IP_VALID_SUBNET | 规则目的地址配置合法性；报文目的地址匹配由 `FAC-PKT-DST-IP` 承载 |
| FAC-PR-RULE-PROTOCOL | RULE_PROTOCOL_IP, RULE_PROTOCOL_TCP, RULE_PROTOCOL_UDP | RULE_PROTOCOL_INVALID | RULE_PROTOCOL_IP, RULE_PROTOCOL_TCP, RULE_PROTOCOL_UDP | 协议非法值只用于配置拒绝 |
| FAC-PR-RULE-SRC-PORT | RULE_SRC_PORT_MIN, RULE_SRC_PORT_MAX, RULE_SRC_PORT_NOMINAL | RULE_SRC_PORT_BELOW_MIN, RULE_SRC_PORT_ABOVE_MAX | RULE_SRC_PORT_NOMINAL | 0/65536 只用于规则源端口配置拒绝 |
| FAC-PR-RULE-DST-PORT | RULE_DST_PORT_MIN, RULE_DST_PORT_MAX, RULE_DST_PORT_NOMINAL | RULE_DST_PORT_BELOW_MIN, RULE_DST_PORT_ABOVE_MAX | RULE_DST_PORT_NOMINAL | 0/65536 只用于规则目的端口配置拒绝 |

### 运行时报文样本

| factor_id | config_test | positive function samples | negative function samples | 说明 |
|---|---|---|---|---|
| FAC-PKT-SRC-IP | not_applicable | SRC_IP_MATCH | SRC_IP_MISMATCH | 报文源 IP 是运行时输入，不生成配置合法性用例 |
| FAC-PKT-DST-IP | not_applicable | DST_IP_MATCH | DST_IP_MISMATCH | 报文目的 IP 是运行时输入，不生成配置合法性用例 |
| FAC-PKT-SRC-PORT | not_applicable | SRC_PORT_MATCH | SRC_PORT_MISMATCH | 报文源端口用于功能流量构造，非法端口归规则配置字段验证 |
| FAC-PKT-DST-PORT | not_applicable | DST_PORT_MATCH | DST_PORT_MISMATCH | 报文目的端口用于功能流量构造，非法端口归规则配置字段验证 |

### 业务流量样本

| sample_id | class | layer | IP match | service/app match | expected | materialization |
|---|---|---|---|---|---|---|
| TRAFFIC_L2_NON_IP_MATCH | positive_function | l2-non-ip | n/a | n/a | hit | `frame_type=l2_non_ip` |
| TRAFFIC_IP_MATCH | positive_function | ip | src-dst-match | n/a | hit | 从规则源/目的 IP 取有效成员 |
| TRAFFIC_TCP_MATCH | positive_function | tcp | src-dst-match | service-match | hit | TCP + 规则服务端口有效成员 |
| TRAFFIC_UDP_MATCH | positive_function | udp | src-dst-match | service-match | hit | UDP + 规则服务端口有效成员 |
| TRAFFIC_FTP_MATCH | positive_function | application | src-dst-match | ftp-match | hit | `application=ftp` |
| TRAFFIC_HTTP_MATCH | positive_function | application | src-dst-match | http-match | hit | `application=http` |
| TRAFFIC_OTHER_APP_MATCH | positive_function | application | src-dst-match | other-app-match | hit | 从规则应用对象取其他应用 |
| TRAFFIC_SRC_IP_MISMATCH | negative_function | ip | src-ip-mismatch | service-match | miss | `src_ip=not_in(rule.src_ip)` |
| TRAFFIC_DST_IP_MISMATCH | negative_function | ip | dst-ip-mismatch | service-match | miss | `dst_ip=not_in(rule.dst_ip)` |
| TRAFFIC_SERVICE_TYPE_MISMATCH | negative_function | ip | src-dst-match | service-type-mismatch | miss | `protocol=not_in(rule.service.protocol)` |
| TRAFFIC_SRC_PORT_MISMATCH | negative_function | tcp | src-dst-match | src-port-mismatch | miss | `src_port=not_in(rule.service.src_port)` |
| TRAFFIC_DST_PORT_MISMATCH | negative_function | tcp | src-dst-match | dst-port-mismatch | miss | `dst_port=not_in(rule.service.dst_port)` |
| TRAFFIC_APP_MISMATCH | negative_function | application | src-dst-match | app-mismatch | miss | `application=not_in(rule.application)` |

## 约束对比

| constraint_id | 触发条件 | require | forbid / allowed | 设计意义 |
|---|---|---|---|---|
| C-L3-EGRESS-001 | `FAC-L3-EGRESS-MODE == next-hop` | FAC-L3-NH-IF-TYPE | forbid FAC-L3-OUTIF-TYPE | 下一跳模式不能混入出接口因子 |
| C-L3-EGRESS-002 | `FAC-L3-EGRESS-MODE == out-interface` | FAC-L3-OUTIF-TYPE | forbid FAC-L3-NH-IF-TYPE | 出接口模式不能混入下一跳接口因子 |
| C-L3-EGRESS-003 | next-hop | n/a | physical, sub-interface, aggregate, bvi, tunnel | 下一跳模式接口能力矩阵 |
| C-L3-EGRESS-004 | out-interface | n/a | tunnel, pppoe | 出接口模式接口能力矩阵 |
| C-L3-EGRESS-005 | `FAC-L3-REACHABILITY == unreachable` | FAC-L3-FAIL-DETECT-METHOD | n/a | 失效检测只在不可达场景展开 |
| C-CONFIG-VS-FUNCTION-001 | config rejected sample | n/a | forbid function precondition/positive/negative | 配置拒绝样本不得进入功能链路 |
| C-TRAFFIC-001 | `sample_class == negative_function` | function_test negative | forbid config accepted/rejected | 功能反向流量不是配置非法值 |
| C-RUNTIME-VS-CONFIG-001 | `owner_object == OBJ-PR-TRAFFIC and factor_id starts_with FAC-PKT-` | config_test not_applicable | forbid config accepted/rejected | 报文运行时输入不参与配置合法性覆盖 |
| C-RULE-CONFIG-001 | source/destination/service 配置字段做 config_test | owner_object OBJ-PR-RULE | forbid owner_object OBJ-PR-TRAFFIC | 规则配置字段合法性由规则对象因子承载 |

## 拓扑实例边界

本库可以描述策略路由设计需要的接口类型、接口能力和出口选择模式：

- `FAC-L3-NH-IF-TYPE` 描述下一跳关联接口类型；
- `FAC-L3-OUTIF-TYPE` 描述出接口接口类型；
- `FAC-L3-IF-CAPABILITY` 描述三层转发接口能力；
- capability matrix 可约束不同出口模式下允许的接口能力。

本库不得描述项目真实组网实例：

| 禁止写入公共因子的对象 | 正确去向 |
|---|---|
| `DUT.port1`、`DUT.port2`、`TG.port1` | LC `topology_bindings.device_id/port_id` |
| `DUT.port1<->TG.port1`、`LINK-PR-001` | LC `topology_bindings.link_id` |
| 某项目拓扑图中的真实入口/出口端口 | `analysis/scenarios/confirmed-scenarios.md` 和 PC 物化字段 |

真实端口不能作为 `values`、`sample_id`、`materialization` 示例或公共因子组成员。若用例需要指定入口/出口端口，`ptm-tde` 应先在 CAE 中引用 `topology_role_refs`，再由 integration 阶段从已确认场景生成 `topology_bindings`。

## 消费规则

- `ptm-tde` 通过项目 lock 固定本库版本，并通过 `factor_bindings` 把 `factor_id`、`sample_id`、`usage_context` 和物化阶段传递给下游 Skill。
- `topology_bindings` 与 `factor_bindings` 并行存在；真实设备、端口和链路只通过 `topology_bindings` 传递。
- M/LC/TD 阶段优先保留 `sample_id` 或表达式，PC 阶段再物化确定值。
- 配置拒绝样本只能用于配置反向用例；功能反向样本是可执行但预期不命中或走反向路径的业务输入。
- `FAC-PKT-*` 的 `config_test=not_applicable` 是明确职责声明，不是配置覆盖缺失；配置字段覆盖应查找 `FAC-PR-RULE-*` 或其他配置对象因子。
- PC 中若出现 `DUT.port1`、`TG.port1` 或 link 实例，必须能回链到 LC `topology_bindings` 和 `analysis/scenarios/confirmed-scenarios.md`；不得把这些实例补写为因子值或候选样本。
- 新因子先作为项目候选提案进入 `analysis/factor-usage/candidate-factor-proposals.yaml`，不得由项目运行直接写回本库。
