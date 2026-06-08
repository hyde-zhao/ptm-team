---
story_id: STORY-012-06
story_name: 上下游 Skill 适配（test-point-integrator + design-planner）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: M
wave: D
depends_on: [STORY-012-01, STORY-012-03, STORY-012-04, STORY-012-05]
blocks: [STORY-012-07]
status: ready-for-verification
file_ownership:
  - skills/test-point-integrator/SKILL.md
  - skills/design-planner/SKILL.md
parallel_safe: false
---

# STORY-012-06：上下游 Skill 适配

## 1. 目标

适配 `test-point-integrator` 和 `design-planner` 两个 Skill，使其消费 M/F/Q 分析器 v3.0 产出的新数据格式和新增数据实体（覆盖矩阵、步骤标签、候选列表），同时保持对旧版输出格式的兼容性（graceful degradation）。

## 2. 范围

- **修改文件**：2 个
- **改动量**：~50 行（test-point-integrator ~35 行 + design-planner ~15 行）
- **不改动**：Skill 的核心归集/合并/设计计划逻辑；YAML frontmatter 的 `name`

### test-point-integrator 适配点

| 适配项 | 说明 |
|--------|------|
| 消费覆盖矩阵 | 读取 `mfq/m-analysis/scenario-tsp-coverage.md`，用于 SR→TSP→TP 覆盖链校验 |
| 消费新 M/F/Q TP 格式 | M 分析 TP 含关联度和 `scenario_refs` 字段；F/Q 分析 TP 含 `tsp_ref` 字段 |
| 消费 M/F/Q 产出的候选列表 | 为 STORY-012-07 候选汇总提供输入数据；integrator 只归集不汇总 |
| CAND 输出路径适配 | 候选汇总产物放到 `mfq/candidates/` |

### design-planner 适配点

| 适配项 | 说明 |
|--------|------|
| 适配 TSP.covered_scenario_segments | 从 `mfq/m-analysis/tsp/` 读取 TSP 时消费新字段 `covered_scenario_segments`，用于设计范围交叉校验 |
| 交叉校验设计范围 | 结合 LC 和 covered_scenario_segments，检查设计计划是否覆盖了场景的关键段落 |
| 输出路径确认 | `process/plan/` 已在 STORY-012-01 中迁移，本 Story 确认无遗漏 |

## 3. 验收标准

- [ ] **AC01**：`skills/test-point-integrator/SKILL.md` grep `scenario-tsp-coverage` 或 `覆盖矩阵` 返回 > 0
- [ ] **AC02**：`skills/test-point-integrator/SKILL.md` grep `candidate` 或 `候选` 返回 > 0（表明消费候选列表）
- [ ] **AC03**：`skills/test-point-integrator/SKILL.md` 输入路径使用 `mfq/m-analysis/` / `mfq/f-analysis/` / `mfq/q-analysis/`
- [ ] **AC04**：`skills/design-planner/SKILL.md` grep `covered_scenario_segments` 或 `covered.*segment` 返回 > 0
- [ ] **AC05**：`skills/design-planner/SKILL.md` 引用 `mfq/m-analysis/tsp/` 作为 TSP 来源
- [ ] **AC06**：`skills/design-planner/SKILL.md` 输出路径使用 `process/plan/`
- [ ] **AC07**：两个 Skill 的 YAML frontmatter 完整（`---` 配对，`name` 不变）

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `skills/test-point-integrator/SKILL.md` | 修改 | 输入契约扩展：增加覆盖矩阵消费（SR→TSP→TP 覆盖链校验）、增加 M/F/Q 候选列表消费；TP 归集逻辑适配新 TP 格式（tsp_ref/scenario_refs）；候选目录 `mfq/candidates/` 写入路径 |
| `skills/design-planner/SKILL.md` | 修改 | 输入扩展：TSP 消费增加 `covered_scenario_segments` 字段；CAE→PPDCS 推断中增加设计范围与 covered_segments 交叉校验逻辑；确认 `process/plan/` 输出路径无遗漏 |

## 5. 依赖关系

- **上游**：STORY-012-01（路径迁移）+ STORY-012-03（M 分析器新格式）+ STORY-012-04（F 分析器新格式）+ STORY-012-05（Q 分析器新格式）
- **下游**：STORY-012-07（候选汇总需要 test-point-integrator 归集后的候选数据）

## 6. 实施注意事项

### test-point-integrator 适配策略
- **最小改动原则**：保留现有归集、去重、LC 生成和拓扑绑定的核心逻辑；只在以下三处做增量修改：
  1. **步骤 1（加载输入）**：输入清单增加 `mfq/m-analysis/scenario-tsp-coverage.md`（覆盖矩阵）和 M/F/Q 候选列表文件路径
  2. **覆盖检查步骤**：在现有 SR→TP 覆盖检查之外，增加 SR→TSP→TP 覆盖链完整性检查（消费覆盖矩阵视角 A）
  3. **候选归集步骤**（为 STORY-012-07 准备数据）：读取 M/F/Q 三源的候选列表，按 factor_id 初步去重，输出到 `mfq/candidates/` 的临时归集文件

### design-planner 适配策略
- **最小改动原则**：保留现有 CAE→PPDCS 推断和设计方法推荐的核心逻辑；只做以下增量：
  1. **步骤 1（加载输入）**：TSP 消费增加 `covered_scenario_segments` 解析
  2. **设计范围交叉校验**（新增子步骤）：对每个 LC，检查其关联的 TSP.covered_scenario_segments 是否覆盖了该 LC 对应的场景段落；未覆盖段落标记 `confirmation_gap`
  3. 不改变 PPDCS 特征到设计方法的映射表

### 向后兼容
- 如果 `scenario-tsp-coverage.md` 不存在（M 分析 v2 模式），test-point-integrator 跳过覆盖矩阵校验，只执行原有 SR→TP 覆盖检查
- 如果 TSP 的 `covered_scenario_segments` 字段不存在，design-planner 跳过设计范围交叉校验，行为等同于旧版
