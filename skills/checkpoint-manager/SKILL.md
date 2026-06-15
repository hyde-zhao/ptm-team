---
name: checkpoint-manager
description: >-
  ptm-tde 三阶段门控检查管理：按阶段执行 Gate 检查，包括 Entry Gate、
  KYM Exit Gate、MFQ Exit Gate、PPDCS Exit Gate、Exit Gate。
  触发词包括：checkpoint、checkpoint-manager、gate、GATE-1、GATE-2、
  GATE-3、GATE-4、GATE-5、自检、输入检查、场景自检、检查点。
  适用场景：ptm-tde 所有阶段的门控检查执行与人工确认稿生成。
argument-hint: "gate=<GATE-1|GATE-2|GATE-3|GATE-4|GATE-5>"
user-invokable: true
status: active
---

## 目标

checkpoint-manager 是 ptm-tde 的**共享工具 Skill**，按阶段参数 `gate=<GATE-N>` 执行对应门控检查。本 Skill 不拥有任何阶段的检查逻辑，只提供统一的检查执行框架（Entry Criteria 校验、Checklist 遍历、Exit Criteria 判定、Deliverables 输出）。

**检查规范真相源**：`docs/ptm-tde/gate-spec.md`。所有 Checklist 项、通过条件、失败处理细节以 gate-spec.md 为准，本文件仅保留各 Gate 的关键入口说明和准入条件概要。

checkpoint-manager 只维护 Agent 与 Skill 调用关系，不负责安装。检查点脚本属于本 Skill 私有资产，路径固定为：

```text
skills/checkpoint-manager/scripts/run_checkpoint.py
```

不得把 checkpoint 脚本放到仓库根 `scripts/`。

当前脚本执行的是 **machine-baseline + 字段级结构检查**：除目录和文件存在性外，还会检查关键字段是否存在，例如 GATE-2 的 `normal_path / abnormal_path / action_source_refs / confirmation_gaps`，并逐 `scenario_id` / 场景标题校验每条 confirmed scenario 的正常链、异常链、逐步骤原子操作回链、`minimal_logic_chain` 和 atomic/action 来源；GATE-3 的 CAE、trace、`factor_bindings / topology_bindings`、PPDCS 方法字段，以及候选测试因子 / 候选原子操作的用户确认状态；GATE-4 的标准 16 列 PC 表、`case_steps`、`atomic_op.op_id`、`action_source_refs` 回链和交付 trace 字段。语义质量、风险接受和业务合理性仍由独立 manual Gate 草稿承载。

---

## GATE-1 Entry Gate

**类型**：纯自检（无人工确认）

GATE-1 在 KYM 阶段启动前执行，校验特性项目输入完整性。完整 Checklist 见 `docs/ptm-tde/gate-spec.md` §GATE-1。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| 特性工作区根目录 | 当前 cwd 是单个 `feature_workspace_root`，或可通过 `.input/` 自动解析 |
| 输入目录 | `.input/` 存在且只读对待；legacy `input/` 仅作为兼容 fallback |
| 状态目录 | `process/` 可创建，状态写入 `process/STATE.yaml` |

### Checklist 概要

| # | 检查项 | 通过条件 |
|---|---|---|
| 1 | 需求文件存在 | 用户显式路径、`.input/` 或 wiki 可找到需求文档 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 |
| 3 | 原子操作可用 | 全局命令 `ptm-atomic` 可执行，或 wiki 有原子操作描述 |
| 4 | 防火墙 topo 可用 | `.input/` 下存在 topo 文件，或 wiki 可找到 topo |
| 5 | 耦合矩阵可用 | `.input/` 下存在耦合矩阵，或 wiki 可找到 |
| 6 | 输出目录就绪 | 可创建 `kym/`、`mfq/`、`ppdcs/`、`process/`、`process/checkpoints/`、`process/execution/` |
| 7 | 公共因子库可解析 | `PTM_TEAM_RESOURCE_HOME/factor-libraries` 等路径可访问（警告不阻断） |
| 7a | 公共因子库内容完整 | index.yaml 中声明的每个因子库对应的文件存在（警告不阻断） |
| 7b | 耦合矩阵内容完整 | coupling-matrix/index.yaml 中声明的每个矩阵的 source/feature_tree 文件存在（警告不阻断） |
| 8 | KYM 产物目录就绪 | `kym/mission-understanding/` 目录已创建且可写入 |
| 9 | mission-statement 模板可访问 | kym Skill 的 mission-statement 模板可被读取 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 检查结果 | `process/checkpoints/GATE-1-Entry.md` 已生成 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: kym` 与 GATE-1 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| Entry Gate 检查结果 | `process/checkpoints/GATE-1-Entry.md` |
| 状态文件 | `process/STATE.yaml` |

---

## GATE-2 KYM Exit Gate

**类型**：自检 + 人工确认

GATE-2 在 KYM 阶段完成后、MFQ 阶段启动前执行，校验场景发现产物的完整性。完整 Checklist 见 `docs/ptm-tde/gate-spec.md` §GATE-2。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| 场景产物存在 | `kym/scenarios/confirmed-scenarios.md` 或用户指定的部署型场景文件存在 |
| 目录结构可读 | `kym/feature-input/directory-structure.md` 或等价产物可读 |
| 输入分类完成 | 场景产物包含 `input_document_classification` 或等价输入文档类型识别 |
| 组网输入已处理 | 若存在 `.input/TGFW测试组网图集合.md` 或 topo 文件，场景产物必须说明读取结果 |

### Checklist 概要

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| 1 | 输入文档类型识别 | 覆盖 raw requirement / functional scenario seed / deployment scenario draft / confirmed scenario artifact | 缺失时回到 `scenario-discovery` 补分类 |
| 2 | 功能种子再发现 | functional scenario seed 已进入再发现、头脑风暴、重构与范围收敛，不存在 seed 一对一改写 | 阻断进入 M 分析，要求补 `Seed-to-Scenario Mapping` |
| 3 | Seed-to-Scenario Mapping | 每个 seed 有 split / merge / expand / narrow / out_of_scope / confirmation_gap 处理结论 | 未映射 seed 必须补齐或进入缺口 |
| 4 | 范围收敛 | 用户约束已进入 `scope_constraints`；被排除内容进入 `out_of_scope_candidates` | 缺失时要求补范围决策 |
| 5 | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源、Mermaid、设备/端口/链路表 | 缺失拓扑或自造拓扑时阻断 |
| 6 | ptm-atomic 唯一口径 | `source_type=ptm-atomic`；`action_source_ref` 直接引用 ptm-atomic `op_id` | 出现旧口径时阻断并要求替换 |
| 7 | 场景链完整 | 每个场景包含 `scenario_goal / principle / preconditions / atomic_operations / observation_points / expected_state / minimal_logic_chain / exit_action` | 缺字段时补场景链 |
| 8 | 正常路径可追溯 | 每个 confirmed scenario 的 `normal_path` 包含 `step_id / sub_step_ids / operation / necessity / description`；每个正常步骤必须包含 `action_source_ref(s)`、`atomic_op` 或 `op_id` 并回链场景级 `action_source_refs`；`necessity` 仅使用 `必要 / 可选 / 至少选择一项` | 缺失字段、缺原子操作或取值不规范时补路径建模 |
| 9 | 选择组完整 | 所有 `至少选择一项` 步骤列出可选择子步骤，并说明不能全部跳过；`minimal_logic_chain` 未把选择组或可选步骤写成必做链路 | 选择关系丢失时补结构化语义 |
| 10 | 异常路径可追溯 | 每个 confirmed scenario 的 `abnormal_path` 包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`；每个异常步骤必须包含 `action_source_ref(s)`、`atomic_op` 或 `op_id` 并回链场景级 `action_source_refs`；无异常路径时必须写明 N/A 理由 | 缺少追溯或缺原子操作时补异常路径或进入确认缺口 |
| 11 | Knowledge Reference 三态 | 知识引用保留 `resolved / missing / unavailable`，不得把缺失知识当作已确认事实 | 缺失时补三态或确认缺口 |
| 12 | Tool Gap | 未满足的 ptm-atomic 或工具能力进入 `Tool Abstraction Draft` 或 `confirmation_gaps` | 缺口未记录时阻断 |
| 13 | Confirmation Gaps | 所有不确定事实显式列出，并区分可下传缺口和必须先确认缺口 | 未分类时不得进入 MFQ |
| 14 | 输出质量检查 | 场景产物末尾包含 scenario-discovery 输出质量检查结果，且覆盖路径必要性、选择组、异常追溯和最小逻辑链一致性 | 缺失时补自检结果 |
| N1 | 使命文档存在 | `kym/mission-understanding/mission-statement.md` 可读且非空 | BLOCKING：提示执行 kym Skill 或补充使命文档 |
| N2 | 启发式探索已执行 | 使命文档包含至少 2 个 CIDTESTD 维度的分析记录（含用户扩展维度） | BLOCKING：若 0-1 个维度，提示用户补充关键维度访谈 |
| N3 | 范围边界已界定 | 使命文档包含明确的 scope 和 dont_test 声明 | BLOCKING：范围未界定时提示用户明确 |
| N4 | 待澄清问题已收集 | confirmation_gaps 所有项状态为 resolved 或 accepted_as_risk | WAIVED 或 BLOCKING：用户可选择接受未决问题并 WAIVED，或回 KYM 阶段解决 |

### 人工确认项

| 确认项 | 说明 |
|---|---|
| 目录结构 | 三级/四级/五级目录是否支撑后续 M/F/Q 分析 |
| 场景列表 | 部署、扩容、维护、可靠性、性能等是否覆盖目标范围 |
| Seed-to-Scenario Mapping | 功能初稿如何重构为部署型场景是否可接受 |
| Operation Path | 正常路径步骤、必要性和选择组是否符合真实操作流程 |
| Topology | `topology_ref`、Mermaid、设备/端口/链路是否符合实际组网 |
| ptm-atomic | 每个 `action_source_ref` 是否为真实 ptm-atomic `op_id` |
| Abnormal Path | 异常项是否追溯到具体正常步骤 |
| Confirmation Gaps | 哪些缺口必须先补，哪些可下传到 M/F/Q |
| 使命声明 | 使命声明是否准确反映用户意图（做什么、为什么做、为谁做） |
| 测试关注点优先级 | 测试关注点排序是否符合项目实际（customers.priority + risks.impact 组合） |
| 范围边界 | 排除项是否合理，是否有遗漏（test_items.dont_test 是否覆盖所有不应测试的模块） |
| 启发式探索覆盖 | 维度是否足够，问题是否到位（核心维度 + 扩展维度的覆盖质量） |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 自动自检结果 | `process/checkpoints/GATE-2-KYM-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-2-KYM-Exit-manual.md` 已生成并展示给用户 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: mfq` 与 GATE-2 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| KYM 自检结果 | `process/checkpoints/GATE-2-KYM-Exit-auto.md` |
| KYM 人工确认稿 | `process/checkpoints/GATE-2-KYM-Exit-manual.md` |
| 场景产物 | `kym/scenarios/confirmed-scenarios.md` 或用户指定部署型场景文件 |

### Gotchas

- GATE-2 不是只看"有场景列表"；必须验证场景是否从 seed 经过再发现和收敛。
- `action_source_refs` 是兼容字段，但其值必须是 ptm-atomic `op_id`。
- REST API / CLI / tool-method 只能作为 ptm-atomic 的调用或观测契约，不能作为独立引用类型。
- TGFW 组网集合存在时不得绕过；集合外拓扑只能进入 `confirmation_gaps`。
- GATE-2 必须逐场景检查 `normal_path` 大步骤/子步骤结构、必要性枚举和 `abnormal_path.related_normal_steps`；文件级出现 `normal_path` / `abnormal_path` 字样不等于通过。
- 正常链和异常链中的每个步骤都必须能追溯到 ptm-atomic `op_id`；新增原子操作只能作为候选展示给用户确认，不能静默写成 confirmed。
- 可选步骤和 `至少选择一项` 选择组必须下传到 `minimal_logic_chain` 与结构化补充；不允许在自检中被视为普通必做步骤。
- GATE-2 人工确认前必须把必须先确认的缺口和可下传缺口分开。

---

## GATE-3 MFQ Exit Gate

**类型**：自检 + 人工确认

GATE-3 在 MFQ 阶段完成后、PPDCS 阶段启动前执行，校验 M/F/Q 分析、测试点整合和设计计划的完整性。完整 Checklist 见 `docs/ptm-tde/gate-spec.md` §GATE-3。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| M 分析完成 | `mfq/m-analysis/` 下有 M 分析产物 |
| F 分析完成 | `mfq/f-analysis/` 下有 F 分析产物 |
| Q 分析完成 | `mfq/q-analysis/` 下有 Q 分析产物 |
| 测试点整合完成 | `mfq/integration/` 下有 LC 和 factor_bindings / topology_bindings |
| 设计计划完成 | `process/plan/` 下有设计计划文件 |
| 公共因子库消费记录 | `mfq/factor-usage/factor-library-lock.yaml` 和 `factor-resolution-report.md` 已生成 |

### Checklist 概要

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| M1 | M 分析输出完整 | 每个单功能有 PPDCS 特征标注和 CAE 测试点 | 缺失时回到 M 分析 |
| M2 | F 分析输出完整 | 耦合关系有三源合并，CAE 耦合测试点已生成 | 缺失时回到 F 分析 |
| M3 | Q 分析输出完整 | 质量属性有 HTSM 映射，CAE 质量测试点已生成 | 缺失时回到 Q 分析 |
| M4 | 测试点整合完整 | M+F+Q 测试点归集到 LC，包含 factor_bindings 和 topology_bindings | 缺失时回到整合 |
| M5 | LC topology_bindings 一致 | topology_bindings 从 `kym/scenarios/confirmed-scenarios.md` 绑定真实组网对象 | 无法绑定时写 `needs-confirmation` |
| M6 | 设计计划存在 | `process/plan/` 下有 CAE→PPDCS 推断和设计计划，格式符合 PPDCS 消费契约 | 缺失或格式错误时回到 plan |
| M7 | 公共因子库 lock 有效 | factor_bindings 中的 `factor_id / sample_id` 能在 lock 指定公共库中找到 | 缺失时补充因子消费记录 |
| M8 | 因子库扫描完整性 | `factor-resolution-report.md` 中 N_scanned / index.yaml 扫描证据已记录 | 不完整时回到 M 分析 |
| M9 | 原子操作匹配完整性 | 候选原子操作记录 match_attempt / L1-L4 / score | 缺失时回到 M 分析补匹配 |
| M10 | 候选测试因子显式确认状态 | 存在候选因子来源时，`mfq/candidates/factor-candidates.md` 或等价文件必须记录 `decision=confirmed/rejected/modified` | 缺确认时回到候选汇总确认 |
| M11 | 候选原子操作显式确认状态 | 存在候选原子操作来源时，`mfq/candidates/ptm-atomic-candidates.md` 或等价文件必须记录 `decision=confirmed/rejected/modified` | 缺确认时回到候选汇总确认 |

### 上下游 Warning（非阻断）

| # | 检查项 | 说明 | 级别 |
|---|---|---|---|
| W1 | KYM 场景下游可消费 | 场景产物可被 MFQ 正确消费 | Warning 提示 |
| W2 | PPDCS 可消费 plan | 设计计划可被 PPDCS 阶段正确读取 | Warning 提示，PPDCS Exit Gate 二次检查 |

### 人工确认项

| 确认项 | 说明 |
|---|---|
| M/F/Q 分析质量 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。各维度分析是否覆盖完整 |
| LC 整合一致性 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。测试点归集、因子绑定和拓扑绑定是否一致 |
| 设计计划 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。CAE→PPDCS 推断是否合理 |
| 公共因子消费 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。因子库 lock 和候选提案是否合理 |
| 候选测试因子与候选原子操作 | ⛔ HARD-STOP：必须展示候选汇总表和确认结果；用户未确认时不得将候选写入最终产物或进入 PPDCS |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 自动自检结果 | `process/checkpoints/GATE-3-MFQ-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-3-MFQ-Exit-manual.md` 已生成并展示给用户 |
| Warning 项 | 已展示给用户，用户知悉 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: ppdcs` 与 GATE-3 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| MFQ 自检结果 | `process/checkpoints/GATE-3-MFQ-Exit-auto.md` |
| MFQ 人工确认稿 | `process/checkpoints/GATE-3-MFQ-Exit-manual.md` |
| MFQ 全部产物 | `mfq/` 目录 |

### 执行协议

> 基于 HLD §11（CR-012 v1.1）定义的硬停止规则。GATE-3 人工确认必须遵守以下协议。

| 规则 ID | 适用场景 | 规则内容 |
|---------|---------|---------|
| STOP-01 | GATE-3 人工确认 | ⛔ HARD-STOP：禁止 Agent 在人工确认项上自行判定"通过"或"质量很高"。必须等待用户回复 `approve` / `修改: ...` / `reject`。未收到用户回复前不得推进到 PPDCS 阶段 |
| STOP-02 | 候选汇总确认 | ⛔ HARD-STOP：禁止 Agent 自行判定候选因子/原子操作为"全部确认"。必须展示候选汇总表，等待用户选择确认选项 |
| STOP-03 | Skill 调用链 | ⛔ HARD-STOP：禁止 Agent 绕过 Skill 直接生成 MFQ 产物。M/F/Q 分析必须通过对应的 Skill 调用执行 |
| STOP-04 | 路径写入校验 | ⛔ HARD-STOP：Skill 写入产物前必须校验目标父目录存在且为目录。禁止 Agent 手动 mkdir 创建目录 |
| STOP-05 | 确认选项视觉区分 | 所有需要用户选择的环节，必须使用 `( )` 单选 / `[ ]` 多选 / `>>>` 开放式 三类标记区分，禁止纯数字列表 |
| STOP-06 | 交互降级 | Claude Code 且 `AskUserQuestion` 可用时可使用结构化选择；Codex 或工具不可用时必须回退到 STOP-05 文本标记。禁止在工具不可用时仍尝试 Claude-only 工具 |

### 人工确认交互方式（平台分支）

GATE-2 / GATE-3 / GATE-4 的人工确认必须按平台能力分支：

- Claude Code 且 `AskUserQuestion` 可用：使用结构化选择。
- Codex 或结构化工具不可用：使用 exact text 协议。

Claude Code `AskUserQuestion` 参数：

- question: "请对 GATE-N 检查结果做出决策："
- header: "Gate decision"
- multiSelect: false
- options:
  1. label: "Approve", description: "接受全部推荐方案，放行进入下一阶段"
  2. label: "Modify", description: "输入修改内容。格式：修改: <决策ID>=<具体修改点>"
  3. label: "Reject", description: "驳回当前阶段，需要重新处理"

Codex 或 `AskUserQuestion` 不可用时，回退到标准 HARD-STOP 文本协议（`approve` / `修改: <具体修改点>` / `reject`）。

Agent 收到选择结果后的 Decision Brief 解析逻辑不变，仅输入通道不同。

---

## GATE-4 PPDCS Exit Gate

**类型**：自检 + 人工确认

GATE-4 在 PPDCS 阶段完成后、交付前执行，校验 PPDCS 设计、PC 生成和覆盖率。完整 Checklist 见 `docs/ptm-tde/gate-spec.md` §GATE-4。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| PPDCS 设计完成 | `ppdcs/ppdcs/` 下每个 LC 有 PPDCS 设计过程文件 |
| PC 生成完成 | `ppdcs/pc/` 下每个 LC 有物理用例文件 |
| 覆盖率验证完成 | `ppdcs/coverage/` 下有覆盖率报告 |

### Checklist 概要

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| P1 | PPDCS 设计过程完整 | `ppdcs/ppdcs/` 下每个 LC 都有设计过程文件，PPDCS 方法与 plan 推荐一致 | 缺失时回到 PPDCS 设计 |
| P2 | PC 文件完整 | `ppdcs/pc/` 下每个 LC 都有物理用例文件；PC 表头等于标准 16 列，所有数据行恰好 16 列；每条 PC 包含 `case_steps`，每一步同时包含 `step_name` 与 `atomic_op.op_id`，且 op_id 回链到 `action_source_refs` | 缺失时回到 PC 生成 |
| P3 | PC 拓扑绑定回链 | PC 中所有真实设备、端口、链路能回链到 LC `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` | 无回链时不得标记 confirmed |
| P4 | 双层覆盖率验证 | `ppdcs/coverage/` 存在覆盖率报告：需求覆盖 = 100%，测试点覆盖 ≥ 95% | 未达标时补用例 |
| P5 | 因子覆盖验证 | 所有 `factor_bindings` 的因子在 PC 中有覆盖 | 缺失覆盖时回到设计阶段补因子映射 |
| P6 | 交付物完整 | `ppdcs/delivery/` 包含测试方案和测试用例；测试用例全文只有一张标准 16 列 PC 汇总表，且 `测试步骤*` 单元格包含 `原子操作：<op_id>` | 缺失或多余时修正交付物 |
| P7 | 交付物字段保留 | 交付物保留 `logic_case_id / physical_case_id / case_steps / action_source_refs / topology_bindings / topology_role / source / fact_status` | 字段缺失时修正渲染逻辑 |

### 人工确认项

| 确认项 | 说明 |
|---|---|
| PPDCS 设计方法 | 每个 LC 的 PPDCS 方法选择是否合理，设计步骤是否完整 |
| 物理用例质量 | PC 编号、组网描述、测试步骤、预期结果是否满足标准 |
| 覆盖率结果 | 需求覆盖率、测试点覆盖率是否达标，未覆盖项是否可接受 |
| 拓扑绑定 | needs-confirmation 项是否已处理或记录为风险 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 自动自检结果 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-4-PPDCS-Exit-manual.md` 已生成并展示给用户 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: exit` 与 GATE-4 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| PPDCS 自检结果 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` |
| PPDCS 人工确认稿 | `process/checkpoints/GATE-4-PPDCS-Exit-manual.md` |
| PPDCS 全部产物 | `ppdcs/` 目录 |

---

## GATE-5 Exit Gate

**类型**：纯自检（无人工确认）

GATE-5 在所有阶段完成后执行，校验最终交付物的完整性和正确性。完整 Checklist 见 `docs/ptm-tde/gate-spec.md` §GATE-5。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| GATE-4 已通过 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` 状态为 PASS |
| 交付物存在 | `ppdcs/delivery/` 下有两份交付文件 |

### Checklist 概要

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| 1 | 交付物完整 | `<特性名>特性测试方案.md` 和 `<特性名>特性测试用例.md` 均存在 | 缺失时回到交付渲染 |
| 2 | 交付字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` | 渲染前修正字段 |
| 3 | 公共库记录 | 测试方案记录公共库 `library_id / version / checksum` 和样本策略摘要 | 缺失时补充 |
| 4 | 不可提升状态 | 交付物中 `needs-confirmation` 未被提升为 `confirmed` | 发现提升时修正 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 检查结果 | `process/checkpoints/GATE-5-Exit.md` 已生成 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: completed` |

### Deliverables

| 产物 | 路径 |
|---|---|
| Exit Gate 检查结果 | `process/checkpoints/GATE-5-Exit.md` |
| 最终交付物 | `ppdcs/delivery/<特性名>特性测试方案.md`、`ppdcs/delivery/<特性名>特性测试用例.md` |

---

## Wiki 兜底规则

当本地 `.input/` 中缺少原子操作、topo 或耦合矩阵信息时，必须按以下顺序查询 wiki：

1. 原子操作描述文档；
2. 特性接口文档；
3. 防火墙 topo / 组网描述；
4. 耦合矩阵或功能耦合关系文档。

wiki 查询结果只能作为只读引用写入检查点证据，不得回写 wiki。

---

## 公共因子库检查补充

`ptm-tde` 使用公共因子库时，各 Gate 的检查责任分配如下：

- **GATE-1**：检查公共 resource 根目录是否可解析：`PTM_TEAM_RESOURCE_HOME/factor-libraries`、`~/.ptm-team/resource/factor-libraries` 或开发态 `resource/factor-libraries`。同时读取 `index.yaml`，逐项验证每个 `library_id` 对应的 `path` 文件是否存在。不可访问或内容缺失时警告但不阻断。
- **GATE-3**：检查 `mfq/factor-usage/factor-library-lock.yaml` 和 `factor-resolution-report.md` 已生成；若存在未命中因子或扩展建议，必须确认 `candidate-factor-proposals.yaml` 已生成，且没有直接修改公共主库；确认 `factor_bindings` 中的 `factor_id / sample_id` 能在 lock 指定公共库中找到。
- **GATE-4**：检查所有 `factor_bindings` 的因子在 PC 中有覆盖（P5），且可在 lock 指定公共库中回查（覆盖率阶段二次确认）。
- **GATE-5**：检查测试方案记录公共库 `library_id / version / checksum` 和样本策略摘要。

---

## 跨阶段拓扑绑定检查

以下检查贯穿所有阶段，用于保证测试因子、拓扑角色和真实组网对象分层。路径引用以 `kym/scenarios/confirmed-scenarios.md` 为场景真相源。完整说明见 `docs/ptm-tde/gate-spec.md` §跨阶段拓扑绑定检查。

| 阶段 | 检查项 | 通过条件 |
|------|--------|----------|
| KYM (GATE-2) | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源、Mermaid、设备/端口/链路表 |
| MFQ (M 分析) | CAE topology role | M 输出只包含 `topology_role_refs`，不包含真实端口作为 factor value |
| MFQ (整合) | LC topology bindings | LC `topology_bindings` 从 `kym/scenarios/confirmed-scenarios.md` 绑定真实组网对象 |
| PPDCS (设计) | PPDCS 消费绑定 | 设计引用 `topology_binding_refs`，不重新发明真实端口 |
| PPDCS (PC) | PC materialization | PC 中真实端口均能回链到 LC `topology_bindings` |
| PPDCS (覆盖) | 覆盖状态保持 | 不把 `needs-confirmation` 提升为 `confirmed` |
| PPDCS (交付) | 交付字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

公共因子校验与拓扑绑定校验并行存在：`factor_bindings` 用于公共因子与样本覆盖，`topology_bindings` 只用于真实组网对象回链。

---

## CP↔Gate 兼容映射

旧 CP 编号通过以下映射自动路由到对应 Gate：

| 旧 CP | 新 Gate | 说明 |
|-------|---------|------|
| CP01 | GATE-1 Entry Gate | input 自检（纯自检） |
| CP02 | GATE-2 KYM Exit Gate | 场景自检 + 人工确认 |
| CP03 | MFQ 阶段内滚动自检 | M 分析完整性 |
| CP04 | MFQ 阶段内滚动自检 | F 分析完整性 |
| CP05 | MFQ 阶段内滚动自检 | Q 分析完整性 |
| CP06 | MFQ 阶段内滚动自检 | 整合完整性 |
| CP07 | MFQ 阶段内滚动自检 | 设计计划完整性 |
| — | GATE-3 MFQ Exit Gate | MFQ 出口人工确认（新增） |
| CP08 | PPDCS 阶段内滚动自检 | PPDCS 设计完整性 |
| CP09 | GATE-4 PPDCS Exit Gate | PPDCS 设计确认 |
| CP10 | PPDCS 阶段内滚动自检 | PC 生成完整性 |
| CP11 | GATE-4 PPDCS Exit Gate | 覆盖率确认 |
| CP12 | GATE-5 Exit Gate | 交付自检（纯自检） |

---

## 脚本用法

按 Gate 执行：

```bash
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py --gate GATE-1 --project-root .
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py --gate GATE-2 --project-root .
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py --gate GATE-3 --project-root .
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py --gate GATE-4 --project-root .
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py --gate GATE-5 --project-root .
```

旧 CP 编号兼容参数（自动路由到对应 Gate）：

```bash
--cp CP01  # 路由到 GATE-1
--cp CP02  # 路由到 GATE-2
--cp CP03  # 路由到 MFQ 阶段内 M 分析自检
--cp CP04  # 路由到 MFQ 阶段内 F 分析自检
--cp CP05  # 路由到 MFQ 阶段内 Q 分析自检
--cp CP06  # 路由到 MFQ 阶段内整合自检
--cp CP07  # 路由到 MFQ 阶段内设计计划自检
--cp CP08  # 路由到 PPDCS 阶段内设计自检
--cp CP09  # 路由到 GATE-4（设计确认）
--cp CP10  # 路由到 PPDCS 阶段内 PC 自检
--cp CP11  # 路由到 GATE-4（覆盖率确认）
--cp CP12  # 路由到 GATE-5
```

可选参数：

```bash
--feature-name "<特性名>"
--input-dir ".input"
--requirement ".input/<需求文件>"
--wiki-index "<wiki导出索引或检索结果>"
```

记录 Skill 执行证据：

```bash
--record-skill-call \
--project-root "<feature_workspace_root>" \
--skill-name "feature-parser" \
--phase "kym" \
--status completed \
--input-ref ".input/<需求文件>" \
--output-ref "kym/feature-input/raw-requirements.md" \
--evidence-summary "feature-parser completed"
```

`status=completed` 时必须至少提供一个 `--output-ref`。GATE-2/3/4 会结构化读取 `process/execution/SKILL-CALLS.yaml`，只接受对应 Skill 的 `status=completed` 且存在 `output_refs` 的记录。

---

## Gotchas

- `ptm-atomic` 是全局命令，不允许硬编码某个项目路径。
- GATE-1 发现 wiki 缺失时应提示用户提供材料，不得虚构 topo、接口或耦合矩阵。
- 检查点文件属于特性项目运行产物，写入 `process/checkpoints/`，不是 ptm-tde 仓库 `process/checks/`。
- `.input/` 只读；若需派生 Markdown 或结构化摘要，写入 `kym/feature-input/` 而非旧路径 `analysis/feature-input/`。
- 同一仓库存在多个 `.input/` 且未指定 `--project-root` 或 `--input-dir` 时，必须阻断并要求用户选择。
- GATE-2/3/4 会结构化读取 `process/execution/SKILL-CALLS.yaml` 验证关键 Skill 的 `completed` 证据；缺证据不得推进。
- checkpoint-manager 是**共享工具 Skill**，不拥有任何阶段逻辑；各阶段 Skill 调用时必须传入正确的 `gate` 参数。
- `docs/ptm-tde/gate-spec.md` 是检查规范**真相源**，本 Skill 只负责执行；若 Checklist 细节与 gate-spec.md 冲突，以 gate-spec.md 为准。
- GATE-3 的上下游 Warning（W1、W2）是非阻断项，仅提示用户注意阶段边界消费关系。

---

## 验收标准

- [ ] 覆盖全部 5 个 Gate（GATE-1 至 GATE-5）
- [ ] GATE-1 输出写入 `process/checkpoints/GATE-1-Entry.md`
- [ ] GATE-2 输出写入 `process/checkpoints/GATE-2-KYM-Exit-auto.md` 和 `process/checkpoints/GATE-2-KYM-Exit-manual.md`
- [ ] GATE-3 输出写入 `process/checkpoints/GATE-3-MFQ-Exit-auto.md` 和 `process/checkpoints/GATE-3-MFQ-Exit-manual.md`
- [ ] GATE-4 输出写入 `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` 和 `process/checkpoints/GATE-4-PPDCS-Exit-manual.md`
- [ ] GATE-5 输出写入 `process/checkpoints/GATE-5-Exit.md`
- [ ] 支持 `--cp` 兼容参数自动路由到对应 `--gate`
- [ ] 支持 `--gate <GATE-N>` 参数执行对应 Gate 检查
- [ ] 公共因子库检查分散到各 Gate 中（GATE-1 可解析、GATE-3 lock 有效、GATE-4 可回查、GATE-5 交付记录）
- [ ] 跨阶段拓扑绑定检查路径引用 `kym/scenarios/confirmed-scenarios.md`
- [ ] 脚本位于 `skills/checkpoint-manager/scripts/run_checkpoint.py`
- [ ] 不依赖安装器或安装清单
