---
name: q-analyzer
description: >-
  Q 分析（质量属性分析）：参考 HTSM 维度评估特性的质量属性相关性，
  仅对相关维度展开分析并生成测试点。
  触发词包括：Q分析、质量分析、HTSM、质量属性、可靠性分析。
  适用场景：MFQ 分析的第五步（q-analysis 阶段）。
argument-hint: "无需参数，自动读取 m-analysis 目录"
user-invokable: true
status: active
---

## 目标

参考 HTSM（Heuristic Test Strategy Model）的质量属性维度，
评估当前特性在各质量维度上的相关性，仅对有相关性的维度展开分析，
生成带 trace chain v6 的质量属性测试点，并评估现有 atomic-ops/工具是否能支撑观测与校验。

## 适用范围

- 适用阶段：MFQ 分析的 q-analysis 阶段
- 输入：`analysis/m-analysis/` + `analysis/scenarios/confirmed-scenarios.md`
- 输出：
  - `analysis/q-analysis/quality-test-points.md`
  - `analysis/q-analysis/tool-analysis.md`

## 前置条件

- [ ] M 分析已完成（`analysis/m-analysis/test-points.md` 存在）
- [ ] 场景文档已确认
- [ ] `Scenario Chain / atomic-ops / Knowledge Reference / confirmation_gaps` 可读取
- [ ] 未确认事实已明确哪些可以带 `[待确认]` 下传

## 拓扑/因子分层 Guardrail

- 保持 trace chain v6、`factor_bindings` 和公共因子库规则；不得用真实组网对象替换逻辑质量因子。
- `factor_refs`、`factor_bindings`、质量测试因子取值中禁止出现 `DUT.port*`、`TG.port*`、link 或 TOPO 实例。
- 若质量场景必须引用真实组网对象，必须登记到 `topology_binding_refs` 或 `topology_source`，并保留 `source_ref / fact_status / confirmation_gap_refs`。
- 若真实组网对象来源、角色绑定或 TOPO 实例语义无法确认，相关相关性结论、TP-Q 或工具缺口必须降级为 `needs-confirmation`。
- `covered_factors` 只填写逻辑质量因子；真实端口只能作为拓扑绑定或 PC 物化对象，不得混入工具覆盖因子。

## HTSM 质量属性维度

| 维度 | 子维度 | 说明 |
|------|--------|------|
| **功能性** | 准确性、适合性、互操作性、合规性 | 功能是否正确完整 |
| **可靠性** | 成熟性、容错性、可恢复性 | 掉电恢复、异常容错、长期稳定 |
| **性能** | 时间效率、资源利用率、容量 | 响应时间、资源消耗、规格上限 |
| **可安装性** | 安装/升级/回滚、迁移 | 首次安装、版本升级、降级回滚 |
| **兼容性** | 共存性、互替性 | 与其他特性/版本/设备的兼容 |
| **安全性** | 保密性、完整性、抗否认性、可审计性 | 权限、加密、审计 |
| **可维护性** | 可分析性、可修改性、可测试性 | 日志、调试、诊断 |
| **可用性** | 易理解性、易操作性、吸引性 | 用户界面友好度 |

## 执行流程

### 步骤 1：相关性评估

对每个 HTSM 维度，评估与当前特性的相关性：

| 相关性 | 定义 | 处理 |
|--------|------|------|
| **强相关** | 该维度是特性的核心质量要求 | 深度分析，生成多个测试点 |
| **弱相关** | 该维度与特性有一定关系 | 简要分析，生成 1~2 个测试点 |
| **不相关** | 该维度与当前特性无关 | 不展开分析，标注"不适用" |

评估依据：
1. 需求文档中是否明确提及该维度
2. `Scenario Chain` 中的观察点、预期状态、前置条件是否涉及该维度
3. `Knowledge Reference` 中是否有该维度的显式依据
4. 防火墙设备的通用质量要求

若支撑依据来自 `missing/unavailable` 的知识结果或未确认 atomic-ops，必须在相关性说明中写明，而不是默认“强相关”。

### 步骤 2：展开分析

对每个强相关/弱相关维度，分析具体的质量测试关注点：

**可靠性分析示例**：
- 掉电后功能是否自动恢复
- 主备切换时数据是否丢失
- 异常输入是否导致服务崩溃
- 长时间运行是否有资源泄漏

**安全性分析示例**：
- 不同权限用户的操作范围
- 审计日志是否完整记录
- 敏感数据是否加密存储

每个质量关注点都应回链：

- `scenario_refs`
- `scenario_chain_refs`
- `action_source_refs`
- `knowledge_refs`
- `confirmation_gap_refs`
- `test_object_refs / factor_refs`
- `topology_binding_refs / topology_source`（仅当质量场景涉及真实端口、link 或 TOPO 实例时填写）

### 步骤 3：测试点生成（CAE 三元组 + trace chain v6）

为每个相关维度生成 CAE 格式的测试点：

| 字段 | 说明 |
|------|------|
| TP-ID | `TP-Q-<维度缩写>-NNN`（如 TP-Q-REL-001） |
| 质量维度 | HTSM 维度名称 |
| 子维度 | HTSM 子维度 |
| 关联模块 | 涉及的四/五级目录模块 |
| C 条件 | 触发该质量测试的前置状态或环境条件（含规格基线 / 设备规格 / 压力条件） |
| A 动作 | 施加的操作（含质量压力/场景触发） |
| E 预期 | 可观测的质量属性表现（含量化指标或定性状态）|
| `scenario_refs` | 来源场景 |
| `scenario_chain_refs` | 对应 PRE / AO / 最小逻辑链节点 |
| `action_source_refs` | 涉及的 atomic-ops `op_id` |
| `knowledge_refs` | 依据引用 |
| `confirmation_gap_refs` | 未确认事实 |
| `test_object_refs` | 关联测试对象 |
| `factor_refs` | 关联质量因子 |
| `topology_binding_refs` | 真实端口、link 或 TOPO 实例的来源绑定；无则写 `—` |
| `trace_refs` | 汇总 trace |
| `fact_status` | `confirmed / needs-confirmation` |

**CAE 字段约束（质量测试点）**：
- C：前置状态 + 质量约束基线（规格参数 / 性能基线 / 环境条件），禁止模糊表述
- A：施加质量压力 / 触发场景（含具体压力值或触发方式）
- E：可观测的质量属性表现（含量化指标或定性状态）；E="待定" 时须附批注 `[待定原因: <如"可靠性指标待产品定义，MTBF基线未确定">]`
- 若无法确认观测方式，必须引用对应 `confirmation_gap_refs` 或 `Tool Capability Gap`
- 若质量测试点依赖 `DUT.port*`、`TG.port*`、link 或 TOPO 实例，必须通过 `topology_binding_refs` 回链来源；不得写入 `factor_refs` 或测试因子取值。

### 步骤 4：工具观测能力评估（Story-04 新增）

对每个质量测试点，评估现有 atomic-ops/工具是否能够：

1. 施加质量压力或触发场景
2. 采集质量观测数据
3. 校验是否达到质量阈值

输出：

#### Existing Tool Summary

| 字段 | 说明 |
|------|------|
| `tool_id` | 工具编号 |
| `tool_name` | 工具名称 |
| `main_usage` | 主要用法 |
| `purpose` | 在质量场景中的用途 |
| `scenario_refs` | 关联场景 |
| `action_source_refs` | 关联 atomic-ops `op_id` |
| `covered_objects` | 已覆盖对象 |
| `covered_factors` | 已覆盖因子 |
| `status` | `ready / partial / needs-confirmation` |

> `Existing Tool Summary` 必须作为 integrator 的正式输入原样保留；`covered_objects / covered_factors` 不得在 Q 分析阶段被折叠成说明文本或只保留别名。

#### Tool Capability Gap

| 字段 | 说明 |
|------|------|
| `tool_id` | 工具编号 |
| `tool_name` | 候选工具名称 |
| `covered_objects` | 已覆盖对象 |
| `covered_factors` | 已覆盖因子 |
| `missing_ops` | 缺失的压测 / 观测 / 校验能力 |
| `proposed_interface` | 建议 CLI/API/method |
| `function_desc` | 需要支持的功能 |
| `io_behavior_matrix` | 输入/输出条件下的处理逻辑 |
| `output_contract` | 输出内容、阈值、时间序列或状态契约 |
| `scenario_refs` | 关联场景 |
| `action_source_refs` | 关联 atomic-ops `op_id` |
| `factor_refs` | 关联因子 |
| `status` | `gap / needs-confirmation` |

> 若质量观测能力存在不确定性，保留 `covered_objects / covered_factors / io_behavior_matrix`，并通过 `status=needs-confirmation` 显式暴露，不得省略字段来“弱化”不确定性。

### 步骤 5：输出

> 追踪链：`SR → Scenario Chain → atomic-ops / Knowledge Reference → TP-Q(CAE + quality trace) → LC → Test Data → PC`

写入 `analysis/q-analysis/quality-test-points.md`，按**四级目录（H2）→ 五级目录（H3）**分节，每节内按质量维度组织 CAE 测试点：

```markdown
# <特性名> — Q 分析测试点

## HTSM 相关性评估

| 质量维度 | 相关性 | 测试点数 | 说明 |
|---------|--------|---------|------|
| 功能性 | — | 0 | 由 M 分析覆盖 |
| 可靠性 | 强相关 | 5 | 掉电恢复、主备切换... |
| 性能 | 弱相关 | 2 | 响应时间 |
| 安全性 | 强相关 | 3 | 权限控制、审计 |
| ... | 不适用 | 0 | — |

## <四级目录>

### <五级目录>

#### 可靠性

| TP-ID | 质量维度 | 子维度 | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `factor_refs` | 关联模块 |
|-------|---------|--------|--------|--------|--------|-----------------|----------------------|---------------|---------|
| TP-Q-REL-001 | 可靠性 | 可恢复性 | 设备处于正常运行状态；日志服务器已配置 | 执行掉电操作，重新上电后等待设备完全启动 | 日志服务器配置自动恢复；日志发送功能恢复正常 | SCN-LOG-REC-001 | fw_power_cycle | FAC-RECOVERY-TIME | 配置管理 |
| TP-Q-REL-002 | 可靠性 | 容错性 | 主备双机已配置，均处于正常状态 | 强制主机下线，触发主备切换 | 备机接管成功；日志服务器配置在备机上保持一致；切换期间无配置数据丢失 | SCN-LOG-HA-001 | fw_trigger_ha_switch | FAC-SWITCH-TIME | 配置管理 |

#### 安全性

| TP-ID | 质量维度 | 子维度 | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `factor_refs` | 关联模块 |
|-------|---------|--------|--------|--------|--------|-----------------|----------------------|---------------|---------|
| TP-Q-SEC-001 | 安全性 | 保密性 | 普通操作员账号已登录；存在其他用户配置的日志服务器 | 尝试查看/修改其他用户创建的日志服务器配置 | 系统拒绝访问或仅显示有权限的条目；提示权限不足 | SCN-LOG-SEC-001 | fw_check_role_permission | FAC-ROLE | 权限管理 |
```

> 若 TP-Q 需要暴露真实端口或 TOPO 实例，在表后附 `topology_binding_refs` 明细表；主表 `factor_refs` 仍只保留逻辑质量因子。

同时写入 **`analysis/q-analysis/tool-analysis.md`**：

```markdown
# <特性名> — Q 分析工具覆盖评估

## Existing Tool Summary

| tool_id | tool_name | main_usage | purpose | scenario_refs | action_source_refs | covered_objects | covered_factors | status |
|---------|-----------|------------|---------|---------------|--------------------|-----------------|-----------------|--------|
| TOOL-Q-001 | perf-cli | `perf-cli sample --metric cpu` | 采集性能指标 | SCN-PERF-001 | fw_collect_perf_metric | OBJ-DEVICE | FAC-CPU-USAGE | ready |

## Tool Capability Gap

| tool_id | tool_name | covered_objects | covered_factors | missing_ops | proposed_interface | function_desc | io_behavior_matrix | output_contract | scenario_refs | action_source_refs | factor_refs | status |
|---------|-----------|-----------------|-----------------|-------------|--------------------|---------------|--------------------|-----------------|---------------|--------------------|-------------|--------|
| GAP-Q-001 | audit-exporter | OBJ-AUDIT-LOG | FAC-AUDIT-FIELD,FAC-AUDIT-TIMELINE | 导出审计时间线 | CLI: `audit-exporter trace --since ...` | 输出审计事件序列与字段完整性 | 指定时间窗且日志可读→返回完整时间线；字段缺失→返回缺失字段清单与失败状态 | stdout/json + field completeness report | SCN-AUDIT-001 | fw_export_audit_timeline | FAC-AUDIT-FIELD,FAC-AUDIT-TIMELINE | gap |
```

## Gotchas

- **功能性维度不在 Q 分析中展开**，因为功能性已由 M 分析覆盖
- 防火墙设备通常对可靠性和安全性有较高要求，这两个维度大概率是强相关
- 性能维度需要考虑设备规格（如最大会话数、转发性能），但测试点应聚焦于功能相关的性能
- 不要过度展开不相关维度（如可用性对于 CLI 配置型特性可能不适用）
- 不能把缺失的观测工具默认为“人工可观察”；必须输出 tool gap
- `Knowledge Reference=missing/unavailable` 时，可继续分析，但必须保留不确定性
- 不得把 `DUT.port1/TG.port2`、link 或 TOPO 实例写入 `factor_refs / factor_bindings / covered_factors`；真实组网对象必须登记拓扑来源，来源不明则降级 `needs-confirmation`。

## 验收标准

- [ ] 所有 HTSM 维度均已评估相关性
- [ ] 每个强相关/弱相关维度至少 1 个测试点
- [ ] 不相关维度明确标注"不适用"
- [ ] 每个测试点包含完整 CAE 三字段（C/A/E 均不为空）
- [ ] C 字段含质量约束基线（规格参数 / 性能基线 / 环境条件）
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 每个 TP-Q 包含 `scenario_refs / action_source_refs / factor_refs / trace_refs`
- [ ] `factor_refs / factor_bindings / covered_factors` 未混入真实端口、link 或 TOPO 实例；涉及真实组网对象时已登记拓扑来源或降级 `needs-confirmation`
- [ ] 工具观测能力评估输出 `Existing Tool Summary` 和 `Tool Capability Gap`
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式透传
- [ ] 输出文件按四/五级目录分节，每节按质量维度组织
- [ ] 输出文件写入 `analysis/q-analysis/quality-test-points.md` 与 `analysis/q-analysis/tool-analysis.md`
