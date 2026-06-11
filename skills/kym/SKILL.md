---
name: kym
description: >-
  Know Your Mission — 通过 CIDTESTD 8 维度结构化访谈理解测试任务的使命、上下文和边界。
  触发词包括：使命理解、KYM、Know Your Mission、特性访谈。
  适用场景：ptm-tde KYM 阶段步骤 1.2（feature-parser 之后、scenario-discovery 之前）。
argument-hint: "特性名称或输入材料路径"
user-invokable: true
status: active
---

## 目标

使用 CIDTESTD（Customers / Information / Developers / Equipment / Schedule / Test Items / Deliverables / Risks）8 维度框架，通过结构化访谈全面理解测试任务的使命、上下文和边界，产出 `kym/mission-understanding/mission-statement.md` 供全流程下游消费。

## 适用范围

- 适用阶段：ptm-tde KYM 阶段步骤 1.2
- 输入：feature-parser 产物（弱依赖）+ 用户对话
- 输出：`kym/mission-understanding/mission-statement.md`
- 不替代：测试设计（归属 MFQ/PPDCS）、场景发现（归属 scenario-discovery）

## 前置条件

- [ ] GATE-1 Entry Gate 自检已通过，或已明确记录阻断项
- [ ] feature-parser 已执行（建议但非强制——产物不存在时阶段零跳过）
- [ ] `kym/` 目录已初始化

## 执行流程

### 阶段零：上下文预加载

> 本阶段从 feature-parser 产物中自动提取已结构化信息，预填 I（Information）和 T（Test Items）维度，减少重复询问。

1. 检查 `kym/feature-input/directory-structure.md` 是否存在。
2. 若存在，读取并提取：
   - 模块列表（四级/五级标题）→ 预填 `test_items.items[]`
   - 参考文档路径 → 预填 `information.key_docs[]`
   - 变更范围描述 → 预填 `information.change_scope`
3. 若 `kym/feature-input/` 不存在或为空：跳过阶段零，I 和 T 维度在阶段三全部询问用户。输出提示：「未检测到 feature-parser 产物，I/T 维度将在访谈中完整收集。建议先执行 feature-parser 以获得更完整的上下文预填（阶段零将自动读取 `kym/feature-input/` 中的结构化产物）。」
4. 向用户报告预填结果：「已从 feature-parser 产物中预填以下信息：I 维度（x 份参考文档 / 变更范围）、T 维度（x 个模块）。这些维度在阶段二将标注为 "已自动预填"，你可以在阶段三确认或补充。」

### 阶段一：初始化

了解项目上下文，确定访谈的介入时机和深度：

1. **项目背景**：询问用户当前项目的基本情况——项目名称、团队规模、是否有测试历史。
2. **介入时机**：使用【单选】格式询问当前阶段。

**平台交互协议**：Claude Code 环境且 `AskUserQuestion` 可用时，优先使用结构化选择：
- question: "请问你目前处于哪个阶段？"
- header: "Phase"
- multiSelect: false
- options:
  1. label: "Early req", description: "早期需求阶段 — 需求文档尚在完善，可用信息有限"
  2. label: "Mid dev", description: "中期开发阶段 — 代码可用，需求较清晰"
  3. label: "Late test", description: "后期补测阶段 — 需要快速覆盖关键风险区域"

Codex 或 `AskUserQuestion` 不可用时，回退到 STOP-05 文本标记：

```
【单选】请问你目前处于哪个阶段？

( ) A. 早期需求阶段 — 需求文档尚在完善，可用信息有限
( ) B. 中期开发阶段 — 代码可用，需求较清晰
( ) C. 后期补测阶段 — 需要快速覆盖关键风险区域
```
3. **已有输入**：确认除 feature-parser 产物外，用户是否还有其他输入材料（产品文档、设计文档、测试策略等）。
4. **特殊约束**：询问用户是否有特殊限制（时间、预算、平台、合规要求等）。

### 阶段二：维度扫描

展示 CIDTESTD 8 维度地图，让用户确认本次访谈的讨论范围。

#### 维度地图（初始状态）

| 缩写 | 维度 | 默认优先级 | 引导问题示例 | 状态 |
|------|------|-----------|-------------|------|
| C | Customers（用户） | 🔴 重点 | "谁是最终用户？他们的使用场景和关注点是什么？" | 待访谈 |
| I | Information（信息） | 🟡 补充 | "参考文档、变更范围、需求版本？" | 阶段零预填后标注「已自动预填」 |
| D | Developers（开发） | 🔴 重点 | "特性属性（新开发/移植/重构）？难度和重要性？" | 待访谈 |
| E | Equipment（设备） | 🔴 重点 | "测试环境类型？目标平台？拓扑需求？" | 待访谈 |
| S | Schedule（计划） | 🟡 补充 | "先分析设计还是先补充依赖？交付件清单？" | 待访谈 |
| T | Test Items（测试项） | 🟡 补充 | "测试范围、排除项、边界？" | 阶段零预填后标注「已自动预填」 |
| D | Deliverables（交付物） | 🟡 补充 | "测试交付物类型、格式、交付对象？" | 待访谈 |
| R | Risks（风险） | 🔴 重点 | "最大的风险区域？概率、影响、应对措施？" | 待访谈 |

> 若阶段零未获取到预填数据，I 和 T 维度默认设为 🔴 重点。

#### 维度优先级说明

- **🔴 重点**（C/D/E/R）：对使命理解至关重要的维度，默认必须覆盖。
- **🟡 补充**（I/S/T/D）：重要但可选的维度，用户可根据项目阶段跳过。
- **⚪ 跳过**：用户明确跳过的维度。

#### 用户操作

向用户展示维度地图后，询问：

```
请确认本次访谈的讨论范围：

1. ✅ 确认通过 — 按当前重点/补充/跳过标注继续
2. ✏️ 调整优先级 — 指定维度缩写和新的优先级，如 "E=🟡, S=🔴"
3. ➕ 新增自定义维度 — 提供维度名称和关注点
4. ⚪ 跳过维度 — 指定要跳过的维度，如 "跳过 E, S"
5. 🔄 回到某维度 — 恢复已跳过的维度，如 "回到 E"
```

#### 自定义维度

用户可通过「新增一个维度：X」的方式扩展维度列表。新增维度追加到列表末尾，格式为 `X<N>: <名称> | 🔴 重点（用户自定义）`，阶段三按标准访谈流程处理。

### 阶段三：深度访谈

> **⛔ HARD-STOP**：本阶段是**与用户的真实对话**，不是 Agent 的独立思考练习。
> Agent **绝对禁止**自行推理、推测、或编造任何维度的答案。
> Agent **必须等待用户回复**每一个问题后才能继续。
> 禁止一次性输出多个维度的所有问题，禁止在用户未回复的情况下填充 mission-statement.md 任何字段。

按用户确认的顺序逐维度访谈。

#### 逐维度访谈规则

每个维度执行以下步骤：

1. **引导提问**：提出该维度的核心问题。**一次只问一个维度的一个问题**，等待用户回复后再继续。

2. **选项格式规范**：根据问题类型使用不同格式，**必须在问题开头标注类型**。

   **交互模式选择**：
   - 选项 ≤ 4 且为纯单选/多选 → Claude Code 且 `AskUserQuestion` 可用时使用结构化选择
   - 选项 > 4 → 尝试语义拆分（如 5 选项拆为 4+1，每个 ≤4）；无法拆分时回退文本标记
   - 需开放式输入（`>>>`）→ 保持文本格式；Claude Code 可先通过 `AskUserQuestion` 做前置分类选择
   - Codex 或 `AskUserQuestion` 不可用 → 回退 STOP-05 文本标记

   **选项拆分规则**（选项 > 4 时）：
   - C-Customers 多选（5 选项）：拆为问题 1（4 个核心角色多选）+ 问题 2（是否有其他角色？Yes → Other 输入）
   - S-Schedule 交付项多选（7 项，5 默认选中）：展示默认选中提示，仅问是否有额外补充
   - D-Deliverables 类型多选（6 项）：同 S-Schedule 模式
   
   **文本标记格式**（回退或 Codex 环境）：
   
   **单选**（用户只能选一个）— 使用 `( )` 前缀：
   ```
   🔵 C — Customers（用户）
   
   【单选】IPv4 策略路由的最终用户是谁？
   
   ( ) A. 网络管理员 — 策略配置、日常运维
   ( ) B. 安全工程师 — 策略审计、合规检查
   ( ) C. DevOps/SRE — 自动化运维
   ( ) D. 其他（请描述）
   ```
   
   **多选**（用户可选多个）— 使用 `[ ]` 前缀：
   ```
   🔵 C — Customers（用户）
   
   【多选】哪些角色会使用 IPv4 策略路由？（可多选）
   
   [ ] A. 网络管理员 — 策略配置、多链路管理
   [ ] B. 安全工程师 — 策略审计、流量牵引
   [ ] C. DevOps/SRE — CI/CD 集成
   [ ] D. 产品经理 — 功能验证
   [ ] E. 其他（请描述）
   ```
   
   **开放式**（无预设选项）— 使用 `>>>` 前缀：
   ```
   【开放式】请描述 1-3 个最常见的使用场景：
   >>>
   ```

3. **I/T 维度特殊处理**：若该维度已从阶段零预填信息，先展示预填内容，再询问：「以上信息是否正确？是否有需要补充或修正的？」— 必须等待用户确认或修正。
3. **追问与深挖**：用户回答后，检查信息充分性：
   - 信息不足：追问「能再具体一点吗？」或「有哪些典型场景？」
   - 信息矛盾：指出矛盾点并请求澄清
   - 信息完成：进入步骤 4
4. **维度小结**：汇总本维度收集到的信息，以结构化格式展示给用户确认：
   - 确认无误：「继续下一维度」
   - 需要修改：重新回答本维度
5. **下一维度**：记录已访谈维度，进入下一个未被跳过的维度。

#### 各维度引导问题

##### C — Customers（用户）

```
【多选】哪些角色会使用本特性？（可多选）

[ ] A. 网络管理员 — 策略配置、日常运维、多链路管理
[ ] B. 安全工程师 — 策略审计、合规检查、流量牵引
[ ] C. DevOps/SRE — 自动化测试、CI/CD 集成
[ ] D. 产品经理/架构师 — 功能验证、性能基准
[ ] E. 其他（请详细描述）
```

```
【单选】哪类用户的优先级最高？

( ) A. 网络管理员 — 核心运维场景
( ) B. 安全工程师 — 安全合规优先
( ) C. DevOps/SRE — 自动化优先
( ) D. 产品经理 — 功能完整性优先
```
→ 让我详细描述

用户的关注点和痛点有哪些？
测试优先级：🔴 高 / 🟡 中 / ⚪ 低？
```

##### I — Information（信息）

```
[若已从阶段零预填，先展示预填的 key_docs 和 change_scope]

除了以上已预填的信息，还有哪些参考文档？
需求文档版本是什么？变更范围是否准确？
```

##### D — Developers（开发）

```
【单选】本特性的属性是什么？

( ) A. 新开发 — 全新功能，无历史代码
( ) B. 移植 — 从其他平台/版本迁移
( ) C. 重构 — 对现有功能的重新实现
( ) D. 其他（请描述）
```

```
【单选】特性难度评估？

( ) A. 高 — 涉及复杂算法、多模块交互、新技术栈
( ) B. 中 — 中等复杂度，有参考实现
( ) C. 低 — 配置项修改、简单逻辑
```

```
【单选】特性重要性评估？

( ) A. 高 — 核心功能、客户强需求、P0 级别
( ) B. 中 — 常用功能、常规需求
( ) C. 低 — 边缘功能、低频使用
```

```
【开放式】还有其他关于开发的补充信息吗？
>>>
```

##### E — Equipment（设备）

```
测试环境类型？

1. 纯虚拟化环境（VM/容器）
2. 物理设备环境
3. 混合环境（部分虚拟+部分物理）
→ 让我详细描述

目标平台是什么（如特定厂商/型号）？
有哪些拓扑需求（如 HA、集群、多节点）？
```

##### S — Schedule（计划）

```
【单选】分析与设计的推进顺序？

( ) A. 先分析设计用例再补充依赖 — 先完成 MFQ 分析和 PPDCS 用例设计，过程中记录缺失的原子操作和测试因子，最后统一补充
( ) B. 先补充依赖再分析设计用例 — 先补齐原子操作和因子库条目，确保依赖就绪后再进入分析和设计
```

```
【多选】需要交付哪些文档？（ptm-tde 默认交付以下全部，取消勾选可排除）

[✅] A. 特性测试方案（Test Plan）
[✅] B. 特性测试用例（Test Cases）
[✅] C. 逻辑用例文档（LC）
[✅] D. 覆盖率报告
[✅] E. 因子解析报告
[✅] F. 原子操作候选清单
[ ] G. 其他（请描述需要补充的交付件）
```

##### T — Test Items（测试项）

```
[若已从阶段零预填，先展示预填的 items[]]

以上模块列表是否准确？是否有需要排除的模块或功能？
测试范围的总体描述？
边界说明（不确定的项）？
```

##### D — Deliverables（交付物）

```
【多选】需要产出哪些测试交付物？

[ ] A. 测试方案（Test Plan）
[ ] B. 测试用例（Test Cases）
[ ] C. 测试报告（Test Report）
[ ] D. 缺陷分析报告（Bug Analysis）
[ ] E. 覆盖率报告（Coverage Report）
[ ] F. 其他（请描述）
```

```
【单选】交付格式偏好？

( ) A. Markdown
( ) B. PDF
( ) C. Excel
( ) D. 其他
```

```
交付对象是谁？内部团队 / 客户 / 合规审计？
```

```
📊 推荐用例规模

根据已收集的 D_dev 维度信息（难度: {difficulty} / 重要性: {importance}），
推荐用例规模计算：

  难度基数: 高=200, 中=100, 低=50  → 当前: {base}
  重要性系数: 高=1.5, 中=1.0, 低=0.7  → 当前: {coefficient}
  推荐规模: {base} × {coefficient} = {recommended} 条物理用例

是否接受此推荐规模？如需调整请说明预期数量。
```

##### R — Risks（风险）

> **⚠️ 格式约束**：风险信息必须按结构化格式收集。请为每个风险区域提供以下四个字段。
> risks 字段使用结构化格式 `{area, likelihood, impact, action}`，供下游测试设计（如 M 分析阶段 CAE-R 的 risk_level 预填）消费。

```
你认为最大的风险区域是什么？
1. 功能风险（需求理解偏差、实现错误）
2. 性能风险（负载、并发、资源耗尽）
3. 兼容性风险（平台、版本、接口变更）
4. 安全风险（漏洞、权限、数据泄露）
5. 时间风险（交付压力、范围蔓延）
→ 让我详细描述

对于每个识别的风险，请逐一提供：
- 风险区域（area）：一句话描述
- 发生概率（likelihood）：高 / 中 / 低
- 影响程度（impact）：高 / 中 / 低
- 应对措施（action）：建议的缓解或应对策略
```

### 阶段四：文档化

> **⛔ 路径校验（HARD-STOP）**：写入前必须以 README.md 为锚点校验输出路径。
>
> 1. 检查 `./README.md` 是否存在。
> 2. 若存在：读取并确认 README.md 中描述的 `kym/mission-understanding/` 路径与当前写入路径一致。不一致时拒绝写入并提示：「README.md 记录的目录结构与实际不符，请先修正。」
> 3. 若不存在：提示「建议先创建 README.md 记录项目结构，确保后续 Skill 路径一致」，然后继续写入。
> 4. 确保 `./kym/mission-understanding/` 目录存在，不存在则创建。
> 5. 写入 `./kym/mission-understanding/mission-statement.md`。

1. **撰写 mission-statement.md**：根据阶段三访谈结果生成内容并写入。
2. **KYM 自检**：
   - 维度覆盖检查：已覆盖维度数是否 ≥ 2？（若 <2，输出 WARNING：「覆盖维度不足，强烈建议至少覆盖 2 个维度」）
   - 信息缺口检查：是否存在关键字段为空？
   - 一致性检查：各维度信息之间是否存在矛盾？
   - 粗粒度检查：是否存在过于笼统、不可操作的描述？
3. **⛔ 用户审阅确认（HARD-STOP）**：展示完整的 mission-statement.md 内容给用户。**必须等待用户明确回复** `approve` 后才能保存。

**平台交互协议**：Claude Code 环境且 `AskUserQuestion` 可用时，优先使用结构化选择：
- question: "请审阅 mission-statement 内容并确认："
- header: "KYM confirm"
- multiSelect: false
- options:
  1. label: "Approve", description: "接受全部内容，保存并进入下一阶段"
  2. label: "Modify", description: "需要修改。输入修改项（格式：修改: <维度>=<修改内容>）"
  3. label: "Reject", description: "驳回，需要重新处理"

Codex 或 `AskUserQuestion` 不可用时，使用标准 HARD-STOP 文本协议等待用户回复 `approve`、`修改: <具体修改点>` 或 `reject`。

用户拒绝确认时，回到阶段三补充或修正指定维度；拒绝接受时，不确定项记录到 `confirmation_gaps`。**禁止**在用户未回复的情况下自行保存或继续后续阶段。

#### KYM 自检清单

- [ ] 覆盖维度数 ≥ 2（C/D/E/R 至少覆盖 1 个）
- [ ] `test_items.items[]` 至少 1 项
- [ ] `customers.users[]` 至少 1 项
- [ ] risks 条目均包含 `{area, likelihood, impact, action}` 四字段
- [ ] skipped_dimensions 与阶段二选择一致
- [ ] deferred_ideas 记录了范畴守卫捕获的测试设计线索
- [ ] 无关键字段大面积空白
- [ ] 各维度信息无自相矛盾

## 输出格式

### mission-statement.md 结构

```markdown
# <特性名> — 使命理解声明（Mission Statement）

> 生成时间：YYYY-MM-DD HH:MM
> 访谈方式：CIDTESTD 8 维度结构化访谈
> 产出 Skill：kym

## Customers（用户）

| 字段 | 值 |
|------|-----|
| users | ... |
| priority | high / medium / low |
| concerns | ... |
| usage_scenarios | ... |

## Information（信息）

| 字段 | 值 |
|------|-----|
| key_docs | ... |
| change_scope | ... |
| requirements_version | ... |

## Developers（开发）

| 字段 | 值 |
|------|-----|
| feature_type | 新开发 / 移植 / 重构 |
| difficulty | high / medium / low |
| importance | high / medium / low |
| notes | ... |

## Equipment（设备）

| 字段 | 值 |
|------|-----|
| env_type | ... |
| platform | ... |
| topology_requirements | ... |

## Schedule（计划）

| 字段 | 值 |
|------|-----|
| analysis_order | 先分析设计再补充依赖 / 先补充依赖再分析设计 |
| deliverables | 默认全选（A-F），记录用户排除和补充项 |

## Test Items（测试项）

| 字段 | 值 |
|------|-----|
| items | ... |
| dont_test | ... |
| scope | ... |
| boundary_notes | ... |

## Deliverables（交付物）

| 字段 | 值 |
|------|-----|
| types | ... |
| format | Markdown / PDF / Excel / 其他 |
| audience | ... |
| recommended_scale | {base} × {coefficient} = {recommended} 条 PC |
| scale_algorithm | 难度基数(高200/中100/低50) × 重要性系数(高1.5/中1.0/低0.7) |

## Risks（风险）

| # | area | likelihood | impact | action |
|---|------|-----------|--------|--------|
| 1 | ... | 高/中/低 | 高/中/低 | ... |

> risks 字段使用结构化格式 `{area, likelihood, impact, action}`，供下游测试设计（如 M 分析阶段 CAE-R 的 risk_level 预填）消费。

## Confirmation Gaps（待澄清项）

| gap_id | dimension | description | status |
|--------|-----------|-------------|--------|
| GAP-01 | ... | ... | open / resolved / deferred |

## Downstream Guidance（下游指引）

| 字段 | 值 |
|------|-----|
| scenario_generation.focus_areas | ... |
| mfq.suggested_m_granularity | ... |
| ppdcs.suggested_coverage_depth | ... |

## Skipped Dimensions（跳过维度）

...（如 "E, S"）...

## Deferred Ideas（暂缓想法）

...（范畴守卫捕获的测试设计讨论线索）...
```

### 字段说明

| 对象 / 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `customers.users[]` | string[] | 至少 1 项 | 最终用户画像列表 |
| `customers.priority` | enum | `high` / `medium` / `low` | 测试优先级，供 scenario-discovery 场景排序 |
| `customers.concerns` | string[] | — | 用户关注点和痛点 |
| `customers.usage_scenarios` | string[] | — | 典型使用场景描述 |
| `information.key_docs[]` | string[] | — | 参考文档路径列表（阶段零从 feature-parser 产物预填） |
| `information.change_scope` | string | — | 变更范围描述（阶段零从 feature-parser 产物预填） |
| `information.requirements_version` | string | — | 需求文档版本 |
| `developers.feature_type` | enum | `新开发` / `移植` / `重构` | 特性属性 |
| `developers.difficulty` | enum | `high` / `medium` / `low` | 特性难度 |
| `developers.importance` | enum | `high` / `medium` / `low` | 特性重要性 |
| `developers.notes` | string | — | 其他补充信息 |
| `equipment.env_type` | string | — | 测试环境类型 |
| `equipment.platform` | string | — | 目标平台 |
| `equipment.topology_requirements` | string[] | — | 拓扑需求描述 |
| `schedule.analysis_order` | enum | `先分析设计再补充依赖` / `先补充依赖再分析设计` | 分析与设计的推进顺序 |
| `schedule.deliverables` | string[] | — | 选中的交付文档清单（默认 A-F 全选） |
| `test_items.items[]` | string[] | 至少 1 项 | 测试项范围列表（阶段零从 feature-parser 产物预填模块分解） |
| `test_items.dont_test[]` | string[] | — | 明确排除的模块/功能 |
| `test_items.scope` | string | — | 范围总体描述 |
| `test_items.boundary_notes` | string | — | 边界说明（含不确定项） |
| `risks[]` | object[] | — | 风险列表，每个元素为 `{area, likelihood, impact, action}` |
| `risks[].area` | string | 必填 | 风险区域（用于下游 M 分析 area→M 名称模糊匹配） |
| `risks[].likelihood` | enum | `高` / `中` / `低` | 发生概率 |
| `risks[].impact` | enum | `高` / `中` / `低` | 影响程度 |
| `risks[].action` | string | 必填 | 应对措施 |
| `deliverables.types[]` | string[] | — | 测试交付物类型 |
| `deliverables.format` | string | — | 交付格式偏好 |
| `deliverables.audience` | string | — | 交付对象 |
| `deliverables.recommended_scale` | number | — | 推荐用例规模（条），由算法自动计算 |
| `deliverables.scale_algorithm` | string | — | 计算公式：难度基数(高200/中100/低50) × 重要性系数(高1.5/中1.0/低0.7) |
| `confirmation_gaps[]` | object[] | — | 待澄清问题，每项 `{gap_id, dimension, description, status}` |
| `downstream_guidance.scenario_generation.focus_areas` | string[] | — | 场景生成聚焦区域 |
| `downstream_guidance.mfq.suggested_m_granularity` | string | — | 建议 M 拆分粒度 |
| `downstream_guidance.ppdcs.suggested_coverage_depth` | string | — | 建议覆盖深度 |
| `skipped_dimensions[]` | string[] | — | 用户跳过的维度缩写列表（如 `["E", "D"]`） |
| `deferred_ideas[]` | string[] | — | 范畴守卫捕获的测试设计讨论线索 |

## 范畴守卫

kym Skill 的职责是**理解使命**，不是测试设计。当用户回答中出现测试设计倾向时，触发范畴守卫。

### 触发关键词（精确匹配）

- 「测试用例」
- 「等价类」
- 「边界值」
- 「Pairwise」
- 「判定表」

### 触发动作

1. 将用户的测试设计讨论内容记录到 `deferred_ideas[]`。
2. 友好提示：「这个问题很重要，我记下来放到测试设计阶段（MFQ 分析）。现在我们先继续了解特性本身。」
3. 回到当前维度的访谈。

### 非触发词

以下词汇**不会**触发范畴守卫（避免误触发）：「测试」「验证」「检查」「覆盖」。

## 维度跳过与恢复

- **跳过**：用户在阶段二指定「跳过 X」时，维度地图中该维度标记为 ⚪ 用户跳过，mission-statement 中 `skipped_dimensions` 追加该维度缩写。
- **恢复**：用户在任何阶段说「回到 X」时，该维度恢复为原始优先级标注，并在当前阶段插入该维度的访谈。
- **阶段四自检**：覆盖维度数 < 2 时输出 WARNING；但跳过所有维度不阻断文档化（输出内容为部分填充）。
- **后续恢复**：mission-statement.md 保存后，用户可重新运行 kym Skill 补充跳过的维度（从阶段零重新开始，已收集信息默认不保留）。

## 反模式

以下行为是 kym Skill 的禁止模式：

1. **跨职责测试设计**：在访谈中输出测试用例、等价类表、Pairwise 组合、判定表或任何测试设计产物。
2. **脑补未知信息**：当用户回答模糊时，不得根据行业默认值或典型场景自动填充字段。必须追问或记录到 `confirmation_gaps`。
3. **跳过确认**：每个维度的访谈结果必须经过用户小结确认，不得跳过确认直接进入下一维度。
4. **risks 非结构化**：不得将风险描述为自然语言段落——必须拆分为 `{area, likelihood, impact, action}` 四字段。
5. **强制覆盖全部维度**：用户有权跳过任意维度，不得强制要求覆盖全部 8 个维度。
6. **忽略 feature-parser 产物**：阶段零必须主动检查 `kym/feature-input/`；存在产物时不得忽略预填信息。
7. **直接发布 mission-statement**：阶段四必须先 KYM 自检 + 用户审阅确认，才能保存为最终文件。

## Gotchas

- **阶段零 feature-parser 产物路径**：kym Skill 从 `kym/feature-input/directory-structure.md` 读取，不读取 `analysis/` 旧路径。若 feature-parser 未执行或产物不在新路径下，阶段零跳过。
- **CIDTESTD 双 D 歧义**：8 个维度中 D 出现两次——第一个 D 是 Developers（开发），第二个 D 是 Deliverables（交付物）。内部标识分别为 `D_dev` 和 `D_del`，用户界面统一展示缩写 D + 全称区分。
- **维度跳过与数据丢失**：用户退出对话后重新启动 kym Skill 时，将**从头执行阶段零**——之前已收集的所有维度信息将丢失。当前版本不设计断点恢复机制。缓解措施：每维度完成后输出小结确认，降低中途退出的信息损失。
- **范畴守卫误触发**：若用户正常讨论中提到「测试用例」等关键词，范畴守卫会记录到 deferred_ideas。用户可通过「这不是测试设计，继续访谈」告知 kym Skill 解除误触发。
- **risks 格式一致性**：阶段三 R 维度访谈必须严格收集四字段。若用户只提供了风险描述而缺少概率/影响，必须追问补全。
- **输出路径**：mission-statement.md 写入 `kym/mission-understanding/` 目录。该目录由 GATE-1 初始化检查项 #8 确保存在，kym Skill 自身不创建目录。

## 验收标准

- [ ] 阶段零正确检查 `kym/feature-input/directory-structure.md`：存在时预填 I/T 维度，不存在时跳过并提示
- [ ] 阶段二维度地图展示全部 8 个 CIDTESTD 维度，正确标注优先级和预填状态
- [ ] 阶段三各维度使用多选题优先 + 自由回答选项，I/T 维度展示预填信息并确认
- [ ] R 维度访谈按 `{area, likelihood, impact, action}` 四字段结构收集风险
- [ ] 范畴守卫正确触发：关键词精确匹配 + Deferred Ideas 记录 + 友好提示
- [ ] 维度跳过与恢复功能正常：阶段二标记 → 阶段四记录 skipped_dimensions → 可恢复
- [ ] 阶段四产出完整 mission-statement.md，包含全部 12 个字段组
- [ ] KYM 自检覆盖全部 8 项检查
- [ ] 用户可通过手动 `/kym` 或触发词调用
- [ ] 不输出测试设计产物（等价类表、Pairwise 组合、判定表、测试用例）
