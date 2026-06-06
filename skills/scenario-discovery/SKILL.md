---
name: scenario-discovery
description: >-
  通过只读 MCP staged query、项目参考材料、功能场景种子、TGFW 组网集合和用户补充事实，
  重新发现并收敛可直接支撑逻辑用例写作的部署型 Scenario Chain / Topology / atomic-ops / Knowledge Reference。
  触发词包括：场景分析、搜索场景、应用场景、场景发现、场景再发现、scenario discovery。
  适用场景：MFQ 分析的第二步（scenario 阶段），尤其适用于把 functional scenario seed 重构为部署型场景发现产物。
argument-hint: "特性名称或输入材料路径"
user-invokable: true
status: active
---

## 目标

生成**准确优先、禁止脑补**的部署型场景发现结果。功能初稿不可直接作为最终场景；必须经过输入文档类型识别、场景再发现、头脑风暴、范围收敛、Topology 锚定、atomic-ops 原子操作映射、Seed-to-Scenario Mapping 和输出质量检查。

每个场景必须能落成：

- Scenario Chain（场景目标 / 原理依据 / 前置条件链 / 最小逻辑链）
- Topology（`Topology / Device / Port / Link` + `topology_ref`）
- precondition_operations（前置条件的原子操作拆分）
- atomic_operations（主流程原子操作）
- observation_points（观察点与预期状态）
- atomic-ops（项目内唯一原子操作引用对象，直接引用 `op_id`）
- Knowledge Reference（只读知识引用）
- Existing Tool Usage Seed（已有工具使用种子）
- Tool Abstraction Draft（工具抽象草案）
- Confirmation Gaps（待用户补充的问题）

## 触发场景

- 用户要求做场景分析、应用场景发现、场景再发现或部署型场景整理。
- 输入是 raw requirement、functional scenario seed、deployment scenario draft 或 confirmed scenario artifact，需要判断下一步是发现、重构、补全还是复核。
- 项目存在 `kym/scenarios/scenario-analysis.md` 这类功能初稿，需要重组为 `kym/scenarios/scenario-deployment-<feature>.md` 这类部署型场景产物。
- 项目存在 `input/TGFW测试组网图集合.md`，需要基于 TGFW 测试组网图集合选择、映射和验证拓扑。
- 项目内统一使用 atomic-ops 原子操作，需要直接引用 `op_id`，并暴露能力状态和调用/观测契约。

## 不适用边界

- 不替代 feature-parser、logic-case 写作、测试数据生成或工具实现。
- 不把未经确认的功能点清单、会议纪要、接口片段直接发布为已确认场景。
- 不创建或修改 MCP 知识库，不维护索引，不写回外部系统。
- 不发明 API、CLI、atomic-ops、组网、设备端口、链路、性能容量指标或项目事实。
- 不在用户明确限制外扩展范围；例如用户声明只做 IPv4 时，IPv6 必须进入 `out_of_scope_candidates`。

## 输入

按以下优先级读取输入，不存在则记录为 `missing`，不得静默跳过：

1. 用户明确给出的特性名称、范围约束、目标输出形态和确认事实。
2. `kym/feature-input/` 中的需求、目录材料和原始输入。
3. 项目确认的目标形态样例：优先读取 `kym/scenarios/scenario-deployment-policy-route.md`；存在时先学习其结构，不复制未适用内容。
4. 功能场景种子：例如 `kym/scenarios/scenario-analysis.md`。
5. TGFW 组网集合：若 `input/TGFW测试组网图集合.md` 存在，必须读取并优先使用其拓扑。
6. 只读 MCP staged query 结果。
7. 用户补充的 atomic-ops 能力说明；REST API、CLI、tool-method 只能作为 atomic-op 的底层调用契约或实现通道，不作为独立引用类型。
8. Web 搜索仅在知识缺失或用户明确要求时作为补充参考。

## 输入文档类型识别

开始分析前必须输出 `input_document_classification`，逐份材料判定类型、证据和处理动作。

| 类型 | 判定信号 | 处理动作 |
|------|----------|----------|
| `raw_requirement` | 描述需求、背景、限制、验收口径，缺少场景结构 | 进入完整场景发现和范围收敛 |
| `functional_scenario_seed` | 以功能点、功能流程、操作步骤或用例雏形为主，缺少部署维度、Topology、atomic-ops 或验证链 | 进入场景再发现，不得直接转最终场景 |
| `deployment_scenario_draft` | 已包含部署目标、Topology、场景矩阵、atomic-ops、Knowledge Reference 或 Confirmation Gaps，但仍有缺口 | 进入补全、校验和收敛 |
| `confirmed_scenario_artifact` | 用户或项目显式确认，且包含确认记录、稳定场景编号、拓扑和 atomic-ops | 仅做一致性复核；新增内容必须标记为候选或缺口 |

硬规则：

- 功能初稿不可直接作为最终输出。
- `functional_scenario_seed` 必须进入场景再发现、头脑风暴、部署重构和 Seed-to-Scenario Mapping。
- 禁止 seed one-to-one rewriting；不得把一个功能点机械改名为一个最终场景。
- `confirmed_scenario_artifact` 的一致性复核必须覆盖 `normal_path.necessity` 取值、子步骤编号连续性、`abnormal_path.related_normal_steps` 可解析性、`minimal_logic_chain` 与正常路径必要性约束一致性、`atomic_operations` 覆盖必要步骤且未把可选步骤误标为必选。
- 无法判定类型时必须写入 `confirmation_gaps` 并说明需要用户确认的判定依据。

## 项目目标形态学习

若项目确认的 `kym/scenarios/scenario-deployment-policy-route.md` 存在，先学习其输出形态，并将以下结构作为首选输出骨架：

1. Document Positioning（文档定位）
2. ptm-tde Deliverable Statement（面向 ptm-tde 的交付说明）
3. Scenario Dimension Overview（场景维度总览）
4. Topology Model / Topology Catalog
5. Scenario List（部署型场景列表）
6. Topology Source Mapping（拓扑来源映射）
7. Scenario Details（场景详情）
8. ptm-tde Scenario Discovery Structured Supplement（结构化补充）
9. Atomic Operation Summary（原子操作摘要）
10. atomic-ops
11. Knowledge References
12. Existing Tool Usage Seed
13. Tool Abstraction Draft
14. Confirmation Gaps

学习规则：

- 只学习结构、字段粒度、命名风格和确认缺口表达，不复制特定项目事实。
- 当用户提供更高优先级约束时，以用户约束覆盖样例结构。
- 若样例不存在，仍按本 Skill 的双层输出格式生成部署型场景产物。

## 核心原则

1. **先识别输入再展开**：必须先完成输入文档类型识别，再决定发现、重构、补全或复核路径。
2. **准确优先**：禁止根据模糊材料补齐“看起来完整”的逻辑链。
3. **功能种子必须重构**：functional scenario seed 只能作为发现素材，不能直接成为最终场景。
4. **范围先收敛再扩展**：显式用户约束、项目记忆和确认文档优先；超出范围的候选进入 `out_of_scope_candidates`。
5. **知识库只读**：只允许引用 MCP 查询结果，不做写回、索引维护或入库。
6. **组网先锚定再回链**：场景依赖组网时，必须先产出 Topology Catalog，并为场景写入 `topology_ref`。
7. **atomic-ops 显式建模**：项目内统一使用 atomic-ops 原子操作；REST API、CLI Tool、Tool Method 只能作为 atomic-op 的 `invoke_contract`、`observe_contract` 或实现通道描述。
8. **缺口显式暴露**：已有工具不能满足场景时，输出 Tool Abstraction Draft，而不是虚构可执行接口。

## 知识查询策略（只读 staged query）

按以下固定顺序查询知识参考：

1. 领域主场景（`domain-scenarios`）
2. 特性场景（`feature-scenarios`）
3. 特性主功能（`feature-functions`）

查询命令示例：`uv run --python 3.11 python scripts/mcp_query_client.py --stage all --domain firewall --feature "<特性名称>"`

三态解释：

- `success` / `resolved`：成功返回可引用知识。
- `knowledge_missing` / `missing`：接口可用，但当前阶段知识缺失。
- `interface_unavailable` / `unavailable`：MCP 接口不可用或未配置。

`knowledge_missing` 与 `interface_unavailable` 必须区分，后续提问和回退策略不同。

## 执行步骤

### 步骤 1：信息收集与输入分类

1. 读取用户输入、`kym/feature-input/`、功能种子、部署型样例、TGFW 组网集合和 atomic-ops 说明。
2. 输出 `input_document_classification`，说明每份输入的类型、证据、处理动作和不确定项。
3. 调用只读 MCP staged query；查询失败时保留三态结果，不伪造知识。
4. 识别显式范围约束，生成 `scope_constraints` 与 `out_of_scope_candidates`。

### 步骤 2：场景再发现与头脑风暴

对 raw requirement 和 functional scenario seed 必须执行场景再发现。头脑风暴维度至少覆盖：

| 维度 | 必须回答的问题 |
|------|----------------|
| primary scenario | 核心部署目标是什么，最小可验收路径是什么 |
| extended scenario | 哪些扩展路径可增加覆盖但不改变核心目标 |
| lifecycle | 创建、启用、修改、停用、删除、回滚如何影响场景 |
| reliability | HA、链路故障、配置恢复、状态保持如何验证 |
| performance | 性能、容量、并发、规模边界如何扩展 |
| usability | 运维可操作性、误操作恢复、诊断入口如何体现 |
| configuration order | 配置顺序、依赖资源和前置状态如何约束 |
| abnormal operation | 非法参数、缺失依赖、冲突配置、权限失败、状态不一致、观测缺失如何暴露；异常项必须追溯到正常路径中的具体步骤或子步骤 |
| TOPO | 场景需要哪个拓扑、为什么需要该拓扑 |
| interface shape | UI、REST API、CLI、tool-method 与 atomic-ops 的边界是什么；哪些接口只能作为 atomic-op 的底层实现通道 |
| exit action | 场景结束时如何清理、回滚或进入稳定状态 |

#### 方法论参考：Superpowers Brainstorming 与 GSD Discuss-Phase

在执行头脑风暴各维度时，遵循以下从 Superpowers Brainstorming（`obra/superpowers`）和 GSD Discuss-Phase（`gsd-build/get-shit-done`）提炼的核心原则：

**澄清问题先行**：在执行每个维度前，先提出至少一个澄清问题，确认理解正确后再展开分析。禁止跳过澄清直接进入细节。

**替代方案探索**：对每个维度的关键设计决策，提出 2-3 个替代方案，包含权衡分析和推荐理由。禁止直接跳到单一方案。

**增量验证**：每完成一个场景的完整分析后暂停，使用 §场景确认规则 中的三选项格式请求用户确认。禁止在未确认的情况下自动进入下一个场景。

**决策可追溯**：所有确认的决策写入对应产物章节，不依赖对话上下文传递；下游消费者（M/F/Q 分析、LC 写作、PC 生成）应能直接从产物中获取决策而不必回溯对话。

**范围护栏**：对超出当前范围但有价值的想法，写入 `out_of_scope_candidates` 或 `Deferred Ideas`，不丢失、不执行。讨论聚焦于"如何实现已确定的范围"，而非"是否应该增加新能力"。

**独立小上下文**：每个场景的 Scenario Chain、atomic-ops 和 Knowledge Reference 应为封闭的独立上下文，可被下游 M/F/Q 分析独立消费而无需重新加载全部场景。

### 步骤 3：策略路由专项维度

当特性属于策略路由、PBR、policy route 或用户提供的材料包含策略路由语义时，必须额外覆盖：

| 维度 | 发现要求 |
|------|----------|
| match dimensions | 源/目的地址、协议、端口、应用、用户、服务、时间、优先级等匹配条件 |
| ingress interface shape | 入接口、VLAN、子接口、聚合口、隧道口、PPPoE 等入口形态 |
| forwarding action | 下一跳、出接口、负载、备份、丢弃、回退路由等转发动作 |
| egress mode/interface type | 普通三层口、HA、PPPoE、链路聚合、交换侧连接等出口形态 |
| risk dimensions | 规则顺序、冲突匹配、链路失效、容量瓶颈、维护窗口、误配置恢复 |

策略路由场景中，`forwarding action` 与 `match dimensions` 必须拆分建模：

- `forwarding action` 通常是必要步骤，例如配置下一跳、出接口或回退路径。
- `match dimensions` 通常是选择组，必须至少选择一项，不能全部为空或全部 any；只有产品明确支持全流量匹配且本场景目标就是验证全匹配时，才允许把全匹配作为已确认目标。
- 地址对象、服务对象、时间对象、应用对象属于匹配条件的支撑对象，必要性通常是 `可选`，取决于规则是否引用对象。
- 不得把“配置策略路由”写成不可拆分的大步骤；必须区分转发动作用于决定去哪里、匹配条件用于决定哪些流量命中。

### 步骤 4：范围收敛

1. 将用户显式限制、项目确认材料、已确认目标形态和 Knowledge Reference 作为收敛依据。
2. 将不在范围内但有价值的候选写入 `out_of_scope_candidates`，字段包含 `candidate`、`reason`、`source`、`reconsider_condition`。
3. 对用户已排除的内容不得在最终场景中保留。例如用户声明只做 IPv4 时，IPv6 场景只允许出现在 `out_of_scope_candidates`。
4. 对范围不确定项写入 `confirmation_gaps`，不得用默认行业经验替代确认。

### 步骤 5：TGFW测试组网图集合规则

若 `input/TGFW测试组网图集合.md` 存在：

1. 必须读取并建立 `Topology Catalog`，优先使用集合中的拓扑。
2. 必须输出 `Topology Source Mapping`，说明每个 `topology_ref` 来源于集合中的哪一项、为何适配哪些场景。
3. 每个依赖组网的场景必须包含 `topology_ref`、来源、Mermaid、设备表、端口表和链路表。
4. 不得发明集合外拓扑；确需新增时只能进入 `confirmation_gaps`，不能作为已确认拓扑使用。
5. 默认策略路由拓扑选择：
   - basic / match / order / maintenance / abnormal：`node2_dut1_tg1_link3`
   - HA：`node4_dut2_tg1_sw2_link7`
   - performance / capacity：`node2_dut1_tg1_link5`
   - PPPoE egress：`node3_dut1_tg1_pppoe_link4`，仅作为 extension suggestion，除非用户确认纳入范围

Topology 最低字段：

| 字段 | 说明 |
|------|------|
| `topology_id` | 组网编号，优先复用 TGFW 集合标识 |
| `source` | `TGFW测试组网图集合.md`、用户确认材料或 `confirmation_gap` |
| `devices[]` | 设备列表，至少包含 `device_id` / `kind` / `ports[]` |
| `ports[]` | 端口清单，至少包含 `port_id` / `device_id` / `role` |
| `links[]` | 链路清单，至少包含 `link_id` / `endpoints[2]` |
| `validation_status` | `valid / needs-confirmation / invalid` |

最低校验规则：

1. 每条 `Link.endpoints` 必须恰好为两个端口。
2. `device_id` / `port_id` / `link_id` 在同一 `topology_id` 内唯一。
3. `DUT` 至少包含两个可参与业务的端口。
4. atomic-op 的 `target` 若指向设备或端口，必须可解析到 `DUT<n>` 或 `DUT<n>.Port<n>`。

### 步骤 6：Seed-to-Scenario Mapping

当输入包含 functional scenario seed 时，必须输出 Seed-to-Scenario Mapping：

| 字段 | 说明 |
|------|------|
| `seed_ref` | 功能种子编号、标题或来源段落 |
| `seed_type` | 功能点、流程、异常、约束、观察点、工具线索等 |
| `deployment_scenario_refs` | 重构后关联的部署型场景编号，允许一对多或多对一 |
| `transformation` | `split / merge / expand / narrow / out_of_scope / confirmation_gap` |
| `rationale` | 为什么这样映射 |
| `lost_or_added_dimension` | 相比 seed 删除、合并或新增的部署维度 |

规则：

- 功能场景到部署场景可以拆分、合并、扩展或收敛，必须解释转换理由。
- 禁止按 seed 顺序生成同数量最终场景。
- 未被使用的 seed 必须进入 `out_of_scope_candidates` 或 `confirmation_gaps`，不得消失。

### 步骤 7：构建 Scenario Chain

对每个候选部署场景输出以下字段：

| 字段 | 说明 |
|------|------|
| `scenario_goal` | 场景目标 |
| `principle` | 场景原理依据 / 业务依据 |
| `preconditions` | 使用该场景前必须成立的条件 |
| `topology_ref` | 关联 Topology 编号；若场景不依赖组网则填 `n/a` 并说明理由 |
| `precondition_operations` | 将前置条件拆成可执行原子操作 |
| `atomic_operations` | 主流程原子操作序列 |
| `observation_points` | 每个关键节点的观察点 |
| `expected_state` | 每个关键节点对应的预期状态 |
| `minimal_logic_chain` | 最小逻辑链（可直接转后续 LC 步骤骨架） |
| `data_overlay_slots` | 后续可叠加测试数据的位置 |
| `exit_action` | 场景结束、清理、回滚或稳定化动作 |

`minimal_logic_chain` 必须反映 `normal_path` 中的必要性约束：

- `必要` 步骤写成明确链路节点。
- `可选` 步骤必须标记为“按需配置”“按需验证”或说明可跳过条件。
- `至少选择一项` 步骤必须在链路中显式写出选择约束，例如 `P4(至少选择一项策略路由匹配条件)`。
- 不得把可选步骤或选择组改写成线性必做流程。

### 操作路径建模规则

`normal_path` 必须支持大步骤与子步骤两层表达。若一个步骤内包含多个可独立配置、独立选择或独立校验的动作，必须使用 `1.1`、`1.2` 这类子步骤编号，不得把多个动作压缩成不可追溯的描述。

`normal_path` 中每个步骤必须包含：

| 字段 | 说明 |
|------|------|
| `step_id` | 大步骤编号，如 `1`、`2` |
| `sub_step_ids` | 子步骤编号，如 `2.1, 2.2`；无子步骤时可与大步骤一致 |
| `operation` | 操作名称；多个子步骤需逐项列出 |
| `necessity` | `必要` / `可选` / `至少选择一项` |
| `description` | 操作目的、前置依赖、可跳过条件或选择约束 |

`necessity` 只能使用以下取值：

- `必要`：该步骤必须执行，否则场景主链路不成立。
- `可选`：该步骤按环境现状、数据模型或引用关系决定是否执行；例如已有接口、路由、对象或安全策略时可跳过。
- `至少选择一项`：同一大步骤内存在多个并列子步骤，执行时必须从这些子步骤中选择至少一项，不能全部跳过。

当多个子步骤属于同一大步骤时，Markdown 表格可使用 `<br>` 保持在同一行内，避免拆散选择组关系。例如：

| 步骤 | 子步骤 | 操作 | 必要性 | 说明 |
|------|--------|------|--------|------|
| 3 | 3.1<br>3.2 | 配置匹配对象：<br>配置地址对象<br>配置服务对象 | 可选 | 仅当策略路由规则引用地址对象或服务对象时执行 |
| 6 | 6.1<br>6.2<br>6.3<br>6.4 | 配置策略路由匹配条件：<br>配置源地址匹配<br>配置目的地址匹配<br>配置服务匹配<br>配置入接口匹配 | 至少选择一项 | 同一条策略路由规则的匹配条件不能全部跳过 |

`abnormal_path` 必须追溯到 `normal_path` 中的大步骤或子步骤，不能只描述异常现象。每条异常操作至少包含：

| 字段 | 说明 |
|------|------|
| `abnormal_item` | 异常项 |
| `related_normal_steps` | 关联的正常路径步骤或子步骤，如 `2.1, 5.1, 7.2` |
| `input_or_state` | 异常输入、异常状态或触发条件 |
| `expected_handling` | 预期处理、可观测结果或判定标准 |

异常操作路径不得缺少 `related_normal_steps`。若异常无法对应到任何正常步骤，必须说明其来源是前置条件、环境故障、退出动作还是独立风险项，并写入 `confirmation_gaps` 或风险说明。

当 `normal_path` 存在 `可选` 或 `至少选择一项` 步骤时，Structured Supplement 不得丢失选择语义。可通过以下方式表达：

- 在 `minimal_logic_chain` 中写明 `按需` 或 `至少选择一项`。
- 在 `data_overlay_slots` 中标记可变数据位置。
- 在 `atomic_operations.expected_state` 或补充字段中说明选择关系。
- 若工具消费格式暂不支持选择组，必须进入 `confirmation_gaps` 或 `tool_gap_refs`。

`precondition_operations` / `atomic_operations` 最低字段：

| 字段 | 说明 |
|------|------|
| `op_id` | 操作编号；若来自 atomic-ops，直接复用或引用原始 `op_id` |
| `phase` | `precondition` / `main-flow` / `exit` |
| `channel` | UI / REST API / CLI / Tool Method / Manual / atomic-ops；非 atomic-ops 通道必须绑定到某个 atomic-op 的调用或观测契约 |
| `action_object` | 操作对象 |
| `input_params` | 输入参数 |
| `observation_point` | 该操作完成后的观察点 |
| `expected_state` | 该操作完成后的预期状态 |
| `action_source_ref` | 关联 atomic-ops；直接引用 `op_id` |

### 步骤 8：建模 atomic-ops / Knowledge Reference / Tool 输出

#### atomic-ops

对所有 atomic-ops 进行显式建模。本项目中 **atomic-ops 是唯一原子操作引用对象**。REST API、CLI、tool-method 不是独立引用类型，只能作为 atomic-op 的底层调用契约、观测契约或实现通道。

- `source_type` 固定使用 `atomic-ops`。
- `action_source_ref` 直接引用 atomic-ops 的 `op_id`。
- 不得发明 `非 op_id 中间编号` 这类中间编号替代 `op_id`。
- 不得将 `rest-api`、`cli-tool`、`tool-method` 填入 `source_type`。
- `capability_status` 只能为 `ready / gap / unknown`。
- 缺少调用或观测契约时，必须标记为 `gap` 或 `unknown`，并进入 `confirmation_gaps`。

atomic-ops 输出字段：

| 字段 | 说明 |
|------|------|
| `action_source_ref` | atomic-ops 引用；必须直接填 atomic-ops `op_id` |
| `source_type` | 固定为 `atomic-ops` |
| `capability_status` | `ready` / `gap` / `unknown` |
| `invoke_contract` | atomic-op 的调用入口、参数、前置条件；可说明底层 REST API / CLI / tool-method，但不得把它们建模为独立引用对象 |
| `observe_contract` | atomic-op 调用后如何观测结果；可说明底层观测通道 |
| `scenario_refs` | 关联场景 |

UI/Manual 操作可以出现在 `channel` 中；若需要自动化或工具化消费，必须映射到 atomic-op，或进入 Tool Abstraction Draft / Confirmation Gaps。

#### Knowledge Reference

将 MCP staged query 结果保留为：

| 字段 | 说明 |
|------|------|
| `knowledge_type` | `domain-scenarios` / `feature-scenarios` / `feature-functions` |
| `source_ref` | 知识来源标识 |
| `queried_at` | 查询时间 |
| `availability_status` | `resolved` / `missing` / `unavailable` |

#### Existing Tool Usage Seed

若已有工具可用，至少输出：

| 字段 | 说明 |
|------|------|
| `tool_name` | 工具名 |
| `main_usage` | 主要用法 |
| `purpose` | 用途 |
| `scenario_refs` | 适用场景 |
| `action_source_refs` | 依赖的 atomic-ops `op_id` |

#### Tool Abstraction Draft

当现有工具能力不足时，输出：

| 字段 | 说明 |
|------|------|
| `tool_name` | 待抽象工具名称 |
| `target_interface` | API / CLI / method / atomic-ops wrapper |
| `function_desc` | 需要支持的能力 |
| `io_behavior_matrix` | 不同输入 / 输出条件下的处理逻辑 |
| `output_contract` | 输出格式与观察点 |
| `scenario_refs` | 关联场景 |

### 步骤 9：缺口识别与用户确认

以下任一项不确定时，必须生成 `confirmation_gaps` 并暂停确认：

- 输入文档类型无法判定。
- 场景目标、范围边界或部署维度不清楚。
- 功能种子到部署场景的映射不清楚。
- 前置条件、原子操作顺序、退出动作不清楚。
- 观察点或预期状态不清楚。
- TGFW Topology 结构、命名或链路归属不清楚。
- atomic-ops、调用契约或观测契约不清楚。
- MCP 结果为 `missing / unavailable`。
- 现有工具能力不足且 Tool Abstraction Draft 仍缺少输入、输出或错误模型。

#### 决策项格式（源自 GSD Discuss-Phase 方法论）

每个 `confirmation_gaps` 条目必须以**决策项**形式呈现，确保下游消费者和后续确认节点可直接消费而不必回溯对话。决策项最低字段：

| 字段 | 说明 |
|------|------|
| `gap_id` | 缺口编号，如 `GAP-01` |
| `question` | 待确认问题，一句话描述 |
| `recommendation` | 推荐方案及理由 |
| `alternatives[]` | 至少 1 个（2 个为宜）备选方案，每个含方案描述和优劣分析 |
| `impact_surface` | 该决策影响的后续产物（如 M 分析、F 分析、LC 生成、PC 物化） |
| `status` | `open` / `resolved` / `deferred` |

备选方案格式要求：

- 每个备选方案必须包含：方案描述、相比推荐方案的优势（至少 1 条）、相比推荐方案的劣势（至少 1 条）。
- 当推荐方案不可行时，备选方案中必须至少有 1 个可作为回退方案。
- 若某个缺口只有 1 个可行方案（无备选），必须显式声明 `alternatives_reason: "无可行备选"` 并说明原因。

#### 场景确认规则（每个场景独立确认）

> **⛔ HARD-STOP**：每完成一个场景的 Scenario Chain、Topology、atomic-ops 和 Knowledge Reference 分析后，必须暂停并请求用户确认，不得自动进入下一个场景。

每次确认使用标准三选项格式：

```
【确认】场景 S<N>（<场景名称>）分析结果是否正确？

( ) A. 确认 — 场景链路无误，继续展开下一个场景
( ) B. 拒绝 — 分析方向有误，请重新分析本场景
( ) C. 修改: <具体修改内容> — 部分需要调整，输出修改点
```

确认通过后，才能继续展开下一个场景。全部场景确认完成后，汇总所有 `confirmation_gaps` 统一呈现。

#### 决策收集规则

在暂停等待用户确认前，必须收集当前场景的全部 `confirmation_gaps` 条目，以统一的决策清单形式呈现。不得逐条分散确认导致遗漏。

## 输出格式

### 双层输出

最终输出采用双层结构：

1. **Scenario Details**：面向场景阅读和后续 LC 写作，包含场景目标、Topology、前置条件、主流程、观察点、异常路径、退出动作。
2. **ptm-tde Scenario Discovery Structured Supplement**：面向工具化消费，包含分类、矩阵、映射、atomic-ops、知识引用、工具草案、缺口和质量检查。

建议写入 `kym/scenarios/confirmed-scenarios.md` 或用户指定的部署型场景文件，结构如下：

| 一级章节 | 必填内容 |
|----------|----------|
| Document Positioning | 文档定位、适用阶段、输入类型识别摘要 |
| ptm-tde Deliverable Statement | 交付目标、可被下游消费的对象 |
| Scope Constraints | 用户限制、项目约束、`out_of_scope_candidates` |
| Scenario Dimension Overview | 场景再发现维度、策略路由专项维度 |
| Topology Catalog | TGFW 拓扑清单、Mermaid、设备/端口/链路表 |
| Scenario List | 场景编号、名称、类型、`topology_ref`、状态 |
| Topology Source Mapping | 拓扑来源、适配理由、关联场景 |
| Seed-to-Scenario Mapping | 功能种子到部署场景的转换关系 |
| Scenario Details | 每个部署场景的完整链路 |
| Structured Supplement | 结构化补充表 |
| Atomic Operation Summary | 原子操作摘要和 atomic-ops 关联 |
| atomic-ops | 原子操作清单：`action_source_ref / source_type=atomic-ops / capability_status / invoke_contract / observe_contract / scenario_refs` |
| Knowledge References | `resolved / missing / unavailable` 三态结果 |
| Existing Tool Usage Seed | 现有工具用法种子 |
| Tool Abstraction Draft | 工具能力缺口和抽象草案 |
| Confirmation Gaps | 待用户确认问题 |
| 输出质量检查 | 本 Skill 的质量检查结果 |

### Scenario Details 最低字段

| 字段 | 说明 |
|------|------|
| `scenario_id` | 稳定场景编号 |
| `scenario_name` | 场景名称 |
| `scenario_type` | primary / extended / lifecycle / reliability / performance / usability / configuration-order / abnormal |
| `source_seed_refs` | 来源 seed 或需求段落 |
| `scenario_goal` | 场景目标 |
| `topology_ref` | 关联 Topology |
| `preconditions` | 前置条件 |
| `normal_path` | 正常路径；必须包含 `step_id / sub_step_ids / operation / necessity / description` |
| `abnormal_path` | 异常路径；必须包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`；无异常路径时必须说明不适用理由 |
| `atomic_operations` | 主流程原子操作 |
| `observation_points` | 观察点 |
| `expected_state` | 预期状态 |
| `exit_action` | 退出、清理或回滚动作 |
| `confirmation_status` | confirmed / needs-confirmation |

### Structured Supplement 最低字段

| 字段 | 说明 |
|------|------|
| `input_document_classification` | 输入文档类型识别 |
| `scope_constraints` | 范围约束 |
| `out_of_scope_candidates` | 收敛排除项 |
| `topology_catalog` | 拓扑目录 |
| `topology_source_mapping` | 拓扑来源映射 |
| `seed_to_scenario_mapping` | Seed-to-Scenario Mapping |
| `action_sources` | atomic-ops 原子操作清单 |
| `knowledge_references` | 知识引用 |
| `existing_tool_usage_seed` | 现有工具种子 |
| `tool_abstraction_draft` | 工具抽象草案 |
| `confirmation_gaps` | 确认缺口 |

## 硬规则

- 功能初稿不可直接发布为 confirmed scenario。
- functional scenario seed 必须进入场景再发现；seed one-to-one rewriting 明确禁止。
- 未读取输入文档类型前，不得输出最终场景列表。
- 未建立 Topology Catalog 前，不得为依赖组网的场景写 confirmed `topology_ref`。
- `input/TGFW测试组网图集合.md` 存在时，优先使用 TGFW 测试组网图集合；集合外拓扑必须进入 `confirmation_gaps`。
- atomic-ops 是唯一原子操作引用对象，`action_source_ref` 必须直接引用 `op_id`。
- `source_type` 必须固定为 `atomic-ops`，不得出现 `rest-api`、`cli-tool`、`tool-method`。
- `normal_path.necessity` 只能使用 `必要 / 可选 / 至少选择一项`；不得输出未定义取值。
- `abnormal_path` 不得缺少 `related_normal_steps`；未能追溯到正常步骤的异常必须说明来源并进入 `confirmation_gaps` 或风险说明。
- `minimal_logic_chain` 必须保留 `normal_path` 的必要性和选择组语义，不得把可选步骤或选择组改写为必做链路。
- Knowledge Reference 必须保留 `resolved / missing / unavailable` 三态。
- Tool Draft 只能描述能力缺口和建议契约，不得伪造已可执行工具。
- Confirmation Gaps 未关闭前，不得把对应场景标记为 confirmed。
- 每个 `confirmation_gaps` 条目必须以决策项格式呈现，包含 `gap_id / question / recommendation / alternatives[] / impact_surface / status`。
- 每个决策项的 `alternatives[]` 至少包含 1 个备选方案（2 个为宜），每个备选方案必须含方案描述和优劣分析；仅 1 个可行方案时须显式声明理由。
- 暂停用户确认前，必须收集全部 `confirmation_gaps` 条目以统一决策清单形式呈现，禁止逐条分散确认。

## 输出质量检查

输出前逐项检查并在产物末尾写入结果：

- [ ] 已输出输入文档类型识别，覆盖 raw requirement / functional scenario seed / deployment scenario draft / confirmed scenario artifact。
- [ ] functional scenario seed 已进入场景再发现和头脑风暴，未直接成为最终场景。
- [ ] 已输出 Seed-to-Scenario Mapping，且不存在 seed one-to-one rewriting。
- [ ] 已输出 `scope_constraints` 与 `out_of_scope_candidates`，显式限制已生效。
- [ ] 若存在 `TGFW测试组网图集合.md`，已输出 Topology Catalog 和 Topology Source Mapping。
- [ ] 每个依赖组网的场景均包含 `topology_ref`、来源、Mermaid、设备表、端口表和链路表。
- [ ] 正常路径和异常路径均被覆盖；无异常路径时已说明不适用理由。
- [ ] `normal_path` 已区分大步骤和子步骤；多动作步骤未被压缩成不可追溯描述。
- [ ] `necessity` 仅使用 `必要 / 可选 / 至少选择一项`，没有出现未定义取值。
- [ ] 所有 `至少选择一项` 步骤均列出了可选择的子步骤，并说明不能全部跳过。
- [ ] 每条 `abnormal_path` 均填写了 `related_normal_steps`，可追溯到正常路径的大步骤或子步骤。
- [ ] `minimal_logic_chain` 与 `normal_path` 的必要性约束一致，未把可选步骤或选择组误写为必做链路。
- [ ] 部署、容量扩展、维护、可靠性、性能、可用性、配置顺序至少被逐项评估。
- [ ] 策略路由场景已覆盖 match dimensions、ingress interface shape、forwarding action、egress mode/interface type、risk dimensions。
- [ ] 已统一按 atomic-ops 建模，`source_type=atomic-ops`，`action_source_ref` 直接引用 `op_id`。
- [ ] 未将 REST API、CLI 或 tool-method 作为独立引用类型输出；它们只出现在 atomic-op 调用/观测契约中。
- [ ] 工具能力缺口已进入 Tool Abstraction Draft 或 Confirmation Gaps。
- [ ] Knowledge Reference 保留 `resolved / missing / unavailable` 三态。
- [ ] 所有不确定项均进入 `confirmation_gaps`，没有隐式假设。
- [ ] 每个 `confirmation_gaps` 条目均按决策项格式输出（`gap_id / question / recommendation / alternatives[] / impact_surface / status`）。
- [ ] 每个决策项至少包含 1 个备选方案（2 个为宜），备选方案均含优劣分析；仅有 1 个可行方案时已显式声明理由。
- [ ] 暂停确认前已收集全部 `confirmation_gaps` 条目并以统一决策清单呈现，未逐条分散确认。

## Gotchas

- `knowledge_missing` 不等于 `interface_unavailable`，不可混写为“无结果”。
- 对用户未提供的 atomic-ops 契约不能自行补全为可执行细节；REST API / CLI / tool-method 细节只能作为 atomic-op 底层契约补充。
- 华为产品术语保持原文，不要擅自改写成熟悉但不准确的说法。
- 若现有工具描述过粗，优先输出 Tool Abstraction Draft。
- 缺口未确认前，不得把场景链当成已确认输入交给 M 分析。
- TGFW 集合中的拓扑标识必须精确引用，不得用“类似双节点拓扑”替代。
- 功能种子中的顺序不代表部署型场景优先级；优先级必须来自用户目标、部署风险和确认材料。
- 选择组不能被拆成彼此无关的主步骤；否则后续 LC 和物理用例会丢失“至少选择一项”的覆盖关系。
- 异常路径不能只写场景级现象；必须定位到具体正常步骤、子步骤、前置条件、环境故障、退出动作或独立风险项。
- 决策项中的备选方案不能写成"方案 A vs 方案 B"的简单标签；必须包含具体描述、与推荐方案的优劣对比和回退可行性。
- 逐条分散确认缺口会导致用户遗漏决策上下文；暂停确认前必须汇总全部缺口为统一清单。

## 验收标准

- [ ] Markdown 结构清晰，无未闭合代码围栏。
- [ ] 每个场景包含 `scenario_goal / principle / preconditions / precondition_operations / atomic_operations / observation_points / minimal_logic_chain / data_overlay_slots / exit_action`。
- [ ] 每个场景的 `normal_path` 包含 `step_id / sub_step_ids / operation / necessity / description`，且必要性取值规范。
- [ ] 每条异常路径包含 `related_normal_steps` 或说明无法追溯的来源。
- [ ] atomic-ops 是唯一原子操作引用对象；REST API / CLI / tool-method 未作为独立引用类型输出。
- [ ] 知识引用保留 `resolved / missing / unavailable`。
- [ ] 不确定信息会进入 `confirmation_gaps`。
- [ ] 已有工具 usage seed 和 Tool Abstraction Draft 可输出。
- [ ] 已输出双层结构：Scenario Details 与 ptm-tde Scenario Discovery Structured Supplement。
- [ ] 已输出 Seed-to-Scenario Mapping、Topology Source Mapping 和输出质量检查。
- [ ] 所有 `confirmation_gaps` 条目均以决策项格式呈现，含推荐方案、备选方案和优劣分析。
