# 公共因子库

## 定位

本目录是 `ptm-team` 公共因子库 canonical source。因子库是仓库级 `resource`，不是任一 Agent 或 Skill 的私有资产。`ptm-tde` 通过 `resource/component-resource-links.yaml` 声明消费关系；后续其他 Agent / Skill 也可复用同一公共库。

安装 `ptm-tde` agent 时，安装器会将关联因子库同步安装到用户级公共资源目录：

```text
~/.ptm-team/resource/factor-libraries/
```

也可通过 `PTM_TEAM_RESOURCE_HOME` 指向团队共享资源目录。

## 目录

```text
resource/factor-libraries/
├── index.yaml
├── _proposals/
├── common-network/
└── ngfw-policy-routing/
```

## 核心对象

| 对象 | 位置 | 职责 |
|---|---|---|
| 因子库索引 | `index.yaml` | 列出所有公共库、版本、状态、路径和兼容消费者 |
| 因子库主文件 | `<library>/factor-library.yaml` | 机器可读事实源，供安装器、ptm-tde 和其他消费者读取 |
| 人读说明 | `<library>/factor-library.md` | 以表格说明因子、样本、约束和消费规则 |
| 因子组说明 | `<library>/factor-groups.md` | 说明因子组合、覆盖目标和场景边界 |
| 变更记录 | `<library>/factor-change-log.md` | 记录新增、拆分、合并、废弃和 schema 变更 |
| 候选提案 | `_proposals/` 或项目 `analysis/factor-usage/candidate-factor-proposals.yaml` | 尚未进入公共主库的候选因子 |

## 因子建模原则

公共因子库只归档可跨项目复用的测试设计变量。一个因子必须回答清楚以下问题：

| 问题 | 字段 | 判断规则 |
|---|---|---|
| 它描述什么对象 | `owner_object` | 配置对象、运行时流量、状态、DFX、HA 等对象必须分清 |
| 它在设计中起什么作用 | `factor_kind` / `design_role` | driver 用于展开设计，constraint 用于裁剪组合，oracle 用于判定结果 |
| 它的值域是什么 | `domain_model` / `value_type` / `values` / `domain_expr` | enum、range、string_pattern、ip_address、state 等必须可被机器解析 |
| 它何时适用 | `applicable_when` | 适用条件必须显式写出，不能靠名称推断 |
| 它服务哪些方法 | `downstream_methods` | 映射到 D-Data、P-Parameter、C-Combination、S-State、oracle-design 等下游设计方法 |
| 它是否可复用 | `reuse_policy` / `status` | active 因子可被项目 lock；deprecated 因子只保留追溯 |

配置字段因子和运行时输入因子必须分开建模：

| 类型 | 典型 owner_object | 样本职责 | 示例 |
|---|---|---|---|
| 配置字段因子 | `OBJ-PR-RULE`、`OBJ-GENERIC-CONFIG` | 生成 accepted / rejected 配置样本；accepted 样本可作为功能前置 | `FAC-PR-RULE-SRC-IP`、`FAC-CONFIG-NAME` |
| 运行时输入因子 | `OBJ-PR-TRAFFIC` | 生成 positive / negative 功能流量；`config_test` 明确为 `not_applicable` | `FAC-PKT-SRC-IP`、`FAC-PKT-DST-PORT` |
| 状态因子 | 业务状态对象 | 描述启用、不可达、恢复、同步等状态变化 | `FAC-L3-REACHABILITY`、`FAC-HA-SYNC-STATE` |
| oracle 因子 | 被验证对象 | 描述预期结果，不作为输入配置 | `FAC-EXPECTED-MATCH-RESULT`、`FAC-L3-EXPECTED-FWD-PATH` |

### 与拓扑实例的边界

接口类型、接口能力、出口模式、链路能力等可复用概念可以建模为公共因子或约束；项目中的真实设备、真实端口和真实 link 实例不是公共因子。

| 对象 | 是否可进入公共因子库 | 原因 | 示例 |
|---|---|---|---|
| 接口类型 | 可以 | 跨项目可复用，适合作为值域或能力矩阵 | physical、sub-interface、aggregate、tunnel |
| 接口能力 | 可以 | 可复用约束或 capability matrix | l3-capable、not-l3-capable |
| 出口选择模式 | 可以 | 可复用业务变量 | next-hop、out-interface |
| 真实设备端口 | 不可以 | 项目拓扑实例，只能来自已确认场景 | `DUT.port1`、`TG.port1` |
| 真实链路实例 | 不可以 | 项目组网实例，不能跨项目复用 | `DUT.port1<->TG.port1`、`LINK-WAN-01` |

真实组网对象必须通过 `topology_role_refs -> topology_bindings -> PC materialization` 链路流转；不得写入公共因子 `values`、`sample_id`、样例值或 `factor_group`。

## 生产流程

公共因子库生产采用固定闭环。生产阶段的目标不是直接生成测试用例，而是把可复用变量、值域、样本和约束沉淀为公共知识：

1. 来源采集：从需求、规格、场景、Operation Path、CAE、LC/TD、历史 PC、缺陷和工具能力中采集候选变量。
2. 候选建模：先写入项目 `analysis/factor-usage/candidate-factor-proposals.yaml` 或公共 `_proposals/`。
3. 去重归一：按 `factor_id / factor_name / aliases / owner_object / factor_group / domain_model` 查重。
4. 处理判定：只能判定为 `reuse / extend / new_factor / new_group / reject / defer`。
5. 因子设计：补齐类型、角色、对象、值域、样本、上下文、约束、下游方法和生命周期状态。
6. 评审激活：通过评审后从 `candidate` 变为 `active`。
7. 发布归档：更新 `factor-library.yaml`、说明文档、change log、`index.yaml` 版本和 checksum，必要时生成 snapshot。

生产时必须同时更新机器文件和人读文件：

| 变更类型 | 必改文件 | 校验重点 |
|---|---|---|
| 新增因子 | `factor-library.yaml`、`factor-library.md`、`factor-change-log.md` | `factor_id` 唯一，值域和样本完整 |
| 扩展取值 | `factor-library.yaml`、`factor-library.md`、`factor-change-log.md` | 新值是否影响约束、因子组和下游方法 |
| 新增样本 | `factor-library.yaml`、`factor-library.md` | `config_test` 与 `function_test` 不能混用 |
| 新增约束 | `factor-library.yaml`、`factor-library.md` | require / forbid / allowed_values 是否引用有效因子 |
| 新增因子组 | `factor-library.yaml`、`factor-groups.md`、`factor-change-log.md` | 覆盖目标、适用场景和消费方法是否明确 |
| 拆分/合并因子 | `factor-library.yaml`、`factor-library.md`、`factor-groups.md`、`factor-change-log.md` | 旧口径、替代因子和迁移原因必须可追溯 |

## 更新流程

项目运行期间发现公共库不足时，`ptm-tde` 只能在项目中生成候选提案，不得直接修改公共主库。

公共库维护者从项目提案回流更新：

1. 收集 `analysis/factor-usage/candidate-factor-proposals.yaml`。
2. 合并同类提案并执行去重归一。
3. 确定目标库：通用因子进入 `common-network`，领域因子进入对应领域库。
4. 选择变更类型：`new_factor / extend_factor_values / extend_factor_samples / extend_usage_profiles / add_constraints / new_factor_group / extend_factor_group / deprecate_factor / merge_factors / split_factor / schema_change`。
5. 更新目标库和 `factor-change-log.md`。
6. 更新 `index.yaml` 的版本、状态和 checksum。

## 消费流程

`ptm-tde` 消费公共因子库时采用“锁定、绑定、物化、回流”的过程：

1. 安装阶段：安装器根据 `resource/component-resource-links.yaml` 把与 `ptm-tde` 关联的公共库安装到资源目录。
2. 项目初始化：读取 `index.yaml` 和目标库主文件，生成项目 `analysis/factor-usage/factor-library-lock.yaml`，锁定库版本和 checksum。
3. M / LC / TD 阶段：使用 `factor_id`、`factor_group`、`sample_id` 和 `usage_profiles` 组织测试设计，不急于物化具体值。
4. 下游 Skill 绑定：在 `analysis/factor-usage/factor-bindings.md` 记录每个测试点使用了哪些因子、样本、约束和 oracle。
5. 拓扑并行绑定：真实设备、端口和链路不进入 `factor-bindings.md`；它们由 LC `topology_bindings` 从 `analysis/scenarios/confirmed-scenarios.md` 绑定。
6. PC 阶段：根据 `expr`、`materialized_value` 或 `materialization` 把因子样本转成具体配置、流量、状态或断言；根据 `topology_bindings` 把拓扑角色物化为真实设备、端口和链路。
7. 覆盖核查：根据因子组和约束检查是否覆盖 required factors、正向/反向样本、状态变化和 oracle；根据 `topology_bindings` 检查 PC 真实端口是否可回链。
8. 候选回流：项目发现新因子或新值域时，只写入 `candidate-factor-proposals.yaml`，由公共库维护者评审后归档。

消费时的职责边界如下：

| 输入类型 | ptm-tde 处理方式 | 下游结果 |
|---|---|---|
| `config_test: accepted` | 可生成配置正向用例，也可作为功能前置 | 有效配置片段或前置条件 |
| `config_test: rejected` | 只生成配置反向用例 | 期望下发失败或校验失败 |
| `function_test: positive` | 生成预期命中的功能输入 | 正向流量、正向状态或正向操作 |
| `function_test: negative` | 生成可执行但预期不命中的功能输入 | 反向流量或反向状态 |
| `function_test: precondition` | 作为功能用例的合法前置 | 不单独作为验证目标 |
| `config_test: not_applicable` | 跳过配置合法性覆盖检查 | 只参与功能、状态或 oracle 设计 |

例如 `FAC-PKT-SRC-IP` 是报文运行时输入，`accepted config samples = n/a` 或 `config_test: not_applicable` 表示它不进入配置字段合法性分析；配置源 IP 合法性应由 `FAC-PR-RULE-SRC-IP` 承载。

`DUT.port1`、`TG.port1`、`DUT.port1<->TG.port1` 这类对象不属于上述任何输入类型；它们不是样本，也不是因子值，只能作为拓扑绑定结果进入 PC 的组网描述、组网约束或测试步骤。

## 关联关系

因子之间的关联必须显式沉淀在主库中，不能只写在自然语言说明里：

| 关联类型 | 载体 | 说明 | 示例 |
|---|---|---|---|
| 适用条件 | `applicable_when` | 某因子只在另一个因子取特定值时展开 | `FAC-L3-NH-IF-TYPE` 只在 `FAC-L3-EGRESS-MODE == next-hop` 时适用 |
| 必选关系 | `constraints.require` | 触发条件满足时必须选择某因子 | 下一跳模式必须选择 `FAC-L3-NH-IF-TYPE` |
| 互斥关系 | `constraints.forbid` | 触发条件满足时禁止选择某因子 | 下一跳模式禁止 `FAC-L3-OUTIF-TYPE` |
| 取值裁剪 | `constraints.allowed_values` | 限定某上下文中的合法取值集合 | 出接口模式只允许 tunnel / pppoe |
| 能力矩阵 | `capability_matrices` | 以矩阵形式表达对象能力、接口能力或版本能力 | 三层转发出口接口能力矩阵 |
| 因子组 | `factor_groups` | 将一组因子绑定为覆盖目标 | `TRAFFIC_MATCHING` 聚合流量层级、IP、服务、应用和预期命中 |
| 样本配置 | `usage_profiles` | 规定哪些样本用于配置、功能、前置或反向 | `CONFIG_FIELD_VALIDITY` 要求 accepted/rejected 配置样本 |
| oracle 关联 | `design_role: oracle` | 把输入条件与预期结果绑定 | `FAC-EXPECTED-MATCH-RESULT` 判定 hit / miss |

## 约束规则

公共库约束分为四类，消费者必须在生成测试点前执行裁剪：

| 约束类别 | 目的 | 失败处理 |
|---|---|---|
| 结构约束 | 防止互斥因子同时出现，或 required 因子缺失 | 阻断该组合，回到因子选择阶段 |
| 值域约束 | 防止选择不在当前上下文中的取值 | 裁剪非法值，记录覆盖原因 |
| 样本用途约束 | 防止配置拒绝样本进入功能前置，或功能反向样本进入配置非法测试 | 阻断该样本绑定，要求重新选样 |
| 职责边界约束 | 防止运行时报文因子承担配置字段合法性 | 跳过配置覆盖检查，定位到对应配置字段因子 |

最低消费规则：

- `rejected_config_samples` 不得作为 `function_test` 的 precondition、positive 或 negative。
- `negative_function` 表示可执行但预期不命中，不表示配置非法。
- `OBJ-PR-TRAFFIC` 下的 `FAC-PKT-*` 默认不参与配置合法性覆盖，除非库中显式声明相反规则。
- 配置字段合法性优先查找 `OBJ-PR-RULE`、`OBJ-GENERIC-CONFIG` 或其他配置对象因子。
- oracle 因子只用于结果判定，不生成配置输入。

## 生命周期

```text
proposed -> candidate -> active
                    \-> rejected
active -> deprecated
```

- `candidate`：可用于分析草稿，但进入最终 PC 前必须确认或记录风险。
- `active`：可被项目正式 lock 和消费。
- `deprecated`：不得用于新设计；历史项目可保留引用，并通过 change log 指向替代因子。
- 删除公共因子默认禁止；用 `deprecated` 保留追溯。

## 项目消费

项目中只保存消费记录：

```text
analysis/factor-usage/
├── factor-library-lock.yaml
├── factor-bindings.md
├── candidate-factor-proposals.yaml
└── factor-resolution-report.md
```

`factor-library-lock.yaml` 锁定公共库版本和 checksum；`factor-bindings.md` 是下游 Skill 的正式输入；`candidate-factor-proposals.yaml` 是回流公共库的唯一项目级入口。

项目若需要记录真实组网对象，使用场景与拓扑绑定产物：

```text
analysis/scenarios/confirmed-scenarios.md
analysis/integration/logic-cases.md  # topology_bindings
design/pc/<basename>.md              # PC materialization
```

`factor_bindings` 与 `topology_bindings` 是并行契约：前者服务公共测试因子，后者服务真实组网对象，不得互相替代。
