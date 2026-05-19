---
name: design-planner
description: >-
  基于 PPDCS 五特征匹配为每个逻辑用例推荐测试设计方法，生成设计计划表并与用户确认。
  触发词包括：设计计划、PPDCS匹配、方法推荐、测试设计计划。
  适用场景：MFQ 分析的第七步（plan 阶段）。
argument-hint: "无需参数，自动读取 integration 目录"
user-invokable: true
status: active
---

## 目标

读取整合后的逻辑用例（LC）、测试数据（TD）和 PPDCS 特征标注，
基于 **LC + TD trace** 完成 CAE→PPDCS 完整推断，
为每个逻辑用例输出**主信号、候选特征、排除理由、推荐方法、trace 回链、待确认缺口**，
生成设计计划表与 reasoning 明细并与用户确认。

## 理论基础

基于《海盗派测试分析: MFQ&PPDCS》的 PPDCS 框架：
- M 分析阶段已为每个子模块标注了 PPDCS 主特征
- 设计方法选择直接由 PPDCS 特征驱动：

| PPDCS 特征 | 对应设计方法 | 对应设计 Skill | 核心建模工具 |
|-----------|-------------|---------------|-------------|
| **P-Process** | 流程图法 | `process-design` | 流程图/活动图 |
| **P-Parameter** | 判定表法 | `parameter-design` | 判定表/因果图/决策树 |
| **D-Data** | 等价类+边界值法 | `data-design` | 等价类划分表 |
| **C-Combination** | 组合法 | `combination-design` | Pairwise/正交阵列 |
| **S-State** | 状态图法 | `state-design` | 状态图/转换表 |

## 适用范围

- 适用阶段：MFQ 分析的 plan 阶段
- 输入：`analysis/integration/logic-cases.md` + `analysis/integration/test-data.md` + `analysis/m-analysis/ppdcs-annotation.md`
- 输出：`analysis/integration/design-plan.md` + `analysis/plan/design-planner-reasoning.md`

## 前置条件

- [ ] 测试点整合完成（`analysis/integration/logic-cases.md` 存在）
- [ ] 测试数据已分配（`analysis/integration/test-data.md` 存在）
- [ ] PPDCS 特征标注已完成（`analysis/m-analysis/ppdcs-annotation.md` 存在）
- [ ] LC / TD 中已保留 Story-04 trace 字段

## 输入契约（Story-04）

design-planner **不得只看 legacy TP 汇总表**，必须同时消费 LC 与 TD 的 trace/gap 字段：

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `logic-cases.md` | `LC-ID`, `source_tp_ids`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `knowledge_refs`, `confirmation_gap_refs`, `test_object_refs`, `factor_refs`, `trace_refs`, `fact_status`, `动作路径`, `因子-取值表`, `CAE聚合规则` | 还原 LC 的主逻辑、场景链、对象/因子与不确定事实 |
| `test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `source_section`, `scenario_refs`, `action_source_refs`, `trace_refs`, `confirmation_gap_refs`, `status` | 判断是数据范围、规则依赖、状态守卫还是组合爆炸 |
| `ppdcs-annotation.md` | 子模块、PPDCS 主特征、辅特征、判定依据 | 作为上游标注基线，不得静默忽略 |

若 LC / TD 缺少上述字段：
- 不得脑补；
- 在 reasoning 中标记 `[待确认]`；
- 将缺口写入 `confirmation_gap_refs / uncertain_facts`；
- 推荐方法可输出，但 `fact_status` 必须降级为 `needs-confirmation`。

## PPDCS 匹配规则

### 主规则：特征驱动匹配

```
逻辑用例 LC → 所属子模块 → 查  m-analysis/ppdcs-annotation.md 获取 PPDCS 主特征
  │
  ├── P-Process   → process-design（流程图法）
  ├── P-Parameter → parameter-design（判定表法）
  ├── D-Data      → data-design（等价类+边界值法）
  ├── C-Combination → combination-design（组合法）
  └── S-State     → state-design（状态图法）
```

### 辅助规则：混合特征处理

当子模块标注了辅特征时：
1. **主特征决定主方法**
2. **辅特征生成补充验证**：在主方法用例中追加辅特征的关键数据
3. 不为辅特征单独设计用例，避免冗余

### 区分判定（当存在疑惑时）

| 疑似 | 区分问题 | 判定 |
|------|---------|------|
| Process vs State | 流程能否回退到之前步骤？ | 不能=Process，可以=State |
| Parameter vs Data | 参数间有业务规则关系？ | 有=Parameter，没有=Data |
| Data vs Combination | 因子独立验证够？ | 够=Data，不够=Combination |
| Parameter vs Combination | 规则是确定的判定逻辑？ | 确定=Parameter，需组合探索=Combination |

### CAE → PPDCS 推断规则

在逻辑用例的 CAE 结构中，若 PPDCS 特征标注不明确或需要复核，
从 **LC 动作路径 + LC 因子表 + TD 取值集合 + trace/gap** 推断。
推断按 **A 模式（主权重）→ C 模式（次权重/强信号）→ E 模式（辅助验证）** 三轮进行。

#### A 模式规则（主权重，5条）

| 规则 | CAE / LC / TD 信号 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| A1 | 动作路径含多个有序步骤/分支，且路径不可回退 | **P-Process** | 主 |
| A2 | 动作路径核心是状态迁移/回退/生命周期切换 | **S-State** | 主 |
| A3 | 动作路径基本稳定，结果由多参数规则决定 | **P-Parameter** | 主 |
| A4 | 动作路径基本稳定，重点是单参数/单因子范围与合法性 | **D-Data** | 主 |
| A5 | 动作路径基本稳定，但 TD 显示多独立因子需压缩组合 | **C-Combination** | 主 |

#### C 模式规则（次权重/强信号，4条）

| 规则 | CAE / LC / TD 信号 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| C1 | C / 因子表 / TD 存在显式规则依赖（IF/THEN、互斥、包含、守卫） | **P-Parameter** | 次（强信号） |
| C2 | C 指向对象当前状态、迁移前置状态或守卫状态 | **S-State** | 次（强信号） |
| C3 | C / TD 含明确范围、边界、阈值、合法/非法值域 | **D-Data** | 次（强信号） |
| C4 | C / TD 含 ≥3 独立因子、多维条件并需覆盖交叉取值 | **C-Combination** | 次（强信号） |

#### E 模式规则（辅助验证，3条）

| 规则 | CAE / LC / TD 信号 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| E1 | E 明确描述进入/保持/拒绝迁移到某状态 | **S-State** | 辅助 |
| E2 | E 明确描述允许/拒绝/分流，且依赖规则命中 | **P-Parameter** | 辅助 |
| E3 | E 明确描述边界值/非法值/范围值导致不同结果 | **D-Data** | 辅助 |

#### 推断结果聚合

```
推断主特征 = A模式命中的特征（优先使用）
           ↓ 若 A 模式无命中，取 C 模式强信号特征
E 模式仅作辅助验证，不独立决定主特征

候选特征 = 标注基线 + A/C/E 命中特征 + TD 结构信号
排除特征 = 所有未被推荐的方法，必须写明排除理由

混合特征规则：
  - A 命中特征 ≠ C 命中特征（且两者均强）→ 输出 "A特征（主）+ C特征（辅）"
  - E 命中与主特征不一致 → 在 reasoning 中记录为 candidate / exclusion，不直接改主特征
  - 若 TD 中存在未确认边界或缺口导致无法定主辅，输出 `[待确认]` 并请求用户确认
```

#### 混合特征输出格式示例

```
PPDCS特征: S-State（主）+ P-Parameter（辅）
推断主信号: A2:状态切换 + C1:参数规则
```

> 该推断规则用于**复核与补全 reasoning**，上游 `ppdcs-annotation.md` 仍是首要基线。
> 若推断结果与标注冲突，需在设计计划表中标注差异原因，并将详细推断路径写入
> `analysis/plan/design-planner-reasoning.md`。

### 直接设计法回退

仅在以下**全部**条件满足时允许直接设计：
1. 步骤 ≤ 3 步
2. 数据项 ≤ 2 个
3. 无分支/无状态/无规则
4. **必须标注回退理由**
5. 直接设计法占比上限 < 5%

## 执行流程

### 步骤 1：加载输入

1. 读取 `analysis/integration/logic-cases.md` 获取逻辑用例列表
2. 读取 `analysis/integration/test-data.md` 获取 TD 清单
3. 读取 `analysis/m-analysis/ppdcs-annotation.md` 获取 PPDCS 特征标注
4. 建立 `LC → TD → 子模块 → PPDCS标注` 映射
5. 校验 LC / TD 是否保留 `scenario_refs / scenario_chain_refs / confirmation_gap_refs / factor_refs`

### 步骤 2：逐条匹配

对每个逻辑用例：
1. 查找所属子模块的 PPDCS 主/辅特征（来自 `ppdcs-annotation.md`）
2. 读取该 LC 的：
   - 动作路径 / `source_tp_ids`
   - 因子-取值表
   - 关联 TD 的 `value_set / source_section / status`
   - `scenario_refs / scenario_chain_refs / action_source_refs / confirmation_gap_refs`
3. 先记录**标注基线候选**：`annotation-primary / annotation-secondary`
4. 按 A/C/E 三轮扫描，提取**main signals** 与 **candidate features**
5. 结合 TD 结构复核：
   - 范围/边界主导 → 强化 D-Data
   - 规则依赖/守卫主导 → 强化 P-Parameter 或 S-State
   - 多因子交叉 + 压缩需求 → 强化 C-Combination
6. 对五类特征都给出处置结果：
   - `recommended`
   - `candidate-secondary`
   - `excluded`
7. 为每个 `excluded` 特征写明排除理由，至少说明“为何不是它”
8. 生成主特征 + 辅特征（若有）与推荐方法
9. 若存在以下情况，必须保留不确定性：
   - `confirmation_gap_refs` 非空
   - TD `status=needs-confirmation`
   - `knowledge_refs=missing/unavailable`
   - 上游标注与 CAE/TD 推断冲突
10. 将详细 reasoning 写入 `analysis/plan/design-planner-reasoning.md`

### 步骤 3：生成设计计划表

```markdown
## 设计计划表

| LC-ID | 逻辑用例标题 | PPDCS特征 | 推荐方法 | 设计Skill | 主信号 | 候选特征 | 排除摘要 | 关键trace | 待确认事项 |
|-------|------------|-----------|---------|-----------|---------|-----------|---------|-----------|-----------|
| LC-001 | 日志服务器参数规则 | P-Parameter | 判定表法 | `parameter-design` | A3+C1：动作稳定且结果由多参数规则决定 | P-Parameter(主), D-Data(辅) | 排除P-Process：无多步骤分支；排除S-State：无状态回退 | `SCN-LOG-001 / PRE-01 / AO-01 / LC-001 / TD-001~003` | — |
| LC-002 | 日志过滤流程 | P-Process | 流程图法 | `process-design` | A1：有序步骤+分支且不可回退 | P-Process(主) | 排除S-State：步骤非生命周期；排除D-Data：数据仅触发分支 | `SCN-LOG-002 / AO-03~AO-05 / LC-002 / TD-004` | — |
| LC-003 | 日志导出状态管理 | S-State | 状态图法 | `state-design` | A2+E1：核心是状态迁移 | S-State(主), P-Parameter(候选) | 排除P-Process：关注状态而非任务流程 | `SCN-LOG-003 / AO-07 / LC-003 / TD-005~006` | `GAP-002: 失败态退出条件待确认` |
```

### 步骤 4：统计与自检

```markdown
## 设计方法分布

| PPDCS 特征 | 设计方法 | 逻辑用例数 | 占比 |
|-----------|---------|-----------|------|
| P-Process | 流程图法 | N | X% |
| P-Parameter | 判定表法 | M | Y% |
| D-Data | 等价类+边界值法 | K | Z% |
| C-Combination | 组合法 | J | W% |
| S-State | 状态图法 | L | V% |
| — | 直接设计法 | H | U%（应<5%） |

## 自检项
- [ ] 每个 LC 都有推荐方法
- [ ] 直接设计法占比 < 5%
- [ ] PPDCS 特征与 `analysis/m-analysis/ppdcs-annotation.md` 一致
- [ ] 每个 LC 都有 `主信号 / 候选特征 / 排除摘要 / 关键trace`
- [ ] 每个 `confirmation_gap_refs` 都进入设计计划或 reasoning
- [ ] 未将 `needs-confirmation` 数据静默当作 confirmed
```

### 步骤 5：用户确认

将设计计划表展示给用户，使用 `ask_user` 工具发起结构化确认：

**ask_user 选项**：
1. ✅ 全部确认 — 设计方法合理，标记 `confirmed: true`，进入用例设计
2. ✏️ 需要修改方法 — 请指出需要调整的 LC 编号及希望改用的设计方法，修改后重新确认
3. 🔀 需要合并/拆分用例 — 请描述合并或拆分的逻辑，调整后重新确认

确认后标记 `confirmed: true`。

### 步骤 6：输出

写入以下文件：

| 文件 | 内容 |
|------|------|
| `analysis/integration/design-plan.md` | 设计计划表（含 PPDCS 特征、主信号、候选特征、排除摘要、关键 trace、待确认事项） |
| `analysis/plan/design-planner-reasoning.md` | 每条 LC 的详细 CAE→PPDCS reasoning（主信号 / 候选 / 排除 / 推荐 / trace / uncertain facts） |

**`design-planner-reasoning.md` 输出骨架**：

```markdown
# <特性名> — Design Planner Reasoning

## LC-XXX：<逻辑用例标题>

### 1. Recommendation
- `recommended_feature`: P-Parameter
- `recommended_method`: 判定表法
- `design_skill`: `parameter-design`
- `fact_status`: confirmed / needs-confirmation

### 2. Primary Signal
- `primary_signal`: A3 + C1
- `signal_summary`: 动作路径稳定，结果由参数规则与守卫决定

### 3. Candidate Features
| feature | level | signals | 结论 |
|---------|-------|---------|------|
| P-Parameter | primary | A3, C1, E2 | recommended |
| D-Data | secondary | C3, TD边界值 | candidate-secondary |
| C-Combination | weak | C4(弱) | excluded |

### 4. Exclusion Reasons
| feature | exclusion_reason |
|---------|------------------|
| P-Process | 无多步骤主路径，数据不驱动流程枚举 |
| S-State | 无可回退状态生命周期 |
| C-Combination | 因子交互受确定规则约束，优先判定表而非组合压缩 |

### 5. Trace Links
| field | refs |
|------|------|
| `scenario_refs` | SCN-001 |
| `scenario_chain_refs` | PRE-01, AO-01, AO-02 |
| `source_tp_ids` | TP-M-001, TP-M-002 |
| `td_refs` | TD-001, TD-002 |
| `test_object_refs` | OBJ-001 |
| `factor_refs` | FAC-001, FAC-002 |
| `action_source_refs` | AS-001 |

### 6. Uncertain Facts / Confirmation Gaps
| ref | 说明 | 影响 |
|-----|------|------|
| GAP-001 | 上限值待产品确认 | D-Data 边界仅作候选辅特征 |
```

## Gotchas

- PPDCS 特征是“子模块级”标注，但 design-planner 必须按 **LC + TD** 做二次复核
- 不得只从 `source_tp_ids` 简写推断，必须查看 LC 动作路径与 TD 取值集合
- `confirmation_gap_refs`、`TD.status=needs-confirmation`、`knowledge_refs=missing/unavailable` 不能被吞掉
- 混合特征必须写明“主 / 辅 / 排除”三类结果，不能只给模糊推荐
- 直接设计法应尽量避免，v2 有 5 种方法足以覆盖大部分场景
- 用户修改方法时需同步更新推荐理由、排除摘要与 reasoning

## 验收标准

- [ ] 每个逻辑用例都有 PPDCS 特征和推荐方法
- [ ] CAE→PPDCS 推断规则覆盖 A/C/E 三维度共 12 条（A5条 + C4条 + E3条）
- [ ] 推断规则按 A/C/E 三组分开呈现，每条规则含信号权重标注
- [ ] design-planner 同时消费 `logic-cases.md` 与 `test-data.md`
- [ ] 设计计划表包含 `主信号 / 候选特征 / 排除摘要 / 关键trace / 待确认事项`
- [ ] 混合特征以 `主（主）+ 辅（辅）` 格式输出
- [ ] 每条 LC 的 reasoning 至少包含 `primary_signal / candidate_features / exclusion_reasons / recommended_method`
- [ ] reasoning 保留 `scenario_refs / scenario_chain_refs / source_tp_ids / td_refs / test_object_refs / factor_refs`
- [ ] 未确认事实通过 `confirmation_gap_refs / uncertain facts` 显式保留
- [ ] 详细推断路径写入 `analysis/plan/design-planner-reasoning.md`（不在设计计划表完整展开）
- [ ] 直接设计法占比 < 5%
- [ ] 用户已确认设计计划
- [ ] 输出文件写入 `analysis/integration/design-plan.md` 与 `analysis/plan/design-planner-reasoning.md`
