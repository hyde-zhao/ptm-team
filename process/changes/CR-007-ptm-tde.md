---
cr_id: "CR-007"
status: "approved"
impact_level: "medium"
rollback_to: "solution-design"
approval_result: "approved-by-user"
created_at: "2026-04-24T10:11:30+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-24T10:11:30+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户指出 meta-flow 已更新，要求同步三项规范：

1. 检查并更新 `process/REQUEST.md` 的文档格式；
2. 检查并更新 `process/USE-CASES.md` 的文档格式；
3. 检查 Story 文档的命名/命令规范，并统一修改 Story 文件名。

本次变更的重点不是重写业务边界，而是把上游治理文档和 Story 文件命名统一到新的格式约定，避免后续引用、命令和自动化处理继续依赖旧命名。

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` | false | 不调整需求内容，仅同步 REQUEST / USE-CASES 格式。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/REQUEST.md` / `process/USE-CASES.md` | true | 对齐 frontmatter、上下文字段和平台口径，但不改变已确认场景边界。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/stories/*` / `process/STORY-STATUS.md` / `process/STORY-BACKLOG.md` | true | Story/Wave 不变，但 Story 文档文件名改为 kebab-case，并同步更新全部引用路径。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 安全边界 / 审计结论 | false | 本次仅调整文档格式与文件命名，不新增权限或执行动作。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | Story 引用路径 / 过程文档 | false | 不新增交付物类型，仅修正治理文档与 Story 路径引用。 |

## 回退决策

- 影响范围：局部（治理文档格式 + Story 文件命名）
- 回退到阶段：`solution-design`
- 需要重新确认的对象：
  - `process/REQUEST.md`
  - `process/USE-CASES.md`
  - `process/stories/story-*.md`
  - `process/stories/story-*-lld.md`

## 处理结论

- 审批结论：`approved-by-user`
- [ ] 自动批准（低风险）
- [x] 待人工确认（中风险）
- [ ] 待人工审批（高风险）

说明：本次变更不会重开需求与 HLD 内容边界，但会调整上游治理文档格式和 Story 文件命名，因此需要同步更新状态对象和路径引用，避免后续命令与引用失效。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE |  |  |
| RUN-EXEC |  |  |
| 其他文档 / 产物 | `process/REQUEST.md` | 需同步到新的 meta-flow 文档格式 |
| 其他文档 / 产物 | `process/USE-CASES.md` | 需同步到新的 meta-flow 文档格式，并收缩平台口径 |
| 其他文档 / 产物 | `process/stories/*` | 需统一改为 kebab-case 文件名 |
| 其他文档 / 产物 | `process/STATE.md` | 需写回活跃 CR 和格式同步状态 |
