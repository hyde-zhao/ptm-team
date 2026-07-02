# NGFW IPv4 路由因子库变更记录

> change_type 必须使用以下枚举值之一

## change_type 枚举

| change_type | 含义 | 适用场景 |
|-------------|------|----------|
| `new_factor` | 新增因子 | 在库中添加全新因子 |
| `extend_factor_values` | 扩展因子取值 | 在 enum/range 中增加新值 |
| `extend_factor_samples` | 扩展因子样本 | 增加新的 sample_definition |
| `extend_usage_profiles` | 扩展样本用途配置 | 修改 usage_profiles |
| `add_constraints` | 新增约束 | 添加新的 require/forbid/allowed_values |
| `update_constraints` | 修改约束 | 修改已有约束的 allowed_values/forbid 等 |
| `new_factor_group` | 新增因子组 | 定义新的因子组合覆盖目标 |
| `extend_factor_group` | 扩展因子组 | 在已有组中增删因子 |
| `deprecate_factor` | 废弃因子 | 标记因子不再推荐使用 |
| `merge_factors` | 合并因子 | 多个因子合并为一个 |
| `split_factor` | 拆分因子 | 一个因子拆分为多个 |
| `split_responsibility` | 职责拆分 | 将混用的因子按职责分离 |
| `schema_change` | Schema 变更 | 修改因子库结构本身的定义 |

## 变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|-----------|---|---|---|---|---|
| FL-RT-0.1-001 | 2026-07-02 | extend_factor_values | FAC-L3-NH-IF-TYPE | 下一跳接口类型 tunnel 细化为 4over6/gre/sslvpn/ipsec（不含 6over4） | candidate |
| FL-RT-0.1-002 | 2026-07-02 | extend_factor_values | FAC-L3-OUTIF-TYPE | 出接口类型 tunnel 细化为 4over6/6over4/gre/sslvpn/ipsec，保留 pppoe | candidate |
| FL-RT-0.1-003 | 2026-07-02 | update_constraints | C-RT-EGRESS-001 | 出接口模式 allowed_values 更新为细化值；修正引用名 FAC-RT-INTERFACE-TYPE→FAC-L3-OUTIF-TYPE | candidate |
| FL-RT-0.1-004 | 2026-07-02 | schema_change | M-L3-EGRESS-INTERFACE | 能力矩阵 tunnel 行细化为多隧道类型行 | candidate |

---

## 变更详细说明

### FL-RT-0.1-001/002/003/004: 出口接口隧道类型细化（CFP-004）

**变更前状态**：
- FAC-L3-NH-IF-TYPE 取值 `[physical, sub-interface, aggregate, bvi, tunnel]`，tunnel 为单一值
- FAC-L3-OUTIF-TYPE 取值 `[tunnel, pppoe]`，tunnel 为单一值
- 约束 C-RT-EGRESS-001 引用 `FAC-RT-INTERFACE-TYPE`（与实际因子名不一致）
- 能力矩阵 M-L3-EGRESS-INTERFACE 仅一行 tunnel

**变更后状态**：
- FAC-L3-NH-IF-TYPE：tunnel 细化为 `4over6/gre/sslvpn/ipsec`（下一跳模式不含 6over4）
- FAC-L3-OUTIF-TYPE：tunnel 细化为 `4over6/6over4/gre/sslvpn/ipsec`，保留 `pppoe`
- 约束 C-RT-EGRESS-001：引用名修正为 `FAC-L3-OUTIF-TYPE`，allowed_values 同步细化
- 能力矩阵：tunnel 行展开为 next-hop 4 行 + out-interface 5 行

**原因**：
- 原始候选 CFP-004（IPSec 隧道耦合）误建为独立因子；实际应为出接口/下一跳接口类型的隧道细化
- 厂商支持 4over6/6over4/gre/sslvpn/ipsec 多种隧道，单一 tunnel 值无法区分

**影响**：
- 下游 C-Combination 阶段需按细化类型组合接口能力
- 消费方（ngfw-policy-routing）通过 factor_bindings 引用时需更新样本引用
- 约束引用名修正消除了 C-RT-EGRESS-001 与实际因子的不一致

**迁移指南**：
- 旧引用 `tunnel` 的 factor_bindings 需映射到具体隧道类型（4over6/6over4/gre/sslvpn/ipsec 之一）
- 旧 sample_id `NH_IF_TUNNEL`/`OUTIF_TUNNEL` 已替换为 `NH_IF_4OVER6` 等
