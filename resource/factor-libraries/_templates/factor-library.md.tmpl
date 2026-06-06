# {Domain Name}因子库

> 复制此文件到 `<library-name>/factor-library.md`，删除 `.tmpl` 后缀
> 将所有 `{...}` 占位符替换为实际内容

## 定位

本库归档 {领域名称} 领域的公共测试因子，供 `ptm-tde` 及未来其他 Agent / Skill 复用。

机器可读主库为 `factor-library.yaml`；本文档用于人工评审、横向对比和维护决策。

## 因子总览

| factor_id | 因子名称 | kind | role | owner_object | domain_model | 取值摘要 | 下游方法 | 用途 |
|-----------|---|---|---|---|---|---|---|---|
| {FAC-ID-1} | {名称} | {kind} | {role} | {owner} | {model} | {摘要} | {methods} | {用途} |
| {FAC-ID-2} | {名称} | {kind} | {role} | {owner} | {model} | {摘要} | {methods} | {用途} |

## 样本对比

### 配置字段样本

| factor_id | accepted config samples | rejected config samples | function precondition | 说明 |
|-----------|---|---|---|---|
| {FAC-ID} | {accepted 样本列表} | {rejected 样本列表} | {precondition 样本} | {说明} |

### 运行时报文样本

| factor_id | config_test | positive function samples | negative function samples | 说明 |
|-----------|---|---|---|---|
| {FAC-PKT-*} | not_applicable | {positive 样本} | {negative 样本} | 报文运行时输入，不参与配置合法性 |

### 业务流量样本（如有）

| sample_id | class | 关键因子组合 | materialization | 说明 |
|-----------|---|---|---|---|
| {TRAFFIC_ID} | {positive/negative} | {因子值组合} | {物化说明} | {说明} |

## 约束对比

| constraint_id | 触发条件 | require | forbid / allowed | 设计意义 |
|-----------|---|---|---|---|
| {C-ID} | {条件} | {require 因子} | {forbid/allowed} | {意义} |

## 拓扑实例边界

本库可以描述的抽象概念：
- {可以建模的抽象对象列表}

本库不得描述的项目真实组网实例：

| 禁止写入公共因子的对象 | 正确去向 |
|---|---|
| `DUT.port1`、`TG.port1` 等 | LC `topology_bindings.device_id/port_id` |
| `DUT.port1<->TG.port1` 等 link 实例 | LC `topology_bindings.link_id` |
| 项目拓扑图中的真实设备/端口 | `analysis/scenarios/confirmed-scenarios.md` 和 PC 物化字段 |

## 消费规则

- `ptm-tde` 通过项目 lock 固定本库版本，通过 `factor_bindings` 传递 `factor_id`、`sample_id`、`usage_context`
- `topology_bindings` 与 `factor_bindings` 并行存在；真实设备、端口和链路只通过 `topology_bindings` 传递
- M/LC/TD 阶段优先保留 `sample_id` 或表达式，PC 阶段再物化确定值
- 配置拒绝样本只能用于配置反向用例；功能反向样本是可执行但预期不命中的业务输入
- `FAC-PKT-*` 的 `config_test=not_applicable` 是明确职责声明，不是配置覆盖缺失
- 新因子先作为项目候选提案，不得由项目运行直接写回本库
