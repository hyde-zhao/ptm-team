# Eval Coverage Matrix — ptm-tde

> 覆盖矩阵追踪每个 case 与风险类别 / 产物类型的映射关系。

| Case ID | Category | Target | Risk Area | Artifact Type |
|---------|----------|--------|-----------|---------------|
| CASE-001 | smoke | `agents/ptm-tde.md` | 结构缺失 | Agent 定义 |
| CASE-002 | positive | `skills/` | 路径断裂 | Skill 定义 |
| CASE-003 | positive | `agents/ptm-tde.md` | 编排不完整 | Agent 定义 |
| CASE-004 | positive | `skills/` | Skill 缺少关键字段 | Skill 定义 |
| CASE-005 | regression | `PROMPT-BUNDLE.yaml` | Hash 不一致 | Bundle 配置 |
| CASE-006 | security | `agents/ptm-tde.md` | 凭证泄露 | Agent 定义 |
| CASE-007 | security | `skills/` | 外部网络调用 | Skill 定义 |
| CASE-008 | permission | `agents/ptm-tde.md` | 权限越界 | Agent 定义 |
| CASE-009 | failure-recovery | `agents/ptm-tde.md` | 门控不可检查 | Agent 定义 |
| CASE-010 | style | `CASE-REGISTRY.yaml` | 引用断裂 | Case 注册表 |
| CASE-011 | content-depth | `skills/deliverable-renderer/SKILL.md` | 输出模板不完整 | Skill 定义 |
| CASE-012 | content-depth | `agents/ptm-tde.md` | 阶段可跳过 | Agent 定义 |
| CASE-013 | content-depth | `skills/` | 表格列不对齐 | Skill 定义 |
| CASE-014 | eval-contract | `WORKFLOW-EVAL.yaml` | 空参数 false-pass | Eval 配置 |
| CASE-015 | workflow-skip | `agents/ptm-tde.md` | Skill 调用链被跳过 | Agent 定义 |
| CASE-016 | workflow-skip | `agents/ptm-tde.md` | 人工 Gate 被自批通过 | Agent 定义 |
| CASE-017 | content-retention | `agents/ptm-tde.md` + core skills | 追踪字段在阶段间丢失 | Agent / Skill 定义 |
| CASE-018 | content-retention | `skills/test-point-integrator/SKILL.md` | 候选项未确认即进入最终产物 | Skill 定义 |
| CASE-019 | table-schema | `skills/deliverable-renderer/SKILL.md` | PC 16 列 schema 漂移 | Skill 定义 |
| CASE-020 | table-schema | `skills/checkpoint-manager/SKILL.md` | Warning 表列 schema 回归 | Skill 定义 |
| CASE-021 | negative | `fixtures/ptm-tde-negative/missing-trace-fields.md` | 缺追踪字段未被检出 | Negative fixture |
| CASE-022 | negative | `fixtures/ptm-tde-negative/missing-candidate-decision.md` | 缺候选 decision 未被检出 | Negative fixture |
| CASE-023 | negative | `fixtures/ptm-tde-negative/pc-15-columns.md` | PC 表缺列未被检出 | Negative fixture |
| CASE-024 | field-feedback | `.ptm-field-feedback.yaml` | 默认反馈仓库配置丢失或指向错误 | Feedback 配置 |
| CASE-025 | field-feedback | `agents/ptm-tde.md` | Agent 无法通过提示词触发反馈闭环 | Agent 定义 |
| CASE-026 | field-feedback | `skills/tde-feedback/SKILL.md` | 问题反馈询问、上传授权或拉取协议缺失 | Skill 定义 |
| CASE-027 | install | `script/install.py` + `script/ptm_team/install.py` | 安装 ptm-tde 时遗漏 tde-feedback | 安装映射 |
| CASE-028 | field-feedback | `script/field_feedback.py` | COLLECT 采集包未自动进入 RUN-EXEC 台账 | Feedback 脚本 |
| CASE-029 | runtime-sample | `evals/RUNTIME-SAMPLE-REGISTRY.yaml` | BGP4+ / policy_route 真实运行样本未登记 | Runtime 样本清单 |
| CASE-030 | runtime-artifact | `/home/hyde/projects/ptm-tde/test/bgp4+` | BGP4+ partial 真实运行样本阶段证据不可消费 | Runtime workspace |
| CASE-031 | runtime-artifact | `/home/hyde/projects/ptm-tde/test/policy_route_rt_verify` | policy_route full 真实运行样本未完成 GATE-5 或交付证据缺失 | Runtime workspace |
| CASE-032 | feedback-source | `evals/WORKFLOW-EVAL.yaml` | feedback source 未接入 meta-flow eval feedback pull/analyze | Eval 配置 |
| CASE-033 | install | `/home/hyde/projects/ptm-tde/test/.claude` | 真实 Claude 安装面缺 ptm-tde 或 tde-feedback | 安装结果 |
| CASE-034 | release-check | `evals/RELEASE-CHECK-PROFILE.yaml` | release 门禁未声明 runtime / feedback / regression asset 要求 | 发布门禁配置 |

## 覆盖分布

| 类别 | 数量 | 占比 |
|------|------|------|
| smoke | 1 | 2.9% |
| positive | 3 | 8.8% |
| regression | 1 | 2.9% |
| security | 2 | 5.9% |
| permission | 1 | 2.9% |
| failure-recovery | 1 | 2.9% |
| style | 1 | 2.9% |
| content-depth | 3 | 8.8% |
| eval-contract | 1 | 2.9% |
| workflow-skip | 2 | 5.9% |
| content-retention | 2 | 5.9% |
| table-schema | 2 | 5.9% |
| negative | 3 | 8.8% |
| field-feedback | 4 | 11.8% |
| install | 2 | 5.9% |
| runtime-sample | 1 | 2.9% |
| runtime-artifact | 2 | 5.9% |
| feedback-source | 1 | 2.9% |
| release-check | 1 | 2.9% |
| **总计** | **34** | **100%** |

## 未覆盖类别（后续迭代补充）

| 类别 | 说明 |
|------|------|
| negative | ~~新增~~ 已通过 CASE-021/022/023 覆盖：缺追踪字段、缺候选 decision、PC 缺列 |
| multi-run | 需要多次运行验证稳定性，依赖实际执行环境 |
| efficiency | 需要运行性能基线，依赖实际执行环境 |
| mutation | 需要自动复制 fixture 并删除关键字段，验证 grader 能失败而不是只在当前文本上 PASS |
| external-adapter | LLM/SaaS grader 默认 disabled；如启用需 runtime_authorization |
| content-depth | ~~新增~~ 已通过 CASE-011/012/013 覆盖：输出模板完整性、状态机形式化、表格列对齐检查 |
| workflow-skip / content-retention / table-schema | ~~新增~~ 已通过 CASE-015~020 覆盖：流程跳过、内容丢失和关键表 schema |
| field-feedback | ~~新增~~ 已通过 CASE-024/025/026/028 覆盖：默认反馈仓库配置、Agent 触发协议、tde-feedback Skill 和 RUN-EXEC 自动登记 |
| runtime-sample | ~~新增~~ 已通过 CASE-029 覆盖：BGP4+ partial field-feedback regression 样本和 policy_route full runtime 样本登记 |
| runtime-artifact | ~~新增~~ 已通过 CASE-030/031 覆盖：BGP4+ partial workspace 与 policy_route full workspace 的真实 artifact 检查 |
| feedback-source | ~~新增~~ 已通过 CASE-032 覆盖：meta-flow eval feedback pull/analyze 的 source 配置 |
| release-check | ~~新增~~ 已通过 CASE-034 覆盖：release 门禁 profile 的 runtime / feedback / regression asset 要求 |
