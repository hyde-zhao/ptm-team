# MFQ&PPDCS 测试用例设计工具（ptm-tde）v3

> **理论基础**：《海盗派测试分析: MFQ&PPDCS》（邰晓梅著，ISBN 978-7-115-44415-8）
> **首版试点**：华为防火墙（TGFW/NGFW）
> **组件定位**：ptm-team 体系中的测试设计组件
> **安装说明**：平台安装、投影和升级由 ptm-team 统一控制，ptm-tde 仅维护 Agent / Skill 调用关系与运行产物契约

---

## 目录

1. [工具简介](#1-工具简介)
2. [实现原理](#2-实现原理)
   - [MFQ 三维分析框架](#21-mfq-三维分析框架)
   - [PPDCS 五特征建模](#22-ppdcs-五特征建模)
   - [CAE 三元组数据模型](#23-cae-三元组数据模型)
   - [追踪链与覆盖机制](#24-追踪链与覆盖机制)
   - [系统架构](#25-系统架构)
3. [11 步主流程](#3-11-步主流程)
4. [人工检查点（3 类）](#4-人工检查点3-类)
5. [五种 PPDCS 设计方法](#5-五种-ppdcs-设计方法)
6. [快速开始](#6-快速开始)
7. [文件结构](#7-文件结构)

---

## 1. 工具简介

`ptm-tde`（Product Test Method - Test Design Engine）是一套基于 **MFQ&PPDCS** 方法论的测试用例设计 Agent，帮助测试工程师从特性需求文件出发，经过系统化分析，输出完整的测试方案和测试用例。

### 核心能力

| 能力 | 说明 |
|------|------|
| 📋 **结构化需求解析** | 支持 Markdown / Word / Excel / PDF，提取 SR 编号/模块/描述字段 |
| 🔍 **M 分析（单功能）** | PPDCS 特征标注 + CAE 三元组测试点 |
| 🔗 **F 分析（耦合）** | Excel 批注读写（522 条已验证）+ 内存图模型 |
| 📊 **Q 分析（质量）** | HTSM 维度评估 + CAE 格式质量测试点 |
| 🧪 **五种设计方法** | P/P/D/C/S 各方法五步专化流程，Pairwise 工具自动检测 |
| ✅ **双层覆盖验证** | SR→TP→LC（需求层）+ TP→PC（测试点层）自动检查 |
| 🔄 **变更增量分析** | 仅影响相关模块，不修改无关用例 |
| 🐛 **问题单回溯** | 定位覆盖盲区、输出流程优化建议 |

---

## 2. 实现原理

### 2.1 MFQ 三维分析框架

```
      特性需求文件
          │
    ┌─────▼─────┐
    │  M 分析   │  Model-based Discrete Function
    │           │  ─ 将特性拆分为独立可测的单功能
    │ PPDCS标注 │  ─ 为每个单功能标注 PPDCS 主特征
    │ CAE测试点 │  ─ 用 CAE 三元组表达测试点
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  F 分析   │  Function Interaction
    │           │  ─ 三源合并：Excel批注 + 场景耦合 + 代码依赖
    │ 耦合图模型│  ─ 内存图模型：nodes=模块, edges=耦合关系
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  Q 分析   │  Quality Characteristics
    │           │  ─ HTSM 维度评估（功能/安全/可靠/性能等）
    │ CAE质量点 │  ─ 仅对相关维度展开分析
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  整合层   │  三源测试点 → CAE 聚合 → 逻辑用例
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │  设计层   │  PPDCS五方法 → 五步专化流程 → 物理用例
    └───────────┘
```

### 2.2 PPDCS 五特征建模

PPDCS 是 M 分析中用于匹配测试设计技术的五种建模特征：

| 特征 | 含义 | 识别关键词 | 推荐设计技术 |
|------|------|-----------|------------|
| **P-Process** | 多步骤有序流程，不可回退 | 先...再...、流程、步骤 | 流程图/活动图 |
| **P-Parameter** | 参数间有确定性业务规则 | 当...且...则...、规则 | 判定表/因果图 |
| **D-Data** | 数据有取值范围，各项独立 | 取值范围、有效值、最大最小 | 等价类+边界值 |
| **C-Combination** | 多因子多状态，需组合压缩 | 组合、配置项、矩阵 | Pairwise/正交阵列 |
| **S-State** | 对象多状态可双向迁移 | 启用/禁用、状态、生命周期 | 状态图/转换表 |

**特征区分决策树**：

```
被测功能有多状态且可回退？
  是 → S-State
  否 ↓
有多步骤且顺序固定（不可回退）？
  是 → P-Process
  否 ↓
参数间有确定性业务规则？
  是 → P-Parameter
  否 ↓
多因子需要交叉组合验证？
  是 → C-Combination
  否 → D-Data（独立数据项验证）
```

### 2.3 CAE 三元组数据模型

v3 核心升级：所有测试点（TP）统一使用 **CAE 三元组**结构化表达：

```
TP-M-001:
  C（Condition）: 防火墙已启动，日志服务器处于"已配置"状态，IP=<IP_ADDRESS>
  A（Action）:    启用日志服务器（点击"启用"按钮）
  E（Effect）:    日志服务器状态变为"已启用"，系统日志记录操作记录
```

| 字段 | 含义 | 约束 |
|------|------|------|
| **C（Condition）** | 可验证的前置状态/边界条件/环境约束 | 禁止"正常情况下"等模糊表述 |
| **A（Action）** | 可执行的测试操作（操作对象+内容） | 不得写成"验证..."等描述性文字 |
| **E（Effect）** | 可观测的系统响应（含观测点+期望值） | 不确定时可写"待定"并标注原因 |

**CAE 三元组的价值**：
- 聚合基础：判断多个 TP 能否合并为一个逻辑用例（LC）
- 推断基础：从 CAE 结构自动推断 PPDCS 特征
- 追踪基础：形成完整可追溯的测试链路

### 2.4 追踪链与覆盖机制

```
SR（系统需求）
  └─► TP(C/A/E)（测试点，CAE 三元组）
        └─► LC（逻辑用例，含因子表+路径+数据）
              └─► 组合方案（Pairwise/判定表/路径组合）
                    └─► PC（物理用例，16列标准格式）
```

**CAE 聚合规则**（三种，按优先级排序）：

| 规则 | 优先级 | 触发条件 | 合并逻辑 |
|------|--------|---------|---------|
| 规则3-步骤序列 | 1（最高） | A 动作间有执行顺序依赖 | 合并为一个有序步骤序列 LC |
| 规则2-状态变体 | 2 | 相同 A，C 为同对象不同前置状态 | 合并为状态枚举 LC |
| 规则1-参数化 | 3 | 相同 A，C 为同参数不同取值 | 合并为参数化 LC，数据集扩展 |
| 规则0-直接 | 4（最低） | 无匹配聚合规则 | 独立 LC，直接输出 |

### 2.5 系统架构

```
┌────────────────────────────────────────────────────────────┐
│                     ptm-tde Agent                          │
│              （11步状态机 + 2扩展分支）                       │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  Input   │ Scenario │ M/F/Q    │  PPDCS   │   Delivery     │
│  Layer   │          │ Analysis │  Design  │                │
├──────────┴──────────┴──────────┴──────────┴────────────────┤
│                      17 Skills                             │
│  feature-parser · scenario-discovery · m-analyzer          │
│  f-analyzer · q-analyzer · test-point-integrator           │
│  design-planner                                            │
│  process-design · parameter-design · data-design           │
│  combination-design · state-design                         │
│  coverage-verifier · deliverable-renderer · case-retriever │
│  change-impact-analyzer · bug-gap-analyzer                 │
├────────────────────────────────────────────────────────────┤
│                   2 Python 工具                             │
│  excel_coupling_tool.py      mcp_query_client.py           │
└────────────────────────────────────────────────────────────┘
```

**CAE→PPDCS 推断规则（12条）**：

| 推断维度 | 规则 | 触发条件 | 推断特征 |
|---------|------|---------|---------|
| A 模式（主权重，5条） | A1 | A 动作含"步骤顺序"关键词 | P-Process |
|  | A2 | A 动作含"切换/迁移状态"关键词 | S-State |
|  | A3 | A 动作含"配置参数值" | P-Parameter 或 D-Data |
|  | A4 | A 含多个因子取值组合 | C-Combination |
|  | A5 | A 含单独数据输入验证 | D-Data |
| C 模式（强信号，4条） | C1 | C 含多个前置状态条件 | S-State |
|  | C2 | C 含 IF...THEN... 规则 | P-Parameter |
|  | C3 | C 含因子数 ≥ 3 | C-Combination |
|  | C4 | C 含数值范围约束 | D-Data |
| E 模式（辅助，3条） | E1 | E 含状态迁移结果 | S-State 印证 |
|  | E2 | E 含规则判定结果 | P-Parameter 印证 |
|  | E3 | E 含数值验证结果 | D-Data 印证 |

---

## 3. 11 步主流程

```
步骤  阶段         描述                                  关键 Skill
───────────────────────────────────────────────────────────────────
 1.  input         CP01自检 + 特性文件解析 + 三~五级目录生成     checkpoint-manager + feature-parser
 2.  scenario      场景再发现 + Topology + atomic-ops + CP02自检/确认  scenario-discovery
 3.  m-analysis    单功能拆分 + PPDCS标注 + CAE测试点           m-analyzer
 4.  f-analysis    耦合分析（三源合并）+ CAE耦合测试点           f-analyzer
 5.  q-analysis    质量属性分析 + CAE质量测试点                 q-analyzer
 6.  integration   M+F+Q CAE聚合 → 逻辑用例(LC)                test-point-integrator
 7.  plan          CAE→PPDCS推断 + 设计方法匹配                 design-planner
 8.  design-ppdcs  每LC输出PPDCS逻辑设计过程文件                 design-ppdcs-analyzer + 5 design Skills
 9.  design-pc     每LC输出物理用例文件                         5 design Skills
10.  coverage      双层覆盖率验证 + CP11确认                    coverage-verifier
11.  delivery      交付物生成（测试方案 + 测试用例总表）          deliverable-renderer
```

**扩展分支**：

- **需求变更**：`change-impact-analyzer` → 增量 MFQ → 增量设计 → 增量覆盖
- **问题单分析**：`bug-gap-analyzer` → 盲区定位 → 用例补充 → 流程优化

---

## 4. 人工检查点（3 类）

> **重要**：工具只在以下 3 个关键节点暂停并等待人工确认，未通过确认不会自动推进。

### ① CP02：目录结构与场景自检/确认（步骤 2 结束后）

**触发时机**：`scenario-discovery` 完成应用场景分析后  
**自动自检内容**：

| 自检项 | 说明 |
|-------|------|
| 输入类型识别 | 是否区分 raw requirement / functional scenario seed / deployment draft / confirmed artifact |
| 场景再发现 | functional seed 是否经过头脑风暴、归并、拆分和范围收敛 |
| Seed-to-Scenario Mapping | 每个 seed 是否映射到部署型场景、排除项或确认缺口 |
| Topology Catalog | 是否读取 TGFW 组网集合并为每个依赖组网场景绑定 `topology_ref` |
| atomic-ops | `action_source_ref` 是否直接引用 atomic-ops `op_id`，REST API / CLI / tool-method 是否只作为底层契约 |
| 缺口分类 | `confirmation_gaps` 是否区分必须先确认与可下传缺口 |

**需要人工确认的内容**：

| 确认项 | 说明 |
|-------|------|
| 目录结构 | 三级/四级/五级目录划分是否正确 |
| 场景完整性 | 部署、扩容、维护、可靠性、性能、易用性、配置顺序、异常路径是否覆盖你关心的使用方式 |
| Seed-to-Scenario Mapping | 功能初稿如何重构为部署型场景是否可接受 |
| Scenario Chain | 每个场景的原子操作、观察点、最小逻辑链是否准确 |
| Topology | 防火墙 topo、设备/端口/链路是否正确 |
| atomic-ops | atomic-ops `op_id`、能力状态和调用/观测契约是否正确 |
| 遗漏场景 | 是否有未列出的重要场景需要补充 |

**通过后**：进入 m-analysis（步骤 3）

---

### ② CP09：PPDCS 逻辑设计确认（步骤 8 结束后）

**触发时机**：`design-ppdcs-analyzer` 为每个 LC 生成 `design/ppdcs/*.md` 后
**需要确认的内容**：

| 确认项 | 说明 |
|-------|------|
| PPDCS 推断结果 | 各逻辑用例的 PPDCS 特征是否正确 |
| 推荐设计方法 | 推荐的设计技术是否适合该功能的特点 |
| 逻辑步骤 | LC 的测试逻辑步骤、分支、状态或规则是否正确 |
| 数据设计 | 数据对象、因子取值、组合结果是否正确 |

**输出**：`design/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`

---

### ③ CP11：覆盖率确认（步骤 10 完成后）

**触发时机**：`coverage-verifier` 生成覆盖报告后
**需要确认的内容**：

| 确认项 | 说明 |
|-------|------|
| 双层覆盖率 | 需求覆盖率 = 100%；测试点覆盖率 = 100% |
| CAE 追踪链完整 | SR→TP(C/A/E)→LC→组合方案→PC 链路无断点 |
| 未覆盖项 | 所有 gap 均已显式列出并可回链 |

**通过后**：进入 delivery，生成最终测试方案与测试用例总表

---

## 5. 五种 PPDCS 设计方法

每种方法均遵循**五步设计过程**：

```
步骤1: 测试数据（因子-取值表补全 + 等价类细化）
步骤2: 方法专化分析（各方法不同，见下表）
步骤3: 数据/路径组合分析
步骤4: 实际取值/触发数据分配
步骤5: 物理用例输出（16列标准格式）
```

### 各方法步骤2专化内容

| 方法 | 步骤2 专化内容 | 核心输出 |
|------|--------------|---------|
| **P-Process**（流程） | Mermaid flowchart + **分支路径枚举表**（路径ID/分支序列/覆盖功能节点/路径类型） | 路径枚举表 |
| **P-Parameter**（参数） | **约束提取+规则组合矩阵**（互斥/包含/蕴含/与/或）+ 冗余规则合并 + 因果图（可选） | 规则组合矩阵 |
| **D-Data**（数据） | **等价类隔离+边界值三点法**（上点/离点/内点）+ Data vs Combination 决策提示 | 等价类表+三点边界 |
| **C-Combination**（组合） | **PICT 工具检测**（可用→`pict_wrapper.py`；不可用→手动 Pairwise）+ PICT 模型文件 | Pairwise 组合表 |
| **S-State**（状态） | Mermaid stateDiagram + 状态转换表 + **状态路径枚举表**（含守卫条件列） | 状态路径枚举表 |

### 步骤4 分配内容对比

| 方法 | 步骤4 输出 |
|------|-----------|
| P-Process | 路径触发数据分配（前置条件 + 触发输入 + 预期结果） |
| P-Parameter | 规则触发参数组分配（有效值 + 边界值 + 拒绝验证值） |
| D-Data | 三类数据分配（有效等价类/无效等价类/边界值） |
| C-Combination | 因子实际取值分配（具体业务值，非抽象等价类标签） |
| S-State | 迁移触发事件+数据分配（事件序列 + 配套数据 + 守卫条件验证） |

---

## 6. 快速开始

### 安装

ptm-tde 后续作为 ptm-team 的组件交付，安装、平台投影、升级和卸载由 ptm-team 工具统一控制。ptm-tde 仓库只维护 Agent、Skill、运行产物契约和组件级说明，不再在 README 中提供独立安装命令。

建议一个特性一个项目，例如：

```text
/home/hyde/projects/ptm-work/<feature-slug>/
```

### 基本用法

**启动测试设计**：

```
@ptm-tde 分析特性 "日志中心-日志服务器"
```

**提供需求文件**：

```
@ptm-tde 读取需求文件 input/日志中心特性需求.md
```

**触发需求变更分析**：

```
@ptm-tde 需求变更：日志服务器新增支持 TLS 1.3，变更文件 input/CR-2025-08.md
```

**分析问题单**：

```
@ptm-tde 问题单分析：input/DEFECT-1234.md
```

---

## 7. 文件结构

### 工作目录

```
<project-root>/
├── input/                       # 用户输入（原始材料，只读）
│   ├── <特性需求>.md
│   ├── <防火墙topo>.yaml
│   ├── <耦合矩阵>.xlsx
│   └── ...
│
├── analysis/                    # ptm-tde 生成的分析过程
│   ├── feature-input/           # 解析后结构化需求 + 目录
    ├── scenarios/               # 确认后的应用场景（三层结构）
    ├── m-analysis/
    │   ├── test-points.md       # M 测试点（CAE 三元组）
    │   └── ppdcs-annotation.md  # PPDCS 特征标注表
    ├── f-analysis/              # 耦合图模型 + 耦合测试点
    ├── q-analysis/              # 质量属性测试点（CAE 格式）
    ├── integration/
    │   ├── all-test-points.md   # M+F+Q 汇总（CAE 格式）
    │   ├── logic-cases.md       # 逻辑用例（含聚合规则标注）
    │   └── design-plan.md       # 设计计划（含 PPDCS 特征+推断主信号）
    ├── plan/
    │   └── design-planner-reasoning.md  # PPDCS 推断详细路径
    └── coverage/
├── design/
│   ├── ppdcs/
│   │   └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
│   └── pc/
│       └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
├── checkpoints/
├── delivery/
│   ├── <特性名>特性测试方案.md
│   └── <特性名>特性测试用例.md
└── doc/
    └── STATE.yaml
```

### 组件归档结构

```
ptm-tde/
├── agents/
│   └── ptm-tde.md
├── skills/
│   ├── checkpoint-manager/
│   ├── design-ppdcs-analyzer/
│   └── <skill-name>/
├── docs/
│   ├── component-manual.md
│   ├── runtime-artifacts.md
│   └── checkpoint-spec.md
└── README.md
```

---

*文档版本：v3.0 | 生成时间：2026-04-16 | 理论基础：MFQ&PPDCS（邰晓梅著）*
