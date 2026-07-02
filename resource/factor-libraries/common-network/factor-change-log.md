# 通用网络因子库变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|---|---|---|---|---|---|
| FL-INIT-001 | 2026-05-21 | new_factor | FAC-NET-IP-SRC | 初始化源 IP 地址因子 | active |
| FL-INIT-002 | 2026-05-21 | new_factor | FAC-NET-TCP-DST-PORT | 初始化 TCP 目的端口因子 | active |
| FL-CMN-0.1-001 | 2026-07-02 | new_factor | FAC-CFG-SOUTHBOUND-IF | 新增南向配置下发通道因子（R01/R03/REST-API），跨特性复用 | active |
| FL-CMN-0.1-002 | 2026-07-02 | new_factor | FAC-SEC-USER-ROLE | 新增用户角色权限因子（admin/readonly/config-admin/auditor），配 ngfw-dfx/FAC-DFX-AUTH-RESULT | active |
| FL-CMN-0.1-003 | 2026-07-02 | update_external_consumers | common-network | 声明 ngfw-dfx/FAC-DFX-AUTH-RESULT 消费 FAC-SEC-USER-ROLE | active |
