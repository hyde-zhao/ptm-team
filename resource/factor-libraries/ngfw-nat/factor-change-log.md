# NGFW NAT 因子库变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|---|---|---|---|---|---|
| FL-NAT-0.1-001 | 2026-07-02 | new_library | ngfw-nat | 新建 NGFW NAT 因子库，承载 NAT44 转换类型公共因子 | active |
| FL-NAT-0.1-002 | 2026-07-02 | new_factor | FAC-NAT44-TYPE | 新增 NAT44 转换类型因子（源NAT/目的NAT/静态NAT），供策略路由跨库引用；源进源出不纳入 | active |
