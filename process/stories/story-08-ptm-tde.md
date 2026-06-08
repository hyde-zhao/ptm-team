---
story_id: "STORY-08"
title: "Delivery & Retrieval — 覆盖、交付、标签检索"
milestone: "M5"
wave: "W5"
priority: "P0"
status: "verified"
size: "L"
depends_on: ["STORY-06", "STORY-07"]
requirements: ["REQ-018", "REQ-019", "REQ-022"]
lld_file: "process/stories/story-08-lld.md"
---

# STORY-08：Delivery & Retrieval — 覆盖、交付、标签检索

## 目标

打通 `coverage-verifier`、`deliverable-renderer` 与 `case-retriever`，形成覆盖报告、交付文档和轻量检索闭环。

## 范围边界

- **包含**：覆盖报告、feature tags、case-index、检索入口
- **不包含**：变更 / 问题单增量逻辑（移交 STORY-09）

## 需求映射

- REQ-018
- REQ-019
- REQ-022

## 产出物

- `skills/coverage-verifier/SKILL.md`
- `skills/deliverable-renderer/SKILL.md`
- `skills/case-retriever/SKILL.md`

## 依赖与 Wave

- Wave：W5
- 依赖：STORY-06、STORY-07
- 后续依赖方：STORY-09

## 开发上下文

- 检索只保留三类入口：需求、LC、功能分类标签。
- renderer 需要同时产出交付物和 case-index。

## 验证上下文

- 覆盖报告必须区分需求层和测试点层。
- 检索结果必须带 trace refs。

## 量化验收标准

1. 输出双层覆盖报告和未覆盖项清单。
2. `case-index.yaml` 至少包含 requirement_ids、logic_case_id、feature_tags、trace_refs。
3. `case-retriever` 仅按三类结构化字段命中。
