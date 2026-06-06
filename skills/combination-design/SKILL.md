---
name: combination-design
description: >-
  C-Combination 组合法用例设计：五步完成因子表建模→Pairwise生成→组合→LC→因子实际取值→物理用例。
  基于 PPDCS 中 C-Combination 特征：多因子多状态，组合爆炸需压缩。
  触发词包括：数据组合、Pairwise、正交、因子组合、C-Combination。
  适用场景：MFQ 设计阶段，PPDCS 特征为 C-Combination 的逻辑用例。
argument-hint: "逻辑用例 ID（如 LC-005）"
user-invokable: true
status: active
---

## 目标

对设计计划中 PPDCS 特征为 **C-Combination** 的逻辑用例，输出完整过程工件：

`输入对齐 → factor catalog → 因子值域/约束 → 压缩策略决策 → 组合生成（工具或显式 fallback）→ data row 叠加 → physical cases`

## 理论基础

C-Combination 是 PPDCS 五特征之一：
> 多个因子共同影响结果，全组合规模过大，需要通过压缩策略保留有效覆盖。

**关键区分**：
- D-Data vs C-Combination：单项独立验证足够 = Data；必须覆盖因子交叉 = Combination
- P-Parameter vs C-Combination：规则可被判定结构完整表达 = Parameter；需要组合压缩探索 = Combination

**建模工具**：Pairwise / 正交 / 约束组合

## 适用范围

> 统一输出规则：本 Skill 的方法过程写入 `ppdcs/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`，物理用例写入 `ppdcs/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`。不得创建 `design/<module>/<sub-module>/` 深目录；同名冲突追加 `-<LC-ID>`。


- 适用阶段：MFQ 的 design 阶段
- 设计输入：`process/plan/design-plan.md`
- reasoning 输入：`process/plan/design-planner-reasoning.md`
- 上游 trace 输入：`mfq/integration/logic-cases.md`、`mfq/integration/test-data.md`
- PPDCS 基线：`mfq/m-analysis/ppdcs-annotation.md`
- 输出：`ppdcs/ppdcs/<basename>.md` 与 `ppdcs/pc/<basename>.md`

## 必收输入契约（STORY-05 / STORY-04）

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `design-plan.md` | `LC-ID`, `PPDCS特征`, `设计Skill`, `主信号`, `候选特征`, `排除摘要`, `待确认事项` | 确认 LC 已进入 `combination-design` |
| `design-planner-reasoning.md` | `recommended_feature`, `design_skill`, `fact_status`, `primary_signal`, `candidate_features`, `exclusion_reasons`, `factor_refs`, `uncertain facts` | 判断为何需要组合压缩，而不是 Parameter / Data |
| `logic-cases.md` | `动作路径`, `因子-取值表`, `topology_bindings`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 形成 factor catalog、拓扑绑定目录与叠加位置 |
| `test-data.md` | `TD-ID`, `factor_ref`, `value_set`, `status`, `confirmation_gap_refs` | 提取各因子取值集与待确认边界 |
| `directory-structure.md` | `### 三级目录`, 四级/五级目录层级映射 | 回查完整 `三级→四级→五级` 层级链，用于构造输出文件名 |

## 前置条件

- [ ] 设计计划已确认
- [ ] 当前 LC 在 `design-plan.md` 中被推荐为 `combination-design`
- [ ] `design-planner-reasoning.md` 中同一 LC 的 `design_skill=combination-design`
- [ ] LC / TD 已保留 `factor_refs / confirmation_gap_refs`

## 不确定事实治理

1. 若任一因子值域、约束或工具可用性不明确，必须保留 `[待确认]`。
2. 若 manual fallback 后无法证明覆盖完整，`fact_status` 必须为 `needs-confirmation`。
3. `uncertain facts`、`confirmation_gap_refs`、`uncovered_pairs` 必须进入 `ppdcs/ppdcs/<basename>.md`。
4. 不得因为没有外部工具就只输出“建议 Pairwise”而不输出实际过程工件。

## 五步用例设计过程

### 第一步：输入对齐 + factor catalog

先对齐 design-plan / reasoning / LC / TD，再形成 **factor catalog**：

```markdown
| factor_id | 因子名称 | 值集合/值域 | factor_type | source_ref | fact_status | confirmation_gap_refs |
|-----------|---------|------------|-------------|------------|-------------|------------------------|
| FAC-SERVER-N | 服务器数量 | 1 / 2 / 4 / 8 | parameter | TD-001~004 | confirmed | — |
| FAC-PROTOCOL | 协议 | syslog / restAPI | parameter | TD-005 | confirmed | — |
| FAC-MODE | 发送模式 | 单播 / 并发 / 轮询 | parameter | TD-006 | confirmed | — |
| FAC-ENCRYPT | 加密方式 | off / tls | parameter | TD-007 | needs-confirmation | GAP-ENC-01 |
```

同时计算：

```text
全组合数 = 各因子取值数乘积
```

同步输出 **topology binding catalog**，但默认不参与全组合数、Pairwise 或正交阵列：

```markdown
| topology_binding_id | topology_role | role_usage | bound_topology_object | source_ref | fact_status | promotion_to_factor |
|---------------------|---------------|------------|------------------------|------------|-------------|---------------------|
| TB-LC-005-01 | DEFAULT_INGRESS_PATH | 默认入方向路径 | DUT.port1 | TOPO-001 | confirmed | no |
| TB-LC-005-02 | MIRROR_OBSERVE_PATH | 旁路观察路径 | DUT.port2 | TOPO-001 | needs-confirmation | no |
```

若全组合数 ≤ 12 且无复杂约束，可降级为全组合；否则进入压缩策略。

拓扑角色边界：
- 默认 `topology_role` 不进入 factor catalog、Pairwise / 正交 / 全组合的因子集合，真实端口、link、TOPO 实例绝不作为组合因子值；
- `DUT.port*`、`TG.port*`、link/TOPO 实例只能在 `topology_bindings` 或 PC 物化阶段出现，并必须保留来源与 `fact_status`；
- 只有测试目标明确要求比较多 TOPO 或多接口角色差异时，才允许将 `topology_role` 升级为组合因子；升级时必须记录 `promotion_reason / objective_ref / source_refs / fact_status`；
- 即使 `topology_role` 被升级为组合因子，也只能使用逻辑角色值（如 ingress/egress/client/server），不得使用真实端口名作为取值。

### 第二步：因子值域与约束建模

输出因子-约束模型：

```markdown
| constraint_id | 表达式 | 涉及因子 | 来源 | 处理 |
|---------------|--------|---------|------|------|
| CT-01 | IF 协议=restAPI THEN 端口字段不适用 | FAC-PROTOCOL,FAC-PORT | TD-008 | 过滤非法组合 |
| CT-02 | IF 加密=tls THEN 证书=[待确认] | FAC-ENCRYPT,FAC-CERT | GAP-ENC-01 | 保留 needs-confirmation |
| CT-03 | IF 服务器数量=8 THEN 模式≠单播 | FAC-SERVER-N,FAC-MODE | TP-021 | 过滤非法组合 |
```

要求：
- 约束必须先于组合生成输出；
- 非法组合要能回链到 `constraint_id`；
- 若约束来自未确认事实，组合结果也必须带 `needs-confirmation`。

### 第三步：压缩策略选择 + 工具检测

| 条件 | 策略 |
|------|------|
| 因子 ≤ 3 且全组合可接受 | 全组合 |
| 因子 ≥ 4 或全组合过大 | Pairwise |
| 各因子水平数整齐且已有阵列模板 | 正交 |
| 约束很多 | 先约束过滤，再 Pairwise/正交 |

**外部工具检测顺序**：
1. 检查仓库约定的组合工具入口（如 `scripts/pict_wrapper.py`）；
2. 若存在，记录 `tool_status=available` 并走工具生成；
3. 若不存在，**必须显式进入 fallback**，不能静默略过。

**fallback 决策记录最小骨架**：

```markdown
| field | value |
|------|-------|
| tool_status | unavailable |
| fallback_mode | manual-greedy-pairwise |
| reason | 未发现已批准外部组合工具 |
| coverage_target | 因子两两取值对全覆盖 |
| risk | 复杂约束下可能存在未验证对 |
| fact_status | confirmed / needs-confirmation |
```

### 第四步：组合生成（工具路径或显式 fallback）

#### 4.1 工具路径

- 生成因子模型；
- 导入约束；
- 输出组合表；
- 记录工具版本、输入模型、过滤规则、压缩率。

#### 4.2 fallback 路径（无外部工具时必须执行）

按以下步骤输出人工可审计过程：

1. 列出全部因子对；
2. 为每个因子对列出待覆盖取值对；
3. 用贪心法生成组合行；
4. 输出 `pair coverage checklist`；
5. 若仍有未覆盖对，记录 `uncovered_pairs` 并降级 `fact_status=needs-confirmation`。

**pair coverage checklist 示例**：

```markdown
| pair_id | 因子对 | 待覆盖取值对数 | 已覆盖取值对数 | 状态 | notes |
|---------|-------|---------------|---------------|------|------|
| PAIR-01 | 服务器数量 × 协议 | 8 | 8 | covered | — |
| PAIR-02 | 服务器数量 × 模式 | 12 | 12 | covered | CT-03 已过滤非法对 |
| PAIR-03 | 协议 × 加密方式 | 4 | 3 | needs-confirmation | TLS 证书约束未确认 |
```

**组合结果最小骨架**：

```markdown
| combo_id | 服务器数量 | 协议 | 模式 | 加密方式 | td_refs | constraint_refs | fact_status |
|----------|-----------|------|------|---------|---------|-----------------|-------------|
| C-01 | 1 | syslog | 单播 | off | TD-001,TD-005 | — | confirmed |
| C-02 | 4 | restAPI | 并发 | tls | TD-003,TD-007 | CT-02 | needs-confirmation |
```

组合生成守则：
- Pairwise 覆盖目标只统计业务/配置/数据类因子；默认不统计 `topology_role` 与 `bound_topology_object`；
- 若启用拓扑角色组合，应在 pair coverage checklist 中单列拓扑角色因子对，并说明为何该覆盖是测试目标必要条件；
- 过滤约束不得把真实端口写成因子取值，应通过 `topology_binding_ref` 指向 LC 绑定。

### 第五步：实际取值 data row 分配、LC 叠加与物理用例输出

在组合框架上分配实际业务值，并映射到 LC：

```markdown
| data_row_id | combo_id | lc_step_ref | 实际取值 | td_refs | 预期结果 | fact_status | confirmation_gap_refs |
|-------------|----------|-------------|---------|---------|---------|-------------|------------------------|
| DR-001 | C-01 | P1-Step2 | serverCount=1, protocol=syslog, mode=单播, encrypt=off | TD-001,TD-005 | 外发成功 | confirmed | — |
| DR-002 | C-02 | P1-Step2 | serverCount=4, protocol=restAPI, mode=并发, encrypt=tls | TD-003,TD-007 | TLS 行为[待确认] | needs-confirmation | GAP-ENC-01 |
```

再输出物理用例：

```markdown
| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | 组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | 首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|------------|------------|--------|---------|----------|
| 日志中心 | 日志服务器 | 日志外发 | 4 台服务器并发外发组合验证 | PC-SVR-CMB-001 | P1 | 单台防火墙 + 多台日志服务器 | | 已配置 4 台日志服务器 | 1.进入外发配置<br>2.按组合设置协议/模式/加密<br>3.保存并触发外发 | 1.配置保存成功<br>2.外发覆盖目标服务器 | V60R001C01 | | 组合,Pairwise | 功能 | 否 |
| 日志中心 | 日志服务器 | 日志外发 | TLS 并发外发组合验证[待确认] | PC-SVR-CMB-006 | P2 | 单台防火墙 + 多台日志服务器 | | TLS 证书规则未确认 | 1.进入外发配置<br>2.配置 tls + 并发外发<br>3.触发外发 | 1.TLS 证书依赖与预期结果[待确认] | V60R001C01 | | 组合,待确认 | 功能 | 否 |
```

## 输出目录结构

```text
ppdcs/ppdcs/<basename>.md
ppdcs/pc/<basename>.md
```

`ppdcs/ppdcs/<basename>.md` 至少包含：
1. `design-plan.md` 与 `design-planner-reasoning.md` 的输入对齐结果；
2. factor catalog；
3. 约束表；
4. 压缩策略决策；
5. 工具检测结果；
6. 若工具不可用，明确 fallback 记录、pair coverage checklist、`uncovered_pairs`；
7. combo/data row → LC 叠加结果。

## 组合爆炸检测

- 全组合数 > 12：建议压缩
- 全组合数 > 50：默认优先 Pairwise
- 约束密集：先过滤非法组合，再评估压缩
- fallback 后仍存在 `uncovered_pairs`：必须标记 `needs-confirmation`

## 优先级分配规则

| 组合类型 | 优先级 |
|---------|--------|
| 核心有效典型组合 | P1 |
| Pairwise / 正交覆盖组合 | P2 |
| 约束边界组合 | P2~P3 |
| `needs-confirmation` 组合 | P3 |

## 公共因子库补充契约

- combination-design 必须消费 lock 指定公共库中的 `factor_groups / constraints / applicable_when / usage_profiles`。
- 生成组合前必须先按公共库约束过滤无效组合。
- 配置组合和功能组合分开处理；禁止把配置拒绝样本带入功能组合。
- 优先使用 `factor_bindings` 形成 factor catalog；`factor_refs` 仅作兼容摘要。
- `factor_bindings` 不承载真实端口；拓扑角色和端口物化通过 LC `topology_bindings` 旁路保留，不替换公共因子库规则。

## Gotchas

- 不得只消费 `design-plan.md`；必须同时消费 `design-planner-reasoning.md`
- 不能只给“推荐 Pairwise”而不输出组合过程和 coverage checklist
- 外部工具不可用时，必须显式写出 fallback；不能沉默失败
- manual fallback 无法证明覆盖完整时，必须保留 `uncovered_pairs` 和 `needs-confirmation`
- 无效值通常单独验证，不与无效值彼此组合
- 常见误用：把 `DUT.port1 / TG.port2` 当成 Pairwise 取值。真实端口是 PC 物化目标，不是组合因子值。

## 方法论细则（用户可定制）

> 以下为设计方法的指导框架。用户可根据项目特点和领域知识补充具体规则。
> 详细的 PPDCS 方法论参见 `ppdcs-analysis-step-by-step.md`。

### 组合法设计步骤

**目标**：对多因子组合爆炸场景，通过约束建模和压缩策略（Pairwise/正交/全组合）生成有效覆盖的因子组合，并通过 PICT 模型或显式 fallback 输出可审计的组合过程。

**核心步骤**：
1. 从 LC 因子-取值表和 test-data 形成 factor catalog，计算全组合数
2. 识别因子间约束：IF/THEN 条件、互斥关系、依赖关系，形成约束模型
3. 根据全组合数和约束复杂度选择压缩策略：全组合数 ≤12 → 全组合；≥4 且全组合大 → Pairwise；水平数整齐且有阵列模板 → 正交
4. 检测外部组合工具（如 PICT）；若可用，生成 PICT 模型文件并运行；若不可用，执行显式 manual-greedy-pairwise fallback
5. 输出 pair coverage checklist；未覆盖对记录为 uncovered_pairs 并降级 fact_status

**关键决策点**：
- Pairwise vs 正交 vs 全组合选择标准：全组合数阈值、因子水平数均匀度、约束密度
- PICT 模型文件构建规则：因子定义语法、约束表达式（IF/THEN）、种子组合
- fallback 覆盖率评估：greedy-pairwise 无法保证的覆盖对必须在 checklist 中显式暴露

**示例**（防火墙领域）：
以日志外发服务器配置为例，4 个因子（服务器数量 1/2/4/8、协议 syslog/restAPI、发送模式 单播/并发/轮询、加密 off/tls），全组合 4×2×3×2=48 过大。约束 CT-01：协议=restAPI 时端口字段不适用。压缩策略选 Pairwise，PICT 生成约 12 条组合，pair coverage checklist 验证全部因子对覆盖。

**下游影响**：
combo/data_row 分配表直接决定 PC 生成（combo_id → data_row → PC）；pair coverage checklist 的 uncovered_pairs 在 GATE-4 覆盖率检查中触发告警；PICT 模型文件作为 PPDCS 过程工件持久化；needs-confirmation 组合生成的 PC 不参与已覆盖计数。

## 验收标准

- [ ] 同时消费 `design-plan.md` 与 `design-planner-reasoning.md`
- [ ] 第一步已形成 factor catalog，并计算全组合数
- [ ] 第二步已输出因子约束模型
- [ ] 第三步已明确压缩策略与工具检测结果
- [ ] 外部工具不可用时已输出显式 fallback 过程，而非只给一句说明
- [ ] 第四步已输出组合结果和 pair coverage checklist；存在缺口时已保留 `uncovered_pairs`
- [ ] 第五步已输出 data row 分配，并明确 `LC + combo/data_row = PC`
- [ ] `needs-confirmation` / `confirmation_gap_refs` 未被静默折叠
- [ ] 默认 Pairwise 未纳入 `topology_role`；若纳入，已记录明确测试目标和升级原因；真实端口未作为组合因子值
