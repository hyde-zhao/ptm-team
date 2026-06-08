# ptm-tde 门控规范（Gate Spec）

> **修订记录**
> | 版本 | 日期 | 修订人 | 变更要点 |
> |------|------|--------|----------|
> | v1.0 | 2026-06-01 | meta-po | 初始版本，替代 checkpoint-spec v1（归档为 checkpoint-spec-v1-archived.md） |
| v1.1 | 2026-06-01 | meta-dev | [M4] 每个 Gate 章节 Deliverables 后增加「实现深度说明」：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 或后续 CR 激活。 |
| v1.3 | 2026-06-02 | meta-dev | [CR-011] GATE-1 新增 #8（KYM 产物目录就绪）+ #9（mission-statement 模板可访问）；GATE-2 新增 N1-N4（使命文档存在/启发式探索已执行/范围边界已界定/待澄清问题已收集）+ 4 项人工确认项（使命声明/测试关注点优先级/范围边界/启发式探索覆盖） |
| v1.4 | 2026-06-02 | meta-dev | [CR-012] GATE-3 Checklist 编号统一为 M1-M7+W1-W2，增加人工确认 HARD-STOP 标记和 STOP-01~05 执行协议引用 |
| v1.5 | 2026-06-06 | meta-dev | [CR-017] GATE-3 Checklist 新增 M8（因子库扫描完整性）；Entry Criteria「公共因子库消费记录」增加 N_scanned 校验要求 |

## 概述

ptm-tde 采用 **三阶段 + 入口/出口门控** 体系。每个阶段拥有各自的检查点（自检 + 人工），由 `checkpoint-manager` 作为共享工具 Skill 按阶段参数执行。

### 阶段划分

| 阶段 | 包含步骤 | 阶段内检查点 |
|------|----------|-------------|
| **KYM**（Know Your Mission） | feature-parser → scenario-discovery | 自动检查 + 人工确认 |
| **MFQ**（M/F/Q Analysis） | m-analyzer → f-analyzer → q-analyzer → test-point-integrator → design-planner | 阶段内滚动自检 + 出口人工确认 |
| **PPDCS**（Design & Delivery） | design-ppdcs-analyzer + 5设计Skill → PC → coverage-verifier → deliverable-renderer | 阶段内滚动自检 + 出口人工确认 |

### 门控总览

| Gate | 名称 | 类型 | 位置 |
|------|------|------|------|
| GATE-1 | Entry Gate | 纯自检 | KYM 启动前 |
| GATE-2 | KYM Exit Gate | 自检 + 人工 | KYM → MFQ 边界 |
| GATE-3 | MFQ Exit Gate | 自检 + 人工 | MFQ → PPDCS 边界 |
| GATE-4 | PPDCS Exit Gate | 自检 + 人工 | PPDCS 交付前 |
| GATE-5 | Exit Gate | 纯自检 | 全流程结束 |

### CP↔Gate 映射表

| 旧 CP | 新 Gate | 说明 |
|-------|---------|------|
| CP01 | GATE-1 Entry Gate | input 自检 |
| CP02 | GATE-2 KYM Exit Gate | 场景自检 + 人工确认 |
| CP03 | MFQ 阶段内滚动自检 | M 分析完整性 |
| CP04 | MFQ 阶段内滚动自检 | F 分析完整性 |
| CP05 | MFQ 阶段内滚动自检 | Q 分析完整性 |
| CP06 | MFQ 阶段内滚动自检 | 整合完整性 |
| CP07 | MFQ 阶段内滚动自检 | 设计计划完整性 |
| — | GATE-3 MFQ Exit Gate | 新增：MFQ 出口人工确认 |
| CP08 | PPDCS 阶段内滚动自检 | PPDCS 设计完整性 |
| CP09 | GATE-4 PPDCS Exit Gate | PPDCS 设计确认 |
| CP10 | PPDCS 阶段内滚动自检 | PC 生成完整性 |
| CP11 | GATE-4 PPDCS Exit Gate | 覆盖率确认 |
| CP12 | GATE-5 Exit Gate | 交付自检 |

### CP 兼容路由规则

当工具链使用旧 CP 编号调用 checkpoint-manager 时，按以下规则路由到对应 Gate 或阶段内自检：

| 旧 CP | 路由目标 | 触发行为 | 输出路径 |
|-------|---------|---------|---------|
| CP01 | GATE-1 | 执行 GATE-1 Entry Gate 完整检查（当前为骨架） | `process/checkpoints/GATE-1-Entry.md` |
| CP02 | GATE-2 | 执行 GATE-2 KYM Exit Gate 完整检查（当前为骨架） | `process/checkpoints/GATE-2-KYM-Exit-auto.md` |
| CP03 | MFQ 阶段内自检 | 检查 M 分析产物目录存在性 | `process/checkpoints/MFQ-internal-CP03.md` |
| CP04 | MFQ 阶段内自检 | 检查 F 分析产物目录存在性 | `process/checkpoints/MFQ-internal-CP04.md` |
| CP05 | MFQ 阶段内自检 | 检查 Q 分析产物目录存在性 | `process/checkpoints/MFQ-internal-CP05.md` |
| CP06 | MFQ 阶段内自检 | 检查整合产物目录存在性 | `process/checkpoints/MFQ-internal-CP06.md` |
| CP07 | MFQ 阶段内自检 | 检查设计计划产物目录存在性 | `process/checkpoints/MFQ-internal-CP07.md` |
| CP08 | PPDCS 阶段内自检 | 检查 PPDCS 设计产物目录存在性 | `process/checkpoints/PPDCS-internal-CP08.md` |
| CP09 | GATE-4 | 执行 GATE-4 PPDCS Exit Gate 完整检查（当前为骨架） | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` |
| CP10 | PPDCS 阶段内自检 | 检查 PC 产物目录存在性 | `process/checkpoints/PPDCS-internal-CP10.md` |
| CP11 | GATE-4 | 执行 GATE-4 PPDCS Exit Gate 完整检查（当前为骨架，与 CP09 路由相同） | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` |
| CP12 | GATE-5 | 执行 GATE-5 Exit Gate 完整检查（当前为骨架） | `process/checkpoints/GATE-5-Exit.md` |

**路由实现说明**：
- CP01/CP02/CP09/CP11/CP12 路由到独立 Gate handler（`dispatch_gate`）
- CP03-CP07 路由到 MFQ 阶段内滚动自检（`run_internal_check`）
- CP08/CP10 路由到 PPDCS 阶段内滚动自检（`run_internal_check`）
- 阶段内自检输出轻量级摘要到 stdout 和对应 `process/checkpoints/` 文件，不生成独立 Gate 输出
- CP09 和 CP11 均路由到 GATE-4（在原体系分别对应设计确认和覆盖率确认，当前骨架版本不区分检查重点，详细区分由后续 CR 实现）

---

## GATE-1 Entry Gate

### Entry Criteria

| 条目 | 要求 |
|------|------|
| 特性项目根目录 | 当前 cwd 是单个特性项目根目录 |
| 输入目录 | `input/` 存在且只读对待 |
| 状态目录 | `process/` 可创建，状态写入 `process/STATE.yaml` |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|--------|----------|----------|
| 1 | 需求文件存在 | 用户显式路径存在，或 `input/` 下存在需求文件，或 wiki 可找到需求文档 | 提示用户提供需求文件 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 | 提示用户提供特性名 |
| 3 | 原子操作可用 | 全局命令 `ptm-atomic` 可执行；`ptm-atomic list --format json` 返回全部操作清单（含 tags + parameters_summary） | 提示用户补充；WARNING 不阻断，m-analyzer 降级精确匹配 |
| 4 | 防火墙 topo 可用 | `input/` 下存在 topo 文件，或 `resource/network-topology/topology-collection.md` 可访问，或 wiki 可找到 topo | 提示用户提供 |
| 5 | 耦合矩阵与特性树可用 | `input/` 下存在耦合矩阵或特性树文件，或 `resource/coupling-matrix/` 下 `tgfw-coupling-matrix.yaml` 和 `tgfw-feature-tree.yaml` 至少一个可访问 | WARNING 不阻断；仅存在一个时提示缺失方将在后续步骤中由模型推理补充 |
| 6 | 输出目录就绪 | 可创建 `kym/`、`mfq/`、`ppdcs/`、`process/`、`process/checkpoints/` | 无权限或路径冲突时阻断 |
| 7 | 公共因子库可解析 | `PTM_TEAM_RESOURCE_HOME/factor-libraries`、`~/.ptm-team/resource/factor-libraries` 或开发态 `resource/factor-libraries` 可访问 | 警告但不阻断 |
| 8 | KYM 产物目录就绪 | `kym/mission-understanding/` 目录已创建且可写入 | 尝试创建；创建失败（权限/路径被普通文件占用）→ BLOCKING |
| 9 | mission-statement 模板可访问 | kym Skill 的 mission-statement 模板可被读取 | BLOCKING（模板是 kym Skill 正常运行的前提） |
| 10 | 组网图资源可用 | `resource/network-topology/topology-collection.md` 可访问 | WARNING 不阻断，缺失时场景设计阶段组网匹配降级为模型推理 |

### Exit Criteria

| 条目 | 要求 |
|------|------|
| 检查结果 | `process/checkpoints/GATE-1-Entry.md` 已生成 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: kym` 与 GATE-1 结果 |

### Deliverables

| 产物 | 路径 |
|------|------|
| Entry Gate 检查结果 | `process/checkpoints/GATE-1-Entry.md` |
| 状态文件 | `process/STATE.yaml` |

> **实现深度说明**：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 按本 gate-spec.md 执行或后续 CR 激活。

---

## GATE-2 KYM Exit Gate

### Entry Criteria

| 条目 | 要求 |
|------|------|
| 场景产物存在 | `kym/scenarios/confirmed-scenarios.md` 或用户指定的部署型场景文件存在 |
| 目录结构可读 | `kym/feature-input/directory-structure.md` 或等价产物可读 |
| 输入分类完成 | 场景产物包含 `input_document_classification` |
| 组网输入已处理 | 若存在 `input/TGFW测试组网图集合.md`、topo 文件或 `resource/network-topology/topology-collection.md`，场景产物必须说明读取结果 |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|--------|----------|----------|
| 1 | 输入文档类型识别 | 覆盖 raw requirement / functional scenario seed / deployment scenario draft / confirmed scenario artifact | 回到 `scenario-discovery` 补分类 |
| 2 | 功能种子再发现 | functional scenario seed 已进入再发现、头脑风暴、重构与范围收敛 | 阻断，要求补 Seed-to-Scenario Mapping |
| 3 | Seed-to-Scenario Mapping | 每个 seed 有 split / merge / expand / narrow / out_of_scope / confirmation_gap 处理结论 | 未映射 seed 必须补齐 |
| 4 | 范围收敛 | 用户约束进入 `scope_constraints`；排除项进入 `out_of_scope_candidates` | 缺失时要求补范围决策 |
| 5 | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源（`resource/network-topology/` 优先 → `input/` → wiki）、Mermaid、设备/端口/链路表 | 缺失拓扑时阻断 |
| 6 | ptm-atomic 唯一口径 | `source_type=ptm-atomic`；`action_source_ref` 引用 ptm-atomic `op_id` | 出现旧口径时阻断 |
| 7 | 场景链完整 | 每个场景包含目标、原理、前置条件、原子操作、观察点、预期状态、最小逻辑链、退出动作 | 缺字段时补场景链 |
| 8 | 正常路径可追溯 | `normal_path` 包含 `step_id / sub_step_ids / operation / necessity / description`，`necessity` 仅使用 `必要 / 可选 / 至少选择一项` | 缺字段或取值不规范时补路径建模 |
| 9 | 选择组完整 | `至少选择一项` 步骤列出可选择子步骤；`minimal_logic_chain` 未把可选步骤写成必做 | 选择关系丢失时补结构化语义 |
| 10 | 异常路径可追溯 | 每条异常路径包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling` | 缺少追溯时补异常路径 |
| 11 | Knowledge Reference 三态 | 保留 `resolved / missing / unavailable` | 混写或缺失时补齐 |
| 12 | Tool Gap | 未满足的 ptm-atomic 进入 `Tool Abstraction Draft` 或 `confirmation_gaps` | 缺口未记录时阻断 |
| 13 | Confirmation Gaps | 区分可下传缺口和必须先确认缺口 | 未分类时不得进入 MFQ |
| 14 | 输出质量检查 | 场景产物包含 scenario-discovery 输出质量检查结果 | 缺失时补自检结果 |
| N1 | 使命文档存在 | `kym/mission-understanding/mission-statement.md` 可读且非空 | BLOCKING：提示执行 kym Skill 或补充使命文档 |
| N2 | 启发式探索已执行 | 使命文档包含至少 2 个 CIDTESTD 维度的分析记录（含用户扩展维度） | BLOCKING：若 0-1 个维度，提示用户补充关键维度访谈 |
| N3 | 范围边界已界定 | 使命文档包含明确的 scope 和 dont_test 声明 | BLOCKING：范围未界定时提示用户明确 |
| N4 | 待澄清问题已收集 | confirmation_gaps 所有项状态为 resolved 或 accepted_as_risk | WAIVED 或 BLOCKING：用户可选择接受未决问题并 WAIVED，或回 KYM 阶段解决 |

### 人工确认项

| 确认项 | 说明 |
|--------|------|
| 目录结构 | 三级/四级/五级目录是否支撑后续 M/F/Q 分析。**四级/五级目录划分优先级**：① 优先从 `resource/coupling-matrix/tgfw-feature-tree.yaml` 读取匹配；② 特性树中无匹配时由模型推理生成，推理结果标记 `source: model-inference` 与特性树来源 `source: feature-tree` 区分 |
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
|------|------|
| 自动自检结果 | `process/checkpoints/GATE-2-KYM-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-2-KYM-Exit-manual.md` 已生成并展示给用户 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: mfq` 与 GATE-2 结果 |

### Deliverables

| 产物 | 路径 |
|------|------|
| KYM 自检结果 | `process/checkpoints/GATE-2-KYM-Exit-auto.md` |
| KYM 人工确认稿 | `process/checkpoints/GATE-2-KYM-Exit-manual.md` |
| 场景产物 | `kym/scenarios/confirmed-scenarios.md` |

> **实现深度说明**：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 按本 gate-spec.md 执行或后续 CR 激活。

---

## GATE-3 MFQ Exit Gate

### Entry Criteria

| 条目 | 要求 |
|------|------|
| M 分析完成 | `mfq/m-analysis/` 下有 M 分析产物 |
| F 分析完成 | `mfq/f-analysis/` 下有 F 分析产物 |
| Q 分析完成 | `mfq/q-analysis/` 下有 Q 分析产物 |
| 测试点整合完成 | `mfq/integration/` 下有 LC 和 factor_bindings / topology_bindings |
| 设计计划完成 | `process/plan/` 下有设计计划文件 |
| 公共因子库消费记录 | `mfq/factor-usage/factor-library-lock.yaml` 已生成；`factor-resolution-report.md` 存在，且 N_scanned 等于 index.yaml 注册库数 |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|--------|----------|----------|
| M1 | M 分析输出完整 | 每个单功能有 PPDCS 特征标注和 CAE 测试点 | 缺失时回到 M 分析 |
| M2 | F 分析输出完整 | 耦合关系有三源合并，CAE 耦合测试点已生成 | 缺失时回到 F 分析 |
| M3 | Q 分析输出完整 | 质量属性有 HTSM 映射，CAE 质量测试点已生成 | 缺失时回到 Q 分析 |
| M4 | 测试点整合完整 | M+F+Q 测试点归集到 LC，包含 `factor_bindings` 和 `topology_bindings` | 缺失时回到整合 |
| M5 | LC topology_bindings 一致 | `topology_bindings` 从 `kym/scenarios/confirmed-scenarios.md` 绑定真实组网对象 | 无法绑定时写 `needs-confirmation` |
| M6 | 设计计划存在 | `process/plan/` 下有 CAE→PPDCS 推断和设计计划，格式符合 PPDCS 消费契约 | 缺失或格式错误时回到 plan |
| M7 | 公共因子库 lock 有效 | `factor_bindings` 中的 `factor_id / sample_id` 能在 lock 指定公共库中找到 | 缺失时补充因子消费记录 |
| M8 | 因子库扫描完整性 | `factor-resolution-report.md` 中 N_scanned == index.yaml 注册库数 | 不等时阻断（M 分析因子库扫描不完整） |
| M9 | 原子操作匹配完整性 | `candidate-ptm-atomic.yaml` 中每个候选记录了 match_attempt（L1-L4 + score）；ptm-atomic-resolution-report.md 存在 | 缺失 match_attempt 时回到 M 分析补语义匹配 |

### 上下游 Warning（非阻断）

| # | 检查项 | 说明 |
|---|--------|------|
| W1 | KYM 场景下游可消费 | 场景产物可被 MFQ 正确消费 | Warning 提示 |
| W2 | PPDCS 可消费 plan | 设计计划可被 PPDCS 阶段正确读取 | Warning 提示，PPDCS Exit Gate 二次检查 |

### 人工确认项

| 确认项 | 说明 |
|--------|------|
| M/F/Q 分析质量 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。各维度分析是否覆盖完整 |
| LC 整合一致性 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。测试点归集、因子绑定和拓扑绑定是否一致 |
| 设计计划 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。CAE→PPDCS 推断是否合理 |
| 公共因子消费 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。因子库 lock 和候选提案是否合理 |

### Exit Criteria

| 条目 | 要求 |
|------|------|
| 自动自检结果 | `process/checkpoints/GATE-3-MFQ-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-3-MFQ-Exit-manual.md` 已生成并展示给用户 |
| Warning 项 | 已展示给用户，用户知悉 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: ppdcs` 与 GATE-3 结果 |

### Deliverables

| 产物 | 路径 |
|------|------|
| MFQ 自检结果 | `process/checkpoints/GATE-3-MFQ-Exit-auto.md` |
| MFQ 人工确认稿 | `process/checkpoints/GATE-3-MFQ-Exit-manual.md` |
| MFQ 全部产物 | `mfq/` 目录 |

> **实现深度说明**：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 按本 gate-spec.md 执行或后续 CR 激活。

### 执行协议

> 基于 HLD §11（CR-012 v1.1）定义的硬停止规则。GATE-3 人工确认必须遵守以下协议。

| 规则 ID | 适用场景 | 规则内容 |
|---------|---------|---------|
| STOP-01 | GATE-3 人工确认 | ⛔ HARD-STOP：禁止 Agent 在人工确认项上自行判定"通过"或"质量很高"。必须等待用户回复 `approve` / `修改: ...` / `reject`。未收到用户回复前不得推进到 PPDCS 阶段 |
| STOP-02 | 候选汇总确认 | ⛔ HARD-STOP：禁止 Agent 自行判定候选因子/原子操作为"全部确认"。必须展示候选汇总表，等待用户选择确认选项 |
| STOP-03 | Skill 调用链 | ⛔ HARD-STOP：禁止 Agent 绕过 Skill 直接生成 MFQ 产物。M/F/Q 分析必须通过对应的 Skill 调用执行 |
| STOP-04 | 路径写入校验 | ⛔ HARD-STOP：Skill 写入产物前必须校验目标父目录存在且为目录。禁止 Agent 手动 mkdir 创建目录 |
| STOP-05 | 确认选项视觉区分 | 所有需要用户选择的环节，必须使用 `( )` 单选 / `[ ]` 多选 / `>>>` 开放式 三类标记区分，禁止纯数字列表 |

---

## GATE-4 PPDCS Exit Gate

### Entry Criteria

| 条目 | 要求 |
|------|------|
| PPDCS 设计完成 | `ppdcs/ppdcs/` 下每个 LC 有 PPDCS 设计过程文件 |
| PC 生成完成 | `ppdcs/pc/` 下每个 LC 有物理用例文件 |
| 覆盖率验证完成 | `ppdcs/coverage/` 下有覆盖率报告 |

### Checklist

| # | 检查项 | 通过条件 |
|---|--------|----------|
| P1 | PPDCS 设计过程完整 | `ppdcs/ppdcs/` 下每个 LC 都有设计过程文件，PPDCS 方法与 plan 推荐一致 |
| P2 | PC 文件完整 | `ppdcs/pc/` 下每个 LC 都有物理用例文件，16 列格式正确 |
| P3 | PC 拓扑绑定回链 | PC 中所有真实设备、端口、链路能回链到 LC `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` |
| P4 | 双层覆盖率验证 | `ppdcs/coverage/` 存在覆盖率报告：需求覆盖 = 100%，测试点覆盖 ≥ 95% |
| P5 | 因子覆盖验证 | 所有 `factor_bindings` 的因子在 PC 中有覆盖 |
| P6 | 交付物完整 | `ppdcs/delivery/` 包含且仅包含测试方案和测试用例两个文件 |
| P7 | 交付物字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

### 人工确认项

| 确认项 | 说明 |
|--------|------|
| PPDCS 设计方法 | 每个 LC 的 PPDCS 方法选择是否合理，设计步骤是否完整 |
| 物理用例质量 | PC 编号、组网描述、测试步骤、预期结果是否满足标准 |
| 覆盖率结果 | 需求覆盖率、测试点覆盖率是否达标，未覆盖项是否可接受 |
| 拓扑绑定 | needs-confirmation 项是否已处理或记录为风险 |

### Exit Criteria

| 条目 | 要求 |
|------|------|
| 自动自检结果 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` 已生成 |
| 人工确认稿 | `process/checkpoints/GATE-4-PPDCS-Exit-manual.md` 已生成并展示给用户 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: exit` 与 GATE-4 结果 |

### Deliverables

| 产物 | 路径 |
|------|------|
| PPDCS 自检结果 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` |
| PPDCS 人工确认稿 | `process/checkpoints/GATE-4-PPDCS-Exit-manual.md` |
| PPDCS 全部产物 | `ppdcs/` 目录 |

> **实现深度说明**：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 按本 gate-spec.md 执行或后续 CR 激活。

---

## GATE-5 Exit Gate

### Entry Criteria

| 条目 | 要求 |
|------|------|
| GATE-4 已通过 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` 状态为 PASS |
| 交付物存在 | `ppdcs/delivery/` 下有两份交付文件 |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|--------|----------|----------|
| 1 | 交付物完整 | `<特性名>特性测试方案.md` 和 `<特性名>特性测试用例.md` 均存在 | 缺失时回到交付渲染 |
| 2 | 交付字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` | 渲染前修正字段 |
| 3 | 公共库记录 | 测试方案记录公共库 `library_id / version / checksum` 和样本策略摘要 | 缺失时补充 |
| 4 | 不可提升状态 | 交付物中 `needs-confirmation` 未被提升为 `confirmed` | 发现提升时修正 |

### Exit Criteria

| 条目 | 要求 |
|------|------|
| 检查结果 | `process/checkpoints/GATE-5-Exit.md` 已生成 |
| 状态更新 | `process/STATE.yaml` 记录 `current_phase: completed` |

### Deliverables

| 产物 | 路径 |
|------|------|
| Exit Gate 检查结果 | `process/checkpoints/GATE-5-Exit.md` |
| 最终交付物 | `ppdcs/delivery/<特性名>特性测试方案.md`、`ppdcs/delivery/<特性名>特性测试用例.md` |

> **实现深度说明**：当前版本由 checkpoint-manager 执行骨架检查（产物目录存在性），详细 Checklist 由主 Agent 按本 gate-spec.md 执行或后续 CR 激活。

---

## 跨阶段拓扑绑定检查

以下检查贯穿所有阶段，用于保证测试因子、拓扑角色和真实组网对象分层。

| 阶段 | 检查项 | 通过条件 |
|------|--------|----------|
| KYM | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源、Mermaid、设备/端口/链路表 |
| MFQ (M 分析) | CAE topology role | M 输出只包含 `topology_role_refs`，不包含真实端口作为 factor value |
| MFQ (整合) | LC topology bindings | LC `topology_bindings` 从 `confirmed-scenarios.md` 绑定真实组网对象 |
| PPDCS (设计) | PPDCS 消费绑定 | 设计引用 `topology_binding_refs`，不重新发明真实端口 |
| PPDCS (PC) | PC materialization | PC 中真实端口均能回链到 LC `topology_bindings` |
| PPDCS (覆盖) | 覆盖状态保持 | 不把 `needs-confirmation` 提升为 `confirmed` |
| PPDCS (交付) | 交付字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

公共因子校验与拓扑绑定校验并行存在：`factor_bindings` 用于公共因子与样本覆盖，`topology_bindings` 只用于真实组网对象回链。
