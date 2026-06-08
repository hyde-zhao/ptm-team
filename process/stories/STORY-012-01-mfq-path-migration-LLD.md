---
story_id: STORY-012-01
story_name: MFQ 路径迁移
lld_version: "1.0"
lld_status: draft
author: meta-dev
created_at: "2026-06-02"
confirmed: true
tier: S
wave: A
---

# STORY-012-01 LLD：MFQ 路径迁移

## 1. Story 信息

| 字段 | 值 |
|------|-----|
| Story ID | STORY-012-01 |
| Story 名称 | MFQ 路径迁移 |
| 所属变更 | CR-012-ptm-tde-mfq-phase |
| Tier | S（小型，~70 处路径替换，0 行净增） |
| Wave | A |
| 上游依赖 | 无 |
| 下游被依赖 | STORY-012-03, 012-04, 012-05, 012-06, 012-07 |
| 并行安全 | 是（与 STORY-012-02 无文件冲突） |
| 设计确认 | HLD v1.1 confirmed=true（CP3 人工确认通过） |

### Goal

将 5 个 MFQ Skill 文件中所有硬编码的 `analysis/` 路径前缀替换为 CR-010 建立的三阶段目录结构（`kym/` / `mfq/` / `process/plan/`），确保旧路径零残留，新路径与 HLD §9 模块职责和 HLD §15 分阶段落地计划一致。

### Requirements

| 类型 | 要求 |
|------|------|
| Functional | 8 条路径映射全部执行（见下表），旧路径零残留 |
| Functional | 替换后 Skill 文件的 YAML frontmatter 未被损坏 |
| Functional | 替换后 Skill 的业务逻辑、步骤编号、方法论内容不变 |
| Non-Functional | 行数变化 ≤ ±5 行（纯替换，不增删行） |
| Non-Functional | 每个 Skill 文件至少包含对应新路径引用 |
| Compatibility | 不改动 KYM 阶段 Skill 和 PPDCS 阶段 Skill |

### 路径迁移映射（来自 CR-012 / HLD §1）

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

---

## 2. 文件影响范围

| 文件 | 变更类型 | ~旧路径出现次数 | 涉及旧路径 |
|------|----------|:---:|------|
| `skills/m-analyzer/SKILL.md` | 修改 | 18 | `analysis/feature-input/`、`analysis/scenarios/`、`analysis/m-analysis/`、`analysis/factor-usage/` |
| `skills/f-analyzer/SKILL.md` | 修改 | 16 | `analysis/m-analysis/`、`analysis/scenarios/`、`analysis/f-analysis/` |
| `skills/q-analyzer/SKILL.md` | 修改 | 7 | `analysis/m-analysis/`、`analysis/scenarios/`、`analysis/q-analysis/` |
| `skills/test-point-integrator/SKILL.md` | 修改 | 11 | `analysis/m-analysis/`、`analysis/f-analysis/`、`analysis/q-analysis/`、`analysis/integration/`、`analysis/scenarios/` |
| `skills/design-planner/SKILL.md` | 修改 | 17 | `analysis/integration/`、`analysis/m-analysis/`、`analysis/plan/` |

**文件所有权**：`file_ownership` 中 5 个文件均属于本 Story，不与任何其他 `dev_running` Story 冲突。

**不改动的文件**：
- `skills/checkpoint-manager/SKILL.md`（STORY-012-02 所有）
- `docs/ptm-tde/gate-spec.md`（STORY-012-02 所有）
- `agents/ptm-tde.md`（由后续 Story 适配）
- `docs/ptm-tde/skill-references.md`（由 STORY-012-07 适配）

---

## 3. 数据模型

本 Story 无新增数据实体。仅做路径文本替换，不涉及数据结构变更。

---

## 4. 接口与契约

### 4.1 路径替换规则

| 规则 ID | 规则 | 优先级 | 示例 |
|---------|------|--------|------|
| R01 | `analysis/feature-input/` → `kym/feature-input/` | 标准 | `analysis/feature-input/raw-requirements.md` → `kym/feature-input/raw-requirements.md` |
| R02 | `analysis/scenarios/` → `kym/scenarios/` | 标准 | `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md` |
| R03 | `analysis/m-analysis/` → `mfq/m-analysis/` | 标准 | `analysis/m-analysis/test-points.md` → `mfq/m-analysis/test-points.md` |
| R04 | `analysis/f-analysis/` → `mfq/f-analysis/` | 标准 | `analysis/f-analysis/coupling-test-points.md` → `mfq/f-analysis/coupling-test-points.md` |
| R05 | `analysis/q-analysis/` → `mfq/q-analysis/` | 标准 | `analysis/q-analysis/quality-test-points.md` → `mfq/q-analysis/quality-test-points.md` |
| R06 | `analysis/integration/` → `mfq/integration/` | 标准 | `analysis/integration/logic-cases.md` → `mfq/integration/logic-cases.md` |
| R07 | `analysis/factor-usage/` → `mfq/factor-usage/` | 标准 | `analysis/factor-usage/factor-library-lock.yaml` → `mfq/factor-usage/factor-library-lock.yaml` |
| R08 | `analysis/plan/` → `process/plan/` | **特殊**（跨阶段边界） | `analysis/plan/design-planner-reasoning.md` → `process/plan/design-planner-reasoning.md` |

### 4.2 替换顺序

替换顺序**不重要**——8 条规则的目标路径互不重叠，不存在替换 A 导致替换 B 误匹配的问题。实现时从最长前缀开始替换（如先替换 `analysis/feature-input/`，后替换 `analysis/scenarios/`），可进一步提高安全性。

### 4.3 design-planner 特殊处理

`analysis/plan/` → `process/plan/` 是仅有的跨阶段边界替换。此替换仅出现在 `design-planner/SKILL.md` 中，确保替换后引用 `process/plan/design-plan.md` 和 `process/plan/design-planner-reasoning.md`，而非 `mfq/plan/`。

### 4.4 契约不变项

- Skill 的 YAML frontmatter（`name`、`description`、`argument-hint` 等）不因路径替换而修改
- Skill 的步骤编号（步骤 1-7/8/5/8/6）不变
- Skill 的方法论内容（PPDCS 特征定义、HTSM 维度、CAE 三元组格式等）不变
- Skill 的触发词、Gotchas、验收标准条目不变

---

## 5. 详细执行流程

### 流程图

```
开始
  │
  ├──→ 步骤 1: 备份现状（git stash 或 branch）
  │
  ├──→ 步骤 2: 按文件依次执行路径替换
  │     │
  │     ├──→ ST101: 处理 m-analyzer/SKILL.md（8 条规则逐一 sed）
  │     ├──→ ST102: 处理 f-analyzer/SKILL.md（8 条规则逐一 sed）
  │     ├──→ ST103: 处理 q-analyzer/SKILL.md（8 条规则逐一 sed）
  │     ├──→ ST104: 处理 test-point-integrator/SKILL.md（8 条规则逐一 sed）
  │     └──→ ST105: 处理 design-planner/SKILL.md（8 条规则逐一 sed）
  │
  ├──→ 步骤 3: 验证（AC01-AC08 全部 grep 命令）
  │     │
  │     ├── PASS → 步骤 4
  │     └── FAIL → 根据 grep 残留结果修正 → 重新步骤 3
  │
  └──→ 步骤 4: 输出 CP6 自检结果
```

### 步骤 2 详细：逐文件 sed 替换

每个 Skill 文件对 8 条路径规则依次执行 `sed` 替换。伪代码：

```bash
for FILE in skills/m-analyzer/SKILL.md \
            skills/f-analyzer/SKILL.md \
            skills/q-analyzer/SKILL.md \
            skills/test-point-integrator/SKILL.md \
            skills/design-planner/SKILL.md; do
  sed -i 's|analysis/feature-input/|kym/feature-input/|g' "$FILE"
  sed -i 's|analysis/scenarios/|kym/scenarios/|g' "$FILE"
  sed -i 's|analysis/m-analysis/|mfq/m-analysis/|g' "$FILE"
  sed -i 's|analysis/f-analysis/|mfq/f-analysis/|g' "$FILE"
  sed -i 's|analysis/q-analysis/|mfq/q-analysis/|g' "$FILE"
  sed -i 's|analysis/integration/|mfq/integration/|g' "$FILE"
  sed -i 's|analysis/factor-usage/|mfq/factor-usage/|g' "$FILE"
  sed -i 's|analysis/plan/|process/plan/|g' "$FILE"
done
```

**替换安全性保证**：
- 每个 sed 使用 `|` 分隔符避免路径中 `/` 的转义问题
- 替换目标路径互不重叠（`kym/`、`mfq/`、`process/` 互不包含）
- `analysis/scenarios/` 替换为 `kym/scenarios/` 不会与 `analysis/m-analysis/`、`analysis/f-analysis/` 等替换冲突——后者已先被替换为 `mfq/m-analysis/` 等，不会残留 `analysis/scenarios/` 串

### 步骤 3 验证流程

执行 AC01-AC08 全部验证命令，任一项 FAIL 即回到步骤 2 修正。

### 步骤 4 CP6 自检

生成 `process/checks/CP6-STORY-012-01-mfq-path-migration-CODING-DONE.md`，记录逐项检查结果。

---

## 6. 异常处理

| 异常场景 | 检测方式 | 处理 | 阻断级别 |
|---------|---------|------|---------|
| sed 替换后文件为空 | `wc -l` 检查文件行数 | 从 git 恢复文件，排查 sed 错误并重试 | BLOCKING |
| 替换后行数变化 > ±5 | `wc -l` 对比替换前后 | 逐文件排查是否有意外的行增删 | BLOCKING |
| frontmatter 损坏（`---` 计数 ≠ 10） | AC06 grep 验证 | 检查 frontmatter 中是否 `description` 字段包含路径被错误替换 | BLOCKING |
| 旧路径残留 | AC01/AC02/AC03/AC07 grep | 针对残留文件追加 sed 替换 | BLOCKING |
| design-planner 的 plan 路径被错误替换为 mfq | AC05 grep 加人工检查 | 确认 `process/plan/` 出现且 `mfq/plan/` 不出现 | BLOCKING |
| 替换后 Skill 引用不存在的路径 | 对照 CR-010 建立的目录结构 | 若属于 CR-010 尚未创建的目录，记录为已知限制 | WARNING |

**失败回退策略**：任一 BLOCKING 项触发，从 git 恢复所有 5 个文件到替换前状态，修正 sed 策略后重试。

---

## 7. 测试设计

### 7.1 自动化验收测试（8 项）

| AC | 命令 | 预期结果 | 接口覆盖 LLD §4 |
|----|------|---------|---------------|
| AC01 | `grep -rn "analysis/" skills/m-analyzer/SKILL.md skills/f-analyzer/SKILL.md skills/q-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` | 0 结果 | R01-R08 全覆盖 |
| AC02 | `grep -rn "analysis/m-analysis\|analysis/f-analysis\|analysis/q-analysis\|analysis/integration\|analysis/factor-usage" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/ skills/design-planner/` | 0 结果 | R03-R07 |
| AC03 | `grep -rn "analysis/scenarios\|analysis/feature-input" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/` | 0 结果 | R01-R02 |
| AC04 | 逐文件 `grep -c "mfq/" skills/<name>/SKILL.md` | 每个文件 > 0 | R03-R07 |
| AC05 | `grep -c "process/plan/" skills/design-planner/SKILL.md` | > 0 | R08 |
| AC06 | `grep "^---$" skills/{m,f,q}-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md \| wc -l` | 10（每个文件 2 个 `---`） | §4.4 契约不变项 |
| AC07 | `grep -rn "analysis/" skills/m-analyzer/ skills/f-analyzer/ skills/q-analyzer/ skills/test-point-integrator/ skills/design-planner/` | 结果仅包含注释或说明性文本（如"analysis"作为方法论术语），不包含路径引用 | §6 异常处理 |
| AC08 | 对比替换前后 `wc -l` | 变化 ≤ ±5 行 | §5 步骤 3 |

### 7.2 正面测试

| 测试项 | 方法 | 覆盖 |
|--------|------|------|
| m-analyzer 产出路径正确 | `grep "mfq/m-analysis/test-points.md" skills/m-analyzer/SKILL.md` | R03 |
| f-analyzer 消费路径正确 | `grep "mfq/m-analysis/test-points.md" skills/f-analyzer/SKILL.md` | R03 |
| integrator 输入路径正确 | `grep "mfq/m-analysis/\|mfq/f-analysis/\|mfq/q-analysis/" skills/test-point-integrator/SKILL.md` | R03-R05 |
| integrator 输出路径正确 | `grep "mfq/integration/logic-cases.md" skills/test-point-integrator/SKILL.md` | R06 |
| design-planner 消费 integrator | `grep "mfq/integration/logic-cases.md" skills/design-planner/SKILL.md` | R06 |
| design-planner 消费 ppdcs-annotation | `grep "mfq/m-analysis/ppdcs-annotation.md" skills/design-planner/SKILL.md` | R03 |
| design-planner plan 输出 | `grep "process/plan/design-plan.md" skills/design-planner/SKILL.md` | R08 |
| KYM 输入路径 | `grep "kym/feature-input/raw-requirements.md" skills/m-analyzer/SKILL.md` | R01 |
| 场景消费路径 | `grep "kym/scenarios/confirmed-scenarios.md" skills/m-analyzer/SKILL.md` | R02 |
| 因子库路径 | `grep "mfq/factor-usage/factor-library-lock.yaml" skills/m-analyzer/SKILL.md` | R07 |

### 7.3 边界和异常测试

| 测试项 | 方法 | 覆盖 |
|--------|------|------|
| 注释中的 analysis 不作为路径替换 | 人工检查全文：确保 `analysis` 出现在方法论说明中时不被替换 | AC07 |
| frontmatter 中的路径不被破坏 | AC06 + 人工检查 5 个文件 frontmatter 可读 | §4.4 |
| 不存在的目标路径 | 不需要验证——本 Story 只改 Skill 引用，不创建目录 | N/A |

---

## 8. 实施步骤（含 TASK-ID）

| TASK-ID | 步骤 | 输入 | 操作 | 输出 | 验收 |
|---------|------|------|------|------|------|
| **TASK-STORY-012-01-01** | 环境准备 | 5 个 Skill 文件 | 确认 5 个文件可读写；`git status` 确认干净工作区 | 工作区状态确认 | 无未暂存修改 |
| **TASK-STORY-012-01-02** | 备份 | 5 个 Skill 文件 | `cp` 或 `git stash` 保留替换前版本 | 备份就绪 | 可在步骤 5 失败时恢复 |
| **TASK-STORY-012-01-03** | 路径替换 — m-analyzer | `skills/m-analyzer/SKILL.md` | 执行 8 条 sed 替换命令 | 替换后文件 | 即时 `grep -c "analysis/"` 验证 |
| **TASK-STORY-012-01-04** | 路径替换 — f-analyzer | `skills/f-analyzer/SKILL.md` | 执行 8 条 sed 替换命令 | 替换后文件 | 即时 `grep -c "analysis/"` 验证 |
| **TASK-STORY-012-01-05** | 路径替换 — q-analyzer | `skills/q-analyzer/SKILL.md` | 执行 8 条 sed 替换命令 | 替换后文件 | 即时 `grep -c "analysis/"` 验证 |
| **TASK-STORY-012-01-06** | 路径替换 — test-point-integrator | `skills/test-point-integrator/SKILL.md` | 执行 8 条 sed 替换命令 | 替换后文件 | 即时 `grep -c "analysis/"` 验证 |
| **TASK-STORY-012-01-07** | 路径替换 — design-planner | `skills/design-planner/SKILL.md` | 执行 8 条 sed 替换命令（特别注意 R08：`process/plan/`） | 替换后文件 | 即时 `grep -c "analysis/"` + `grep "process/plan/"` 验证 |
| **TASK-STORY-012-01-08** | 全体验收验证 | 替换后 5 个文件 | 执行 AC01-AC08 全部 grep 命令 | 8 项验收结果 | 全部 PASS |
| **TASK-STORY-012-01-09** | 行数验证 | 替换后 5 个文件 | `wc -l` 对比替换前后（AC08） | 行数差 ≤ ±5 | AC08 PASS |
| **TASK-STORY-012-01-10** | CP6 自检 | 验证结果 | 调用 checkpoint-manager Skill 输出 CP6 | `process/checks/CP6-STORY-012-01-mfq-path-migration-CODING-DONE.md` | CP6 PASS |

**任务依赖**：TASK-STORY-012-01-03 至 012-01-07 可并行执行（文件互不依赖）。TASK-STORY-012-01-08 依赖所有替换完成。

---

## 9. 风险与缓解

| 风险 ID | 风险描述 | 概率 | 影响 | 缓解措施 | 触发信号 |
|---------|---------|------|------|---------|---------|
| R1 | sed 替换导致 frontmatter 的 `description` 字段被意外修改（如 description 包含路径示例） | 低 | 中 | AC06 校验 `---` 数量；替换后检查 5 个 Skill frontmatter | AC06 FAIL |
| R2 | design-planner 的 `analysis/plan/` 被错误替换为 `mfq/plan/`（sed 顺序问题） | 极低 | 高 | 使用独立的 R08 规则；AC05 显式验证 | AC05 FAIL 或 grep 到 `mfq/plan/` |
| R3 | 某个 Skill 中有非路径上下文的 `analysis/` 文本被错误替换 | 低 | 低 | AC07 人工检查过滤；`analysis` 作为方法论术语通常不会以 `analysis/子目录` 形式出现 | AC07 有非预期匹配 |
| R4 | 替换后文件行数意外变化（如 sed 吞掉行尾） | 极低 | 低 | AC08 `wc -l` 对比 | 行数变化 >5 |
| R5 | CR-010 尚未创建全部目标目录（如 `mfq/factor-usage/`） | 低 | 低 | 本 Story 只改 Skill 引用不创建目录；目录缺失不影响 Skill 文档可读性 | N/A |

---

## 10. 发布与回滚

### 10.1 发布策略

- **发布方式**：不独立 commit。替换完成后标记 Story `ready-for-verification`，由 Wave A 统一管理 git 提交。
- **发布范围**：5 个 Skill 文件内的路径文本（~70 处），无其他产物。
- **不发布项**：不创建目录结构（CR-010 已建立），不修改安装脚本。

### 10.2 回滚策略

| 回滚方式 | 操作 | 适用场景 |
|---------|------|---------|
| Git revert | `git checkout -- <5个文件路径>` | 替换后发现验收失败且原因复杂 |
| 反向 sed | 将 8 条映射的 `从左→右` 改为 `从右→左`，重新执行 | 发现个别路径映射错误需要调整 |
| 整体 Wave revert | `git revert <Wave A commit>` | Wave A 整体出问题 |

**回滚验证**：回滚后执行 AC01 的反向验证（确认旧路径全部恢复）。

---

## 11. 依赖与前置条件

### 11.1 前置条件

| 条件 | 状态 | 验证方式 |
|------|------|---------|
| HLD v1.1 confirmed=true | 已满足 | `process/HLD-CR-012.md` frontmatter `confirmed: true` |
| CP3 人工确认通过 | 已满足 | `checkpoints/CP3-HLD-REVIEW-CR-012.md` |
| 5 个 Skill 文件存在且可读写 | 需运行时确认 | `ls -la skills/{m,f,q}-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` |
| CR-010 三阶段目录结构已建立 | 已满足 | `ls -d kym/ mfq/ process/plan/` |
| 无文件所有权冲突（STORY-012-02 不碰这 5 个文件） | 已满足 | 对比 `file_ownership` |

### 11.2 依赖类型

| 依赖 | 类型 | 状态 |
|------|------|------|
| CR-010（目录结构） | `runtime` | 已完成 |
| CR-011（KYM 阶段） | 无直接依赖 | N/A（本 Story 只改路径引用） |
| STORY-012-02 | 无依赖（并行） | Wave A 并行 |
| STORY-012-03~07 | 被依赖（`contract`：提供正确路径） | 待本 Story 完成 |

---

## 12. 实现灰区

| ID | 灰区 | 决策 | 理由 | 影响面 | 重访条件 |
|----|------|------|------|--------|---------|
| GA-01 | `analysis/scenarios/` 在 `q-analyzer` 的输入/前置条件中是否引用？ | 是，需要替换。已从 Story 范围确认 q-analyzer 引用 `analysis/scenarios/confirmed-scenarios.md` | q-analyzer 步骤 1 读取场景以评估质量维度相关性 | q-analyzer | 若发现 q-analyzer 不消费场景，撤回该条替换 |
| GA-02 | `design-planner` 的 `analysis/plan/design-planner-reasoning.md` 是否与 `analysis/integration/design-plan.md` 路径分离？ | 是。`analysis/integration/design-plan.md` 归属 R06（→ `mfq/integration/`），`analysis/plan/design-planner-reasoning.md` 归属 R08（→ `process/plan/`） | HLD §9 明确 design-planner 输出到 `process/plan/`（跨阶段边界），但设计计划表写入 `mfq/integration/`（MFQ 阶段内） | design-planner | 若后续 CR 统一 plan 输出路径，需调整 R08 |

**澄清队列**：无。本 Story 范围明确，路径映射表来自 CR-012 / HLD §1（已人工确认），无需要澄清的实现灰区。

---

## 13. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-02 | meta-dev | 初始 LLD，覆盖 5 个 Skill 文件的 8 条路径映射规则、10 个 TASK-ID、8 项验收测试和全部实现细节 |

---

## 14. 验收清单

- [ ] 8 条路径映射全部执行（R01-R08），旧路径零残留（AC01 PASS）
- [ ] 5 个 Skill 文件的 YAML frontmatter 完好（AC06：`---` 计数 = 10）
- [ ] 4 个分析器 Skill 中 `mfq/` 路径正确（AC04：每个 > 0）
- [ ] design-planner 中 `process/plan/` 替代 `analysis/plan/`（AC05 PASS）
- [ ] 行数变化 ≤ ±5（AC08 PASS）
- [ ] 步骤编号、PPDCS 特征定义、HTSM 维度、CAE 格式等方法论内容不变
- [ ] 触发词、Gotchas、验收标准等非路径文本不变
- [ ] CP6 自检通过（`process/checks/CP6-STORY-012-01-mfq-path-migration-CODING-DONE.md`）
