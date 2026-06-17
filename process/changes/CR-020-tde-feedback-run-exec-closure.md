---
change_id: CR-020-tde-feedback-run-exec-closure
title: tde-feedback 现场采集自动登记 RUN-EXEC
status: closed
implementation_status: implemented
workflow_mode: fast-lane
created: 2026-06-17
approved: 2026-06-17
closed: 2026-06-17
impact_level: low
rollback_to: CR-018/CR-019 delivered evaluation baseline
related_active_change: CR-018-ptm-tde-workflow-compliance-and-workspace-isolation
source: user
owner: host-orchestrator
---

# CR-020 - tde-feedback 现场采集自动登记 RUN-EXEC

## 变更描述

用户要求将“ptm-team 需要改进的地方”形成 CR 并开始实施。根据 2026-06-17 的评估过程汇总，当前 ptm-team 最大缺口是：`tde-feedback` 已能生成 `COLLECT-*` 原始采集包并同步 GitLab，但不会自动生成 `RUN-EXEC`，导致真实使用反馈没有自动进入评估台账。

本 CR 的首个实施切片聚焦：

- `field_feedback.py collect` 成功后自动生成 `RUN-EXEC-*`。
- `field_feedback.py submit` 成功后自动生成 `RUN-EXEC-*` 并记录发布路径。
- `RUN-EXEC` 记录绑定 `COLLECT-*` 本地路径和 GitLab / feedback repo 发布路径。
- `tde-feedback` Skill、用户文档、eval 契约和测试同步更新。

## CR 冲突预检

| 项 | 结论 |
|---|---|
| 当前 active CR | `CR-018-ptm-tde-workflow-compliance-and-workspace-isolation` |
| 是否重叠 | 部分重叠，均属于 ptm-tde 质量闭环和流程合规范围 |
| 并行推进依据 | 用户在本轮明确要求“形成 CR 并开始实施”；本 CR 为低风险 fast-lane，实施对象局限于 feedback 脚本、Skill、eval、测试和文档 |
| 冲突处理 | 不修改 CR-018 的状态机和既有交付结论；CR-020 作为 CR-018 之后的质量闭环增量 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `docs/ptm-tde/USER-MANUAL.md` | 原文档更新 | 保留既有 tde-feedback 章节，追加 RUN-EXEC 自动登记说明 | 文档末尾修订记录 | approved |
| `script/README.md` | 原文档更新 | 保留既有命令说明，更新 collect/submit 输出行为 | 不适用 | approved |
| `skills/tde-feedback/SKILL.md` | 原文档更新 | 保留既有采集/上传协议，强化 RUN-EXEC 绑定要求 | 不适用 | approved |
| `evals/WORKFLOW-EVAL.yaml` | 原文档更新 | 保留既有 field-feedback grader，增加 RUN-EXEC 自动登记契约 | 不适用 | approved |
| `evals/CASE-REGISTRY.yaml` / `evals/EVAL-COVERAGE-MATRIX.md` | 原文档更新 | 保留既有 CASE-024~027，新增自动 RUN-EXEC 覆盖 | 不适用 | approved |

## 旧基线映射

| 原基线对象 | 新增 / 修改对象 | 保留策略 | 映射说明 |
|---|---|---|---|
| `COLLECT-*` 采集包 | `RUN-EXEC-*` + `collection_path` | 原行为保留并增强 | 采集包仍是原始材料；RUN-EXEC 成为评估台账入口 |
| 手工运行 `run-exec` | collect/submit 自动生成 RUN-EXEC | 原命令保留 | 维护者仍可手工补登，但默认现场采集不再停留在 COLLECT |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | ptm-tde 反馈闭环使用约定 | false | 不修改产品需求基线 |
| 场景层 | 是否改变测试矩阵覆盖范围 | 真实使用反馈场景 | true | 将反馈采集场景从“只生成 COLLECT”扩展为“COLLECT + RUN-EXEC” |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | feedback 脚本、Skill、eval | false | fast-lane 单切片实施 |
| 安全层 | 是否引入新的高风险动作或权限要求 | GitLab push / 本地文件写入 | false | 不新增权限；`--push` 授权规则保持不变 |
| 交付层 | 是否需要重新生成交付物或回归子集 | 用户手册、eval、测试 | true | 更新文档、eval case 和回归测试 |

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | true | 修改局限于脚本、Skill、eval、测试和文档 |
| 修改架构、权限、安全边界或平台安装路径 | false | 不改权限边界，不改安装路径 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | false | 不新增外部接口 |
| 需要 HLD / LLD 才能解释影响 | false | 评估反馈闭环增量，不需要新 HLD/LLD |
| 是否保持 fast-lane | true | 用户已授权开始实施 |

## 实施切片

| 切片 | 内容 | 验证 |
|---|---|---|
| P1 | `field_feedback.py` 自动生成 RUN-EXEC 并绑定 collection | `tests.test_field_feedback` |
| P2 | 更新 `tde-feedback` Skill、文档和 eval 契约 | `meta-flow eval validate/run` |
| P3 | 刷新 suite-health 和覆盖矩阵 | `meta-flow eval suite-health` |

## 评估能力分层决策

本 CR 只实施 ptm-team 侧的 `COLLECT -> RUN-EXEC` 入口闭环；以下分层原则作为后续 CR / meta-flow 平台能力的设计约束，不在 CR-020 内扩大实现。

| 决策项 | 结论 | 归属 |
|---|---|---|
| 领域实例归属 | `ptm-tde` 的具体 `CASE-REGISTRY`、BGP4+ / policy_route 样本、默认 feedback repo、领域阈值和具体 negative fixtures 保留在 ptm-team | ptm-team |
| 通用能力归属 | 通用 runner、grader 类型、schema、feedback source 抽象、mutation engine、suite-health、release-check、install-check 和 backlog 规则由 meta-flow 提供 | meta-flow |
| `runtime_artifact` 与 `runtime-eval-runner` | 必须分开；`runtime_artifact` 是 grader，输入为已产生的 workspace；`runtime-eval-runner` 负责安装、引导运行和收集 artifacts | meta-flow 提供能力，ptm-team 提供样本 |
| feedback analyze 流程 | 不得直接等同于“生成 ISSUE 并关闭循环”；必须走 `feedback source -> normalized RUN-EXEC -> triage -> ISSUE draft / GAP / backlog -> 人工或规则确认 -> regression asset` | meta-flow 定规范，ptm-team 落实例 |
| suite-health 边界 | `suite-health` 只表示评估套件健康，不承载全部发布逻辑 | meta-flow |
| release 判定 | 新增独立 `meta-flow eval release-check --eval evals/WORKFLOW-EVAL.yaml --runs process/evals/runs --profile release`，负责发布阈值、blocking case、ISSUE、runtime sample 和 regression asset 判定 | meta-flow |

## 后续事项台账

| 候选编号 | 标题 | 状态 | 类型 | 优先级 | 正式 CR 路径 | 当前门控 | 下一步 |
|---|---|---|---|---:|---|---|---|
| CR-021-candidate | ptm-team runtime sample manifest 与 BGP4+ / policy_route 样本绑定 | candidate | CR | 1 |  | 未启动 | 在 ptm-team 内固化领域样本，不实现通用 grader |
| CR-MF-EVAL-001-candidate | meta-flow `runtime_artifact` grader | candidate | meta-flow CR | 1 |  | 未启动 | 在 meta-flow 项目实现，输入为已产生 workspace |
| CR-MF-EVAL-002-candidate | meta-flow `runtime-eval-runner` Skill / 命令 | candidate | meta-flow CR | 1 |  | 未启动 | 与 `runtime_artifact` 解耦，负责安装、运行引导和 artifacts 收集 |
| CR-MF-EVAL-003-candidate | meta-flow feedback source 到 normalized RUN-EXEC / triage 管线 | candidate | meta-flow CR | 1 |  | 未启动 | 明确 triage 与人工 / 规则确认边界，避免噪声反馈直接变 blocking regression |
| CR-MF-EVAL-004-candidate | meta-flow `eval release-check` | candidate | meta-flow CR | 1 |  | 未启动 | 独立于 suite-health，按 release profile 执行发布判定 |
| CR-MF-EVAL-005-candidate | meta-flow mutation engine、install-check 和 eval backlog 规则 | candidate | meta-flow CR | 2 |  | 未启动 | 分阶段补充通用平台能力 |
| CR-022-candidate | ptm-team FIELD-QUALITY-DASHBOARD 领域指标增强 | candidate | CR | 2 |  | 未启动 | 在 RUN-EXEC/ISSUE 样本增多后实施，消费 meta-flow 通用指标能力 |
| CR-023-candidate | ptm-team ISSUE/GAP/regression_asset 领域分流规则 | candidate | CR | 2 |  | 未启动 | 基于真实失败样本推进，不直接替代 meta-flow triage 规范 |

## 验收标准

- [x] `collect` 后生成 `COLLECT-*` 和 `RUN-EXEC-*`。
- [x] `submit` 后生成 `COLLECT-*`、`RUN-EXEC-*`，并在 RUN-EXEC 中记录发布路径。
- [x] `RUN-EXEC-INDEX.md` 自动登记运行。
- [x] `tde-feedback` Skill 明确“采集即登记 RUN-EXEC”。
- [x] eval 覆盖该契约。
- [x] 单元测试和 meta-flow eval 均通过。

## 实施结果

| 对象 | 结果 |
|---|---|
| `script/field_feedback.py` | `collect` / `submit` 自动调用 RUN-EXEC 登记逻辑；RUN-EXEC 写入 `collection_path` / `published_path`；`MANIFEST.json` 回写 `run_exec_id` / `run_exec_path` |
| `skills/tde-feedback/SKILL.md` | 明确 `collect` / `submit` 的 RUN-EXEC 自动登记和完成报告要求 |
| `agents/ptm-tde.md` | 反馈闭环协议增加 RUN-EXEC 绑定要求 |
| `docs/ptm-tde/USER-MANUAL.md` / `script/README.md` | 更新用户侧和维护侧说明 |
| `evals/WORKFLOW-EVAL.yaml` | 新增 `field-feedback-run-exec-contract` grader |
| `evals/CASE-REGISTRY.yaml` | 新增 `CASE-028` |
| `evals/EVAL-COVERAGE-MATRIX.md` | field-feedback 覆盖扩展到 4 个 case / 总计 28 case |

## 验证结果

| 命令 | 结果 |
|---|---|
| `uv run python -m unittest tests.test_cr018_p2 tests.test_field_feedback tests.test_install_mapping` | PASS，23 tests |
| `uv run python /home/hyde/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/tde-feedback` | PASS |
| `meta-flow eval validate --eval evals/WORKFLOW-EVAL.yaml` | PASS |
| `meta-flow eval run --eval evals/WORKFLOW-EVAL.yaml --out process/evals/runs/ptm-tde` | PASS，`eval-20260617T090924Z` |
| `meta-flow eval suite-health --runs process/evals/runs --out docs/quality/EVAL-SUITE-HEALTH.md` | PASS |
| `meta-flow check cr-tracking --project-root . --allow-multiple-active` | PASS，CR-018 / CR-020 并行状态已显式授权 |

## 收敛状态

本 CR 的首个实施切片已完成。用户于 2026-06-17 确认关闭；后续 runtime、feedback analyze、release-check、mutation、install-check、dashboard 和 ISSUE/GAP 分流按“ptm-team 领域实例 / meta-flow 通用能力”分层推进。
