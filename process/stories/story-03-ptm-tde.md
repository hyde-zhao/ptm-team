---
story_id: "STORY-03"
title: "Scenario Foundation — 场景链 / 动作源 / 只读 MCP"
milestone: "M1"
wave: "W1"
priority: "P0"
status: "verified"
size: "L"
depends_on: []
requirements: ["REQ-005", "REQ-006", "REQ-007", "REQ-023", "REQ-024", "REQ-025", "REQ-026"]
lld_file: "process/stories/story-03-lld.md"
---

# STORY-03：Scenario Foundation — 场景链 / 动作源 / 只读 MCP

## 目标

让 `scenario-discovery` 能输出 **最小逻辑链 + 原子操作 + 观察点 + Action Source + 只读知识引用 + 工具抽象草案**。

## 范围边界

- **包含**：`scenario-discovery`、`mcp_query_client.py`、场景模板、动作源缺口表达、工具抽象输出
- **不包含**：M/F/Q/Integrator 对下游 trace 的消费（移交 STORY-04）

## 需求映射

- REQ-005~007
- REQ-023~026

## 产出物

- `skills/scenario-discovery/SKILL.md`
- `scripts/mcp_query_client.py`
- `agents/ptm-tde.md`

## 依赖与 Wave

- Wave：W1
- 依赖：无
- 后续依赖方：STORY-04

## 开发上下文

- 用户会提供 REST API 配置、CLI 工具说明或已有工具能力边界。
- 知识查询只读，不做入库和远端索引维护。

## 验证上下文

- 场景模板必须能直接支撑逻辑用例步骤写作。
- 当 API / 工具契约不足时，必须显式提示并输出工具抽象草案。

## 量化验收标准

1. 场景链包含目标、前置、原子操作、观察点、最小逻辑链、数据叠加位。
2. Action Source 能区分 `rest-api / cli-tool / tool-method`。
3. 知识查询返回成功 / 缺失 / 不可用三态。
