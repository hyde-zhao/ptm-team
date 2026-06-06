# 因子建模标准

> 本文是 `/home/hyde/projects/ptm-team/resource/factor-libraries/README.md` 的浓缩版，聚焦于研究区日常建模所需的规则和参考。

---

## 1. 因子建模 6 问

每个因子必须能回答以下 6 个问题。不能靠名称推断，必须在 YAML 中显式写出。

| # | 问题 | YAML 字段 | 判断规则 |
|---|------|-----------|----------|
| 1 | 它描述什么对象 | `owner_object` | 分清配置对象、运行时流量、状态、DFX、HA 等 |
| 2 | 它在设计中起什么作用 | `factor_kind` / `design_role` | driver 展开设计，constraint 裁剪组合，oracle 判定结果 |
| 3 | 它的值域是什么 | `domain_model` / `value_type` / `values` / `domain_expr` | 可被机器解析的取值集合或表达式 |
| 4 | 它何时适用 | `applicable_when` | 必须显式写出，如 `always`、`FAC-X == value`、或自然语言条件 |
| 5 | 它服务哪些方法 | `downstream_methods` | D-Data / P-Parameter / C-Combination / S-State / oracle-design |
| 6 | 它是否可复用 | `reuse_policy` / `status` | 研究区默认 `candidate`，发布后为 `active` |

---

## 2. 因子类型

### 2.1 按 owner_object 分类

| 类型 | 典型 owner_object | 样本职责 | 示例 |
|------|-------------------|----------|------|
| 配置字段因子 | `OBJ-PR-RULE`、`OBJ-GENERIC-CONFIG` | 生成 accepted / rejected 配置样本 | `FAC-PR-RULE-SRC-IP`、`FAC-CONFIG-NAME` |
| 运行时输入因子 | `OBJ-PR-TRAFFIC` | 生成 positive / negative 功能流量；`config_test` = `not_applicable` | `FAC-PKT-SRC-IP`、`FAC-PKT-DST-PORT` |
| 状态因子 | 业务状态对象 | 描述启用、不可达、恢复、同步等状态变化 | `FAC-L3-REACHABILITY`、`FAC-HA-SYNC-STATE` |
| oracle 因子 | 被验证对象 | 描述预期结果，不作为输入配置 | `FAC-EXPECTED-MATCH-RESULT`、`FAC-L3-EXPECTED-FWD-PATH` |

### 2.2 按 factor_kind 分类

| factor_kind | 含义 | 典型用法 |
|-------------|------|----------|
| `data` | 数据因子 | 描述被测对象的取值，如 IP 地址、端口号、协议 |
| `control` | 控制因子 | 描述设计选择或策略，如出口模式、规则顺序 |
| `constraint` | 约束因子 | 限制其他因子的取值或组合，如接口能力 |
| `state` | 状态因子 | 描述系统或环境的状态变化，如可达性、同步状态 |
| `oracle` | oracle 因子 | 描述预期结果，用于判定测试是否通过 |
| `condition` | 条件因子 | 描述触发条件，如失效检测方式 |

### 2.3 按 design_role 分类

| design_role | 含义 | 消费方 |
|-------------|------|--------|
| `driver` | 驱动测试设计的变量 | M/LC/TD 阶段展开为测试点 |
| `constraint` | 限制因子组合的规则 | 组合生成前裁剪 |
| `oracle` | 预期结果的判定标准 | PC 阶段断言 |

---

## 3. 必填字段速查表

### 3.1 所有因子通用

```yaml
factor_id: FAC-{DOMAIN}-{NAME}       # 全局唯一标识
factor_name: "中文名称"               # 人读名称
factor_kind: data|control|constraint|state|oracle|condition
design_role: driver|constraint|oracle
owner_object: OBJ-{DOMAIN}-{NAME}    # 所属被测对象
domain_model: enum|range|ip_address|ip_network|string_pattern|state|object_instance
value_type: enum|integer|string|state
aliases: []                           # 别名列表，用于搜索和匹配
applicable_when: "条件表达式"         # 不能为空，最低写 always
downstream_methods: []               # D-Data|P-Parameter|C-Combination|S-State|oracle-design
reuse_policy: must_reuse              # 研究区默认 must_reuse
status: candidate                     # 研究区默认 candidate
```

### 3.2 enum 类型额外字段

```yaml
values: [value1, value2, ...]         # 枚举取值列表
display_values:                       # 中文显示名（可选）
  value1: 显示名1
  value2: 显示名2
```

### 3.3 range 类型额外字段

```yaml
domain_expr: "int[1,65535]"           # 值域表达式
```

### 3.4 string_pattern 类型额外字段

```yaml
domain_expr:
  length: "1..31"                     # 长度范围
  charset: [uppercase_letter, ...]    # 允许字符集
  regex: "^[A-Za-z0-9...]{1,31}$"    # 正则表达式
```

### 3.5 ip_address 类型额外字段

```yaml
domain_expr: ipv4_or_ipv6             # IP 版本标识
```

### 3.6 ip_network 类型额外字段

IP 网段类型，格式为 `地址/掩码`。适用于路由目的网络、ACL 网段等需要同时表达 IP 地址和掩码长度的场景。

```yaml
domain_expr:
  version: ipv4                       # ipv4 | ipv6 | ipv4_or_ipv6
  semantic_constraints:               # 可选：语义约束
    unicast_only: true                # 仅单播地址
    exclude_loopback: true            # 排除 127.0.0.0/8
    exclude_multicast: true           # 排除 224.0.0.0/4
    prefix_range: "0..32"             # 掩码长度范围
```

### 3.7 object_instance 类型额外字段

设备上已定义的命名对象。值域不是固定范围，而是运行时设备上已存在的对象名称集合。

```yaml
domain_expr:
  object_type: address               # 对象类型标识
  api: /api/v1/ippool                # 管理 API（可选）
  stored_in: topology.address_objects # 运行时存储位置
  members: ngfw-objects/FAC-OBJ-ADDRESS  # 成员类型（仅组类型需要，跨库引用）
```

每个 `object_instance` 因子遵循统一 3 样本模式：
- `valid_config` — 设备上已存在的名称 → `from_topology.<source>.any`
- `invalid_config` — 设备上不存在的名称 → `from_topology.<source>.nonexistent`
- `invalid_format` — 名称格式非法 → `from_factor(common-network/FAC-CONFIG-NAME).rejected`

### 3.8 有 sample_definitions 的因子额外字段

```yaml
sample_definitions:
  - sample_id: SAMPLE_NAME            # 样本唯一标识
    sample_class: valid_member|boundary_min|boundary_max|...  # 样本分类
    description: "一句话说清这个样本代表什么"  # 人读：等价类说明
    representative_values:            # 人读：几个具体示例值
      - "示例值1"
      - "示例值2"
    expr: "表达式"                     # 机器读：PC 阶段按 seed=case_id 求值
    materialized_value: 具体值         # 默认物化结果（取 representative_values 首项）
    applicability:
      config_test: accepted|rejected|not_applicable
      function_test: positive|negative|precondition|not_applicable|not_preferred

usage_profiles:
  config_test:
    accepted_config_samples: [SAMPLE_A, SAMPLE_B]
    rejected_config_samples: [SAMPLE_C]
    policy: not_applicable            # 对运行时因子整类跳过配置覆盖
  function_test:
    positive_samples: [SAMPLE_X]
    negative_samples: [SAMPLE_Y]
    precondition_samples: [SAMPLE_Z]
```

### 3.9 sample_class 枚举

| sample_class | 含义 | 典型用途 |
|-------------|------|----------|
| `valid_member` | 域中有效成员 | 等价类正向值 |
| `boundary_min` | 边界最小值 | 边界值测试 |
| `boundary_max` | 边界最大值 | 边界值测试 |
| `in_range_nominal` | 域内随机典型值 | 功能前置 |
| `below_min` | 低于最小值 | 配置拒绝 |
| `above_max` | 高于最大值 | 配置拒绝 |
| `min_length` | 最小长度 | 字符串边界 |
| `max_length` | 最大长度 | 字符串边界 |
| `charset_mixed` | 混合字符集 | 字符串典型值 |
| `invalid_charset` | 非法字符集 | 字符串拒绝 |
| `valid_config` | 合法配置值 | 配置字段正向 |
| `invalid_config` | 非法配置值（语义） | 配置字段拒绝 — 格式正确但语义不合法 |
| `invalid_format` | 非法格式 | 配置字段拒绝 — 格式本身不合法（空值、超长、错误分隔符等） |
| `positive_function` | 功能正向样本 | 预期命中/匹配 |
| `negative_function` | 功能反向样本 | 可执行但预期不命中 |

> `invalid_config` 与 `invalid_format` 的区别：
> - `invalid_config`: 格式合法但**语义**不合法。如 `224.0.0.0/4` 的 IP 格式正确，但 D 类组播地址不能作为路由目的网络。
> - `invalid_format`: **格式**本身不合法。如空字符串、3段IP、16进制IP 等根本不符合 IP 网段格式。

---

## 4. 表达式规范

### 4.1 表达式的双重角色

每个样本的取值定义分为**人读**和**机器读**两层：

| 字段 | 层 | 用途 | 示例 |
|------|-----|------|------|
| `description` | 人读 | 一句话说清样本代表的等价类 | "A类单播网段。IP首段 1~126，掩码 1~31 位。" |
| `representative_values` | 人读 | 几个具体例子，评审时一眼看懂取值 | `["<IP_ADDRESS>/8", "42.173.89.0/24"]` |
| `expr` | 机器读 | PC 阶段按 `seed=case_id` 求值为具体值 | `ip_net(class=a, prefix=1..31)` |
| `materialized_value` | 默认物化 | expr 在默认条件下的输出 | `"<IP_ADDRESS>/8"` |

### 4.2 表达式函数参考

#### range 类型

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `min` | — | 值域最小值 | `expr: "min"` → `1` |
| `max` | — | 值域最大值 | `expr: "max"` → `255` |
| `min - N` | N=偏移量 | 低于最小值 N | `expr: "min - 1"` → `0` |
| `max + N` | N=偏移量 | 高于最大值 N | `expr: "max + 1"` → `256` |
| `random_int(a,b,seed=X)` | a=下界, b=上界, seed=种子 | [a,b] 间确定性随机整数 | `expr: "random_int(2,254,seed=case_id)"` → `137` |

#### string_pattern 类型

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `string(charset, length)` | charset=字符集, length=长度 | 指定长度字符串 | `expr: "string(charset=allowed,length=1)"` → `"A"` |
| `string(include, length, seed)` | include=字符列表, length=范围, seed=种子 | 确定性随机字符串 | `expr: "string(include=[upper,lower],length=12..20,seed=case_id)"` → `"AbcDefGhijKl"` |

#### ip_address 类型

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `valid_ipv4_host()` | — | 合法 IPv4 主机地址 | → `"<IP_ADDRESS>"` |
| `valid_ipv4_subnet()` | — | 合法 IPv4 子网地址 | → `"<IP_ADDRESS>/24"` |
| `invalid_ipv4()` | — | 非法 IPv4 地址 | → `"0.0.0.0"` |

#### ip_network 类型（🆕）

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `ip_net(s)` | s=字面量字符串 | 精确网段 | `expr: 'ip_net("0.0.0.0/0")'` → `"0.0.0.0/0"` |
| `ip_net(class, prefix)` | class=a\|b\|c\|d\|e\|loopback, prefix=掩码范围 | 指定地址类+掩码的网段 | `expr: 'ip_net(class=a, prefix=1..31)'` → `"<IP_ADDRESS>/8"` |
| `ip_net(class, prefix, invalid=true)` | 同上 + 语义非法标记 | 语义非法的网段 | `expr: 'ip_net(class=d, prefix=3..32, invalid=true)'` → `"224.0.0.0/4"` |

class 参数的首段范围映射：

| class | IP 首段 | 含义 |
|-------|---------|------|
| `a` | 1~126 | A 类单播 |
| `b` | 128~191 | B 类单播 |
| `c` | 192~223 | C 类单播 |
| `d` | 224~239 | D 类组播 |
| `e` | 240~255 | E 类保留 |
| `loopback` | 127 | 环回地址 |

#### 格式非法生成

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `invalid_format(type=empty)` | — | 空字符串 | → `""` |
| `invalid_format(type=too_long)` | — | 确定性随机超长字符串 | → `"<IP_ADDRESS>.10.20/24/32/extra"` |
| `invalid_format(type=wrong_segments, segments=N)` | N=段数 | N 段点分格式 | `segments=3` → `"192.168.1"` |
| `invalid_format(type=bad_separator, sep=X)` | X=分隔符 | 使用错误分隔符的 IP | `sep="-"` → `"192-168-1-1/24"` |
| `invalid_format(type=bad_mask_sep, sep=X)` | X=分隔符 | 使用错误掩码分隔符 | `sep="\\"` → `"<IP_ADDRESS>\\24"` |
| `invalid_format(type=hex)` | — | 16 进制 IP 格式 | → `"0xC0A80101/24"` |

#### 上下文引用（适用于运行时因子）

| 函数 | 参数 | 输出 | 示例 |
|------|------|------|------|
| `from_rule.<field>.valid_member` | field=规则字段名 | 从关联规则的有效成员中取值 | `from_rule.src_ip.valid_member` → `"<IP_ADDRESS>/16"` |
| `not_in(rule.<field>)` | field=规则字段名 | 不在关联规则定义的集合中 | `not_in(rule.src_ip)` → `"<IP_ADDRESS>/12"` |
| `not_in(values)` | — | 不在因子枚举值集合中 | 用于 enum 类型生成非法值 |

### 4.3 表达式求值模型

```
PC 物化阶段
    │
    ├── 读取 sample_definitions[].expr
    ├── 注入 seed = hash(case_id)       ← 保证同一用例永远生成相同值
    ├── 注入 rule_context               ← 仅 from_rule.* 函数需要
    │     └── from_rule.src_ip.members → ["<IP_ADDRESS>/16", "<IP_ADDRESS>/16"]
    ├── 注入 topology_bindings          ← 仅拓扑相关因子需要
    └── 输出 materialized_value
```

**确定性保证**：所有带随机性的表达式函数都接受 `seed=case_id` 作为种子。同一 `case_id` 下 `hash(case_id, sub_seed)` 的子种子也确定，因此输出完全可复现。

> ⚠️ `ip_network` 类型的因子不需要 `from_rule` 上下文（目的网络是独立配置），只需要 `seed=case_id`。这与 `FAC-PKT-SRC-IP`（需要 `from_rule.src_ip`）不同。

### 4.4 跨库引用规范

研究区的因子分布在多个库中。一个库的因子可以引用另一个库的因子，做到"统一定义、全库复用"。

#### 引用方声明（consumer）

在因子的 `sample_definitions[].expr` 中使用 `from_target()` 从被引用目标取样本：

```yaml
# 策略路由引用地址对象
- factor_id: FAC-PR-RULE-SRC-NETWORK
  domain_expr:
    reference:
      default: any                              # 默认值（可选）
      switch:                                   # switch 型引用（可选，有开关字段时使用）
        field: source_network_is_group          # 开关字段名
        cases:
          false: ngfw-objects/FAC-OBJ-ADDRESS       # is_group=false → 地址对象
          true: ngfw-objects/FAC-OBJ-ADDRESS-GROUP  # is_group=true → 地址组对象
      target: ngfw-objects/FAC-OBJ-ADDRESS      # 直接引用（无开关时使用）
  sample_definitions:
    - sample_id: OBJ_VALID
      expr: 'from_target().accepted'            # 从引用目标的 accepted 样本池取
    - sample_id: OBJ_NOT_EXIST
      expr: 'from_target().invalid_config'      # 从引用目标的语义无效池取
    - sample_id: OBJ_NAME_INVALID
      expr: 'from_target().invalid_format'      # 从引用目标的格式无效池取
```

`reference` 的三种模式：

| 模式 | 使用场景 | 示例 |
|------|---------|------|
| `target` 直接引用 | 固定引用一个因子 | `ngfw-objects/FAC-OBJ-ADDRESS` |
| `switch` 开关引用 | 通过 `_is_group` 等字段动态选择 | `false → 地址对象 / true → 地址组对象` |
| `default` 默认值 | 可选的 `any` 值 | 不填时使用 |

`from_target()` 可取的样本池：

| 表达式 | 含义 |
|--------|------|
| `from_target().accepted` | 引用目标的 `accepted_config_samples` + `function_test.precondition_samples` |
| `from_target().invalid_config` | 引用目标的 `rejected_config_samples`（语义非法） |
| `from_target().invalid_format` | 引用目标的 `rejected_config_samples`（格式非法） |

#### 依赖声明（depends_on）

因子组可以声明对另一个库的因子的依赖：

```yaml
factor_groups:
  - group_id: PR_TRAFFIC_MATCHING
    depends_on:
      factor: ngfw-traffic/FAC-PKT-VALIDITY-MODE
      required_value: policy_match
    factors: [FAC-TRAFFIC-LAYER-TYPE, ...]
```

`depends_on.required_value` 表示该组的覆盖策略只在依赖因子取特定值时才生效。

#### 被引用方反向记录（external_consumers）

被引用的因子需要在库级声明"谁在用我"，确保引用变更时能通知所有消费方：

```yaml
# ngfw-objects/factor-library.yaml
external_consumers:
  - consumer: ngfw-policy-routing/FAC-PR-RULE-SRC-NETWORK
    samples_used: [accepted, invalid_config, invalid_format]
    switch_case: false        # 仅 switch 型引用需要
  - consumer: ngfw-policy-routing/FAC-PR-RULE-SRC-NETWORK
    samples_used: [accepted, invalid_config, invalid_format]
    switch_case: true
```

#### 引用完整性规则

1. **引用方**必须通过 `reference` 声明依赖关系，不能直接在 `expr` 中硬编码跨库引用。
2. **被引用方**必须在 `external_consumers` 中记录所有消费者。
3. 被引用因子废弃或变更取值时，必须检查 `external_consumers` 并通知所有消费方同步更新。
4. 同库内的因子引用不视为跨库引用，直接用 `factor_id` 即可。

### 4.5 `object_instance` 类型

`object_instance` 用于"设备上已定义的命名对象"，与 `ip_network`（直接建模 IP 值域）不同，它的值域不是固定的 IP 范围，而是**设备运行时已存在的对象名称的集合**。

#### domain_expr 字段

```yaml
domain_model: object_instance
value_type: string
domain_expr:
  object_type: address                              # 对象类型
  api: /api/v1/ippool                               # 管理 API（可选，用于追溯）
  stored_in: topology.address_objects               # 运行时存储位置
  members: ngfw-objects/FAC-OBJ-ADDRESS             # 成员类型（仅组类型需要）
```

#### 标准样本模式

所有 `object_instance` 因子共享同一个 3 样本模式：

| sample_id | sample_class | 语义 | expr |
|-----------|-------------|------|------|
| `{TYPE}_EXISTING` | `valid_config` | 设备上已存在的对象名称 | `from_topology.<source>.any` |
| `{TYPE}_NOT_EXIST` | `invalid_config` | 设备上不存在的对象名称 | `from_topology.<source>.nonexistent` |
| `{TYPE}_NAME_INVALID` | `invalid_format` | 名称格式非法 | `from_factor(common-network/FAC-CONFIG-NAME).rejected` |

> `FAC-CONFIG-NAME` 的 rejected 样本是所有对象名称格式非法的唯一来源。新增名称格式非法类型时，只需修改 `FAC-CONFIG-NAME`，所有 `object_instance` 因子自动生效。

---

## 5. 样本用途规则

### 5.1 applicability 语义

| applicability 取值 | 含义 |
|-------------------|------|
| `config_test: accepted` | 该样本可作为合法配置值 → 生成配置正向用例 |
| `config_test: rejected` | 该样本预期被配置拒绝 → **只**生成配置反向用例 |
| `config_test: not_applicable` | 该因子不参与配置合法性覆盖 |
| `function_test: positive` | 预期命中/匹配的输入 |
| `function_test: negative` | 可执行但预期不命中的输入 |
| `function_test: precondition` | 作为功能用例的合法前置 |
| `function_test: not_applicable` | 不用于功能测试 |
| `function_test: preferred_precondition` | 推荐的合法前置（多个合法值时优先选） |

### 5.2 最低消费规则

- ❌ `rejected_config_samples` **不得**作为 function_test 的 precondition、positive 或 negative
- ❌ `negative_function` 表示可执行但预期不命中，**不表示配置非法**
- ❌ `OBJ-PR-TRAFFIC` 下的 `FAC-PKT-*` 默认 **不参与** 配置合法性覆盖
- ✅ 配置字段合法性优先查找 `OBJ-PR-RULE`、`OBJ-GENERIC-CONFIG` 或其他配置对象因子
- ✅ oracle 因子**只**用于结果判定，**不**生成配置输入

---

## 6. 约束规则

### 6.1 约束类型

| 约束类别 | 目的 | 失败处理 |
|----------|------|----------|
| 结构约束 | 防止互斥因子同时出现，或 required 因子缺失 | 阻断该组合，回到因子选择阶段 |
| 值域约束 | 防止选择不在当前上下文中的取值 | 裁剪非法值，记录覆盖原因 |
| 样本用途约束 | 防止配置拒绝样本进入功能前置 | 阻断该样本绑定，要求重新选样 |
| 职责边界约束 | 防止运行时报文因子承担配置字段合法性 | 跳过配置覆盖检查，定位到对应配置字段因子 |

### 6.2 约束关联类型

| 关联类型 | YAML 载体 | 示例 |
|----------|-----------|------|
| 适用条件 | `applicable_when` | `FAC-L3-NH-IF-TYPE` 只在 `FAC-L3-EGRESS-MODE == next-hop` 时适用 |
| 必选关系 | `constraints.require` | 下一跳模式必须选择 `FAC-L3-NH-IF-TYPE` |
| 互斥关系 | `constraints.forbid` | 下一跳模式禁止 `FAC-L3-OUTIF-TYPE` |
| 取值裁剪 | `constraints.allowed_values` | 出接口模式只允许 tunnel / pppoe |

---

## 7. 拓扑实例边界 🚫

> 以下对象**绝对不能**写入因子库的 `values`、`sample_id`、`materialized_value`、`sample_definitions` 或 `factor_groups`：

| 禁止对象 | 正确去向 |
|----------|----------|
| `DUT.port1`、`DUT.port2`、`TG.port1` | LC `topology_bindings.device_id/port_id` |
| `DUT.port1<->TG.port1`、`LINK-WAN-01` | LC `topology_bindings.link_id` |
| 项目拓扑图中的真实入口/出口端口 | `analysis/scenarios/confirmed-scenarios.md` 和 PC 物化字段 |

### 可以进入因子库的对象

| 对象 | 示例 |
|------|------|
| 接口类型 | physical、sub-interface、aggregate、tunnel |
| 接口能力 | l3-capable、not-l3-capable |
| 出口选择模式 | next-hop、out-interface |

---

## 8. 命名规范

### 8.1 factor_id

```
FAC-{DOMAIN}-{SHORT-NAME}
```

- 前缀统一 `FAC-`
- DOMAIN 用大写缩写（`L3`、`PR`、`NET`、`HA`、`DFX`、`PKT` 等）
- 分隔符统一用连字符 `-`

示例：
- `FAC-L3-EGRESS-MODE` — L3 域出口模式
- `FAC-PR-RULE-SRC-IP` — 策略路由规则源 IP
- `FAC-PKT-DST-PORT` — 报文目的端口
- `FAC-HA-SYNC-STATE` — HA 同步状态
- `FAC-EXPECTED-MATCH-RESULT` — 预期命中结果

### 8.2 owner_object

```
OBJ-{DOMAIN}-{NAME}
```

示例：
- `OBJ-PR-RULE` — 策略路由规则
- `OBJ-PR-TRAFFIC` — 策略路由业务流量
- `OBJ-PR-EGRESS` — 策略路由三层转发出口
- `OBJ-PR-HA` — 策略路由 HA
- `OBJ-PR-DFX` — 策略路由 DFX
- `OBJ-GENERIC-CONFIG` — 通用配置对象

### 8.3 sample_id

```
{PREFIX}_{CATEGORY}_{DESCRIPTOR}
```

示例：
- `SRC_IP_MATCH` — 源 IP 匹配
- `WEIGHT_BELOW_MIN` — 权重低于最小值
- `NAME_MIXED_CHARSET` — 名称混合字符集
- `TRAFFIC_TCP_MATCH` — TCP 流量匹配

### 8.4 factor_group_id

```
{CONTEXT}_{DOMAIN}_{FEATURE}
```

示例：
- `L3_EGRESS_NEXT_HOP` — L3 出口下一跳模式
- `TRAFFIC_MATCHING` — 流量匹配
- `CONFIG_FIELD_VALIDITY` — 配置字段合法性
- `HA_POLICY_ROUTE` — HA 策略路由

---

## 9. 生命周期

```text
proposed → candidate → active
                    ↘ rejected
active → deprecated
```

研究区中的因子状态：

| 状态 | 含义 | 何时使用 |
|------|------|----------|
| `proposed` | 从原始材料提取，尚未完整建模 | 刚提取到 `_proposals/` |
| `candidate` | 已完成建模，待评审 | 写入 `<library>/factor-library.yaml` |
| `active` | 已评审通过，可被消费 | 迁移到发布区后 |
| `deprecated` | 不再使用，保留追溯 | 合并或替换后 |
| `rejected` | 不适合作为公共因子 | 判定为领域特化或不满足复用条件 |

---

## 10. 自检清单

写完一个因子后，逐项检查：

1. [ ] `factor_id` 全局唯一、命名规范
2. [ ] 6 问全部有明确答案
3. [ ] `applicable_when` 不是 `always` 时，条件表达式能否被机器解析
4. [ ] 值域完整（enum 有 values + display_values，range 有 domain_expr）
5. [ ] sample_definitions 覆盖正向和反向（如适用）
6. [ ] usage_profiles 正确分配样本用途
7. [ ] rejected samples 没有混入 function precondition
8. [ ] `FAC-PKT-*` 声明了 `config_test: not_applicable`
9. [ ] 不含真实设备端口或链路实例
10. [ ] oracle 因子没有 config_test accepted/rejected 样本
