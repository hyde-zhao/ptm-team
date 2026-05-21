# NGFW 策略路由因子库变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|---|---|---|---|---|---|
| FL-PR-0.2-001 | 2026-05-21 | merge_factors | FAC-L3-EGRESS-MODE | 将旧出口类型口径收敛为三层转发出口选择模式 | active |
| FL-PR-0.2-002 | 2026-05-21 | new_factor | FAC-L3-NH-IF-TYPE | 新增下一跳关联接口类型，覆盖物理口、子接口、聚合口、BVI、隧道口 | active |
| FL-PR-0.2-003 | 2026-05-21 | new_factor | FAC-L3-OUTIF-TYPE | 新增出接口接口类型，覆盖隧道口和 PPPoE 接口 | active |
| FL-PR-0.2-004 | 2026-05-21 | new_factor | FAC-L3-IF-CAPABILITY | 新增三层转发接口能力约束因子 | active |
| FL-PR-0.2-005 | 2026-05-21 | new_factor | FAC-L3-REACHABILITY | 新增出口可达、不可达、恢复状态因子 | active |
| FL-PR-0.2-006 | 2026-05-21 | new_factor | FAC-L3-FAIL-DETECT-METHOD | 新增 IP-LINK 与接口 Down 失效检测方式 | active |
| FL-PR-0.2-007 | 2026-05-21 | new_factor | FAC-L3-EXPECTED-FWD-PATH | 新增转发路径 oracle | active |
| FL-PR-0.2-008 | 2026-05-21 | extend_factor_samples | FAC-L3-NH-WEIGHT | 补齐配置 accepted/rejected 与功能 precondition 样本 | active |
| FL-PR-0.2-009 | 2026-05-21 | new_factor | FAC-CONFIG-NAME | 新增配置对象名称合法性因子 | active |
| FL-PR-0.2-010 | 2026-05-21 | split_factor | TRAFFIC_MATCHING | 将粗粒度流量画像拆分为流量层级、IP匹配、服务匹配、应用匹配和预期命中结果 | active |
| FL-PR-0.2-011 | 2026-05-21 | new_factor_group | L3_EGRESS_NEXT_HOP | 新增下一跳模式三层转发接口覆盖组 | active |
| FL-PR-0.2-012 | 2026-05-21 | new_factor_group | L3_EGRESS_OUT_INTERFACE | 新增出接口模式三层转发接口覆盖组 | active |
| FL-PR-0.2-013 | 2026-05-21 | new_factor_group | L3_EGRESS_FAILOVER | 新增出口不可达和故障恢复组 | active |
| FL-PR-0.2-014 | 2026-05-21 | new_factor_group | POLICY_RULE_ORDER | 新增策略路由重叠规则命中判定组 | active |
| FL-PR-0.2-015 | 2026-05-21 | new_factor_group | DFX_COUNTER | 新增命中计数展示和清零组 | active |
| FL-PR-0.2-016 | 2026-05-21 | new_factor_group | DFX_LOG_AUDIT | 新增操作日志审计组 | active |
| FL-PR-0.2-017 | 2026-05-21 | new_factor_group | HA_POLICY_ROUTE | 新增策略路由 HA 同步与切换组 | active |
| FL-PR-0.2.1-001 | 2026-05-21 | split_responsibility | FAC-PKT-SRC-IP | 将配置非法样本迁出报文源 IP 因子，明确其只承载运行时流量输入 | active |
| FL-PR-0.2.1-002 | 2026-05-21 | split_responsibility | FAC-PKT-DST-IP | 将配置非法样本迁出报文目的 IP 因子，明确其只承载运行时流量输入 | active |
| FL-PR-0.2.1-003 | 2026-05-21 | split_responsibility | FAC-PKT-SRC-PORT | 将 0/65536 配置非法样本迁出报文源端口因子 | active |
| FL-PR-0.2.1-004 | 2026-05-21 | split_responsibility | FAC-PKT-DST-PORT | 将 0/65536 配置非法样本迁出报文目的端口因子 | active |
| FL-PR-0.2.1-005 | 2026-05-21 | new_factor | FAC-PR-RULE-SRC-IP | 新增规则源 IPv4 配置字段合法性因子 | active |
| FL-PR-0.2.1-006 | 2026-05-21 | new_factor | FAC-PR-RULE-DST-IP | 新增规则目的 IPv4 配置字段合法性因子 | active |
| FL-PR-0.2.1-007 | 2026-05-21 | new_factor | FAC-PR-RULE-PROTOCOL | 新增规则服务协议配置字段合法性因子 | active |
| FL-PR-0.2.1-008 | 2026-05-21 | new_factor | FAC-PR-RULE-SRC-PORT | 新增规则源端口配置字段合法性因子 | active |
| FL-PR-0.2.1-009 | 2026-05-21 | new_factor | FAC-PR-RULE-DST-PORT | 新增规则目的端口配置字段合法性因子 | active |
| FL-PR-0.2.1-010 | 2026-05-21 | new_factor_group | CONFIG_FIELD_VALIDITY | 新增策略路由配置字段合法性因子组 | active |
