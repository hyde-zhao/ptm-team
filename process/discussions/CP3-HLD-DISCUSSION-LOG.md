# CP3 HLD 讨论日志 — CR-011 ptm-tde KYM 阶段改造

> 本文件记录 HLD 设计过程中的 Architecture Gray Areas 讨论。用于审计和恢复，不替代 HLD.md 中的正式方案记录。

## 会话信息

| 字段 | 值 |
|------|-----|
| workflow_id | WF-PTM-TEAM-20260520-001 |
| change_id | CR-011 |
| phase | solution-design |
| agent_role | meta-se |
| started_at | 2026-06-02T00:00:00+08:00 |

---

## Architecture Gray Areas 识别

识别时间：2026-06-02T00:00:00+08:00
识别来源：CR-011 定义、gate-spec.md、agents/ptm-tde.md、skills/feature-parser/SKILL.md、skills/scenario-discovery/SKILL.md、skills/checkpoint-manager/SKILL.md、skills/README.md、docs/ptm-tde/skill-references.md、process/HLD-CR-010.md

### 灰区列表

| ID | 灰区 | 影响面 | canonical refs |
|----|------|--------|---------------|
| AGA-01 | kym Skill 归属形态：独立 Skill vs 合并到 feature-parser | 模块边界、Skill 索引、Agent 流程 | CR-011 §一 |
| AGA-02 | 启发式探索框架设计：固化维度 vs 全定制 vs 预设+扩展 | kym Skill 步骤 2 结构、GATE-2 N2 通过条件 | CR-011 §启发式探索占位框架；superpowers/brainstorming；gsd-core/discuss-phase |
| AGA-03 | Gate 自检 vs 人工确认划分边界 | gate-spec.md GATE-1 #8/#9 + GATE-2 N1-N4 的分类 | CR-011 §三 |
| AGA-04 | 路径迁移范围边界：严格 KYM vs 连带修正跨阶段引用 | feature-parser/scenario-discovery 的路径替换范围 | CR-011 §二 |

---

## 讨论记录

### Round 1 — 2026-06-02

**meta-se 发起**：聚焦 AGA-02（启发式探索框架设计），推荐方案 A（预设核心维度 + 用户扩展席位）。

**推荐方案要点**：
- 5 个固化核心维度：What / Why / Who / Scope & Boundaries / Confirmation Gaps
- 用户可定制扩展维度席位
- 融入 superpowers HARD-GATE + gsd-core「思考伙伴」哲学
- 自检通过条件：核心维度 + ≥1 个扩展维度

等待用户确认...

---

## 用户选择汇总

| 灰区 ID | 用户选择 | 确认时间 | 备注 |
|---------|---------|---------|------|
| AGA-01 | 方案 A：kym 作为独立 Skill | 2026-06-02T03:44:00+08:00 | 独立 Skill，不合并到 feature-parser |
| AGA-02 | 方案 A：CIDTESTD 8 维度预设+扩展 | 2026-06-02T03:44:00+08:00 | 固化核心维度 + 用户扩展席位 |
| AGA-03 | 方案 A：保持当前 Gate 自检 vs 人工确认分类 | 2026-06-02T03:44:00+08:00 | GATE-1 #8/#9 自检，GATE-2 N1-N4 自检+人工确认 |
| AGA-04 | 方案 A：严格 KYM 边界路径迁移 | 2026-06-02T03:44:00+08:00 | 只迁移 KYM 阶段路径，不触碰 MFQ/PPDCS 路径 |

### Round 2-5 决策汇总

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 状态 |
|---------|---------|-----------|---------|------|
| DQ-TSP-01 | architecture | TSP 是否作为独立实体插入 M 分析流程？ | 方案 A：独立结构化实体 | **已确认**（2026-06-02） |
| DQ-TSP-02 | scope | TSP 和 CAE-R 实现归属哪个 CR？ | HLD 给出完整设计，实现归属后续 CR（CR-012） | **已确认**（2026-06-02） |
| DQ-CAER-01 | architecture | CAE→CAE-R 演进路径？ | 渐进式超集 | **已确认**（2026-06-02） |
| DQ-CAER-02 | scope | CAE-R 实现归属？ | HLD 完整设计，实现归属后续 CR | **已确认**（2026-06-02） |
| DQ-CAER-03 | implementation | kym Skill risks 结构是否需增强？ | 保持现有结构，M 分析通过模糊匹配消费 | **已确认**（2026-06-02） |
| DQ-FACTOR-01 | architecture | 因子格式演进策略？ | 渐进兼容：保留当前 + 新增 factor_type/tags | **已确认**（2026-06-02） |
| DQ-FACTOR-02 | scope | factor_type 标注归属哪个 CR？ | 后续 CR（因子库增强） | **已确认**（2026-06-02） |
| DQ-FLOW-01 | architecture | CR-011 HLD 中 TSP/CAE-R 的设计深度？ | HLD 完整设计 + 标记「设计前瞻」 | **已确认**（2026-06-02） |
| DQ-FLOW-02 | implementation | kym Skill risks 契约说明？ | SKILL.md 增加一句说明 | **已确认**（2026-06-02） |
| DQ-FLOW-03 | scope | agents/ptm-tde.md 追踪链是否本 CR 更新？ | 暂不更新，标注注释说明 v2 方向 | **已确认**（2026-06-02） |

---

## Round 2 — TSP 实体设计决策

**meta-se 发起时间**：2026-06-02T03:00:00+08:00

**分析来源**：`ptm-tde-workflow-v2.md` §2.1 TSP + §3.2 M 分析 + §3.3 PPDCS

### 背景

v2 文档在 M 分析阶段插入 TSP（Topic/Scope/Purpose）三元组：
```
当前 ptm-tde 流程: M 识别 → PPDCS 特征标注 → CAE 测试点
v2 建议流程:      M 识别 → TSP 描述 → PPDCS 特征标注 → CAE-R 测试点
```

TSP 的核心价值：在建模之前明确每个 M 的「测什么、输入输出边界、测试意图」，为 PPDCS 特征选择提供方向性引导。

### 推荐方案

**方案 A（推荐）：将 TSP 作为 M 分析中独立的结构化实体**

TSP 数据结构：
```yaml
tsp:
  id: "TSP-M2-001"
  m_id: "M2"
  topic: "根据优惠规则计算价格并输出购物清单"   # 一句话描述被测功能
  scope: "接收校验后商品数据 + 价格 + 优惠配置"  # 输入输出边界
  purpose: "验证买二赠一/95折/冲突处理规则计算正确" # 测试意图
```

TSP 与 PPDCS 特征选择的引导关系表：

| Purpose 关注点 | 倾向特征 | 理由 |
|---------------|---------|------|
| 步骤顺序/流程协调 | P-Process | 多步骤有序约束 |
| 规则的输入输出正确性 | P-Parameter | 参数参与业务规则判定 |
| 数据本身的合法性 | D-Data | 独立取值验证 |
| 状态间的转换一致性 | S-State | 对象有多状态可互转 |
| 参数太多需要压缩组合 | C-Combination | 因子组合爆炸 |

**在 M 分析流程中的插入位置**：
- 在 `m-analyzer` 步骤 2（逐模块功能分析）之后
- 在步骤 4（PPDCS 特征标注）之前
- 新增步骤 3：TSP 描述（为每个 M 产出 TSP）
- 原步骤 4 改为消费 TSP 的 purpose 字段来辅助特征判断

**修改影响的文件**：
- `skills/m-analyzer/SKILL.md`：在步骤 2 和步骤 4 之间插入 TSP 步骤（新增 ~30 行）
- `agents/ptm-tde.md`：追踪链更新（新增 TSP 节点），初始化流程不涉及

### 备选方案

**方案 B（备选）：将 TSP 作为 PPDCS 特征标注的嵌入式注释**

不创建独立实体，而是在 PPDCS 标注表中为每个 M 增加 topic/scope/purpose 三列。优势是不改流程步骤数，劣势是 TSP 不可被下游独立引用，且与因子库、CAE-R 的关联弱。

**方案 C（备选）：延迟 TSP，先用现有 PPDCS 标注的「判定依据」字段替代**

不新增任何结构，依靠 m-analyzer 已有 `ppdcs-annotation.md` 中的「判定依据」列承载类似信息。优势是零改动量，劣势是判定依据不区分 topic/scope/purpose，缺乏结构化引导力。

### Advisor Table

| 维度 | 方案 A（推荐） | 方案 B | 方案 C |
|------|--------------|--------|--------|
| 可读性 | 高：TSP 三元组直观 | 中：嵌入在标注表中 | 低：混在判定依据文本中 |
| 可复用性 | 高：TSP 可被 LC、CAE-R、下游独立引用 | 中：只能作为表列被引用 | 低：不可独立引用 |
| 下游影响 | 中：m-analyzer 新增步骤，agent flow 追踪链更新 | 低：只改 ppdcs-annotation 格式 | 无 |
| 认知负担 | 中：需理解 TSP 三个字段 | 低：与现有标注表一致 | 无 |
| 对 PPDCS 特征选择的引导 | 强：purpose→特征映射表可程序化 | 弱：人工从话题/范围/意图推理 | 极弱：依赖人工文本解读 |
| 与 v2 方法论对齐度 | 完全对齐 | 部分对齐 | 不对齐 |

### 对 CR-011 Story 的影响

| Story | 影响 | 说明 |
|-------|------|------|
| STORY-011-01 (kym Skill) | 无直接影响 | TSP 位于 MFQ 阶段，不属于 KYM 阶段 |
| STORY-011-02 (路径迁移) | 无影响 | 不涉及 KYM 路径 |
| STORY-011-03 (Gate 增强) | 无直接影响 | GATE-2 (KYM Exit) 不检查 TSP；若未来 GATE-3 (MFQ Exit) 需检查，由后续 CR 处理 |
| STORY-011-04 (Agent 流程更新) | **间接影响** | `agents/ptm-tde.md` 追踪链需增加 TSP，但当前 CR-011 聚焦 KYM 阶段，TSP 和 CAE-R 属于 MFQ/PPDCS 阶段，建议在本 CR 的 HLD 中标注为「设计前瞻」，由后续 CR（如 CR-012）实现 |

> **关键判断**：TSP 和 CAE-R 不是 CR-011 的直接实现范围。CR-011 负责 KYM 阶段改造（kym Skill + 路径迁移 + Gate 增强）。但 HLD 需要在架构层面给出 TSP/CAE-R 的完整设计，确保 CR-011 的 kym Skill 输出格式为后续 TSP/CAE-R 消费做好准备。

### 待用户确认

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 |
|---------|---------|-----------|---------|---------|
| DQ-TSP-01 | architecture | TSP 是否作为独立实体插入 M 分析流程？ | 方案 A：独立结构化实体 | 方案 B：嵌入式注释 / 方案 C：延迟 |
| DQ-TSP-02 | scope | TSP 和 CAE-R 实现归属哪个 CR？ | HLD 给出完整设计，实现归属后续 CR（CR-012） | 纳入 CR-011 范围扩大 |

---

## Round 3 — CAE-R 实体设计决策

**meta-se 发起时间**：2026-06-02T03:00:00+08:00

**分析来源**：`ptm-tde-workflow-v2.md` §2.3 CAE-R + §3.3 PPDCS + `kym-brainstorming-skill-设计.md` §A.3 KYM 文档模板

### 背景

v2 文档在现有 CAE 三元组基础上增加 R（Reason/追溯）：
```yaml
# 当前 CAE
cae: {condition, action, effect}

# v2 建议 CAE-R
cae_r: {condition, action, effect, reason: {rule_id, model_type, coverage, intent, risk_level}}
```

### CAE → CAE-R 演变路径设计

**推荐：渐进式超集方案**

```
M 分析阶段:
  产出 CAE 雏形（C=因子域引用，A=动词，E=待定/期望，无 R 字段）
  此时 Model 尚未建立，rule_id 和 coverage 不可得

PPDCS 建模阶段:
  CAE 雏形 → CAE-R 完整形态
  C: 因子域引用 → 因子具体值（从 Model 规则实例化）
  A: 保持不变
  E: 待定/期望 → 具体期望值（从 Model 规则输出）
  R: 新建（rule_id + model_type + coverage + intent + risk_level）
```

两个阶段的数据形态对比：

| 字段 | M 分析 (CAE 雏形) | PPDCS 建模 (CAE-R 完整) |
|------|-------------------|------------------------|
| C.factors | `value: "@domain.普通"` | `value: "普通"` |
| A | `verb: "执行打印小票"` | `verb: "执行打印小票"` |
| E | `[待定原因: 依赖业务规则]` | `{output: "receipt.total", check: 6.00}` |
| R.rule_id | — (不可得) | `"R3"` |
| R.model_type | — (不可得) | `"P-Parameter"` |
| R.coverage | — (不可得) | `[{factor_id: "F-M2-01", covered: ["普通"]}]` |
| R.intent | — (可选) | `"验证普通商品买二赠一优惠的价格计算是否正确"` |
| R.risk_level | — (可从 KYM 预填) | `"high"` (确认或更新) |

### R 字段的消费价值分析

| R 字段 | 消费方 | 价值 |
|--------|--------|------|
| `rule_id` | 失败追溯 | 从失败 PC → CAE-R → Model 规则，定位根因 |
| `model_type` | 覆盖率报告 | 按 Model 类型统计覆盖分布 |
| `coverage` | 覆盖率验证 | 累加为因子覆盖矩阵，检测未覆盖域值 |
| `intent` | ptm-te/ptm-tae 执行层 | 失败时提供人类可读的测试意图上下文，帮助大模型理解「这段代码想测什么」 |
| `risk_level` | ptm-tm 风险管理 | 风险跟踪和优先级判断 |

### R 字段对 kym Skill 产出的依赖

| R 字段 | 可从 KYM 直接填入？ | 说明 |
|--------|-------------------|------|
| `risk_level` | **是** — KYM `risks[].impact` + `risks[].likelihood` | KYM 已识别风险区域和等级，M 分析阶段可按 M 所属区域预填，PPDCS 阶段确认 |
| `intent` | **部分** — KYM `test_items.items` + `customers.concerns` | KYM 已记录测试项和用户关切，可辅助生成 intent 描述，但最终 intent 需等 Model 规则确定 |
| `rule_id` | **否** | 来自 Model（判定表/流程图），KYM 阶段不存在 |
| `model_type` | **否** | 来自 PPDCS 特征选择，KYM 阶段不确定 |
| `coverage` | **否** | 来自 Model 规则实例化后的因子具体值，KYM 阶段不可得 |

**关键设计点**：kym Skill 的输出格式（`kym/mission-understanding/mission-statement.md`）需要在设计上预留风险信息结构，使得 M 分析阶段能从 KYM 读取 `risks` 并预填 CAE 雏形的 `risk_level`。这要求 CR-011 的 kym Skill 输出模板中 `risks` 字段使用结构化格式（已在 `kym-brainstorming-skill-设计.md` §A.3 模板中定义），当前 CR-011 的 kym Skill 设计已满足此需求。

### Advisor Table

| 维度 | 渐进式超集（推荐） | 整体替换 CAE 为 CAE-R |
|------|------------------|----------------------|
| 兼容性 | 高：现有 CAE 格式不变，下游逐步升级 | 低：所有消费 CAE 的 Skill 需同步修改 |
| 实现复杂度 | 低：分两阶段（M 分析 + PPDCS），每阶段改动独立 | 高：需一次改动 m-analyzer/test-point-integrator/所有 design Skill/coverage-verifier/deliverable-renderer |
| 回退风险 | 低：任一阶段可独立回退 | 高：耦合改动，回退影响大 |
| 与 v2 对齐度 | 中等（CAE 雏形不叫 CAE-R，但语义等价） | 完全对齐 |
| 测试验证 | 逐步验证，每阶段可独立测试 | 需全链路回归 |

### 对 CR-011 Story 的影响

| Story | 影响 | 说明 |
|-------|------|------|
| STORY-011-01 (kym Skill) | **需确认** | kym Skill 输出的 `risks` 结构需确保可被 M 分析消费为 `risk_level` 预填值。当前设计已满足，但需在 SKILL.md 中显式标注 `risks[].area` 字段用于匹配 M 名称 |
| STORY-011-02~04 | 无直接影响 | CAE-R 属于 MFQ/PPDCS 阶段 |

### 待用户确认

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 |
|---------|---------|-----------|---------|---------|
| DQ-CAER-01 | architecture | CAE→CAE-R 演进路径？ | 渐进式超集（CAE 雏形 → CAE-R 完整） | 整体替换 |
| DQ-CAER-02 | scope | CAE-R 实现归属？ | HLD 给出完整设计，实现归属后续 CR | 纳入 CR-011 范围扩大 |
| DQ-CAER-03 | implementation | kym Skill 输出的 risks 结构是否需要增强以支持 risk_level 预填？ | 保持现有 CIDTESTD risks 结构，M 分析通过 area→M 名称模糊匹配 | 新增 `risk_level` 枚举字段到 KYM 输出 |

---

## Round 4 — 因子格式对比分析

**meta-se 发起时间**：2026-06-02T03:00:00+08:00

**分析来源**：`resource/factor-libraries/` 当前格式 vs `ptm-tde-workflow-v2.md` §2.2 + §3.2

### 当前 ptm-tde 因子格式

以 `resource/factor-libraries/ngfw-policy-routing/factor-library.yaml` 为例：

```yaml
factors:
  - factor_id: FAC-L3-EGRESS-MODE
    factor_name: 三层转发出口选择模式
    factor_kind: control          # control/data/constraint/state/condition
    design_role: driver           # driver/constraint/oracle/precondition
    owner_object: OBJ-PR-EGRESS
    domain_model: enum            # enum/range/ip_address/state
    value_type: enum
    values: [next-hop, out-interface]
    display_values: {next-hop: 下一跳, out-interface: 出接口}
    aliases: [出口模式, 转发出口类型]
    applicable_when: always
    downstream_methods: [P-Parameter, C-Combination]
    reuse_policy: must_reuse
    status: active
    # 部分因子还有:
    sample_definitions: [...]     # 样本定义（含 sample_id, expr, applicability）
    usage_profiles: {...}         # 使用场景配置
    constraints: [...]            # 约束条件
```

### v2 建议的因子格式

```yaml
factor:
  id: "F-M2-01"
  name: "商品编号类型"
  m_id: "M2"                     # ← 新增：所属 M
  object: "输入商品数据中的编号格式"  # ← 语义近似 owner_object 但更偏描述
  domain: ["普通商品", "称重商品"]   # ← 语义近似 values，但去掉了 display_values
  type: "equivalence"            # ← 新增：因子类型分类
  tags: ["M2", "输入数据", "等价类"]  # ← 新增：索引标签
```

### 逐字段对比

| 维度 | 当前格式 | v2 格式 | 分析 |
|------|---------|---------|------|
| ID/名称 | `factor_id` + `factor_name` | `id` + `name` | 当前格式更丰富（支持 aliases、display_values），但 v2 简洁 |
| **因子类型** | `factor_kind` (control/data/constraint/state/condition) | `type` (equivalence/boundary/bool/state/process) | **两个维度正交**：factor_kind 描述因子性质（控制/数据/约束），type 描述测试设计方法（等价类/边界值/流程）。两者不冲突，可共存 |
| 被测对象 | `owner_object` (对象引用) | `object` (自然语言描述) | 当前格式更结构化（可关联 Test Object），v2 更自由但不可程序化关联 |
| 取值域 | `values` + `display_values` + `domain_model` | `domain` (简单列表) | 当前格式更完整：区分内部值和显示值、标注域模型类型、支持表达式域（`domain_expr`）。v2 丢失了 display_values 和 domain_model |
| 样本/使用场景 | `sample_definitions` + `usage_profiles` | 无 | **当前格式的核心优势**：支持自动化样本选择和组合。v2 完全缺失，无法支撑 CAE-R 的因子实例化 |
| 适用条件 | `applicable_when` | 无 | 当前格式有条件触发逻辑，v2 缺失 |
| PPDCS 关联 | `downstream_methods` | `type` (间接) | 当前格式显式声明适用的 PPDCS 方法，v2 通过 type 枚举间接关联 |
| M 归属 | 无（公共因子库跨项目） | `m_id` | v2 将因子与 M 绑定，但公共因子库的因子应跨 M 可复用。可改为在项目 factor-usage 中绑定 |
| 标签索引 | 无（依赖 aliases + factor_name 全文检索） | `tags` | v2 的 tags 增强可检索性，值得引入 |

### 优劣总结

| 维度 | 当前格式优势 | v2 格式优势 |
|------|------------|-----------|
| **可读性** | 中（字段多但含义明确） | 高（字段少、扁平） |
| **可复用性** | 高（sample_definitions、usage_profiles 支持跨项目样本复用） | 低（无样本机制） |
| **自动化兼容性** | 高（domain_model、sample_definitions、constraints 可程序化消费） | 低（domain 是自由列表、无样本定义） |
| **覆盖率计算** | 中（通过 sample coverage 间接计算） | 高（type 分类 + domain 平坦列表可直接计域值覆盖数） |
| **因子组合匹配** | 高（applicable_when + constraints 支持条件组合） | 低（无约束机制） |
| **测试设计引导** | 中（downstream_methods 直接映射） | 高（type 枚举 = 测试设计方法 prompt） |
| **检索能力** | 中（aliases + factor_name） | 高（tags 自由标签） |

### 推荐方案：渐进兼容（保留当前格式 + 选择性引入 v2 字段）

**原则**：公共因子库（`resource/factor-libraries/`）是生产级资产，不可为了对齐 v2 而丢失现有自动化能力。v2 格式更多是「测试设计视角」的因子表达，适合在项目级因子消费层（`mfq/factor-usage/`）体现，而非替代公共因子库格式。

**第一阶段（CR-011 期间或紧后 CR）**：

| 改动 | 位置 | 动作 |
|------|------|------|
| 新增 `factor_type` 字段 | `resource/factor-libraries/*.yaml` | 为每个因子增加 `factor_type: equivalence/boundary/bool/state/process`，作为可选字段，不影响现有消费者 |
| 新增 `tags` 字段 | `resource/factor-libraries/*.yaml` | 为每个因子增加 `tags: [...]`，作为可选索引标签 |
| `tools/migrate-factor-types.py` 或手动标注 | 新增脚本 | 工具辅助从现有 `domain_model` + `downstream_methods` 推断 `factor_type` 默认值 |
| 项目级因子消费更新 | `mfq/factor-usage/factor-bindings.md` | 在绑定层增加对 `factor_type` 和 `tags` 的透传，供覆盖率计算使用 |

**不在第一阶段做的**：
- 不删除现有 `factor_kind`、`design_role`、`sample_definitions`、`usage_profiles`、`constraints`
- 不引入 `m_id`（公共因子属于库，不属于特定 M；M 归属在项目 `factor-bindings` 中表达）
- 不替换 `owner_object` 为 `object`（`owner_object` 可程序化关联，保留为主字段；可新增 `object_description` 作为可选的 human-readable 补充）

**Why not 方案 B（完全迁移）**：丢失 `sample_definitions`、`usage_profiles`、`constraints` 后，自动化样本选择和 CAE-R 因子实例化将退化为人工填写，与 ptm-tde 自动化目标冲突。

**Why not 方案 C（并存两套）**：维护两套格式的同步成本高，且公共因子库是 truth source，项目级应派生而非复制。

### 对 CR-011 Story 的影响

| Story | 影响 | 说明 |
|-------|------|------|
| STORY-011-01~04 | 无直接影响 | 因子格式改造不属于 KYM 阶段，但 kym Skill 输出中的 `risks` 和 `test_items` 可以辅助后续 `factor_type` 推断 |

### 待用户确认

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 |
|---------|---------|-----------|---------|---------|
| DQ-FACTOR-01 | architecture | 因子格式演进策略？ | 渐进兼容：保留当前格式 + 新增 `factor_type` 和 `tags` 可选字段 | 完全迁移至 v2 / 两套并存 |
| DQ-FACTOR-02 | scope | `factor_type` 标注归属哪个 CR？ | 后续 CR（因子库增强），CR-011 不涉及 | 纳入 CR-011 作为 kym Skill 的配套改动 |

---

## Round 5 — 数据流优化评估

**meta-se 发起时间**：2026-06-02T03:00:00+08:00

**分析来源**：`ptm-tde-workflow-v2.md` §一完整数据流 + `agents/ptm-tde.md` §追踪链 + `kym-brainstorming-skill-设计.md` §三消费关系

### 当前 ptm-tde 追踪链 vs v2 追踪链

| 节点 | 当前 ptm-tde (`agents/ptm-tde.md`) | v2 建议 | 差距 |
|------|-----------------------------------|---------|------|
| 需求输入 | SR（系统需求） | 需求文档 → KYM | 当前缺少 KYM 作为显式起始节点 |
| 场景 | SR → 场景发现 (scenario-discovery) | KYM → 场景发现 | v2 中 KYM 为场景发现提供优先级依据 |
| 单功能 | 隐式在 M 分析中，无独立实体 | **TSP** — 显式三元组描述 | **差距：缺少 TSP** |
| 建模 | TP → LC，无显式 Model 节点 | **Model(LC)** — Model 是 LC 的前置产物 | 当前 LC 中无独立 Model 结构（判定表/流程图/状态图） |
| 因子 | 因子库 → factor_bindings → CAE | 因子库 → Factor → CAE-R | v2 链中 Factor 是显式节点，当前作为隐式绑定存在 |
| 测试点 | TP(C/A/E) | **CAE-R**(C/A/E + Reason) | **差距：缺少 R 追溯** |
| 组合 | 组合（数据×路径×拓扑绑定） | CAE-R × 因子值 | v2 中组合不是独立阶段，是 CAE-R 的实例化 |
| 物理用例 | PC | PC | 一致 |
| 执行 | — | 原子操作序列 | v2 显式定义映射规则 |

### kym Skill 产出在追踪链中的注入点

kym Skill 产出的消费关系（已在 v2 §3.1 消费关系表 + kym-brainstorming §A.3 模板中定义）：

```
KYM 产出                          注入点                         状态
─────────────────────────────────────────────────────────────────────
customers (用户画像/优先级)   → 场景发现: 场景优先级排序        ✅ CR-011 覆盖
information (需求文档/变更)   → feature-parser: 结构化解析       ✅ 当前已支持
developers (团队/复杂度)      → PPDCS: 覆盖深度                 ✅ 当前可消费
test_team (测试人员/熟悉度)   → PPDCS: 覆盖深度                 ✅ 当前可消费
schedule (时间/周期)          → PPDCS: 风险优先级               ✅ 当前可消费
test_items (范围/排除项)      → m-analyzer: M 识别边界           ⚠️ 需在 m-analyzer 中显式消费
risks (风险区域/等级)         → m-analyzer: CAE-R risk_level预填 ⚠️ 需 CAE-R 落地后生效
equipment (执行环境)          → PC 生成: 执行环境                ✅ 当前可消费
deliverables (交付物/格式)    → deliverable-renderer: 输出格式   ✅ 当前可消费
```

**注入点状态**：
- ✅ 已覆盖的注入点：6 个（场景优先级、需求解析、覆盖深度、风险优先级、执行环境、交付格式）
- ⚠️ 需后续 CR 补全的注入点：2 个（M 识别边界显式消费 -> 需 m-analyzer 改造；risk_level 预填 -> 需 CAE-R 落地）
- KYM 产出已为大部分下游消费做好准备，CR-011 的 kym Skill 输出模板（`kym-brainstorming-skill-设计.md` §A.3）结构足够

### 需要修改的文件来对齐 v2 链（仅新增 TSP 和 CAE-R，不推翻现有体系）

| 文件 | 需要改动 | 改动原因 | 归属 CR |
|------|---------|---------|---------|
| `agents/ptm-tde.md` | 追踪链增加 TSP + CAE-R 节点 | 显式化 v2 链 | CR-011（设计前瞻）或 CR-012 |
| `skills/m-analyzer/SKILL.md` | 步骤 2→3→4 插入 TSP 步骤 | 产出 TSP 实体 | 后续 CR（MFQ 阶段改造） |
| `skills/test-point-integrator/SKILL.md` | CAE→CAE-R 渐进升级（R 字段） | 整合时生成 R 字段雏形 | 后续 CR（MFQ 阶段改造） |
| `skills/design-ppdcs-analyzer/SKILL.md` | Model→CAE-R 实例化（R 字段完整填充） | PPDCS 建模时完成 R 字段 | 后续 CR（PPDCS 阶段改造） |
| `skills/coverage-verifier/SKILL.md` | 消费 `R.coverage` 计算因子覆盖矩阵 | 覆盖率统计 | 后续 CR（PPDCS 阶段改造） |
| `skills/deliverable-renderer/SKILL.md` | 交付物中输出 CAE-R 追溯信息 | 测试方案/用例包含 R 字段 | 后续 CR（PPDCS 阶段改造） |
| `resource/factor-libraries/*.yaml` | 新增 `factor_type` + `tags`（可选） | 支持 v2 因子类型分类 | 后续 CR（因子库增强） |
| `docs/ptm-tde/gate-spec.md` | GATE-3 新增 TSP 完整性检查项、GATE-4 新增 R 字段完整性检查项 | Gate 门控覆盖新实体 | 后续 CR |
| `kym/mission-understanding/mission-statement.md` | risks 结构确保 M 分析可消费 `area` + `impact` + `likelihood` | risk_level 预填的数据基础 | CR-011（需确认模板中 risks 结构完整） |

### 对 CR-011 当前 Story 的最终影响评估

| Story | 影响等级 | 具体影响 |
|-------|---------|---------|
| STORY-011-01 (kym Skill) | **中** | 需确保 kym Skill 输出模板中的 `risks` 使用结构化格式（`{area, likelihood, impact, action}`），以便后续 M 分析消费为 `risk_level` 预填。当前 `kym-brainstorming-skill-设计.md` §A.3 模板已满足此要求，无需额外改动。**但需在 kym SKILL.md 中增加一条说明**：「risks 字段使用结构化格式，供下游测试设计消费」。 |
| STORY-011-02 (路径迁移) | **无** | — |
| STORY-011-03 (Gate 增强) | **低** | GATE-2 KYM Exit Gate 新增人工确认项中可加入「KYM risks 是否覆盖关键风险区域」，但不是必须 |
| STORY-011-04 (Agent 流程更新) | **低** | `agents/ptm-tde.md` 追踪链可在注释中标注 v2 前瞻（TSP + CAE-R），但实际节点等后续 CR 再更新 |

### 待用户确认

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 |
|---------|---------|-----------|---------|---------|
| DQ-FLOW-01 | architecture | CR-011 HLD 中 TSP/CAE-R 的设计深度？ | HLD 给出完整实体设计 + 数据流评估，标记为「设计前瞻」，实现归属后续 CR | CR-011 扩大范围包含 TSP/CAE-R 实现 |
| DQ-FLOW-02 | implementation | kym Skill 输出的 risks 结构是否需要显式标注「供下游消费」的契约说明？ | 在 kym SKILL.md 中增加一句说明即可，不改变数据结构 | 新增专门的 KYM-MFQ 消费契约文档 |
| DQ-FLOW-03 | scope | `agents/ptm-tde.md` 追踪链是否在本 CR 中更新为 v2 链？ | 不更新：标注注释说明 v2 前瞻方向，实际节点等 CR-012 再更新 | 现在就更新追踪链，新增 TSP/CAE-R 节点 |

---

---

## Round 6 — 用户最终确认（2026-06-02）

**用户选择**：全部方案 A

**确认范围**：
- AGA-01 至 AGA-04 四个灰区全部采用推荐方案
- DQ-TSP-01 至 DQ-FLOW-03 十项决策全部采用推荐方案
- HLD 设计策略：完整前瞻设计（TSP 实体、CAE-R 实体、因子格式演进策略、数据流评估），CR-011 范围不变（4 Stories in 2 Waves），前瞻内容归属后续 CR

**HLD 编写启动**：2026-06-02T03:44:00+08:00

---

## 变更记录

| 时间 | 事件 |
|------|------|
| 2026-06-02T00:00:00+08:00 | CP3 HLD 讨论日志创建，Architecture Gray Areas 识别完成，Round 1 发起 |
| 2026-06-02T03:00:00+08:00 | Round 2-5 发起：TSP 实体设计、CAE-R 实体设计、因子格式对比、数据流优化评估 |
| 2026-06-02T03:44:00+08:00 | Round 6 用户最终确认：全部方案 A，HLD 编写启动 |
| 2026-06-02T09:00:00+08:00 | Round 7 CP3 人工确认修正：用户提出三项修正，更新 HLD v1.0 → v1.1 |

---

## Round 7 — CP3 人工确认修正（2026-06-02）

**发起方**：user（在 CP3 人工确认中提出三项修正）
**影响范围**：HLD §4/§6/§8/§9/§10/§12/§14/§16/§18/§19/§21/§22、CP3 预检、CP3 人工确认稿

### 修正 1：不存在过渡期，路径迁移一次完成

**用户指正**：ptm-tde 是独立运行时项目，不存在旧系统过渡期。当前 CR-011 修改的 Skill 和目标都是 ptm-tde 自身的文件，没有外部消费者依赖旧路径。

**动作**：
- CP3-DQ-05 改为：一次完成全部路径迁移，不保留 `analysis/` 旧路径写入
- R3（路径迁移后消费者找不到文件）删除——没有过渡期就没有此风险
- HLD §18.3「过渡期路径状态」改为「路径迁移最终状态」
- `analysis/feature-input/` 和 `analysis/scenarios/` 在 STORY-011-02 完成后不再被写入
- 旧 R4→R3、旧 R5→R4（重新编号）

### 修正 2：feature-parser → kym 顺序重设计

**用户指正**：feature-parser 的产物是 kym 的输入。kym Skill 应先从 feature-parser 的结构化需求中提取已有信息，只有找不到答案时才询问用户。

**原顺序**：
```
kym Skill (step 1.1) → feature-parser (step 1.2) → scenario-discovery (step 1.3)
```

**新顺序**：
```
feature-parser (step 1.1) → kym Skill (step 1.2) → scenario-discovery (step 1.3)
```

**kym Skill 新增「上下文预加载」步骤**：
- 阶段零：读取 `kym/feature-input/` 中 feature-parser 的结构化产物
- CIDTESTD 各维度中，能从 feature-parser 产物自动获取的信息不再询问用户
- 只询问 feature-parser 产物中缺失的信息

| CIDTESTD 维度 | 可从 feature-parser 获取？ | 获取方式 | 仍需询问用户？ |
|--------------|-------------------------|---------|-------------|
| C (Customers) | 否 | — | **是**：用户画像、使用场景 |
| I (Information) | **是** | 参考文档路径、变更范围已在 feature-parser `directory-structure.md` 中 | 仅确认和补充 |
| D (Developer) | 否 | — | **是**：团队、代码复杂度、已知问题 |
| E (Equipment) | 否 | — | **是**：测试环境、平台 |
| S (Schedule) | 否 | — | **是**：交付时间、测试周期 |
| T (Test Items) | **是** | 测试项可从 feature-parser 的模块分解推断 | 仅确认优先级和排除项 |
| D (Deliverables) | 否 | — | **是**：交付物类型、格式 |

**R2 重新设计**：原 R2（mission-statement 与 feature-parser 信息冗余）改为「feature-parser 产物不足时，kym Skill 的 I/T 维度自动预填信息过少，仍需用户大量输入」。应对改为：阶段零预填为优化手段而非必须；feature-parser 产物不存在时 kym Skill 不阻断，I/T 维度改为全部询问用户。

**受影响文件更新**：
- `process/HLD-CR-011.md` v1.0 → v1.1：§4/§6/§8/§9/§10/§12/§14/§16/§18/§19/§21/§22 更新
- `process/checks/CP3-HLD-CONSISTENCY-CR-011.md`：重新运行预检
- `checkpoints/CP3-HLD-REVIEW-CR-011.md`：更新 Decision Brief、风险清单、不授权项
- `process/discussions/CP3-HLD-DISCUSSION-LOG.md`（本文件）：追加 Round 7

### 未变更项

- 4 个 Story 数量和 2 Wave 结构不变
- STORY-011-02（路径迁移）内容不变，仅描述从"过渡期"改为"一次完成"
- AGA-01 至 AGA-04 决策结论不变
- 10 项前瞻决策不变
- 方案 A 整体架构不变

### 修正后状态

**结论**：三项修正已全部应用到 HLD v1.1 及相关文件。CP3 自动预检重新运行，结论更新。CP3 人工确认稿更新 Decision Brief 和风险清单。
