---
change_id: CR-022-meta-flow-runtime-eval-consumption
title: ptm-team 消费 meta-flow runtime / release / feedback eval 能力
status: closed
implementation_status: implemented
workflow_mode: fast-lane
created: 2026-06-17
approved: 2026-06-17
closed: 2026-06-17
impact_level: low
rollback_to: CR-021 runtime sample registry baseline
related_active_change: CR-021-runtime-sample-manifest
source: user
owner: host-orchestrator
---

# CR-022 - ptm-team 消费 meta-flow runtime / release / feedback eval 能力

## 变更描述

用户明确要求默认 meta-flow 已完成通用能力，继续推进 ptm-team 的整改。CR-020 已把现场反馈采集接入 `RUN-EXEC`，CR-021 已登记 BGP4+ / policy_route 真实 runtime 样本。本 CR 将 ptm-team 侧从“样本已登记”推进到“可被 meta-flow 通用 eval 能力直接消费”。

实施范围：

- 在 `evals/WORKFLOW-EVAL.yaml` 中接入 `runtime_artifact` grader，消费 BGP4+ partial 样本和 policy_route full 样本。
- 在 `evals/WORKFLOW-EVAL.yaml` 中声明 `feedback_sources`，供 `meta-flow eval feedback pull/analyze` 使用。
- 接入 `install_mapping` grader，检查 `/home/hyde/projects/ptm-tde/test/.claude` 已安装 ptm-tde Agent 和关键 Skills。
- 新增 release profile 配置，供 `meta-flow eval release-check` 的发布门禁语义消费。
- 更新 CASE、覆盖矩阵和本地测试，防止配置漂移。

## CR 冲突预检

| 项 | 结论 |
|---|---|
| 当前 active CR | `CR-018`、`CR-020`、`CR-021` |
| 是否重叠 | 与 CR-020/021 同属 eval / feedback 闭环；不改 CR-018 流程合规基线 |
| 并行推进依据 | 用户要求继续推进 ptm-team 整改；本 CR 只修改 eval 配置、测试和文档，不改 Agent 主流程语义 |
| 冲突处理 | 保留 CR-020/021 已实现内容；CR-022 只在其上新增 meta-flow 消费端配置 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `evals/WORKFLOW-EVAL.yaml` | 原文档更新 | 保留既有静态 grader，新增 runtime / install / feedback source 消费配置 | 不适用 | approved |
| `evals/CASE-REGISTRY.yaml` | 原文档更新 | 保留 CASE-001~029，新增 CASE-030~034 | 不适用 | approved |
| `evals/EVAL-COVERAGE-MATRIX.md` | 原文档更新 | 保留既有覆盖分类，新增 runtime-artifact / release-check / feedback-source 覆盖 | 不适用 | approved |
| `evals/RUNTIME-SAMPLE-REGISTRY.yaml` | 原文档更新 | 保留 BGP4+ / policy_route 样本，补充 meta-flow grader 绑定语义 | 不适用 | approved |
| `evals/RELEASE-CHECK-PROFILE.yaml` | 新增 | 不适用 | 不适用 | approved |
| `tests/test_meta_flow_eval_consumption.py` | 新增 | 不适用 | 不适用 | approved |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | ptm-tde 评估闭环 | false | 不修改需求基线 |
| 场景层 | 是否改变测试矩阵覆盖范围 | BGP4+ / policy_route runtime 样本、反馈源 | true | 将真实 runtime / feedback 纳入 eval suite |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | eval suite 配置 | false | fast-lane 单切片实施 |
| 安全层 | 是否引入新的高风险动作或权限要求 | Git 读取、local-fs runtime 检查 | false | 默认只跑 local-fs；Git 拉取需显式 `--allow-git-read` |
| 交付层 | 是否需要重新生成交付物或回归子集 | eval run / suite-health / release-check | true | 更新配置后重新验证 eval / release-check |

## fast-lane 判定

| 条件 | 是否命中 | 说明 |
|---|---|---|
| 仅低风险轻量实现 / 文档 / 规则修改 | true | 只改 eval 配置、测试和 CR 文档 |
| 修改架构、权限、安全边界或平台安装路径 | false | 不改安装器行为；只新增安装结果检查 |
| 修改外部接口契约、文件所有权或多 Story 依赖 | false | 不新增外部接口 |
| 需要 HLD / LLD 才能解释影响 | false | 评估消费端配置，不需要新 HLD/LLD |
| 是否保持 fast-lane | true | 用户已授权继续实施 |

## 验收标准

- [x] `WORKFLOW-EVAL.yaml` 包含 `runtime_artifact` grader，分别覆盖 BGP4+ partial 与 policy_route full 样本。
- [x] `WORKFLOW-EVAL.yaml` 包含 `feedback_sources`，可被 `meta-flow eval feedback pull/analyze` 消费。
- [x] `WORKFLOW-EVAL.yaml` 包含 `install_mapping` grader，能检查 Claude 安装面包含 `ptm-tde` 与 `tde-feedback`。
- [x] `CASE-REGISTRY.yaml` 新增 runtime / feedback / install / release 门禁 CASE，并带 release-check 可消费元数据。
- [x] `RELEASE-CHECK-PROFILE.yaml` 明确 release 门禁阈值、runtime 样本、feedback triage 和 regression asset 要求。
- [x] 单元测试、`meta-flow eval validate/run/suite-health/release-check` 通过。

## 实施结果

| 对象 | 结果 |
|---|---|
| `evals/WORKFLOW-EVAL.yaml` | 新增 `feedback_sources`、`release_profiles`、2 个 `runtime_artifact` grader、1 个 `install_mapping` grader、feedback source / release profile contract grader |
| `evals/CASE-REGISTRY.yaml` | 新增 `CASE-030`~`CASE-034`，并补充 `severity`、`blocking`、`coverage_status`、`runtime_required`、`regression_asset` 等 release-check 元数据 |
| `evals/RUNTIME-SAMPLE-REGISTRY.yaml` | BGP4+ / policy_route 样本绑定到对应 `runtime_artifact_grader` |
| `evals/RELEASE-CHECK-PROFILE.yaml` | 新增 release profile，声明必选 runtime 样本、advisory 样本、feedback triage、issue gate 和 suite-health gate |
| `tests/test_meta_flow_eval_consumption.py` | 新增 ptm-team 消费 meta-flow runtime / release / feedback eval 能力的契约测试 |
| `docs/ptm-tde/USER-MANUAL.md` / `script/README.md` | 增补 `meta-flow eval feedback pull/analyze`、`suite-health`、`release-check` 的执行说明 |
| `docs/quality/EVAL-SUITE-HEALTH.md` | 刷新后显示 `runtime_sample_count=2`、`status=PASS` |
| `docs/quality/EVAL-RELEASE-CHECK.md` | 新增发布门禁报告，结论 `READY` |

## 验证结果

| 命令 | 结果 |
|---|---|
| `uv run python -m unittest tests.test_cr018_p2 tests.test_field_feedback tests.test_install_mapping tests.test_runtime_sample_registry tests.test_meta_flow_eval_consumption` | PASS，32 tests |
| `git diff --check` | PASS |
| `meta-flow eval validate --eval evals/WORKFLOW-EVAL.yaml` | PASS |
| `meta-flow eval run --eval evals/WORKFLOW-EVAL.yaml --out process/evals/runs/ptm-tde` | PASS，`eval-20260617T094026Z` |
| `meta-flow eval suite-health --runs process/evals/runs --out docs/quality/EVAL-SUITE-HEALTH.md` | PASS，`runtime_sample_count=2` |
| `meta-flow eval release-check --eval evals/WORKFLOW-EVAL.yaml --runs process/evals/runs --out docs/quality/EVAL-RELEASE-CHECK.md` | PASS，decision=`READY` |
| `meta-flow eval feedback pull --eval evals/WORKFLOW-EVAL.yaml --out process/field-feedback/meta-flow-pull` | PASS，本地源 PASS；GitLab 源因未授权 `git-read` 按预期 SKIP |
| `meta-flow eval feedback analyze --eval evals/WORKFLOW-EVAL.yaml --source-dir process/field-feedback/meta-flow-pull/ptm-team-feedback-local --out process/field-feedback/meta-flow-analysis` | 返回 1；生成 triage 证据：255 feedback files、75 fail-like issue drafts/backlog。该结果表示反馈中存在待分流问题，不表示 eval 配置失败 |
| `meta-flow eval install-check --eval evals/WORKFLOW-EVAL.yaml --out process/evals/install-check/ptm-tde` | PASS，`eval-20260617T094137Z` |
| `meta-flow check cr-tracking --project-root . --allow-multiple-active` | PASS，active CRs: CR-018/020/021/022 |

## 收敛状态

本 CR 实施切片已完成。用户于 2026-06-17 确认关闭。`feedback analyze` 已证明本地反馈源可以进入 meta-flow triage 输出，但当前真实反馈材料中存在 75 个 fail-like draft/backlog，需要后续人工或规则分流；该分流不在 CR-022 内直接关闭。
