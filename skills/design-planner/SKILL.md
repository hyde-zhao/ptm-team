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

读取整合后的逻辑用例列表和 PPDCS 特征标注，根据 PPDCS 五特征匹配规则
为每个逻辑用例推荐最适合的测试设计方法，生成设计计划表并与用户确认。

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
- 输入：`.output/integration/logic-cases.md` + `.output/m-analysis/ppdcs-annotation.md`
- 输出：`.output/integration/design-plan.md`

## 前置条件

- [ ] 测试点整合完成（`.output/integration/logic-cases.md` 存在）
- [ ] 测试数据已分配（`.output/integration/test-data.md` 存在）
- [ ] PPDCS 特征标注已完成（`.output/m-analysis/ppdcs-annotation.md` 存在）

## PPDCS 匹配规则

### 主规则：特征驱动匹配

```
逻辑用例 LC → 所属子模块 → 查 .output/m-analysis/ppdcs-annotation.md 获取 PPDCS 主特征
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

在逻辑用例的 CAE 结构中，若 PPDCS 特征标注不明确，可从 CAE 特征推断。
推断按 **A 模式（主权重）→ C 模式（次权重/强信号）→ E 模式（辅助验证）** 三轮进行。

#### A 模式规则（主权重，5条）

| 规则 | CAE 特征 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| A1 | A 含多个有序步骤，有分支，不可回退 | **P-Process** | 主 |
| A2 | A 描述状态切换（从状态X到状态Y） | **S-State** | 主 |
| A3 | A 是单次操作 + C 为多参数规则组合（参数间有业务约束） | **P-Parameter** | 主 |
| A4 | A 是单次操作 + C 为单参数多取值（参数独立，验证范围） | **D-Data** | 主 |
| A5 | C 包含多个独立因子且组合数 > 可枚举量（≥ 3 因子，各 ≥ 3 取值） | **C-Combination** | 主 |

#### C 模式规则（次权重/强信号，4条）

| 规则 | CAE 特征 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| C1 | C 描述参数间规则依赖（若 P1=X 且 P2=Y 则允许） | **P-Parameter** | 次（强信号） |
| C2 | C 描述特定对象状态（对象处于状态 X） | **S-State** | 次（强信号） |
| C3 | C 描述数值范围（大于 / 小于 / 等于 N） | **D-Data** | 次（强信号） |
| C4 | C 描述多因子组合（A=x, B=y, C=z，因子数 ≥ 3） | **C-Combination** | 次（强信号） |

#### E 模式规则（辅助验证，3条）

| 规则 | CAE 特征 | 推断 PPDCS | 信号权重 |
|------|---------|-----------|---------|
| E1 | E 描述状态变化（系统进入状态 Z） | **S-State** | 辅助 |
| E2 | E 描述结果与规则强相关（允许 / 拒绝，依赖业务规则） | **P-Parameter** | 辅助 |
| E3 | E 描述不同数据值对应不同结果（各参数取值范围不同则结果不同） | **D-Data** | 辅助 |

#### 推断结果聚合

```
推断主特征 = A模式命中的特征（优先使用）
           ↓ 若 A 模式无命中，取 C 模式强信号特征
E 模式仅作辅助验证，不独立决定主特征

混合特征规则：
  - A 命中特征 ≠ C 命中特征（且两者均强）→ 输出 "A特征（主）+ C特征（辅）"
  - E 命中与主特征不一致 → 在推断路径文件中记录差异，不改变主特征
```

#### 混合特征输出格式示例

```
PPDCS特征: S-State（主）+ P-Parameter（辅）
推断主信号: A2:状态切换 + C1:参数规则
```

> 该推断规则仅用于辅助判定，最终以 `.output/m-analysis/ppdcs-annotation.md` 中的标注为准。
> 若推断结果与标注冲突，需在设计计划表中标注差异原因，并将详细推断路径写入
> `.output/plan/design-planner-reasoning.md`。

### 直接设计法回退

仅在以下**全部**条件满足时允许直接设计：
1. 步骤 ≤ 3 步
2. 数据项 ≤ 2 个
3. 无分支/无状态/无规则
4. **必须标注回退理由**
5. 直接设计法占比上限 < 5%

## 执行流程

### 步骤 1：加载输入

1. 读取 `.output/integration/logic-cases.md` 获取逻辑用例列表
2. 读取 `.output/m-analysis/ppdcs-annotation.md` 获取 PPDCS 特征标注
3. 建立 LC → 子模块 → PPDCS 特征的映射

### 步骤 2：逐条匹配

对每个逻辑用例：
1. 查找所属子模块的 PPDCS 主特征（来自 `ppdcs-annotation.md`）
2. 若特征明确，按主规则匹配设计方法；记录推断主信号（简洁版：如 `标注:P-Process`）
3. 若特征标注为"混合"或不明确，按 CAE 推断规则三轮扫描：
   - **A 模式扫描**（A1→A5）→ 命中则记录主特征
   - **C 模式扫描**（C1→C4）→ 命中则记录次特征（强信号）
   - **E 模式扫描**（E1→E3）→ 命中则记录辅助特征
4. 聚合推断结果（A主 + C次 + E辅），生成主特征 + 辅特征（若有）
5. 检查辅特征，记录补充验证需求
6. 将详细推断路径写入 `.output/plan/design-planner-reasoning.md`

### 步骤 3：生成设计计划表

```markdown
## 设计计划表

| LC-ID | 逻辑用例标题 | PPDCS特征 | 推荐方法 | 设计Skill | 推断主信号 | 辅特征补充 |
|-------|------------|-----------|---------|-----------|----------|-----------|
| LC-001 | 日志服务器参数规则 | P-Parameter | 判定表法 | parameter-design | A3:单操作+多参数规则 | D-Data:端口边界值(C3) |
| LC-002 | 日志过滤流程 | P-Process | 流程图法 | process-design | A1:多步骤有序 | — |
| LC-003 | 日志导出状态管理 | S-State | 状态图法 | state-design | A2:状态切换 | — |
| LC-004 | 日志查询条件 | D-Data | 等价类+边界值法 | data-design | A4:单操作+单参数多值 | C-Combination(C4):多条件组合 |
| LC-005 | 日志告警级别组合 | C-Combination | 组合法 | combination-design | A5:多独立因子 | — |
| LC-006 | 连接状态转换 | S-State（主）+P-Parameter（辅） | 状态图法 | state-design | A2:状态切换+C1:参数规则 | — |
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
- [ ] PPDCS 特征与 `.output/m-analysis/ppdcs-annotation.md` 一致
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
| `.output/integration/design-plan.md` | 设计计划表（含 PPDCS 特征列 + 推断主信号列） |
| `.output/plan/design-planner-reasoning.md` | 每条 LC 的详细 CAE 推断路径（A/C/E 三轮扫描结果，不在设计计划表展示） |

## Gotchas

- PPDCS 特征是"子模块级"标注，同一子模块的不同 LC 通常共享主特征
- 如果某 LC 的逻辑与子模块主特征不一致，以 LC 实际逻辑为准做二次判定
- 直接设计法应尽量避免，v2 有 5 种方法足以覆盖大部分场景
- 用户修改方法时需更新推荐理由

## 验收标准

- [ ] 每个逻辑用例都有 PPDCS 特征和推荐方法
- [ ] CAE→PPDCS 推断规则覆盖 A/C/E 三维度共 12 条（A5条 + C4条 + E3条）
- [ ] 推断规则按 A/C/E 三组分开呈现，每条规则含信号权重标注
- [ ] 设计计划表包含"推断主信号"列（简洁格式，如 `A1:多步骤有序`）
- [ ] 混合特征以 `主（主）+ 辅（辅）` 格式输出
- [ ] 详细推断路径写入 `.output/plan/design-planner-reasoning.md`（不在设计计划表展示）
- [ ] 直接设计法占比 < 5%
- [ ] 用户已确认设计计划
- [ ] 输出文件写入 `.output/integration/design-plan.md`
