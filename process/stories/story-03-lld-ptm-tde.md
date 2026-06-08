---
story_id: "STORY-03"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "application"
shared_fragments:
  - "scenario-chain-model"
  - "action-source-model"
  - "knowledge-reference-model"
open_items:
  - "CLI tool descriptor 示例需在实现时从 skill tree examples 补齐"
depends_on: []
---

# STORY-03 LLD：Scenario Foundation — 场景链 / 动作源 / 只读 MCP

## 1. 目标

重构 `scenario-discovery` 和 `mcp_query_client.py`，让场景阶段形成正式的 Scenario Chain、Action Source、Knowledge Reference、Existing Tool Usage Seed 和 Tool Abstraction 输出。该 Story 的首要原则是：**场景分析必须准确正确；无法确认的信息必须向用户询问，而不是猜测。**

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-005~007 | 场景链与原子操作 |
| REQ-023~025 | 只读知识查询 |
| REQ-026 | 工具抽象 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `scenario-discovery` | 生成场景链、前置条件链、原子操作、动作源缺口 |
| `mcp_query_client.py` | 只读 staged query，返回三态 |
| prompt / template 区块 | 组织用户补充与确认 |
| precondition extractor | 从场景目标倒推出使用该功能的先决条件，并拆成原子操作 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/scenario-discovery/SKILL.md` | 主体重写 |
| `scripts/mcp_query_client.py` | 查询契约升级 |
| `agents/ptm-tde.md` | 场景确认提示更新 |

## 5. 数据模型与持久化设计

| 模型 | 关键字段 |
|---|---|
| Scenario Chain | `scenario_goal / principle / preconditions / precondition_operations / atomic_operations / observation_points / minimal_logic_chain / data_overlay_slots` |
| Action Source | `source_type / config_ref / invoke_contract / observe_contract / main_usage / purpose / scenario_refs / capability_status` |
| Knowledge Reference | `knowledge_type / source_ref / queried_at / availability_status` |
| Tool Abstraction Draft | `tool_name / target_interface / function_desc / io_behavior_matrix / output_contract / scenario_refs` |
| Confirmation Gap | `gap_type / gap_field / question_text / candidate_draft / user_answer` |

## 6. API / Interface 设计

| 接口 | 输入 | 输出 |
|---|---|---|
| `scenario-discovery` | 目录、参考资料、API/工具配置、MCP 结果、用户补充事实 | 场景链稿、前置条件链、现有工具 usage seed、工具抽象草案、待确认字段 |
| `mcp_query_client` | 领域/特性/功能查询 | `resolved / missing / unavailable` |

## 7. 核心处理流程

1. 装载目录与输入材料；
2. 执行只读 staged query，形成领域/特性/功能知识参考；
3. 先确定**场景目标**与**原理依据**；
4. 倒推出用户要执行该场景的**先决条件**；
5. 把先决条件拆成 `precondition_operations`（这些步骤后续可直接作为用例预置条件来源）；
6. 再拆解主流程的 `atomic_operations`、`observation_points` 与 `expected_state`；
7. 挂载 API / CLI / tool-method 到 Action Source；
8. 对已可直接使用的工具补入 `main_usage / purpose / scenario_refs`；
9. 若任何场景、前置条件、动作源或观察点不确定，生成待确认问题并向用户询问；
10. 若现有工具能力不足，输出带 `target_interface / function_desc / io_behavior_matrix / output_contract / scenario_refs` 的工具抽象草案；
11. 生成待确认场景模板并等待用户确认。

## 8. 技术设计细节

### 8.1 场景分析准确性规则

- 不允许基于模糊材料直接脑补场景。
- 当以下任一信息缺失时，必须向用户确认：
  - 场景目标不清楚；
  - 前置条件不清楚；
  - 原子操作顺序不清楚；
  - 观察点或预期状态不清楚；
  - API / CLI / 工具能力描述不清楚。

### 8.2 前置条件建模规则

- 每个场景都必须输出 `preconditions`。
- 每条 `precondition` 都要进一步拆分为 `precondition_operations`。
- `precondition_operations` 与主流程原子操作一样，必须带：
  - 操作通道
  - 操作对象
  - 输入参数
  - 观察点
  - 预期状态

### 8.3 动作源与知识引用

- API / CLI / tool-method 统一进入 Action Source；
- 缺知识与接口异常必须显式区分；
- 已可使用工具需记录主要用法、用途和场景引用；
- 工具能力不足时，先输出抽象草案，再等待用户确认。

## 9. 安全与性能设计

- 对外知识库访问只读；
- 用户补充内容只写 `.output/` 产物，不回写原始输入；
- 对不确定场景强制停在确认前，不允许生成“看似完整”的错误场景链。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 场景链字段完整性 | 检查 `preconditions` 与 `precondition_operations` 是否存在 |
| 不确定信息提问机制 | 样例评审：缺失信息时是否进入用户确认 |
| API / CLI 动作源识别 | 样例评审 |
| MCP 三态返回 | 契约测试 |

## 11. 实施步骤

1. 重写 Scenario Chain 输出，加入 `principle / preconditions / precondition_operations`；
2. 在场景分析流程中加入“缺信息即提问”的分支；
3. 增加 Action Source 字段；
4. 改造 MCP 查询返回结构；
5. 增加现有工具 usage seed 输出；
6. 增加工具抽象输出；
7. 更新确认提示与落盘格式。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 前置条件来源不充分 | 先输出候选前置条件，再向用户确认 |
| 用户提供的工具描述过粗 | 输出缺口字段和抽象草案 |
| staged query 结果不足 | 使用 `missing / unavailable` 区分并回到人工补充 |

## 13. 回滚与发布策略

- 回滚范围为 `scenario-discovery` 与 `mcp_query_client.py`；
- 若查询契约不稳定，先保留只读兜底文本结果。

## 14. Definition of Done

- [ ] 场景链字段完整
- [ ] 每个场景都有 `preconditions` 和 `precondition_operations`
- [ ] 不确定信息会触发用户确认
- [ ] Action Source 三类来源可表达
- [ ] MCP 返回三态
- [ ] 可输出现有工具的主要用法 / 用途 / 场景引用
- [ ] 工具抽象草案可输出
