---
name: design-ppdcs-analyzer
description: >-
  PPDCS 设计协调：读取设计计划并为每个逻辑用例调用对应 PPDCS 方法 Skill，
  统一输出 ppdcs/ppdcs 与 ppdcs/pc 的单文件产物。
  触发词包括：PPDCS设计、逻辑用例设计、单文件设计、ppdcs/ppdcs、ppdcs/pc。
  适用场景：MFQ design 阶段，design-planner 已确认后。
argument-hint: "可选：logic_case_id=<LC-ID>"
user-invokable: true
status: active
---

## 目标

作为 design 阶段的协调 Skill，确保五类 PPDCS 方法产物遵循统一文件布局：

- `ppdcs/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`
- `ppdcs/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`

不再使用深目录模式（旧：`design/<module>/<sub-module>/<LC-ID>/`），统一使用扁平命名。

## 输入

| 输入 | 路径 |
|---|---|
| 设计计划 | `mfq/integration/design-plan.md` |
| 推断明细 | `process/plan/design-planner-reasoning.md` |
| 逻辑用例 | `mfq/integration/logic-cases.md` |
| 测试数据 | `mfq/integration/test-data.md` |
| 场景链 | `kym/scenarios/confirmed-scenarios.md` |
| 目录结构 | `kym/feature-input/directory-structure.md` |

## 拓扑绑定输入契约

design-ppdcs-analyzer 必须消费 LC 中由 integrator 生成的 `topology_bindings`，不得在 design 阶段重新发明 DUT/TG/接口/link 绑定。

| 输入字段 | 来源 | 用途 |
|---|---|---|
| `topology_bindings` | `mfq/integration/logic-cases.md` 的“组网绑定（来自 confirmed-scenarios.md）”章节 | 为 PPDCS 过程和 PC 提供真实组网对象回链 |
| `topology_role_refs` | LC trace refs | 保留测试逻辑位置约束 |
| `topology_refs` | LC trace refs / confirmed-scenarios.md | 回链 TOPO 实例 |
| `topology_gap_refs` / `confirmation_gap_refs` | TP/LC 透传 | 保留缺失、不唯一或冲突绑定 |

三层概念必须保持分离：
- 测试因子 = 业务/配置/数据/报文取值，继续消费 `factor_bindings`。
- 拓扑角色 = 测试逻辑位置，只作为 PPDCS/PC 的前置与动作位置约束。
- 真实组网对象 = confirmed-scenarios.md TOPO 实例，只能通过 LC `topology_bindings` 使用。

若 LC 缺少必需拓扑绑定，或绑定状态不是 `confirmed`，PPDCS/PC 可以生成草案，但相关 PC 的 `fact_status` 必须为 `needs-confirmation`，并透传 gap。

## 调用关系

| PPDCS 特征 | 调用 Skill | PPDCS 文件内容 |
|---|---|---|
| P-Process | `process-design` | 流程图、路径枚举、覆盖策略、触发数据 |
| P-Parameter | `parameter-design` | factor catalog、规则、判定表、data row |
| D-Data | `data-design` | 等价类、边界值、独立性检查、实际取值 |
| C-Combination | `combination-design` | 因子表、约束、Pairwise/正交、组合覆盖 |
| S-State | `state-design` | 状态图、迁移表、守卫条件、迁移路径 |

## 目录层级查找

PPDCS 文件名由四段组成（`<三级>-<四级>-<五级>-<LC用例名>.md`），每段必须来自 `directory-structure.md` 和 LC 表。由于 LC 的 `所属模块` 字段仅提供五级目录名，必须通过 `directory-structure.md` 回查完整的 `三级→四级→五级` 层级链。

### 查找表构建

在处理任何 LC 之前，先加载 `kym/feature-input/directory-structure.md` 并构建查找表：

```
1. 解析 "### 三级目录：<三级名>" 获取完整三级目录名（含 "IPv4" 等前缀，不得截断）
2. 解析目录树和层级表格，提取每条 (四级名, 五级名) 映射
3. 构建 lookup[五级名] = (三级名, 四级名)
```

示例（基于 IPv4策略路由 项目的 directory-structure.md）：

```
lookup["策略配置"]   = ("IPv4策略路由", "配置管理")
lookup["出口配置"]   = ("IPv4策略路由", "配置管理")
lookup["入接口匹配"] = ("IPv4策略路由", "路由匹配")
lookup["五元组匹配"] = ("IPv4策略路由", "路由匹配")
lookup["策略优先级"] = ("IPv4策略路由", "路由匹配")
lookup["网关转发"]   = ("IPv4策略路由", "路由转发")
lookup["出接口转发"] = ("IPv4策略路由", "路由转发")
lookup["负载分担"]   = ("IPv4策略路由", "路由转发")
lookup["DFX"]        = ("IPv4策略路由", "管理维护")
```

### 文件名构造

对每个 LC，按以下规则构造文件名：

1. 从 LC 表的 `所属模块` 列获取五级目录名
2. 查 lookup 表获取三级目录名和四级目录名
3. 拼接：`<三级目录>-<四级目录>-<五级目录>-<LC标题>.md`
4. 去除路径分隔符、控制字符和首尾空白
5. 同名冲突时追加 `-<LC-ID>`
6. `ppdcs/ppdcs/` 与 `ppdcs/pc/` 使用同一个 basename

**异常处理**：
- 若 lookup 查不到 `所属模块` → 标记 `needs-confirmation`，文件名暂用 `LC-ID` 替代 LC 标题，并在 reasoning 中记录"目录层级查找失败：所属模块 `<模块名>` 不在 directory-structure.md 中"
- 若 `directory-structure.md` 不存在或无法解析 → **BLOCKING**，不得继续生成 PPDCS/PC 文件

## 文件命名规则

文件名必须由四段组成：

```text
<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
```

规则：

1. 每段来自 `directory-structure.md` 查找表和 LC 标题，按 §目录层级查找 中定义的规则构造。
2. 去除路径分隔符、控制字符和首尾空白。
3. 同名冲突时追加 `-<LC-ID>`。
4. `ppdcs/ppdcs/` 与 `ppdcs/pc/` 使用同一个 basename。

## 输出契约

### PPDCS 过程文件

`ppdcs/ppdcs/<basename>.md` 至少包含：

1. LC 基本信息与 trace；
2. design-planner 推荐与 reasoning；
3. 对应 PPDCS 方法的完整五步设计过程；
4. 未确认事实与 gap 原样透传；
5. LC `topology_bindings` 原样透传，并说明拓扑角色如何作为前置/动作位置约束；
6. 指向 PC 文件的相对路径。

### PC 文件

`ppdcs/pc/<basename>.md` 至少包含：

1. LC 基本信息与 trace；
2. 物理用例 16 列总表；
3. 每条 PC 的 `case_steps` 结构化步骤清单，步骤必须同时包含人类可读 `step_name` 与可执行 `atomic_op`；
4. 每条 PC 回链到 `requirement_ids / logic_case_id / trace_refs / scenario_refs / action_source_refs / factor_bindings / factor_refs / topology_bindings / topology_role_refs / topology_refs / fact_status`；
5. 指向 PPDCS 过程文件的相对路径。

### PC 步骤契约

`case_steps` 是 PC 的主步骤契约，16 列表中的 `测试步骤*` 是它的交付渲染结果。不得只输出原子操作而缺少步骤名称。

```yaml
case_steps:
  - step_id: STEP-001
    step_name: 配置策略路由的匹配源地址对象 OBJ_SRC_WEB
    target: DUT
    atomic_op:
      op_id: config-policy-route
      args:
        src-addr: OBJ_SRC_WEB
    expected_result: 策略路由规则成功引用源地址对象 OBJ_SRC_WEB
    trace_refs:
      - TP-001
      - TD-ADDR-001
```

字段要求：

| 字段 | 必填 | 说明 |
|---|:---:|---|
| `step_id` | 是 | PC 内稳定步骤编号，如 `STEP-001` |
| `step_name` | 是 | 面向测试人员的动作意图，例如“配置策略路由的匹配源地址对象 OBJ_SRC_WEB” |
| `target` | 否 | 执行对象，如 `DUT`、`TG`、`Controller`；未知写 `—` 或 `[待确认]` |
| `atomic_op.op_id` | 是 | ptm-atomic 操作 ID，必须同步进入 `action_source_refs` |
| `atomic_op.args` | 是 | 原子操作参数键值；无参数写 `{}` |
| `expected_result` | 是 | 当前步骤的预期结果；未知保留 `[待确认]` |
| `trace_refs` | 否 | 当前步骤回链的 TP / TD / scenario chain 引用 |

`atomic_op.op_id` 回链硬约束：

- 每个 `case_steps[].atomic_op.op_id` 必须逐字匹配当前 LC / PC `action_source_refs` 中的某一项。
- 不得把相近语义、IPv4/IPv6 变体、历史示例或通用 fallback 操作写入 `case_steps`，除非该 `op_id` 已在 `action_source_refs` 中出现。
- 若上游缺少所需 `op_id`，必须把 PC 标记为 `needs-confirmation`，并写入 `pc_step_contract_gap`；不得自行创造未回链操作。
- 典型反例：IPv6 PC 的 `action_source_refs` 只有 `tg_send_ipv6_traffic / fw_query_policy_route6_hit_count` 时，`case_steps` 不能写 `tg_send_ipv4_traffic / fw_query_policy_route_hit_count`。

16 列表 `测试步骤*` 渲染规则：

```text
<序号>. <step_name>
   执行对象：<target>
   原子操作：<op_id> <arg1>=<value1> <arg2>=<value2>
```

Markdown 表格中使用 `<br>` 表达换行，不新增 16 列之外的列。

## 拓扑绑定校验

生成每个 PPDCS/PC 文件前必须执行以下校验，并把结论写入 PPDCS 过程文件：

| 检查项 | 通过条件 | 失败处理 |
|---|---|---|
| LC 绑定来源 | 每个 `topology_binding_id` 均来自 LC “组网绑定（来自 confirmed-scenarios.md）”章节 | 标记 `needs-confirmation`，写入 `confirmation_gap_refs` |
| TOPO 回链 | `topology_ref / binding_source` 可回链 `kym/scenarios/confirmed-scenarios.md` | 不得把真实端口写入 confirmed PC；降级 `fact_status` |
| PC 端口使用 | PC 中出现的 `DUT.port* / TG.port* / link` 均能回链 LC `topology_bindings` 和 confirmed-scenarios.md | 记录拓扑绑定错误，不得静默通过 |
| 因子分层 | `factor_bindings` 不包含拓扑角色或真实组网对象 | 标记设计输入污染，相关 PC `needs-confirmation` |
| 步骤双层表达 | 每条 `case_steps[]` 同时包含 `step_name` 与 `atomic_op.op_id`，且 `atomic_op.op_id` 可回链 `action_source_refs` | 缺任一项则 PC 降级为 `needs-confirmation` 并记录交付字段缺口 |

PC 表中若需要展示真实端口，只能来自 `topology_bindings.bound_object`，并同时保留 `topology_binding_id`；不得从动作文本或角色名直接推断。

## Gotchas

- 五个方法 Skill 可以负责方法细节，但最终文件布局必须由本 Skill 收敛。
- 同一个 LC 只能有一个 PPDCS 文件和一个 PC 文件。
- `needs-confirmation` 不得在设计阶段被静默改成 confirmed。
- 不生成 case-index 或工具分析表；当前最终交付只保留测试方案和测试用例两份 Markdown。
- PPDCS/PC 消费 LC `topology_bindings`，不重新推断组网绑定。
- 真实端口可以出现在 PC 执行步骤中，但必须可回链到 LC 绑定和 confirmed-scenarios.md。
- 拓扑角色只约束测试位置，不是 D-Data/C-Combination/P-Parameter 的测试因子。
- PC 步骤名称表达测试动作意图；原子操作表达可执行动作和参数。两者不得互相替代。

## 验收标准

- [ ] 每个目标 LC 在 `ppdcs/ppdcs/` 有且只有一个过程文件
- [ ] 每个目标 LC 在 `ppdcs/pc/` 有且只有一个 PC 文件
- [ ] 文件名符合 `<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`（4 段，`-` 分隔）
- [ ] 三级目录名与 `directory-structure.md` "### 三级目录" 完全一致（含 `IPv4` 等前缀，不截断）
- [ ] 查找表覆盖 LC 表中所有 `所属模块` 值
- [ ] 查找失败的 LC 标记 `needs-confirmation`，文件名使用 LC-ID 替代
- [ ] 不创建旧式深目录（如 `design/<module>/<sub-module>/`），统一使用 `ppdcs/ppdcs/` 扁平命名
- [ ] PPDCS 过程文件保留 LC `topology_bindings` 与拓扑绑定校验结论
- [ ] PC 中真实端口均可回链 LC `topology_bindings` 和 `kym/scenarios/confirmed-scenarios.md`
- [ ] 未确认或不唯一拓扑绑定导致相关 PC `fact_status=needs-confirmation`
- [ ] 每条 PC 均包含 `case_steps`，且每一步同时包含 `step_name` 与 `atomic_op`
