---
cr_id: "CR-006"
status: "approved"
impact_level: "high"
rollback_to: "solution-design"
approval_result: "approved-by-user"
created_at: "2026-04-24T09:47:01+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-24T09:47:01+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户新增正式交付要求：在最终交付件中，除测试方案、测试用例和检索索引外，还必须提供**工具分析表**。

该工具分析表需要覆盖两类对象：

- **已使用工具 / 动作源**：给出工具名称、主要用法、用途、关联场景或逻辑链位置。
- **待实现工具 / 工具抽象**：给出接口形式（API 或 CLI）、功能描述、不同输入/输出条件下的处理逻辑、输出内容，以及已使用场景或目标适用场景。

该要求不是单纯补交付文案，而是要求把“已有工具”和“待实现工具”分别建模为可追踪、可评审、可渲染的正式设计对象。

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` | true | 升级 `REQ-026` 的工具抽象细度，并新增“工具分析表交付”需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/HLD.md` / `story-03-lld.md` / `story-04-lld.md` | true | 在动作源、工具能力评估和工具抽象输出中补入“主要用法 / 用途 / 场景引用 / 接口与行为说明”字段。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/STORY-BACKLOG.md` / `process/DEVELOPMENT-PLAN.yaml` | false | Story/Wave 边界不变；本次仅收敛既有 Story 的设计对象与交付模型。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 安全边界 / 审计结论 | false | 本次只新增设计与交付说明，不新增执行权限，也不扩大外部调用边界。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | `process/HLD.md` / `checkpoints/CHECKPOINT-HLD.md` / `story-08-lld.md` | true | 交付层需新增“工具分析表”正式产物，并要求 renderer 消费动作源和工具 gap 结构化数据。 |

## 回退决策

- 影响范围：局部（需求 + HLD + 相关 LLD + 交付模型）
- 回退到阶段：`solution-design`
- 需要重新确认的对象：
  - `process/HLD.md`
  - `checkpoints/CHECKPOINT-HLD.md`
  - 受影响的 `story-03-lld.md`、`story-04-lld.md`、`story-08-lld.md`、`story-09-lld.md`

## 处理结论

- 审批结论：`approved-by-user`
- [ ] 自动批准（低风险）
- [ ] 待人工确认（中风险）
- [x] 待人工审批（高风险）

说明：该变更新增正式交付物，并要求把动作源、工具满足性评估和工具抽象升级为可渲染的正式对象，因此需要回退到 `solution-design` 更新 HLD，再冻结等待检查点②确认。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE |  |  |
| RUN-EXEC |  |  |
| 其他文档 / 产物 | `process/REQUIREMENTS.md` | 需升级为 v6.0，补入工具分析表需求，并细化工具抽象验收口径 |
| 其他文档 / 产物 | `process/HLD.md` | 需升级为 v7.0，补入工具分析模型和交付路径 |
| 其他文档 / 产物 | `process/stories/story-03-lld.md` | 需补入已有工具 usage seed 与工具抽象字段 |
| 其他文档 / 产物 | `process/stories/story-04-lld.md` | 需补入工具分析结构化数据与行为矩阵来源 |
| 其他文档 / 产物 | `process/stories/story-08-lld.md` | 需补入工具分析表渲染逻辑 |
| 其他文档 / 产物 | `process/STATE.md` | 需写回活跃 CR、阶段回退和待确认对象 |
