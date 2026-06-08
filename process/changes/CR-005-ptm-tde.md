---
cr_id: "CR-005"
status: "approved"
impact_level: "high"
rollback_to: "requirement-clarification"
approval_result: "approved-by-user"
created_at: "2026-04-23T20:04:00+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-23T20:04:00+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户对知识库 / 安装 / 检索 / 外部动作源建模补充了四项明确约束：

- **M1**：REST API 由用户提供可配置接口；工具能力由用户提供已有测试工具和可用接口，工具需按 CLI 方式抽象；若现有工具不支持当前特性测试，`ptm-tde` 需要协助输出工具接口抽象和待实现功能描述。
- **M2**：Claude Code 与 Codex 的安装均由安装脚本统一托管，并需要纳入 **project scope / user scope** 两种安装方式；其中 user scope 需要设计 `AGENTS.md` / `CLAUDE.md` 的合并策略，如实现复杂可采用分阶段落地。
- **M3**：用例检索收敛为按**需求、逻辑用例、功能分类标签**检索，不再扩展更复杂的排序与全文检索能力。
- **M4**：知识库当前仅需**只读查询**，暂不承担知识入库、远端索引维护或写回动作。

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | `process/REQUIREMENTS.md` | true | 调整安装范围、检索范围、知识库边界，并新增“工具接口抽象”需求。 |
| 场景层 | 是否改变测试矩阵覆盖范围 | `process/USE-CASES.md` / 场景发现口径 | true | 不重写场景列表，但补强“原子操作来源”“REST API 配置”“CLI 工具抽象”的场景建模口径。 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | `process/HLD.md` / 后续 Story 规划 | true | Story 规划需改为“project scope 先落地，user scope 合并策略后补”，并移除知识入库链路。 |
| 安全层 | 是否引入新的高风险动作或权限要求 | user scope 安装 / 全局规则文件合并 / 外部知识库访问 | true | 需要明确用户级安装时禁止静默覆盖现有 `CLAUDE.md` / `AGENTS.md`，并保持知识库只读访问。 |
| 交付层 | 是否需要重新生成交付物或回归子集 | HLD / 检查点稿 / 用例索引说明 | true | 需要更新 HLD、检查点稿和状态对象，重新等待检查点②确认。 |

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

说明：该变更重定义了知识库职责边界，并对平台安装策略、检索能力边界和动作源抽象口径产生直接影响，需要回退到需求澄清后重新收敛 HLD。

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| ISSUE |  |  |
| RUN-EXEC |  |  |
| 其他文档 / 产物 | `process/REQUIREMENTS.md` | 需升级为 v5.0，纳入双 scope 安装、只读知识查询和工具抽象要求 |
| 其他文档 / 产物 | `process/HLD.md` | 需升级为 v6.0，收敛为只读 MCP 查询链并补入 user scope 合并策略 |
| 其他文档 / 产物 | `process/STATE.md` | 需写回活跃 CR 和新的等待 HLD v6 确认状态 |
