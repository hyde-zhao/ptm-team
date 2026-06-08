---
cr_id: "CR-003"
status: "approved"
impact_level: "high"
rollback_to: "init"
approval_result: "approved-by-user"
created_at: "2026-04-23T17:05:18+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-23T17:05:18+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户明确要求：由于开发流程已经更新，需要对 `ptm-tde` 工作流进行重新设计与更新；当前已有 Agent、Skill、脚本、文档和流程工件可以作为参考信息，但全部正式设计对象都要从头重新规划，不能沿用已有确认结论。

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUEST.md` / `process/REQUIREMENTS.md` / `process/USE-CASES.md` | true | 旧需求与场景降级为参考输入，从头重建请求基线、使用场景与结构化需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md` / `process/CLARIFICATION-LOG.md` | true | 重新开展场景澄清，不沿用此前“已确认”的场景范围与覆盖结论。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/STATE.md` / `process/STORY-BACKLOG.md` / `process/DEVELOPMENT-PLAN.yaml` | true | 回退到 `init`，重置检查点，待 HLD 确认后重新拆解 Story 和 Wave。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 权限边界 / 审计结论 / 安装与执行约束 | true | 在新流程设计中重新审视状态门控、安装边界、运行时写入边界和人工审批点。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `README.md` / `USER-MANUAL.md` / `delivery/` / 平台安装投影 | true | 旧交付物仅作参考，待新流程设计完成后按新口径重新生成。 |

## 回退决策

- 影响范围：全局
- 回退到阶段：`init`
- 需要重新确认的对象：
  - `process/REQUEST.md`
  - `process/INPUT-INDEX.md`
  - `process/USE-CASES.md`
  - `process/REQUIREMENTS.md`
  - `process/HLD.md`
  - `process/STORY-BACKLOG.md`
  - `process/DEVELOPMENT-PLAN.yaml`
  - 最终安装、验证与交付文档

## 处理结论

- 审批结论：`approved-by-user`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

说明：本 CR 属于高影响全局重设计，但用户已直接发起并批准进入重新规划。后续所有正式对象仍必须按检查点①~⑤重新确认，不得跳过人工门控。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE |  |  |
| RUN-EXEC |  |  |
| 其他文档 / 产物 | `process/STATE.md` | 已同步写回活跃变更单、回退语义与待执行动作 |
| 其他文档 / 产物 | `process/REQUEST.md` | 已重写为“从头重设计”请求基线 |
| 其他文档 / 产物 | `process/INPUT-INDEX.md` | 已刷新为本轮重设计的参考资料索引 |
