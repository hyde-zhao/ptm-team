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

> 统一输出规则：本 Skill 的方法过程写入 `design/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`，物理用例写入 `design/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`。不得创建 `design/<module>/<sub-module>/` 深目录；同名冲突追加 `-<LC-ID>`。


- 适用阶段：MFQ 的 design 阶段
- 设计输入：`analysis/integration/design-plan.md`
- reasoning 输入：`analysis/plan/design-planner-reasoning.md`
- 上游 trace 输入：`analysis/integration/logic-cases.md`、`analysis/integration/test-data.md`
- PPDCS 基线：`analysis/m-analysis/ppdcs-annotation.md`
- 输出：`design/ppdcs/<basename>.md` 与 `design/pc/<basename>.md`

## 必收输入契约（STORY-05 / STORY-04）

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `design-plan.md` | `LC-ID`, `PPDCS特征`, `设计Skill`, `主信号`, `候选特征`, `排除摘要`, `待确认事项` | 确认 LC 已进入 `data-design` |
| `design-planner-reasoning.md` | `recommended_feature`, `design_skill`, `fact_status`, `primary_signal`, `candidate_features`, `exclusion_reasons`, `factor_refs`, `uncertain facts` | 判断为什么是 D-Data、哪些事实未确认 |
| `logic-cases.md` | `动作路径`, `因子-取值表`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 建立 factor catalog 与 LC 叠加位置 |
| `test-data.md` | `TD-ID`, `factor_ref`, `value_set`, `source_section`, `status`, `confirmation_gap_refs` | 提取取值域、边界、异常值 |

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
4. `design/ppdcs/<basename>.md` 中必须保留 reasoning 的 `uncertain facts` 与当前数据分析结论的映射。

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

### 第五步：物理用例输出

```markdown
| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | 组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | 首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|------------|------------|--------|---------|----------|
| 日志中心 | 配置管理 | 日志备份配置 | 日志保存天数最小值配置 | PC-CFG-DAT-001 | P2 | 单台防火墙 | | 管理员已登录 | 1.进入日志配置<br>2.将保存天数设置为 1<br>3.保存并刷新 | 1.保存成功<br>2.页面显示保存天数为 1 | V60R001C01 | | 边界值,等价类 | 功能 | 否 |
| 日志中心 | 配置管理 | 日志备份配置 | 备份路径非法值校验[待确认] | PC-CFG-DAT-009 | P3 | 单台防火墙 | | 管理员已登录 | 1.进入日志配置<br>2.输入路径[待确认]<br>3.点击保存 | 1.系统路径校验规则[待确认] | V60R001C01 | | 待确认,数据边界 | 功能 | 否 |
```

## 输出目录结构

```text
design/ppdcs/<basename>.md
design/pc/<basename>.md
```

`design/ppdcs/<basename>.md` 至少包含：
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

## Gotchas

- 不得只消费 `design-plan.md`；必须同时消费 `design-planner-reasoning.md`
- D-Data 的核心是“独立性”；若独立性被打破，必须显式回退
- 无效值必须隔离；不能把多个无效值压进同一 PC
- `[待确认]` 边界、默认值、精度要求必须透传
- 输出不能只剩最终 PC，必须保留等价类、边界策略和分配过程

## 验收标准

- [ ] 同时消费 `design-plan.md` 与 `design-planner-reasoning.md`
- [ ] 第一步已形成 factor catalog，且保留 `fact_status / confirmation_gap_refs`
- [ ] 第二步每个数据项都有值域、等价类、边界值分析
- [ ] 第三步已执行独立性检查，并显式说明为何不是 Parameter / Combination
- [ ] 第四步输出 data row 分配，并明确 `LC + data_row = PC`
- [ ] `needs-confirmation` 事实未被静默折叠
- [ ] 物理用例以 16 列表格输出，且可回链到 `TD-ID / factor_id / trace_refs`
