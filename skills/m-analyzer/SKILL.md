---
name: m-analyzer
description: >-
  M 分析（MD: Model-based Discrete Function）：按四/五级目录拆分单功能，
  为每个单功能标注 PPDCS 特征（Process/Parameter/Data/Combination/State），
  生成覆盖需求和场景的测试点。
  触发词包括：M分析、功能分析、模块分析、测试点分析、PPDCS标注。
  适用场景：MFQ 分析的第三步（m-analysis 阶段）。
argument-hint: "无需参数，自动读取 feature-input 目录"
user-invokable: true
status: active
---

## 目标

基于 feature-parser 输出的结构化需求、已确认目录以及 STORY-03 产出的
`Scenario Chain / atomic-ops / Knowledge Reference / Existing Tool Usage Seed / Tool Abstraction Draft / confirmation_gaps`，
逐模块/子模块分析功能点，**为每个单功能标注 PPDCS 主特征**，
生成带 trace chain v6 的 CAE 测试点，并抽取后续设计所需的测试对象与测试因子。

## 理论基础

M 分析即 MFQ 框架中的 **MD（Model-based Discrete Function）**：
> 将被测对象细分为可独立测试的单功能，使用 PPDCS 模型分析每个单功能的内在逻辑特征。

**PPDCS 五特征**（来源：《海盗派测试分析》P183-199）：

| 特征 | 识别条件 | 对应建模技术 |
|------|---------|-------------|
| **P-Process** | 需求有业务流程含义，多步骤有序约束 | 流程图/活动图 |
| **P-Parameter** | 参数参与业务规则判定，输入组合影响输出 | 判定表/因果图 |
| **D-Data** | 数据有明确取值范围，各数据项相对独立 | 等价类 + 边界值 |
| **C-Combination** | 多因子多状态，全组合不可枚举 | Pairwise/正交 |
| **S-State** | 对象有多状态可互转，存在状态生命周期 | 状态图/转换表 |

**区分规则**：
- Process vs State → 流程能否回退？不能 = Process，可以 = State
- Parameter vs Data → 参数间有业务规则？有 = Parameter，无/独立 = Data
- Data vs Combination → 因子独立验证够？够 = Data，需组合 = Combination

## 适用范围

- 适用阶段：MFQ 分析的 m-analysis 阶段
- 输入：`analysis/feature-input/` + `analysis/scenarios/confirmed-scenarios.md`
- 输出：
  - `analysis/m-analysis/test-points.md`
  - `analysis/m-analysis/ppdcs-annotation.md`
  - `analysis/m-analysis/test-objects-factors.md`

## 前置条件

- [ ] `analysis/feature-input/raw-requirements.md` 存在
- [ ] `analysis/feature-input/directory-structure.md` 存在（用户已确认）
- [ ] `analysis/scenarios/confirmed-scenarios.md` 存在（用户已确认）
- [ ] 若 `confirmation_gaps` 仍存在，已明确哪些 gap 可继续下游透传，哪些必须先回到场景确认

## 场景输入契约（trace chain v6）

M 分析必须消费以下上游字段，不再假设“只有场景标题 + 简述”：

| 上游字段 | 用途 | 缺失处理 |
|------|------|------|
| `Scenario Chain` | 生成 TP 的场景上下文与最小逻辑链骨架 | 不得脑补，输出 `[待确认]` 并挂 `confirmation_gap_refs` |
| `precondition_operations` | 生成 C 条件与前置动作 trace | 缺失时仅保留已确认前置，不得伪造操作 |
| `atomic_operations` | 生成 A 动作、动作顺序和 `scenario_chain_refs` | 缺失时不得把“功能描述”直接当成可执行动作 |
| `atomic-ops` | 关联 `action_source_refs`，识别 atomic-ops `op_id` 依赖 | 若原子操作契约不清，仅标记 `unknown/gap` |
| `Knowledge Reference` | 记录需求/场景依据来源 | `missing/unavailable` 必须保留原状态 |
| `Existing Tool Usage Seed` | 保留已有工具线索供后续 F/Q/Integrator 使用 | 没有则留空，不做默认映射 |
| `Tool Abstraction Draft` | 标记能力缺口背景 | 仅引用已确认草案 |
| `confirmation_gaps` | 显式透传不确定事实 | 不得静默吞掉 |

## 执行流程

### 步骤 1：加载输入

1. 读取 `analysis/feature-input/raw-requirements.md` 获取需求条目列表
2. 读取 `analysis/feature-input/directory-structure.md` 获取目录层级
3. 读取 `analysis/scenarios/confirmed-scenarios.md` 获取已确认场景链、atomic-ops、知识引用与 gap
4. 校验每个场景是否包含 `Scenario Chain / atomic-ops / Knowledge Reference`
5. 对影响 CAE 落地的未确认事实建立 `confirmation_gap_refs`，不做隐式默认

### 步骤 2：逐模块功能分析

按四级目录（模块）→五级目录（子模块）的顺序，依次分析：

对每个子模块：
1. 提取该子模块关联的需求条目
2. 提取该子模块关联的 `scenario_refs`
3. 从 `minimal_logic_chain + precondition_operations + atomic_operations` 提取该子模块的功能点
4. 对每个功能点，考虑以下维度生成测试点：
   - **正常功能**：功能按预期工作
   - **参数边界**：输入参数的有效/无效边界
   - **异常处理**：错误输入、异常条件下的行为
   - **默认值**：默认配置下的行为
   - **交互影响**：与同模块内其他功能的交互

### 步骤 3：测试对象 / 测试因子提取

先提取测试对象，再提取测试因子：

1. **测试对象提取优先级**：`C（Condition） → A（Action） → E（Effect）`
2. 每个对象至少记录：

| 字段 | 说明 |
|------|------|
| `object_id` | 对象编号 |
| `object_name` | 对象名称 |
| `object_type` | 配置对象 / 运行态对象 / 接口对象 / 观测对象 |
| `observation_targets` | 如何判断对象状态变化 |
| `scenario_refs` | 来源场景 |
| `action_source_refs` | 关联 atomic-ops `op_id` |

3. 每个因子至少记录：

| 字段 | 说明 |
|------|------|
| `factor_id` | 因子编号 |
| `factor_name` | 因子名称 |
| `source_section` | `precondition / condition / action-input / observation` |
| `data_domain` | 取值范围 / 枚举 / 阈值 |
| `related_object_id` | 关联对象 |
| `scenario_refs` | 来源场景 |
| `confirmation_gap_refs` | 若取值边界未确认 |

4. 典型因子：`IP地址 / 接口类型 / 协议类型 / 状态值 / 数量阈值`
5. 无法确认对象或因子边界时，输出 `[待确认]` 并保留 gap，不得自行补齐

### 步骤 4：PPDCS 特征标注（v2 新增）

**对每个五级目录节点（单功能），分析其内在逻辑特征并标注 PPDCS 主特征**：

```
对每个单功能：
  1. 分析需求描述中的逻辑结构
  2. 按以下优先级逐条判断：
     ├── 是否涉及多状态互转（可回退）？   → 标注 S-State
     ├── 是否有多步骤有序业务流程？         → 标注 P-Process
     ├── 参数间是否存在规则依赖？           → 标注 P-Parameter
     ├── 因子是否过多需组合压缩？           → 标注 C-Combination
     └── 数据是否独立可单独验证？           → 标注 D-Data
  3. 如有混合特征，标注主特征 + 辅特征
  4. 记录判定依据
```

### 步骤 5：测试点标注（CAE 三元组 + trace chain v6）

每个测试点必须包含 **CAE 三元组**（条件/动作/预期），在什么条件下（C），完成什么操作（A），发生什么结果（E）：

| 字段 | 说明 | 示例 |
|------|------|------|
| TP-ID | 测试点编号 | `TP-M-<模块缩写>-<子模块缩写>-NNN` |
| 所属模块 | 四级目录名称 | 配置管理 |
| 所属子模块 | 五级目录名称 | 日志服务器配置 |
| C 条件 | 触发该测试的前置状态、数据边界或环境约束（多个条件用"；"分隔） | 系统已配置5台日志服务器（达上限）；管理员已登录 |
| A 动作 | 可执行的测试操作，包含操作对象和内容（复合动作用"→"连接） | 尝试新建第6台日志服务器，点击"确定" |
| E 预期 | 可观测的预期行为或系统响应（多个预期用"；"分隔） | 系统提示"超出最大服务器数量限制"；新建失败；服务器列表条目数不变 |
| 关联需求 | 需求编号列表 | SR-001, SR-003 |
| `scenario_refs` | 场景编号列表 | SCN-XXX-001 |
| `scenario_chain_refs` | `PRE-* / AO-* / minimal_logic_chain` 引用 | PRE-01, AO-02 |
| `action_source_refs` | atomic-ops `op_id` 引用 | fw_config_policy_route |
| `knowledge_refs` | 支撑该 TP 的知识引用 | KR-001 |
| `confirmation_gap_refs` | 上游未确认事实引用 | GAP-001 |
| `trace_refs` | 汇总 `requirement_refs / scenario_refs / action_source_refs / knowledge_refs` | 结构化 trace |
| `test_object_refs` | 关联测试对象 | OBJ-001 |
| `factor_refs` | 关联测试因子 | FAC-001, FAC-002 |
| 来源 | M 分析 | M |
| 测试类型建议 | 功能/边界/异常/默认 | 边界 |
| `fact_status` | `confirmed / needs-confirmation` | confirmed |

**CAE 字段约束**：
- C 必须是可验证的前置状态，禁止模糊表述（如"正常情况下"）
- A 必须是可执行的操作，不能是"验证..."等描述性文字
- E 必须是可观测的结果，包含观测点和期望值
- **E="待定" 容错规则（Q1 default）**：预期结果尚不明确时（如依赖硬件规格、待确认的产品行为），E 可填 `"待定"`，但必须追加批注 `[待定原因: <描述>]`；进入用例设计阶段前须补全。空值不允许。
- 若 A 依赖 atomic-ops 但契约不完整，A 只能写已确认部分，并在 `confirmation_gap_refs` 中注明缺口
- 若 `Knowledge Reference` 为 `missing/unavailable`，仅记录状态，不得伪造理论依据

### 步骤 6：覆盖初检

1. **需求覆盖**：检查每条 SR 至少关联 1 个测试点
2. **场景覆盖**：检查每个场景的关键功能点至少关联 1 个测试点
3. **atomic-ops 覆盖**：每个被引用的 `action_source_ref`（atomic-ops `op_id`）至少落到 1 个 TP 或显式标记为 `未形成测试点`
4. **输出未覆盖项**：标记为 `⚠️ 待补充`

### 步骤 7：输出

> 追踪链：`SR → Scenario Chain → atomic-ops / Knowledge Reference → TP(CAE + PPDCS + object/factor) → LC → Test Data → PC`

写入以下文件：

**`analysis/m-analysis/test-points.md`**：按**四级目录（H2）→ 五级目录（H3）**分节输出，每节标注 PPDCS 主特征，测试点以 CAE 格式呈现：

```markdown
# <特性名> — M 分析测试点

## 统计

| 来源 | 测试点数 |
|------|---------|
| M 分析 | N |

## <四级目录名称（模块）>

### <五级目录名称（子模块）>
> PPDCS 主特征：P-Parameter | 辅特征：D-Data

| TP-ID | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `test_object_refs` | `factor_refs` | 来源 | 测试类型 |
|-------|--------|--------|--------|-----------------|----------------------|--------------------|---------------|------|---------|
| TP-M-CFG-SRV-001 | 系统无已配置的日志服务器；管理员已登录 | 在新建表单输入IP=<IP_ADDRESS>、端口=514、协议=UDP，点击"确定" | 服务器创建成功；服务器列表新增该条目；状态显示为"已配置" | SCN-LOG-001 | fw_config_log_server | OBJ-LOG-SERVER | FAC-IP,FAC-PORT,FAC-PROTO | M | 功能 |
| TP-M-CFG-SRV-002 | 系统已配置5台日志服务器（已达上限） | 尝试新建第6台日志服务器，点击"确定" | 系统提示"超出最大服务器数量限制"；新建失败；服务器列表条目数不变 | SCN-LOG-001 | fw_config_log_server | OBJ-LOG-SERVER | FAC-SERVER-COUNT | M | 边界 |

### <五级目录名称（子模块2）>
> PPDCS 主特征：P-Process

| TP-ID | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `test_object_refs` | `factor_refs` | 来源 | 测试类型 |
|-------|--------|--------|--------|-----------------|----------------------|--------------------|---------------|------|---------|
| ... | ... | ... | ... | ... | ... | ... | ... | M | ... |
```

> ⚠️ **完整性要求**：目录结构中每个五级目录节点必须有至少一个测试点，不允许跳过。若某节点无需求支撑，需标注 `⚠️ 无对应测试点 — 原因：<说明>`。

**`analysis/m-analysis/ppdcs-annotation.md`**：

```markdown
# <特性名> — PPDCS 特征标注表

## 统计

| PPDCS 特征 | 子模块数 | 占比 |
|-----------|---------|------|
| P-Process | N | X% |
| P-Parameter | M | Y% |
| D-Data | K | Z% |
| C-Combination | J | W% |
| S-State | L | V% |
| 混合特征 | H | U% |

## 标注详表

| 子模块 | PPDCS 主特征 | 辅特征 | 判定依据 |
|--------|-------------|--------|---------|
| 日志服务器配置 | P-Parameter | D-Data | 多参数规则判定（IP/端口/协议组合影响结果） |
| 日志过滤流程 | P-Process | — | 过滤有明确步骤和分支（格式校验→名称检查→保存） |
| 日志导出状态 | S-State | — | 导出任务有状态变迁（未启动→导出中→完成/失败） |
| 日志查询 | D-Data | C-Combination | 查询条件有取值范围，多条件需组合 |
```

**`analysis/m-analysis/test-objects-factors.md`**：

```markdown
# <特性名> — 测试对象与测试因子

## Test Objects

| object_id | object_name | object_type | observation_targets | scenario_refs | action_source_refs |
|-----------|-------------|-------------|---------------------|---------------|--------------------|
| OBJ-LOG-SERVER | 日志服务器 | 配置对象 | 列表条目、状态字段、告警信息 | SCN-LOG-001 | fw_config_log_server |

## Test Factors

| factor_id | factor_name | source_section | data_domain | related_object_id | scenario_refs | confirmation_gap_refs |
|-----------|-------------|----------------|-------------|-------------------|---------------|-----------------------|
| FAC-IP | IP地址 | action-input | IPv4合法/非法边界 | OBJ-LOG-SERVER | SCN-LOG-001 | — |
| FAC-SERVER-COUNT | 服务器数量 | condition | 0 / 1~4 / 5(上限) / >5[待确认] | OBJ-LOG-SERVER | SCN-LOG-001 | GAP-001 |
```

## 测试点生成原则

1. **一个功能点至少一个测试点**
2. **正面优先**：先覆盖正常功能，再覆盖异常和边界
3. **粒度适中**：测试点应可独立验证
4. **可追溯**：每个测试点必须关联至少一条需求
5. **不预设设计方法**：M 分析只关注"测什么"和"什么特征"，不关注"怎么测"

## 公共因子库补充契约

- M 分析是公共因子库首个强制消费者；提取测试因子前必须读取 `analysis/factor-usage/factor-library-lock.yaml` 或从公共 resource 目录选择库。
- 公共库查找顺序：`PTM_TEAM_RESOURCE_HOME/factor-libraries` → `~/.ptm-team/resource/factor-libraries` → 开发态 `resource/factor-libraries`。
- 按 `factor_id / factor_name / aliases / owner_object / factor_group` 检索；命中 `active` 因子时复用，值域/样本/约束不足时输出扩展建议，未命中时写入 `analysis/factor-usage/candidate-factor-proposals.yaml`。
- 项目运行不得直接修改公共主库；公共库归档和更新只能回流到 `resource/factor-libraries/`。
- CAE 中使用 `{{TF:FAC-ID|role=<role>|usage=<usage_context>|sample=<sample_id>}}`；下游主契约是 `factor_bindings`，`factor_refs` 只保留为兼容摘要。
- `factor_bindings` 至少包含 `library_id / factor_id_or_group_id / role / binding_mode / usage_context / sample_id / expr / materialized_stage / gap`。
- 禁止把 atomic-ops、`scenario_refs`、`knowledge_refs`、`confirmation_gap_refs` 当成测试因子。
- 必须输出 `analysis/factor-usage/factor-resolution-report.md`；如有未命中或需扩展内容，必须输出 `candidate-factor-proposals.yaml`。

## Gotchas

- 需求描述中隐含的功能也需要提取测试点
- 同一需求可能跨多个子模块
- 不要在 M 分析阶段引入耦合测试点（F 分析职责）
- PPDCS 标注时注意区分 Process 和 State 的双向性差异
- 一个子模块可能有混合特征，此时标注主特征+辅特征
- 不得把 `confirmation_gaps` 当作已确认事实
- `action_source_refs` 只引用上游已建模 atomic-ops `op_id`，不重新命名为新的字段体系

## 验收标准

- [ ] 每个五级目录节点至少有 1 个测试点，无跳过；无法覆盖的节点明确标注原因
- [ ] 每个测试点包含完整的 CAE 三字段（C/A/E 均不为空、不模糊）
- [ ] C 字段为可验证状态，A 字段为可执行操作，E 字段为可观测结果
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 每个 TP 包含 `scenario_refs / action_source_refs / test_object_refs / factor_bindings / factor_refs / trace_refs`
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式透传
- [ ] 输出文件按**四级目录（H2）→ 五级目录（H3）**分节，每节标注 PPDCS 主特征
- [ ] **每个五级目录节点均有 PPDCS 主特征标注和判定依据**
- [ ] 需求覆盖初检已执行，未覆盖项已标记
- [ ] 输出 `test-points.md`、`ppdcs-annotation.md`、`test-objects-factors.md`
