# NGFW DFX 因子库变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|---|---|---|---|---|---|
| FL-DFX-0.1-001 | 2026-07-02 | new_factor | FAC-DFX-CONCURRENT-OP | 新增并发操作模式因子（single/concurrent-modify/batch-create/batch-delete） | active |
| FL-DFX-0.1-002 | 2026-07-02 | new_factor | FAC-DFX-REF-COUNT | 新增引用计数因子（int[0,N]） | active |
| FL-DFX-0.1-003 | 2026-07-02 | new_factor | FAC-DFX-CONFIG-PERSISTENCE | 新增配置持久化模式因子（saved/rollback），unsaved 不可构造不纳入 | active |
| FL-DFX-0.1-004 | 2026-07-02 | new_factor | FAC-DFX-CONFIG-PERSISTENCE-RESULT | 新增配置持久化结果 oracle（保留/丢失/部分丢失），配 CONFIG-PERSISTENCE | active |
| FL-DFX-0.1-005 | 2026-07-02 | new_factor | FAC-DFX-VPP-CONSISTENCY | 新增 VPP 下发一致性 oracle | active |
| FL-DFX-0.1-006 | 2026-07-02 | new_factor | FAC-DFX-MEMORY-TREND | 新增内存使用趋势 oracle（稳定/增长/泄漏），配 STABILITY-TYPE=soak | active |
| FL-DFX-0.1-007 | 2026-07-02 | new_factor | FAC-DFX-LB-RATIO-DEVIATION | 新增负载分担比率偏差 oracle（0%/≤5%/>5%），配 ECMP-LOAD-BALANCE | active |
| FL-DFX-0.1-008 | 2026-07-02 | new_factor | FAC-DFX-FAILOVER-LOSS | 新增切换丢包数 oracle（0/≤10/>10），配 AVAILABILITY-METRIC | active |
| FL-DFX-0.1-009 | 2026-07-02 | new_factor | FAC-DFX-BATCH-RESPONSE-TIME | 新增批量操作响应时间 oracle（≤3s/>3s/超时），配 CONCURRENT-OP | active |
| FL-DFX-0.1-010 | 2026-07-02 | new_factor | FAC-DFX-AUTH-RESULT | 新增权限校验结果 oracle（通过/拒绝），配 common-network/FAC-SEC-USER-ROLE | active |
| FL-DFX-0.1-011 | 2026-07-02 | new_factor | FAC-DFX-UPGRADE-COMPATIBILITY | 新增升级配置兼容性 oracle（兼容/部分兼容/不兼容），配 RELIABILITY-OP=upgrade | active |
| FL-DFX-0.1-012 | 2026-07-02 | new_factor | FAC-DFX-APP-MATCH-LOSS-RATE | 新增应用匹配丢包率 oracle（0/≤1%/>1%），配 TRAFFIC-APP-MATCH | active |
| FL-DFX-0.1-013 | 2026-07-02 | new_factor | FAC-DFX-MULTI-PATH-CONSISTENCY | 新增多通道一致性 oracle（一致/不一致/部分一致），配 ECMP 系列 | active |
| FL-DFX-0.1-014 | 2026-07-02 | new_factor_group | DFX_CONFIG_DURABILITY | 新增配置耐久性与并发因子组 | active |
| FL-DFX-0.1-015 | 2026-07-02 | new_factor_group | DFX_QUALITY_ORACLE | 新增质量度量判定因子组，含 10 个 oracle | active |
