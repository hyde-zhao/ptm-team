---
change_id: CR-013-ptm-tde-ppdcs-phase
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-01T12:00:00+08:00"
created_by: meta-po
status: closed
impact_level: medium
strategy: fast-lane（路径修正）+ standard（剩余范围）
closed_at: "2026-06-04T00:00:00+08:00"
closed_by: meta-po（po-zhao）
rollback_to: story-execution
approval_source: user-request
depends_on: CR-010-ptm-tde三阶段框架改造
followed_by: n/a
---

# CR-013 — ptm-tde PPDCS 阶段改造（内容层）

## 变更请求摘要

完成 PPDCS 阶段的全部内容层改造：迁移 PPDCS 阶段相关 Skill 的路径引用（`design/` → `ppdcs/`，`analysis/coverage/` → `ppdcs/coverage/`，`delivery/` → `ppdcs/delivery/`），充实 5 个 PPDCS 设计 Skill 的方法论内容（占位框架），补充 PPDCS Exit Gate 的阶段专属检查项。

**依赖**：CR-010（框架改造）必须已完成。

**注意**：本 CR 完成后，所有 Skill 的路径迁移已完成，可以安全删除旧的 `analysis/` 和 `design/` 目录。

## 背景

### PPDCS 阶段在框架中的位置

```
... → MFQ Exit Gate → [PPDCS Phase] → PPDCS Exit Gate → Exit Gate
                          │
                          ├─ 子步骤 3.1: design-ppdcs-analyzer + 5设计Skill
                          ├─ 子步骤 3.2: 5设计Skill → PC生成
                          ├─ 子步骤 3.3: coverage-verifier
                          └─ 子步骤 3.4: deliverable-renderer
```

### 本 CR 的四项工作

1. **路径迁移**：PPDCS 阶段涉及的 8 个 Skill 的路径更新
2. **方法论充实**：5 个 PPDCS 设计 Skill 增加方法论占位节（用户后续补充具体内容）
3. **PPDCS Exit Gate 增强**：补充设计过程和覆盖率的检查项
4. **旧目录清理**：删除 `analysis/` 和 `design/` 目录（附 README-DEPRECATED.md）

## 一、路径迁移

### 受影响 Skill 文件

| Skill 文件 | 路径引用更新 | 改动量 |
|-----------|-------------|--------|
| `skills/design-ppdcs-analyzer/SKILL.md` | `analysis/integration/` → `mfq/integration/`、`analysis/plan/` → `process/plan/`、`analysis/scenarios/` → `kym/scenarios/`、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`（~8 处） | ~8 |
| `skills/process-design/SKILL.md` | `analysis/integration/` → `mfq/integration/`、`analysis/plan/` → `process/plan/`、`analysis/scenarios/` → `kym/scenarios/`、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`（~9 处） | ~9 |
| `skills/parameter-design/SKILL.md` | `analysis/integration/` → `mfq/integration/`、`analysis/plan/` → `process/plan/`、`analysis/m-analysis/` → `mfq/m-analysis/`、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`（~7 处） | ~7 |
| `skills/data-design/SKILL.md` | 同 parameter-design 模式（~7 处） | ~7 |
| `skills/combination-design/SKILL.md` | 同 parameter-design 模式（~7 处） | ~7 |
| `skills/state-design/SKILL.md` | `analysis/integration/` → `mfq/integration/`、`analysis/plan/` → `process/plan/`、`analysis/scenarios/` → `kym/scenarios/`、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`（~9 处） | ~9 |
| `skills/coverage-verifier/SKILL.md` | `analysis/scenarios/` → `kym/scenarios/`、`analysis/integration/` → `mfq/integration/`、`analysis/factor-usage/` → `mfq/factor-usage/`、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`、`analysis/coverage/` → `ppdcs/coverage/`（~13 处） | ~13 |
| `skills/deliverable-renderer/SKILL.md` | `analysis/` → 分阶段路径、`design/ppdcs/` → `ppdcs/ppdcs/`、`design/pc/` → `ppdcs/pc/`、`analysis/coverage/` → `ppdcs/coverage/`、`delivery/` → `ppdcs/delivery/`、`analysis/scenarios/` → `kym/scenarios/`（~11 处） | ~11 |

### 路径迁移映射（PPDCS 阶段专用）

| 旧路径 | 新路径 | 说明 |
|--------|--------|------|
| `analysis/integration/` | `mfq/integration/` | 跨阶段读取 MFQ 产出 |
| `analysis/plan/` | `process/plan/` | 跨阶段读取设计计划 |
| `analysis/m-analysis/` | `mfq/m-analysis/` | 跨阶段读取 M 分析产出 |
| `analysis/scenarios/` | `kym/scenarios/` | 跨阶段读取 KYM 产出 |
| `analysis/factor-usage/` | `mfq/factor-usage/` | 跨阶段读取因子库记录 |
| `analysis/coverage/` | `ppdcs/coverage/` | PPDCS 阶段内部 |
| `design/ppdcs/` | `ppdcs/ppdcs/` | PPDCS 阶段内部 |
| `design/pc/` | `ppdcs/pc/` | PPDCS 阶段内部 |
| `delivery/` | `ppdcs/delivery/` | PPDCS 阶段内部 |

### 注意事项

- `coverage-verifier` 是跨阶段读取最多的 Skill（读 kym + mfq + ppdcs），改动量最大（~13 处）。
- `deliverable-renderer` 消费所有阶段产出，`delivery/` → `ppdcs/delivery/` 是关键变更。
- 本 CR 完成后，全部 18 个 Skill 的路径迁移完毕，`analysis/` 和 `design/` 目录不再有任何 Skill 引用。

## 二、方法论充实

### 更新文件

| 文件 | 新增内容 | 改动量 |
|------|----------|--------|
| `skills/process-design/SKILL.md` | P-Process 方法论占位节 | ~10 |
| `skills/parameter-design/SKILL.md` | P-Parameter 方法论占位节 | ~10 |
| `skills/data-design/SKILL.md` | D-Data 方法论占位节 | ~10 |
| `skills/combination-design/SKILL.md` | C-Combination 方法论占位节 | ~10 |
| `skills/state-design/SKILL.md` | S-State 方法论占位节 | ~10 |

### 方法论占位格式（统一模板）

```markdown
### 方法论细则（用户可定制）

> 以下为设计方法的指导框架。用户可根据项目特点和领域知识补充具体规则。

#### [方法名称] 设计步骤与方法

**目标**：[方法解决什么设计问题]

**核心步骤**：
1. [步骤1]
2. [步骤2]
3. ...

**关键决策点**：
- [决策1：何时选择此方法]
- [决策2：如何处理边界情况]

**示例**（防火墙领域）：
[具体示例]

**下游影响**：
[设计产出如何影响 PC 生成和覆盖率验证]
```

### 各设计 Skill 方法论占位维度

| Skill | 占位维度 |
|-------|----------|
| process-design | 流程图构建规则、路径枚举策略、触发数据分配规则 |
| parameter-design | 约束提取规则、规则组合矩阵构建、参数组分配规则、判定表 vs 因果图 vs 决策树选择 |
| data-design | 等价类划分规则、边界值选取策略（三点法）、数据 vs 组合判定规则 |
| combination-design | 因子识别规则、约束建模规则、压缩策略选择（Pairwise/正交/全组合）、PICT 模型文件构建 |
| state-design | 状态识别规则、迁移表构建、守卫条件提取、状态路径枚举、合法 vs 非法迁移区分 |

## 三、PPDCS Exit Gate 增强

### 更新文件

| 文件 | 改动 |
|------|------|
| `docs/ptm-tde/gate-spec.md` | PPDCS Exit Gate 增加：设计过程自检项 + PC 完整性自检项 + 覆盖率验证自检项 + 人工确认项 |
| `skills/checkpoint-manager/SKILL.md` | 增加 PPDCS Exit Gate 专用检查项 |

### PPDCS Exit Gate 自检项

| # | 检查项 | 通过条件 |
|---|--------|----------|
| P1 | PPDCS 设计过程完整 | `ppdcs/ppdcs/` 下每个 LC 都有设计过程文件，PPDCS 方法与 plan 推荐一致 |
| P2 | PC 文件完整 | `ppdcs/pc/` 下每个 LC 都有物理用例文件，16 列格式正确 |
| P3 | PC 拓扑绑定回链 | PC 中所有真实设备、端口、链路能回链到 LC `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` |
| P4 | 双层覆盖率验证 | `ppdcs/coverage/` 存在覆盖率报告：需求覆盖 = 100%，测试点覆盖 ≥ 95% |
| P5 | 因子覆盖验证 | 所有 `factor_bindings` 的因子在 PC 中有覆盖 |
| P6 | 交付物完整 | `ppdcs/delivery/` 包含且仅包含测试方案和测试用例两个文件 |
| P7 | 交付物字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

### PPDCS Exit Gate 人工确认项

| 确认项 | 说明 |
|--------|------|
| PPDCS 设计方法 | 每个 LC 的 PPDCS 方法选择是否合理，设计步骤是否完整 |
| 物理用例质量 | PC 编号、组网描述、测试步骤、预期结果是否满足标准 |
| 覆盖率结果 | 需求覆盖率、测试点覆盖率是否达标，未覆盖项是否可接受 |
| 拓扑绑定 | needs-confirmation 项是否已处理或记录为风险 |

## 四、旧目录清理

本 CR 完成所有 Skill 路径迁移后，删除旧目录：

| 操作 | 说明 |
|------|------|
| 删除 `analysis/` | 所有子目录已迁移到 `kym/`、`mfq/`、`ppdcs/`、`process/plan/` |
| 删除 `design/` | 所有子目录已迁移到 `ppdcs/ppdcs/`、`ppdcs/pc/` |

删除前执行验证：
```bash
grep -rn "analysis/" skills/ | grep -v "kym/\|mfq/\|ppdcs/\|process/"
grep -rn "design/" skills/ | grep -v "ppdcs/"
```
两条命令均返回 0 结果后方可删除。

## 受影响文件汇总

| 文件 | 变更类型 |
|------|----------|
| `skills/design-ppdcs-analyzer/SKILL.md` | 路径更新 |
| `skills/process-design/SKILL.md` | 路径更新 + 方法论占位节 |
| `skills/parameter-design/SKILL.md` | 路径更新 + 方法论占位节 |
| `skills/data-design/SKILL.md` | 路径更新 + 方法论占位节 |
| `skills/combination-design/SKILL.md` | 路径更新 + 方法论占位节 |
| `skills/state-design/SKILL.md` | 路径更新 + 方法论占位节 |
| `skills/coverage-verifier/SKILL.md` | 路径更新 |
| `skills/deliverable-renderer/SKILL.md` | 路径更新 |
| `docs/ptm-tde/gate-spec.md` | PPDCS Exit Gate 增加检查项 |
| `skills/checkpoint-manager/SKILL.md` | 增加 PPDCS Exit Gate 检查项 |
| `analysis/` | 删除（全部子目录已迁移） |
| `design/` | 删除（全部子目录已迁移） |

## 验证方法

1. `grep -rn "analysis/\|design/" skills/ | grep -v "kym/\|mfq/\|ppdcs/\|process/"` 返回 0 结果（全部 Skill 旧路径已迁移）
2. `ls analysis/ 2>/dev/null && echo "FAIL: analysis/ still exists" || echo "PASS: analysis/ removed"`
3. `ls design/ 2>/dev/null && echo "FAIL: design/ still exists" || echo "PASS: design/ removed"`
4. 每个 PPDCS 设计 Skill 保留所有原始章节不变，方法论占位节使用统一格式
5. `docs/ptm-tde/gate-spec.md` 中 PPDCS Exit Gate 包含 P1-P7 自检项 + 人工确认项
6. `skills/checkpoint-manager/SKILL.md` 包含 PPDCS Exit Gate 专用检查项

## 实施记录

| 时间 | 事件 |
|------|------|
| 2026-06-01 | CR 创建，状态 draft |
