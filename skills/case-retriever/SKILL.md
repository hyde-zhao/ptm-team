---
name: case-retriever
description: >-
  用例检索：基于最终测试用例总表中的结构化追踪字段执行精确检索，
  支持需求编号、逻辑用例编号、功能分类标签三类入口。
  触发词包括：检索用例、按需求查用例、按LC查用例、按标签查用例。
  适用场景：delivery 后的轻量追溯与回查。
argument-hint: "requirement_id=<REQ> | logic_case_id=<LC> | feature_tags=<tag1,tag2>"
user-invokable: true
status: active
---

## 目标

读取 `delivery/<特性名>特性测试用例.md` 中的结构化用例总表，提供精确过滤检索：

1. 按 `requirement_id` 检索；
2. 按 `logic_case_id` 检索；
3. 按 `feature_tags` 检索。

不生成、不依赖 `case-index.yaml`。

## 输入

| 输入 | 路径 |
|---|---|
| 测试用例总表 | `delivery/<特性名>特性测试用例.md` |

## 查询规则

| 参数 | 匹配规则 |
|---|---|
| `requirement_id` | 精确命中用例行的 `requirement_ids` |
| `logic_case_id` | 精确等于用例行的 `logic_case_id` |
| `feature_tags` | 精确命中标签值；多标签默认 AND |

不支持全文检索、模糊匹配、语义扩展或排序打分。

## 返回字段

每条命中结果至少返回：

- `logic_case_id`
- `physical_case_id`
- `requirement_ids`
- `feature_tags`
- `trace_refs`
- `scenario_refs`
- `action_source_refs`
- `factor_refs`
- `confirmation_gap_refs`
- `fact_status`

## Gotchas

- 只能读取测试用例总表中的结构化字段，不得从自然语言段落中猜测。
- 若最终测试用例缺少必要追踪列，应返回“交付字段缺口”，而不是回退到模糊搜索。
- `fact_status=needs-confirmation` 的结果仍可返回，但必须显式展示。

## 验收标准

- [ ] 仅支持 `requirement_id / logic_case_id / feature_tags` 三类入口
- [ ] 检索为精确过滤，不做 ranking
- [ ] 不依赖 `case-index.yaml`
