---
story_id: "STORY-04"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "application"
shared_fragments:
  - "trace-chain-v6"
open_items:
  - "LC 到 Action Source 的 trace field 命名需与 STORY-08 的 renderer 对齐"
depends_on:
  - "STORY-03"
---

# STORY-04 LLD：MFQ Trace Chain — M/F/Q/Integrator 贯通新模型

## 1. 目标

升级 M/F/Q 与 `test-point-integrator` 的输入输出，使其显式消费 `Scenario Chain / Action Source / Knowledge Reference` 并形成统一 trace。除 trace 外，本 Story 还需要完成三件事：**提取测试对象 / 测试因子**、**评估现有工具是否满足分析需求**，以及**生成可供交付阶段渲染的工具分析结构化数据**。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-009~011 | MFQ 三维与 LC 整合 |
| REQ-026~027 | 工具抽象与工具分析表的数据来源 |
| HLD §6.4 | 新追踪链 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `m-analyzer` | 从场景链产出 CAE TP，提取测试对象 / 测试因子并挂 trace |
| `f-analyzer` | 耦合点引用上游场景与动作源，并评估工具覆盖性 |
| `q-analyzer` | 质量点引用上游场景约束，并评估观测能力 |
| `test-point-integrator` | 归集 TP、测试对象、测试因子并输出 LC/测试数据 |
| tool capability assessor | 评估现有 CLI/API/工具是否能覆盖目标因子与观察点 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/m-analyzer/SKILL.md` | trace 与 TP 输出升级 |
| `skills/f-analyzer/SKILL.md` | 耦合点 trace 升级 |
| `skills/q-analyzer/SKILL.md` | 质量点 trace 升级 |
| `skills/test-point-integrator/SKILL.md` | LC/测试数据 trace 升级 |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| TP | `trace_refs`, `scenario_id`, `action_source_refs`, `test_object_refs`, `factor_refs` |
| LC | `source_tp_ids`, `scenario_refs`, `action_source_refs`, `test_object_refs`, `factor_refs` |
| Test Object | `object_id`, `object_name`, `object_type`, `observation_targets` |
| Test Factor | `factor_id`, `factor_name`, `source_section`, `data_domain`, `related_object_id` |
| Existing Tool Summary | `tool_id`, `tool_name`, `main_usage`, `purpose`, `scenario_refs`, `action_source_refs`, `covered_objects`, `covered_factors`, `status` |
| Tool Capability Gap | `tool_id`, `covered_objects`, `covered_factors`, `missing_ops`, `proposed_interface`, `function_desc`, `io_behavior_matrix`, `output_contract`, `scenario_refs` |

## 6. API / Interface 设计

### 输入

- 已确认的 `Scenario Chain`
- `Action Source`
- 用户现有工具与 API 配置

### 输出

- 所有 TP 输出都要带 `trace refs / test_object_refs / factor_refs`
- integrator 需要把 trace 和 factor 透传到 LC
- 若工具能力不足，输出 CLI/API 工具抽象建议
- 同时输出 `Existing Tool Summary` 和 `Tool Capability Gap` 供交付层渲染工具分析表

## 7. 核心处理流程

1. 读取已确认 `Scenario Chain`，包括 `precondition_operations` 和主流程原子操作；
2. 从 `C/A/E`、观察点、预期状态中提取**测试对象**；
3. 从测试对象中提取**测试因子**，例如 `IP地址 / 接口类型 / 协议类型 / 状态值`；
4. 评估现有 CLI / API / 工具是否能够：
   - 触发这些因子；
   - 观察这些对象；
   - 产生所需结果；
5. 对可直接使用的工具生成 `Existing Tool Summary`，记录主要用法、用途、场景和覆盖对象/因子；
6. 若工具不足，形成 `Tool Capability Gap` 并产出 CLI/API 抽象建议、功能说明、行为矩阵和输出契约；
7. 生成 M/F/Q TP，并挂载 `trace / object / factor / tool` 引用；
8. 聚合为 LC；
9. 输出测试数据、覆盖关系和工具分析结构化数据。

## 8. 技术设计细节

### 8.1 测试对象提取规则

- 优先从 `C（Condition）` 中提取被约束对象；
- 再从 `A（Action）` 中提取被操作对象；
- 最后从 `E（Effect）` 中提取被观察对象；
- 同一对象可在多个 TP 中复用同一 `object_id`。

### 8.2 测试因子提取规则

- 因子是构成测试对象的一组可变测试数据；
- 典型示例：
  - `IP地址`
  - `接口类型`
  - `协议类型`
  - `状态值`
  - `数量阈值`
- 每个因子必须记录来源：`precondition / condition / action-input / observation`

### 8.3 工具满足性评估

- 对每个测试对象 / 因子，评估现有工具是否可：
  - 配置；
  - 触发；
  - 观察；
  - 校验结果；
- 若工具可用，则输出 `Existing Tool Summary`；
- 若任一环节缺失，则输出工具 gap，并至少补入建议的 CLI/API 接口、功能描述、输入输出条件下的处理逻辑、输出内容和适用场景。

## 9. 安全与性能设计

- 只增加结构化字段，不引入外部写入；
- 聚合逻辑保持确定性，不增加隐式 fallback；
- 工具不满足时必须显式暴露 gap，不能假设“人工可补”。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| TP trace 完整 | 结构检查 |
| 测试对象提取 | 样例：能否从 CAE 中提取对象 |
| 测试因子提取 | 样例：能否提取 IP / 接口类型等因子 |
| 已使用工具汇总 | 样例：是否输出工具名称、主要用法、用途和场景 |
| 工具满足性评估 | 样例：现有工具不足时是否输出抽象建议 |
| LC trace 透传 | 样例对比 |
| 覆盖关系可回链 | 手工审阅 |

## 11. 实施步骤

1. 在 `m-analyzer` 中增加测试对象 / 因子提取；
2. 在 `f-analyzer` / `q-analyzer` 中增加工具覆盖评估；
3. 对齐 TP 输出骨架；
4. 对齐 LC 输出骨架；
5. 增加 trace / object / factor 透传规则；
6. 增加现有工具 summary 输出；
7. 增加工具 gap 与 CLI/API 抽象建议输出；
8. 对齐 M/F/Q 三维命名。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| trace 字段命名不一致 | 先统一字段表，再扩展到 renderer |
| 测试对象和因子边界不稳 | 先定义抽取规则，再做样例校验 |
| 工具 gap 输出不一致 | 统一 Tool Capability Gap 模型 |
| F/Q 维度引用过深 | 仅保留必要回链 |

## 13. 回滚与发布策略

- 可按 Skill 单独回滚；
- 若 integrator 透传不稳定，可先保持 TP 级 trace 不丢失。

## 14. Definition of Done

- [ ] TP 含 trace refs
- [ ] TP 含 test_object_refs / factor_refs
- [ ] 能从 CAE 中提取测试对象与测试因子
- [ ] 能输出已使用工具的主要用法 / 用途 / 场景
- [ ] 工具不足时能输出 CLI/API 抽象建议
- [ ] LC 含 trace refs
- [ ] M/F/Q/Integrator 命名一致
