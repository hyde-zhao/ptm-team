---
story_id: "STORY-09"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "adaptation"
shared_fragments:
  - "trace-chain-v6"
  - "knowledge-reference-model"
open_items:
  - "最小回归集的命中细则在实现时补充到验证方案"
depends_on:
  - "STORY-04"
  - "STORY-08"
---

# STORY-09 LLD：Feedback Adaptation — 变更影响与问题单适配新模型

## 1. 目标

升级 `change-impact-analyzer` 与 `bug-gap-analyzer`，让它们基于 v6 追踪链做增量识别与盲区定位。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-020 | 变更影响增量更新 |
| REQ-021 | 问题单盲区分析 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `change-impact-analyzer` | 命中受影响场景链、LC、PC、索引 |
| `bug-gap-analyzer` | 定位遗漏环节并输出补齐建议 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/change-impact-analyzer/SKILL.md` | 消费新 trace 模型 |
| `skills/bug-gap-analyzer/SKILL.md` | 消费新 trace 与 case-index |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| impact scope | `scenario_refs`, `action_source_refs`, `logic_case_refs`, `physical_case_refs`, `factor_refs`, `tool_gap_refs`, `tool_analysis_refs` |
| gap finding | `missing_stage`, `missing_asset`, `suggested_backfill` |

## 6. API / Interface 设计

- 输入：CR / 问题单 / case-index / trace refs
- 输出：影响范围或盲区报告

## 7. 核心处理流程

1. 读取新 trace 与 case-index；
2. 命中场景链与动作源；
3. 识别受影响 LC / PC；
4. 输出增量路径或补齐建议。

## 8. 技术设计细节

- 影响分析坚持最小影响范围；
- 问题单分析要区分场景遗漏、MFQ 遗漏、设计遗漏、交付遗漏；
- 若问题或变更命中的是测试因子、工具 gap 或工具分析表条目，也必须能回链到对应 `factor_refs / tool_gap_refs / tool_analysis_refs`。

## 9. 安全与性能设计

- 不改动未受影响资产；
- 对信息不完整输入显式标记待确认。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 受影响范围命中 | 样例 CR 评审 |
| 盲区阶段定位 | 样例问题单评审 |
| 未受影响资产不变 | 差异检查 |

## 11. 实施步骤

1. 升级 impact analyzer 的输入输出；
2. 升级 bug gap analyzer 的定位骨架；
3. 对齐 trace refs、case-index 字段和 tool-analysis 引用字段。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 变更描述不足 | 显式输出待确认范围 |
| 问题单证据不全 | 先定位可能遗漏环节，再要求补充 |

## 13. 回滚与发布策略

- 两个 Skill 可独立回滚；
- 若 trace 命名尚未稳定，先保持兼容旧字段读取。

## 14. Definition of Done

- [ ] 影响分析输出最小受影响范围
- [ ] 问题单分析输出遗漏环节与补齐建议
- [ ] 两个 Skill 可消费 case-index 与新 trace
