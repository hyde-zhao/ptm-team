# LLD — STORY-010-05 更新核心文档

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-01 | meta-dev | 初始 LLD，定义 5 个 `docs/ptm-tde/` 核心文档的变更方案。 |
| 1.1 | 2026-06-01 | meta-dev | [P0-B1] 统一路径引用：修正 README.md §7「改后目录树」、USER-MANUAL.md §3.3「改后目录树」、runtime-artifacts.md §3.3「改后目录树」三处目录树结构：将 `checkpoints/` 和 `doc/STATE.yaml` 从顶层目录移入 `process/` 子树（新增 `process/checkpoints/`、`process/STATE.yaml`）。 |
| 1.2 | 2026-06-01 | meta-dev | [M1] 补全 meta-dev LLD 规范要求的 7 个缺失章节：Requirements (F/NF)、模块拆分与职责、数据模型与持久化设计、技术设计细节、安全与性能设计、实施步骤、风险/难点与预研建议。 |

---

## 1. 概述

将 5 个 `docs/ptm-tde/` 核心文档从 **11 步 + CP + analysis/design/** 体系更新为 **三阶段 + Gate + kym/mfq/ppdcs/process/** 体系。本 Story 只做文档描述层的更新，不修改任何 Skill 的 SKILL.md 文件或 Agent 配置。

**核心文件**（5 个）：
1. `docs/ptm-tde/README.md`
2. `docs/ptm-tde/USER-MANUAL.md`
3. `docs/ptm-tde/runtime-artifacts.md`
4. `docs/ptm-tde/component-manual.md`
5. `docs/ptm-tde/skill-references.md`

---

## 2. 受影响文件清单

| 文件 | 变更类型 | 变更范围 |
|------|----------|----------|
| `docs/ptm-tde/README.md` | 更新 | 5 个章节（见 §3.1） |
| `docs/ptm-tde/USER-MANUAL.md` | 更新 | 5 个章节（见 §3.2） |
| `docs/ptm-tde/runtime-artifacts.md` | 更新 | 目录树 + 8 处路径引用（见 §3.3） |
| `docs/ptm-tde/component-manual.md` | 更新 | 主流程表 + 调用关系表（见 §3.4） |
| `docs/ptm-tde/skill-references.md` | 更新 | 主流程 Skill 表 + 阶段归属（见 §3.5） |

**不修改的文件**：
- `docs/ptm-tde/gate-spec.md`（本 CR 已新建，规格已冻结）
- `docs/ptm-tde/checkpoint-spec.md`（待 STORY-010-01 处理，已归档为 `checkpoint-spec-v1-archived.md`）
- `docs/ptm-tde/checkpoint-spec-v1-archived.md`（归档文件，不动）

---

## 3. 变更方案

### 3.1 README.md 变更

**章节定位**：`docs/ptm-tde/README.md`（当前 557 行）

#### 3.1.1 目录 TOC 更新

**位置**：`## 目录`（第 10-26 行）

改前（涉及行）：
```markdown
3. [11 步主流程](#3-11-步主流程)
4. [人工检查点（3 类）](#4-人工检查点3-类)
```

改后：
```markdown
3. [三阶段框架](#3-三阶段框架)
4. [Gate 检查点（3 类）](#4-gate-检查点3-类)
```

#### 3.1.2 §2.5 系统架构图更新

**位置**：`### 2.5 系统架构`（第 155-176 行）

改前：
```text
│              （11步状态机 + 2扩展分支）                       │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  Input   │ Scenario │ M/F/Q    │  PPDCS   │   Delivery     │
│  Layer   │          │ Analysis │  Design  │                │
```

改后：
```text
│           （三阶段框架 + 入口/出口门控）                        │
├───────────────┬──────────────────┬──────────────────────┤
│  KYM Phase    │  MFQ Phase       │  PPDCS Phase         │
│  (输入解析+场景) │  (M/F/Q/整合/计划) │  (设计+PC+覆盖+交付)   │
```

架构图中 `19 Skills` 保持不变。

#### 3.1.3 §3 11步主流程 → 三阶段框架

**位置**：`## 3. 11 步主流程`（第 222-244 行）

**变更要点**：整节替换。

改前（全节内容）：
```markdown
## 3. 11 步主流程

```
步骤  阶段         描述                                  关键 Skill
───────────────────────────────────────────────────────────────────
 1.  input         CP01自检 + 特性文件解析 + 三~五级目录生成     checkpoint-manager + feature-parser
 2.  scenario      场景再发现 + 操作路径建模 + Topology + atomic-ops + CP02自检/确认  scenario-discovery
 3.  m-analysis    单功能拆分 + PPDCS标注 + CAE测试点           m-analyzer
 4.  f-analysis    耦合分析（三源合并）+ CAE耦合测试点           f-analyzer
 5.  q-analysis    质量属性分析 + CAE质量测试点                 q-analyzer
 6.  integration   M+F+Q CAE聚合 → 逻辑用例(LC) + topology_bindings test-point-integrator
 7.  plan          CAE→PPDCS推断 + 设计方法匹配                 design-planner
 8.  design-ppdcs  每LC输出PPDCS逻辑设计过程文件                 design-ppdcs-analyzer + 5 design Skills
 9.  design-pc     每LC输出物理用例文件                         5 design Skills
10.  coverage      双层覆盖率验证 + CP11确认                    coverage-verifier
11.  delivery      交付物生成（测试方案 + 测试用例总表）          deliverable-renderer
```

**扩展分支**：

- **需求变更**：`change-impact-analyzer` → 增量 MFQ → 增量设计 → 增量覆盖
- **问题单分析**：`bug-gap-analyzer` → 盲区定位 → 用例补充 → 流程优化
```

改后：
```markdown
## 3. 三阶段框架

ptm-tde 按三阶段 + 入口/出口门控体系推进：

```
Entry Gate（GATE-1，纯自检）
  → KYM Phase: feature-parser → scenario-discovery
    → KYM Exit Gate（GATE-2，自检+人工确认）
      → MFQ Phase: m-analyzer → f-analyzer → q-analyzer → test-point-integrator → design-planner
        → MFQ Exit Gate（GATE-3，自检+人工确认）
          → PPDCS Phase: design-ppdcs-analyzer + 5设计Skill → PC → coverage-verifier → deliverable-renderer
            → PPDCS Exit Gate（GATE-4，自检+人工确认）
              → Exit Gate（GATE-5，纯自检）
```

| 阶段 | 步骤 | 关键 Skill | 出口 Gate |
|------|------|-----------|-----------|
| **KYM**（Know Your Mission） | 输入解析 + 场景发现 | `feature-parser`、`scenario-discovery` | GATE-2 KYM Exit Gate（自检+人工确认） |
| **MFQ**（M/F/Q Analysis） | M分析 → F分析 → Q分析 → 整合 → 设计计划 | `m-analyzer`、`f-analyzer`、`q-analyzer`、`test-point-integrator`、`design-planner` | GATE-3 MFQ Exit Gate（自检+人工确认） |
| **PPDCS**（Design & Delivery） | PPDCS设计 → PC生成 → 覆盖验证 → 交付 | `design-ppdcs-analyzer`、5设计Skill、`coverage-verifier`、`deliverable-renderer` | GATE-4 PPDCS Exit Gate（自检+人工确认） + GATE-5 Exit Gate（纯自检） |

### CP↔Gate 映射

| 原 CP | 新体系 | 类型 |
|-------|--------|------|
| CP01 | GATE-1 Entry Gate | 纯自检 |
| CP02 | GATE-2 KYM Exit Gate | 自检+人工 |
| CP03-CP07 | MFQ 阶段内滚动自检 | 纯自检 |
| — | GATE-3 MFQ Exit Gate | 自检+人工（新增） |
| CP08/CP10 | PPDCS 阶段内滚动自检 | 纯自检 |
| CP09+CP11 | GATE-4 PPDCS Exit Gate | 自检+人工 |
| CP12 | GATE-5 Exit Gate | 纯自检 |

**扩展分支**：

- **需求变更**：`change-impact-analyzer` → 增量 MFQ → 增量设计 → 增量覆盖
- **问题单分析**：`bug-gap-analyzer` → 盲区定位 → 用例补充 → 流程优化
```

#### 3.1.4 §4 人工检查点（3 类）→ Gate 检查点

**位置**：`## 4. 人工检查点（3 类）`（第 247-314 行）

**变更要点**：
1. 标题从 "人工检查点（3 类）" 改为 "Gate 检查点（3 类）"
2. 介绍文字从 "工具只在以下 3 个关键节点暂停并等待人工确认" 改为 "工具在以下 3 个 Gate 暂停并等待人工确认"
3. 三个确认点重新编号和命名：

**汇总变更表**：

| 改前 | 改后 |
|------|------|
| `### ① CP02：目录结构与场景自检/确认（步骤 2 结束后）` | `### GATE-2 KYM Exit Gate（自检+人工）` |
| 触发时机：`scenario-discovery` 完成应用场景分析后 | 触发时机：KYM 阶段（feature-parser + scenario-discovery）完成后 |
| **自动自检内容** 10 项不变 | 内容不变 |
| **通过后**：进入 m-analysis（步骤 3） | **通过后**：进入 MFQ 阶段 |
| `### ② CP09：PPDCS 逻辑设计确认（步骤 8 结束后）` | `### GATE-3 MFQ Exit Gate（自检+人工）` |
| `### ③ CP11：覆盖率确认（步骤 10 完成后）` | `### GATE-4 PPDCS Exit Gate（自检+人工）` |

**GATE-3 是新增内容**，需要在 README 中增加：
```markdown
### GATE-3 MFQ Exit Gate（自检+人工，**新增**）

**触发时机**：MFQ 阶段（M/F/Q/整合/设计计划）全部完成后
**自动自检内容**：

| 自检项 | 说明 |
|-------|------|
| M 分析完整性 | 每个单功能有 PPDCS 特征标注和 CAE 测试点 |
| F 分析完整性 | 耦合关系有三源合并，CAE 耦合测试点已生成 |
| Q 分析完整性 | 质量属性有 HTSM 映射，CAE 质量测试点已生成 |
| 整合完整性 | M+F+Q 测试点归集到 LC，包含 factor_bindings 和 topology_bindings |
| 设计计划完整性 | CAE→PPDCS 推断和设计计划已生成 |

**需要人工确认**：

| 确认项 | 说明 |
|-------|------|
| M/F/Q 分析质量 | 各维度分析是否覆盖完整 |
| LC 整合一致性 | 测试点归集、因子绑定和拓扑绑定是否一致 |
| 设计计划 | CAE→PPDCS 推断是否合理 |
| 公共因子消费 | 因子库 lock 和候选提案是否合理 |

**通过后**：进入 PPDCS 阶段
```

原有 CP09 确认内容（PPDCS 逻辑设计确认）合并到 GATE-4 中。

#### 3.1.5 §7 文件结构更新

**位置**：`## 7. 文件结构`（第 401-438 行）

**变更要点**：将 `### 工作目录` 下的目录树替换为新目录结构。

改前目录树：
```text
├── analysis/                    # ptm-tde 生成的分析过程
│   ├── feature-input/
│   ├── scenarios/
│   ├── m-analysis/
│   ├── f-analysis/
│   ├── q-analysis/
│   ├── integration/
│   ├── plan/
│   ├── factor-usage/
│   └── coverage/
├── design/
│   ├── ppdcs/
│   └── pc/
├── checkpoints/
├── delivery/
└── doc/STATE.yaml
```

改后目录树：
```text
├── kym/                         # KYM 阶段产物
│   ├── feature-input/           # 解析后结构化需求 + 目录
│   └── scenarios/               # 确认后的应用场景（三层结构）
├── mfq/                         # MFQ 阶段产物
│   ├── m-analysis/
│   │   ├── test-points.md       # M 测试点（CAE 三元组）
│   │   └── ppdcs-annotation.md  # PPDCS 特征标注表
│   ├── f-analysis/              # 耦合图模型 + 耦合测试点
│   ├── q-analysis/              # 质量属性测试点（CAE 格式）
│   ├── integration/
│   │   ├── all-test-points.md   # M+F+Q 汇总（CAE 格式）
│   │   ├── logic-cases.md       # 逻辑用例（含聚合规则标注）
│   │   └── design-plan.md       # 设计计划（含 PPDCS 特征+推断主信号）
│   └── factor-usage/            # 因子库 lock、binding、候选提案和解析报告
├── process/
│   ├── plan/
│   │   └── design-planner-reasoning.md  # PPDCS 推断详细路径
│   ├── checkpoints/
│   └── STATE.yaml
├── ppdcs/                       # PPDCS 阶段产物
│   ├── ppdcs/
│   │   └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
│   ├── pc/
│   │   └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
│   ├── coverage/
│   └── delivery/
│       ├── <特性名>特性测试方案.md
│       └── <特性名>特性测试用例.md
```

同时更新目录说明文字：
- `analysis/` → `kym/` + `mfq/` + `process/`
- `design/` → `ppdcs/`
- 所有 `analysis/factor-usage/` → `mfq/factor-usage/`
- 所有 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`

#### 3.1.6 §8 近期变更同步 — 公共因子库路径更新

**位置**：`### 8.2 CR-20260521-001：公共因子库 Resource`（第 499-555 行）

变更要点：
- `analysis/factor-usage/` → `mfq/factor-usage/`（5 处出现）
- 目录树 `analysis/factor-usage/` → `mfq/factor-usage/`

---

### 3.2 USER-MANUAL.md 变更

**章节定位**：`docs/ptm-tde/USER-MANUAL.md`（当前 582 行）

#### 3.2.1 角色说明 — CP→Gate 引用更新

**位置**：`## 2. 角色说明`（第 12-17 行）

改前：
```markdown
| 测试架构师 | 导入需求、确认目录与 Scenario Chain、评审设计计划与覆盖率 | 通过 `@ptm-tde ...` 发起分析、确认关键检查点 |
```

改后：
```markdown
| 测试架构师 | 导入需求、确认目录与 Scenario Chain、评审设计计划与覆盖率 | 通过 `@ptm-tde ...` 发起分析、在 GATE-2/GATE-3/GATE-4 确认检查点 |
```

#### 3.2.2 §3.3 运行时目录规则更新

**位置**：`### 3.3 运行时目录规则`（第 57-67 行）

改前目录树：
```text
├── input/          # 用户原始输入，只读
├── analysis/       # feature-input / scenarios / M/F/Q / integration / plan / coverage
│   └── factor-usage/ # 公共因子库 lock、binding、候选提案和解析报告
├── design/
│   ├── ppdcs/      # 每个逻辑用例一份 PPDCS 设计过程
│   └── pc/         # 每个逻辑用例一份物理用例设计
├── checkpoints/    # 自动和人工检查点记录
├── delivery/       # 最终测试方案与测试用例总表
└── doc/            # STATE.yaml 等运行状态
```

改后目录树：
```text
├── input/          # 用户原始输入，只读
├── kym/            # KYM 阶段产物：feature-input / scenarios
├── mfq/            # MFQ 阶段产物：M/F/Q / integration / factor-usage
│   └── factor-usage/ # 公共因子库 lock、binding、候选提案和解析报告
├── process/
│   ├── plan/       # MFQ→PPDCS 跨阶段设计计划
│   ├── checkpoints/# Gate 检查点记录
│   └── STATE.yaml  # 当前特性项目运行状态
├── ppdcs/          # PPDCS 阶段产物：ppdcs / pc / coverage / delivery
│   ├── ppdcs/      # 每个逻辑用例一份 PPDCS 设计过程
│   ├── pc/         # 每个逻辑用例一份物理用例设计
│   ├── coverage/   # 覆盖率报告
│   └── delivery/   # 最终测试方案与测试用例总表
```

强约束更新：
1. `input/` 只读，不回写分析产物（不变）
2. 不创建、不写入 `.output/`（不变）
3. 阶段产物按目录归档，最终交付只写入 `ppdcs/delivery/`（原 `delivery/`）
4. PPDCS 与 PC 均采用扁平文件，不再使用多级嵌套目录（不变）
5. 公共因子库主库只在 `ptm-team/resource/` 和用户级公共资源目录归档，项目内不得复制为主库（不变）

#### 3.2.3 公共因子库路径更新

**位置**：`### 4.2 公共因子库`（第 95-105 行）

变更：
- 步骤 3 中 `analysis/factor-usage/factor-library-lock.yaml` → `mfq/factor-usage/factor-library-lock.yaml`
- 步骤 4/5 中的 `analysis/factor-usage/` → `mfq/factor-usage/`

**位置**：`### 4.2.1 测试因子...`（第 106-128 行）

变更：
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`（3 处出现）

#### 3.2.4 公共因子库消费记录路径更新

**位置**：`### 12.2 公共因子库安装...`（第 522-555 行）

变更：
- `analysis/factor-usage/` → `mfq/factor-usage/`（目录树中 2 处）

#### 3.2.5 拓扑绑定基线路径更新

**位置**：`### 4.4 Topology Modeling (CR-008)`（第 160-176 行）

变更：
- `analysis/scenarios/<scene-id>/` → `kym/scenarios/<scene-id>/`（输出位置）
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`

---

### 3.3 runtime-artifacts.md 变更

**章节定位**：`docs/ptm-tde/runtime-artifacts.md`（当前 156 行）

#### 3.3.1 目录树完全替换

**位置**：`## 目录结构`（第 5-24 行）

改前：
```text
<feature-project-root>/
├── input/
├── analysis/
│   ├── feature-input/
│   ├── scenarios/
│   ├── m-analysis/
│   ├── f-analysis/
│   ├── q-analysis/
│   ├── integration/
│   ├── plan/
│   ├── factor-usage/
│   └── coverage/
├── design/
│   ├── ppdcs/
│   └── pc/
├── checkpoints/
├── delivery/
└── doc/STATE.yaml
```

改后：
```text
<feature-project-root>/
├── input/
├── kym/
│   ├── feature-input/
│   └── scenarios/
├── mfq/
│   ├── m-analysis/
│   ├── f-analysis/
│   ├── q-analysis/
│   ├── integration/
│   └── factor-usage/
├── process/
│   ├── plan/
│   ├── checkpoints/
│   └── STATE.yaml
├── ppdcs/
│   ├── ppdcs/
│   ├── pc/
│   ├── coverage/
│   └── delivery/
```

#### 3.3.2 公共因子库消费记录路径更新

**位置**：`## 公共因子库消费记录`（第 39-60 行）

变更：
- 特性项目保存位置说明：`analysis/factor-usage/` → `mfq/factor-usage/`
- 目录树中 `analysis/factor-usage/` → `mfq/factor-usage/`（含 4 个子文件路径不变）
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`（末尾段落 1 处）

#### 3.3.3 场景产物字段路径更新

**位置**：`## 场景产物字段`（第 64 行起）

变更：
- `analysis/scenarios/` → `kym/scenarios/`（开头描述）
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`（2 处）

#### 3.3.4 分析产物目录表更新

**位置**：`## 分析产物`（第 102-114 行）

改前：
```markdown
| 目录 | 内容 |
| `analysis/feature-input/` | 结构化需求与三~五级目录 |
| `analysis/scenarios/` | Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference |
| `analysis/m-analysis/` | M 分析测试点、PPDCS 标注、对象与因子 |
| `analysis/f-analysis/` | 耦合图、耦合测试点 |
| `analysis/q-analysis/` | 质量属性测试点 |
| `analysis/integration/` | 全量测试点、逻辑用例、测试数据、设计计划输入；LC 中保留 `factor_bindings` 与 `topology_bindings` |
| `analysis/plan/` | PPDCS 推断 reasoning |
| `analysis/factor-usage/` | 公共因子库 lock、binding、候选提案和解析报告 |
| `analysis/coverage/` | 需求层与测试点层覆盖报告 |
```

改后：
```markdown
| 目录 | 内容 | 阶段 |
| `kym/feature-input/` | 结构化需求与三~五级目录 | KYM |
| `kym/scenarios/` | Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference | KYM |
| `mfq/m-analysis/` | M 分析测试点、PPDCS 标注、对象与因子 | MFQ |
| `mfq/f-analysis/` | 耦合图、耦合测试点 | MFQ |
| `mfq/q-analysis/` | 质量属性测试点 | MFQ |
| `mfq/integration/` | 全量测试点、逻辑用例、测试数据、设计计划输入；LC 中保留 `factor_bindings` 与 `topology_bindings` | MFQ |
| `mfq/factor-usage/` | 公共因子库 lock、binding、候选提案和解析报告 | MFQ |
| `process/plan/` | PPDCS 推断 reasoning | 跨阶段边界 |
| `ppdcs/coverage/` | 需求层与测试点层覆盖报告 | PPDCS |
```

#### 3.3.5 设计产物路径更新

**位置**：`## 设计产物`（第 116-155 行）

变更：
- `design/ppdcs/<...>.md` → `ppdcs/ppdcs/<...>.md`（2 处）
- `design/pc/<...>.md` → `ppdcs/pc/<...>.md`（2 处）
- PC 拓扑物化字段小节的 `design/pc/<basename>.md` → `ppdcs/pc/<basename>.md`
- 尾部说明 `design/<module>/<sub-module>/` → `ppdcs/<module>/<sub-module>/`

#### 3.3.6 交付产物路径更新

**位置**：`## 交付产物`（第 146-156 行）

变更：
- `delivery/` → `ppdcs/delivery/`（标题下描述和文件路径）

---

### 3.4 component-manual.md 变更

**章节定位**：`docs/ptm-tde/component-manual.md`（当前 54 行）

#### 3.4.1 主流程表替换

**位置**：`## 主流程`（第 9-21 行）

改前：
```markdown
| 步骤 | 阶段 | 主要 Skill | 产物目录 |
| 1 | input | `checkpoint-manager`、`feature-parser` | `checkpoints/`、`analysis/feature-input/` |
| 2 | scenario | `scenario-discovery` | `analysis/scenarios/` |
| 3 | m-analysis | `m-analyzer` | `analysis/m-analysis/` |
| 4 | f-analysis | `f-analyzer` | `analysis/f-analysis/` |
| 5 | q-analysis | `q-analyzer` | `analysis/q-analysis/` |
| 6 | integration | `test-point-integrator` | `analysis/integration/` |
| 7 | plan | `design-planner` | `analysis/plan/` |
| 8 | design-ppdcs | `design-ppdcs-analyzer` + 五类设计 Skill | `design/ppdcs/` |
| 9 | design-pc | 五类设计 Skill | `design/pc/` |
| 10 | coverage | `coverage-verifier` | `analysis/coverage/` |
| 11 | delivery | `deliverable-renderer` | `delivery/` |
```

改后：
```markdown
| 阶段 | 步骤 | 主要 Skill | 产物目录 | 出口 Gate |
|------|------|-----------|----------|-----------|
| **KYM** | 输入解析 + 场景发现 | `checkpoint-manager`（GATE-1）、`feature-parser`、`scenario-discovery` | `kym/feature-input/`、`kym/scenarios/` | GATE-2 KYM Exit |
| **MFQ** | M分析 | `m-analyzer` | `mfq/m-analysis/` | — |
| | F分析 | `f-analyzer` | `mfq/f-analysis/` | — |
| | Q分析 | `q-analyzer` | `mfq/q-analysis/` | — |
| | 整合 | `test-point-integrator` | `mfq/integration/` | — |
| | 设计计划 | `design-planner` | `process/plan/`、`mfq/factor-usage/` | GATE-3 MFQ Exit |
| **PPDCS** | PPDCS 设计 | `design-ppdcs-analyzer` + 五类设计 Skill | `ppdcs/ppdcs/` | — |
| | PC 生成 | 五类设计 Skill | `ppdcs/pc/` | — |
| | 覆盖验证 | `coverage-verifier` | `ppdcs/coverage/` | — |
| | 交付 | `deliverable-renderer` | `ppdcs/delivery/` | GATE-4 PPDCS Exit + GATE-5 Exit |
```

#### 3.4.2 使用边界路径更新

**位置**：`## 使用边界`（第 23-31 行）

变更：
- `所有运行产物直接生成在特性项目根目录下的规范目录` —— 保留不变，但补充"按阶段目录归档"
- `analysis/factor-usage/` → `mfq/factor-usage/`

#### 3.4.3 关键调用关系更新

**位置**：`## 关键调用关系`（第 33-43 行）

变更（逐条）：
1. `checkpoint-manager 执行 CP01 input 自检` → `checkpoint-manager 执行 GATE-1 Entry Gate 自检`
2. 不变
3. 不变
4. 不变
5. `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`
6. 不变
7. 不变
8. 不变
9. 不变
10. 不变

---

### 3.5 skill-references.md 变更

**章节定位**：`docs/ptm-tde/skill-references.md`（当前 62 行）

#### 3.5.1 主流程 Skill 表 — 阶段列更新

**位置**：`## 主流程 Skill`（第 16-33 行）

改前表格的 `<阶段>` 列取值：`checkpoint`、`input`、`scenario`、`m-analysis`、`f-analysis`、`q-analysis`、`integration`、`plan`、`design-ppdcs`、`design-ppdcs / design-pc`（5 条）、`coverage`、`delivery`

改后：

| 阶段 | Skill | 职责 |
|------|-------|------|
| KYM | `checkpoint-manager` | 执行 GATE-1 Entry Gate 和 GATE-2 KYM Exit Gate 自检与人工确认；保留旧 CP 编号兼容路由。 |
| KYM | `feature-parser` | 解析特性需求文件，提取结构化需求并生成三至五级目录结构。 |
| KYM | `scenario-discovery` | 重新发现部署型场景，生成 Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference 和确认缺口。 |
| MFQ | `m-analyzer` | 执行 M 分析；提取测试因子前先读取公共因子库，复用 active 因子，输出 factor bindings、扩展建议和候选提案；CAE 只引用 `topology_role_refs`，不写真实端口。 |
| MFQ | `f-analyzer` | 执行 F 分析，合并耦合矩阵、场景耦合和可选代码依赖，生成 CAE 耦合测试点。 |
| MFQ | `q-analyzer` | 执行 Q 分析，基于 HTSM 质量属性维度生成 CAE 质量测试点和工具覆盖评估。 |
| MFQ | `test-point-integrator` | 整合 M/F/Q 测试点，消费 `factor_bindings`，从 `kym/scenarios/confirmed-scenarios.md` 生成 LC `topology_bindings`，输出逻辑用例、测试数据、工具分析归并和覆盖关系。 |
| MFQ | `design-planner` | 根据 LC、测试数据、CAE 信号、公共因子库约束和 `topology_binding_status` 推荐 PPDCS 设计方法，并输出推断过程。 |
| PPDCS | `design-ppdcs-analyzer` | 协调 PPDCS 逻辑设计，按 LC 统一收敛 PPDCS 设计过程文件和 PC 文件，并要求 PC 真实端口回链到 LC `topology_bindings`。 |
| PPDCS | `process-design` | 针对 P-Process 类型 LC 执行流程图法设计，输出流程模型、路径枚举、触发数据和物理用例。 |
| PPDCS | `parameter-design` | 针对 P-Parameter 类型 LC 执行参数规则设计，输出规则提取、判定结构、参数组和物理用例。 |
| PPDCS | `data-design` | 针对 D-Data 类型 LC 执行等价类与边界值设计，输出值域、等价类、边界选点和物理用例。 |
| PPDCS | `combination-design` | 针对 C-Combination 类型 LC 执行组合设计，输出因子值域、约束、组合压缩策略和物理用例。 |
| PPDCS | `state-design` | 针对 S-State 类型 LC 执行状态图设计，输出状态模型、迁移表、守卫条件和物理用例。 |
| PPDCS | `coverage-verifier` | 执行 SR 到 LC 到 PC、TP 到 PC 的双层覆盖验证，校验公共库因子覆盖，并校验 PC 真实端口能回链到 LC `topology_bindings` 与 `kym/scenarios/confirmed-scenarios.md`。 |
| PPDCS | `deliverable-renderer` | 汇总分析、设计和覆盖结果，生成最终测试方案和测试用例总表，输出因子库版本、样本策略摘要，并保留 `topology_bindings / topology_role / source / fact_status`。 |

同时在职责文字中更新路径引用：
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`（2 处出现在 `test-point-integrator` 和 `coverage-verifier` 的职责描述中）

---

## 4. 接口与契约

本 Story 仅修改文档描述，不引入新接口或变更契约。所有 Skill 的运行逻辑不变。

**文档间一致性契约**：
- 所有 5 个文档中 `analysis/` 和 `design/` 不作为主路径引用
- 所有 5 个文档中使用相同的阶段名称（KYM / MFQ / PPDCS）
- 所有 5 个文档中使用相同的 Gate 编号（GATE-1 至 GATE-5）
- `confirmed-scenarios.md` 路径在所有文档中一致为 `kym/scenarios/confirmed-scenarios.md`
- `factor-usage` 路径在所有文档中一致为 `mfq/factor-usage/`

---

## 5. 异常与失败处理

| 场景 | 处理 |
|------|------|
| 文档更新后路径引用不一致（如 README 说 `kym/scenarios/` 而 USER-MANUAL 说 `analysis/scenarios/`） | 验证脚本逐文件 grep，发现不一致时回退到对应文档的该段并修正 |
| 文档中遗漏了某处旧路径引用 | 验证脚本逐文件搜索 `analysis/`、`design/`（除 `design/ppdcs/` → `ppdcs/ppdcs/` 需逐行确认上下文） |
| `process/plan/` 路径与 ptm-team 运行时 `process/` 混淆 | 在文档中增加注释说明：特性项目根目录下的 `process/plan/` 与 ptm-team 仓库的 `process/` 是不同路径 |

---

## 6. 测试方案

### 6.1 文档级测试

| 测试项 | 验证方式 | 预期结果 |
|--------|----------|----------|
| README.md 旧编号消除 | `grep -c "11 步\|11步\|CP01\|...\|CP12" docs/ptm-tde/README.md` | 仅在 CP↔Gate 映射表中出现旧 CP 编号 |
| README.md 旧路径消除 | `grep -c "analysis/\|design/" docs/ptm-tde/README.md` | 0（或仅出现在历史说明中） |
| USER-MANUAL.md 旧路径消除 | `grep -c "analysis/factor-usage\|analysis/scenarios/confirmed-scenarios\|design/ppdcs/\|design/pc/" docs/ptm-tde/USER-MANUAL.md` | 0 |
| runtime-artifacts.md 目录树完整性 | 检查所有 12 个新目录是否存在 | 每个目录出现在树中，路径前缀正确 |
| component-manual.md 主流程表阶段列 | 检查阶段列取值为 KYM / MFQ / PPDCS | 3 个阶段完整覆盖所有 Skill |
| skill-references.md 阶段归属一致性 | 对比 `agents/ptm-tde.md` 的 Skill 触发表 | 两个文件中的阶段归属一致 |

### 6.2 跨文档一致性测试

| 测试项 | 验证方式 | 预期结果 |
|--------|----------|----------|
| Gate 编号一致 | 搜索 5 个文档中 `GATE-` 出现次数，检查编号范围 | 所有引用在 GATE-1 至 GATE-5 范围内 |
| 阶段名称一致 | 搜索 KYM / MFQ / PPDCS 在各文档中的使用 | 全部大写，语义一致 |
| confirmed-scenarios.md 路径 | `grep "confirmed-scenarios.md" docs/ptm-tde/*.md` | 所有结果路径前缀为 `kym/scenarios/` |
| factor-usage 路径 | `grep "factor-usage" docs/ptm-tde/*.md` | 所有结果路径前缀为 `mfq/` |

---

## 7. 回滚方案

| 回滚方式 | 操作 |
|----------|------|
| git revert | `git revert <commit-hash>`，将 5 个文档恢复到改造前状态 |
| 手动回退 | 从 git 历史中提取 5 个旧版文件覆盖 |
| 部分回退 | 若仅某个文档有问题，单文件 revert |

**回退影响**：
- 5 个文档互不依赖，可独立回退
- 回退 STORY-010-05 后，若 STORY-010-06 已完成，其索引和需求文件中的新框架引用会失去文档支撑——两者宜同步回退

---

## 8. tier（复杂度）

**tier = M**

判定依据：
- 文件数：5 个
- 变更行数：合计约 ±300 行
- 变更类型：文档描述层更新，不涉及逻辑实现
- 风险：中（需确保跨文档一致性，防止路径引用遗漏）

---

## 9. shared_fragments（共享片段引用）

| 片段 | 来源 | 用途 |
|------|------|------|
| 三阶段框架总览文本 | `agents/ptm-tde.md`（本 CR STORY-010-02 产物） | README §3、USER-MANUAL 工作流路径 |
| CP↔Gate 映射表 | `docs/ptm-tde/gate-spec.md` | README §3 |
| 目录迁移表 | `process/HLD-CR-010.md` §8.2 | runtime-artifacts.md、README §7 |
| Skill 阶段归属 | `agents/ptm-tde.md` §Skill 触发词映射 | skill-references.md、component-manual.md |

---

## 10. open_items（待确认项）

| ID | 问题 | 状态 | 说明 |
|----|------|------|------|
| O-05-01 | README.md §4 中是否需要保留旧 CP02/CP09/CP11 的详细检查清单内容（当前各约 20 行），还是改为引用 `gate-spec.md` 的简要摘要？ | OPEN | 推荐改为引用 `gate-spec.md` 路径 + 简要摘要，避免两份内容不同步。若保留详细清单则需同步维护 `gate-spec.md` 和 README.md 两处。 |
| O-05-02 | USER-MANUAL.md §4.4 Topology Modeling 中的 `analysis/scenarios/<scene-id>/` 路径，是否改为 `kym/scenarios/<scene-id>/`？ | OPEN | 推荐改为新路径以保持一致，原路径不存在新目录结构中。 |
| O-05-03 | USER-MANUAL.md §12 近期变更同步中引用的旧路径（`analysis/scenarios/`）是否需要更新？ | OPEN | 推荐更新为新路径，因为是当前版本的使用文档，不是历史记录。若需保留历史语境，则加 `（v3 旧路径）` 标注。 |

---

## 11. 验证 checklist

- [ ] README.md§3 包含三阶段表格 + CP↔Gate 映射表
- [ ] README.md§4 三个 Gate 确认点完整，GATE-3 标注为新增
- [ ] README.md§7 文件结构树使用新目录
- [ ] USER-MANUAL.md§3.3 目录规则使用新路径
- [ ] USER-MANUAL.md 全部路径引用使用新路径
- [ ] runtime-artifacts.md 目录树完全替换，12 个子目录全部存在
- [ ] runtime-artifacts.md 分析产物表目录列全部更新为新路径
- [ ] runtime-artifacts.md 设计产物和交付产物路径全部更新
- [ ] component-manual.md 主流程表更新为三阶段 + Gate
- [ ] skill-references.md 阶段列全部更新为 KYM / MFQ / PPDCS
- [ ] 全 5 个文档无旧 CP 编号作为主引用（CP↔Gate 映射表除外）
- [ ] 全 5 个文档 `confirmed-scenarios.md` 路径一致为 `kym/scenarios/confirmed-scenarios.md`
- [ ] 全 5 个文档 `factor-usage` 路径前缀一致为 `mfq/`

---

## 12. 依赖与门控

| 依赖项 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| STORY-010-02 | contract | pending | 主 Agent 框架重写完成后，5 个文档中的三阶段框架描述、Gate 命名、阶段归属、目录结构才能与主 Agent 保持一致 |
| STORY-010-01 | contract | done | `gate-spec.md` Gate 编号和命名已冻结，文档引用遵循 |

---

## 13. DEV-LOG 预留

实现时在此记录：
- 每个文件变更的章节和行号
- 跨文档一致性的验证结果
- 意外发现的旧路径引用

---

## 14. Gotchas

1. **README.md 中有历史章节引用 `analysis/` 路径**：§8 近期变更同步中的 CR-20260520-001 和 CR-20260521-001 小节引用旧路径——这些是历史记录，不是当前工作流说明。有两种处理方式：(a) 同步更新为新路径（推荐），(b) 保留旧路径并标注 `（v3旧路径）`。推荐 (a)，因为 README 是当前交付文档不是历史档案。

2. **`ppdcs/ppdcs/` 双重目录名**：新目录结构中 `ppdcs/ppdcs/`（阶段目录/子目录）与旧 `design/ppdcs/` 不同——前者是 `ppdcs` 阶段目录下的 `ppdcs` 子目录，容易混淆。文档中需明确说明：`ppdcs/` 是阶段级目录，`ppdcs/ppdcs/` 是 PPDCS 设计过程文件目录。

3. **USER-MANUAL.md §8 工作流典型路径**：Simple/Standard/Complex 路径中的 Agent → 用户交互流程未改变，但若其中引用了 CP 编号则需要更新。当前检查：Simple 路径中无 CP 编号引用，Standard/Complex 路径中也无——无需变更，但需要验证。

4. **runtime-artifacts.md 的 `process/plan/` 与整体目录**：`process/plan/` 是目录树中唯一不与阶段同名的顶级目录。在表格"分析产物"中需要单独列为跨阶段边界产物，并在阶段列标注"跨阶段边界"而非 MFQ。

5. **skill-references.md 中 `checkpoint-manager` 的阶段归属**：该 Skill 从 `checkpoint` 阶段改为 `KYM` 阶段（因为 GATE-1 和 GATE-2 都在 KYM 阶段范围内触发）。但 `checkpoint-manager` 实际是共享工具，在 MFQ 阶段内滚动自检和 PPDCS 阶段也会被调用。skill-references.md 将其列在 KYM 行下是为了表示"首次出现在 KYM 入口"，但需在职责描述中说明它也在后续阶段被调用。

---

## 补充章节：Requirements（Functional / Non-Functional）

> 本部分补全 meta-dev LLD 规范要求的章节，内容来自 CR-010 与 HLD-CR-010。

### Functional Requirements

| # | 需求 | 来源 |
|---|------|------|
| FR-05-01 | README.md §3 从「11 步主流程」改为「三阶段框架」+ CP↔Gate 映射表；§4 从「人工检查点（3 类）」改为「Gate 检查点（3 类）」含 GATE-3 新增内容；§7 目录树替换为新结构 | CR-010 §实施步骤 1,2,4 |
| FR-05-02 | USER-MANUAL.md 角色说明中 CP 引用改为 Gate；§3.3 目录树 + 强约束更新；公共因子库、拓扑绑定路径全部更新为新路径 | CR-010 §目录结构迁移 |
| FR-05-03 | runtime-artifacts.md 目录树完全替换；分析/设计/交付产物表中的所有路径更新为新路径（12 个子目录） | CR-010 §目录结构迁移 |
| FR-05-04 | component-manual.md 主流程表从 11 步改为三阶段 + Gate；调用关系中的路径和 CP 编号更新 | CR-010 §实施步骤 3 |
| FR-05-05 | skill-references.md 主流程 Skill 表的阶段列更新为 KYM / MFQ / PPDCS；职责描述中路径引用同步更新 | CR-010 §Skill 归属 |
| FR-05-06 | 全部 5 个文档中 `analysis/` 和 `design/` 不作为主路径引用，使用一致的 Gate 编号和阶段名称 | CR-010 §文档一致性 |

### Non-Functional Requirements

- **跨文档一致性**：5 个文档中的 Gate 编号、阶段名称、`confirmed-scenarios.md` 路径、`factor-usage` 路径必须完全一致
- **可维护性**：所有文档中 Gate 确认点的详细内容引用 `gate-spec.md` 而非重复维护
- **向后兼容**：CP↔Gate 映射表保留作为历史参考，不删除旧 CP 知识

---

## 补充章节：模块拆分与职责

本 Story 修改 5 个文档，不涉及模块拆分。各文档的变更职责：

| 文档 | 变更职责 |
|------|----------|
| `docs/ptm-tde/README.md` | 6 处变更：TOC、架构图、§3 主流程→三阶段、§4 CP→Gate 确认点（含 GATE-3 新增）、§7 目录树、§8 历史路径 |
| `docs/ptm-tde/USER-MANUAL.md` | 5 处变更：角色说明、§3.3 目录规则、公共因子库路径（2 处）、拓扑绑定路径 |
| `docs/ptm-tde/runtime-artifacts.md` | 6 处变更：目录树、公共因子库路径、场景产物路径、分析产物表、设计产物路径、交付产物路径 |
| `docs/ptm-tde/component-manual.md` | 3 处变更：主流程表、使用边界路径、调用关系表 |
| `docs/ptm-tde/skill-references.md` | 1 处变更：主流程 Skill 表阶段列 + 职责描述路径 |

---

## 补充章节：数据模型与持久化设计

本 Story 为纯文档更新，不涉及数据模型或持久化存储。所有变更均为 Markdown 文本中的路径和术语替换。

---

## 补充章节：技术设计细节

- **路径替换策略**：采用逐文件、逐章节人工替换，不依赖全局搜索替换。每个旧路径引用（`analysis/`、`design/`、`delivery/`、`checkpoints/`、`doc/STATE.yaml`）根据上下文判断替换目标，避免误伤历史记录中的引用。
- **历史章节处理**：README.md §8 中的 CR-20260520-001 和 CR-20260521-001 引用旧路径——推荐同步更新为新路径（因为 README 是当前交付文档，非历史档案）。
- **`ppdcs/ppdcs/` 命名**：文档中需明确区分 `ppdcs/`（阶段目录）和 `ppdcs/ppdcs/`（设计过程文件目录），避免读者混淆。
- **GATE-3 新增内容**：GATE-3 在 README.md §4 中需要完整描述（检查项 + 确认项 + 通过条件），不能仅写占位符。

---

## 补充章节：安全与性能设计

本 Story 为纯文档改写，不涉及运行时代码变更，无安全风险或性能影响。

---

## 补充章节：实施步骤

| 步骤 | 操作 | 验证方式 |
|------|------|----------|
| 1 | 更新 README.md：§3 三阶段框架 + §4 Gate 确认点（含 GATE-3）+ §7 目录树 + TOC | `grep "11 步\|CP01\|CP09\|CP11"` 仅在映射表中出现 |
| 2 | 更新 USER-MANUAL.md：角色说明 + §3.3 目录树 + 全部路径引用 | `grep "analysis/factor-usage\|analysis/scenarios/confirmed-scenarios"` 返回 0 |
| 3 | 更新 runtime-artifacts.md：目录树 + 6 处路径引用 | 检查 12 个新目录全部出现在树中 |
| 4 | 更新 component-manual.md：主流程表 + 调用关系 | 检查阶段列取值 KYM / MFQ / PPDCS |
| 5 | 更新 skill-references.md：阶段列 + 职责描述路径 | 对比 agents/ptm-tde.md 的 Skill 阶段归属一致性 |
| 6 | 跨文档一致性验证 | 全 5 个文档的 Gate 编号、阶段名称、路径引用一致性检查 |

---

## 补充章节：风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 |
|-------------|------|----------|
| README.md §8 历史章节旧路径 | 低 — 历史记录中 `analysis/` 引用与新目录不一致 | 推荐同步更新为新路径，或显式标注 `（v3旧路径）` |
| 跨文档路径遗漏 | 中 — 5 个文档中的路径引用分散，容易遗漏某处旧引用 | 验证脚本逐文件 grep；跨文档一致性测试逐项检查 |
| `ppdcs/ppdcs/` 混淆 | 低 — 双重目录名可能让读者困惑 | 文档中显式注释区分阶段目录和子目录 |
| GATE-3 新增内容描述不充分 | 中 — 若 README §4 中 GATE-3 只有占位符，用户无法理解确认内容 | 从 gate-spec.md 提取 Checklist + 确认项摘要
