---
name: coverage-verifier
description: >-
  双层覆盖率验证：校验需求层（SR→TP→LC→TD→PC）与测试点层（TP→LC/设计过程→PC）的完整覆盖，
  并保留 trace / gap / fact_status 字段。
  触发词包括：覆盖检查、覆盖率、覆盖验证、需求覆盖。
  适用场景：MFQ 分析的 coverage 阶段。
argument-hint: "无需参数，自动扫描 analysis/coverage 所需输入"
user-invokable: true
status: active
---

## 目标

在所有设计 Skill 完成后，输出 **双层覆盖报告 + 未覆盖项清单**，并确保 STORY-06 / STORY-07 的**完整过程工件**被消费，而不是只看最终 PC：

1. **需求层**：校验 `SR → TP → LC → TD → PC` 是否完整闭环；
2. **测试点层**：校验 `TP → LC / design/ppdcs / design/pc` 是否落地为可执行 PC；
3. 保留并透传 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status`；
4. 对缺口输出结构化原因，而不是只给覆盖率数字。

## 适用范围

- 适用阶段：MFQ 的 coverage 阶段
- 输入：`analysis/integration/`、`design/ppdcs/`、`design/pc/`、`process/REQUIREMENTS.md`
- 输出：`analysis/coverage/`

## 前置条件

- [ ] `process/REQUIREMENTS.md` 可读取
- [ ] `analysis/integration/all-test-points.md`、`logic-cases.md`、`test-data.md`、`coverage-matrix.md` 已生成
- [ ] `design/ppdcs/` 与 `design/pc/` 下已存在各 LC 单文件
- [ ] 上游 LC / TD / PC 已保留 trace、gap、fact_status 字段

## 必须消费的输入契约

### 1. 基线与整合层

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `process/REQUIREMENTS.md` | `SR/REQ 编号`, 需求描述 | 需求层覆盖基线 |
| `all-test-points.md` | `TP-ID`, `关联SR`, `scenario_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 需求→测试点映射 |
| `logic-cases.md` | `LC-ID`, `source_tp_ids`, `关联SR`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 测试点→逻辑用例映射 |
| `test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `scenario_refs`, `action_source_refs`, `trace_refs`, `confirmation_gap_refs`, `status` | LC→TD 落地与数据链校验 |
| `coverage-matrix.md` | `SR`, `TP-IDs`, `LC-ID`, `TD-IDs`, `action_source_refs`, 覆盖状态 | 与设计产物交叉复核 |

### 2. STORY-06 / STORY-07 设计层（必须全量消费）

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `design/ppdcs/<basename>.md`（process/state） | `recommended_feature`, `design_skill`, `path_id / state_path_id`, `coverage_goal`, `td_ref`, `trace_refs`, `scenario_refs`, `action_source_refs`, `confirmation_gap_refs`, `fact_status` | 校验 TP 是否真正进入设计过程 |
| `design/ppdcs/<basename>.md`（parameter/data/combination） | `design_skill`, `rule_id / value_class / combo_id / data_row_id`, `factor_refs`, `td_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 校验完整过程已进入覆盖链 |
| `design/pc/<basename>.md` | `physical_case_id`, `logic_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status` | 校验最终 PC 覆盖 |

> 不允许只统计 `design/pc/*.md` 数量就判定“已覆盖”；必须确认 LC 在 `design/ppdcs/*.md` 中已有可审计过程。

## 执行流程

### 步骤 1：建立覆盖基线

1. 从 `process/REQUIREMENTS.md` 提取全部需求编号；
2. 从 `all-test-points.md` 建立 `SR → TP` 索引；
3. 从 `logic-cases.md` 建立 `TP → LC` 索引；
4. 从 `test-data.md` 建立 `LC → TD` 索引；
5. 从 `design/pc/*.md` 建立 `LC → PC` 索引；
6. 从 `design/ppdcs/*.md` 建立 `LC → 设计过程证据` 索引。

### 步骤 2：校验设计过程完整性

对每个 LC，至少确认：

- 存在 `design/ppdcs/<basename>.md`
- 存在 `design/pc/<basename>.md`
- PPDCS 文件中存在可回链的 `path / state_path / rule / value_class / combo / data_row`
- PC 文件中 `logic_case_id` 与 LC 对齐

若缺任一项：

- 不得把该 LC 记为“完整覆盖”
- 在覆盖报告中列入 `design_artifact_gaps`
- 保留相关 `confirmation_gap_refs / fact_status`

### 步骤 3：需求层覆盖检查

对每条需求：

1. 找到关联 TP；
2. 找到覆盖这些 TP 的 LC；
3. 找到 LC 对应 TD 与 PC；
4. 复核 `coverage-matrix.md` 与设计过程是否一致；
5. 输出覆盖状态：
   - `covered`
   - `covered-with-confirmation-gap`
   - `uncovered`

**需求覆盖矩阵至少保留以下字段：**

| 字段 | 说明 |
|------|------|
| `requirement_id` | 需求编号 |
| `tp_ids` | 命中的测试点 |
| `logic_case_ids` | 命中的 LC |
| `td_ids` | 命中的 TD |
| `pc_ids` | 命中的 PC |
| `feature_tags` | 来自 PC / 设计输出的标签 |
| `trace_refs` | 汇总 trace |
| `scenario_refs` | 汇总场景 |
| `action_source_refs` | 汇总 atomic-ops `op_id` |
| `confirmation_gap_refs` | 未确认事实 |
| `fact_status` | `confirmed / needs-confirmation` |
| `coverage_status` | 覆盖结论 |

### 步骤 4：测试点层覆盖检查

对每个 TP：

1. 确认是否进入某个 LC；
2. 确认该 LC 是否在 `design/ppdcs/<basename>.md` 中有实际设计证据；
3. 确认是否至少落成 1 个 PC；
4. 输出覆盖状态：
   - `covered-direct`
   - `covered-merged`
   - `not-designed-with-reason`
   - `uncovered`

**测试点覆盖矩阵至少保留以下字段：**

| 字段 | 说明 |
|------|------|
| `tp_id` | 测试点编号 |
| `logic_case_id` | 归属 LC |
| `physical_case_ids` | 命中的 PC |
| `requirement_ids` | 关联需求 |
| `feature_tags` | 关联标签 |
| `trace_refs` | trace 链 |
| `scenario_refs` | 场景来源 |
| `action_source_refs` | atomic-ops `op_id` |
| `factor_refs` | 因子 |
| `confirmation_gap_refs` | 未确认事实 |
| `fact_status` | `confirmed / needs-confirmation` |
| `coverage_status` | 覆盖结论 |
| `notes` | 合并原因 / 不设计原因 / 缺口说明 |

### 步骤 5：输出覆盖摘要与未覆盖项

至少输出：

- `coverage_summary`
- `requirement_gaps`
- `test_point_gaps`
- `design_artifact_gaps`

未覆盖项建议只能基于**已存在结构化证据**给出：

- 缺 LC
- 缺 TD
- 缺 `design/ppdcs/<basename>.md`
- 缺 PC
- 因 `confirmation_gap_refs` 无法确认

不得补写新的业务规则、状态机、接口或工具行为。

## 输出文件

| 文件 | 内容 |
|------|------|
| `requirement-coverage.md` | 需求层覆盖矩阵 + 统计 + 需求缺口 |
| `test-point-coverage.md` | 测试点层覆盖矩阵 + 统计 + 测试点缺口 |
| `coverage-summary.md` | 汇总 `coverage_summary / requirement_gaps / test_point_gaps / design_artifact_gaps` |

## 输出格式参考

### `requirement-coverage.md`

```markdown
## 需求覆盖矩阵

| requirement_id | tp_ids | logic_case_ids | td_ids | pc_ids | feature_tags | trace_refs | scenario_refs | action_source_refs | confirmation_gap_refs | fact_status | coverage_status |
|----------------|--------|----------------|--------|--------|--------------|------------|---------------|--------------------|-----------------------|-------------|-----------------|
| REQ-018 | TP-M-001,TP-F-003 | LC-001 | TD-001,TD-009 | PC-001,PC-002 | coverage,traceability | TR-001,TR-009 | SCN-001 | fw_config_log_server | — | confirmed | covered |
| REQ-019 | TP-M-010 | LC-004 | TD-014 | — | delivery,feature-tags | TR-020 | SCN-007 | fw_unknown_gap_008 | GAP-DEL-01 | needs-confirmation | uncovered |
```

### `test-point-coverage.md`

```markdown
## 测试点覆盖矩阵

| tp_id | logic_case_id | physical_case_ids | requirement_ids | feature_tags | trace_refs | scenario_refs | action_source_refs | factor_refs | confirmation_gap_refs | fact_status | coverage_status | notes |
|------|----------------|-------------------|-----------------|--------------|------------|---------------|--------------------|-------------|-----------------------|-------------|-----------------|------|
| TP-Q-REL-001 | LC-REL-001 | PC-REL-001 | REQ-018 | reliability,recovery | TR-Q-001 | SCN-REL-001 | fw_power_cycle | FAC-RECOVERY-TIME | — | confirmed | covered-direct | — |
| TP-F-TOOL-002 | LC-TOOL-003 | — | REQ-027 | tool-analysis | TR-F-010 | SCN-TOOL-001 | fw_observe_timeline | FAC-TIMELINE | GAP-TOOL-02 | needs-confirmation | uncovered | 缺可执行 PC |
```

## 质量门控

| 指标 | 阈值 |
|------|------|
| 需求覆盖率 | = 100% |
| 测试点覆盖率 | ≥ 95% |
| `design_artifact_gaps` | = 0 |

## Gotchas

- 必须消费 STORY-06 / STORY-07 的**完整过程文档**
- 覆盖验证优先依据结构化编号链，再补充已确认文本语义
- `feature_tags` 缺失时应报 gap，不得临时脑补
- `fact_status=needs-confirmation` 不能被统计逻辑静默提升为 `confirmed`
- `confirmation_gap_refs` 必须进入报告，不得因“先交付再说”而删除

## 验收标准

- [ ] 输出需求层与测试点层双层覆盖报告
- [ ] 覆盖检查消费 `logic-cases.md`、`test-data.md`、`design/ppdcs/*.md` 与 `design/pc/*.md`
- [ ] 报告保留 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status`
- [ ] 未覆盖项与设计缺口被单独列出
- [ ] 未扩写上游不存在的规则、接口或行为
