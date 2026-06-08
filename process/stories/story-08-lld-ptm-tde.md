---
story_id: "STORY-08"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "delivery"
shared_fragments:
  - "case-index-model"
  - "feature-tag-model"
open_items:
  - "排序保持精确命中优先，不扩展复杂 ranking"
depends_on:
  - "STORY-06"
  - "STORY-07"
---

# STORY-08 LLD：Delivery & Retrieval — 覆盖、交付、标签检索与工具分析表

## 1. 目标

把覆盖、交付和检索闭环一次打通，形成 `coverage-report + delivery docs + tool-analysis + case-index + case-retriever`。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-018 | 双层覆盖报告 |
| REQ-019 | 交付物与标签 |
| REQ-022 | 轻量检索 |
| REQ-027 | 工具分析表 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `coverage-verifier` | 输出需求层 / 测试点层覆盖结果 |
| `deliverable-renderer` | 输出文档、case-index、标签、工具分析表 |
| `case-retriever` | 按需求 / LC / feature tags 检索 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/coverage-verifier/SKILL.md` | 双层覆盖口径升级 |
| `skills/deliverable-renderer/SKILL.md` | 交付与索引升级 |
| `skills/case-retriever/SKILL.md` | 新增技能 |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| case index | `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs` |
| coverage report | `requirement_gaps`, `test_point_gaps`, `coverage_summary` |
| tool analysis entry | `tool_entry_id`, `tool_kind`, `tool_name`, `main_usage`, `purpose`, `scenario_refs`, `action_source_refs`, `factor_refs`, `interface_contract`, `function_desc`, `io_behavior_matrix`, `output_contract`, `status` |

## 6. API / Interface 设计

- `deliverable-renderer` 输入：coverage report、PC、case-index 字段、`Existing Tool Summary`、`Tool Capability Gap`
- `deliverable-renderer` 输出：测试方案、测试用例、工具分析表、case-index
- `case-retriever` 输入：需求编号 / LC 编号 / 功能分类标签
- `case-retriever` 输出：命中用例与 trace refs

## 7. 核心处理流程

1. 生成覆盖报告；
2. 输出测试方案 / 测试用例；
3. 汇总 `Existing Tool Summary` 与 `Tool Capability Gap`；
4. 生成 `<feature>-工具分析表.md`；
5. 生成 case-index 与 feature tags；
6. 通过 `case-retriever` 检索命中。

## 8. 技术设计细节

- case-index 由 renderer 生成，retriever 只消费；
- 不扩展全文检索和复杂排序。
- 工具分析表按两部分渲染：
  - 已使用工具：工具名称、主要用法、用途、已使用场景
  - 待实现工具：API/CLI 接口、功能描述、输入输出条件下的处理逻辑、输出内容、适用场景
- 工具分析表中的每条记录都要保留 `scenario_refs / action_source_refs / factor_refs`。

## 9. 安全与性能设计

- 交付与索引都写入 `.output/`；
- 检索保持纯读，不修改交付物。
- 工具分析表只消费上游结构化结果，不允许在交付阶段脑补接口或行为。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 双层覆盖报告 | 结构检查 |
| 工具分析表字段完整 | 结构检查 |
| 已使用工具区块 | 样例检查：名称、主要用法、用途、场景是否齐全 |
| 待实现工具区块 | 样例检查：接口、功能、行为矩阵、输出说明是否齐全 |
| case-index 字段完整 | 结构检查 |
| 三类检索命中 | 样例查询 |

## 11. 实施步骤

1. 升级 coverage-verifier；
2. 在 renderer 中增加工具分析表模型；
3. 升级 renderer 输出；
4. 新增 `case-retriever`；
5. 对齐 trace refs、feature tags 和工具分析字段。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| case-index 字段不统一 | 以 shared fragment 统一字段表 |
| 检索需求膨胀 | 明确首版只做三类精确过滤 |
| 工具分析字段来源不齐 | 强制要求 renderer 只消费 STORY-03/04 产出的结构化字段 |

## 13. 回滚与发布策略

- renderer 与 retriever 可分别回滚；
- 但 case-index 或 tool-analysis 模型回滚时需同步评估两个模块。

## 14. Definition of Done

- [ ] 输出双层覆盖报告
- [ ] 交付物含 feature tags
- [ ] 输出 `<feature>-工具分析表.md`
- [ ] 工具分析表同时覆盖已使用工具与待实现工具
- [ ] `case-retriever` 支持三类结构化检索
