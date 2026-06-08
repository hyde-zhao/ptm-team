---
change_id: CR-012-ptm-tde-mfq-phase
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-01T12:00:00+08:00"
updated_at: "2026-06-02T23:00:00+08:00"
created_by: meta-po
status: closed
impact_level: high
rollback_to: story-execution
approval_source: user-request（扩展范围：纳入 mfq-analysis-step-by-step.md v3.0 全部方法论）
depends_on: CR-010-ptm-tde三阶段框架改造
followed_by: CR-013-ptm-tde-ppdcs-phase
---

# CR-012 — ptm-tde MFQ 阶段改造（内容层，扩展范围）

## 变更请求摘要

**范围已扩展**（2026-06-02）：原始范围仅覆盖路径迁移 + 方法论占位 + Gate 增强。用户选择将设计文档 `mfq-analysis-step-by-step.md`（v3.0）的全部方法论纳入本次 CR，包括：

1. **路径迁移**：5 个 Skill 文件中 `analysis/` → `mfq/` / `kym/`（~70 处）
2. **M 分析器 v3.0 重写**：7步→10步，场景步骤驱动的对象/因子/原子操作发现模式，新增 Scenario-TSP 覆盖矩阵和步骤标签实体
3. **F 分析器 v3.0 重写**：8步→9步，改为逐 TSP 驱动耦合分析，消费 M 分析的 [F→] 标签作为种子线索
4. **Q 分析器 v3.0 重写**：5步→6步，改为逐 TSP 驱动质量分析，消费 M 分析的 [Q→] 标签作为补充依据
5. **候选汇总流程**：M/F/Q 三源候选合并 + 用户批量确认
6. **MFQ Exit Gate 增强**：自检项编号改为 M1-M7 + W1-W2 前缀
7. **上下游 Skill 适配**：test-point-integrator + design-planner 适配新数据格式

**设计文档**：`/home/hyde/projects/llm-wiki/llm-wiki/work/studies/ptm-team/team-design/ptm-tde/mfq-analysis-step-by-step.md`（v3.0，2026-06-02）

**依赖**：CR-010（框架改造）已 closed（CP7 已修复为 PASS）。

## 背景

### MFQ 阶段在框架中的位置

```
... → KYM Exit Gate → [MFQ Phase] → MFQ Exit Gate（自检+人工，新增） → PPDCS Phase → ...
                          │
                          ├─ 子步骤 2.1: m-analyzer
                          ├─ 子步骤 2.2: f-analyzer
                          ├─ 子步骤 2.3: q-analyzer
                          ├─ 子步骤 2.4: test-point-integrator
                          └─ 子步骤 2.5: design-planner
```

### 本 CR 的三项工作

1. **路径迁移**：MFQ 阶段涉及的 5 个 Skill + 跨阶段 `process/plan/` 路径更新
2. **方法论充实**：M/F/Q 分析器增加方法论占位节（用户后续补充具体内容）
3. **MFQ Exit Gate 增强**：补充新增人工门的自检和人工检查项

## 一、路径迁移

### 受影响 Skill 文件

| Skill 文件 | 路径引用更新 | 改动量 |
|-----------|-------------|--------|
| `skills/m-analyzer/SKILL.md` | `analysis/feature-input/` → `kym/feature-input/`、`analysis/scenarios/` → `kym/scenarios/`、`analysis/m-analysis/` → `mfq/m-analysis/`、`analysis/factor-usage/` → `mfq/factor-usage/`（~18 处） | ~18 |
| `skills/f-analyzer/SKILL.md` | `analysis/m-analysis/` → `mfq/m-analysis/`、`analysis/scenarios/` → `kym/scenarios/`、`analysis/f-analysis/` → `mfq/f-analysis/`（~10 处） | ~10 |
| `skills/q-analyzer/SKILL.md` | `analysis/m-analysis/` → `mfq/m-analysis/`、`analysis/scenarios/` → `kym/scenarios/`、`analysis/q-analysis/` → `mfq/q-analysis/`（~4 处） | ~4 |
| `skills/test-point-integrator/SKILL.md` | `analysis/m-analysis/` → `mfq/m-analysis/`、`analysis/f-analysis/` → `mfq/f-analysis/`、`analysis/q-analysis/` → `mfq/q-analysis/`、`analysis/scenarios/` → `kym/scenarios/`、`analysis/integration/` → `mfq/integration/`、`analysis/factor-usage/` → `mfq/factor-usage/`（~12 处） | ~12 |
| `skills/design-planner/SKILL.md` | `analysis/integration/` → `mfq/integration/`、`analysis/plan/` → `process/plan/`、`analysis/m-analysis/` → `mfq/m-analysis/`、`analysis/factor-usage/` → `mfq/factor-usage/`（~6 处） | ~6 |

### 路径迁移映射（MFQ 阶段专用）

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `analysis/feature-input/` | `kym/feature-input/` | 跨阶段读取 KYM 产出 |
| `analysis/scenarios/` | `kym/scenarios/` | 跨阶段读取 KYM 产出 |
| `analysis/m-analysis/` | `mfq/m-analysis/` | MFQ 阶段内部 |
| `analysis/f-analysis/` | `mfq/f-analysis/` | MFQ 阶段内部 |
| `analysis/q-analysis/` | `mfq/q-analysis/` | MFQ 阶段内部 |
| `analysis/integration/` | `mfq/integration/` | MFQ 阶段内部 |
| `analysis/factor-usage/` | `mfq/factor-usage/` | MFQ 阶段内部 |
| `analysis/plan/` | `process/plan/` | 跨阶段边界产物 |

### 注意事项

- `design-planner` 属 MFQ 阶段（子步骤 2.5），但其输出 `plan/` 放在 `process/plan/`（跨阶段边界），不是 `mfq/plan/`。
- MFQ Skill 引用 `kym/scenarios/confirmed-scenarios.md` 属于跨阶段读取，路径指向 KYM 阶段产出。
- 本 CR 不触碰 PPDCS 路径（`design/ppdcs/`、`design/pc/`、`analysis/coverage/`），由 CR-013 处理。

## 二、方法论充实

### 更新文件

| 文件 | 新增内容 | 改动量 |
|------|----------|--------|
| `skills/m-analyzer/SKILL.md` | M 分析方法论占位节 | ~15 |
| `skills/f-analyzer/SKILL.md` | F 分析方法论占位节 | ~12 |
| `skills/q-analyzer/SKILL.md` | Q 分析方法论占位节 | ~12 |

### 方法论占位格式（统一模板）

每个方法论占位节使用以下格式，用户后续补充具体内容：

```markdown
### 方法论细则（用户可定制）

> 以下为分析方法的指导框架。用户可根据项目特点和领域知识补充具体规则。

#### [方法名称]

**目标**：[方法要解决什么问题]

**核心步骤**：
1. [步骤1]
2. [步骤2]
3. ...

**示例**（防火墙领域）：
[具体示例]

**下游影响**：
[该方法论的输出如何影响后续 Skill]
```

### M 分析方法论占位维度

| 占位项 | 说明 |
|--------|------|
| PPDCS 特征标注策略 | 如何判断一个单功能属于 P/P/D/C/S 哪种特征 |
| CAE 测试点生成指导 | C/A/E 三元组的编写规则和质量标准 |
| 因子提取规则 | 从单功能中提取测试因子的方法和约束 |
| 因子绑定策略 | 如何将因子与 PPDCS 特征关联 |
| 拓扑角色提取规则 | 如何从场景中提取 topology_role_refs |

### F 分析方法论占位维度

| 占位项 | 说明 |
|--------|------|
| 耦合识别规则 | 如何识别功能间的耦合关系（顺序/容忍/数据/接口资源） |
| 三源合并策略 | Excel 矩阵 + 场景耦合 + 代码依赖如何合并去重 |
| 耦合测试点生成指导 | 耦合 CAE 的编写规则 |

### Q 分析方法论占位维度

| 占位项 | 说明 |
|--------|------|
| HTSM 维度评估规则 | 如何评估各质量维度的相关性（强/弱/无关） |
| 质量测试点生成指导 | 质量 CAE 的编写规则 |
| 质量与功能测试的边界 | Q 分析何时独立产出、何时合并到 M 分析 |

## 三、MFQ Exit Gate 增强

### 更新文件

| 文件 | 改动 |
|------|------|
| `docs/ptm-tde/gate-spec.md` | MFQ Exit Gate 增加：自检项 + 人工确认项 |
| `skills/checkpoint-manager/SKILL.md` | 增加 MFQ Exit Gate 专用检查项 |

### MFQ Exit Gate 自检项

| # | 检查项 | 通过条件 |
|---|--------|----------|
| M1 | M 分析输出完整 | `mfq/m-analysis/test-points.md` 和 `mfq/m-analysis/ppdcs-annotation.md` 存在且非空 |
| M2 | F 分析输出完整 | `mfq/f-analysis/coupling-test-points.md` 存在且非空 |
| M3 | Q 分析输出完整 | `mfq/q-analysis/quality-test-points.md` 存在且非空 |
| M4 | 测试点整合完成 | `mfq/integration/logic-cases.md` 存在，LC 包含 factor_bindings 和 topology_bindings |
| M5 | 设计计划产出 | `process/plan/design-plan.md` 存在，每个 LC 有 PPDCS 方法推荐 |
| M6 | 因子库消费闭环 | `mfq/factor-usage/factor-library-lock.yaml` 存在；无未解析的 candidate 提案，或已记录为 confirmation_gaps |
| M7 | 拓扑链路连续 | M 分析 CAE 只包含 topology_role_refs（无真实端口）；LC topology_bindings 来源可追溯到 `kym/scenarios/confirmed-scenarios.md` |
| W1 | KYM 场景覆盖 Warning | M/F/Q 测试点是否覆盖了 KYM 阶段确认的全部场景（非阻断） |
| W2 | PPDCS 数据充足 Warning | MFQ 产出是否包含 PPDCS 所需的全部数据字段（非阻断） |

### MFQ Exit Gate 人工确认项

| 确认项 | 说明 |
|--------|------|
| M 分析覆盖 | 单功能拆分是否完整，PPDCS 标注是否合理 |
| F 分析覆盖 | 耦合关系是否遗漏，三源合并是否准确 |
| Q 分析覆盖 | 质量维度评估是否全面，HTSM 裁剪是否合理 |
| LC 与因子绑定 | 逻辑用例是否合理，因子绑定是否正确 |
| PPDCS 方法推荐 | CAE→PPDCS 推断是否合理，直接分析法比例是否 <5% |
| 因子库消费 | 公共因子复用是否充分，候选提案是否合理 |

## 四、Story 分解（扩展范围）

### 依赖关系

```
Wave A（并行，tier=S）
  ├── STORY-012-01：路径迁移（5 Skill ~70 处）
  └── STORY-012-02：Gate 增强（M1-M7 编号）
       │
       ▼
Wave B（tier=M）
  └── STORY-012-03：M 分析器 v3.0 重写（7步→10步，场景步骤驱动）
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
Wave C（并行，tier=M）
  ├── STORY-012-04：F 分析器 v3.0 重写（逐 TSP 驱动）
  └── STORY-012-05：Q 分析器 v3.0 重写（逐 TSP 驱动）
       │
       ▼
Wave D（tier=M/S）
  ├── STORY-012-06：上下游适配（integrator + design-planner）
  ├── STORY-012-07：候选汇总 + skill-references
  └── STORY-012-08：文档更新
```

### Story 清单

| # | Story ID | 名称 | tier | Wave | 文件数 | 改动量 |
|---|----------|------|------|------|--------|--------|
| 1 | STORY-012-01 | MFQ 路径迁移 | S | A | 5 | ~70 处 |
| 2 | STORY-012-02 | MFQ Exit Gate 增强 | S | A | 2 | ~25 行 |
| 3 | STORY-012-03 | M 分析器 v3.0 重写 | M | B | 1 | ~200 行 |
| 4 | STORY-012-04 | F 分析器 v3.0 重写 | M | C | 1 | ~150 行 |
| 5 | STORY-012-05 | Q 分析器 v3.0 重写 | M | C | 1 | ~120 行 |
| 6 | STORY-012-06 | 上下游 Skill 适配 | M | D | 2 | ~50 行 |
| 7 | STORY-012-07 | 候选汇总 + skill-references | M | D | 2 | ~30 行 |
| 8 | STORY-012-08 | 文档更新 | S | D | 3 | ~30 行 |

### 各 Story 验收标准

**STORY-012-01（路径迁移）**：
- `grep -rn "analysis/" skills/{m,f,q}-analyzer/ skills/test-point-integrator/ skills/design-planner/` 返回 0
- 所有新路径 (`mfq/`, `kym/`, `process/plan/`) 在文件中存在

**STORY-012-02（Gate 增强）**：
- gate-spec.md GATE-3 Checklist 使用 M1-M7 + W1-W2 编号前缀
- checkpoint-manager SKILL.md GATE-3 同步一致

**STORY-012-03（M 分析器 v3.0）**：
- 12 项验收标准（见设计文档 §M 分析验收标准）
- 覆盖矩阵双视角（视角 A + 视角 B）
- 场景步骤标签 [M]/[F→]/[Q→] 产出

**STORY-012-04（F 分析器 v3.0）**：
- 逐 TSP 驱动模式，消费 [F→] 标签种子
- 耦合因子候选列表标注 tsp_ref
- 测试点按 TSP 组织

**STORY-012-05（Q 分析器 v3.0）**：
- 逐 TSP 驱动模式，消费 [Q→] 标签补充
- 质量因子候选列表标注 tsp_ref
- 测试点按 TSP 组织

**STORY-012-06（上下游适配）**：
- test-point-integrator 消费覆盖矩阵和新 M/F/Q 格式
- design-planner 适配 TSP.covered_scenario_segments

**STORY-012-07（候选汇总）**：
- 候选汇总功能就绪（内嵌到 test-point-integrator）
- skill-references.md 更新

**STORY-012-08（文档）**：
- CR-INDEX.yaml、STATE.md 更新
- ptm-tde Agent 文件 MFQ 阶段引用更新

## 受影响文件汇总

| 文件 | 变更类型 | Story |
|------|----------|-------|
| `skills/m-analyzer/SKILL.md` | 路径迁移 + v3.0 重写 | 012-01, 012-03 |
| `skills/f-analyzer/SKILL.md` | 路径迁移 + v3.0 重写 | 012-01, 012-04 |
| `skills/q-analyzer/SKILL.md` | 路径迁移 + v3.0 重写 | 012-01, 012-05 |
| `skills/test-point-integrator/SKILL.md` | 路径迁移 + 适配 + 候选汇总 | 012-01, 012-06, 012-07 |
| `skills/design-planner/SKILL.md` | 路径迁移 + 适配 | 012-01, 012-06 |
| `docs/ptm-tde/gate-spec.md` | MFQ Exit Gate 增强 | 012-02 |
| `skills/checkpoint-manager/SKILL.md` | MFQ Exit Gate 增强 | 012-02 |
| `skills/README.md` | 候选汇总注册 | 012-07 |
| `docs/ptm-tde/skill-references.md` | 引用关系更新 | 012-07 |
| `agents/ptm-tde.md` | MFQ 阶段引用更新 | 012-08 |

## 验证方法

### 路径迁移验证
```bash
grep -rn "analysis/m-analysis\|analysis/f-analysis\|analysis/q-analysis\|analysis/integration\|analysis/factor-usage" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/ skills/design-planner/
# 期望：0 结果

grep -rn "analysis/scenarios\|analysis/feature-input" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/
# 期望：0 结果
```

### Gate 增强验证
```bash
grep -c "M[1-7]\|W[1-2]" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md
# 期望：两个文件均存在 M1-M7 + W1-W2 引用
```

### M/F/Q 方法论验证
- M 分析器：12 项验收标准全部通过（见设计文档 §M 分析验收标准）
- F 分析器：逐 TSP 驱动模式，F 线索消费正确
- Q 分析器：逐 TSP 驱动模式，Q 线索消费正确

## 实施记录

| 时间 | 事件 |
|------|------|
| 2026-06-01 | CR 创建，状态 draft（原始范围：路径迁移+方法论占位+Gate） |
| 2026-06-02T21:00 | 用户批准扩展范围（纳入 mfq-analysis-step-by-step.md v3.0 全部方法论），impact_level medium→high |
| 2026-06-02T21:00 | CR-010 CP7 修复（checkpoint-spec.md → 561B 重定向页），CR-010 closed |
| 2026-06-02T21:00 | CR-012 范围更新完成，Story 分解 8 Stories / 4 Waves，进入 story-execution |
| 2026-06-02T23:00 | CR-012 closed：8 Stories / 4 Waves 全部完成。MFQ v3.0 方法论落地：M 分析 10 步（场景步骤驱动，产出覆盖矩阵+步骤标签）、F 分析 9 步（逐 TSP 驱动，消费 [F→] 标签）、Q 分析 6 步（逐 TSP 驱动，消费 [Q→] 标签）、候选汇总（⛔ HARD-STOP 确认）、GATE-3 增强（M1-M7+W1-W2 编号）。全部 Story CP7 verified。 |
