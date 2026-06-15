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
   - [测试因子、拓扑角色与真实组网对象分层](#26-测试因子拓扑角色与真实组网对象分层)
3. [三阶段框架](#3-三阶段框架)
4. [Gate 检查点（3 类）](#4-gate-检查点3-类)
5. [五种 PPDCS 设计方法](#5-五种-ppdcs-设计方法)
6. [快速开始](#6-快速开始)
7. [文件结构](#7-文件结构)
8. [近期变更同步](#8-近期变更同步)

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
  └─► TP(C/A/E + topology_role_refs)（测试点）
        └─► LC（逻辑用例，含因子表+topology_bindings+路径+数据）
              └─► 组合方案（Pairwise/判定表/路径组合/拓扑绑定）
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
│           （三阶段框架 + 入口/出口门控）                        │
├───────────────┬──────────────────┬──────────────────────┤
│  KYM Phase    │  MFQ Phase       │  PPDCS Phase         │
│  (输入解析+场景) │  (M/F/Q/整合/计划) │  (设计+PC+覆盖+交付)   │
├──────────┴──────────┴──────────┴──────────┴────────────────┤
│                      19 Skills                             │
│  checkpoint-manager · feature-parser                       │
│  scenario-discovery · m-analyzer                           │
│  f-analyzer · q-analyzer · test-point-integrator           │
│  design-planner · design-ppdcs-analyzer                    │
│  process-design · parameter-design · data-design           │
│  combination-design · state-design                         │
│  coverage-verifier · deliverable-renderer · case-retriever │
│  change-impact-analyzer · bug-gap-analyzer                 │
├────────────────────────────────────────────────────────────┤
│                   2 Public Resources                       │
│  factor-library: common-network · ngfw-policy-routing      │
└────────────────────────────────────────────────────────────┘
```

### 2.6 测试因子、拓扑角色与真实组网对象分层

CR-20260521-001 明确要求 `ptm-tde` 区分三类对象，防止把真实端口误写为公共因子：

| 层 | 说明 | 示例 | 运行字段 |
|---|---|---|---|
| 测试因子 | 可跨项目复用的测试变量、值域、样本和约束 | 接口类型、接口能力、流量匹配状态、规则源 IP 合法性 | `factor_id`, `sample_id`, `factor_bindings` |
| 拓扑角色 | CAE 测试逻辑中的抽象位置或职责 | client、server、dut-ingress、dut-egress | `topology_role_refs`, `topology_role` |
| 真实组网对象 | 已确认场景中的设备、端口、链路实例 | `DUT.port1`, `TG.port1`, `LINK-WAN-01` | `topology_bindings`, `device_id`, `port_id`, `link_id`, `source`, `fact_status` |

并行链路：

```text
factor_refs -> factor_bindings -> factor materialization
topology_role_refs -> topology_bindings -> PC materialization
```

执行约束：

- CAE 负责表达测试逻辑和拓扑角色，不承载真实端口。
- `test-point-integrator` 从 `kym/scenarios/confirmed-scenarios.md` 绑定真实组网对象并写入 LC `topology_bindings`。
- PPDCS 和 PC 只消费 LC 绑定表；PC 中任何真实端口必须能回链到 `LC.topology_bindings -> confirmed-scenarios.md`。
- `coverage-verifier` 和 `deliverable-renderer` 必须保留 `topology_bindings / topology_role / source / fact_status`。
- `needs-confirmation` 的拓扑绑定不得因覆盖统计或交付渲染被提升为 `confirmed`。

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

---

## 4. Gate 检查点（3 类）

> **重要**：工具在以下 3 个 Gate 暂停并等待人工确认，未通过确认不会自动推进。

### GATE-2 KYM Exit Gate（自检+人工）

**触发时机**：KYM 阶段（feature-parser + scenario-discovery）完成后
**自动自检内容**：

| 自检项 | 说明 |
|-------|------|
| 输入类型识别 | 是否区分 raw requirement / functional scenario seed / deployment draft / confirmed artifact |
| 场景再发现 | functional seed 是否经过头脑风暴、归并、拆分和范围收敛 |
| Seed-to-Scenario Mapping | 每个 seed 是否映射到部署型场景、排除项或确认缺口 |
| Topology Catalog | 是否读取 TGFW 组网集合并为每个依赖组网场景绑定 `topology_ref` |
| Topology Bindings | 真实端口是否来自已确认场景，并可回链到 `kym/scenarios/confirmed-scenarios.md` |
| atomic-ops | `action_source_ref` 是否直接引用 atomic-ops `op_id`，REST API / CLI / tool-method 是否只作为底层契约 |
| Operation Path | `normal_path` 是否包含大步骤、子步骤、必要性枚举和选择组约束；每个步骤是否有可回链 `action_source_refs` 的原子操作 |
| Abnormal Path | `abnormal_path` 是否通过 `related_normal_steps` 追溯到正常路径步骤或说明异常来源；每个异常步骤是否有可回链 `action_source_refs` 的原子操作 |
| 新增原子操作候选 | 场景阶段发现的新 atomic-op 是否在 GATE-2 发起时显式展示并等待用户确认 |
| Minimal Logic Chain | 是否保留可选步骤和 `至少选择一项` 选择语义，未误写成线性必做链路 |
| 缺口分类 | `confirmation_gaps` 是否区分必须先确认与可下传缺口 |

**需要人工确认的内容**：

| 确认项 | 说明 |
|-------|------|
| 目录结构 | 三级/四级/五级目录划分是否正确 |
| 场景完整性 | 部署、扩容、维护、可靠性、性能、易用性、配置顺序、异常路径是否覆盖你关心的使用方式 |
| Seed-to-Scenario Mapping | 功能初稿如何重构为部署型场景是否可接受 |
| Scenario Chain | 每个场景的原子操作、观察点、最小逻辑链是否准确 |
| Operation Path | 正常路径的大步骤、子步骤、必要性和选择组是否符合真实操作流程 |
| Topology | 防火墙 topo、设备/端口/链路是否正确 |
| atomic-ops | 每个正常/异常步骤的 atomic-ops `op_id`、能力状态和调用/观测契约是否正确；新增候选是否接受、修改、复用已有或拒绝 |
| 遗漏场景 | 是否有未列出的重要场景需要补充 |

**通过后**：进入 MFQ 阶段

---

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
| 候选确认状态 | 候选测试因子和候选原子操作存在时，`mfq/candidates/` 汇总文件必须记录用户确认结果 |

**需要人工确认**：

| 确认项 | 说明 |
|-------|------|
| M/F/Q 分析质量 | 各维度分析是否覆盖完整 |
| LC 整合一致性 | 测试点归集、因子绑定和拓扑绑定是否一致 |
| 设计计划 | CAE→PPDCS 推断是否合理 |
| 公共因子消费 | 因子库 lock 和候选提案是否合理 |
| 候选测试因子 / 原子操作 | 候选汇总表是否已展示给用户，逐项 `decision=confirmed/rejected/modified` 是否符合预期 |

**通过后**：进入 PPDCS 阶段

---

### GATE-4 PPDCS Exit Gate（自检+人工）

**触发时机**：PPDCS 阶段（设计+覆盖验证）完成后
**需要确认的内容**：

| 确认项 | 说明 |
|-------|------|
| PPDCS 推断结果 | 各逻辑用例的 PPDCS 特征是否正确 |
| 推荐设计方法 | 推荐的设计技术是否适合该功能的特点 |
| 逻辑步骤 | LC 的测试逻辑步骤、分支、状态或规则是否正确 |
| 数据设计 | 数据对象、因子取值、组合结果是否正确 |
| 双层覆盖率 | 需求覆盖率 = 100%；测试点覆盖率 = 100% |
| CAE 追踪链完整 | SR→TP(C/A/E)→LC→组合方案→PC 链路无断点 |
| PC 步骤契约 | 每条 PC 包含 `case_steps`；每一步同时包含步骤名称、执行对象、`atomic_op.op_id` 和预期结果；op_id 回链 `action_source_refs` |
| 16 列表格稳定性 | PC 与交付测试用例表头等于标准 16 列，所有数据行恰好 16 列，`测试步骤*` 单元格包含 `原子操作：<op_id>` |
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
步骤5: 物理用例输出（结构化 `case_steps` + 标准 16 列渲染）
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

ptm-tde 后续作为 ptm-team 的组件交付，安装、平台投影、升级和卸载由 ptm-team 工具统一控制。ptm-tde 仓库只维护 Agent、Skill、运行产物契约和组件级说明。

常用安装与漂移检查命令：

```bash
uv run python script/install.py install codex --agent ptm-tde
uv run python script/install.py install claude --agent ptm-tde
uv run python script/install.py check codex --agent ptm-tde
uv run python script/install.py check claude --agent ptm-tde
```

安装 `ptm-tde` agent 时，安装器还会写入平台规则托管块：

| 平台 | 规则文件 | 行为 |
|---|---|---|
| Codex | `AGENTS.md` | 文件不存在则创建；存在则追加或替换 `ptm-tde-workflow` managed block |
| Claude Code | `CLAUDE.md` | 文件不存在则创建；存在则追加或替换 `ptm-tde-workflow` managed block |

`check <platform> --agent ptm-tde` 会读取 `.ptm-team-manifest.json`，检查 agent、skill、规则 managed block 和共享 resource 的 installed hash，并检查源仓库 hash 是否已变化；发现 `INSTALLED_DRIFT`、`SOURCE_DRIFT` 或 `MISSING` 时返回非 0，建议重新安装。

安装 `ptm-tde` agent 时，ptm-team 安装器会读取 `resource/component-resource-links.yaml`，同步安装关联公共因子库到用户级公共资源目录：

```text
~/.ptm-team/resource/factor-libraries/
```

可通过 `PTM_TEAM_RESOURCE_HOME` 覆盖资源根目录。公共因子库是仓库级 `resource/` 资产，后续可被其他 Agent / Skill 复用，不属于 ptm-tde 私有目录。

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
@ptm-tde 读取需求文件 .input/日志中心特性需求.md
```

**触发需求变更分析**：

```
@ptm-tde 需求变更：日志服务器新增支持 TLS 1.3，变更文件 .input/CR-2025-08.md
```

**分析问题单**：

```
@ptm-tde 问题单分析：.input/DEFECT-1234.md
```

---

## 7. 文件结构

### 工作目录

```
<project-root>/
├── .input/                       # 用户输入（原始材料，只读）
│   ├── <特性需求>.md
│   ├── <防火墙topo>.yaml
│   ├── <耦合矩阵>.xlsx
│   └── ...
│
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

公共因子库主库不保存在项目 `kym/` 或 `mfq/` 中；项目只在 `mfq/factor-usage/` 记录本次使用的库版本、因子绑定和候选回流建议。真实设备、真实端口和 link 实例不进入 `mfq/factor-usage/`，由 `kym/scenarios/confirmed-scenarios.md` 和 LC `topology_bindings` 承载。

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

仓库级公共资源结构：

```text
resource/
├── component-resource-links.yaml
└── factor-libraries/
    ├── index.yaml
    ├── common-network/
    └── ngfw-policy-routing/
```

---

## 8. 近期变更同步

本节增量同步 `process/changes/CR-20260520-001.md` 与 `process/changes/CR-20260521-001.md` 的已确认变更。原有流程、目录和交付说明继续保留，本节只补充当前生效口径。

### 8.1 CR-20260520-001：场景再发现与 Operation Path

`scenario-discovery` 已从“整理场景输入”升级为“场景再发现 + 部署型场景重构”：

- 输入文档会先识别为 `raw_requirement`、`functional_scenario_seed`、`deployment_scenario_draft` 或 `confirmed_scenario_artifact`。
- functional scenario seed 不能直接改写成最终场景，必须经过头脑风暴、归并、拆分、范围收敛和 Seed-to-Scenario Mapping。
- 场景输出采用 Scenario Details 与 ptm-tde Structured Supplement 双层结构，保留 Topology、atomic-ops、Knowledge Reference、Confirmation Gaps 和质量检查。
- atomic-ops 是唯一原子操作引用对象；REST API、CLI、tool-method 只能作为 atomic-op 的底层调用或观测契约。
- `action_source_refs` 直接引用 atomic-ops `op_id`，不再使用独立 source-action 对象。
- GATE-2 KYM Exit Gate 已扩展为 auto + manual：自动检查输入分类、再发现、Seed-to-Scenario Mapping、Topology Catalog、atomic-ops 唯一口径、Operation Path 和缺口分类；同时逐 `scenario_id` / 场景标题校验每条 confirmed scenario 的正常链和异常链。

Operation Path 是场景阶段的强契约：

| 字段 | 要求 |
|---|---|
| `normal_path` | 每个 confirmed scenario 均包含 `step_id / sub_step_ids / operation / necessity / description`；每个步骤都有 `action_source_ref(s)`、`atomic_op` 或 `op_id` |
| `necessity` | 只能使用 `必要 / 可选 / 至少选择一项` |
| 选择组 | 必须列出可选子步骤，并说明不能全部跳过的约束 |
| `abnormal_path` | 每个 confirmed scenario 均包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`；每个异常步骤都有 `action_source_ref(s)`、`atomic_op` 或 `op_id`；无异常路径时必须写明 N/A 理由 |
| `minimal_logic_chain` | 必须保留可选步骤和 `至少选择一项` 语义，不得改写成线性必做链路 |

策略路由类场景还必须拆分 `forwarding action` 与 `match dimensions`，避免把“配置策略路由”写成不可审计的大步骤。

### 8.2 CR-20260521-001：公共因子库 Resource

公共因子库已确认为 `ptm-team` 仓库级 resource，不属于单个特性项目，也不是 ptm-tde 私有资产。

| 项 | 当前口径 |
|---|---|
| canonical source | `resource/factor-libraries/` |
| 组件关联 | `resource/component-resource-links.yaml` |
| 默认安装位置 | `~/.ptm-team/resource/factor-libraries/` |
| 可覆盖变量 | `PTM_TEAM_RESOURCE_HOME` |
| 项目消费记录 | `mfq/factor-usage/` |

安装 `ptm-tde` agent 时，ptm-team 安装器同步安装关联 factor libraries；卸载时只移除当前项目内的 agent、skill 和规则 managed block，不删除用户级共享 resource。如需清理共享资源，应使用单独的显式资源清理流程。

项目内不保存公共因子库主库，只保存：

```text
mfq/factor-usage/
├── factor-library-lock.yaml
├── factor-bindings.md
├── candidate-factor-proposals.yaml
└── factor-resolution-report.md
```

ptm-tde 消费流程：

1. 读取公共资源目录和 `index.yaml`。
2. 根据用户指定、项目 lock 或领域选择公共库。
3. `m-analyzer` 在提取测试因子前先查公共库。
4. 命中 `active` 因子时复用；值域、样本、上下文或约束不足时生成扩展建议。
5. 未命中时写入 `candidate-factor-proposals.yaml`，不得直接修改公共主库。
6. 下游 Skill 消费 `factor_bindings`；`factor_refs` 只保留为兼容摘要。

公共因子库边界：

- 接口类型、接口能力、出口模式等可复用变量可以是公共因子。
- `DUT.port1`、`TG.port1`、`DUT.port1<->TG.port1` 等真实拓扑实例不是公共因子，不能写入公共因子 `values`、`sample_id` 或样例值。
- 真实组网对象通过 `topology_role_refs -> topology_bindings -> PC materialization` 单独流转。
- `topology_bindings` 不替代 `factor_bindings`；两者并行消费、分别校验。

因子库生产和更新采用公共资源治理闭环：

```text
来源采集 → 候选建模 → 去重归一 → 因子设计 → 评审激活 → 发布归档 → 安装同步 → 项目消费 → 候选回流
```

公共库生命周期：

```text
proposed → candidate → active
                    ↘ rejected
active → deprecated
```

删除公共因子默认禁止；历史引用通过 `deprecated` 与 change log 保留追溯。

---

*文档版本：v3.0 | 生成时间：2026-04-16 | 理论基础：MFQ&PPDCS（邰晓梅著）*
