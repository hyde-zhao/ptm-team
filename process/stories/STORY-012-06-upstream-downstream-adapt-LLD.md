---
story_id: "STORY-012-06"
title: "上下游 Skill 适配（test-point-integrator + design-planner）"
story_slug: "upstream-downstream-adapt"
lld_version: "1.0"
tier: "M"
status: "ready-for-review"
confirmed: false
created_by: "meta-dev"
created_at: "2026-06-02T23:50:00+08:00"
confirmed_by: ""
confirmed_at: ""
shared_fragments: []
open_items: 0
---

# LLD: STORY-012-06 — 上下游 Skill 适配（test-point-integrator + design-planner）

> 文件名：`STORY-012-06-upstream-downstream-adapt-LLD.md`，其中 `story_slug` 复用 Story 卡片中的 `upstream-downstream-adapt`。
>
> 本文档是 `STORY-012-06` 的低层设计（Low-Level Design），需纳入 CR-012 全部 8 个目标 Story 的 LLD 统一确认，并满足 Wave D 的 `dev_gate`（Wave A/B/C 全部 verified）后方可进入实现。
>
> 设计蓝本：`HLD-CR-012.md` §9（test-point-integrator + design-planner v3.0 模块职责）+ M/F/Q 分析器 v3.0 LLD 中的输出格式契约。

---

## 1. Goal

对 `skills/test-point-integrator/SKILL.md`（~387 行 v2）和 `skills/design-planner/SKILL.md`（~367 行 v2）执行**增量适配**，使其消费 M/F/Q 分析器 v3.0 产出的新数据格式和新增数据实体（覆盖矩阵、`covered_scenario_segments`、候选列表），同时将路径从旧版 `analysis/` 迁移到 `mfq/` / `kym/` / `process/plan/`。保持现有归集/合并/设计计划核心逻辑不变，改动量约 50 行。

完成后：
- **test-point-integrator** 具备：覆盖矩阵消费能力（SR→TSP→TP 覆盖链校验）、M/F/Q 候选列表归集能力（为 STORY-012-07 候选汇总准备数据）、输出路径全部使用 `mfq/integration/` 和 `mfq/candidates/`
- **design-planner** 具备：TSP `covered_scenario_segments` 消费能力、设计范围与场景覆盖段的交叉校验能力、输出路径使用 `process/plan/`

---

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- **FR01（test-point-integrator）**：步骤 1（加载输入）中增加 `mfq/m-analysis/scenario-tsp-coverage.md`（覆盖矩阵）和 M/F/Q 候选列表文件（`mfq/m-analysis/candidate-factor-proposals.yaml`、`mfq/m-analysis/candidate-atomic-ops.yaml`、F/Q 候选列表嵌入在各自的测试点文件中）的消费逻辑
- **FR02（test-point-integrator）**：步骤 2（覆盖检查）中增加 SR→TSP→TP 覆盖链完整性检查，消费覆盖矩阵视角 A 的 covered/uncovered/excluded 统计
- **FR03（test-point-integrator）**：新增候选归集步骤：读取 M/F/Q 三源候选列表，按 `factor_id` / `candidate_id` 初步去重，输出到 `mfq/candidates/factor-candidates.md` 和 `mfq/candidates/atomic-op-candidates.md`（临时归集文件，为 STORY-012-07 候选汇总提供输入数据）
- **FR04（test-point-integrator）**：全部输入路径从 `analysis/` 迁移到 `mfq/` / `kym/`；输出路径从 `analysis/integration/` 迁移到 `mfq/integration/`；新增 `mfq/candidates/` 输出
- **FR05（design-planner）**：步骤 1（加载输入）中增加 TSP `covered_scenario_segments` 字段的解析逻辑，引用 `mfq/m-analysis/tsp/` 作为 TSP 来源
- **FR06（design-planner）**：步骤 2（逐条匹配）中新增设计范围交叉校验子步骤：对每个 LC，检查关联 TSP 的 `covered_scenario_segments` 是否覆盖该 LC 对应的场景段落；未覆盖段落标记 `confirmation_gap`
- **FR07（design-planner）**：输出路径从 `analysis/integration/design-plan.md` 迁移到 `process/plan/design-plan.md`；`analysis/plan/design-planner-reasoning.md` 迁移到 `process/plan/design-planner-reasoning.md`

### 2.2 Non-Functional

- **NFR01（v3.0 专用，不需要向后兼容）**：覆盖矩阵、候选列表和 TSP 文件是 M/F/Q 分析器 v3.0 的强制产出。Wave B/C（012-03/04/05）在 Wave D（012-06）之前必须完成，这些文件必然存在。不存在时的正确行为是 **fail fast 报错**，而非静默降级跳过。v2/v3 混合模式不在本 CR 范围内
- **NFR03（路径一致性）**：修改后两个 Skill 中 `analysis/` 旧路径零残留（不含注释中的路径说明引用）
- **NFR04（最小改动）**：不改动 Skill 的核心归集/合并/设计计划逻辑；不改动 YAML frontmatter 的 `name`；不改动 CAE 聚合规则、LC 生成逻辑、PPDCS 匹配规则、设计方法推荐等核心算法
- **NFR05（HARD-STOP 保留）**：现有 HARD-STOP 标记（如 integrator 步骤 2 覆盖检查后的确认、design-planner 步骤 5 用户确认）不削弱、不移除
- **NFR06（行数控制）**：test-point-integrator 净增 ≤ 35 行，design-planner 净增 ≤ 15 行

---

## 3. 模块拆分与职责

由于本 Story 修改 2 个现有的单文件 Skill，仅做增量适配而不重写，模块拆分聚焦于每个文件内的修改区块划分。

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `skills/test-point-integrator/SKILL.md` — 输入契约区块 | 路径迁移 + 覆盖矩阵 + 候选列表入口 | §适用范围/前置条件/输入契约中的路径更新 + 新增 2 个输入源 |
| `skills/test-point-integrator/SKILL.md` — 步骤 1 区块 | 加载覆盖矩阵和候选列表 | 在现有输入加载中追加覆盖矩阵读取 + 候选列表文件路径声明 |
| `skills/test-point-integrator/SKILL.md` — 步骤 2 区块 | SR→TSP→TP 覆盖链检查 | 在现有 SR→TP 覆盖检查之外增加覆盖矩阵视角 A 的统计消费 |
| `skills/test-point-integrator/SKILL.md` — 候选归集区块 | 三源候选初步归集 | 新增子步骤/步骤：读取 M/F/Q 候选 → 按 ID 去重 → 输出到 `mfq/candidates/` |
| `skills/test-point-integrator/SKILL.md` — 步骤 8 输出区块 | 输出路径迁移 + 新产出 | `analysis/integration/` → `mfq/integration/`；新增候选归集文件输出 |
| `skills/design-planner/SKILL.md` — 适用范围/前置条件区块 | 路径迁移 | `analysis/` → `mfq/` / `process/plan/` |
| `skills/design-planner/SKILL.md` — 步骤 1 区块 | TSP 新字段消费 | 在 TSP 加载中增加 `covered_scenario_segments` 解析 |
| `skills/design-planner/SKILL.md` — 步骤 2 区块 | 设计范围交叉校验 | 新增子步骤：LC 场景段落 ↔ TSP.covered_scenario_segments 覆盖对比 |
| `skills/design-planner/SKILL.md` — 步骤 6 输出区块 | 输出路径迁移 | `analysis/integration/design-plan.md` → `process/plan/design-plan.md`；`analysis/plan/` → `process/plan/` |

> 共享设计片段引用：HLD-CR-012.md §9（test-point-integrator 和 design-planner v3.0 模块职责）、STORY-012-03 LLD §5/§6（覆盖矩阵格式和输出契约）、STORY-012-04 LLD §5/§6（F 分析输出格式）、STORY-012-05 LLD §5/§6（Q 分析输出格式）。

---

## 4. 代码结构与文件影响范围

> 使用确定性动词（创建 / 修改），不改动核心逻辑，只做增量适配。

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `skills/test-point-integrator/SKILL.md` | 增量适配 ~35 行。适用范围/前置条件/输入契约：路径 `analysis/` → `mfq/`/`kym/`；步骤 1：新增覆盖矩阵和候选列表加载；步骤 2：新增 SR→TSP→TP 覆盖链检查；新增候选归集步骤：读取三源候选 → 去重 → 输出到 `mfq/candidates/`；步骤 8：输出路径迁移 + 新增候选归集文件 |
| 修改 | `skills/design-planner/SKILL.md` | 增量适配 ~15 行。适用范围/前置条件：路径 `analysis/` → `mfq/`/`process/plan/`；步骤 1：TSP 消费增加 `covered_scenario_segments` 解析；步骤 2：新增设计范围交叉校验子步骤；步骤 6：输出路径 `analysis/` → `process/plan/` |

> 仅修改 2 个文件。无新建文件、无删除文件。不涉及 Python 脚本、MCP 服务、安装脚本。

---

## 5. 数据模型与持久化设计

本 Story 不引入新数据实体，仅消费上游已定义格式并适配路径。无数据库持久化。

### 5.1 test-point-integrator 消费的新数据

| 对象 / 字段 | 来源（v3.0） | 格式 | 用途 |
|---|---|---|---|
| 覆盖矩阵 | `mfq/m-analysis/scenario-tsp-coverage.md` | Markdown 表格（视角 A：场景→TSP，含 covered/uncovered/excluded 统计） | SR→TSP→TP 覆盖链完整性校验 |
| M 因子候选 | `mfq/m-analysis/candidate-factor-proposals.yaml` | YAML（`candidate_id / factor_name / data_domain / source=new-candidate / scenario_refs`） | 候选归集输入 |
| M 原子操作候选 | `mfq/m-analysis/candidate-atomic-ops.yaml` | YAML（`candidate_id / op_name / op_desc / related_object_id / scenario_refs`） | 候选归集输入 |
| F 耦合因子候选 | 嵌入 `mfq/f-analysis/coupling-test-points.md` 末尾 | Markdown 表格（`factor_id / factor_name / data_domain / tsp_ref / coupling_ref / source=new-coupling-candidate`） | 候选归集输入 |
| Q 质量因子候选 | 嵌入 `mfq/q-analysis/quality-test-points.md` 末尾 | Markdown 表格（`factor_id / factor_name / data_domain / tsp_ref / quality_dimension / source=new-quality-candidate / generation_basis`） | 候选归集输入 |

### 5.2 test-point-integrator 新增产出

| 文件路径 | 格式 | 内容 |
|---|---|---|
| `mfq/candidates/factor-candidates.md` | Markdown 表格 | M/F/Q 三源因子候选合并（按 `factor_id` 去重），含 `候选ID / 因子名称 / 数据域 / 来源分析器（M/F/Q）/ 关联 TSP / 优先级 / 原始来源` |
| `mfq/candidates/atomic-op-candidates.md` | Markdown 表格 | M 分析原子操作候选（当前仅 M 分析产出原子操作候选），含 `候选ID / 操作名称 / 操作描述 / 关联对象 / 关联场景` |

> STORY-012-07（候选汇总）将消费这两个归集文件，进行进一步合并和用户批量确认。

### 5.3 design-planner 消费的新数据

| 对象 / 字段 | 来源（v3.0） | 格式 | 用途 |
|---|---|---|---|
| `covered_scenario_segments` | `mfq/m-analysis/tsp/<M编号>-tsp.md` 的 YAML frontmatter | `scenario_ref` + `covered_steps[]` + `coverage_type`（full/partial）+ `coverage_note` | 设计范围交叉校验 |

### 5.4 design-planner 输出路径变更

| 旧路径 | 新路径 | 说明 |
|---|---|---|
| `analysis/integration/design-plan.md` | `process/plan/design-plan.md` | 设计计划表，跨阶段边界（供 PPDCS 阶段消费） |
| `analysis/plan/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` | CAE→PPDCS reasoning 明细 |

---

## 6. API / Interface 设计

本 Story 修改的是 Claude Code Skill 文件，不存在传统 API。这里的"接口"指 Skill 的输入消费契约和输出生产契约的变化。

### 6.1 test-point-integrator 输入消费契约变更

| 接口 / 入口 | 旧输入 | 新输入 | 说明 |
|---|---|---|---|
| 步骤 1（场景输入） | `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` | 路径迁移（STORY-012-01 已迁移） |
| 步骤 1（M 分析产物） | `analysis/m-analysis/` 下的 test-points.md、test-objects-factors.md、ppdcs-annotation.md | `mfq/m-analysis/` 下同路径文件 | 路径迁移 |
| 步骤 1（F 分析产物） | `analysis/f-analysis/coupling-test-points.md`、`analysis/f-analysis/tool-analysis.md` | `mfq/f-analysis/coupling-test-points.md`、`mfq/f-analysis/tool-analysis.md` | 路径迁移 |
| 步骤 1（Q 分析产物） | `analysis/q-analysis/quality-test-points.md`、`analysis/q-analysis/tool-analysis.md` | `mfq/q-analysis/quality-test-points.md`、`mfq/q-analysis/tool-analysis.md` | 路径迁移 |
| 步骤 1（**新增**：覆盖矩阵） | — | `mfq/m-analysis/scenario-tsp-coverage.md` | v3.0 新实体，用于步骤 2 覆盖链校验 + 候选归集时场景回链 |
| 步骤 1（**新增**：M 候选） | — | `mfq/m-analysis/candidate-factor-proposals.yaml`、`mfq/m-analysis/candidate-atomic-ops.yaml` | v3.0 新实体，用于候选归集步骤 |
| 步骤 1（**新增**：F/Q 候选） | — | `mfq/f-analysis/coupling-test-points.md` 中的候选汇总节、`mfq/q-analysis/quality-test-points.md` 中的候选汇总节 | v3.0 新实体，用于候选归集步骤 |

### 6.2 test-point-integrator 输出生产契约变更

| 接口 / 入口 | 旧输出 | 新输出 | 消费方 | 说明 |
|---|---|---|---|---|
| 步骤 8 | `analysis/integration/all-test-points.md` | `mfq/integration/all-test-points.md` | design-planner、coverage-checker | 路径迁移 |
| 步骤 8 | `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` | design-planner | 路径迁移 |
| 步骤 8 | `analysis/integration/test-data.md` | `mfq/integration/test-data.md` | design-planner | 路径迁移 |
| 步骤 8 | `analysis/integration/tool-analysis.md` | `mfq/integration/tool-analysis.md` | design-planner | 路径迁移 |
| 步骤 8 | `analysis/integration/coverage-matrix.md` | `mfq/integration/coverage-matrix.md` | coverage-checker | 路径迁移 |
| 步骤 8（**新增**：候选归集） | — | `mfq/candidates/factor-candidates.md` | STORY-012-07（候选汇总） | 三源因子候选归集 |
| 步骤 8（**新增**：候选归集） | — | `mfq/candidates/atomic-op-candidates.md` | STORY-012-07（候选汇总） | 原子操作候选归集 |

### 6.3 design-planner 输入消费契约变更

| 接口 / 入口 | 旧输入 | 新输入 | 说明 |
|---|---|---|---|
| 步骤 1（LC） | `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` | 路径迁移 |
| 步骤 1（TD） | `analysis/integration/test-data.md` | `mfq/integration/test-data.md` | 路径迁移 |
| 步骤 1（PPDCS 标注） | `analysis/m-analysis/ppdcs-annotation.md` | `mfq/m-analysis/ppdcs-annotation.md` | 路径迁移 |
| 步骤 1（**新增**：TSP） | — | `mfq/m-analysis/tsp/<M编号>-tsp.md`（含 `covered_scenario_segments`） | v3.0 新消费字段，用于步骤 2 设计范围交叉校验 |

### 6.4 design-planner 输出生产契约变更

| 接口 / 入口 | 旧输出 | 新输出 | 消费方 | 说明 |
|---|---|---|---|---|
| 步骤 6 | `analysis/integration/design-plan.md` | `process/plan/design-plan.md` | PPDCS 阶段 Skill | 跨阶段边界，`process/plan/` 是 CR-010 定义的设计计划输出目录 |
| 步骤 6 | `analysis/plan/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` | 人工审阅 | 同目录迁移 |

### 6.5 消费链路变更总览

```
v2（旧）:
  m-analyzer ──→ test-points.md ──→ test-point-integrator ──→ logic-cases.md ──→ design-planner ──→ design-plan.md
  f-analyzer ──→ coupling-test-points.md ──→ ...                                                    (analysis/integration/)
  q-analyzer ──→ quality-test-points.md ──→ ...

v3.0（新，本 Story 适配）:
  m-analyzer ──→ test-points.md ───────────┐
          ├──→ scenario-tsp-coverage.md ───┤
          ├──→ candidate-factor-proposals ─┤
          └──→ candidate-atomic-ops ───────┤
  f-analyzer ──→ coupling-test-points.md ──┤ ──→ test-point-integrator ──→ mfq/integration/logic-cases.md ──→ design-planner ──→ process/plan/design-plan.md
          └──→ (候选嵌入测试点末尾) ────────┤                                  └── mfq/candidates/factor-candidates.md
  q-analyzer ──→ quality-test-points.md ───┤                                  └── mfq/candidates/atomic-op-candidates.md
          └──→ (候选嵌入测试点末尾) ────────┘
                                                                    m-analyzer ──→ tsp/<M>-tsp.md (covered_scenario_segments) ──→ design-planner（交叉校验）
```

> 本节每个接口条目，在 **第 10 节测试设计** 中找到至少 1 条对应测试（输入变更 → 测试 TC01-TC04，输出变更 → 测试 TC05-TC06）。

---

## 7. 核心处理流程

### 7.1 test-point-integrator：主流程变更点

现有 8 步流程保留，仅在以下位置做增量插入：

```
步骤 1: 加载输入
  ├─ [保留] 读取 M/F/Q 测试点文件（路径更新为 mfq/）
  ├─ [保留] 读取 confirmed-scenarios.md（路径更新为 kym/）
  ├─ [新增] 读取 scenario-tsp-coverage.md → 解析覆盖矩阵视角 A 的统计
  └─ [新增] 声明 M/F/Q 候选列表文件路径（用于候选归集步骤）
      │
      ▼
步骤 2: 覆盖检查
  ├─ [保留] 需求层覆盖（每条 SR → ≥1 TP）
  ├─ [保留] 场景层覆盖（每个 confirmed scenario → ≥1 TP）
  ├─ [保留] atomic-ops 覆盖
  ├─ [保留] confirmation_gap_refs 覆盖
  ├─ [保留] 覆盖判定规则（CF-05）
  └─ [新增] 覆盖矩阵视角 A 检查：
      · 统计 covered / uncovered / excluded 步骤数
      · 检查 uncovered 步骤是否有关联 TP（逐条列出缺口）
      · 检查 excluded 步骤的排除理由是否与排除条件一致
      · 输出：覆盖矩阵覆盖率 = covered / (total - excluded)
      │
      ▼
步骤 3-7: [不变] CAE 聚合 → LC 生成 → 拓扑绑定 → TD 归集 → 工具归并 → 覆盖矩阵输出
      │
      ▼
[新增] 候选归集步骤（插入在步骤 7 之后、步骤 8 之前）：
  ├─ 读取 M 因子候选（candidate-factor-proposals.yaml）
  ├─ 读取 M 原子操作候选（candidate-atomic-ops.yaml）
  ├─ 从 F 分析 coupling-test-points.md 末尾提取耦合因子候选
  ├─ 从 Q 分析 quality-test-points.md 末尾提取质量因子候选
  ├─ 按 factor_id / candidate_id 初步去重（同 ID 合并来源标注）
  ├─ 写入 mfq/candidates/factor-candidates.md
  └─ 写入 mfq/candidates/atomic-op-candidates.md
      │
      ▼
步骤 8: 输出
  ├─ [修改] 输出路径全部从 analysis/integration/ → mfq/integration/
  └─ [新增] 输出文件清单增加 mfq/candidates/factor-candidates.md + mfq/candidates/atomic-op-candidates.md
```

### 7.2 design-planner：主流程变更点

现有 6 步流程保留，仅在以下位置做增量插入：

```
步骤 1: 加载输入
  ├─ [保留] 读取 logic-cases.md（路径更新为 mfq/integration/）
  ├─ [保留] 读取 test-data.md（路径更新为 mfq/integration/）
  ├─ [保留] 读取 ppdcs-annotation.md（路径更新为 mfq/m-analysis/）
  ├─ [保留] 建立 LC→TD→子模块→PPDCS 映射
  └─ [新增] 读取 mfq/m-analysis/tsp/<M编号>-tsp.md，建立 LC→TSP→covered_scenario_segments 映射
      · 通过 LC 的 trace/scenario_refs 回链到对应的 TSP
      · 解析每个 TSP 的 covered_scenario_segments[{scenario_ref, covered_steps, coverage_type}]
      │
      ▼
步骤 2: 逐条匹配
  ├─ [保留] 子步骤 1-8：PPDCS 主辅特征 → CAE/TD 三轮扫描 → 候选/排除 → 推理
  └─ [新增] 子步骤：设计范围交叉校验
      · 对每个 LC，从步骤 1 的映射中查找关联 TSP 列表
      · 提取每个关联 TSP 的 covered_scenario_segments
      · 对比 LC 涉及场景的 minimal_logic_chain 步骤与 covered_steps
      · 覆盖 → 记录 coverage_confirmed
      · 部分覆盖 → 记录 coverage_note 中的 partial 说明
      · 未覆盖 → 标记 confirmation_gap，写入待确认事项
      │
      ▼
步骤 3-5: [不变] 生成设计计划表 → 统计与自检 → 用户确认
      │
      ▼
步骤 6: 输出
  ├─ [修改] design-plan.md → process/plan/design-plan.md
  └─ [修改] design-planner-reasoning.md → process/plan/design-planner-reasoning.md
```

### 7.3 文件缺失处理（fail-fast）

> v2/v3 混合模式不在本 CR 范围内。覆盖矩阵、候选列表和 TSP 是上游 v3.0 的强制产出，Wave B/C 必须先于 Wave D 完成。文件缺失意味着上游 Skill 未正确执行，正确行为是 **阻断报错**。

**test-point-integrator**：
```
若 scenario-tsp-coverage.md 不存在：
  → 报错并终止："mfq/m-analysis/scenario-tsp-coverage.md 不存在，请先执行 M 分析（STORY-012-03）"

若 M/F/Q 任一候选列表文件不存在：
  → 报错并终止："<文件路径> 不存在，请先执行对应的分析器"
```

**design-planner**：
```
若 TSP 文件不存在或 covered_scenario_segments 字段缺失：
  → 报错并终止："TSP 文件缺失或缺少 covered_scenario_segments 字段，请先执行 M 分析（STORY-012-03）"
```

---

## 8. 技术设计细节

### 8.1 关键算法 / 规则

#### 8.1.1 test-point-integrator：覆盖矩阵视角 A 检查规则

从 `mfq/m-analysis/scenario-tsp-coverage.md` 的视角 A（场景→TSP）表格中提取：

```
对每个场景的步骤段：
  ├── covered → 通过 TSP 链接到对应 TP，检查 TP 是否有覆盖该步骤段
  │   └── 预期：每个 covered 步骤段至少在步骤 5（测试数据归集）或步骤 7（覆盖矩阵输出）的追踪矩阵中有对应 TP
  ├── uncovered → 该步骤段在 scope 内但未被任何 TSP 覆盖
  │   └── 检查：是否在测试点生成或覆盖检查中被标记为 ⚠️ 待补充
  └── excluded → 显式排除（UI操作/超出 test_items/dont_test）
      └── 检查：排除理由与 M 分析步骤 2 子步骤 D 的排除判定一致

输出：覆盖矩阵覆盖率统计 + uncovered 步骤段与 TP 的缺口对照表
```

该检查**追加**在现有 SR→TP 覆盖检查之后，作为第二层覆盖验证。两个检查层互补：
- SR→TP 检查：从需求视角验证测试点覆盖（基于 SR 列表和 TP 的关联需求字段）
- 覆盖矩阵检查：从场景步骤视角验证 TSP→TP 链（基于覆盖矩阵的 covered/uncovered 统计）

#### 8.1.2 test-point-integrator：候选归集去重规则

```
因子候选去重（因子候选来源：M/F/Q 三源）：
  去重 key = factor_id（优先）或 factor_name（fallback）
  同名但不同数据域的因子候选 → 保留多条，标注差异
  同名同数据域的因子候选 → 合并为 1 条，标注多来源

原子操作候选去重（原子操作候选来源：仅 M 分析）：
  去重 key = candidate_id
  暂不涉及去重（当前仅 M 分析产出原子操作候选）
```

#### 8.1.3 design-planner：设计范围交叉校验规则

```
对每个 LC：
  1. 从 LC 的 scenario_refs 回链到场景
  2. 从场景的 TSP 覆盖映射中找到关联的 TSP 列表
  3. 读取每个关联 TSP 的 covered_scenario_segments：
     - scenario_ref：该 TSP 覆盖的场景引用
     - covered_steps[]：被覆盖的步骤编号列表（如 ["step-5", "step-6"]）
     - coverage_type：full（完整覆盖）| partial（部分覆盖）
  4. 对比 LC 涉及的功能步骤与 covered_steps：
     - LC 涉及的步骤全部在 covered_steps 中 → 记录 coverage_confirmed
     - LC 涉及的步骤部分在 covered_steps 中 → 记录 coverage_partial：
       · 已覆盖步骤标记 ✅
       · 未覆盖步骤标记 confirmation_gap：
         "设计计划的场景步骤 {step} 未被 TSP {tsp_id} 的 covered_scenario_segments 覆盖，
          请确认是否需要设计补充用例或更新 covered_scenario_segments"
     - LC 涉及的步骤全不在 covered_steps 中 → 记录 coverage_gap：
       "设计计划的全部场景步骤未被该 TSP 的 covered_scenario_segments 覆盖，
        可能原因：LC 跨 TSP 或 TSP 覆盖段定义不完整"
  5. 交叉校验结果写入：
     - design-plan.md 的「待确认事项」列
     - design-planner-reasoning.md 的「Uncertain Facts / Confirmation Gaps」
```

### 8.2 依赖选择与复用点

| 复用项 | 来源 | 是否修改 | 说明 |
|---|---|---|---|
| test-point-integrator 步骤 2 覆盖检查 | 现有 SKILL.md | 追加 | 保留所有现有检查项（需求层/场景层/atomic-ops/confirmation_gap_refs/CF-05），仅追加覆盖矩阵检查段 |
| test-point-integrator 步骤 3-7 核心逻辑 | 现有 SKILL.md | 不修改 | CAE 聚合、LC 生成、拓扑绑定、TD 归集、工具归并全部保持不变 |
| design-planner 步骤 2 PPDCS 匹配 | 现有 SKILL.md | 追加 | 保留 A/C/E 三轮扫描、候选/排除/推荐全部规则，仅追加设计范围交叉校验子步骤 |
| design-planner 步骤 3-5 核心逻辑 | 现有 SKILL.md | 不修改 | 设计计划表生成、统计自检、用户确认全部保持不变 |
| CAE 字段约束 | 现有 SKILL.md | 不修改 | C/A/E 三元组约束、E="待定"批注规则完整保留 |
| 拓扑/因子分层 Guardrail | 现有 SKILL.md | 不修改 | 完整保留 |

### 8.3 兼容性处理

| 兼容项 | 处理方式 |
|---|---|
| 与 STORY-012-01（路径迁移）的兼容 | STORY-012-01 已对 test-point-integrator 和 design-planner 做过 sed 路径替换。本 Story 在 STORY-012-01 修改结果的基础上做增量适配。实施时需注意：STORY-012-01 已改路径 `analysis/` → `mfq/` / `kym/`，本 Story 只需确认路径一致并追加新内容 |
| 与 STORY-012-03（M 分析器 v3.0）的兼容 | 消费 M 分析的覆盖矩阵和候选列表。若这些文件不存在（M 分析 v2 模式），test-point-integrator 自动降级 |
| 与 STORY-012-04（F 分析器 v3.0）的兼容 | F 分析 v3.0 按 TSP 组织测试点（而非按四/五级目录），integrator 步骤 1 归集时需适配新组织方式。但归集逻辑（按目录归集 TP）不变：TSP 内的 M 编号仍可映射到四/五级目录 |
| 与 STORY-012-05（Q 分析器 v3.0）的兼容 | Q 分析 v3.0 按 TSP 组织+按质量维度分组测试点，integrator 归集时需解析这种二级组织方式 |
| 候选列表缺失 | M/F/Q 中任一候选列表缺失时，候选归集步骤跳过该源，输出中标注缺失 |
| TSP 文件缺失 | design-planner 若无法找到对应 TSP 文件，跳过设计范围交叉校验 |

### 8.4 图示类型选择

- **流程图**：test-point-integrator 主流程序列（见 §7.1）
- **伪代码**：候选归集去重逻辑（见 §8.1.2）+ 设计范围交叉校验逻辑（见 §8.1.3）

---

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全（路径写入前置校验） | 沿用 STOP-04 规则：候选归集步骤写入 `mfq/candidates/` 前校验目标父目录存在且为目录。design-planner 写入 `process/plan/` 前同样校验。禁止 Agent 手动 mkdir | grep `mkdir` 在修改后的两个 SKILL.md 中返回 0 |
| 安全（HARD-STOP 保留） | test-point-integrator 步骤 2 覆盖检查后的 HARD-STOP、design-planner 步骤 5 用户确认的 STOP-02 HARD-STOP 不修改、不削弱 | 检查修改后的 Skill 中 HARD-STOP 标记数量不减 |
| 安全（向后兼容降级） | 所有新增消费逻辑均有降级路径：文件不存在或字段缺失时跳过新逻辑而非报错 | 见 §7.3 降级路径描述 |
| 安全（候选归集不自行确认） | 候选归集步骤仅做归集和去重，不附加"建议确认"等自行判定语句。候选状态保留上游标注（`new-candidate`/`new-coupling-candidate`/`new-quality-candidate`） | 检查候选归集步骤中无"建议确认"、"推荐通过"等语句 |
| 性能 | Skill 为声明式 Markdown 文档，无运行时性能要求。新增的覆盖矩阵检查是纯文本对比，不涉及计算密集操作 | N/A |
| 可维护性 | 采用增量修改而非全量重写，改动量控制在 ~50 行以内。每个修改点有明确的"新增"/"保留"标注 | `wc -l` 对比修改前后行数变化；人工审阅增量部分是否清晰标注 |

---

## 10. 测试设计

### 10.1 验收标准映射表

| AC | 测试目标 | 验证方式 | 对应接口 / 流程 |
|---|---|---|---|
| AC01 | 覆盖矩阵消费 | `grep -i 'scenario-tsp-coverage\|覆盖矩阵' skills/test-point-integrator/SKILL.md` 返回 > 0 | §6.1（覆盖矩阵输入契约） |
| AC02 | 候选列表消费 | `grep -i 'candidate\|候选' skills/test-point-integrator/SKILL.md` 返回 > 0（在候选归集上下文中） | §6.1（候选列表输入契约） |
| AC03 | 输入路径使用 mfq/ | `grep 'mfq/m-analysis/\|mfq/f-analysis/\|mfq/q-analysis/' skills/test-point-integrator/SKILL.md` 返回 > 0 | §6.1（输入契约变更） |
| AC04 | covered_scenario_segments 消费 | `grep -i 'covered_scenario_segments\|covered.*segment' skills/design-planner/SKILL.md` 返回 > 0 | §6.3（design-planner 输入变更） |
| AC05 | TSP 来源引用 | `grep 'mfq/m-analysis/tsp/' skills/design-planner/SKILL.md` 返回 > 0 | §6.3（design-planner 输入变更） |
| AC06 | 输出路径 process/plan/ | `grep 'process/plan/' skills/design-planner/SKILL.md` 返回 > 0 | §6.4（design-planner 输出变更） |
| AC07 | YAML frontmatter name 不变 | `grep '^name: test-point-integrator$' skills/test-point-integrator/SKILL.md` 返回 1；`grep '^name: design-planner$' skills/design-planner/SKILL.md` 返回 1 | §4（文件影响范围） |

### 10.2 关键流程测试

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| **TC01**：覆盖矩阵正常消费 | `mfq/m-analysis/scenario-tsp-coverage.md` 存在，包含 3 个场景的覆盖数据 | test-point-integrator 步骤 1 加载 | 覆盖矩阵被读取；步骤 2 输出 covered/uncovered/excluded 统计 | grep 检查 integrator SKILL.md 步骤 2 是否含"视角 A"、"covered"、"uncovered"等关键词 |
| **TC02**：覆盖矩阵缺失降级 | `scenario-tsp-coverage.md` 不存在 | test-point-integrator 步骤 1 加载 | 跳过覆盖矩阵加载；步骤 2 仅执行原有 SR→TP 检查；不报错 | 检查 integrator SKILL.md 是否含"如果 scenario-tsp-coverage.md 不存在"的条件分支 |
| **TC03**：候选归集去重 | M 分析有 `FAC-CAND-001: 服务器数量上限`；F 分析也有同名候选 | 执行候选归集步骤 | 合并为 1 条，来源标注 M+F | 检查 integrator SKILL.md 候选归集步骤是否含"按 factor_id 去重"、"合并来源"逻辑 |
| **TC04**：设计范围交叉校验 | LC-001 涉及场景 SCN-001 的 step-5/step-6；TSP 的 covered_steps 仅含 step-5 | design-planner 步骤 2 交叉校验 | step-5 标记 coverage_partial；step-6 标记 confirmation_gap | 检查 design-planner SKILL.md 是否含"未覆盖段落"、"confirmation_gap"输出逻辑 |
| **TC05**：TSP 无 covered_scenario_segments 降级 | TSP 文件不含 covered_scenario_segments 字段 | design-planner 步骤 1 加载 | 跳过交叉校验；行为完全等同于旧版 | 检查 design-planner SKILL.md 是否含"如果 covered_scenario_segments 不存在"的条件分支 |
| **TC06**：输出路径验证 | 修改完成 | grep 旧路径 | `grep -rn 'analysis/' skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` 返回 0（不含注释中的路径说明引用） | 直接执行 grep 命令 |
| **TC07**：YAML frontmatter 完整性 | 修改完成 | 检查 frontmatter | test-point-integrator 的 `name: test-point-integrator` 不变；design-planner 的 `name: design-planner` 不变。`---` 配对完整 | grep frontmatter name + 人工审阅 |

---

## 11. 实施步骤

> 严格使用 TASK-ID + 确定性动词（修改）。由于改动量小（~50 行），修改按 Skill 分组、按区块次序编排。每个 TASK-ID 对应一个明确的修改区块。

### 11.1 test-point-integrator 修改（~35 行）

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| TASK-012-06-01 | 修改 | `skills/test-point-integrator/SKILL.md` | **适用范围/前置条件/输入契约区块**：路径从 `analysis/` → `mfq/`/`kym/`；前置条件路径更新；输入契约新增覆盖矩阵和候选列表条目 | TC06 |
| TASK-012-06-02 | 修改 | `skills/test-point-integrator/SKILL.md` | **步骤 1（加载输入）**：在现有 M/F/Q 测试点加载后追加 2 段：① 读取 `mfq/m-analysis/scenario-tsp-coverage.md`，解析视角 A 的覆盖矩阵（场景→TSP，含 covered/uncovered/excluded 统计）；② 声明候选列表文件路径（M 两个 YAML + F/Q 候选嵌入位置） | TC01、TC02 |
| TASK-012-06-03 | 修改 | `skills/test-point-integrator/SKILL.md` | **步骤 2（覆盖检查）**：在现有四层覆盖检查（需求/场景/atomic-ops/confirmation_gap）之后追加「覆盖矩阵视角 A 检查」段：统计 covered/uncovered/excluded 步骤数、检查 uncovered 步骤的 TP 缺口、计算覆盖率。覆盖矩阵缺失时报错终止 | TC01 |
| TASK-012-06-04 | 修改 | `skills/test-point-integrator/SKILL.md` | **新增候选归集步骤**（插入步骤 7 之后、步骤 8 之前）：读取 M/F/Q 三源候选列表 → 按 factor_id/candidate_id 去重 → 合并来源标注 → 输出候选归集表格。因子候选按 factor_id 去重（同名不同域保留多条），原子操作候选直接透传。标注「为候选汇总阶段准备数据，本步骤只归集不确认」 | TC03 |
| TASK-012-06-05 | 修改 | `skills/test-point-integrator/SKILL.md` | **步骤 8（输出）**：输出文件清单路径全部从 `analysis/integration/` → `mfq/integration/`；新增 2 个候选归集输出文件：`mfq/candidates/factor-candidates.md` + `mfq/candidates/atomic-op-candidates.md`（含格式示例）。更新前置条件中的输出路径引用。标注路径写入前置校验（STOP-04） | TC06 |
| TASK-012-06-06 | 修改 | `skills/test-point-integrator/SKILL.md` | **Gotchas + 验收标准区块**：Gotchas 新增 2 条（覆盖矩阵不存在时报错终止 + 候选归集不自行确认）；验收标准更新：路径前缀改为 `mfq/`、新增覆盖矩阵引用和候选归集产出检查 | TC06、AC01-AC03 |

### 11.2 design-planner 修改（~15 行）

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| TASK-012-06-07 | 修改 | `skills/design-planner/SKILL.md` | **适用范围/前置条件区块**：路径从 `analysis/` → `mfq/`/`process/plan/`；前置条件新增 TSP 文件可用性检查（含 `covered_scenario_segments`）；输出路径更新 | TC06 |
| TASK-012-06-08 | 修改 | `skills/design-planner/SKILL.md` | **步骤 1（加载输入）**：在现有 LC/TD/PPDCS 读取之后追加 TSP 加载段：读取 `mfq/m-analysis/tsp/<M编号>-tsp.md`；解析每个 TSP 的 `covered_scenario_segments` 字段（`scenario_ref` + `covered_steps[]` + `coverage_type` + `coverage_note`）；建立 `LC→scenario_ref→TSP→covered_steps` 映射。TSP 不存在或字段缺失时报错终止 | TC04 |
| TASK-012-06-09 | 修改 | `skills/design-planner/SKILL.md` | **步骤 2（逐条匹配）**：在现有逐条匹配逻辑末尾（子步骤 10 之后）追加「设计范围交叉校验」子步骤：对每个 LC 查找映射中的关联 TSP 列表 → 对比 LC 场景步骤与 covered_steps → 输出 coverage_confirmed / coverage_partial / coverage_gap → 未覆盖步骤标记 confirmation_gap 写入待确认事项 | TC04 |
| TASK-012-06-10 | 修改 | `skills/design-planner/SKILL.md` | **步骤 6（输出）+ Gotchas + 验收标准区块**：设计计划输出路径 `analysis/integration/design-plan.md` → `process/plan/design-plan.md`；reasoning 输出路径 `analysis/plan/` → `process/plan/`。Gotchas 新增 1 条（covered_scenario_segments 缺失时报错终止）。验收标准更新：路径改为 `process/plan/`、新增 covered_scenario_segments 引用检查 | TC06、AC04-AC06 |

> 每个 TASK-ID 对应 1 个修改区块；10 个 TASK-ID 覆盖 2 个目标文件的 10 个修改区块。

---

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

本 Story 改动量小（~50 行）、适配逻辑明确（所有上游输出格式已在 STORY-012-03/04/05 LLD 中定义），不存在需要用户或上游决策的实现灰区。所有设计决策可在 LLD 阶段自行确定：

| 设计决策 | 选择 | 理由 | 影响面 | 重访条件 |
|---|---|---|---|---|
| 候选归集去重 key | `factor_id`（优先）/ `factor_name`（fallback） | 与 M/F/Q 分析器候选列表的 `factor_id` / `candidate_id` 字段对齐 | 候选归集步骤输出格式 | 若上游候选列表无统一 `factor_id` 字段，改为仅按 `factor_name` 去重 |
| 候选归集输出文件 | 分离为 `factor-candidates.md` + `atomic-op-candidates.md` | 因子候选和原子操作候选语义不同，分开便于 STORY-012-07 独立处理 | 输出文件清单 | 若 STORY-012-07 需要合并文件，修改输出格式 |
| 覆盖矩阵检查与现有覆盖检查的关系 | 追加（两层互补）而非替换 | SR→TP 从需求视角、覆盖矩阵从场景步骤视角，两者互补 | integrator 步骤 2 结构 | 若用户反馈双重检查冗余，可合并为一层 |
| design-planner 交叉校验输出位置 | 写入「待确认事项」列 + reasoning 的 Uncertain Facts | 保持与现有 design-planner 输出结构一致 | design-plan.md 列结构 | 无 |

### 12.2 风险与难点

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| **R1：STORY-012-01 路径迁移覆盖不完整** | 低。STORY-012-01 可能遗漏某些 `analysis/` 路径引用，导致本 Story 的路径迁移基准不干净 | 实施前先 `grep -n 'analysis/' skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` 确认当前残留情况；实施后在静态 grep 检查中验证零残留 |
| **R2：F/Q 测试点新组织方式导致归集适配复杂化** | 中。F 分析 v3.0 按 TSP 组织测试点，Q 分析 v3.0 按 TSP+质量维度分组，与 v2 的按四/五级目录分节不同。integrator 步骤 1 的归集逻辑需识别新格式 | integrator 步骤 1 的归集逻辑描述使用"按 M/F/Q 来源归集到四/五级目录"而非"读取固定格式"，Agent 实施时有灵活性。若归集困难，在 TASK-012-06-02 中补充归集适配说明 |
| **R3：候选列表嵌入在测试点文件中，提取逻辑需写明** | 低。F 候选嵌入 `coupling-test-points.md` 末尾，Q 候选嵌入 `quality-test-points.md` 末尾。提取时需定位候选汇总节 | TASK-012-06-04 中明确：F 候选从 coupling-test-points.md 末尾的「耦合因子候选列表汇总」节提取；Q 候选从 quality-test-points.md 末尾的「质量因子候选列表汇总」节提取 |
| **R4：covered_scenario_segments 中步骤编号格式不一致** | 低。M 分析器 TSP 的 `covered_steps` 使用 `["step-5", "step-6"]` 格式，但场景的 `minimal_logic_chain` 步骤编号可能用 `["AO-01", "AO-02"]` 格式，两者无法直接对比 | TASK-012-06-09 中不要求精确步骤编号匹配，改为语义级对比：将 covered_steps 的场景步骤描述与 LC 动作路径描述做语义相似度判断，而非编号精确匹配。若无法确定覆盖关系，标记为不确定并写入 reasoning |

### OPEN / Spike 跟踪

| ID | 类型 | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| — | — | 无 OPEN / Spike 项。所有设计决策均已在本 LLD 中确定，无需用户或上游额外决策。 | — | — |

---

## 13. 回滚与发布策略

- **发布方式**：本 Story 修改 2 个 Skill 文件。通过 git commit 发布，message 格式：`feat: test-point-integrator 和 design-planner 适配 M/F/Q v3.0 新数据格式`。在 Story 卡片中将 status 推进到 `ready-for-verification`，等待 meta-qa 的 CP7 验证。

- **回滚触发条件**：
  1. CP7 验证发现 AC01-AC07 中 ≥3 项 FAIL（特别是 AC03 旧路径残留、AC06 输出路径错误）
  2. STORY-012-07（候选汇总）实施时发现候选归集格式不可消费，且无法在 STORY-012-07 侧修复
  3. test-point-integrator 归集逻辑无法适配 F/Q 分析器 v3.0 的 TSP 组织方式，导致覆盖检查大面积 FAIL

- **回滚动作**：
  1. `git revert <STORY-012-06 commit>` — 回退两个 Skill 到修改前的状态
  2. 若修改前 STORY-012-01 已做路径迁移，回退到 STORY-012-01 修改后的版本（即路径已迁移但无 v3.0 适配）
  3. 重新评估是否需要更深入的归集逻辑修改（而非纯增量适配）

- **回退后的恢复路径**：以 STORY-012-01 迁移后的版本为基础，重新评估 F/Q 测试点的 TSP 组织方式对 integrator 归集的影响。若增量适配不足以处理组织方式变化，将归集逻辑修改拆分到独立的 Story 或扩大本 Story 范围。

---

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] 文件影响范围（§4：2 个文件）、接口（§6：4 组契约变更）、测试（§10：7 项测试场景）与实施步骤（§11：10 个 TASK-ID）可直接指导编码
- [ ] 实现灰区与取舍记录（§12.1）已回填所有设计决策，无 OPEN / Spike 项
- [ ] `confirmed=false` 时不进入实现
- [ ] 人工确认意见已收敛（CP5 全量 LLD 统一确认）
- [ ] frontmatter 已填写 `tier: "M"`
- [ ] OPEN / Spike 已清点：无（§12.2 显式写"无"）
- [ ] 第 6 节接口条目与第 10 节测试条目已配对：TC01-TC03 对应 test-point-integrator 输入/输出，TC04-TC05 对应 design-planner 输入，TC06-TC07 对应全局验收
- [ ] 第 7 节异常路径已覆盖：覆盖矩阵缺失降级（test-point-integrator）、covered_scenario_segments 缺失降级（design-planner）、候选文件缺失降级、TSP 文件缺失降级
- [ ] 第 11 节 TASK-ID 与第 4 节文件影响范围一一对应：TASK-012-06-01~06 对应 test-point-integrator，TASK-012-06-07~10 对应 design-planner
- [ ] 向后兼容降级路径在 §7.3 和 §8.3 中明确定义（共 4 种降级场景）
- [ ] STOP-04 路径写入前置校验在两个 Skill 的修改点中均已覆盖（§9）
- [ ] 候选归集步骤不自行确认候选（§9）
- [ ] 现有 HARD-STOP 标记不削弱、不移除（§9）

---

## 人工确认区

> **CP5 — Story LLD 可实现性门**
> meta-dev 先写入 `process/checks/CP5-STORY-012-06-upstream-downstream-adapt-LLD-IMPLEMENTABILITY.md` 自动预检结果。
> meta-po 收齐 CR-012 全部 8 个目标 Story 的 LLD、CP4 自动预检摘要和 CP5 自动预检后，再生成并提示用户审查 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md`。
> 用户统一确认全部目标 Story 的 LLD 后，仍需满足 Wave D 的依赖门控（STORY-012-01/03/04/05 全部 verified）与文件所有权门控方可进入实现。

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | §2.1 FR01-FR07 + §10 测试设计（7 项 AC 全部覆盖） |
| 2 | 与 HLD / ADR 一致 | 待检查 | §3 / §8.2 / §12.1：HLD-CR-012.md §9（test-point-integrator + design-planner v3.0 模块职责）、AGA-01（候选内嵌→integrator）、AGA-03（覆盖矩阵独立文件→integrator 消费）、AGA-04（标签嵌入覆盖矩阵→integrator 消费）全部落实 |
| 3 | 文件影响范围明确 | 待检查 | §4 / §11：修改 2 文件，10 个 TASK-ID 全部覆盖 |
| 4 | 接口契约完整 | 待检查 | §6：4 组契约变更（test-point-integrator 输入/输出 + design-planner 输入/输出），含消费链路图 |
| 5 | 测试与 dev_gate 可计算 | 待检查 | §10 / §14 / Story Card AC01-AC07；dev_gate = Wave A/B/C 全部 verified |
| 6 | clarification queue 已收敛 | 待检查 | §12.1：所有设计决策已在 LLD 中确定，无 OPEN / Spike 项，无需用户决策的灰区 |

**人工确认回复**：

请直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```

- `approve`：LLD 设计合理，允许进入实现。
- `修改: <具体修改点>`：指出具体修改点后由 meta-dev 更新重提。
- `reject`：设计方向有根本问题，需重新设计。
- Codex 历史别名 `1/通过`、`2/修改: ...`、`3/不通过` 仅作兼容解析；新提示不得把多个别名混排为主要选项。

**人工审查结果回填**：

- 结论：`approved | changes_requested | rejected`
- 审查人：
- 审查时间：
- 修改意见：
- 风险接受项：
