---
name: bug-gap-analyzer
description: >-
  问题单覆盖盲区分析：分析问题单在当前用例框架下是否可覆盖，
  定位设计遗漏环节，补充用例，提供流程优化建议。
  触发词包括：问题单、缺陷分析、覆盖盲区、遗漏分析。
  适用场景：MFQ 扩展分支 — 问题单反馈分析。
argument-hint: "问题单列表文件路径或内容"
user-invokable: true
status: active
---

## 目标

当用户提供问题单（缺陷报告）时：
1. 基于 `delivery/<特性名>特性测试用例.md` 与 v6 trace 链判断当前资产是否可覆盖
2. 不能覆盖时，明确区分遗漏发生在 `scenario / mfq / design / delivery`
3. 输出可回链的缺失资产与补齐建议
4. 保留原有 `trace_refs / confirmation_gap_refs / fact_status`，不改未受影响资产

## 适用范围

- 适用阶段：MFQ 扩展分支（已有用例发现了问题单后）
- 输入：问题单列表 + 已有 `kym/`, `mfq/`, `ppdcs/`, `process/checkpoints/`, `process/STATE.yaml` 基线资产
- 输出：盲区分析报告 + 补齐建议 + 流程优化建议

## 工作区隔离契约

- 以当前特性的 `.input/` 为输入锚点，`.input` 的父目录是 `feature_workspace_root`。
- 本 Skill 只读取和写入当前 `feature_workspace_root` 下的资产，不得默认回退到仓库根目录。
- 多个 `.input/` 同时存在且用户未指定目标时，必须暂停并要求用户选择；不得自动选择第一个目录。
- 问题单覆盖盲区分析过程产物统一写入 `feature_workspace_root/process/changes/`、`feature_workspace_root/process/issues/` 或受影响阶段目录下的增量文件；不得写入 `.input/`，不得创建 `.output/`。
- `process/STATE.yaml`、`process/execution/SKILL-CALLS.yaml` 和 Gate 文件均为当前特性私有状态，不得跨目录复用。

## 前置条件

- [ ] 首次 MFQ 分析和用例设计已完成
- [ ] 用户提供了问题单（缺陷描述）
- [ ] `delivery/<特性名>特性测试用例.md` 已由 `deliverable-renderer` 生成
- [ ] 上游 LC / PC / design / delivery 资产保留 trace / gap / status 字段

## 必须消费的输入契约

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `delivery/<特性名>特性测试用例.md` | `requirement_ids`, `logic_case_id`, `feature_tags`, `physical_case_id`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status`, `source_artifacts` | 仅用 `requirement_ids / logic_case_id / feature_tags` 三类入口精确命中测试用例总表；`physical_case_id` 只作为命中后的结果校验与回显字段 |
| `mfq/integration/all-test-points.md` | `TP-ID`, `关联SR`, `scenario_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 判断 MFQ 是否已有对应测试点 |
| `mfq/integration/logic-cases.md` | `LC-ID`, `source_tp_ids`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `factor_refs`, `trace_refs`, `confirmation_gap_refs`, `fact_status` | 判断 LC 是否存在 |
| `mfq/integration/test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `trace_refs`, `confirmation_gap_refs`, `status` | 判断是否缺触发数据 |
| `mfq/integration/tool-analysis.md` | `tool_entry_id`, `tool_id`, `tool_kind`, `scenario_refs`, `action_source_refs`, `factor_refs`, `status` | 判断是否已存在工具缺口证据 |
| `ppdcs/ppdcs/*.md` | `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status` | 判断设计过程是否落地 |
| `ppdcs/pc/*.md` | `physical_case_id`, `logic_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `confirmation_gap_refs`, `fact_status` | 判断最终 PC 是否存在 |
| `ppdcs/coverage/*.md` | `requirement_gaps`, `test_point_gaps`, `design_artifact_gaps`, `trace_refs`, `fact_status` | 判断缺口是否早已被覆盖报告暴露 |

> 问题单若没有 `requirement_ids / logic_case_id / feature_tags / scenario_refs / action_source_refs / factor_refs` 等结构化锚点，只能输出 `[待确认]`，不得做模糊回查。`physical_case_id` 不能作为测试用例总表的独立检索入口。

## 执行流程

### 步骤 1：问题单解析

从用户提供的问题单中提取关键信息：

| 字段 | 说明 |
|------|------|
| 问题编号 | 缺陷追踪系统编号 |
| 模块 | 问题所属模块 |
| 描述 | 缺陷详细描述 |
| 重现步骤 | 缺陷重现步骤 |
| 根因 | 根本原因（如有） |
| 严重程度 | 严重/一般/轻微 |
| 结构化锚点 | `requirement_ids / logic_case_id / feature_tags / scenario_refs / action_source_refs / factor_refs / tool_id / physical_case_id(仅作命中后校验)` |

### 步骤 2：覆盖回溯

先按最终测试用例总表的既有语义精确查询 `delivery/<特性名>特性测试用例.md`：

- `requirement_id` 精确命中 `requirement_ids`
- `logic_case_id` 精确等于 `logic_case_id`
- `feature_tags` 精确 AND
- 若问题单直接给出 `physical_case_id`，只能在上述三类入口已命中后做结果校验与回显；不得把它作为独立查询条件

命中后再沿 v6 追踪链反向查找：

```
问题单锚点 → 用 `requirement_ids / logic_case_id / feature_tags` 命中测试用例总表？
    ├── 命中索引，且回显/校验得到 PC 且 trace 能闭环 → 标记 "已覆盖但未检出"
    └── 索引未命中或缺少 PC 闭环 → 继续反向查找
        → 匹配 LC / design-process？
            ├── 找到 LC 但缺设计证据或 TD/PC → `missing_stage=design`
            └── 未找到 LC → 继续查找
                → 匹配 TP / tool-analysis？
                    ├── 找到 TP 但未转为 LC / PC → `missing_stage=mfq`
                    └── 未找到 TP → 继续查找
                        → 匹配场景链 / ptm-atomic / 因子？
                            ├── 找到场景证据但未进 MFQ → `missing_stage=mfq`
                            └── 找不到场景证据 → `missing_stage=scenario`

若 design 已完整但测试用例总表 / 交付缺项：
    → `missing_stage=delivery`
```

### 步骤 3：遗漏环节定位

输出每个问题单的遗漏分析：

```markdown
## 遗漏分析报告

| 问题编号 | coverage_status | missing_stage | missing_asset | suggested_backfill | logic_case_refs | physical_case_refs | scenario_refs | action_source_refs | factor_refs |
|---------|-----------------|---------------|---------------|--------------------|-----------------|--------------------|---------------|--------------------|-------------|
| BUG-001 | covered-but-not-detected | — | TD-001 | 补充触发数据并复核执行证据 | LC-001 | PC-001 | SCN-001 | fw_config_log_server | FAC-001 |
| BUG-002 | uncovered | scenario | SCN-GAP-001 | 补场景链并回到 MFQ | — | — | — | fw_unknown_gap_003 | FAC-003 |
| BUG-003 | uncovered | mfq | TP-F-001 | 补耦合 TP 并重新整合 LC/PC | LC-003 | — | SCN-002 | fw_unknown_gap_005 | FAC-009 |
| BUG-004 | uncovered | design | LC-007 / TD-009 | 补 design-process / TD / PC | LC-007 | — | SCN-004 | fw_unknown_gap_010 | FAC-011 |
| BUG-005 | uncovered | delivery | PC-014 | 重渲染测试用例总表 | LC-009 | PC-014 | SCN-005 | fw_unknown_gap_012 | FAC-015 |
```

### 遗漏环节分类

| 遗漏环节 | 说明 | 典型原因 |
|---------|------|---------|
| `scenario` | 场景链、ptm-atomic 或知识依据未建立 | 场景遗漏、原子操作缺失、观察点未建模 |
| `mfq` | 场景已存在，但 TP / LC / tool-analysis 未落地 | M/F/Q 分析遗漏、整合丢失、因子未进入 LC |
| `design` | LC 已存在，但设计过程 / TD / PC 不足 | 路径/状态/规则/数据覆盖不足 |
| `delivery` | 设计已落地，但交付总表未正确暴露 | renderer 漏列、测试用例总表缺项、trace 未进入交付 |

> 若需要更细说明，可在备注中补充 `mfq-detail = m / f / q / integration`，但 `missing_stage` 主分类仍保持 `scenario / mfq / design / delivery`。

### 步骤 4：用例补充

对未覆盖的问题单：

1. **回到遗漏环节**：从 `missing_stage` 对应阶段开始补充
2. **增量分析**：仅补充命中的缺失资产
3. **用例设计**：按 LC 的既有设计方法补齐，不改无关 LC
4. **交付修复**：若 `missing_stage=delivery`，只修复渲染与索引链
5. **不修改现有用例**：仅新增或局部修正，不改变不受影响的用例

### 步骤 5：流程优化建议

分析遗漏的系统性原因，提供工作流优化建议：

```markdown
## 流程优化建议

### 问题模式

| missing_stage | 频次 | 模式分析 |
|---------------|------|---------|
| scenario | 2次 | 原子操作/观察点在场景阶段未固化 |
| mfq | 3次 | TP 或整合链未完整承接场景与因子 |
| design | 2次 | 路径/状态/规则覆盖不足 |
| delivery | 1次 | renderer / 测试用例总表未暴露已存在资产 |

### 优化措施

1. **scenario 优化**：补场景链检查项
2. **mfq 优化**：补 TP→LC→TD 归并核对项
3. **design 优化**：补设计过程与触发数据完整性检查
4. **delivery 优化**：补索引字段完整性检查
```

## 不可变保护

与 `change-impact-analyzer` 相同，不修改不受影响的用例。

## 输出骨架

每个问题单至少输出以下字段：

| 字段 | 说明 |
|------|------|
| `coverage_status` | `covered-but-not-detected / uncovered / needs-confirmation` |
| `missing_stage` | `scenario / mfq / design / delivery` |
| `missing_asset` | 缺失资产编号或条目 |
| `suggested_backfill` | 从哪个阶段补齐、补什么 |
| `logic_case_refs` | 命中的 LC |
| `physical_case_refs` | 命中的 PC |
| `scenario_refs` | 场景链回链 |
| `action_source_refs` | ptm-atomic `op_id` 回链 |
| `factor_refs` | 因子回链 |
| `tool_analysis_refs` | 已使用工具条目 |
| `tool_gap_refs` | 工具缺口条目 |
| `trace_refs` | 原样保留 trace |
| `confirmation_gap_refs` | 原样保留未确认事实 |
| `fact_status` | 原样保留确认状态 |

## Gotchas

- 必须复用 STORY-08 的精确检索语义，不能对交付文档做模糊回查
- 若问题命中的是测试因子、工具 gap 或 `tool-analysis` 条目，必须回链到 `factor_refs / tool_gap_refs / tool_analysis_refs`
- `trace_refs / confirmation_gap_refs / fact_status` 只能透传或并集汇总，不能改名
- "已覆盖但未检出" 说明交付链可覆盖；此时不要误报为 `scenario / mfq / design / delivery` 缺失
- 问题单描述模糊时必须要求补充锚点，不得脑补
- 流程优化建议应该是具体可操作的，不要泛泛而谈

## 验收标准

- [ ] 每个问题单的 `coverage_status` 与 `missing_stage` 已识别
- [ ] `missing_stage` 可区分 `scenario / mfq / design / delivery`
- [ ] 可回链到 `logic_case_refs / physical_case_refs / scenario_refs / action_source_refs / factor_refs`
- [ ] 命中工具条目时保留 `tool_analysis_refs / tool_gap_refs`
- [ ] 未覆盖的问题单有具体的补齐建议
- [ ] 不受影响的用例未被修改
- [ ] 不引入模糊检索或新的检索接口
