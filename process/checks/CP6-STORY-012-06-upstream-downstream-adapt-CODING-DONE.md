---
checkpoint_id: CP6-STORY-012-06
story_id: STORY-012-06
story_slug: upstream-downstream-adapt
checkpoint_type: auto
status: PASS
created_by: meta-dev
created_at: "2026-06-02T12:00:00+08:00"
---

# CP6: STORY-012-06 编码完成检查

## Entry Criteria

- [x] Story `status=in-development`
- [x] LLD `STORY-012-06-upstream-downstream-adapt-LLD.md` 存在且已确认
- [x] CP5 全量 LLD 人工确认已通过
- [x] Wave D `dev_gate` 满足（Wave A 012-01/02、Wave B 012-03、Wave C 012-04/05 均已完成）
- [x] 文件所有权无冲突

## Checklist

### 1. 文件完整性

| # | 检查项 | 状态 | 证据 |
|---|--------|------|------|
| 1.1 | `skills/test-point-integrator/SKILL.md` 已修改 | PASS | 文件存在，前置条件、步骤 1/2/7.5/8、Gotchas、验收标准均已更新 |
| 1.2 | `skills/design-planner/SKILL.md` 已修改 | PASS | 文件存在，前置条件、步骤 1/2/6、Gotchas、验收标准均已更新 |
| 1.3 | 仅修改 2 个文件，无新建/删除文件 | PASS | `git diff --stat` 仅显示 2 个 Skill 文件 |

### 2. 验收标准逐项验证

| AC | 验证命令 | 结果 | 状态 |
|----|---------|------|------|
| AC01 | `grep -ci 'scenario-tsp-coverage\|覆盖矩阵' skills/test-point-integrator/SKILL.md` | 11 | PASS |
| AC02 | `grep -ci 'candidate\|候选' skills/test-point-integrator/SKILL.md` | 25 | PASS |
| AC03 | `grep -c 'mfq/m-analysis/\|mfq/f-analysis/\|mfq/q-analysis/' skills/test-point-integrator/SKILL.md` | 17 | PASS |
| AC04 | `grep -ci 'covered_scenario_segments\|covered.*segment' skills/design-planner/SKILL.md` | 5 | PASS |
| AC05 | `grep -c 'mfq/m-analysis/tsp/' skills/design-planner/SKILL.md` | 2 | PASS |
| AC06 | `grep -c 'process/plan/' skills/design-planner/SKILL.md` | 7 | PASS |
| AC07 | YAML frontmatter `name` 字段 | `test-point-integrator` 和 `design-planner` 均不变 | PASS |

### 3. 代码质量

| # | 检查项 | 状态 | 证据 |
|---|--------|------|------|
| 3.1 | `analysis/` 独立目录前缀零残留 | PASS | `grep -n 'analysis/' skills/*/SKILL.md | grep -v 'mfq/[mfq]-analysis/'` 无输出 |
| 3.2 | fail-fast 逻辑存在 | PASS | test-point-integrator: 步骤 1 覆盖矩阵 + 候选列表缺失时 `报错并终止`；design-planner: 步骤 1 TSP 缺失或字段缺失时 `报错并终止` |
| 3.3 | 无降级路径 | PASS | 所有 v2 兼容降级逻辑（`如果...不存在则跳过`）均已删除，改为 fail-fast |
| 3.4 | `mfq/candidates/` 路径引用存在 | PASS | `mfq/candidates/factor-candidates.md` 和 `mfq/candidates/atomic-op-candidates.md` 在步骤 7.5 和步骤 8 中引用 |
| 3.5 | `process/plan/` 输出路径正确 | PASS | `process/plan/design-plan.md` 和 `process/plan/design-planner-reasoning.md` 在步骤 6 中引用 |
| 3.6 | HARD-STOP 保留 | PASS | test-point-integrator 步骤 2 覆盖检查后的 HARD-STOP、design-planner 步骤 5 用户确认 HARD-STOP 均未修改 |
| 3.7 | 候选归集不自行确认 | PASS | 步骤 7.5 显式声明「只做归集和去重，不附加自行判定语句」 |
| 3.8 | STOP-04 前置校验 | PASS | 步骤 7.5 和步骤 8 均包含「写入前必须校验目标父目录存在且为目录」 |

### 4. LLD 实现一致性

| # | TASK-ID | 对应 LLD 章节 | 状态 | 说明 |
|---|---------|-------------|------|------|
| 4.1 | TASK-012-06-01 | §3/§4 前置条件区块 | PASS | 新增覆盖矩阵和候选文件前置条件 |
| 4.2 | TASK-012-06-02 | §7.1 步骤 1 | PASS | 步骤 1 新增覆盖矩阵加载 + 候选列表声明，含 fail-fast |
| 4.3 | TASK-012-06-03 | §7.1 步骤 2 / §8.1.1 | PASS | 步骤 2 新增覆盖矩阵视角 A 检查（covered/uncovered/excluded） |
| 4.4 | TASK-012-06-04 | §7.1 候选归集 / §8.1.2 | PASS | 新增步骤 7.5：三源候选读取 → 按 factor_id 去重 → 输出到 mfq/candidates/ |
| 4.5 | TASK-012-06-05 | §6.2 / §7.1 步骤 8 | PASS | 步骤 8 输出清单增加 factor-candidates.md + atomic-op-candidates.md |
| 4.6 | TASK-012-06-06 | §9 / §14 | PASS | Gotchas 新增 2 条（fail-fast + 不自行确认）；验收标准新增 3 条 |
| 4.7 | TASK-012-06-07 | §3/§4 前置条件区块 | PASS | 新增 TSP 文件和 covered_scenario_segments 前置条件 |
| 4.8 | TASK-012-06-08 | §7.2 步骤 1 | PASS | 步骤 1 新增子步骤 7：TSP covered_scenario_segments 加载 + LC→TSP→covered_steps 映射，含 fail-fast |
| 4.9 | TASK-012-06-09 | §7.2 步骤 2 / §8.1.3 | PASS | 步骤 2 新增子步骤 11：设计范围交叉校验（coverage_confirmed/partial/gap） |
| 4.10 | TASK-012-06-10 | §6.4 / §7.2 步骤 6 / §9 | PASS | 步骤 6 design-plan.md 路径改为 process/plan/；Gotchas 新增 fail-fast；验收标准新增 2 条 |

## Exit Criteria

- [x] 2 个目标文件已修改
- [x] AC01-AC07 全部 PASS
- [x] `analysis/` 旧路径独立目录前缀零残留
- [x] fail-fast 逻辑覆盖所有文件缺失场景（覆盖矩阵、候选列表、TSP）
- [x] 无 v2 降级路径残留
- [x] `mfq/candidates/` 和 `process/plan/` 新路径引用完整
- [x] HARD-STOP 标记未削弱
- [x] 候选归集步骤不自行确认
- [x] STOP-04 路径写入前置校验覆盖所有输出点
- [x] 10 个 TASK-ID 全部完成，与 LLD §11 一一对应

## Deliverables

| 文件 | 动作 | 路径 |
|------|------|------|
| test-point-integrator SKILL.md | 修改（~40 行净增） | `skills/test-point-integrator/SKILL.md` |
| design-planner SKILL.md | 修改（~12 行净增） | `skills/design-planner/SKILL.md` |
| CP6 编码完成检查 | 新建 | `process/checks/CP6-STORY-012-06-upstream-downstream-adapt-CODING-DONE.md` |

## Agent Dispatch Evidence

- **dispatch.mode**: inline-fallback
- **agent_id**: meta-dev (inline)
- **fallback_reason**: 用户直接委托实施，平台未拉起独立 meta-dev subagent
- **approved_by**: 用户
- **approved_at**: 2026-06-02
