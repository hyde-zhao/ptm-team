---
change_id: CR-021-runtime-sample-manifest
title: ptm-tde runtime 样本清单与 BGP4+ / policy_route 绑定
status: closed
implementation_status: implemented
workflow_mode: fast-lane
created: 2026-06-17
approved: 2026-06-17
closed: 2026-06-17
impact_level: low
rollback_to: CR-020 feedback RUN-EXEC baseline
related_active_change: CR-020-tde-feedback-run-exec-closure
source: user
owner: host-orchestrator
---

# CR-021 - ptm-tde runtime 样本清单与 BGP4+ / policy_route 绑定

## 变更描述

CR-020 已把 `tde-feedback collect / submit` 接入 `RUN-EXEC` 台账。下一步需要在 ptm-team 保留 ptm-tde 的领域 runtime 样本实例，但不把通用 runtime grader / runner 逻辑混入 ptm-team。

本 CR 实施：

- 新增 `evals/RUNTIME-SAMPLE-REGISTRY.yaml`，登记 BGP4+ 与 policy_route 的真实运行样本。
- BGP4+ 作为 `partial / blocked` 现场反馈回归样本，绑定 `COLLECT-20260615-BGP4-005`。
- policy_route 作为 `full / pass` GATE-5 样本，绑定 `/home/hyde/projects/ptm-tde/test/policy_route_rt_verify`。
- 新增 ptm-team 单元测试验证样本清单中登记的本机 workspace / collection 关键 artifacts 存在。
- 新增 eval case 守住 runtime sample registry 的领域契约。

## 边界

| 项 | 结论 |
|---|---|
| 是否实现 meta-flow `runtime_artifact` grader | 否，保留为 meta-flow 后续 CR |
| 是否实现 `runtime-eval-runner` | 否，保留为 meta-flow 后续 CR |
| 是否复制 BGP4+ / policy_route 大量样本文件进 ptm-team | 否，只登记路径与关键 artifact contract |
| 是否改变 release 判定 | 否，release-check 属于 meta-flow 后续能力 |

## 文档处理决策

| 受影响文档 | 处理方式 | 旧基线保留方式 | 修订记录位置 | 批准状态 |
|---|---|---|---|---|
| `evals/RUNTIME-SAMPLE-REGISTRY.yaml` | 新增 | 不适用 | 不适用 | approved |
| `evals/WORKFLOW-EVAL.yaml` | 原文档更新 | 保留既有 eval suite，新增 runtime sample registry 契约 | 不适用 | approved |
| `evals/CASE-REGISTRY.yaml` / `evals/EVAL-COVERAGE-MATRIX.md` | 原文档更新 | 保留既有 case，新增 runtime-sample 覆盖 | 不适用 | approved |

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增、删除或重定义 REQ-* | ptm-tde 评估样本资产 | false | 不修改需求基线 |
| 场景层 | 是否改变测试矩阵覆盖范围 | BGP4+ / policy_route 样本 | true | 将两个真实特性登记为 runtime sample |
| 计划层 | 是否改变 Phase、Wave、Story / 任务依赖 | eval registry / tests | false | fast-lane 单切片实施 |
| 安全层 | 是否引入新的高风险动作或权限要求 | 本机路径读取 | false | 只读验证，不执行外部命令 |
| 交付层 | 是否需要重新生成交付物或回归子集 | eval suite / tests | true | 增加 registry、case 和测试 |

## 验收标准

- [x] `evals/RUNTIME-SAMPLE-REGISTRY.yaml` 登记 BGP4+ partial 样本和 policy_route full 样本。
- [x] registry 明确 `runtime_artifact` 输入语义，但不实现通用 grader。
- [x] 单元测试验证 registry 指向的本机 workspace / collection 关键 artifact 存在。
- [x] meta-flow eval 新增 runtime-sample case 并通过。

## 实施结果

| 对象 | 结果 |
|---|---|
| `evals/RUNTIME-SAMPLE-REGISTRY.yaml` | 新增 BGP4+ partial field-feedback regression 样本和 policy_route GATE-5 full runtime 样本 |
| `tests/test_runtime_sample_registry.py` | 验证 registry 声明的 workspace / collection 关键 artifact 在当前环境存在 |
| `evals/WORKFLOW-EVAL.yaml` | 新增 `runtime-sample-registry-contract` grader |
| `evals/CASE-REGISTRY.yaml` | 新增 `CASE-029` |
| `evals/EVAL-COVERAGE-MATRIX.md` | 新增 `runtime-sample` 类别，总 case 数更新为 29 |

## 验证结果

| 命令 | 结果 |
|---|---|
| `uv run python -m unittest tests.test_cr018_p2 tests.test_field_feedback tests.test_install_mapping tests.test_runtime_sample_registry` | PASS，27 tests |
| `meta-flow eval validate --eval evals/WORKFLOW-EVAL.yaml` | PASS |
| `meta-flow eval run --eval evals/WORKFLOW-EVAL.yaml --out process/evals/runs/ptm-tde` | PASS，`eval-20260617T092241Z` |
| `meta-flow eval suite-health --runs process/evals/runs --out docs/quality/EVAL-SUITE-HEALTH.md` | PASS |

## 收敛状态

本 CR 的实施切片已完成。用户于 2026-06-17 确认关闭。后续消费这些样本执行真实 runtime artifact 判定已在 CR-022 接入 meta-flow 通用 `runtime_artifact` grader；ptm-team 不实现通用 runner / grader。
