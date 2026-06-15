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

## 覆盖分布

| 类别 | 数量 | 占比 |
|------|------|------|
| smoke | 1 | 3.7% |
| positive | 3 | 11.1% |
| regression | 1 | 3.7% |
| security | 2 | 7.4% |
| permission | 1 | 3.7% |
| failure-recovery | 1 | 3.7% |
| style | 1 | 3.7% |
| content-depth | 3 | 11.1% |
| eval-contract | 1 | 3.7% |
| workflow-skip | 2 | 7.4% |
| content-retention | 2 | 7.4% |
| table-schema | 2 | 7.4% |
| negative | 3 | 11.1% |
| field-feedback | 3 | 11.1% |
| install | 1 | 3.7% |
| **总计** | **27** | **100%** |

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
| field-feedback | ~~新增~~ 已通过 CASE-024/025/026 覆盖：默认反馈仓库配置、Agent 触发协议和 tde-feedback Skill |
