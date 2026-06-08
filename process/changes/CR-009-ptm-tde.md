---
cr_id: "CR-009"
status: "closed"
impact_level: "medium"
rollback_to: "delivered"
approval_result: "user-requested"
created_at: "2026-05-19T10:26:08+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-05-19T10:26:08+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户要求按 ptm-tde 作为 ptm-team 组件的定位重构运行产物、检查点、交付物和组件文档口径：

- 一个特性一个项目，运行产物直接在特性项目根目录生成，不再使用 `.output/`。
- 推荐运行目录结构改为 `input/`、`analysis/`、`design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/STATE.yaml`。
- `input` 自检 CP01 增强，覆盖需求文件、全局 `atomic-ops`、wiki 兜底、特性名推断、防火墙 topo 与耦合矩阵。
- PPDCS 设计和 PC 设计均按每个逻辑用例单文件输出，文件名为 `<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`，不再使用深目录。
- `delivery/` 只保留 `<特性名>特性测试方案.md` 与 `<特性名>特性测试用例.md` 两个最终交付文件。
- ptm-tde 只维护 Agent 与 Skill 调用关系，不处理安装器和安装清单。
- checkpoint 脚本归属到 `skills/checkpoint-manager/scripts/run_checkpoint.py`，不放仓库根 `scripts/`。
- 组件级手册归档到 `docs/component-manual.md`、`docs/runtime-artifacts.md`、`docs/checkpoint-spec.md`；ptm-team 负责统一安装和总手册。

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `agents/ptm-tde.md` | 原文档更新 | 旧 `.input/.output` 与安装口径由本 CR 摘录并替换 | 不适用 | approved |
| `skills/*/SKILL.md` | 原文档更新 | 旧路径口径由本 CR 摘录并替换；设计与交付契约按新目录增量修正 | 不适用 | approved |
| `skills/checkpoint-manager/SKILL.md` | 新增 | 新增组件级 checkpoint skill | 不适用 | approved |
| `skills/design-ppdcs-analyzer/SKILL.md` | 新增 | 新增 PPDCS/PC 单文件设计协调 skill | 不适用 | approved |
| `README.md` | 原文档更新 | 旧安装说明不删除历史实现，仅当前组件 README 不再指导安装 | 不适用 | approved |
| `delivery/README.md` | 原文档更新 | 旧安装手册口径由 ptm-team 后续接管 | 不适用 | approved |
| `delivery/USER-MANUAL.md` | 原文档更新 | 旧安装手册口径由 ptm-team 后续接管 | 不适用 | approved |
| `docs/*.md` | 新增 | 新增组件级手册归档 | 不适用 | approved |
| `scripts/install.py` / `doc/INSTALL-MANIFEST.yaml` | 不变 | 用户明确要求不处理安装器或安装清单 | 不适用 | approved |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论（true/false） | 处理动作 |
|------|----------|-----------|--------------------|---------|
| 需求层 | 是否新增、删除或重定义运行需求 | Agent/Skill 契约 | true | 更新运行目录、输入自检、交付文件数量、组件职责边界 |
| 场景层 | 是否改变测试矩阵覆盖范围 | input/scenario/F 分析前置 | true | 增加 CP01 对需求文件、topo、耦合矩阵和 wiki 兜底的检查 |
| 计划层 | 是否改变 Phase、Wave、任务依赖 | ptm-tde 10 步主流程 | true | 保持主流程，新增 checkpoint-manager 与 design-ppdcs-analyzer 调用点 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 安装与写入边界 | false | 移除 ptm-tde 安装职责；`input/` 只读，产物写项目根规范目录 |
| 交付层 | 是否需要重新生成交付物或回归子集 | README、delivery 文档、docs 手册、Skill 文件 | true | 刷新组件文档与交付口径；最终交付仅两份 Markdown |

## 回退决策

- 影响范围：中等，主要影响运行目录契约、Skill 调用关系和文档。
- 回退到阶段：`delivered` 后变更，不重开全量 Story。
- 需要重新确认的对象：本 CR 涉及的 Agent/Skill/README/docs 文档更新。

## LLD 设计批次门禁

- 是否需要 LLD 设计批次：false
- batch_id：`CR-009-LLD-BATCH`
- 批次范围来源：不适用，本次为已交付组件的 prompt/文档契约最小改造，不改安装器、不改核心 Python 安装脚本。
- 批次内 Story：无
- 开发启动条件：不适用

## 执行链路

| 顺序 | 责任角色 | 动作 | 输入 | 输出 | 门控 | 完成后下一步 |
|---|---|---|---|---|---|---|
| 1 | `meta-po` | 创建 CR 并状态化调度限制 | 用户请求、STATE | 本 CR、STATE lifecycle | CR 已登记 | 继续检查仓库事实 |
| 2 | `meta-pm` | 复核需求/场景口径 | 用户约束、README、Agent/Skill | 需求影响结论 | 子 agent 调度工具不可用，本轮记录 unavailable | meta-po inline fallback 吸收 |
| 3 | `meta-se` | 复核目录与流程架构 | Agent/Skill 契约 | 运行目录与调用关系结论 | 子 agent 调度工具不可用，本轮记录 unavailable | meta-po inline fallback 吸收 |
| 4 | `meta-dev` | 修改 Agent/Skill/脚本归属文件 | CR、仓库文件 | 文件修改 | 子 agent 调度工具不可用，本轮记录 unavailable | meta-po inline fallback 吸收 |
| 5 | `meta-doc` | 刷新 README、delivery 文档和 docs 手册 | CR、修改结果 | 文档更新 | 子 agent 调度工具不可用，本轮记录 unavailable | meta-po inline fallback 吸收 |
| 6 | `meta-po` | 汇总验证与风险 | git diff、grep、可运行命令 | 最终说明 | 不执行安装器/安装清单修改 | 返回用户 |

## 子 Agent 调度证据

当前 Codex 工具面未提供 `spawn_agent`、`resume_agent` 或 `send_input`。因此本 CR 所需 `meta-pm`、`meta-se`、`meta-dev`、`meta-doc` 均登记为 `unavailable`，不能声称真实子 agent 已完成。实际修改由本 meta-po 线程在自身上下文内以 inline fallback 完成，最终报告按“组织视角/实际执行限制”如实说明。

## 自动终验授权

- 是否启用：false
- 授权范围：不适用
- 适用检查点：不适用
- 自动通过条件：不适用
- 授权原文：
- 授权时间：
- 回填要求：不适用

## 处理结论

- 审批结论：`user-requested`
- [x] 自动批准（用户同轮明确要求实施）
- [ ] 待人工确认（中风险）
- [ ] 待人工审批（高风险）

## 关联对象

| 类型 | 标识 | 说明 |
|---|---|---|
| STATE | `process/STATE.md` | 登记 CR-009 与 agent lifecycle 调度受限 |
| 组件文档 | `docs/component-manual.md`、`docs/runtime-artifacts.md`、`docs/checkpoint-spec.md` | 新增组件级手册 |
| Skill | `skills/checkpoint-manager/`、`skills/design-ppdcs-analyzer/` | 新增组件级运行检查和设计协调 |
