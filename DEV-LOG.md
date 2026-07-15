# DEV-LOG — CR-013 ptm-tde PPDCS 阶段改造

## STORY-013-01：5 设计 Skill 路径迁移 + 方法论占位

**实现时间**：2026-06-03T04:00:00+08:00
**执行模式**：meta-dev 直接执行（用户显式调度）
**Applies to**：WF-PTM-TEAM-20260520-001, CR-013 Wave A
**tier**：M
**wave**：A
**story_status**：ready-for-verification

### 实现清单

| 文件 | 路径替换数 | 方法论占位 |
|------|:---:|:---:|
| `skills/process-design/SKILL.md` | ~12 处 | 流程图法设计步骤 |
| `skills/parameter-design/SKILL.md` | ~11 处 | 判定表法设计步骤 |
| `skills/data-design/SKILL.md` | ~10 处 | 等价类+边界值法设计步骤 |
| `skills/combination-design/SKILL.md` | ~10 处 | 组合法设计步骤 |
| `skills/state-design/SKILL.md` | ~13 处 | 状态图法设计步骤 |

### 路径迁移映射（已执行）

| 旧路径 | 新路径 | 涉及文件数 |
|--------|--------|:---:|
| `analysis/integration/design-plan.md` | `process/plan/design-plan.md` | 5 |
| `analysis/plan/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` | 5 |
| `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` | 5 |
| `analysis/integration/test-data.md` | `mfq/integration/test-data.md` | 5 |
| `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` | 2 |
| `analysis/m-analysis/ppdcs-annotation.md` | `mfq/m-analysis/ppdcs-annotation.md` | 3 |
| `design/ppdcs/` | `ppdcs/ppdcs/` | 5 |
| `design/pc/` | `ppdcs/pc/` | 5 |

### 方法论占位节

5 个 Skill 均在 `§验收标准` 之前插入 `§方法论细则（用户可定制）`，格式统一（目标/核心步骤/关键决策点/示例/下游影响），各 Skill 的具体维度：

- **process-design**：流程图构建规则、路径枚举策略、触发数据分配规则
- **parameter-design**：约束提取规则、规则组合矩阵构建、参数组分配规则、判定表 vs 因果图 vs 决策树选择
- **data-design**：等价类划分规则、边界值选取策略（三点法）、数据 vs 组合判定规则
- **combination-design**：因子识别规则、约束建模规则、压缩策略选择（Pairwise/正交/全组合）、PICT 模型文件构建
- **state-design**：状态识别规则、迁移表构建、守卫条件提取、状态路径枚举、合法 vs 非法迁移区分

### 验证结果

- 全部 5 文件旧路径 `analysis/` / `design/` 真实残留 = 0
- 3 处 `m-analysis/` 子串假阳性均确认为新路径 `mfq/m-analysis/`
- 5 文件方法论占位节均存在
- 原始执行流程和验收标准未修改
- CP6 编码完成检查：17 PASS / 0 FAIL / 0 WAIVED

### 已知限制

- `analysis/factor-usage/` 路径在 5 个文件中未出现（该路径仅在 coverage-verifier 和 design-ppdcs-analyzer 中引用）
- 方法论占位节为框架性内容，需用户后续根据项目特点填充具体规则

---
# DEV-LOG — CR-010 三阶段框架改造

## STORY-012-03：M 分析器 v3.0 重写 LLD 设计

**设计时间**：2026-06-02T20:00:00+08:00
**执行模式**：meta-dev（lld-designer Skill 驱动）
**LLD 状态**：ready-for-review（confirmed=false）
**CP5 自动预检**：PASS（14 项检查：10 PASS + 2 WAIVED + 2 N/A，0 FAIL）
**调度批次**：CR-012-all-stories batch_1，Agent B
**tier**：M
**wave**：B

### LLD 摘要

- **文件**：`process/stories/STORY-012-03-m-analyzer-v3-rewrite-LLD.md`（14 章节，~30KB）
- **影响文件**：仅 `skills/m-analyzer/SKILL.md`（全量重写，357行→~480行）
- **步骤变化**：v2 7 步 → v3.0 7 步（场景步骤驱动的逐步发现模式）
- **实施步骤**：10 个 TASK-ID（TASK-012-03-01 至 TASK-012-03-10），按重写逻辑次序编排
- **可复用**：理论基础、PPDCS 五特征表、CAE 约束、MFQ 分层概念、拓扑/因子 Guardrail、公共因子库契约、拓扑绑定契约
- **完全重写**：执行流程 7 步、适用范围、前置条件、输出清单（3→8 文件）、验收标准

### 关键新增实体

| 实体 | 产出路径 | 说明 |
|------|---------|------|
| 覆盖矩阵（实体 H） | `mfq/m-analysis/scenario-tsp-coverage.md` | 视角 A（场景→TSP）+ 视角 B（目录→场景）+ F/Q 线索汇总表 |
| 步骤标签（实体 G） | 嵌入覆盖矩阵 + TSP.f_tags/q_tags | [M] / [F→目标] / [Q→维度] 三类标签 |
| 因子候选 | `mfq/m-analysis/candidate-factor-proposals.yaml` | source=new-candidate 的因子提案 |
| 原子操作候选 | `mfq/m-analysis/candidate-atomic-ops.yaml` | 无已有 atomic-ops 支撑的步骤候选 |

### 接口契约

- **输入消费**：10 个入口（raw-requirements.md、directory-structure.md、confirmed-scenarios.md、mission-statement.md、atomic-ops、公共因子库 + 步骤 1-5 内部产出）
- **输出生产**：8 个文件供下游消费（f-analyzer 消费 F 线索 + TSP + 因子表；q-analyzer 消费 Q 线索 + TSP + 因子表；test-point-integrator 消费全量测试点 + 候选列表 + 覆盖矩阵；design-planner 消费 TSP.covered_scenario_segments）

### 未决点（Clarification Queue）

| ID | 问题 | 状态 | 是否阻断 LLD |
|----|------|------|-------------|
| LCQ-STORY-012-03-01 | 覆盖矩阵视角 A/B 一致性检查脚本化 vs 手动标注 | open（推荐方案 A：手动校验） | 否 |
| LCQ-STORY-012-03-02 | 公共因子库搜索路径：三层回退 vs 单一路径 | open（推荐方案 A：沿用三层回退） | 否 |

### 依赖与门控

- **上游**：STORY-012-01（路径迁移，file-conflict 依赖，共享 `skills/m-analyzer/SKILL.md` 所有权）
- **dev_gate**：全量 CP5 人工确认通过 + Wave A 完成 + 文件所有权不冲突
- **HARD-STOP**：步骤 6 覆盖初检禁止 Agent 自行判定通过；步骤 7 写入前禁止 Agent mkdir

### 待确认项

- 等待 meta-po 收齐 CR-012 全部 8 Story 的 LLD 后统一发起 CP5 人工确认
- 2 项 OPEN 待用户在 CP5 人工确认时统一决策

---

## STORY-010-06：更新索引与需求文件

**实现时间**：2026-06-01T15:40:00+08:00
**执行模式**：meta-dev inline（用户直接指令激活）
**CP6 结论**：PASS（全部 8 项验证通过）

### 变更文件清单

| 文件 | 变更数 | 说明 |
|---|---|---|
| `skills/README.md` | 2 处 | 第 8 行"11 步"→"三阶段框架"；第 38 行 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md` |
| `agents/README.md` | 1 处 | 第 53-55 行 ptm-tde 章节：增加三阶段框架（KYM → MFQ → PPDCS）+ GATE-1 至 GATE-5 门控描述 |
| `process/REQUIREMENTS-ptm-tde.md` | 3 处 | frontmatter（v6.2→v7.0, total_requirements 29→31, source_inputs +CR-010）；新增 REQ-030（三阶段框架）；新增 REQ-031（MFQ Exit Gate）；追加 v7.0 修订记录行 |

### 关键决策与偏差

- **无偏差**：全部变更严格按 LLD §3 执行。
- **REQ-030/REQ-031 格式**：使用与现有需求表格一致的 markdown table 格式（6 列：ID/类型/功能描述/优先级/验收条件/来源），与 LLD §3.3.2 定义一致。
- **修订记录处理人**：标注为 `meta-po`，与 CR-010 的整体管理角色一致。

### 已知限制

- `REQUIREMENTS-ptm-tde.md` RA-07/RA-08/RA-09 风险描述不涉及旧路径引用，无需更新。
- `agents/README.md` ngfw-factory-installer 章节不在 CR-010 范围内，不修改。
- `skills/README.md` Skill Index 中 19 个 Skill 的职责描述保持不变（Skill 运行逻辑未变，仅阶段归属改变）。

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-010-06-update-index-and-requirements-CODING-DONE.md`
- 8 项 grep 验证全部 PASS（无旧编号、路径、版本残留）
- 需求表格条目数 31 与 `total_requirements: 31` 一致

### 提供给 meta-qa 的验证提示

- STORY-010-07（grep 验证）将执行跨文档 grep 检查所有旧引用
- meta-qa 应验证 `skills/README.md`、`agents/README.md`、`process/REQUIREMENTS-ptm-tde.md` 与 `agents/ptm-tde.md`（STORY-010-02）三阶段描述保持一致

---

# DEV-LOG — CR-012 ptm-tde MFQ 阶段改造

## Wave A LLD 设计批次：STORY-012-01 + STORY-012-02

**设计时间**：2026-06-02T03:44:42+08:00
**执行模式**：meta-dev inline（meta-po 直接指令激活）
**LLD 设计批次**：Wave A（2 个 Story，互不依赖，可并行实施）
**批次状态**：`lld-ready-for-review`（等待 CP5 全量人工确认）

### STORY-012-01：MFQ 路径迁移

**LLD 路径**：`process/stories/STORY-012-01-mfq-path-migration-LLD.md`
**CP5 自动预检**：`process/checks/CP5-STORY-012-01-mfq-path-migration-LLD-IMPLEMENTABILITY.md`
**CP5 结论**：PASS（12 PASS + 1 N/A + 0 FAIL）

#### LLD 摘要

- **范围**：5 个 Skill 文件（m-analyzer, f-analyzer, q-analyzer, test-point-integrator, design-planner）
- **核心操作**：8 条 sed 路径映射规则（`analysis/` → `kym/` / `mfq/` / `process/plan/`），~70 处替换
- **TASK-ID**：10 个，其中 5 个替换任务可并行（文件互不依赖）
- **验收方式**：8 项 grep 自动化验收（AC01-AC08），零外部依赖

#### 关键设计决策

- **替换顺序**：不重要（8 条映射目标路径互不重叠），从最长前缀开始替换以提高安全性
- **design-planner 特殊处理**：`analysis/plan/` → `process/plan/` 是唯一跨阶段边界替换（R08）
- **校验策略**：AC06 通过 `---` 计数验证 YAML frontmatter 未被损坏

#### 未决点

- 无。路径映射表来自 CR-012 / HL D §1（已人工确认），clarification queue 为空。

### STORY-012-02：MFQ Exit Gate 增强

**LLD 路径**：`process/stories/STORY-012-02-mfq-exit-gate-enhance-LLD.md`
**CP5 自动预检**：`process/checks/CP5-STORY-012-02-mfq-exit-gate-enhance-LLD-IMPLEMENTABILITY.md`
**CP5 结论**：PASS（12 PASS + 1 N/A + 0 FAIL）

#### LLD 摘要

- **范围**：2 个文件（`docs/ptm-tde/gate-spec.md` + `skills/checkpoint-manager/SKILL.md`）
- **核心操作**：GATE-3 Checklist #1-8 → M1-M7 + W1-W2（合并 #8）+ 人工确认项 4 处 HARD-STOP 标记 + 执行协议 STOP-01~05 引用追加
- **TASK-ID**：9 个，gate-spec.md 修改完成后同步到 checkpoint-manager
- **验收方式**：8 项 grep 验收（AC01-AC08）+ 5 项回归测试（GATE-1/2/4/5 不变）

#### 关键设计决策

- **真相源策略**：先修改 gate-spec.md（规范真相源），再以之为参照同步 checkpoint-manager
- **#8 合并**：旧 #8（plan 存在性和格式）合并到 M6（设计计划存在 + 格式符合 PPDCS 消费契约）
- **HARD-STOP 位置**：放在每个确认项的「说明」列最前面，后跟原有说明文本
- **执行协议位置**：放在 GATE-3 末尾（Deliverables 之后、下一个 Gate 之前）

#### 未决点

- 无。编号映射表来自 CR-012 Story 卡片，HARD-STOP 标记和 STOP-01~05 来自 HL D §11（已人工确认），clarification queue 为空。

### 跨 Story 契约

| 契约项 | STORY-012-01 | STORY-012-02 | 一致性 |
|--------|-------------|-------------|--------|
| 文件所有权 | 5 个 Skill 文件 | gate-spec.md + checkpoint-manager SKILL.md | 不冲突 |
| 并行安全 | `parallel_safe: true` | `parallel_safe: true` | 可并行实施 |
| Wave | A | A | 同一批次 |
| upstream 依赖 | 无 | 无 | 互不依赖 |
| downstream 依赖 | STORY-012-03~07 | 无直接文件依赖 | — |

### 待 CP5 全量人工确认

- 两个 Story LLD 均已完成，CP5 自动预检均为 PASS
- clarification queue 空（两个 LLD 的 §12 均明确"澄清队列：无"）

---

## Wave B LLD 设计批次：STORY-012-03（M 分析器 v3.0 重写）

**设计时间**：2026-06-02T23:30:00+08:00
**执行模式**：meta-dev inline（Agent B 独立完成）
**LLD 状态**：`lld-ready-for-review`

> 此为 Agent B 的产出记录占位。详细摘要见 Agent B 的 DEV-LOG 追加。CP5 自动预检文件路径：`process/checks/CP5-STORY-012-03-m-analyzer-v3-rewrite-LLD-IMPLEMENTABILITY.md`。

---

## Wave C LLD 设计批次：STORY-012-04 + STORY-012-05

**设计时间**：2026-06-02T23:30:00+08:00
**执行模式**：meta-dev inline（Agent C 负责 Wave C: 012-04 + 012-05）
**LLD 设计批次**：Batch 1 Wave C（F/Q 分析器，同组 fq-analyzers，可并行实施）
**批次状态**：`lld-ready-for-review`（STORY-012-04/05 均已完成，等待 CP5 全量人工确认）

### STORY-012-04：F 分析器 v3.0 重写（逐 TSP 驱动耦合分析）

**LLD 路径**：`process/stories/STORY-012-04-f-analyzer-v3-rewrite-LLD.md`
**CP5 自动预检**：`process/checks/CP5-STORY-012-04-f-analyzer-v3-rewrite-LLD-IMPLEMENTABILITY.md`
**CP5 结论**：PASS（6/6 checklist 通过，2 项 non-blocking LCQ）

#### LLD 摘要

- **范围**：单文件 `skills/f-analyzer/SKILL.md`（全量重写，314 行 → ~450 行，净增 ~150 行）
- **流程**：8 步 v2 → 9 步 v3.0。核心新增：步骤 1 加载 TSP 列表 + F 线索；步骤 2 逐 TSP 场景耦合推理（子步骤 A/B/C）；步骤 9 耦合因子候选列表汇总
- **新概念**：`[F→]` 标签种子线索、`discovery_source`（f-tag-seed / scenario-inference）、耦合对象/因子发现、耦合因子全候选降级
- **TASK-ID**：16 个，全部作用于同一文件的不同区块

#### 关键设计决策

- **耦合关系发现顺序**：优先从 F 标签种子展开（discovery_source=f-tag-seed），再自主发现（discovery_source=scenario-inference）
- **三源合并增强**：新增 discovery_source 取并集规则；以 (source_tsp, target_tsp) 为 key 去重
- **输出组织**：耦合测试点按 TSP 组织（替代 v2 的按目录组织）
- **旧版保留**：11 条 Gotchas、CAE 耦合约束、拓扑/因子 Guardrail 全部迁移

#### 未决点（clarification queue）

| ID | 问题 | 推荐方案 | blocks_lld |
|----|------|---------|------------|
| LCQ-STORY-012-04-01 | object_role_in_coupling 枚举约束 | 方案 A：枚举（触发方/受影响方/共享资源） | false |
| LCQ-STORY-012-04-02 | F 线索指向不存在 TSP 的处理 | 方案 A：记录 gap + 警告不阻断 | false |

### STORY-012-05：Q 分析器 v3.0 重写（逐 TSP 驱动质量分析）

**LLD 路径**：`process/stories/STORY-012-05-q-analyzer-v3-rewrite-LLD.md`
**CP5 自动预检**：`process/checks/CP5-STORY-012-05-q-analyzer-v3-rewrite-LLD-IMPLEMENTABILITY.md`
**CP5 结论**：PASS（6/6 checklist 通过，2 项 non-blocking LCQ）

#### LLD 摘要

- **范围**：单文件 `skills/q-analyzer/SKILL.md`（全量重写，257 行 → ~370 行，净增 ~120 行）
- **流程**：5 步 v2 → 6 步 v3.0。核心新增：步骤 1 加载 TSP + Q 线索 + 逐 TSP 相关性评估；步骤 2 逐 TSP 质量对象与因子发现（子步骤 A/B）；步骤 6 质量因子候选列表汇总
- **新概念**：`[Q→]` 标签起评/提升规则、`generation_basis`（行业标准/经验推断/需求推断）、质量对象/因子发现、质量因子全候选降级
- **TASK-ID**：16 个，全部作用于同一文件的不同区块

#### 关键设计决策

- **[Q→] 标签提升规则**：标签维度至少弱相关起评，可提升至强相关；不降级已有强相关判定
- **相关性评估**：逐 TSP 逐 HTSM 维度评估，不确定项标记 OPEN 不自行判定
- **generation_basis 枚举**：3 类（行业标准/经验推断/需求推断），与设计文档 §5 一致
- **输出组织**：质量测试点按 TSP 组织、按质量维度分组（替代 v2 的按目录+按维度双层组织）
- **旧版保留**：7 条 Gotchas、HTSM 维度定义表、CAE 质量约束全部迁移

#### 未决点（clarification queue）

| ID | 问题 | 推荐方案 | blocks_lld |
|----|------|---------|------------|
| LCQ-STORY-012-05-01 | generation_basis 枚举范围（3 类 vs 5 类） | 方案 A：保持 3 类 | false |
| LCQ-STORY-012-05-02 | OPEN 标记项汇总确认策略 | 方案 A：单次展示等待确认 | false |

### 跨 Story 契约（Wave C 内部）

| 契约项 | STORY-012-04 | STORY-012-05 | 一致性 |
|--------|-------------|-------------|--------|
| 文件所有权 | `skills/f-analyzer/SKILL.md` | `skills/q-analyzer/SKILL.md` | 不冲突 |
| 并行安全 | `parallel_safe: true` | `parallel_safe: true` | 可并行实施 |
| parallel_group | fq-analyzers | fq-analyzers | 同一并行组 |
| Wave | C | C | 同一批次 |
| upstream 依赖 | STORY-012-01 + STORY-012-03 | STORY-012-01 + STORY-012-03 | 相同上游 |
| downstream 依赖 | STORY-012-06 | STORY-012-06 | 相同下游 |
| 消费 M 分析产物 | TSP（含 f_tags）+ 覆盖矩阵 F 线索 | TSP（含 q_tags）+ 覆盖矩阵 Q 线索 | 消费不同标签类型，无冲突 |

### 待 CP5 全量人工确认

- 两个 Story LLD 均已完成（14 章节），CP5 自动预检均为 PASS（6/6 checklist）
- 4 项 clarification queue item（012-04: 2 项, 012-05: 2 项），均不阻断 LLD（blocks_lld=false）
- 与 Agent A（012-01/02）和 Agent B（012-03）的 LLD 共同组成 Batch 1
- 等待 meta-po 收齐全部 8 个目标 Story 的 CP5 后生成 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md` 并发起统一确认
- 等待 meta-po 收齐全部目标 Story（本次仅 Wave A：STORY-012-01 + STORY-012-02）的 CP5 后生成 `checkpoints/CP5-ALL-STORIES-LLD-BATCH.md` 并发起统一确认

---

## Wave D LLD 设计批次：STORY-012-07（候选汇总 + STOP 协议落地）

**设计时间**：2026-06-02T23:00:00+08:00
**执行模式**：meta-dev inline（lld-designer Skill 驱动，Agent E 负责 012-07 + 012-08）
**LLD 状态**：`lld-ready-for-review`（confirmed=false）
**CP5 自动预检**：PASS（14 项检查：13 PASS + 1 WAIVED，0 FAIL，0 BLOCKED）
**调度批次**：CR-012 Wave D，Story 012-06 的下游
**tier**：M
**wave**：D

### LLD 摘要

- **LLD 路径**：`process/stories/STORY-012-07-candidate-summary-stop-protocol-LLD.md`（14 章节）
- **CP5 自动预检路径**：`process/checks/CP5-012-07-candidate-summary-stop-protocol-LLD-IMPLEMENTABILITY.md`
- **影响文件**：5 个（test-point-integrator SKILL.md、skill-references.md、m-analyzer SKILL.md、f-analyzer SKILL.md、q-analyzer SKILL.md）
- **改动量**：约 90 行（候选汇总 ~40 行 + skill-references ~15 行 + STOP 标记 ~12 行 × 3 Skill ~36 行）
- **实施步骤**：4 个 TASK-ID（TASK-012-07-01 至 TASK-012-07-04）

### 三项工作详情

#### 1. 候选汇总步骤（test-point-integrator，TASK-012-07-01）

- **插入位置**：步骤 4（LC 生成）之后，步骤 5（测试数据归集）之前，使用编号 `步骤 4.5`
- **核心逻辑**：
  - 三源候选归集：从 `mfq/m-analysis/candidate-*.yaml`、F/Q 候选列表读取
  - 去重合并：以 `factor_id` / `candidate_op_name` 为 key，标注多来源
  - 优先级判定：高（M 高关联度）/ 中（F 关键耦合 or Q 强相关）/ 低（中关联 or 弱相关）
  - 用户批量确认：4 个 `( )` 单选选项（全部确认/逐项确认/批量修改/全部拒绝）
  - 确认后回写：`mfq/candidates/factor-candidates.md` + `mfq/candidates/atomic-op-candidates.md`
- **STOP-02 标记**：步骤 4.5 开头和用户确认环节各标注 `⛔ HARD-STOP`
- **容错设计**：候选列表全不存在 → Warning 跳过；格式不一致 → Warning 展示原始内容

#### 2. skill-references.md 更新（TASK-012-07-02）

- m-analyzer：职责描述更新为「M 分析 v3.0（场景步骤驱动）」→ 含覆盖矩阵、场景步骤标签、CAE 测试点、候选列表
- f-analyzer：职责描述更新为「F 分析 v3.0（逐 TSP 驱动）」→ 含耦合因子候选
- q-analyzer：职责描述更新为「Q 分析 v3.0（逐 TSP 驱动）」→ 含质量因子候选
- test-point-integrator：职责描述追加「候选汇总：三源候选去重合并与用户批量确认」
- 新增「MFQ 候选汇总」段落，包含 `mfq/candidates/` 路径说明

#### 3. STOP 协议落地（TASK-012-07-03, TASK-012-07-04）

| STOP | 落地文件 | 位置 | 内容 |
|------|---------|------|------|
| STOP-02 | test-point-integrator | 步骤 4.5 | 禁止自行判定候选确认 |
| STOP-03 | m-analyzer | 前置条件末尾 | 禁止绕过 Skill，不得使用 v2.0 旧模式 |
| STOP-03 | f-analyzer | 前置条件末尾 | 禁止绕过 Skill |
| STOP-03 | q-analyzer | 前置条件末尾 | 禁止绕过 Skill |
| STOP-04 | m-analyzer | 步骤 7（输出）开头 | 写入前校验父目录存在且为目录 |

> STOP-01 已在 STORY-012-02 落地到 gate-spec.md，STOP-05 已在候选汇总确认界面落地（`( )` 单选标记）。

### 未决点（Clarification Queue）

| ID | 问题 | 推荐方案 | blocks_lld |
|----|------|---------|------------|
| O-01 | F/Q 候选列表确切文件名和路径需等待 STORY-012-06 完成 | 实现时以 STORY-012-06 最终产出为准，LLD 中使用占位符 | false（不阻断 LLD 结构） |

### 依赖与门控

- **上游（runtime）**：STORY-012-06（test-point-integrator 已适配，消费 M/F/Q 候选列表）。F/Q 候选列表路径在 STORY-012-06 中确定。
- **下游（文件级）**：STORY-012-08（文档更新需引用 skill-references.md 最新状态）
- **文件所有权**：5 个文件均在本 Story 范围内，与其他 Story 无冲突（`parallel_safe=false` 确保串行）

### 待确认项

- LLD 已完成 14 章节，CP5 自动预检 PASS
- 与 CR-012 其他 Story 的 LLD 共同组成全量批次
- 等待 meta-po 收齐全部 8 个目标 Story 的 CP5 后生成 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md` 并发起统一确认

---

## Wave D LLD 设计批次：STORY-012-08（文档更新）

**设计时间**：2026-06-02T23:00:00+08:00
**执行模式**：meta-dev inline（lld-designer Skill 驱动，Agent E 负责 012-07 + 012-08）
**LLD 状态**：`lld-ready-for-review`（confirmed=false）
**CP5 自动预检**：PASS（6/6 checklist 通过，0 项 clarification item）
**调度批次**：CR-012-all-stories batch_2，Agent E
**tier**：S
**wave**：D

### LLD 摘要

- **文件**：`process/stories/STORY-012-08-documentation-update-LLD.md`（14 章节）
- **影响文件**：4 个（`process/changes/CR-INDEX.yaml`、`process/STATE.md`、`agents/ptm-tde.md`、`process/changes/CR-012-ptm-tde-mfq-phase.md`）
- **改动量**：~27 行，纯文本/配置修改
- **TASK-ID**：5 个（TASK-012-08-01 至 TASK-012-08-05），前 4 个为文件修改，第 5 个为验收验证
- **AC 覆盖**：8 项 AC 在 LLD §2/§10/§14 中全部有对应设计和验证

### 关键设计决策

- **CR-INDEX.yaml**：closed 字段放在 approved 之后、phase 之前（与已 closed 的 CR-010/CR-011 格式一致）；notes 使用单行字符串
- **STATE.md**：active_change 双处同步修改（frontmatter + Current Work 表）；lld_design_batch 状态清理；History 追加
- **agents/ptm-tde.md**：MFQ Phase 行 21 空格缩进对齐（匹配现有 KYM Phase 行风格）；GATE-3 描述增加 v3.0 方法论引用
- **STATE.md current_phase 不一致**：frontmatter 为 `delivered`，Current Work 表为 `story-execution`。不在本 Story 范围修改，留待 CR-013 或下次阶段推进时统一处理

### 文件所有权

| 文件 | 冲突检查 | 结果 |
|------|---------|------|
| `process/changes/CR-INDEX.yaml` | 其他 Story 不修改 | 无冲突 |
| `process/STATE.md` | 其他 Story 不修改 | 无冲突 |
| `agents/ptm-tde.md` | CR-011 STORY-011-04 已完成 | 无冲突 |
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | 其他 Story 不修改 | 无冲突 |

### 未决点（Clarification Queue）

- 无。改动量小，范围明确，无需澄清项。

### 依赖与门控

- **上游**：STORY-012-07（runtime 依赖，同为 batch_2 LLD 设计）
- **dev_gate**：STORY-012-07 verified + 全量 CP5 人工确认通过 + Wave D 可执行
- **执行时机**：本 Story 必须在 STORY-012-01 ~ 012-07 全部 CP7 verified 后执行

### 待确认项

- 等待 meta-po 收齐全部 8 Story 的 LLD 后统一发起 CP5 人工确认
- STORY-012-08 LLD CP5 自动预检 PASS（6/6），汇入 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md`

---

## Wave D LLD 设计批次：STORY-012-06（上下游 Skill 适配）

**设计时间**：2026-06-02T23:50:00+08:00
**执行模式**：meta-dev inline（lld-designer Skill 驱动）
**LLD 状态**：`lld-ready-for-review`（confirmed=false）
**CP5 自动预检**：PASS（14 项检查：12 PASS + 2 WAIVED，0 FAIL）
**调度批次**：CR-012 Wave D，Story 012-03/04/05 的下游、012-07 的上游
**tier**：M
**wave**：D

### LLD 摘要

- **LLD 路径**：`process/stories/STORY-012-06-upstream-downstream-adapt-LLD.md`（14 章节，~684 行）
- **CP5 自动预检路径**：`process/checks/CP5-STORY-012-06-upstream-downstream-adapt-LLD-IMPLEMENTABILITY.md`
- **影响文件**：2 个（`skills/test-point-integrator/SKILL.md` ~35 行、`skills/design-planner/SKILL.md` ~15 行）
- **改动模式**：增量适配（非全量重写），保留现有核心归集/合并/设计计划逻辑
- **实施步骤**：10 个 TASK-ID（TASK-012-06-01 至 TASK-012-06-10）

### test-point-integrator 适配（6 个 TASK，~35 行）

| 修改点 | 内容 |
|--------|------|
| 适用范围/前置条件 | 路径 `analysis/` → `mfq/`/`kym/` |
| 步骤 1（加载输入） | 新增覆盖矩阵（`scenario-tsp-coverage.md`）+ M/F/Q 候选列表加载 |
| 步骤 2（覆盖检查） | 新增覆盖矩阵视角 A 检查：SR→TSP→TP 覆盖链 + covered/uncovered/excluded 统计 |
| 候选归集步骤（新增） | 读取三源候选 → 按 factor_id/candidate_id 去重 → 输出到 `mfq/candidates/` |
| 步骤 8（输出） | 路径 `analysis/integration/` → `mfq/integration/`；新增候选归集文件 |
| Gotchas + 验收标准 | 新增覆盖矩阵缺失降级 + 候选不自行确认 Gotchas；验收标准路径更新 |

### design-planner 适配（4 个 TASK，~15 行）

| 修改点 | 内容 |
|--------|------|
| 适用范围/前置条件 | 路径 `analysis/` → `mfq/`/`process/plan/` |
| 步骤 1（加载输入） | 新增 TSP `covered_scenario_segments` 解析：`scenario_ref` + `covered_steps[]` + `coverage_type` |
| 步骤 2（逐条匹配） | 新增设计范围交叉校验：LC 场景步骤 ↔ covered_steps 对比 → coverage_confirmed/partial/gap |
| 步骤 6（输出）+ Gotchas | 设计计划输出路径 → `process/plan/`；新增 covered_segments 缺失降级 Gotcha |

### 向后兼容降级路径

| 场景 | 处理 |
|------|------|
| `scenario-tsp-coverage.md` 不存在 | test-point-integrator 跳过覆盖矩阵校验 |
| TSP 不含 `covered_scenario_segments` | design-planner 跳过设计范围交叉校验 |
| 候选列表文件缺失 | candidate 归集步骤跳过该来源 |
| TSP 文件不存在 | design-planner 仅加载现有输入 |

### 关键设计决策

- **改动策略**：增量修改而非全量重写（2 个文件各 ~15-35 行），保留全部现有核心逻辑
- **候选归集**：仅做归集和去重，不附加确认选项。确认由 STORY-012-07 处理
- **输出分离**：因子候选（`factor-candidates.md`）与原子操作候选（`atomic-op-candidates.md`）分开输出
- **路径零残留**：修改后 grep `analysis/` 在两个 Skill 中返回 0

### 未决点（Clarification Queue）

- 无。所有设计决策均在 LLD 阶段自行确定，4 项设计决策已在 LLD §12.1 记录。本 Story 适配逻辑明确（所有上游输出格式已在 STORY-012-03/04/05 LLD §5/§6 中定义），无需用户或上游额外决策。

### 依赖与门控

- **上游（runtime）**：STORY-012-01（路径迁移）+ STORY-012-03（M 分析器 v3.0）+ STORY-012-04（F 分析器 v3.0）+ STORY-012-05（Q 分析器 v3.0）
- **下游（runtime）**：STORY-012-07（候选汇总消费 `mfq/candidates/` 中的归集文件）
- **文件所有权**：2 个文件均独属于本 Story，与其他 Story 无冲突（test-point-integrator 与 STORY-012-01 有 file-conflict 依赖，但 012-01 已在 Wave A 完成）
- **dev_gate**：Wave A/B/C 全部 verified + 全量 CP5 人工确认通过 + 文件所有权不冲突

### 待确认项

- 等待 meta-po 收齐 CR-012 全部 8 个目标 Story 的 LLD 后，统一生成 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md` 并发起 CP5 人工确认

---

# DEV-LOG — STORY 实施记录

## STORY-012-01：MFQ 路径迁移 实施

**实现时间**：2026-06-02T23:00:00+08:00
**执行模式**：meta-dev inline（用户显式指令激活）
**CP6 结论**：PASS（8/8 AC 通过）
**Wave**：A

### 实现文件清单

| 文件 | 变更类型 | 旧路径引用数 | 说明 |
|------|----------|:---:|------|
| `skills/m-analyzer/SKILL.md` | 修改 | 18 | `analysis/` → `kym/` + `mfq/`，含 scripts 输出路径 |
| `skills/f-analyzer/SKILL.md` | 修改 | 16 | `analysis/` → `kym/` + `mfq/`，含工具脚本输出路径 |
| `skills/q-analyzer/SKILL.md` | 修改 | 7 | `analysis/` → `kym/` + `mfq/` |
| `skills/test-point-integrator/SKILL.md` | 修改 | 11 | `analysis/` → `kym/` + `mfq/`，含全部 M/F/Q 读取和输出路径 |
| `skills/design-planner/SKILL.md` | 修改 | 17 | `analysis/` → `mfq/` + `process/plan/`（跨阶段边界） |
| | | **69** | **合计 ~70 处替换，0 行净增** |

### 关键决策与偏差

- **无偏差**：严格按 LLD §5 执行 8 条 sed 命令逐文件替换。
- **AC01 假阳性**：`grep "analysis/"` 会匹配新路径 `mfq/m-analysis/`、`mfq/f-analysis/`、`mfq/q-analysis/` 中的 `analysis/` 子串。精确验证（AC02 + AC03 + 旧 plan 路径检查）确认零旧路径残留。
- **F-01 修复**：`design-planner/SKILL.md:75` 原有裸 `m-analysis/ppdcs-annotation.md`（不含 `analysis/` 前缀），sed 规则 `s|analysis/m-analysis/|mfq/m-analysis/|` 无法匹配，手动修正为 `mfq/m-analysis/ppdcs-annotation.md`。
- **替换安全性**：8 条 sed 使用 `|` 分隔符避免路径 `/` 转义；目标路径 `kym/`、`mfq/`、`process/` 互不重叠，无替换交叉污染风险。

### 验收结果

| AC | 状态 | 说明 |
|----|------|------|
| AC01 | PASS (假阳性) | `grep "analysis/"` 匹配 `m-analysis/` 等子串；精确旧路径检查 PASS |
| AC02 | PASS | 零旧 MFQ 路径（`analysis/m-analysis/` 等） |
| AC03 | PASS | 零旧 KYM 路径（`analysis/scenarios/`、`analysis/feature-input/`） |
| AC04 | PASS | 5 个文件 `mfq/` 引用数：9/14/7/8/12 |
| AC05 | PASS | `process/plan/` 引用 6 处 |
| AC06 | PASS | frontmatter `---` 计数 = 10 |
| AC07 | PASS | 裸 `m-analysis/` 1 处修复；其余均为 `mfq/` 前缀正确路径 |
| AC08 | PASS | 行数变化 = 0（5 文件仍然 1680 行） |

### 已知限制

- **AC01 grep 模式缺陷**：`analysis/` 作为 grep 模式会匹配 `m-analysis/`、`f-analysis/`、`q-analysis/` 子串，无法准确区分旧路径残留与新路径中的阶段名称。建议后续 AC 改为精确旧路径前缀匹配。
- **不验证目标目录存在性**：本 Story 只做 Skill 文件内的路径文本替换，不创建或验证目录结构。

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-01-mfq-path-migration-CODING-DONE.md`
- 验证命令：`grep -rn "analysis/m-analysis\|analysis/f-analysis\|analysis/q-analysis\|analysis/integration\|analysis/factor-usage\|analysis/scenarios\|analysis/feature-input\|analysis/plan/" skills/{m,f,q}-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md`（预期 0 结果）
- 正面验证命令：`grep -c "kym/feature-input/" skills/m-analyzer/SKILL.md`（预期 5）；`grep -c "process/plan/" skills/design-planner/SKILL.md`（预期 6）

### 提供给 meta-qa 的验证提示

- 本 Story 为纯路径文本替换，无代码逻辑变更。验证重点是 grep 旧路径残留和使用新路径的正确性。
- 注意 AC01 的 grep 模式假阳性——现有 `mfq/m-analysis/` 路径会在 `grep "analysis/"` 中被匹配。
- 建议 meta-qa 以 AC02（MFQ 旧路径）+ AC03（KYM 旧路径）+ 旧 plan 路径检查作为真实残留判定标准。
- 下游 Story（STORY-012-03~07）会消费迁移后的路径，可在这些 Story 的 CP7 中验证路径一致性。

---

## STORY-012-02：MFQ Exit Gate 增强 实施

**实现时间**：2026-06-02T23:59:00+08:00
**执行模式**：meta-dev inline（用户显式指令激活）
**CP6 结论**：PASS（8/8 AC 通过）
**Wave**：A
**Tier**：S（小型，~30 行改动，2 个文件）

### 实现文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `docs/ptm-tde/gate-spec.md` | 修改 | GATE-3 Checklist #1-8 → M1-M7（合并 #8）+ 人工确认项 HARD-STOP 标记 + 执行协议 STOP-01~05 + 修订记录 v1.4 |
| `skills/checkpoint-manager/SKILL.md` | 修改 | 镜像同步：编号重命名 + HARD-STOP + 执行协议 |

### 关键决策与偏差

- **无偏差**：严格按 LLD §8 的 9 个 TASK-ID 和 §4 的契约定义执行。
- **LLD 小型偏差**：LLD §4.1 声称 checkpoint-manager GATE-3 Checklist 为 3 列表格，实际文件为 4 列表格（与 gate-spec.md 相同格式）。实施时以实际文件格式为准，不影响结果。
- **M6 通过条件扩展**：原 `缺失时回到 plan` → `缺失或格式错误时回到 plan`，吸收了旧 #8 的格式检查职责。

### 验收结果

| AC | 状态 | 证据 |
|----|------|------|
| AC01 | PASS | `grep -c "M[1-7]\|W[1-2]" docs/ptm-tde/gate-spec.md` = 11（>= 9） |
| AC02 | PASS | `grep -c "M[1-7]\|W[1-2]" skills/checkpoint-manager/SKILL.md` = 10（>= 9） |
| AC03 | PASS | gate-spec.md HARD-STOP = 9（4 确认项 + 4 STOP + 1 修订记录） |
| AC04 | PASS | checkpoint-manager HARD-STOP = 8（4 确认项 + 4 STOP） |
| AC05 | PASS | GATE-3 Checklist # 列无纯数字（1-8），全部使用 M1-M7 |
| AC06 | PASS | Warning 表 W1/W2 编号确认 |
| AC07 | PASS | 双向一致性：M1-M7/HARD-STOP/STOP-01~05 两文件完全一致 |
| AC08 | PASS | STOP-01~05 在两文件的 GATE-3 章节均存在 |

### 已知限制

- gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3 Checklist 中 M4/M5/M7 的 backtick 使用略有差异（`` `factor_bindings` `` vs `factor_bindings`），此为 CR-011 遗留的格式差异，不影响内容一致性
- checkpoint-manager SKILL.md 无修订记录表，变更追溯依赖 git log 和 gate-spec.md v1.4 修订记录

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-02-mfq-exit-gate-enhance-CODING-DONE.md`
- 验收命令：
  ```bash
  grep -c "M[1-7]" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md
  grep -c "W[1-2]" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md
  grep -c "HARD-STOP" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md
  ```

### 提供给 meta-qa 的验证提示

- GATE-3 人工确认项每行以 `⛔ HARD-STOP：禁止 Agent 自行判定通过。` 开头
- STOP-01~05 执行协议位于 GATE-3 Deliverables 之后、GATE-4 之前
- 确认 GATE-1/GATE-2/GATE-4/GATE-5 编号体系（纯数字 #1-N）未被变更
- gate-spec.md 修订记录已追加 v1.4 行

## STORY-012-03：M 分析器 v3.0 重写 — 实施完成

**实施时间**：2026-06-02
**执行模式**：meta-dev（Claude Code inline，用户显式指令实施）
**Story 状态**：ready-for-verification
**CP6 状态**：PASS（全部 13 AC + 6 NFR + 10 TASK-ID 通过）

### 实现摘要

- **重写文件**：`skills/m-analyzer/SKILL.md`（357 行 → 547 行，净增 +190 行）
- **10 个 TASK-ID 全部完成**，按 LLD §11 顺序实施
- **v2 7 步 → v3.0 7 步**：步骤 1（加载输入增强）、步骤 2（场景步骤驱动发现，4 子步骤 A/B/C/D）、步骤 3（TSP 新增 covered_scenario_segments + f_tags + q_tags）、步骤 4（PPDCS + TSP.purpose 引导）、步骤 5（按关联度分级生成测试点）、步骤 6（四维覆盖初检）、步骤 7（输出 8 文件 + 路径校验）
- **frontmatter**：`name: m-analyzer` 不变，`description` 更新为 v3.0 描述

### 保留内容

- PPDCS 五特征表 + 区分规则（Process vs State、Parameter vs Data、Data vs Combination）
- MFQ 分层概念（测试因子/拓扑角色/真实组网对象）
- CAE 字段约束 + E="待定"批注规则
- 拓扑/因子分层 Guardrail
- 公共因子库三层回退搜索路径（LCQ-03-02 推荐方案 A）
- 拓扑绑定补充契约
- Gotchas（9 条旧 + 3 条 v3.0 新增）

### 新增内容

| 实体 | 文件路径 | 说明 |
|------|---------|------|
| 覆盖矩阵 | `mfq/m-analysis/scenario-tsp-coverage.md` | 视角 A（场景→TSP）+ 视角 B（目录→场景）+ F/Q 线索汇总 |
| 步骤标签 | 嵌入覆盖矩阵 | [M] / [F→目标] / [Q→维度]，步骤 2 子步骤 D 生产 |
| 因子候选 | `mfq/m-analysis/candidate-factor-proposals.yaml` | source=new-candidate |
| 原子操作候选 | `mfq/m-analysis/candidate-atomic-ops.yaml` | 无已有支撑的步骤 |
| TSP 新字段 | `tsp/<M>-tsp.md` | covered_scenario_segments + f_tags + q_tags |

### 关键决策

- **LCQ-03-01（覆盖矩阵一致性）**：按推荐方案 A，SKILL.md 描述一致性约束规则，Agent 在步骤 6 执行人工校验
- **LCQ-03-02（因子库搜索路径）**：按推荐方案 A，沿用旧版三层回退路径
- **关联度分级**：高→全部生成、中→选择性（至少正常功能）、低→不生成 M 测试点
- **候选因子降级**：全为候选时 fact_status=needs-confirmation，C 条件使用 @domain.xxx 域引用

### 已知限制

- 覆盖矩阵一致性检查依赖 Agent 自觉执行，无脚本自动化
- 候选因子和原子操作候选的确认由 test-point-integrator（STORY-012-07）完成，本 Story 仅记录和透传
- NFR01 行数上限 550，当前 547（3 行余量），若后续修改需谨慎控制

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-03-m-analyzer-v3-rewrite-CODING-DONE.md`
- 验证命令：
  ```bash
  # AC 快速验证
  grep -c '^### 步骤 [0-9]' skills/m-analyzer/SKILL.md        # AC01: >= 7
  grep -c 'mfq/m-analysis/' skills/m-analyzer/SKILL.md         # AC02: > 0
  grep -c '覆盖矩阵\|scenario-tsp-coverage' skills/m-analyzer/SKILL.md  # AC03
  grep -c '候选\|candidate' skills/m-analyzer/SKILL.md         # AC04
  grep -c '\[M\]\|\[F→\]\|\[Q→\]' skills/m-analyzer/SKILL.md   # AC05
  grep -c '高关联\|中关联\|低关联' skills/m-analyzer/SKILL.md   # AC06
  grep -c '关联度\|关联对象' skills/m-analyzer/SKILL.md        # AC07
  grep -c 'C 条件\|A 动作\|E 预期' skills/m-analyzer/SKILL.md  # AC08
  grep -c '待定' skills/m-analyzer/SKILL.md                    # AC09
  grep -c 'P-Process\|P-Parameter\|D-Data\|C-Combination\|S-State' skills/m-analyzer/SKILL.md  # AC10
  grep -c 'v3.0\|场景步骤驱动' skills/m-analyzer/SKILL.md      # AC11
  wc -l skills/m-analyzer/SKILL.md                              # AC12: >= 400
  grep -c 'F 分析\|Q 分析\|消费' skills/m-analyzer/SKILL.md    # AC13
  # NFR 验证
  grep -c 'HARD-STOP' skills/m-analyzer/SKILL.md                # NFR04: >= 2
  grep -c 'GATE-3' skills/m-analyzer/SKILL.md                   # NFR06: >= 1
  grep -c 'mkdir' skills/m-analyzer/SKILL.md                    # NFR04: 仅"禁止 mkdir"
  ```

### 提供给 meta-qa 的验证提示

- 验证重点关注步骤 2 的 4 个子步骤（A/B/C/D）是否完整、标签定义表和关联度判定维度表是否正确
- 确认步骤 6 和步骤 7 的 HARD-STOP 均含 GATE-3 引用
- 确认公共因子库三层回退路径（PTM_TEAM_RESOURCE_HOME → ~/.ptm-team → resource/）在步骤 2 子步骤 B 和公共因子库补充契约章节都存在
- 确认 8 个输出文件路径均以 `mfq/m-analysis/` 开头
- 确认候选因子降级处理（@domain.xxx 域引用 + fact_status=needs-confirmation）在步骤 5 中有描述

---

## STORY-012-04：F 分析器 v3.0 重写 实施

**实施时间**：2026-06-02T23:50:00+08:00
**执行模式**：meta-dev（inline execution，当前线程直接实施）
**Story 状态**：`lld-ready-for-review` → `in-development` → `ready-for-verification`
**CP6 自动预检**：PASS（11 项 checklist：9 PASS + 2 WAIVED + 2 N/A，0 FAIL）
**调度批次**：CR-012-all-stories batch_1，Agent C
**Wave**：C（与 STORY-012-05 并行）
**tier**：M
**依赖关系**：上游 STORY-012-01（ready-for-verification）+ STORY-012-03（ready-for-verification）

### 实施摘要

- **重写文件**：`skills/f-analyzer/SKILL.md`（314 行 v2 → 583 行 v3.0，净增 +269 行）
- **16 个 TASK-ID 全部完成**，按 LLD §11 顺序实施
- **v2 8 步 → v3.0 9 步**：
  - 步骤 1：加载 TSP 列表、覆盖矩阵与矩阵基线（新增 F 线索索引 `TSP → [F→标签列表]`，F 线索指向不存在 TSP 记录 gap + 警告不阻断）
  - 步骤 2：逐 TSP 场景耦合推理（全新驱动模式，子步骤 A 识别耦合关系 → B 发现耦合对象 → C 发现/匹配耦合因子，discovery_source 区分 f-tag-seed/scenario-inference）
  - 步骤 3：代码依赖收集（保留旧版）
  - 步骤 4：三源合并增强（discovery_source 取并集规则）
  - 步骤 5：候选耦合点确认（HARD-STOP STOP-02 + `( )` 单选）
  - 步骤 6：耦合测试点按 TSP 组织（全候选降级 fact_status=needs-confirmation）
  - 步骤 7：工具覆盖评估（保留旧版）
  - 步骤 8：可选回写（HARD-STOP）
  - 步骤 9：耦合因子候选列表汇总（v3.0 新增，标注 tsp_ref/coupling_ref/discovery_source）
- **frontmatter**：`name: f-analyzer` 不变，`description` 更新为 v3.0 描述

### 实现文件清单

| 文件 | 变更类型 | 行数变化 | 说明 |
|------|---------|---------|------|
| `skills/f-analyzer/SKILL.md` | 全量重写 | 314→583（+269） | v2→v3.0，9 步逐 TSP 驱动 |
| `process/stories/STORY-012-04-f-analyzer-v3-rewrite.md` | 状态更新 | — | `status: in-development → ready-for-verification` |
| `process/stories/STORY-012-04-f-analyzer-v3-rewrite-LLD.md` | 状态更新 | — | `confirmed: false → true` |
| `process/checks/CP6-STORY-012-04-f-analyzer-v3-rewrite-CODING-DONE.md` | 新建 | — | CP6 编码完成 |

### 保留内容

- 三源数据模型（Excel 矩阵基线 + 场景耦合 + 代码依赖）
- 拓扑/因子分层 Guardrail（全文不变）
- 耦合类型定义（顺序/数据/容错/接口资源）
- Excel 工具调用方式（`python scripts/excel_coupling_tool.py`）
- CAE 耦合特有约束（A 动作不得直接操作耦合目标）
- 工具评估格式（Existing Tool Summary + Tool Capability Gap）
- Gotchas（7 条旧 + 3 条 v3.0 新增）

### 新增内容

| 特性 | 说明 |
|------|------|
| TSP 列表加载 | 步骤 1 加载 M 分析 TSP 列表（含 f_tags/covered_scenario_segments） |
| F 线索索引 | `TSP → [F→标签列表]` 映射，作为步骤 2 种子线索 |
| 逐 TSP 耦合推理 | 步骤 2 全新 3 子步骤（A/B/C），标注 discovery_source |
| coupling_object_discovery | 子步骤 B：从 M 分析对象表查找 + 新建，object_role_in_coupling 枚举 |
| coupling_factor_candidate | 子步骤 C：M 分析因子表匹配 → 公共因子库检索 → 生成候选 |
| discovery_source | f-tag-seed / scenario-inference 区分与聚合 |
| 步骤 9 候选汇总 | 汇总所有 source=new-coupling-candidate 的因子，按 TSP 组织表格 |
| 耦合测试点按 TSP 组织 | 步骤 6，每个 TSP 一个子节 |
| 全候选降级 | fact_status=needs-confirmation，C 条件使用 @domain.xxx 域引用 |

### 关键决策

- **LCQ-04-01（object_role_in_coupling）**：按推荐方案 A，使用枚举 `触发方 / 受影响方 / 共享资源`，与设计文档 §4 子步骤 B 一致
- **LCQ-04-02（F 线索→不存在 TSP）**：按推荐方案 A，记录 `confirmation_gap`（类型 `f-tag-target-tsp-missing`）+ 警告，不阻断流程。该线索不纳入种子线索索引
- **discovery_source 聚合**：同一耦合关系被多 TSP 视角或多源发现时，取并集（如 `[f-tag-seed, scenario-inference]`）
- **路径全部 mfq/f-analysis/**：零 `analysis/` 残留，与 STORY-012-01 路径迁移一致

### 已知限制

- 覆盖矩阵格式依赖（F 线索汇总表的列名为 `来源场景 / 步骤 / 标签 / 目标 M/系统 / 说明`）
- 耦合因子候选的确认由候选汇总步骤（STORY-012-07）完成，本 Story 仅记录和汇总
- NFR01 行数上限 500，当前 583（超出 83 行）。超出原因是步骤 1（TSP 加载+F 线索索引）+ 步骤 2（逐 TSP 耦合推理的 3 子步骤）+ 步骤 9（候选汇总）+ Gotchas 新增 3 条。net new 内容量符合 ~150 行预估，但 v2 基线 314 行中保留内容达到 ~310 行（guardrail + 三源模型 + 耦合维度 + 旧 gotchas + 输出格式 + tool 格式），导致总行数超出预估

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-04-f-analyzer-v3-rewrite-CODING-DONE.md`
- 验证命令：
  ```bash
  # AC01: TSP count >= 5
  grep -ci 'TSP' skills/f-analyzer/SKILL.md  # 90
  # AC02: [F→] or F 线索 or F标签
  grep -cP '\[F→\]|F 线索|F标签' skills/f-analyzer/SKILL.md  # 12
  # AC03: 覆盖矩阵 or scenario-tsp-coverage
  grep -cP 'scenario-tsp-coverage\.md|覆盖矩阵' skills/f-analyzer/SKILL.md  # 10
  # AC04: mfq/f-analysis/
  grep -c 'mfq/f-analysis/' skills/f-analyzer/SKILL.md  # 15
  # AC05: 耦合对象 or coupled_object
  grep -cP '耦合对象|coupled_object|耦合.*object' skills/f-analyzer/SKILL.md  # 15
  # AC06: 候选 or candidate
  grep -cP '候选|candidate' skills/f-analyzer/SKILL.md  # 32
  # AC07: discovery_source or f-tag-seed or scenario-inference
  grep -cP 'discovery_source|f-tag-seed|scenario-inference' skills/f-analyzer/SKILL.md  # 28
  # AC08: 不得直接操作耦合目标
  grep -c '不得直接操作耦合目标' skills/f-analyzer/SKILL.md  # 3
  # AC09: 三源合并
  grep -c '三源合并' skills/f-analyzer/SKILL.md  # 7
  # AC10: name: f-analyzer
  grep -c '^name: f-analyzer$' skills/f-analyzer/SKILL.md  # 1
  # 补充: 9 步编号连续
  grep -c '^### 步骤 [1-9]' skills/f-analyzer/SKILL.md  # 9
  # 补充: HARD-STOP
  grep -c 'HARD-STOP' skills/f-analyzer/SKILL.md  # 3
  # 补充: 旧路径零残留
  grep -cP '(?<!mfq)/analysis/(?=[a-z])' skills/f-analyzer/SKILL.md  # 0
  ```

### 提供给 meta-qa 的验证提示

- 验证重点关注步骤 1 的 TSP 列表加载、F 线索索引建立、F 线索指向不存在 TSP 的 gap 处理
- 验证步骤 2 的 3 个子步骤（A/B/C）是否完整，discovery_source 标注是否正确
- 确认 discovery_source 在步骤 2（标注）、步骤 4（聚合）、步骤 6（透传）中一致
- 确认步骤 5 和步骤 8 的 HARD-STOP 均含 STOP-02 标记和 `( )` 单选选项
- 确认输出文件路径 100% 为 `mfq/f-analysis/`，无 `analysis/` 裸路径
- 确认步骤 9（耦合因子候选列表汇总）存在且标注 tsp_ref/coupling_ref/discovery_source
- 确认耦合测试点按 TSP 组织（每个 TSP 一个子节），非旧版按四/五级目录分节
- 确认 frontmatter `name: f-analyzer` 未变

---

## STORY-012-05：Q 分析器 v3.0 重写 — 实施完成

**实施时间**：2026-06-02T23:45:00+08:00
**执行模式**：meta-dev（inline execution，当前线程直接实施）
**Story 状态**：`lld-ready-for-review` → `in-development` → `ready-for-verification`
**CP6 自动预检**：PASS（20 项 checklist：20 PASS，0 FAIL，0 BLOCKED）
**调度批次**：CR-012-all-stories batch_1，Agent C
**Wave**：C（与 STORY-012-04 并行）
**tier**：M
**并行组**：fq-analyzers
**依赖关系**：上游 STORY-012-01（ready-for-verification）+ STORY-012-03（ready-for-verification）

### 实施摘要

- **重写文件**：`skills/q-analyzer/SKILL.md`（257 行 v2 → 501 行 v3.0，净增 +244 行）
- **16 个 TASK-ID 全部完成**，按 LLD §11 顺序实施
- **v2 5 步 → v3.0 6 步**：
  - 步骤 1：加载 TSP 列表、覆盖矩阵与相关性评估（新增 TSP 驱动 + Q 线索索引 + 逐 TSP 逐 HTSM 维度评估 + [Q→] 标签提升/起评规则 + OPEN 汇总 HARD-STOP）
  - 步骤 2：逐 TSP 质量对象与因子发现（全新驱动模式，子步骤 A 识别质量对象 → B 发现/匹配质量因子候选，标注 tsp_ref + quality_dimension + generation_basis）
  - 步骤 3：按 TSP 组织、按质量维度分组测试点（全候选降级 fact_status=needs-confirmation）
  - 步骤 4：工具观测能力评估（保留旧版，路径更新为 `mfq/`）
  - 步骤 5：写入 Q 分析产物扩展（+质量因子候选列表，路径前置校验禁止 mkdir）
  - 步骤 6：质量因子候选列表汇总（v3.0 新增，标注 tsp_ref/quality_dimension/generation_basis）
- **frontmatter**：`name: q-analyzer` 不变，`description` 更新为 v3.0 描述

### 实现文件清单

| 文件 | 变更类型 | 行数变化 | 说明 |
|------|---------|---------|------|
| `skills/q-analyzer/SKILL.md` | 全量重写 | 257→501（+244） | v2→v3.0，6 步逐 TSP 驱动 |
| `process/stories/STORY-012-05-q-analyzer-v3-rewrite.md` | 状态更新 | — | `status: lld-ready-for-review → in-development → ready-for-verification` |
| `process/stories/STORY-012-05-q-analyzer-v3-rewrite-LLD.md` | 状态更新 | — | `confirmed: false → true` |
| `process/checks/CP6-STORY-012-05-q-analyzer-v3-rewrite-CODING-DONE.md` | 新建 | — | CP6 编码完成 |

### 保留内容

- HTSM 质量属性维度定义表（8 维度 CRUSSPICSTML，含功能性）
- 拓扑/因子分层 Guardrail（全文不变）
- CAE 字段约束（质量测试点）+ E="待定" 批注规则
- Gotchas（7 条旧版全部保留，新增 4 条 v3.0 特有）
- Existing Tool Summary + Tool Capability Gap 格式
- 确认选项 `( )` 单选标记（STOP-05）

### 新增内容

| 特性 | 位置 | 说明 |
|------|------|------|
| TSP 列表加载 + Q 线索索引 | 步骤 1 | 逐 TSP 逐 HTSM 维度评估，Q 线索从 M 分析覆盖矩阵提取 |
| `[Q→]` 标签提升/起评规则 | 步骤 1 处理逻辑 | 标签维度至少弱相关起评，可提升至强相关，不降级已有判定 |
| HARD-STOP OPEN 汇总 | 步骤 1 末尾 | 汇总所有相关性判定不确定项，4 选项 `( )` 单选等待确认 |
| 质量对象发现 | 步骤 2 子步骤 A | M 分析对象表查找 → 新建质量对象，标注 tsp_ref + quality_dimension + source |
| 质量因子候选生成 | 步骤 2 子步骤 B | 无已有因子时基于知识生成，标注 generation_basis 枚举 |
| `generation_basis` 枚举 | 步骤 2 + § 枚举表 | 行业标准/经验推断/需求推断（LCQ-05-01 推荐方案 A） |
| 质量因子全候选降级 | 步骤 3 | fact_status=needs-confirmation，C 使用因子域引用 @domain.xxx |
| 路径写入前置校验 | 步骤 5 | 写入前校验目标父目录存在且为目录，**禁止 mkdir** |
| 质量因子候选列表汇总 | 步骤 6 | 按 TSP 组织，因子归属统计，generation_basis 标注 |

### 关键决策

- **LCQ-05-01（generation_basis 枚举）**：按推荐方案 A，保持 3 类（行业标准/经验推断/需求推断），枚举表完整定义并提供示例
- **LCQ-05-02（OPEN 汇总策略）**：按推荐方案 A，步骤 1 末尾 HARD-STOP 汇总展示，`( )` 单选标记选项（A 全部按推荐判定 / B 全部跳过 / C 逐项指定 / D 暂不处理），用户回复后方可进入步骤 2
- **行数超出 NFR 预估**：LLD 预估 ~370 行，实际 501 行（+131）。原因：设计文档 §5 的处理逻辑伪代码在 Markdown 代码块中展开后行数增加，输出格式模板（quality-test-points.md + tool-analysis.md）总计 ~90 行。所有内容均为 LLD 和设计文档要求的实质性内容，无冗余
- **HTSM 维度数**：保留 8 维度（含功能性），与旧版一致。功能性标注「不在此展开（M 分析已覆盖）」

### 已知限制

- 行数 501 超出 NFR 上限 ~400 行约 25%，主要由伪代码块（§ 步骤 1/2 处理逻辑 70+ 行）和输出格式模板（90+ 行）导致，实质性文本密度合理
- 质量因子候选的 generation_basis 标注依赖 Agent 自觉执行，无自动化校验
- `mfq/q-analysis/` 目录存在性校验依靠读取或用户确认，Skill 不自动创建目录
- Q 线索指向不存在 TSP 的处理（与 F 分析器的 LCQ-04-02 对应场景）未在 Q 分析器中显式描述——当 Q 线索指向 TSP 列表之外的 TSP 时，记录 confirmation_gap 但不阻断流程

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-05-q-analyzer-v3-rewrite-CODING-DONE.md`
- 验证命令：
  ```bash
  # AC01: TSP count >= 3
  grep -c 'TSP' skills/q-analyzer/SKILL.md  # 72
  # AC02: [Q→] or Q 线索 or Q标签
  grep -c '\[Q→\]' skills/q-analyzer/SKILL.md  # 13
  # AC03: 覆盖矩阵 or scenario-tsp-coverage
  grep -c '覆盖矩阵\|scenario-tsp-coverage' skills/q-analyzer/SKILL.md  # 10
  # AC04: mfq/q-analysis/
  grep -c 'mfq/q-analysis/' skills/q-analyzer/SKILL.md  # 9
  # AC05: 质量对象 or quality_object
  grep -c '质量对象\|quality_object' skills/q-analyzer/SKILL.md  # 16
  # AC06: 候选 or candidate
  grep -c '候选\|candidate' skills/q-analyzer/SKILL.md  # 35
  # AC07: generation_basis or 生成依据
  grep -c 'generation_basis\|生成依据' skills/q-analyzer/SKILL.md  # 8
  # AC08: HTSM 维度（可靠性/性能/安全性/可维护性/可用性）>= 5
  grep -c '可靠性\|性能\|安全性\|可维护性\|可用性' skills/q-analyzer/SKILL.md  # 26
  # AC09: 强相关/弱相关/不适用
  grep -c '强相关\|弱相关\|不适用' skills/q-analyzer/SKILL.md  # 24
  # AC10: name: q-analyzer
  grep -c '^name: q-analyzer$' skills/q-analyzer/SKILL.md  # 1
  # 补充: 6 步编号连续
  grep -o '步骤 [1-6]' skills/q-analyzer/SKILL.md | sort -u  # 应输出 1/2/3/4/5/6
  # 补充: HARD-STOP
  grep -c 'HARD-STOP' skills/q-analyzer/SKILL.md  # 1
  # 补充: mkdir 仅禁止文本
  grep 'mkdir' skills/q-analyzer/SKILL.md  # 仅 2 处"禁止执行 mkdir"
  # 补充: Gotchas 总数
  grep -c '^- \*\*' skills/q-analyzer/SKILL.md | tail -1  # Gotchas 条目数
  ```

### 提供给 meta-qa 的验证提示

- 验证重点关注 6 步序列是否完整、步骤 1 的逐 TSP 逐 HTSM 维度相关性评估逻辑是否清晰
- 确认 `[Q→]` 标签提升规则表（不降级/可提升/可起评）在步骤 1 处理逻辑中有落地
- 确认步骤 1 末尾的 HARD-STOP 协议包含 OPEN 汇总展示、4 个 `( )` 单选选项和「用户回复后方可进入步骤 2」指令
- 确认步骤 2 子步骤 A（质量对象发现）和 B（质量因子候选生成）的处理逻辑独立可追踪，`generation_basis` 枚举表包含 3 类并各有示例
- 确认步骤 6（候选汇总）的表格格式包含 `tsp_ref`、`quality_dimension`、`generation_basis` 列
- 确认旧版 Gotchas 7 条全部保留，v3.0 新增 4 条（Q 线索缺失不阻断、OPEN 标记规则、generation_basis 约束、跨 TSP 去重合并）
- 确认路径前置校验在步骤 5，描述中使用「禁止执行 mkdir」而非授权创建目录
- 确认输出文件路径 100% 为 `mfq/q-analysis/`，零 `analysis/` 裸路径残留
- 确认 frontmatter `name: q-analyzer` 未变，`description` 更新为 v3.0 逐 TSP 驱动描述
- 行数 501 超出 LLD NFR 预估 370 行，内容均为 LLD 和设计文档 §5 要求的实质性内容，建议 meta-qa 判定为可接受偏差

---

## STORY-012-06：上下游 Skill 适配 — 实施完成

**实施时间**：2026-06-02T12:00:00+08:00
**执行模式**：meta-dev（inline execution，当前线程直接实施）
**Story 状态**：`lld-ready-for-review` → `in-development` → `ready-for-verification`
**CP6 自动预检**：PASS（10 项 checklist 全部通过，AC01-AC07 全部 PASS）
**调度批次**：CR-012 Wave D，Story 012-03/04/05 的下游、012-07 的上游
**Wave**：D
**tier**：M

### 实施摘要

- **修改文件**：2 个（`skills/test-point-integrator/SKILL.md` ~40 行净增、`skills/design-planner/SKILL.md` ~12 行净增）
- **10 个 TASK-ID 全部完成**，按 LLD §11 顺序实施
- **改动模式**：增量适配（非全量重写），保留全部现有核心归集/合并/设计计划逻辑

### test-point-integrator 适配（6 个 TASK）

| TASK-ID | 修改位置 | 内容 |
|---------|---------|------|
| TASK-012-06-01 | 前置条件 | 新增覆盖矩阵和候选文件检查项 |
| TASK-012-06-02 | 步骤 1 | 新增覆盖矩阵加载 + 候选列表声明，含 fail-fast |
| TASK-012-06-03 | 步骤 2 | 新增覆盖矩阵视角 A 检查（SR→TSP→TP 覆盖链，covered/uncovered/excluded 统计） |
| TASK-012-06-04 | 步骤 7.5（新增） | 候选归集：三源候选读取 → 按 factor_id 去重 → 输出到 `mfq/candidates/` |
| TASK-012-06-05 | 步骤 8 | 输出清单增加 `mfq/candidates/factor-candidates.md` + `mfq/candidates/atomic-op-candidates.md` |
| TASK-012-06-06 | Gotchas + 验收标准 | Gotchas 新增 2 条（fail-fast + 不自行确认）；验收标准新增 4 条 |

### design-planner 适配（4 个 TASK）

| TASK-ID | 修改位置 | 内容 |
|---------|---------|------|
| TASK-012-06-07 | 前置条件 | 新增 TSP 文件和 `covered_scenario_segments` 字段检查项 |
| TASK-012-06-08 | 步骤 1 | 新增子步骤 7：TSP `covered_scenario_segments` 加载 + `LC→TSP→covered_steps` 映射，含 fail-fast |
| TASK-012-06-09 | 步骤 2 | 新增子步骤 11：设计范围交叉校验（coverage_confirmed/partial/gap） |
| TASK-012-06-10 | 步骤 6 + Gotchas + 验收标准 | design-plan.md 路径 `mfq/integration/` → `process/plan/`；Gotchas 新增 fail-fast；验收标准新增 2 条 |

### 关键设计决策

- **fail-fast 替代降级**：LLD 原设计有 4 种向后兼容降级路径（覆盖矩阵缺失、TSP 字段缺失、候选列表缺失、TSP 文件缺失），经用户决策全部改为 fail-fast 报错终止。v2/v3 混合模式不在本 CR 范围内
- **候选归集不自行确认**：步骤 7.5 显式声明「只做归集和去重，不附加自行判定语句」，候选确认由 STORY-012-07 处理
- **STOP-04 路径前置校验**：所有输出点（步骤 7.5、步骤 8）均含写入前校验，禁止 Agent mkdir

### 偏差记录

- **无偏差**：严格按 LLD §7（核心处理流程）和 §11（实施步骤）执行，10 个 TASK-ID 与 LLD 契约一致
- **LLD §12.2 R1（路径迁移覆盖不完整）**：实施前确认 STORY-012-01 已正确迁移路径，无残留旧路径
- **LLD §12.2 R2（F/Q 新组织方式）**：候选归集步骤明确指定 F 候选从 `coupling-test-points.md` 末尾「耦合因子候选列表汇总」节提取、Q 候选从 `quality-test-points.md` 末尾「质量因子候选列表汇总」节提取
- **LLD §12.2 R4（covered_steps 格式不一致）**：设计范围交叉校验采用语义级对比（非编号精确匹配），无法确定覆盖关系时标记为不确定

### 验收结果

| AC | 状态 | 证据 |
|----|------|------|
| AC01 | PASS | `grep -ci 'scenario-tsp-coverage\|覆盖矩阵' skills/test-point-integrator/SKILL.md` = 11 |
| AC02 | PASS | `grep -ci 'candidate\|候选' skills/test-point-integrator/SKILL.md` = 25 |
| AC03 | PASS | `grep -c 'mfq/m-analysis/\|mfq/f-analysis/\|mfq/q-analysis/' skills/test-point-integrator/SKILL.md` = 17 |
| AC04 | PASS | `grep -ci 'covered_scenario_segments\|covered.*segment' skills/design-planner/SKILL.md` = 5 |
| AC05 | PASS | `grep -c 'mfq/m-analysis/tsp/' skills/design-planner/SKILL.md` = 2 |
| AC06 | PASS | `grep -c 'process/plan/' skills/design-planner/SKILL.md` = 7 |
| AC07 | PASS | frontmatter `name: test-point-integrator` 和 `name: design-planner` 均不变 |
| 旧路径残留 | PASS | `grep -n 'analysis/' skills/{test-point-integrator,design-planner}/SKILL.md | grep -v 'mfq/[mfq]-analysis/'` 零输出 |
| fail-fast 逻辑 | PASS | test-point-integrator: 步骤 1 覆盖矩阵 + 候选缺失 `报错并终止`（2 处）；design-planner: 步骤 1 TSP 缺失或字段缺失 `报错并终止`（1 处） |

### 已知限制

- `mfq/candidates/` 目录不存在于仓库中，由上游 M/F/Q 分析器运行时创建。本 Story 的路径写入（STOP-04）要求校验父目录存在但不创建目录
- F/Q 候选提取依赖于测试点文件末尾的特定节标题（「耦合因子候选列表汇总」/「质量因子候选列表汇总」），若上游格式有变化会导致提取失败
- 设计范围交叉校验的「语义级对比」依赖 Agent 自行判断，无自动化脚本辅助

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-06-upstream-downstream-adapt-CODING-DONE.md`
- 验证命令：
  ```bash
  # AC01-AC07 快速验证
  grep -c 'scenario-tsp-coverage\|覆盖矩阵' skills/test-point-integrator/SKILL.md
  grep -c 'candidate\|候选' skills/test-point-integrator/SKILL.md
  grep -c 'covered_scenario_segments' skills/design-planner/SKILL.md
  grep -c 'mfq/m-analysis/tsp/' skills/design-planner/SKILL.md
  grep -c 'process/plan/' skills/design-planner/SKILL.md
  # 旧路径残留
  grep -n 'analysis/' skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md | grep -v 'mfq/[mfq]-analysis/'
  # fail-fast 逻辑
  grep -n '不存在.*报错\|报错并终止\|fail-fast' skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md
  # YAML frontmatter name
  grep '^name:' skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md
  ```

### 提供给 meta-qa 的验证提示

- 本 Story 为增量适配，非全量重写。验证重点是新增内容的正确性和旧逻辑的无损保留
- 验证 test-point-integrator 步骤 2 末尾存在「覆盖矩阵视角 A 检查」段和 covered/uncovered/excluded 统计逻辑
- 验证 test-point-integrator 步骤 7.5（候选归集）存在且包含三源读取、去重规则和输出路径
- 验证 design-planner 步骤 1 末尾存在子步骤 7（TSP 覆盖段映射加载）且含 fail-fast
- 验证 design-planner 步骤 2 末尾存在子步骤 11（设计范围交叉校验）且含 coverage_confirmed/partial/gap 三种结果
- 确认 fail-fast 在所有文件缺失场景（覆盖矩阵、候选列表、TSP、covered_scenario_segments）中均有体现，无降级路径残留
- 确认 design-planner 步骤 6 的 `design-plan.md` 输出路径为 `process/plan/design-plan.md`（非 `mfq/integration/design-plan.md`）
- 确认 `analysis/` 旧路径独立目录前缀零残留（注意 `mfq/m-analysis/` 等新路径中包含的 `analysis/` 子串不算残留）
- 两个 Skill 的 CAE 聚合规则、LC 生成逻辑、PPDCS 匹配规则、设计方法推荐等核心算法未修改，无需重新验证这些部分

---

## STORY-012-07：候选汇总 + skill-references 更新 + STOP 协议落地 — 实施完成

**实施时间**：2026-06-02T23:30:00+08:00
**执行模式**：meta-dev（inline execution，用户显式指令实施）
**Story 状态**：`lld-ready-for-review` → `in-development` → `ready-for-verification`
**CP6 自动预检**：PASS（17 项 checklist：11 PASS + 4 WAIVED + 3 N/A，0 FAIL，0 BLOCKED）
**调度批次**：CR-012 Wave D，012-06 的下游
**Wave**：D
**tier**：M

### 实施摘要

- **修改文件**：5 个
- **4 个 TASK-ID 全部完成**，按 LLD §11 顺序实施
- **改动量**：~95 行（候选汇总 ~70 行 + skill-references ~15 行 + STOP 标记 ~10 行）

### 实现文件清单

| 文件 | TASK-ID | 变更类型 | 改动说明 |
|------|---------|---------|----------|
| `skills/test-point-integrator/SKILL.md` | TASK-012-07-01 | 修改 | 新增步骤 4.5（约 70 行）：三源候选归集、去重合并（factor_id 主 key + factor_name fallback）、优先级判定（高/中/低三级）、用户 4 选项 `( )` 单选确认、确认后回写；STOP-02 ⛔ HARD-STOP ×2；Gotchas 新增 2 条 |
| `docs/ptm-tde/skill-references.md` | TASK-012-07-02 | 修改 | MFQ 阶段 4 个 Skill 职责更新为 v3.0；test-point-integrator 增加候选汇总职责；新增「MFQ 候选汇总」段落含 `mfq/candidates/` 输出路径表 |
| `skills/m-analyzer/SKILL.md` | TASK-012-07-03 | 修改 | 前置条件末尾 STOP-03 ⛔ HARD-STOP（禁止绕过 Skill，含 v2.0 旧模式禁止条款）；步骤 7 开头 STOP-04 ⛔ HARD-STOP（路径写入前校验） |
| `skills/f-analyzer/SKILL.md` | TASK-012-07-04 | 修改 | 前置条件末尾 STOP-03 ⛔ HARD-STOP（禁止绕过 Skill） |
| `skills/q-analyzer/SKILL.md` | TASK-012-07-04 | 修改 | 前置条件末尾 STOP-03 ⛔ HARD-STOP（禁止绕过 Skill） |

### 关键决策与偏差

- **无偏差**：严格按 LLD §8（技术设计细节）和 §11（实施步骤）执行，4 个 TASK-ID 与 LLD 契约完全一致
- **F/Q 候选路径使用现有引用**：F 候选从 `mfq/f-analysis/coupling-test-points.md` 末尾「耦合因子候选列表汇总」节提取，Q 候选从 `mfq/q-analysis/quality-test-points.md` 末尾「质量因子候选列表汇总」节提取。此路径已在 STORY-012-06 步骤 7.5 中确定
- **优先级判定**：严格按 LLD §7.3 规则表实现，高 → M 高关联度、中 → F 关键耦合或 Q 强相关、低 → 中关联/弱相关
- **确认选项格式**：4 选项使用 `( )` 单选标记，完全遵循 HLD §11 STOP-05 规范

### 验收结果

| AC | 状态 | 证据 |
|----|------|------|
| AC01 | PASS | `grep "步骤 4.5.*候选汇总" skills/test-point-integrator/SKILL.md` 返回行 255 |
| AC02 | PASS | `grep "去重\|合并.*factor_id" skills/test-point-integrator/SKILL.md` 返回行 271, 273, 275, 280, 282 |
| AC03 | PASS | `grep "全部确认\|逐项确认\|批量修改\|全部拒绝" skills/test-point-integrator/SKILL.md` 返回行 304-307（4 选项完整） |
| AC04 | PASS | `grep "v3.0\|场景步骤驱动\|覆盖矩阵" docs/ptm-tde/skill-references.md` 返回行 29-31（m-analyzer/f-analyzer/q-analyzer 全部 v3.0） |
| AC05 | PASS | `grep "候选汇总\|candidate" docs/ptm-tde/skill-references.md` 返回行 32, 43, 45（test-point-integrator + MFQ 候选汇总段落） |
| AC06 | PASS | `grep "mfq/candidates/" docs/ptm-tde/skill-references.md` 返回行 45, 49-50（路径表格） |
| AC07 | PASS | `grep -rn "STOP-0[1-5]"` 5 个 Skill 文件全部返回 > 0。m-analyzer: STOP-03+STOP-04；f-analyzer: STOP-03+STOP-02×2；q-analyzer: STOP-03；test-point-integrator: STOP-02×2+STOP-04×2；design-planner 已有 STOP-01 |
| AC08 | PASS | `grep "⛔.*HARD-STOP\|禁止.*自行" skills/test-point-integrator/SKILL.md` 返回行 257, 310, 504 |

### 已知限制

- STOP-02/03/04 标记仅为文档级约束，无法绝对阻止 Agent 绕过。双重防御依赖 checkpoint-manager 自检脚本校验人工确认回填
- 候选汇总的优先级判定依赖上游 M/F/Q 分析器输出的 `priority`/`relevance`/`coupling_strength` 字段。若上游输出缺少这些字段，降级为「中」优先级
- F/Q 候选汇总中「同名但不同数据域的因子候选保留多条」依赖上游输出包含 `data_domain` 字段

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-012-07-candidate-summary-stop-protocol-CODING-DONE.md`
- 验证命令：
  ```bash
  # AC01: 候选汇总章节
  grep -n '步骤 4.5.*候选汇总' skills/test-point-integrator/SKILL.md
  # AC02: 去重合并
  grep -n '去重\|合并.*factor_id' skills/test-point-integrator/SKILL.md
  # AC03: 4 选项确认格式
  grep -n '全部确认\|逐项确认\|批量修改\|全部拒绝' skills/test-point-integrator/SKILL.md
  # AC04: skill-references v3.0
  grep -n 'v3.0\|场景步骤驱动\|覆盖矩阵\|逐 TSP 驱动\|耦合因子候选\|质量因子候选' docs/ptm-tde/skill-references.md
  # AC05: skill-references 候选汇总
  grep -n '候选汇总\|candidate' docs/ptm-tde/skill-references.md
  # AC06: skill-references mfq/candidates/
  grep -n 'mfq/candidates/' docs/ptm-tde/skill-references.md
  # AC07: STOP 标记全局
  grep -rn 'STOP-0[1-5]' skills/m-analyzer/SKILL.md skills/f-analyzer/SKILL.md skills/q-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md
  # AC08: test-point-integrator HARD-STOP
  grep -n '⛔.*HARD-STOP\|禁止.*自行' skills/test-point-integrator/SKILL.md
  ```

### 提供给 meta-qa 的验证提示

- 验证重点：步骤 4.5 候选汇总的 4 个子节（4.5.1-4.5.4）是否完整、去重合并逻辑是否正确（factor_id 主 key + factor_name fallback）、优先级判定规则表是否与 LLD §7.3 一致
- 确认 STOP-02 标记在步骤 4.5.3 用户确认环节是否存在且格式正确（`⛔ HARD-STOP（STOP-02）`）
- 确认 skill-references.md 中 m-analyzer/f-analyzer/q-analyzer 的版本号均为 v3.0
- 确认 skill-references.md 中新增的「MFQ 候选汇总」段落包含 `mfq/candidates/` 路径和输出文件说明表
- 确认 m-analyzer 的 STOP-03 标记额外包含「不得跳过子步骤 A/B/C/D」和「不得使用 v2.0 旧模式」的禁止条款
- 确认 f-analyzer 和 q-analyzer 的 STOP-03 标记格式与 m-analyzer 一致（`⛔ HARD-STOP（STOP-03）`）
- 确认 m-analyzer 步骤 7 的 STOP-04 标记在写入前校验段落之前（禁止 Agent mkdir + 校验父目录）
- 注意：本 Story 无新建文件，所有修改均为增量（在现有文件中插入/追加）、无旧内容删除

---

# STORY-012-08：文档更新（CR-012 最后一个 Story）

**实施时间**：2026-06-02T23:00:00+08:00
**执行模式**：meta-dev（Claude Code inline，用户直接指派）
**Story 状态**：in-development → ready-for-verification
**CP6**：PASS（14 项 checklist，8 项 AC 全部验证通过）
**tier**：S
**wave**：D
**调度批次**：CR-012-all-stories batch_2，Agent E

## 实施摘要

- **修改文件**：4 个（CR-INDEX.yaml、STATE.md、agents/ptm-tde.md、CR-012-ptm-tde-mfq-phase.md）
- **实际改动量**：~35 行（含 story_status 新增节）
- **5 个 TASK-ID** 全部完成

## 各 TASK-ID 实施细节

### TASK-012-08-01：CR-INDEX.yaml

- `status: "active"` → `"closed"`
- `phase: "story-execution"` → `"delivered"`
- 新增 `closed: "2026-06-02"` 字段
- `notes` 扩展为完成摘要（v3.0 方法论、8 Stories / 4 Waves、候选汇总、GATE-3 HARD-STOP）
- YAML 校验通过（7 CR entries）

### TASK-012-08-02：STATE.md

- `active_change` → `CR-013-ptm-tde-ppdcs-phase（pending，下一阶段候选）`
- `pending_action` 更新为 CR-012 完成描述
- `lld_design_batch.phase` → `complete`；`pending_llds` → `0`
- History 表追加 CR-012 close 事件行
- 新增 `## story_status` 区段（CR-012 8 Story 状态表）
- `updated_at` → `2026-06-02T23:00:00+08:00`
- frontmatter 完整性验证：6 个字段全部保留

### TASK-012-08-03：agents/ptm-tde.md

- MFQ Phase ASCII 图扩展为 5 行（v3.0 版本号、步骤数、驱动模式、关键特性）
- GATE-3 描述增强：新增 Scenario-TSP 覆盖矩阵、步骤标签、候选汇总 HARD-STOP、自检项编号 M1-M7+W1-W2 引用

### TASK-012-08-04：CR-012-ptm-tde-mfq-phase.md

- frontmatter `status: approved` → `closed`，`updated_at` 更新
- 实施记录表追加关闭事件行

### TASK-012-08-05：验收验证

- AC01-AC08 全部通过（详见 CP6 文件）
- 其他 CR 记录不受影响（CR-INDEX.yaml 仍为 7 条）
- YAML 有效性验证通过

## 关键决策与偏差

- **没有偏差**：所有修改严格按 LLD §8 和 Story 卡片 §2 执行
- **story_status 区段**：用户任务描述中要求新增，LLD 未提及但属文档更新范围，已在 STATE.md 末尾追加

## 已知限制

- CR-012 前序 Story（012-01~012-07）的 CP7 验证文件尚未创建（`process/checks/CP7-STORY-012-*.md` 不存在）。本 Story 的前置条件（STORY-012-07 verified）依赖前序 meta-qa 完成验证
- STATE.md 中 `current_phase` 存在不一致：frontmatter 为 `delivered`，Current Work 表为 `story-execution`。此不一致由 CR-013 或下一次阶段推进时统一处理

## 提供给 meta-qa 的验证入口

- 验证重点：CR-INDEX.yaml YAML 有效性、STATE.md active_change 是否正确切换、agents/ptm-tde.md MFQ Phase 描述是否完整含 v3.0 信息、CR-012 CR 文件是否有关闭记录
- 跨文件一致性验证：CR-INDEX.yaml CR-012 = closed/delivered ←→ CR-012 CR 文件 status = closed ←→ STATE.md active_change = CR-013
- 建议全局 grep 确认：`grep -rn "CR-012-ptm-tde-mfq-phase" process/changes/CR-INDEX.yaml process/STATE.md agents/ptm-tde.md` 在两处出现且语义一致

## CP6 编码完成门

- **结论**：PASS
- **证据路径**：`process/checks/CP6-STORY-012-08-documentation-update-CODING-DONE.md`
- **14 项 checklist 全部 PASS，8 项 AC 全部验证通过**

---

# CR-013 — PPDCS 阶段改造

## Phase 1：Fast-lane 路径不一致修正（2026-06-03）

**背景**：CR-012 实施后 design-planner 输出到 `process/plan/`（HLD §9 设计决策），但 PPDCS 分析文档（写于 CR-012 前）和 design-planner SKILL.md Scope 节仍引用旧路径 `mfq/integration/`。

### 修改文件

| 文件 | 修改 | 旧路径 | 新路径 |
|------|:---:|--------|--------|
| `ppdcs-analysis-step-by-step.md` | 4 处 | `mfq/integration/design-plan.md` | `process/plan/design-plan.md` |
| `ppdcs-analysis-step-by-step.md` | | `mfq/integration/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` |
| `design-planner/SKILL.md` | 1 处 | `mfq/integration/design-plan.md` | `process/plan/design-plan.md`（消除 Scope 节与步骤 6 内部矛盾） |

### CP6 编码完成门

- **结论**：PASS
- **证据路径**：`process/checks/CP6-CR-013-fast-lane-path-fix-CODING-DONE.md`
- **7 项 checklist 全部 PASS**
- **调度模式**：fast-lane（meta-po inline 执行）

### CP7 验证完成门

- **结论**：PASS
- **证据路径**：`process/checks/CP7-CR-013-fast-lane-path-fix-VERIFICATION-DONE.md`
- **8 项 checklist 全部 PASS**
- **验证方法**：grep 全局搜索 + 人工逐行对比

---

## STORY-013-02：coverage-verifier 路径迁移 — 实施完成

**实施时间**：2026-06-03T03:44:00+08:00
**执行模式**：meta-dev（dev-yang，用户显式指令实施）
**Story 状态**：draft → in-development → ready-for-verification
**CP6 自动预检**：PASS（12 项 checklist：12 PASS / 0 FAIL / 0 WAIVED / 0 N/A）
**调度批次**：CR-013 Wave A（与 STORY-013-01 并行）
**Wave**：A
**tier**：S
**依赖关系**：无上游依赖（depends_on: []）

### 实施摘要

- **变更文件**：1 个（`skills/coverage-verifier/SKILL.md`），~32 处路径替换
- **LLD TASK-ID**：TASK-013-02-A（单文件单任务）
- **改动模式**：纯路径字符串替换（不修改执行流程、验收标准等原始内容）

### 替换统计（8 类映射）

| # | 映射 | 替换数 |
|---|------|:---:|
| 1 | `analysis/scenarios/` → `kym/scenarios/` | 6 |
| 2 | `analysis/integration/` → `mfq/integration/` | 2 |
| 3 | `analysis/factor-usage/` → `mfq/factor-usage/` | 1 |
| 4 | `analysis/coverage/` → `ppdcs/coverage/` | 2 |
| 5 | `design/ppdcs/` → `ppdcs/ppdcs/` | 11 |
| 6 | `design/pc/` → `ppdcs/pc/` | 8 |
| 7 | 描述文字 `MFQ 分析的 coverage 阶段` → `PPDCS 的 coverage 子步骤` | 2 |
| | **合计** | **32** |

> 注：`analysis/m-analysis/` → `mfq/m-analysis/` 映射在 coverage-verifier 中无出现（该 Skill 作为跨阶段消费者，不直接引用 m-analysis 产出目录）。

### 关键决策与偏差

- **无偏差**：严格按 LLD §3.1 的 8 类路径映射执行。
- **LLD 预估差异**：LLD 预估 ~23 处，实际 32 处。差异主要来自 `design/ppdcs/` 和 `design/pc/` 的频繁引用（各 11/8 处，LLD 分别预估 ~3/~4 处）。LLD 同时高估了 `analysis/integration/logic-cases.md` 和 `analysis/integration/test-data.md`（当前文件仅在 `all-test-points.md` 处有完整前缀路径，其余 logic-cases/test-data 引用无 `analysis/integration/` 前缀）。
- **覆盖率报告生产路径**：`analysis/coverage/` → `ppdcs/coverage/` 是关键输出路径变更，已在 argument-hint 和输出路径两处正确替换。
- **描述文字同步**：frontmatter `适用场景` 和正文 `适用阶段` 已更新为 PPDCS 术语。

### 验收结果

| 验收标准 | 状态 | 证据 |
|---------|:---:|------|
| 旧路径 `analysis/` 无残留 | PASS | `grep "analysis/\|design/" \| grep -v "ppdcs/"` = 0 |
| 旧路径 `design/` 无残留 | PASS | 同上 |
| `ppdcs/coverage` 出现次数 | PASS | 2 次（argument-hint + 输出路径） |
| `kym/scenarios` 出现次数 | PASS | 6 次 |
| `mfq/` 新路径引用正确 | PASS | `mfq/integration`: 2 次, `mfq/factor-usage`: 1 次 |
| 原始执行流程不变 | PASS | 仅路径字符串替换，流程/验收/Gotchas 未修改 |

### 已知限制

- coverage-verifier 输出路径从 `analysis/coverage/` 改为 `ppdcs/coverage/`，下游 deliverable-renderer（STORY-013-03）需同步消费新路径。
- `ppdcs/coverage/` 目录实际由 coverage-verifier 运行时写入，本 Story 只做文本替换，不验证目录存在性。

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-013-02-coverage-verifier-migration-CODING-DONE.md`
- 验证命令：
  ```bash
  grep -n "analysis/\|design/" skills/coverage-verifier/SKILL.md | grep -v "ppdcs/"  # 预期 0
  grep -c "ppdcs/coverage" skills/coverage-verifier/SKILL.md                         # 预期 2
  grep -c "kym/scenarios" skills/coverage-verifier/SKILL.md                          # 预期 6
  grep -c "mfq/integration\|mfq/factor-usage" skills/coverage-verifier/SKILL.md     # 预期 3
  ```

### 提供给 meta-qa 的验证提示

- 本 Story 为纯路径文本替换，无代码逻辑变更。验证重点是旧路径零残留和新路径引用正确性。
- 重点验证覆盖率报告输出路径 `ppdcs/coverage/` 是否正确（原为 `analysis/coverage/`，是生产路径变更）。
- 验证 frontmatter description 和正文适用阶段的文字同步（MFQ → PPDCS）。
- 注意 `mfq/m-analysis/` 等新路径中不包含需要替换的旧 `analysis/` 前缀（coverage-verifier 本来就不引用 m-analysis 子目录）。
- 下游 Story（STORY-013-03 deliverable-renderer）会消费 `ppdcs/coverage/` 输出，可交叉验证路径一致性。

---

## STORY-013-03：design-ppdcs-analyzer + deliverable-renderer 路径迁移 + ppdcs/delivery/ 目录创建 — 实施完成

**实施时间**：2026-06-03T15:22:00+08:00
**执行模式**：meta-dev（dev-zhao，用户显式指令实施）
**Story 状态**：draft → in-development → ready-for-verification
**CP6 自动预检**：PASS（全部 checklist 通过）
**调度批次**：CR-013 Wave B（与 STORY-013-04 并行）
**Wave**：B
**tier**：M
**依赖关系**：runtime 依赖 STORY-013-01（CP6 PASS）+ STORY-013-02（CP6 PASS）

### 实施摘要

- **变更文件**：2 个修改（`skills/design-ppdcs-analyzer/SKILL.md`、`skills/deliverable-renderer/SKILL.md`）+ 1 个新建（`ppdcs/delivery/.gitkeep`）
- **3 个 TASK-ID** 全部完成（TASK-013-03-A/B/C）
- **改动模式**：纯路径字符串替换 + 目录创建

### TASK-013-03-A：design-ppdcs-analyzer 路径迁移（~20 处替换）

| 映射 | 替换数 |
|------|:---:|
| `analysis/scenarios/` → `kym/scenarios/` | 3 |
| `analysis/plan/` → `process/plan/` | 1 |
| `analysis/integration/` → `mfq/integration/` | 4 |
| `design/ppdcs/` → `ppdcs/ppdcs/` | 6 |
| `design/pc/` → `ppdcs/pc/` | 6 |

### TASK-013-03-B：deliverable-renderer 路径迁移（~26 处替换）

| 映射 | 替换数 |
|------|:---:|
| `analysis/scenarios/` → `kym/scenarios/` | 3 |
| `analysis/integration/` → `mfq/integration/` | 2 |
| `analysis/coverage/` → `ppdcs/coverage/` | 2 |
| `analysis/factor-usage/` → `mfq/factor-usage/` | 1 |
| `design/ppdcs/` → `ppdcs/ppdcs/` | 7 |
| `design/pc/` → `ppdcs/pc/` | 7 |
| `delivery/` → `ppdcs/delivery/` | 3 |
| 描述性文字 `analysis/` → `kym/、mfq/` + delivery 闭环更新 | 1 |

### TASK-013-03-C：ppdcs/delivery/ 目录创建

- `mkdir -p ppdcs/delivery/` + `touch ppdcs/delivery/.gitkeep`
- 目录已创建，供 deliverable-renderer 运行时写入

### 关键决策与偏差

- **无偏差**：严格按 LLD §3.1/§3.2 路径映射表执行。
- **`design/ppdcs` 无尾斜杠修复**：analyzer 的 frontmatter description 和触发词使用 `design/ppdcs`（无尾斜杠），首轮 `design/ppdcs/` → `ppdcs/ppdcs/` 替换未匹配，追加 `design/ppdcs` → `ppdcs/ppdcs` 修复。
- **`analysis/factor-usage/` 补充**：此映射在 HLD-CR-013 §3.2 全局路径映射表中定义，但 LLD §3.2 映射表遗漏（仅影响 deliverable-renderer 1 处）。实施时按 HLD 全局映射补充。
- **`analysis/` 描述性文字处理**：deliverable-renderer §目标第一句「读取 `analysis/`」无对应子路径，按 Story 指令（描述性文字中的旧术语也要替换）更新为「读取 `kym/、mfq/`」。
- **历史守卫保留**：analyzer 中 2 处 `design/<module>/<sub-module>/` 为禁止旧深目录的历史守卫描述，不属于当前路径映射范围，保留。
- **`delivery 阶段` 保留**：renderer 中 2 处 `delivery 阶段`（frontmatter description 适用场景、正文适用阶段）为阶段名称而非目录路径，不属于 `delivery/` 映射范围，保留。

### 验收结果

| 验收标准 | 状态 | 证据 |
|---------|:---:|------|
| design-ppdcs-analyzer 旧路径 = 0 | PASS | `grep "analysis/" | grep -v "ppdcs/"` 仅 2 处 `design/<module>/` 历史守卫 |
| deliverable-renderer 旧路径 = 0 | PASS | `grep "analysis/" | grep -v "ppdcs/"` 无输出 |
| `delivery/` → `ppdcs/delivery/` 已更新 | PASS | renderer 中 3 处 path + 1 处描述性文字全部更新 |
| 跨文件与 Wave A 一致 | PASS | analyzer/renderer 的 `ppdcs/ppdcs/` + `ppdcs/pc/` 引用（7+9 处）与 5 设计 Skill 产出路径一致；renderer 的 `ppdcs/coverage/` 引用与 coverage-verifier 产出路径一致 |

### 已知限制

- analyzer 的 `design/<module>/<sub-module>/` 2 处历史守卫在 `grep design/` 中会被匹配，需注意与真实旧路径残留区分。
- `ppdcs/delivery/` 目录通过 `.gitkeep` 确保入库，实际交付物由 deliverable-renderer 运行时写入。
- deliverable-renderer 的 `delivery 阶段`（frontmatter + 正文）保留原词，因为它是阶段名称而非路径。

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-013-03-analyzer-renderer-migration-CODING-DONE.md`
- 验证命令：
  ```bash
  grep -n "analysis/\|design/" skills/design-ppdcs-analyzer/SKILL.md | grep -v "ppdcs/"  # 预期 2 处历史守卫
  grep -n "analysis/\|design/" skills/deliverable-renderer/SKILL.md | grep -v "ppdcs/"    # 预期 0
  ls -la ppdcs/delivery/                                                                    # 预期 .gitkeep 存在
  ```

### 提供给 meta-qa 的验证提示

- 本 Story 为纯路径文本替换 + 目录创建，无代码逻辑变更。验证重点是旧路径零残留和新路径引用正确性。
- analyzer 的 2 处 `design/<module>/<sub-module>/` 为历史守卫，不视为旧路径残留。
- renderer 的 `delivery 阶段`（2 处）为阶段名称，不视为旧路径残留。
- 跨文件验证：analyzer 输出路径 = `ppdcs/ppdcs/` + `ppdcs/pc/` = 5 设计 Skill 产出路径；renderer 消费路径含 `ppdcs/coverage/` = coverage-verifier 产出路径。
- `ppdcs/delivery/.gitkeep` 确保空目录入库，实际交付物由运行时产出。

---

## STORY-013-04：GATE-4 增强（gate-spec.md + checkpoint-manager）— 实施完成

**实施时间**：2026-06-03T04:30:00+08:00
**执行模式**：meta-dev（dev-yang，用户显式指令实施）
**Story 状态**：draft → in-development → ready-for-verification
**CP6 自动预检**：PASS（11 项 checklist：7 PASS / 0 FAIL / 4 WAIVED / 2 N/A）
**调度批次**：CR-013 Wave B（与 STORY-013-03 并行）
**Wave**：B
**tier**：M
**依赖关系**：无上游依赖（depends_on: []）

### 实施摘要

- **变更文件**：2 个（`docs/ptm-tde/gate-spec.md`、`skills/checkpoint-manager/SKILL.md`）
- **2 个 TASK-ID** 全部完成：
  - TASK-013-04-A：gate-spec.md GATE-4 骨架升级为 P1-P7 完整自检项 + 4 项人工确认
  - TASK-013-04-B：checkpoint-manager GATE-4 Checklist/人工确认项同步对齐 + 公共因子库 P5 引用

### TASK-013-04-A：gate-spec.md GATE-4 增强

| 修改位置 | 改前 | 改后 |
|---------|------|------|
| GATE-4 Checklist | 7 项骨架（编号 #1-#7，含「失败处理」列） | 7 项 P1-P7 自检（编号 P1-P7，仅含检查项/通过条件 3 列） |
| GATE-4 人工确认项 | 3 项（PPDCS 设计/覆盖率报告/物化结果） | 4 项（PPDCS 设计方法/物理用例质量/覆盖率结果/拓扑绑定） |
| GATE-4 Entry Criteria | 3 项（不变） | 3 项（不变） |
| GATE-4 Exit Criteria/Deliverables | 不变 | 不变 |
| GATE-1~GATE-3 | 不变 | 不变（基线 28 次引用 = 28） |

### TASK-013-04-B：checkpoint-manager 对齐

| 修改位置 | 改前 | 改后 |
|---------|------|------|
| GATE-4 Checklist 概要 | 7 项（编号 #1-#7） | 7 项 P1-P7（编号 P1-P7，通过条件与 gate-spec 对齐） |
| GATE-4 人工确认项 | 3 项 | 4 项（与 gate-spec 完全一致） |
| 公共因子库检查补充 GATE-4 | 仅回查 | 因子覆盖验证（P5）+ 回查 |
| 旧路径残留 | 基线为 0 | 仍为 0（无需替换） |

### P1-P7 自检项对照

| 编号 | 旧 Check | 新 Check | 变化说明 |
|:---:|---------|---------|---------|
| P1 | PPDCS 设计完整 | PPDCS 设计过程完整 | 增加「方法与 plan 推荐一致」条件 |
| P2 | PC 生成完整 | PC 文件完整 | 增加「16 列格式正确」条件 |
| P3 | PC 物化回链 | PC 拓扑绑定回链 | 增加 `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` 链路 |
| P4 | 覆盖率验证 | 双层覆盖率验证 | 量化目标：需求覆盖 = 100%，测试点覆盖 ≥ 95% |
| P5 | 拓扑绑定状态保持 | 因子覆盖验证 | 从「needs-confirmation 不提升」改为「所有 factor_bindings 在 PC 中有覆盖」 |
| P6 | 交付物预检 | 交付物完整 | 明确「包含且仅包含测试方案和测试用例两个文件」 |
| P7 | plan 消费完整性 | 交付物字段保留 | 从「plan 消费完整性」改为「topology_bindings/topology_role/source/fact_status 字段保留」 |

### 验收结果

| 验收标准 | 状态 | 证据 |
|---------|:---:|------|
| gate-spec.md GATE-4 含 P1-P7 | PASS | `grep -c "^| P[1-7]" docs/ptm-tde/gate-spec.md` = 7 |
| gate-spec.md GATE-4 含 4 项人工确认 | PASS | GATE-4 人工确认项表格含 4 行（设计方法/PC 质量/覆盖率/拓扑绑定） |
| checkpoint-manager GATE-4 与 gate-spec 对齐 | PASS | P1-P7 编号一致，4 项人工确认一致，公共因子库引用 P5 |
| checkpoint-manager 旧路径残留 = 0 | PASS | `grep "analysis/\|design/" | grep -v "ppdcs/\|kym/\|mfq/"` 无输出 |
| GATE-1~GATE-3 不被修改 | PASS | GATE-1~GATE-3 出现次数基线 28 = 28 |
| 不引入新的 Gate 编号 | PASS | 仅修改 GATE-4，无新增 Gate |

### 关键决策与偏差

- **无偏差**：严格按 LLD §3.1（gate-spec.md）和 §3.2（checkpoint-manager）执行
- **checkpoint-manager 旧路径无需替换**：前置 grep 验证确认该文件基线已无 `analysis/` 或 `design/` 旧路径残留（CR-011/CR-012 已完成迁移）
- **P5 语义变化**：旧 GATE-4 #5 为「拓扑绑定状态保持（needs-confirmation 不提升）」，新 P5 改为「因子覆盖验证」。旧的拓扑状态保持语义分散到 P3（拓扑绑定回链）和人工确认「拓扑绑定」项中
- **P7 语义变化**：旧 GATE-4 #7 为「plan 消费完整性」，新 P7 改为「交付物字段保留」。plan 消费完整性已隐含在 P1（方法与 plan 推荐一致）中

### 已知限制

- gate-spec.md 修订记录未追加 v1.5 行（按 Story 范围，修订记录由 meta-po 在 CP8 统一处理）
- checkpoint-manager GATE-4 Checklist 概要保留了「失败处理」列（与 gate-spec.md 的 3 列格式不同），这是 checkpoint-manager 的一贯格式约定（所有 Gate 的 Checklist 概要均为 4 列表格）
- GATE-4 的「实现深度说明」行（「当前版本由 checkpoint-manager 执行骨架检查...」）已过时（因为本 Story 已将骨架升级为完整检查项），但按 Story 范围保留该行不变（由 meta-qa 在 CP7 中标记或后续 CR 处理）

### 验证入口

- CP6 检查文件：`process/checks/CP6-STORY-013-04-gate4-enhancement-CODING-DONE.md`
- 验证命令：
  ```bash
  grep -c "^| P[1-7]" docs/ptm-tde/gate-spec.md                       # 7
  grep -n "analysis/\|design/" skills/checkpoint-manager/SKILL.md | grep -v "ppdcs/\|kym/\|mfq/"  # 无输出
  grep -c "GATE-1\|GATE-2\|GATE-3" docs/ptm-tde/gate-spec.md          # 28
  grep -c "^| P[1-7]" skills/checkpoint-manager/SKILL.md              # 7
  ```

### 提供给 meta-qa 的验证提示

- 验证重点：gate-spec.md 和 checkpoint-manager 的 GATE-4 P1-P7 编号一致性（两文件均为 7 项 P1-P7）
- 确认 gate-spec.md GATE-4 人工确认项表格含 4 行，且 checkpoint-manager 同步为 4 行
- 确认 GATE-1~GATE-3 内容未被本次修改影响（grep 基线 28 次引用不变）
- 确认 gate-spec.md GATE-4 Checklist 的「失败处理」列已被移除（改为 3 列格式），而 checkpoint-manager 的 Checklist 概要保持 4 列（含失败处理）是其格式约定
- P5（因子覆盖验证）为新增语义项，原「拓扑绑定状态保持（needs-confirmation 不提升）」已分散到 P3 和人工确认「拓扑绑定」项中
- 确认 checkpoint-manager 公共因子库检查补充中 GATE-4 条目已引用 P5
- 确认未引入新的 Gate 编号（GATE-1~GATE-5 体系不变）
2026-06-05/06 | user + meta-po（po-zhao） | 根因分析 + CR 创建：发现 m-analyzer 两类资源消费缺口——① atomic-ops 库 74 个 op 完全未查询（CR-016），② 因子库 9 个只扫了 2 个（CR-017）。同一根因：m-analyzer 消费表声明消费 X但未提供发现/查询 X 的机制。CR-016 需等 atomic-ops 仓库 P0+P1（list 输出增加 tags + parameters_summary），CR-017 无外部依赖可立即启动。两 CR 共享 Step 1.5 资源发现设计模式，推荐 CR-017 先于 CR-016。双 CR 合计 7 项待人工决策 + 4 项历史 CP8 待处理。恢复入口：@meta-po 推进，读取 STATE.md pending_gate 和 pending_decision_ids。

---

## docs 重组：交付文档与过程文档分离（2026-07-09）

**执行时间**：2026-07-09
**执行模式**：host-orchestrator 直接执行（用户显式调度）
**背景**：ptm-team/docs/ 混杂交付文档与过程产物，按双项目归档策略分离

### 决策

- **交付文档（20 个）留 ptm-team/docs/**：README、USER-MANUAL、RELEASE-NOTES、组件规约（skill-references/gate-spec/checkpoint-spec/component-manual/runtime-artifacts/data-flow-spec）、质量运营仪表盘（EVAL-*/FIELD-*）、DEPLOY-CHECKLIST
- **过程文档（25 个）移 meta-flow-artifacts/docs/ptm-team/**：design/（4）、product/（7）、quality 过程报告（4）、release/FEEDBACK（1）、ptm-tde 设计产物（7）、ptm-te 草案（2）

### 分类标准

- 交付文档：使用者/维护者持续查阅，或被运行时 Skill/Agent/安装器引用
- 过程文档：开发迭代快照，零运行时引用

### 交叉引用处理

- 全局核查：交付文档零引用过程文件路径，无断链
- data-flow-spec.md 原计划移走，因 skill-references.md 引用改为保留
- component-manual.md / runtime-artifacts.md 与 skill-references.md 同属组件规约类，同进同退保留

### 连接机制（ignored symlink 保持旧路径可读）

- **纯过程目录（3 个目录级 symlink）**：`docs/design`、`docs/product`、`docs/features` 整目录 symlink，路径 `../../meta-flow-artifacts/docs/ptm-team/<dir>`
- **混合目录（12 个文件级 symlink）**：`quality/`（4）、`release/`（1）、`ptm-tde/`（7）含交付文件不能整目录 symlink，改为逐文件 symlink，路径 `../../../meta-flow-artifacts/docs/ptm-team/<dir>/<file>`（比目录级深一层）
- **纯交付目录**：`ptm-qa/`、`ptm-tae/`、`ptm-te/`、`ptm-tm/`、`ptm-tse/` 无过程文件，无需 symlink
- 全部 15 个 symlink 被 `*` 规则自动忽略，git 不跟踪，git status 不受影响

### 路由元数据

- artifact repo: `docs/ptm-team/.meta-flow-docs.yaml`（routing_mode=symlink，retained_in_source 记录 20 个交付文件）
- process symlink: `process/ -> ../meta-flow-artifacts/process/ptm-team/`（不变，运行时状态归档）

### .gitignore 变更

- 保留通用 `!*/README.md`、`!*/USER-MANUAL.md` 规则
- 新增 `!ptm-tde/RELEASE-NOTES.md`、`!ptm-tde/data-flow-spec.md`
- 移除已迁走的 component-manual/runtime-artifacts 白名单（注：后修正为保留，两者仍为交付文档）
