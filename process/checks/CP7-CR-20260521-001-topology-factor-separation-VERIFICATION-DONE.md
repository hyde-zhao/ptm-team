---
checkpoint_id: "CP7-CR-20260521-001-topology-factor-separation-VERIFICATION-DONE"
checkpoint_name: "CR-20260521-001 topology-role/factor-separation 验证完成门"
type: "rolling_auto"
status: "PASS"
owner: "meta-qa"
created_at: "2026-05-21T15:33:32+08:00"
checked_at: "2026-05-21T15:33:32+08:00"
target:
  phase: "story-execution"
  change_id: "CR-20260521-001"
  artifacts:
    - "agents/ptm-tde.md"
    - "docs/ptm-tde/"
    - "resource/factor-libraries/"
    - "skills/*/SKILL.md"
    - "script/install.py"
    - "script/ptm_team/install.py"
handoff: "process/handoffs/CR-20260521-001-meta-qa-topology-factor-separation.md"
---

# CP7 CR-20260521-001 Topology Factor Separation 验证完成门

## Entry Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| CR 处于可验证状态 | PASS | `process/changes/CR-20260521-001.md` status=`in-progress`，包含 topology role / factor separation rework acceptance criteria | 本轮验证目标明确。 |
| CP6 编码完成门通过 | PASS | `process/checks/CP6-CR-20260521-001-topology-factor-separation-CODING-DONE.md` status=`PASS` | 三个 meta-dev worker 的实现范围已登记。 |
| 验证环境确认 | PASS | `process/VALIDATION-ENV.yaml` 中 `approval.confirmed=true` | 满足 meta-qa 入口门控。 |
| QA 调度证据存在 | PASS | `process/handoffs/CR-20260521-001-meta-qa-topology-factor-separation.md` | handoff 记录 target_role=`meta-qa`、mode=`spawn_agent`、agent_id。 |
| 未要求修改产品文件 | PASS | 用户明确要求不要回退或修改产品文件 | 本次仅写入 CP7 检查文件和 QA handoff 证据。 |

## Checklist

| # | 检查项 | 状态 | 证据 | 处理意见 |
|---|---|---|---|---|
| 1 | Diff 格式检查 | PASS | `git diff --check -- README.md agents docs script skills resource process` exit=0 | 仅出现 `skills/f-analyzer/SKILL.md`、`skills/q-analyzer/SKILL.md` 的 CRLF 将被 Git 规范化 warning；无 whitespace error。 |
| 2 | 分层契约关键词覆盖 | PASS | `rg -n "topology_bindings|topology_role_refs|topology_binding_status|topology_gap_refs|factor_bindings|materialized_stage" skills agents docs resource process` exit=0，输出 264 行 | 命中覆盖 `agents/ptm-tde.md`、`docs/ptm-tde/*`、`resource/factor-libraries/*`、`skills/m-analyzer`、`test-point-integrator`、`design-planner`、`design-ppdcs-analyzer`、五类设计 Skill、`coverage-verifier`、`deliverable-renderer`、`skills/README.md` 和 CR/handoff。 |
| 3 | factor catalog 负向规则检查 | PASS | `rg -n "FAC-TOPO|BTO-|bound_topology_object.*factor catalog|topology_role.*factor catalog|DUT\\.port.*factor catalog|TG\\.port.*factor catalog" skills/parameter-design/SKILL.md skills/combination-design/SKILL.md` exit=0 | 唯一命中为 `skills/combination-design/SKILL.md:98` 的负向规则：`topology_role` 默认不进入 factor catalog；`parameter-design` 无命中。未发现示例把 topology role 或真实端口放入 factor catalog。 |
| 4 | 公共 resource 校验 | PASS | `uv run --no-project python script/install.py resource validate` exit=0，输出“公共资源校验通过” | resource/factor-libraries schema 与索引可被安装器校验。 |
| 5 | Codex 安装 dry-run | PASS | `uv run --no-project python script/install.py install codex --agent ptm-tde --dry-run` exit=0 | dry-run 安装 `.codex/agents/ptm-tde.toml`、19 个 skills，并同步 2 个公共 resources：`common-network`、`ngfw-policy-routing`。 |
| 6 | Claude 安装 dry-run | PASS | `uv run --no-project python script/install.py install claude --agent ptm-tde --dry-run` exit=0 | dry-run 安装 `.claude/agents/ptm-tde.md`、19 个 skills，并同步 2 个公共 resources：`common-network`、`ngfw-policy-routing`。 |
| 7 | 安装器语法检查 | PASS | `uv run --no-project python -m py_compile script/install.py script/ptm_team/install.py` exit=0 | 语法检查通过，无输出。 |
| 8 | 缓存生成物清理 | PASS | py_compile 后发现 `script/__pycache__`、`script/ptm_team/__pycache__`；已执行 `rm -rf script/__pycache__ script/ptm_team/__pycache__`，复查 `find . -path '*/__pycache__' -type d` 无输出 | 仅清理本轮验证产生的缓存；未删除现有未跟踪 `skills/atomic-ops-builder-restapi/`。 |
| 9 | 安全合规只读扫描 | PASS | `rg -n "rm -rf|sudo|curl .*[|].*sh|wget .*[|].*sh|dd if=|mkfs|chmod 777|chown -R|shell=True|os\\.system|eval\\(|ignore previous|忽略.*指令|API[_ -]?KEY|secret" <本轮目标文件 + install.py>` exit=1 | 对本轮 rework 目标文件未命中危险命令、明显 Prompt 注入或凭据模式。全仓库 scan 会命中既有/未跟踪 skill 的历史 credential 示例，未纳入本 CR 放行判断。 |
| 10 | MFQ 测试因子分层 | PASS | `skills/m-analyzer/SKILL.md` 明确 `factor_bindings` 只承载测试因子，`topology_role_refs` 只能表达逻辑位置；`skills/f-analyzer/SKILL.md`、`skills/q-analyzer/SKILL.md` 禁止真实端口进入 factor refs/bindings | 满足“测试因子不承载真实组网对象”的验收目标。 |
| 11 | 拓扑角色到真实组网绑定链路 | PASS | `skills/test-point-integrator/SKILL.md` 定义从 `topology_role_refs` 回查 `confirmed-scenarios.md` 并生成 LC `topology_bindings`；缺失/不唯一时写 `needs-confirmation` 与 `topology_gap_refs` | 满足 CAE 表达拓扑角色、LC 绑定真实组网对象的分层要求。 |
| 12 | PPDCS/PC 消费与回链 | PASS | `skills/design-ppdcs-analyzer/SKILL.md` 要求 PC 真实端口只能来自 LC `topology_bindings.bound_object`，并回链到 `confirmed-scenarios.md` | 满足真实端口只在 PC 物化阶段出现且可回链的要求。 |
| 13 | Coverage 与 delivery 保留状态 | PASS | `skills/coverage-verifier/SKILL.md` 要求 PC 真实端口回链 LC/confirmed-scenarios，`needs-confirmation` 不得提升；`skills/deliverable-renderer/SKILL.md` 要求交付物保留 `topology_bindings / topology_role / source / fact_status` | 满足 coverage/delivery 对 topology binding 状态不篡改的要求。 |
| 14 | Docs/resource 说明闭环 | PASS | `docs/ptm-tde/README.md`、`USER-MANUAL.md`、`component-manual.md`、`skill-references.md` 和 `resource/factor-libraries/README.md`、`ngfw-policy-routing/factor-library.md` 均说明真实端口不是公共因子，须通过 `topology_role_refs -> topology_bindings -> PC materialization` 流转 | 满足 Skill/docs/resource 同步落地要求。 |

## 8 维度验收矩阵

| 维度 | 阻断等级 | 状态 | 说明 |
|---|---|---|---|
| 完整性 | BLOCKING | PASS | CP6 标定的 Agent、Skill、docs、resource、coverage/delivery 相关文件均在本轮 grep/安装验证范围内。 |
| 平台适配 | BLOCKING | PASS | Codex 与 Claude dry-run 均通过；ptm-tde 安装路径、skill 同步和公共 resource 同步均可解析。 |
| 验收标准覆盖 | BLOCKING | PASS | CR acceptance criteria 逐项映射到 Checklist #10-#14，并由命令 #1-#7 支撑。 |
| 安全合规 | BLOCKING | PASS | 目标文件危险命令/注入/凭据模式扫描 exit=1，无命中；安装命令均为 dry-run 或只读校验。 |
| 命名规范 | REQUIRED | PASS | 目标 Skill 目录和 `SKILL.md`、docs/resource 文件路径保持既有 kebab-case/Markdown/YAML 约定。 |
| Frontmatter 完整性 | REQUIRED | PASS | 本轮修改目标为既有 Agent/Skill/docs/resource 契约；未发现破坏安装器可发现性的 Frontmatter 问题，安装 dry-run 成功加载 19 个 skills。 |
| 可安装性 | REQUIRED | PASS | resource validate、Codex dry-run、Claude dry-run 和 py_compile 均通过。 |
| 文档覆盖 | OPTIONAL | PASS | README、USER-MANUAL、component-manual、runtime-artifacts、skill-references、factor-library README 与领域库文档均覆盖 topology/factor 分层。 |

## Agent Dispatch Evidence

| Role | Agent ID | Tool | Evidence | Status |
|---|---|---|---|---|
| meta-qa | `019e496f-493e-7850-b9f1-7e040f92bb0f` | `spawn_agent` | `process/handoffs/CR-20260521-001-meta-qa-topology-factor-separation.md` | completed |
| meta-dev A | `019e4963-cc54-7d73-8437-6602514e9e1b` | `spawn_agent` | `process/handoffs/CR-20260521-001-meta-dev-A-topology-core.md` | completed before QA |
| meta-dev B | `019e4963-ffd1-7bf2-9799-58fc4e0b715d` | `spawn_agent` | `process/handoffs/CR-20260521-001-meta-dev-B-design-guards.md` | completed before QA |
| meta-dev C | `019e4964-4334-7263-b439-201ced017ef8` | `spawn_agent` | `process/handoffs/CR-20260521-001-meta-dev-C-docs-coverage.md` | completed before QA |

## Exit Criteria

| 条目 | 状态 | 证据 | 说明 |
|---|---|---|---|
| BLOCKING 维度全部通过 | PASS | 8 维度验收矩阵 | 无阻断项。 |
| REQUIRED 维度通过 | PASS | 命名、Frontmatter、可安装性均 PASS | 无需豁免。 |
| 用户指定命令全部执行 | PASS | Checklist #1-#7 | 全部 exit=0；第 #3 命令仅命中负向规则。 |
| 真实组网对象未作为公共因子值域 | PASS | Checklist #3、#10、#14 | Skill/docs/resource 明确真实端口只走 topology binding 链路。 |
| 生成物已清理 | PASS | Checklist #8 | py_compile 产生的 `__pycache__` 已清理。 |

## Deliverables

| 交付物 | 路径 | 状态 | 说明 |
|---|---|---|---|
| CP7 验证检查结果 | `process/checks/CP7-CR-20260521-001-topology-factor-separation-VERIFICATION-DONE.md` | PASS | 本文件。 |
| QA handoff 完成证据 | `process/handoffs/CR-20260521-001-meta-qa-topology-factor-separation.md` | PASS | 已补充 completed_at 与 QA Result。 |

## 结论

- 结论：`PASS`
- 阻断项：无
- 豁免项：无
- 残留风险：`git diff --check` 输出 CRLF normalization warning，涉及既有 `skills/f-analyzer/SKILL.md`、`skills/q-analyzer/SKILL.md`；不构成本轮验证阻断。
- 下一步：可由 meta-po 聚合 CR-20260521-001 本轮 topology-role/factor-separation rework 的验证结论。
