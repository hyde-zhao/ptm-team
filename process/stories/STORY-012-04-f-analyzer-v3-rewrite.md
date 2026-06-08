---
story_id: STORY-012-04
story_name: F 分析器 v3.0 重写（逐 TSP 驱动耦合分析）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: M
wave: C
depends_on: [STORY-012-01, STORY-012-03]
blocks: [STORY-012-06]
status: ready-for-verification
file_ownership:
  - skills/f-analyzer/SKILL.md
parallel_safe: true
parallel_group: fq-analyzers
---

# STORY-012-04：F 分析器 v3.0 重写（逐 TSP 驱动耦合分析）

## 1. 目标

以设计文档 `mfq-analysis-step-by-step.md` v3.0 §4 为蓝本，对 `skills/f-analyzer/SKILL.md` 进行全量重写：从 8 步 v2 模式升级为 9 步 v3.0「逐 TSP 驱动」模式。核心变化：消费 M 分析产出的 TSP 列表和覆盖矩阵中的 `[F→]` 标签作为种子线索，逐 TSP 识别耦合关系、发现耦合对象/因子、三源合并、生成耦合测试点。

## 2. 范围

- **修改文件**：`skills/f-analyzer/SKILL.md`（全量重写，314 行 → ~450 行）
- **改动量**：~150 行净增
- **不改动**：YAML frontmatter 的 `name`；Excel 耦合工具调用方式

### 重写结构（9 步，来自设计文档 §4）

| 步骤 | 名称 | 来源 | 核心变化 |
|:---:|------|------|----------|
| 1 | 加载 TSP 列表、覆盖矩阵与矩阵基线 | §4 步骤 1 | **新增**：加载 M 分析 TSP 列表（含 `f_tags`）+ 覆盖矩阵中 F 线索列表；优先展开 [F→] 标签标记的耦合点 |
| 2 | 逐 TSP 场景耦合推理 | §4 步骤 2 | **全新驱动模式**：逐 TSP 分析交互，含 A 识别耦合关系（种子线索优先 + 自主发现）、B 发现耦合对象、C 发现/匹配耦合因子；标注 `discovery_source`（f-tag-seed / scenario-inference） |
| 3 | 代码依赖收集 | §4 步骤 3 | 保留旧版可选代码依赖收集 |
| 4 | 三源合并 | §4 步骤 4 | 保留旧版三源合并逻辑，耦合强度取最高值 |
| 5 | 候选耦合点确认 | §4 步骤 5 | 保留旧版用户确认流程 |
| 6 | 耦合测试点生成 | §4 步骤 6 | 测试点按 TSP 组织；耦合因子候选使用域引用；全候选降低 fact_status |
| 7 | 工具覆盖评估 | §4 步骤 7 | 保留旧版工具评估逻辑 |
| 8 | 可选回写 | §4 步骤 8 | 保留旧版 Excel 回写询问 |
| — | 更新 description | — | frontmatter description 更新为 v3.0 描述 |

## 3. 验收标准

- [ ] **AC01**：`skills/f-analyzer/SKILL.md` grep `TSP` 返回 >= 5（证明 TSP 驱动模式已落地）
- [ ] **AC02**：包含 `[F→]` 标签消费逻辑（grep `\[F→\]` 或 `F 线索` 或 `F标签` 返回 > 0）
- [ ] **AC03**：包含 `scenario-tsp-coverage.md` 或 `覆盖矩阵` 引用
- [ ] **AC04**：输出路径全部使用 `mfq/f-analysis/`（grep `mfq/f-analysis/` 返回 > 0）
- [ ] **AC05**：包含耦合对象发现（`耦合对象` 或 `coupled_object` 或 `coupling.*object`）
- [ ] **AC06**：包含耦合因子候选概念（`候选` 或 `candidate`，且在 F 分析上下文中）
- [ ] **AC07**：包含 `discovery_source` 或 `f-tag-seed` / `scenario-inference` 区分概念
- [ ] **AC08**：CAE 耦合测试点约束保留（A 动作不得直接操作耦合目标）
- [ ] **AC09**：三源合并逻辑保留
- [ ] **AC10**：YAML frontmatter `name: f-analyzer` 不变

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `skills/f-analyzer/SKILL.md` | 重写 | v2 8 步 → v3.0 9 步。步骤 1 新增 TSP 列表+F 线索加载；步骤 2 改为逐 TSP 耦合推理（含耦合对象/耦合因子发现）；步骤 6 TP 按 TSP 组织；新增耦合因子候选列表产出 |

## 5. 依赖关系

- **上游**：STORY-012-01（路径迁移）+ STORY-012-03（M 分析器需产出 TSP 列表 + 覆盖矩阵中的 F 线索）
- **下游**：STORY-012-06（test-point-integrator 消费新 F 产出格式）
- **并行**：可与 STORY-012-05（Q 分析器）并行（无文件冲突，依赖相同的上游但消费不同的标签类型）

## 6. 实施注意事项

### [F→] 标签消费链路（步骤 1→2）
1. 步骤 1 从 `mfq/m-analysis/scenario-tsp-coverage.md` 的「F 分析线索汇总」表提取所有 `[F→]` 标签行
2. 建立 `TSP → [F→标签列表]` 索引，作为步骤 2 的种子线索
3. 步骤 2 逐 TSP 分析时：优先展开种子线索中的耦合点（`discovery_source=f-tag-seed`），再自主发现未标记的耦合关系（`discovery_source=scenario-inference`）

### 耦合对象与因子发现（步骤 2 子步骤 B-C）
- 耦合对象：优先从 M 分析测试对象表中查找已有对象（`source=M-analysis`），无则新建（`source=new-coupling-discovery`）
- 耦合因子：优先从 M 分析因子表中匹配；新发现的标注 `source=new-coupling-candidate`，标注 `tsp_ref` 和 `coupling_ref`

### 可复用旧版内容
- 「三源数据模型」（Excel 矩阵基线 + 场景耦合 + 代码依赖）
- 耦合类型定义（顺序/数据/容错/接口资源）
- Excel 工具调用方式：`python scripts/excel_coupling_tool.py`
- 拓扑/因子分层 Guardrail
- CAE 耦合特有约束（A 动作不得直接操作耦合目标）

### STOP 协议落地
- 保留已有「拓扑/因子分层 Guardrail」章节
- 新增候选确认步骤中的 STOP-02 规则（禁止判定候选全部确认）
- 路径写入前校验目标父目录存在
