---
name: data-design
description: >-
  D-Data 等价类+边界值法用例设计：五步完成等价类划分→等价类隔离+边界值识别→LC→三类数据分配→物理用例。
  基于 PPDCS 中 D-Data 特征：数据有取值范围，各数据项相对独立。
  触发词包括：等价类、边界值、数据分析、D-Data。
  适用场景：MFQ 设计阶段，PPDCS 特征为 D-Data 的逻辑用例。
argument-hint: "逻辑用例 ID（如 LC-004）"
user-invokable: true
status: active
---

## 目标

对设计计划中 PPDCS 特征为 **D-Data** 的逻辑用例，输出完整过程工件：

`输入对齐 → factor catalog → 值域/等价类/边界分析 → 独立性检查 → data row 分配 → LC 叠加 → physical cases`

## 理论基础

D-Data 是 PPDCS 五特征之一：
> 被测功能的数据项有明确取值范围，且各数据项可相对独立地验证合法性。

**关键区分**：
- D-Data vs P-Parameter：存在确定规则依赖 = Parameter；不存在 = Data
- D-Data vs C-Combination：单项独立验证足够 = Data；需跨因子交叉覆盖 = Combination

**建模工具**：等价类划分 + 边界值分析

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
| `design-plan.md` | `LC-ID`, `PPDCS特征`, `设计Skill`, `主信号`, `候选特征`, `排除摘要`, `待确认事项` | 确认 LC 已进入 `data-design` |
| `design-planner-reasoning.md` | `recommended_feature`, `design_skill`, `fact_status`, `primary_signal`, `candidate_features`, `exclusion_reasons`, `factor_refs`, `uncertain facts` | 判断为什么是 D-Data、哪些事实未确认 |
| `logic-cases.md` | `动作路径`, `因子-取值表`, `topology_bindings`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 建立 factor catalog、拓扑绑定目录与 LC 叠加位置 |
| `test-data.md` | `TD-ID`, `factor_ref`, `value_set`, `source_section`, `status`, `confirmation_gap_refs` | 提取取值域、边界、异常值 |
| `directory-structure.md` | `### 三级目录`, 四级/五级目录层级映射 | 回查完整 `三级→四级→五级` 层级链，用于构造输出文件名 |

若 reasoning 提示 `candidate-secondary=P-Parameter / C-Combination`：
- 不得直接忽略；
- 必须在独立性检查中显式复核；
- 若复核仍无法排除，保留 `needs-confirmation`。

## 前置条件

- [ ] 设计计划已确认
- [ ] 当前 LC 在 `design-plan.md` 中被推荐为 `data-design`
- [ ] `design-planner-reasoning.md` 中同一 LC 的 `design_skill=data-design`
- [ ] LC / TD 已保留 `factor_refs / confirmation_gap_refs`

## 不确定事实治理

1. `TD.status=needs-confirmation` 的边界值只能以 `[待确认]` 进入数据分析表。
2. 缺最小值 / 最大值 / 精度 / 默认值时，不得脑补。
3. 若发现交叉约束或规则依赖，必须写明“可能应切换到 `parameter-design` / `combination-design`”。
4. `ppdcs/ppdcs/<basename>.md` 中必须保留 reasoning 的 `uncertain facts` 与当前数据分析结论的映射。

## 拓扑绑定边界

- 必须消费 LC 的 `topology_bindings`，但拓扑绑定不参与等价类划分和边界值分析；
- `D-Data` 的数据项和值域不得使用 `DUT.port*`、`TG.port*`、link/TOPO 实例；真实组网对象只能作为 `topology_bindings` / PC 物化目标；
- 逻辑拓扑角色（如 ingress/egress/client/server）可作为绑定维度保留，但不得被当作数据项边界值；
- 若 TD `value_set` 中出现真实端口或 TOPO 实例，必须移入拓扑绑定记录，并保留 `source_ref / fact_status`；来源不清时对应 data row 降级为 `needs-confirmation`。

## 五步用例设计过程

### 第一步：输入对齐 + factor catalog

先基于设计计划、reasoning、LC、TD 形成 **factor catalog**：

```markdown
| factor_id | 数据项 | 值域摘要 | data_type | source_ref | fact_status | confirmation_gap_refs |
|-----------|-------|---------|-----------|------------|-------------|------------------------|
| FAC-RETENTION | 日志保存天数 | 1~365 | integer | TD-001~007 | confirmed | — |
| FAC-SIZE | 日志文件大小 | 1~1024 MB | integer | TD-008~010 | confirmed | — |
| FAC-PATH | 备份路径 | 本地路径 / 远程路径 | string | TD-011 | needs-confirmation | GAP-PATH-01 |
```

要求：
- factor catalog 先于等价类划分输出；
- 每个数据项都要保留 `source_ref` 与 `fact_status`；
- 值域来自 TD 时必须记录 TD 编号。
- factor catalog 只收录数据项；真实端口、link 或 TOPO 实例不得作为 `数据项` 或 `值域摘要`，需单列为拓扑绑定旁路信息。

### 第二步：值域、等价类与边界值识别

为每个数据项输出完整分析表：

```markdown
| factor_id | value_class | 取值/范围 | class_type | boundary_role | source_refs | fact_status |
|-----------|-------------|-----------|------------|---------------|-------------|-------------|
| FAC-RETENTION | EVP-01 | 30 | valid-typical | typical | TD-001 | confirmed |
| FAC-RETENTION | BVP-LOW | 1 | valid-boundary | min-on | TD-002 | confirmed |
| FAC-RETENTION | BVP-HIGH | 365 | valid-boundary | max-on | TD-003 | confirmed |
| FAC-RETENTION | IVP-LOW | 0 | invalid | min-off | TD-004 | confirmed |
| FAC-RETENTION | IVP-HIGH | 366 | invalid | max-off | TD-005 | confirmed |
| FAC-RETENTION | IVP-TBD | [待确认] | invalid | precision-gap | TD-006 | needs-confirmation |
```

边界值建议：
- 数值型：`min, min+1, typical, max-1, max, min-1, max+1`
- 枚举型：合法枚举 + 非法枚举 + 空值
- 字符串型：空串、超长、非法字符、编码边界

### 第三步：独立性检查与覆盖策略判定

在进入 PC 设计前，必须先判断“是否仍然是 D-Data”：

```markdown
| 检查项 | 结论 | 证据 | 处理 |
|--------|------|------|------|
| 数据项 A 是否依赖 B 的值 | 否 | reasoning 排除 Parameter；TD 无 IF/THEN | 保持 D-Data |
| 数据项间是否需交叉覆盖 | 否 | reasoning 排除 Combination；LC 动作路径稳定 | 保持 D-Data |
| 是否存在待确认交叉约束 | 是 | GAP-003 | fact_status=needs-confirmation |
```

覆盖策略：

| 数据类型 | 处理策略 |
|---------|---------|
| 有效典型值 | 可合并 |
| 有效边界值 | 单独保留或与典型值邻近合并 |
| 无效值 | 必须隔离，一次一个无效值 |
| `[待确认]` 边界 | 单独保留为 `needs-confirmation` |

### 第四步：三类数据分配与 LC 叠加

将数据分析结果分配为可执行 data row：

```markdown
| data_row_id | data_type | lc_step_ref | 分配值 | td_refs | 预期结果 | fact_status | confirmation_gap_refs |
|-------------|-----------|-------------|-------|---------|---------|-------------|------------------------|
| DR-001 | valid-typical | P1-Step2 | retention=30,size=512 | TD-001,TD-008 | 保存成功 | confirmed | — |
| DR-002 | valid-boundary | P1-Step2 | retention=1,size=512 | TD-002,TD-008 | 保存成功 | confirmed | — |
| DR-003 | invalid-off | P1-Step2 | retention=0,size=512 | TD-004,TD-008 | 提示输入无效 | confirmed | — |
| DR-004 | invalid-gap | P1-Step2 | path=[待确认] | TD-011 | 路径校验结果[待确认] | needs-confirmation | GAP-PATH-01 |
```

叠加规则：
- `LC + data_row = PC seed`
- 无效值一次只变一个，其余保持有效值
- `needs-confirmation` data row 只能输出 `needs-confirmation` PC
- PC seed 若需要真实端口，只能从 LC `topology_bindings` 物化，并在过程文档记录 `topology_binding_ref / materialized_object / source_ref / fact_status`。

### 第五步：物理用例输出

```markdown
| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | 组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | 首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|------------|------------|--------|---------|----------|
| 日志中心 | 配置管理 | 日志备份配置 | 日志保存天数最小值配置 | PC-CFG-DAT-001 | P2 | 单台防火墙 | | 管理员已登录 | 1.进入日志配置<br>2.将保存天数设置为 1<br>3.保存并刷新 | 1.保存成功<br>2.页面显示保存天数为 1 | V60R001C01 | | 边界值,等价类 | 功能 | 否 |
| 日志中心 | 配置管理 | 日志备份配置 | 备份路径非法值校验[待确认] | PC-CFG-DAT-009 | P3 | 单台防火墙 | | 管理员已登录 | 1.进入日志配置<br>2.输入路径[待确认]<br>3.点击保存 | 1.系统路径校验规则[待确认] | V60R001C01 | | 待确认,数据边界 | 功能 | 否 |
```

## 输出目录结构

```text
ppdcs/ppdcs/<basename>.md
ppdcs/pc/<basename>.md
```

`ppdcs/ppdcs/<basename>.md` 至少包含：
1. `design-plan.md` 与 `design-planner-reasoning.md` 的输入对齐结果；
2. factor catalog；
3. 等价类/边界值分析表；
4. Data vs Parameter / Combination 的独立性检查；
5. data row 分配表；
6. LC 叠加说明。

## 优先级分配规则

| 用例类型 | 优先级 |
|---------|--------|
| 有效典型值 | P1 |
| 有效边界值 | P2 |
| 无效边界值 | P2 |
| 类型错误 / 空值 | P3 |
| `needs-confirmation` 边界 | P3 |

## 公共因子库补充契约

- data-design 必须消费 lock 指定公共库中的 `domain_expr / sample_definitions / usage_profiles`。
- 优先使用 `factor_bindings` 中的 `sample_id` 和 `expr` 形成 factor catalog；`factor_refs` 仅作兼容摘要。
- 配置用例只使用 `accepted_config_samples / rejected_config_samples`；功能用例不得使用 `rejected_config_samples` 作为前置。
- 表达式样本在 PC 阶段才物化，并记录 `materialized_value` 与 deterministic seed。
- `factor_bindings` 中的样本表达逻辑数据，不承载真实端口；拓扑物化使用 LC `topology_bindings`，不得替换公共因子库的样本规则。

## Gotchas

- 不得只消费 `design-plan.md`；必须同时消费 `design-planner-reasoning.md`
- D-Data 的核心是“独立性”；若独立性被打破，必须显式回退
- 无效值必须隔离；不能把多个无效值压进同一 PC
- `[待确认]` 边界、默认值、精度要求必须透传
- 输出不能只剩最终 PC，必须保留等价类、边界策略和分配过程
- 不得把 TOPO 实例、link 或真实端口当作数据值做等价类/边界值分析；它们只能作为 PC 物化目标。

## 方法论细则（用户可定制）

> 以下为设计方法的指导框架。用户可根据项目特点和领域知识补充具体规则。
> 详细的 PPDCS 方法论参见 `ppdcs-analysis-step-by-step.md`。

### 等价类+边界值法设计步骤

**目标**：对独立数据项进行等价类划分和边界值分析，通过一次一个无效值的隔离策略生成覆盖合法/非法取值的 PC。

**核心步骤**：
1. 从 LC 因子-取值表和 test-data 形成 factor catalog，标注 data_type、值域摘要、fact_status
2. 为每个数据项划分等价类：有效典型值（valid-typical）、有效边界值（valid-boundary）、无效值（invalid），标注 boundary_role
3. 按三点法选取边界值：数值型取 min/min+1/typical/max-1/max/min-1/max+1；枚举型取合法枚举+非法枚举+空值
4. 执行独立性检查：确认数据项间无规则依赖（否则应回退 Parameter/Combination），输出检查表
5. 分配 data row：有效典型值可合并，有效边界值单独保留，无效值一次一个隔离

**关键决策点**：
- 等价类粒度：何时拆分/合并——取决于取值对预期结果的影响是否有差异
- 独立性判断标准：数据项 A 的合法值范围不因 B 的取值改变 → 独立；TD 中出现 IF/THEN → 依赖
- 边界值三点法适用条件：数值型必用三点法；枚举型用合法+非法；字符串型加空串/超长/非法字符

**示例**（防火墙领域）：
以日志保存天数配置为例，数据项为"保存天数"（1~365）。等价类划分：有效典型值=30，有效边界值=1/365，无效边界值=0/366。每个无效值单独一条 PC（PC-LOG-004: retention=0, size=512），其余数据项保持有效值。

**下游影响**：
data_row 分配表直接决定 PC 生成（LC + data_row → PC）；独立性检查结论影响方法回退决策（若检查失败，需在过程文档中记录为何切换）；needs-confirmation 边界值生成的 PC 在 GATE-4 覆盖率检查中不参与已覆盖计数。

## 验收标准

- [ ] 同时消费 `design-plan.md` 与 `design-planner-reasoning.md`
- [ ] 第一步已形成 factor catalog，且保留 `fact_status / confirmation_gap_refs`
- [ ] 第二步每个数据项都有值域、等价类、边界值分析
- [ ] 第三步已执行独立性检查，并显式说明为何不是 Parameter / Combination
- [ ] 第四步输出 data row 分配，并明确 `LC + data_row = PC`
- [ ] `needs-confirmation` 事实未被静默折叠
- [ ] 物理用例以 16 列表格输出，且可回链到 `TD-ID / factor_id / trace_refs`
- [ ] 已消费 LC `topology_bindings`；真实端口物化保留来源和 `fact_status`，且未进入数据项值域
