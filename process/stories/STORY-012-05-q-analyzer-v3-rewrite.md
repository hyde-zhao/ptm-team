---
story_id: STORY-012-05
story_name: Q 分析器 v3.0 重写（逐 TSP 驱动质量分析）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: M
wave: C
depends_on: [STORY-012-01, STORY-012-03]
blocks: [STORY-012-06]
status: ready-for-verification
file_ownership:
  - skills/q-analyzer/SKILL.md
parallel_safe: true
parallel_group: fq-analyzers
---

# STORY-012-05：Q 分析器 v3.0 重写（逐 TSP 驱动质量分析）

## 1. 目标

以设计文档 `mfq-analysis-step-by-step.md` v3.0 §5 为蓝本，对 `skills/q-analyzer/SKILL.md` 进行全量重写：从 5 步 v2 模式升级为 6 步 v3.0「逐 TSP 驱动」模式。核心变化：消费 M 分析产出的 TSP 列表和覆盖矩阵中的 `[Q→]` 标签作为相关性评估补充依据，逐 TSP 逐 HTSM 维度评估、发现质量对象/因子、生成质量测试点。

## 2. 范围

- **修改文件**：`skills/q-analyzer/SKILL.md`（全量重写，257 行 → ~370 行）
- **改动量**：~120 行净增
- **不改动**：YAML frontmatter 的 `name`；HTSM 维度定义表

### 重写结构（6 步，来自设计文档 §5）

| 步骤 | 名称 | 来源 | 核心变化 |
|:---:|------|------|----------|
| 1 | 加载 TSP 列表、覆盖矩阵与相关性评估 | §5 步骤 1 | **新增**：逐 TSP 逐 HTSM 维度评估相关性；[Q→] 标签维度至少弱相关起评；消费 TSP 的 `q_tags` 字段 |
| 2 | 逐 TSP 质量对象与因子发现 | §5 步骤 2 | **全新驱动模式**：对每个 TSP 逐维度展开，含 A 识别质量对象、B 发现/匹配质量因子；无对应因子时基于知识生成候选 |
| 3 | 逐 TSP 质量测试点生成 | §5 步骤 3 | 测试点按 TSP 组织、按质量维度分组；质量因子全候选降级 fact_status |
| 4 | 工具观测能力评估 | §5 步骤 4 | 保留旧版工具评估逻辑 |
| 5 | 写入 Q 分析产物 | §5 步骤 5 | 输出清单扩展（+质量因子候选列表，标注 tsp_ref） |
| — | 更新 description | — | frontmatter description 更新为 v3.0 描述 |

## 3. 验收标准

- [ ] **AC01**：`skills/q-analyzer/SKILL.md` grep `TSP` 返回 >= 3（证明 TSP 驱动模式已落地）
- [ ] **AC02**：包含 `[Q→]` 标签消费逻辑（grep `\[Q→\]` 或 `Q 线索` 或 `Q标签` 返回 > 0）
- [ ] **AC03**：包含 `scenario-tsp-coverage.md` 或 `覆盖矩阵` 引用
- [ ] **AC04**：输出路径全部使用 `mfq/q-analysis/`（grep `mfq/q-analysis/` 返回 > 0）
- [ ] **AC05**：包含质量对象发现（`质量对象` 或 `quality_object`）
- [ ] **AC06**：包含质量因子候选概念（`候选` 或 `candidate`，且在 Q 分析上下文中）
- [ ] **AC07**：包含 `generation_basis` 或「生成依据」概念（质量因子基于知识/经验/需求推断生成）
- [ ] **AC08**：HTSM 维度定义表保留（CRUSSPICSTML 或至少含可靠性/性能/安全性等维度）
- [ ] **AC09**：包含逐维度相关性评估（强相关/弱相关/不相关 或 strong/weak/not-applicable）
- [ ] **AC10**：YAML frontmatter `name: q-analyzer` 不变

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `skills/q-analyzer/SKILL.md` | 重写 | v2 5 步 → v3.0 6 步。步骤 1 新增 TSP 列表+Q 线索加载+逐 TSP 相关性评估；步骤 2 改为逐 TSP 质量对象与因子发现；步骤 3 TP 按 TSP 组织+按质量维度分组；新增质量因子候选列表产出 |

## 5. 依赖关系

- **上游**：STORY-012-01（路径迁移）+ STORY-012-03（M 分析器需产出 TSP 列表 + 覆盖矩阵中的 Q 线索）
- **下游**：STORY-012-06（test-point-integrator 消费新 Q 产出格式）
- **并行**：可与 STORY-012-04（F 分析器）并行（无文件冲突，依赖相同的上游但消费不同的标签类型）

## 6. 实施注意事项

### [Q→] 标签消费链路（步骤 1）
1. 步骤 1 从 `mfq/m-analysis/scenario-tsp-coverage.md` 的「Q 分析线索汇总」表提取所有 `[Q→]` 标签行
2. 建立 `TSP → [Q→标签列表]` 索引
3. 步骤 1 逐 TSP 逐 HTSM 维度评估相关性时：如果某维度已由 [Q→] 标签标记，该维度至少弱相关起评，可提升（如场景明确涉及质量行为→升为强相关）

### 质量因子候选生成依据（步骤 2 子步骤 B）
- 当质量对象无已有因子时，根据 TSP 的 scope/purpose + 质量维度知识生成候选
- 候选因子必须标注 `generation_basis`（行业标准/经验推断/需求推断）和 `tsp_ref`
- 示例：TSP-M2 + 可靠性 → 候选因子「数据一致性校验结果（一致/不一致/部分一致）」

### 可复用旧版内容
- HTSM 质量属性维度定义表（CRUSSPICSTML）
- 各维度的防火墙典型关注点
- 拓扑/因子分层 Guardrail
- Q 分析 CAE 特有约束（C 条件含质量约束基线）

### STOP 协议落地
- 保留已有「拓扑/因子分层 Guardrail」章节
- 路径写入前校验目标父目录存在
- 相关性评估中不确定项标记为 OPEN，不自行判定
