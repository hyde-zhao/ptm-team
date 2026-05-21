---
name: parameter-design
description: >-
  P-Parameter 判定表法用例设计：五步完成参数规则提取→约束提取+规则组合→判定表→LC→规则触发参数组→物理用例。
  基于 PPDCS 中 P-Parameter 特征：参数参与业务规则判定，输入组合影响输出。
  触发词包括：判定表、因果图、参数规则、决策树、P-Parameter。
  适用场景：MFQ 设计阶段，PPDCS 特征为 P-Parameter 的逻辑用例。
argument-hint: "逻辑用例 ID（如 LC-001）"
user-invokable: true
status: active
---

## 目标

对设计计划中 PPDCS 特征为 **P-Parameter** 的逻辑用例，输出**完整过程工件**而不是只给最终 PC：

`输入对齐 → factor catalog → 参数范围/规则抽取 → 判定结构 → 规则触发 data row → LC 叠加 → physical cases`

## 理论基础

P-Parameter 是 PPDCS 五特征之一：
> 被测功能的输入参数参与业务规则判定，参数间存在确定性约束，
> 不同参数组合命中不同业务结果。

**关键区分**：
- P-Parameter vs D-Data：参数间存在业务规则 = Parameter；各参数独立 = Data
- P-Parameter vs C-Combination：规则可确定表达 = Parameter；需压缩探索 = Combination
- P-Parameter vs P-Process：主要矛盾是条件判定 = Parameter；主要矛盾是步骤顺序 = Process

**建模工具**：判定表 / 因果图 / 决策树

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
| `design-plan.md` | `LC-ID`, `PPDCS特征`, `推荐方法`, `设计Skill`, `主信号`, `候选特征`, `排除摘要`, `关键trace`, `待确认事项` | 确认该 LC 已被推荐给 `parameter-design` |
| `design-planner-reasoning.md` | `recommended_feature`, `recommended_method`, `design_skill`, `fact_status`, `primary_signal`, `candidate_features`, `exclusion_reasons`, `factor_refs`, `trace refs`, `uncertain facts` | 读取推荐原因和不确定事实，不得只消费计划表 |
| `logic-cases.md` | `动作路径`, `因子-取值表`, `source_tp_ids`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `confirmation_gap_refs`, `test_object_refs`, `factor_refs`, `trace_refs`, `fact_status` | 形成 factor catalog 与 LC 叠加骨架 |
| `test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `source_section`, `trace_refs`, `confirmation_gap_refs`, `status` | 提取参数值域、边界值、待确认项 |

若 `design-plan.md` 与 `design-planner-reasoning.md` 不一致：
- 不得自行选一份静默覆盖另一份；
- 必须在 `design/ppdcs/<basename>.md` 中保留差异；
- 当前 LC 的 `fact_status` 降级为 `needs-confirmation`。

## 前置条件

- [ ] 设计计划已确认
- [ ] 当前 LC 在 `design-plan.md` 中被推荐为 `parameter-design`
- [ ] `design-planner-reasoning.md` 中同一 LC 的 `design_skill=parameter-design`
- [ ] LC / TD 已保留 `factor_refs` 与 `confirmation_gap_refs`

## 不确定事实治理

1. `reasoning.fact_status=needs-confirmation`、`TD.status=needs-confirmation`、`confirmation_gap_refs` 非空时，**不得**写成已确认事实。
2. 缺参数上限、优先级、互斥关系时，用 `[待确认]` 保留原缺口，并透传到规则表与 PC。
3. `uncertain facts` 只能被细化，不能被删除或隐式默认。
4. 若规则优先级冲突无法判定，只能输出候选判定结构，不能伪造唯一规则。

## 五步用例设计过程

### 第一步：输入对齐 + factor catalog

先对齐 STORY-05 计划表与 reasoning，再基于 LC / TD 形成 **factor catalog**：

```markdown
| factor_id | 因子名称 | 来源 | 典型取值/值域 | factor_type | source_ref | fact_status | confirmation_gap_refs |
|-----------|---------|------|--------------|-------------|------------|-------------|------------------------|
| FAC-ROLE | 用户角色 | LC 因子表 + TD | 管理员 / 操作员 / 审计员 | parameter | LC-001 / TD-001~003 | confirmed | — |
| FAC-OP | 操作类型 | LC 因子表 | 查看 / 修改 / 删除 | parameter | LC-001 | confirmed | — |
| FAC-LEVEL | 日志级别 | TD | 通知 / 告警 / 紧急 | parameter | TD-004~006 | needs-confirmation | GAP-LEVEL-01 |
```

要求：
- 优先使用 `factor_refs`；
- `factor_refs` 不足时，才从 LC 因子表与 TD `value_set` 补提；
- factor catalog 必须先于规则抽取产出。

### 第二步：参数范围与规则抽取

对每个参数补齐取值范围、边界、约束来源，并输出规则清单：

```markdown
| rule_id | rule_type | 条件表达式 | 动作/结果 | factor_refs | source_refs | priority | fact_status |
|---------|-----------|------------|-----------|-------------|-------------|----------|-------------|
| R-01 | imply | IF 用户角色=管理员 AND 日志级别=通知 THEN 允许修改/删除 | allow | FAC-ROLE,FAC-LEVEL,FAC-OP | TP-001,TD-001 | P2 | confirmed |
| R-02 | imply | IF 用户角色=操作员 AND 操作类型=删除 THEN 拒绝 | reject | FAC-ROLE,FAC-OP | TP-002 | P1 | confirmed |
| R-03 | mutex | IF 日志级别=紧急 THEN 操作类型≠修改/删除 | reject | FAC-LEVEL,FAC-OP | TP-003 | [待确认] | needs-confirmation |
```

补充规则：
- 约束统一写成 `IF ... THEN ...`；
- 若存在隐含优先级，必须显式列出 `priority`；
- 若某值域仅来自 `needs-confirmation` TD，规则也必须带 `needs-confirmation`。

### 第三步：判定结构建模

根据规则复杂度选择判定表 / 因果图 / 决策树，并输出**完整结构**：

| 场景 | 推荐结构 |
|------|---------|
| 参数 ≤ 4、规则直观 | 判定表 |
| 逻辑嵌套或优先级复杂 | 因果图 → 判定表 |
| 条件分层明显 | 决策树 |

**判定表最小骨架**：

```markdown
| 条件/动作 | Rule-01 | Rule-02 | Rule-03 | Rule-04 |
|-----------|---------|---------|---------|---------|
| 用户角色 | 管理员 | 操作员 | 审计员 | 任意 |
| 操作类型 | 修改 | 删除 | 修改 | 查看 |
| 日志级别 | 通知 | 通知 | 任意 | 任意 |
| 预期结果 | 成功 | 拒绝 | 拒绝 | 成功 |
| trace_refs | TD-001 | TD-002 | TD-003 | TD-004 |
| fact_status | confirmed | confirmed | needs-confirmation | confirmed |
```

判定结构必须同时输出：
- 规则覆盖清单；
- 冗余规则合并说明；
- `excluded / candidate-secondary` 来自 reasoning 的保留说明。

### 第四步：规则触发 data row 分配与 LC 叠加

将每条规则映射为可执行的 data row，再叠加到 LC：

```markdown
| data_row_id | rule_id | lc_step_ref | 触发参数组 | td_refs | 预期结果 | confirmation_gap_refs | fact_status |
|-------------|---------|-------------|-----------|---------|---------|------------------------|-------------|
| DR-001 | R-01 | P1-Step3 | role=admin, op=modify, level=info | TD-001,TD-004 | 保存成功 | — | confirmed |
| DR-002 | R-02 | P1-Step3 | role=operator, op=delete, level=info | TD-002,TD-004 | 403 拒绝 | — | confirmed |
| DR-003 | R-03 | P1-Step3 | role=admin, op=modify, level=critical | TD-003 | 423 拒绝 | GAP-LEVEL-01 | needs-confirmation |
```

叠加规则：
- `LC + data_row = PC seed`；
- 每个 data row 必须绑定 `lc_step_ref`；
- `needs-confirmation` data row 只能生成 `needs-confirmation` PC，不能静默转 confirmed。

### 第五步：物理用例输出

```markdown
| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | 组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | 首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |
|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|---------|------------|------------|--------|---------|----------|
| 日志中心 | 日志管理 | 权限管理 | 管理员修改通知级别日志 | PC-LOG-PRM-001 | P1 | 单台防火墙 | | 管理员已登录；存在通知级别日志 | 1.进入日志管理<br>2.选择通知级别日志<br>3.执行修改并保存 | 1.允许修改<br>2.保存成功 | V60R001C01 | | 权限,判定表 | 功能 | 否 |
| 日志中心 | 日志管理 | 权限管理 | 管理员修改紧急级别日志[待确认] | PC-LOG-PRM-006 | P2 | 单台防火墙 | | 管理员已登录；存在紧急级别日志 | 1.进入日志管理<br>2.选择紧急级别日志<br>3.执行修改 | 1.预期拒绝；具体错误码[待确认] | V60R001C01 | | 权限,待确认 | 功能 | 否 |
```

## 输出目录结构

```text
design/ppdcs/<basename>.md
design/pc/<basename>.md
```

`design/ppdcs/<basename>.md` 至少包含：
1. 来自 `design-plan.md` 的推荐摘要；
2. 来自 `design-planner-reasoning.md` 的 primary/candidate/exclusion/uncertain facts；
3. factor catalog；
4. 规则清单；
5. 判定结构；
6. data row → LC 叠加结果。

## 优先级分配规则

| 规则类型 | 优先级 |
|---------|--------|
| 高频正常规则 | P1 |
| 权限/安全拒绝规则 | P1~P2 |
| 明确边界规则 | P2 |
| `needs-confirmation` 规则 | P2~P3 |
| Don't Care 验证 | P3 |

## 公共因子库补充契约

- parameter-design 必须消费 lock 指定公共库中的 `factor_groups / constraints / usage_profiles / oracle` 因子。
- 优先使用 `factor_bindings` 生成判定条件桩；`factor_refs` 仅作兼容摘要。
- 配置判定使用 accepted/rejected；功能判定使用 hit/miss/fallback/fail，不得混用。
- 业务流量匹配类用例应使用 oracle 因子表达预期命中结果。

## Gotchas

- 不得只看 `design-plan.md`；必须同时消费 `design-planner-reasoning.md`
- factor catalog 未形成前，不得直接写判定表
- `needs-confirmation`、`confirmation_gap_refs`、`uncertain facts` 不能被吞掉
- Parameter 关注**确定性规则**；若主要矛盾变为取值范围，应回退 D-Data；若主要矛盾变为组合压缩，应回退 C-Combination
- `—` / Don't Care 必须说明为什么“不影响结果”

## 验收标准

- [ ] 同时消费 `design-plan.md` 与 `design-planner-reasoning.md`
- [ ] 第一步已形成 factor catalog，且保留 `fact_status / confirmation_gap_refs`
- [ ] 第二步输出参数范围、规则清单、约束类型和优先级
- [ ] 第三步输出完整判定结构，而非只给最终结论
- [ ] 第四步输出规则触发 data row，并明确 `LC + data_row = PC`
- [ ] 未确认事实保持 `needs-confirmation`，未被静默降噪
- [ ] 物理用例以 16 列表格输出，且可回链到 `rule_id / td_refs / factor_refs`
