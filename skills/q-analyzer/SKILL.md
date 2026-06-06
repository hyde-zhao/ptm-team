---
name: q-analyzer
description: >-
  Q 分析（质量属性分析）v3.0：逐 TSP 驱动质量分析，6 步。消费 M 分析产出的 TSP 列表与覆盖矩阵中的 [Q→] 标签线索，逐 TSP 逐 HTSM 维度评估相关性、发现质量对象与因子（含候选）、生成按 TSP 组织且按质量维度分组的 CAE 质量测试点、产出质量因子候选列表。
  触发词包括：Q分析、质量分析、HTSM、质量属性、可靠性分析。
  适用场景：MFQ 分析的第五步（q-analysis 阶段）。
argument-hint: "无需参数，自动读取 m-analysis 目录"
user-invokable: true
status: active
---

## 目标

以 M 分析产出的 TSP 列表为驱动单元，消费覆盖矩阵中的 [Q→] 标签作为相关性评估的补充依据，逐 TSP 逐 HTSM 维度评估质量属性相关性，对有相关性的维度展开质量对象与因子发现（含基于知识生成的质量因子候选），生成按 TSP 组织且按质量维度分组的 CAE 质量测试点，评估工具观测能力，最终产出质量因子候选列表供下游候选汇总消费。

## 适用范围

- 适用阶段：MFQ 分析的 q-analysis 阶段
- 核心驱动：逐 TSP（来自 M 分析）进行质量属性分析
- 输入：
  - `mfq/m-analysis/tsp/*.md` — M 分析的 TSP 列表（含 `q_tags`）
  - `mfq/m-analysis/scenario-tsp-coverage.md` — 覆盖矩阵（Q 分析线索列表）
  - `mfq/m-analysis/test-objects-factors.md` — M 分析的测试对象与因子表
  - `kym/scenarios/confirmed-scenarios.md` — 已确认场景
  - `kym/mission-understanding/mission-statement.md` — KYM 产出（风险 + 测试边界）
  - `kym/feature-input/raw-requirements.md` — 需求条目
  - `resource/factor-library/` — 公共因子库
- 输出：
  - `mfq/q-analysis/quality-test-points.md` — 按 TSP 组织、按质量维度分组的 CAE 质量测试点 + HTSM 相关性评估表
  - `mfq/q-analysis/tool-analysis.md` — 工具观测能力评估（Existing Tool Summary + Tool Capability Gap）
  - 质量因子候选列表（嵌入 `quality-test-points.md` 末尾，标注 `tsp_ref`）

## 前置条件

- [ ] M 分析已完成（`mfq/m-analysis/test-points.md` 存在）
- [ ] M 分析的 TSP 列表可用（`mfq/m-analysis/tsp/`，每个 TSP 含 `id / m_id / topic / scope / purpose / q_tags / covered_scenario_segments`）
- [ ] M 分析的覆盖矩阵可用（`mfq/m-analysis/scenario-tsp-coverage.md`，含 Q 分析线索列表）
- [ ] 场景文档已确认（`kym/scenarios/confirmed-scenarios.md`）
- [ ] `Scenario Chain / atomic-ops / Knowledge Reference / confirmation_gaps` 可读取
- [ ] 未确认事实已明确哪些可以带 `[待确认]` 下传

⛔ **HARD-STOP（STOP-03）**：禁止 Agent 绕过本 Skill 直接生成 Q 分析产物。Q 分析必须通过 q-analyzer Skill 调用执行。

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

### 步骤 1：加载 TSP 列表、覆盖矩阵与相关性评估

**📥 消费**：

| 消费数据 | 消费字段 | 用途 |
|---------|---------|------|
| M 分析的 TSP 列表 | 全部 TSP（`id / m_id / topic / scope / purpose / q_tags`） | **Q 分析的核心驱动单元** |
| M 分析的覆盖矩阵 | **Q 分析线索列表**（所有 `[Q→]` 标签） | **相关性评估的补充依据**，已标记维度的起评基线 |
| `raw-requirements.md` | 全文 | 检查是否提及质量维度 |
| `confirmed-scenarios.md` | Scenario Chain 的观察点、预期状态 | 检查是否涉及质量维度 |
| `mission-statement.md` | `risks[].area` + `test_items.items` | 风险关联 |
| HTSM 维度定义 | CRUSSPICSTML 维度 | 评估框架 |

**🔄 处理逻辑**：

```
1. 加载 TSP 列表：TSP-M1, TSP-M2, TSP-M3, ...

2. 加载覆盖矩阵中的 Q 分析线索列表（从「Q 分析线索汇总」表提取）：
   - 这些线索是 M 分析步骤 2 中从场景步骤提取的 [Q→] 标签
   - 建立 TSP → [Q→标签维度的集合] 索引
   - 若覆盖矩阵不含 Q 线索表或为空 → 降级为无种子线索模式（不影响评估正确性）

3. 对每个 TSP，逐个 HTSM 维度评估相关性：

   判定逻辑：
   ├── 该 TSP 的 q_tags 中有关联此维度的 [Q→] 标签
   │   → **至少弱相关起评**（[Q→] 标签强制起评规则），可升级为强相关
   ├── TSP.purpose 明确涉及该质量维度 → 强相关
   ├── TSP 关联的场景链中该维度的观察点 → 弱相关或强相关
   ├── TSP 关联的 Knowledge Reference 有显式依据 → 按引用强度判定
   ├── 防火墙设备通用质量要求 → 弱相关
   └── 无任何依据 → 不适用

4. 归类：
   ├── 强相关（strong）    → 该维度是此 TSP 的核心质量要求，深度分析
   ├── 弱相关（weak）      → 该维度与此 TSP 有一定关系，简要分析
   ├── 不适用（not-applicable） → 标注，不展开
   └── 功能性              → 不在此展开（M 分析已覆盖）

5. [Q→] 标签的提升/起评规则：
   - 不降级：已有强相关的维度不受 [Q→] 标签影响（不收窄）
   - 可提升：弱相关 + [Q→] 标签 → 强相关
   - 可起评：不适用 + [Q→] 标签 → 弱相关
   - 示例：TSP-M2 无明显可靠性依据，但 q_tags 含 [Q→可靠性] → 从"不适用"提升为"弱相关"

6. 不确定项标记为 OPEN：
   - 相关性判定依据不足时，标记 OPEN 并记录不确定原因
   - 不得自行判定为强相关或弱相关
   - 若 TSP 的 covered_scenario_segments 为空或场景链不可读 → 标记 OPEN
```

**HARD-STOP**：步骤 1 结束后，汇总所有 OPEN 项（TSP 维度相关性不确定项），以单次消息展示给用户。

**优先使用 AskUserQuestion 工具**：
- question: "请确认 Q 分析相关性评估中的待确认项："
- header: "Q relevance"
- multiSelect: false
- options:
  1. label: "Accept all", description: "全部按推荐判定（弱相关起评）"
  2. label: "Skip all", description: "全部跳过（不适用）"
  3. label: "Item by item", description: "逐项指定每个 OPEN 项的相关性"
  4. label: "Defer", description: "暂不处理，先继续后续步骤（OPEN 项暴露为 confirmation_gap_refs）"

若 AskUserQuestion 不可用，回退到 STOP-05 文本标记：

```
## Q 分析相关性评估 — 待确认项

以下维度因判定依据不足标记为待确认（OPEN），请在下方选择后继续：

| # | TSP | 质量维度 | 不确定原因 |
|---|-----|---------|-----------|
| 1 | TSP-M1 | 可靠性 | TSP 关联的场景链中无可靠性观察点，但防火墙设备通常需要；缺少显式依据 |

选项：
  ( ) A. 全部按推荐判定（弱相关起评）
  ( ) B. 全部跳过（不适用）
  ( ) C. 逐项指定
  ( ) D. 暂不处理，先继续后续步骤
```

> 用户回复后方可进入步骤 2。若选择 D（暂不处理），OPEN 项在最终产物中暴露为 `confirmation_gap_refs`，相关测试点降级为 `fact_status=needs-confirmation`。

**📤 生产**：

| 产出 | 内容 |
|------|------|
| 逐 TSP 相关性评估表 | `tsp_ref → [(quality_dimension, relevance, rationale), ...]` |
| Q 线索索引 | `TSP → [Q→标签维度集合]` |
| OPEN 项清单 | 待用户确认的相关性不确定项 |

---

### 步骤 2：逐 TSP 质量对象与因子发现

**📥 消费**：

| 消费数据 | 用途 |
|---------|------|
| 步骤 1 的逐 TSP 相关性评估 | 确定每个 TSP 需要展开的维度 |
| M 分析的测试对象表（`test-objects-factors.md`） | 查找已有对象 |
| M 分析的因子表（已有 + 候选，`test-objects-factors.md`） | 查找已有因子 |
| `confirmed-scenarios.md` | 质量场景回链 |
| 公共因子库（`resource/factor-library/`） | 补充检索 |

**🔄 处理逻辑**：

```
对每个 TSP：
  ┌─ TSP 级 Q 分析 ──────────────────────────────────────────┐
  │                                                            │
  │ 对该 TSP 的每个强相关/弱相关维度：                           │
  │                                                            │
  │   【子步骤 A：识别该 TSP 在此质量维度下的质量对象】           │
  │   1. 确定该质量维度在 TSP 范围内关注的对象：                  │
  │      - 可靠性 → TSP 输出结果的数据一致性、恢复能力           │
  │      - 性能   → TSP 关键路径的响应时间、吞吐量               │
  │      - 安全性 → TSP 输入数据的校验完整性、权限控制           │
  │      - 可维护性 → TSP 相关日志/诊断信息的可分析性            │
  │                                                            │
  │   2. 从 M 分析的测试对象表中查找已有对象 → 直接引用          │
  │   3. 无对应对象 → 新建"质量对象"，标注：                     │
  │      - quality_object_id / quality_object_name              │
  │      - tsp_ref（所属 TSP）                                   │
  │      - quality_dimension（所属质量维度）                     │
  │      - source（M-analysis / new-quality-discovery）          │
  │      - scenario_refs / knowledge_refs                        │
  │                                                            │
  │   【子步骤 B：发现/匹配该 TSP 在此维度下的质量因子】          │
  │   对每个质量对象：                                           │
  │     1. 从 M 分析的因子表中查找关联因子：                     │
  │        - 已有因子 → 直接引用，标注 source=public-library     │
  │        - 候选因子 → 引用并标记 source=candidate              │
  │                                                            │
  │     2. 若质量对象无对应因子：                                │
  │        → 基于质量维度的知识和经验生成"质量因子候选"          │
  │        → 结合 TSP 的 scope 和 purpose 设定合理的取值域       │
  │        → 在公共因子库中检索确认是否已有                      │
  │        → 未命中 → 加入"质量因子候选列表"                     │
  │                                                            │
  │     3. 记录质量因子候选：                                   │
  │        - factor_id / factor_name / data_domain              │
  │        - tsp_ref（所属 TSP）                                  │
  │        - related_quality_object_id                          │
  │        - quality_dimension                                  │
  │        - source=new-quality-candidate                       │
  │        - generation_basis（生成依据，见下方枚举）            │
  │        - scenario_refs / knowledge_refs                     │
  └────────────────────────────────────────────────────────────┘

汇总（所有 TSP 分析完成后）：
  - 同一质量对象/因子被多个 TSP 引用时，合并来源但保留所有 tsp_refs
  - 按 TSP 组织输出，每个 TSP 一组 Q 分析结果
```

**`generation_basis` 枚举**：

| 取值 | 含义 | 示例 |
|------|------|------|
| `行业标准` | 来源于 ISO 25010、IEC 61508、OWASP 等公认标准 | 基于 ISO 25010 可靠性子特性生成的恢复时间因子 |
| `经验推断` | 基于防火墙设备测试经验的通用质量因子 | 基于防火墙掉电恢复经验生成的数据一致性因子 |
| `需求推断` | 从使命陈述、场景描述或风险清单中推断 | 从 KYM 风险清单中「配置丢失风险」推断的配置持久化因子 |

**📤 生产**：

| 产出 | 内容 |
|------|------|
| 逐 TSP 质量对象列表 | `quality_object_id / tsp_ref / quality_dimension / source` |
| **质量因子候选列表** | `factor_id / data_domain / tsp_ref / quality_dimension / generation_basis` |

---

### 步骤 3：逐 TSP 质量测试点生成（CAE 三元组 + trace chain v6）

**📥 消费**：

| 消费数据 | 用途 |
|---------|------|
| 步骤 1 的逐 TSP 相关性评估 | 确定每个 TSP 需要生成的范围 |
| 步骤 2 的逐 TSP 质量对象 + 质量因子 | C 条件和 factor_refs |
| M 分析的测试对象/因子 | 补充引用 |
| `confirmed-scenarios.md` + 全局 atomic-ops | trace 和 A 动作 |

**🔄 处理逻辑**：

```
对每个 TSP 的每个强相关/弱相关维度，按质量维度生成质量测试点：

  - C 条件：前置状态 + 质量约束基线 + 质量因子取值
    （已有因子用具体域，候选因子基于理解预设典型值并标注[待确认]）
  - A 动作：施加质量压力/触发场景
  - E 预期：质量属性表现（量化指标或定性状态）
  - 标注 tsp_ref（回链到 TSP）
  - 测试点按 TSP 组织，每个 TSP 下的测试点按质量维度分组

质量因子全候选降级规则：
  - 若该 TP-Q 的所有关联质量因子 source 均为 new-quality-candidate
    → fact_status 降级为 needs-confirmation
    → C 条件中使用因子域引用（如 @domain.典型值）或基于理解预设典型值并标注 [待确认]
    → E 预期含量化预期并标注 [待确认]
```

每个测试点的字段：

| 字段 | 说明 |
|------|------|
| TP-ID | `TP-Q-<维度缩写>-NNN`（如 TP-Q-REL-001） |
| tsp_ref | 所属 TSP 的 ID |
| 质量维度 | HTSM 维度名称 |
| 子维度 | HTSM 子维度 |
| 关联模块 | 涉及的四/五级目录模块 |
| C 条件 | 触发该质量测试的前置状态或环境条件（含规格基线 / 设备规格 / 压力条件） |
| A 动作 | 施加的操作（含质量压力/场景触发） |
| E 预期 | 可观测的质量属性表现（含量化指标或定性状态） |
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

**📤 生产**：

| 产出 | 文件路径 |
|------|---------|
| 质量测试点（按 TSP 组织，每个 TSP 下按质量维度分组） | `mfq/q-analysis/quality-test-points.md` |

---

### 步骤 4：工具观测能力评估

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

> 若质量观测能力存在不确定性，保留 `covered_objects / covered_factors / io_behavior_matrix`，并通过 `status=needs-confirmation` 显式暴露，不得省略字段来"弱化"不确定性。

**📤 生产**：

| 产出 | 文件路径 |
|------|---------|
| Existing Tool Summary + Capability Gap | `mfq/q-analysis/tool-analysis.md` |

---

### 步骤 5：写入 Q 分析产物

> 追踪链：`SR → Scenario Chain → atomic-ops / Knowledge Reference → TSP → TP-Q(CAE + quality trace) → LC → Test Data → PC`

**⚠️ 写入前置校验**：写入前校验目标父目录 `mfq/q-analysis/` 存在且为目录。若不存在或为普通文件，**停止并提示用户**：`目标目录 mfq/q-analysis/ 不存在或为非目录，请确认 M 分析是否已完成路径初始化`。**禁止执行 `mkdir` 或创建目录**。

写入 `mfq/q-analysis/quality-test-points.md`，按 **TSP（H2）→ 质量维度（H3）**分节，每个 TSP 一节，每节内按质量维度组织 CAE 测试点。

同时写入 `mfq/q-analysis/tool-analysis.md`（Existing Tool Summary + Tool Capability Gap）。

在 `quality-test-points.md` 末尾追加**质量因子候选列表**节，汇总步骤 2 中所有 `source=new-quality-candidate` 的因子候选。

**📤 生产**：

| 文件 | 内容 | 主要消费方 |
|------|------|-----------|
| `quality-test-points.md` | HTSM 相关性评估表 + 按 TSP 组织的 CAE 质量测试点 + 质量因子候选列表 | test-point-integrator |
| `tool-analysis.md` | 工具覆盖评估 | test-point-integrator |

---

### 步骤 6：质量因子候选列表汇总

**📥 消费**：步骤 2 中所有 `source=new-quality-candidate` 的质量因子候选。

**🔄 处理逻辑**：

```
1. 收集步骤 2 中所有 source=new-quality-candidate 的质量因子候选
2. 去重：以 factor_id 为 key 合并同 key 的多源候选
3. 按 TSP 组织成候选汇总表，追加到 quality-test-points.md 末尾
4. 标注每个候选的 generation_basis，供候选汇总阶段的用户确认时提供可信度判断依据
```

候选汇总表格式：

```markdown
## 质量因子候选列表

| factor_id | factor_name | data_domain | tsp_ref | quality_dimension | related_quality_object_id | source | generation_basis | 优先级 |
|-----------|-------------|-------------|---------|-------------------|--------------------------|--------|-----------------|:---:|
| FAC-CAND-Q-001 | ... | ... | TSP-M1 | 可靠性 | Q-OBJ-001 | new-quality-candidate | 经验推断 | 中 |
```

**📤 生产**：质量因子候选列表（嵌入 `quality-test-points.md` 末尾）

---

## 输出文件

全部写入 `mfq/q-analysis/`：

| 文件 | 内容 | 格式 |
|------|------|------|
| `quality-test-points.md` | HTSM 相关性评估表 + 按 TSP 组织、按质量维度分组的 CAE 测试点 + 质量因子候选列表 | 按 TSP（H2）→ 质量维度（H3）分节 |
| `tool-analysis.md` | Existing Tool Summary + Tool Capability Gap | 按工具表 + 缺口表分节 |

## 输出格式

### quality-test-points.md 模板

```markdown
# <特性名> — Q 分析测试点

## HTSM 相关性评估总览

| TSP | 可靠性 | 性能 | 安全性 | 可维护性 | 可安装性 | 兼容性 | 可用性 |
|-----|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| TSP-M1 | 强相关 | 不适用 | 弱相关 | 不适用 | 不适用 | 不适用 | 不适用 |
| TSP-M2 | **强相关** [Q→] | 不适用 | 弱相关 | 弱相关 | 不适用 | 不适用 | 不适用 |
| TSP-M3 | 弱相关 | 弱相关 | 不适用 | 不适用 | 不适用 | 不适用 | 不适用 |

> 标注 `[Q→]` 表示该维度因 [Q→] 标签线索从弱相关提升为强相关或从不适用提升为弱相关。

## TSP-M1: <topic>

### <HTSM 维度>

| TP-ID | tsp_ref | 质量维度 | 子维度 | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `factor_refs` | `fact_status` | 关联模块 |
|-------|---------|---------|--------|--------|--------|--------|-----------------|----------------------|---------------|---------------|---------|
| TP-Q-REL-001 | TSP-M1 | 可靠性 | 可恢复性 | 设备处于正常运行状态；日志服务器已配置 | 执行掉电操作，重新上电后等待设备完全启动 | 日志服务器配置自动恢复；日志发送功能恢复正常 | SCN-LOG-REC-001 | fw_power_cycle | FAC-RECOVERY-TIME | confirmed | 配置管理 |
| TP-Q-REL-002 | TSP-M1 | 可靠性 | 容错性 | 主备双机已配置，均处于正常状态 | 强制主机下线，触发主备切换 | 备机接管成功；日志服务器配置在备机上保持一致；切换期间无配置数据丢失 | SCN-LOG-HA-001 | fw_trigger_ha_switch | FAC-SWITCH-TIME | confirmed | 配置管理 |

### <下一个 HTSM 维度>

...

## TSP-M2: <topic>

### <HTSM 维度>

...

## 质量因子候选列表

| factor_id | factor_name | data_domain | tsp_ref | quality_dimension | related_quality_object_id | source | generation_basis | 优先级 |
|-----------|-------------|-------------|---------|-------------------|--------------------------|--------|-----------------|:---:|
| FAC-CAND-Q-001 | 数据一致性校验结果 | 一致/不一致/部分一致 | TSP-M1 | 可靠性 | Q-OBJ-001 | new-quality-candidate | 经验推断 | 中 |
| FAC-CAND-Q-002 | 计算完成状态确认 | 成功/失败/超时 | TSP-M2 | 可靠性 | Q-OBJ-002 | new-quality-candidate | 需求推断 | 中 |
```

> 若 TP-Q 需要暴露真实端口或 TOPO 实例，在表后附 `topology_binding_refs` 明细表；主表 `factor_refs` 仍只保留逻辑质量因子。

### tool-analysis.md 模板

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
- 不能把缺失的观测工具默认为"人工可观察"；必须输出 tool gap
- `Knowledge Reference=missing/unavailable` 时，可继续分析，但必须保留不确定性
- 不得把 `DUT.port1/TG.port2`、link 或 TOPO 实例写入 `factor_refs / factor_bindings / covered_factors`；真实组网对象必须登记拓扑来源，来源不明则降级 `needs-confirmation`。
- **v3.0 新增：Q 线索缺失不阻断流程** — 若 M 分析的覆盖矩阵不含 Q 线索表或为空，步骤 1 仅基于 TSP.purpose、场景链和需求文档评估相关性，不依赖 Q 线索
- **v3.0 新增：相关性评估不确定项的 OPEN 标记规则** — 判定依据不足时必须标记 OPEN，不得自行判定；步骤 1 末尾汇总所有 OPEN 项单次展示等待用户确认
- **v3.0 新增：generation_basis 取值约束** — 质量因子候选必须标注 generation_basis，只能取「行业标准」「经验推断」「需求推断」三个值之一
- **v3.0 新增：质量对象跨 TSP 去重合并** — 同一质量对象被多个 TSP 引用时合并来源，保留所有 tsp_refs；以 `(quality_object_id, quality_dimension)` 为 key 去重

## 验收标准

- [ ] TSP 列表已加载，逐 TSP 逐维度相关性评估已执行（含 [Q→] 标签消费逻辑）
- [ ] 覆盖矩阵中的 Q 分析线索列表已提取，Q 线索索引已建立
- [ ] 步骤 1 相关性评估不确定项已标记 OPEN，步骤 1 结束时已汇总展示并等待用户确认
- [ ] 每个 TSP 的强相关/弱相关维度已展开质量对象发现（含 quality_object_id / tsp_ref / quality_dimension / source）
- [ ] 质量因子候选已按步骤 2 子步骤 B 发现/生成，标注 generation_basis（行业标准/经验推断/需求推断）
- [ ] 质量因子候选在公共因子库中已检索确认（未命中才加入候选列表）
- [ ] 质量测试点按 TSP 组织、按质量维度分组，每个测试点含 tsp_ref
- [ ] 质量因子全候选时 TP-Q 的 fact_status 已降级为 needs-confirmation
- [ ] 每个测试点包含完整 CAE 三字段（C/A/E 均不为空）
- [ ] C 字段含质量约束基线（规格参数 / 性能基线 / 环境条件）
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 每个 TP-Q 包含 `scenario_refs / action_source_refs / factor_refs / trace_refs / tsp_ref`
- [ ] `factor_refs / factor_bindings / covered_factors` 未混入真实端口、link 或 TOPO 实例；涉及真实组网对象时已登记拓扑来源或降级 `needs-confirmation`
- [ ] 工具观测能力评估输出 `Existing Tool Summary` 和 `Tool Capability Gap`
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式透传
- [ ] 步骤 6 质量因子候选列表已汇总并追加到 `quality-test-points.md` 末尾
- [ ] 输出文件写入 `mfq/q-analysis/quality-test-points.md` 与 `mfq/q-analysis/tool-analysis.md`
- [ ] 写入前已校验目标父目录存在且为目录，未执行 mkdir
