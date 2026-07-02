# NGFW 设备命名对象因子库变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|---|---|---|---|---|---|
| FL-OBJ-0.1-001 | 2026-07-02 | new_factor | FAC-OBJ-ADDRESS-EXCLUDE-MODE | 新增地址对象排除模式因子（仅包含网段/包含与排除共存） | active |
| FL-OBJ-0.1-002 | 2026-07-02 | new_factor | FAC-OBJ-ADDRESS-EXCLUDE-RELATION | 新增包含与排除网段关系因子（无交集/交叉/包含覆盖排除/排除覆盖包含），供策略路由流量匹配位置引用 | active |
| FL-OBJ-0.1-003 | 2026-07-02 | update_external_consumers | ngfw-objects | 声明 ngfw-policy-routing/FAC-TRAFFIC-ADDR-MATCH-POSITION 消费排除因子 | active |
