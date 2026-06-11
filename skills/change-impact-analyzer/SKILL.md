---
name: change-impact-analyzer
description: >-
  需求变更影响分析：分析变更影响模块，增量 MFQ 分析，增量用例设计，
  保证不修改未受影响的用例。
  触发词包括：需求变更、变更分析、增量分析、需求修改。
  适用场景：MFQ 扩展分支 — 需求变更处理。
argument-hint: "变更需求描述或文件路径"
user-invokable: true
status: active
---

## 目标

当特性的测试资产已按 v6 追踪链归档后，收到需求变更时：
1. 直接消费 `Scenario Chain / ptm-atomic / Knowledge Reference / delivery/<特性名>特性测试用例.md`
2. 复用最终测试用例总表的**精确检索语义**命中最小受影响范围
3. 仅对受影响的 MFQ / 设计 / 覆盖资产执行增量处理
4. 保持未受影响资产不变，并保留原有 `trace_refs / confirmation_gap_refs / fact_status`

## 适用范围

- 适用阶段：MFQ 扩展分支（已完成首次用例设计后）
- 输入：变更需求描述 + 已有 `kym/`, `mfq/`, `ppdcs/`, `process/checkpoints/`, `process/STATE.yaml` 基线资产
- 输出：最小影响范围 + 增量更新建议

## 工作区隔离契约

- 以当前特性的 `.input/` 为输入锚点，`.input` 的父目录是 `feature_workspace_root`。
- 本 Skill 只读取和写入当前 `feature_workspace_root` 下的资产，不得默认回退到仓库根目录。
- 多个 `.input/` 同时存在且用户未指定目标时，必须暂停并要求用户选择；不得自动选择第一个目录。
- 变更分析过程产物统一写入 `feature_workspace_root/process/changes/` 或受影响阶段目录下的增量文件；不得写入 `.input/`，不得创建 `.output/`。
- `process/STATE.yaml`、`process/execution/SKILL-CALLS.yaml` 和 Gate 文件均为当前特性私有状态，不得跨目录复用。

## 前置条件

- [ ] 首次 MFQ 分析和用例设计已完成
- [ ] 交付物已生成（`delivery/` 存在）
- [ ] `delivery/<特性名>特性测试用例.md` 已由 `deliverable-renderer` 生成
- [ ] 上游 LC / PC / tool-analysis 已保留 `trace_refs / scenario_refs / action_source_refs / factor_refs / confirmation_gap_refs / fact_status`

## 必须消费的输入契约

### 1. 交付测试用例总表

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `delivery/<特性名>特性测试用例.md` | `logic_case_id`, `physical_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status`, `source_artifacts` | 用精确过滤命中变更入口，并回链到 LC / PC |

### 2. STORY-04 / STORY-08 上游资产

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `mfq/integration/logic-cases.md` | `LC-ID`, `source_tp_ids`, `关联SR`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 扩展 LC / TP / 场景链影响范围 |
| `mfq/integration/test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `trace_refs`, `confirmation_gap_refs`, `status` | 判断测试数据是否受影响 |
| `mfq/integration/tool-analysis.md` | `tool_entry_id`, `tool_id`, `tool_kind`, `scenario_refs`, `action_source_refs`, `factor_refs`, `status` | 回链已使用工具与工具缺口 |
| `ppdcs/pc/*.md` | `physical_case_id`, `logic_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status` | 确认受影响 PC 范围 |
| `ppdcs/coverage/*.md` | `requirement_gaps`, `test_point_gaps`, `trace_refs`, `fact_status` | 判断是否需要增量覆盖复核 |

> 若输入只给自然语言变更描述而没有可回链的结构化锚点，必须输出 `[待确认]`，不得发明新的检索接口或模糊匹配规则。

## 执行流程

### 步骤 1：变更需求解析

读取变更需求，优先提取**结构化锚点**：
- `requirement_ids`
- `logic_case_id`
- `feature_tags`
- 已明确给出的 `scenario_refs / action_source_refs / factor_refs / tool_id`
- 变更类型：新增 / 修改 / 删除

若只提供自由文本：
- 可以整理为待确认字段清单；
- **不得**对测试用例总表或设计文件做全文、模糊、语义或相似度检索。

### 步骤 2：影响分析

先按最终测试用例总表的既有语义命中 `delivery/<特性名>特性测试用例.md`：

1. `requirement_id`：精确命中 `requirement_ids`
2. `logic_case_id`：精确等于 `logic_case_id`
3. `feature_tags`：多标签按精确 AND 命中

命中后再沿 v6 追踪链扩展**最小必要范围**：

1. 从命中的测试用例行收集 `logic_case_id / physical_case_id`
2. 回链 `scenario_refs / action_source_refs / factor_refs / trace_refs`
3. 如命中工具条目，再关联 `tool_entry_id / tool_id`
4. 仅在同一 trace 证据闭环内扩展到相邻 LC / TD / PC / tool-analysis

输出影响矩阵：

```markdown
## 变更影响矩阵

| impact_type | requirement_ids | logic_case_refs | physical_case_refs | scenario_refs | action_source_refs | factor_refs | tool_analysis_refs | tool_gap_refs | 说明 |
|-------------|-----------------|-----------------|--------------------|---------------|--------------------|-------------|--------------------|---------------|------|
| direct | REQ-020 | LC-001 | PC-001 | SCN-001 | fw_config_log_server | FAC-001 | TOOL-001 | — | 直接命中索引与 trace |
| propagated | REQ-020 | LC-003 | — | SCN-001 | fw_config_log_server | FAC-003 | — | GAP-TOOL-001 | 同一 trace/factor 受影响 |
```

### 步骤 3：增量 MFQ 分析

仅对步骤 2 命中的范围执行增量 MFQ：

1. **增量 M 分析**：更新受影响子模块的测试点
   - 新增变更引入的新测试点
   - 修改变更改变的已有测试点
   - 标记变更删除的测试点
2. **增量 F 分析**：检查变更是否引入新的耦合关系
3. **增量 Q 分析**：检查变更是否影响质量属性

若变更只命中：
- `factor_refs` → 优先缩到相关 LC / TD / PC
- `action_source_refs` → 优先缩到同 ptm-atomic `op_id` 下的 LC / PC / tool-analysis
- `tool_gap_refs / tool_analysis_refs` → 只更新对应工具分析与受影响用例链

### 步骤 4：增量整合

1. 在受影响 LC / TD 范围内标记变更状态（新增/修改/删除）
2. 重新执行受影响逻辑用例的合并
3. 更新命中的测试数据与覆盖证据
4. 保持未命中的 LC / PC / tool-analysis 不变

### 步骤 5：增量用例设计

1. 对新增/修改的逻辑用例执行用例设计
2. 删除废弃的物理用例
3. **不修改未受影响的用例文件**

### 步骤 6：增量覆盖验证

1. 执行覆盖检查（包含变更后的需求）
2. 确保增量覆盖率 = 100%

### 步骤 7：更新交付物

1. 仅更新受影响章节的测试方案
2. 仅更新受影响模块的测试用例
3. 仅刷新受影响条目的索引与审计记录

## 不可变保护

以下内容在变更过程中**禁止修改**：
- 不受影响的模块的测试点
- 不受影响的逻辑用例
- 不受影响的物理用例
- 不受影响的设计过程文档
- 不受影响的 `delivery/<特性名>特性测试用例.md` 行
- 不受影响的工具分析条目

## 输出骨架

至少输出以下字段：

| 字段 | 说明 |
|------|------|
| `requirement_ids` | 命中的需求编号 |
| `logic_case_refs` | 受影响 LC |
| `physical_case_refs` | 受影响 PC |
| `scenario_refs` | 回链场景 |
| `action_source_refs` | 回链 ptm-atomic `op_id` |
| `factor_refs` | 回链因子 |
| `tool_analysis_refs` | 已使用工具条目 |
| `tool_gap_refs` | 工具缺口条目 |
| `trace_refs` | 原样保留 trace 链 |
| `confirmation_gap_refs` | 原样保留未确认事实 |
| `fact_status` | 原样保留确认状态 |
| `suggested_updates` | 建议重做的 MFQ / design / coverage 资产 |

## 变更审计记录

每次变更至少输出一份可审阅审计摘要：

```markdown
## 变更记录

| 变更ID | 命中锚点 | logic_case_refs | physical_case_refs | factor_refs | tool_gap_refs | confirmation_gap_refs | fact_status |
|--------|----------|-----------------|--------------------|-------------|---------------|-----------------------|-------------|
| CHG-001 | REQ-020,LC-001 | LC-001,LC-003 | PC-001 | FAC-001 | GAP-TOOL-001 | GAP-001 | needs-confirmation |
```

## Gotchas

- 必须复用最终测试用例总表的精确过滤语义，**不得**引入模糊检索、全文扫描或自定义 ranking
- `trace_refs / confirmation_gap_refs / fact_status` 只能透传或并集汇总，不能改名
- 删除功能时要同步删除对应的测试点和用例，不要留下孤儿数据
- 修改功能时要检查修改是否改变了设计方法的适用性
- 若命中的是工具缺口或工具分析条目，也必须显式输出 `tool_gap_refs / tool_analysis_refs`
- 变更后的覆盖检查需包含变更前后的需求差异，但范围只限命中资产

## 验收标准

- [ ] 基于 `delivery/<特性名>特性测试用例.md` 和 v6 trace 链输出最小影响范围
- [ ] 影响矩阵保留 `logic_case_refs / physical_case_refs / scenario_refs / action_source_refs / factor_refs`
- [ ] 命中工具分析时保留 `tool_analysis_refs / tool_gap_refs`
- [ ] 仅受影响的模块被修改
- [ ] 未受影响的用例文件未被修改
- [ ] 不引入模糊检索或新增检索接口
