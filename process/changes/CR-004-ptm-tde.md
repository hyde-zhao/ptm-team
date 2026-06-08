---
cr_id: "CR-004"
status: "approved"
impact_level: "high"
rollback_to: "requirement-clarification"
approval_result: "approved-by-user"
created_at: "2026-04-23T19:01:08+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-23T19:01:08+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户新增要求：`ptm-tde` 需要支持**知识入库和索引维护**，并与当前已搭建的知识库联合实现 MCP 开发。设计中需要明确：

- 如何把防火墙主应用场景、特性应用场景、特性主功能等知识纳入知识库；
- 如何通过 MCP 分阶段查询这些知识，并把结果作为 `scenario-discovery`、特性分析和测试设计的参考；
- 如何维护知识索引与同步机制。

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` | true | 新增知识入库、索引维护、分阶段知识查询与 MCP 联合开发相关需求；移除“知识入库和索引维护”为排除项。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md` / 场景发现口径 | true | 不改用户场景列表，但补充场景发现的知识源与参考路径设计。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/HLD.md` / 后续 Story 规划 | true | Story 规划需新增知识索引、MCP 联调和场景查询链路相关 Story。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | MCP 边界 / 索引同步 / 写入权限 | true | 需要明确知识入库写入边界、索引同步权限和知识源可信度。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | HLD / 检查点稿 / 检索索引文档 | true | 需要更新 HLD、检查点稿，并在交付设计中纳入知识索引产物。 |

## 回退决策

- 影响范围：局部（需求 + HLD + 后续规划）
- 回退到阶段：`requirement-clarification`
- 需要重新确认的对象：
  - `process/REQUIREMENTS.md`
  - `process/HLD.md`
  - `checkpoints/CHECKPOINT-HLD.md`

## 处理结论

- 审批结论：`approved-by-user`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

说明：该变更直接改变知识源治理和 MCP 职责边界，属于设计层高影响变更。用户已直接发起并批准进入补充设计。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE |  |  |
| RUN-EXEC |  |  |
| 其他文档 / 产物 | `process/REQUIREMENTS.md` | 已升级需求，加入知识入库、索引维护和分阶段知识查询能力 |
| 其他文档 / 产物 | `process/HLD.md` | 已补充知识库增强版 HLD 设计 |
| 其他文档 / 产物 | `process/STATE.md` | 已写回活跃 CR 与当前等待 HLD 重新确认的状态 |
