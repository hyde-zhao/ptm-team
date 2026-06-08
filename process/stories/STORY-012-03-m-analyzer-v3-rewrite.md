---
story_id: STORY-012-03
story_name: M 分析器 v3.0 重写（场景步骤驱动）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: M
wave: B
depends_on: [STORY-012-01]
blocks: [STORY-012-04, STORY-012-05, STORY-012-06]
status: ready-for-verification
file_ownership:
  - skills/m-analyzer/SKILL.md
parallel_safe: false
---

# STORY-012-03：M 分析器 v3.0 重写（场景步骤驱动）

## 1. 目标

以设计文档 `mfq-analysis-step-by-step.md` v3.0 §3 为蓝本，对 `skills/m-analyzer/SKILL.md` 进行全量重写：从 7 步 v2 模式升级为 10 步 v3.0「场景步骤驱动发现」模式，新增 Scenario-TSP 覆盖矩阵和场景步骤标签两个数据实体。

## 2. 范围

- **修改文件**：`skills/m-analyzer/SKILL.md`（全量重写，357 行 → ~500 行）
- **改动量**：~200 行净增（删旧版 7 步流程，写新版 10 步流程 + 覆盖矩阵/标签/候选产出）
- **不改动**：YAML frontmatter 的 `name`、`user-invokable` 字段保留；Skill 名称保持 `m-analyzer`

### 重写结构（10 步，来自设计文档 §3）

| 步骤 | 名称 | 来源 | 核心变化 |
|:---:|------|------|----------|
| 1 | 加载输入 | §3 步骤 1 | 扩展消费字段：mission-statement 的 `test_items/dont_test/risks`、scenario 的 `minimal_logic_chain/observation_targets` |
| 2 | 场景步骤驱动发现 | §3 步骤 2 | **全新**：逐场景步骤扫描，含 A 识别测试对象（高/中/低关联度）、B 发现/匹配因子（已有 vs 候选）、C 检查原子操作支撑、D 打标签 + 建覆盖映射 |
| 3 | TSP 描述生成 | §3 步骤 3 | TSP 增加 `covered_scenario_segments` + `f_tags` + `q_tags` 字段 |
| 4 | PPDCS 特征标注 | §3 步骤 4 | 保留旧版 PPDCS 逻辑，增加 TSP.purpose 引导特征判断 |
| 5 | 测试点生成 | §3 步骤 5 | 按对象关联度分级生成（高→全部、中→选择性、低→不生成）；候选因子使用域引用 `@domain.xxx` |
| 6 | 覆盖初检 | §3 步骤 6 | **新增**：需求覆盖 + 场景步骤覆盖 + 对象覆盖 + atomic-ops 覆盖四维检查 |
| 7 | 写入 M 分析产物 | §3 步骤 7 | 输出清单扩展（+覆盖矩阵、+候选列表） |
| — | 更新 description | — | frontmatter description 改为 v3.0 描述 |

## 3. 验收标准

基于设计文档 §M 分析验收标准（13 项）：

- [ ] **AC01**：`skills/m-analyzer/SKILL.md` 包含 10 个步骤标题（grep `^### 步骤 [0-9]` 返回 7~10，取决于步骤标题格式；最少 grep `步骤 [0-9]` 返回 >= 7）
- [ ] **AC02**：输出路径全部使用 `mfq/m-analysis/`（grep `mfq/m-analysis/` 返回 > 0）
- [ ] **AC03**：包含「覆盖矩阵」或 `scenario-tsp-coverage.md` 引用
- [ ] **AC04**：包含因子候选（`candidate` 或 `候选`）和原子操作候选概念
- [ ] **AC05**：包含场景步骤标签 `[M]` / `[F→]` / `[Q→]` 定义
- [ ] **AC06**：包含测试对象关联度评估（高/中/低 或 strong/medium/low）规则
- [ ] **AC07**：包含「关联度」或「关联对象」概念的文字描述
- [ ] **AC08**：CAE 三元组字段约束（C/A/E）保持与旧版一致（至少包含 C 条件/A 动作/E 预期三字段说明）
- [ ] **AC09**：E="待定" 必须有批注的规则保留
- [ ] **AC10**：PPDCS 五特征定义表保留（可在步骤 4 或理论基础中）
- [ ] **AC11**：YAML frontmatter 的 `name: m-analyzer` 不变，`description` 更新（包含 "v3.0" 或 "场景步骤驱动"）
- [ ] **AC12**：SKILL.md 行数 ≥ 400（旧版 357，新流程 + 覆盖矩阵 + 候选 + 标签预期 ~500）
- [ ] **AC13**：引用 `[F→]` / `[Q→]` 标签概念说明其由 M 分析生产、F/Q 分析消费

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `skills/m-analyzer/SKILL.md` | 重写 | v2 7 步 → v3.0 10 步。保留 frontmatter name；理论基础 + PPDCS 五特征可复用；新增步骤 2（场景步骤驱动发现）、步骤 6（覆盖初检）、步骤 7（新产物清单）；TSP 扩展 covered_segments + tags；测试点按关联度分级生成 |

## 5. 依赖关系

- **上游**：STORY-012-01（路径迁移，确保文件中引用 `mfq/` 而非 `analysis/`）
- **下游**：STORY-012-04（F 分析器消费覆盖矩阵+F 标签）、STORY-012-05（Q 分析器消费覆盖矩阵+Q 标签）、STORY-012-06（test-point-integrator 消费新 M 产出格式）

## 6. 实施注意事项

### 重写策略（方案 A：全量重写）
- 以设计文档 §3 的 10 步流程为骨架，逐步骤翻译为 SKILL.md 的 markdown 章节
- **可复用部分**：理论基础（§1 MFQ 理论基础，调为 M 分析视角）、PPDCS 五特征表（旧版已有，保留并补充 TSP.purpose 引导规则）、CAE 三元组约束（旧版已有，保留）、拓扑/因子分层 Guardrail（旧版 §拓扑/因子分层 Guardrail）
- **必须重写部分**：步骤 1-7 全部按设计文档 §3 重写；旧版按四级→五级目录遍历的逻辑替换为逐场景步骤扫描

### 关键新增实体
- **覆盖矩阵格式**（设计文档 §2.3）：视角 A（场景→TSP 逐步骤覆盖）+ 视角 B（目录→场景反向索引）+ 覆盖率统计。产出路径 `mfq/m-analysis/scenario-tsp-coverage.md`
- **场景步骤标签**（设计文档 §2.3 实体 G）：三类标签 `[M]` / `[F→目标]` / `[Q→维度]`，附着在覆盖矩阵每行上，步骤 2 子步骤 D 生成，末尾汇总 F/Q 线索表
- **候选列表**：因子候选 `mfq/m-analysis/candidate-factor-proposals.yaml`（YAML 格式）+ 原子操作候选 `mfq/m-analysis/candidate-atomic-ops.yaml`

### 关联度判定（步骤 2 子步骤 A）
- 高关联：该对象是特性的核心操作目标 → 标记为"已确认对象"，必须生成测试点
- 中关联：辅助/中间角色 → 已确认对象，选择性生成测试点
- 低关联：环境/基础设施 → 记录但不生成测试点，供 F 分析参考

### STOP 协议落地
- 保持旧版已有的「拓扑/因子分层 Guardrail」章节
- 新增或保留「前置条件」校验 KYM 阶段输出完整性（步骤 1 中）
- 新增路径写入前校验（步骤 7）
- 禁止 Agent 自行判定"覆盖完成"——步骤 6 覆盖初检结果需明确标记 ⚠️ 缺口，待人工审查

### 旧版隐性知识保护
- 重写完成后对照旧版逐章检查，确保 PPCDS 特征区分规则（Process vs State、Parameter vs Data、Data vs Combination）完整保留
- 拓扑角色 vs 真实组网对象的分层规则完整保留
- MFQ 分层概念（测试因子 / 拓扑角色 / 真实组网对象）完整保留
