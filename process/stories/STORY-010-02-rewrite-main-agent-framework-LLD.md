# LLD — STORY-010-02 重写主 Agent 框架部分

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-01 | meta-dev | 初始 LLD，定义 `agents/ptm-tde.md` 框架部分 7 处变更。 |
| 1.1 | 2026-06-01 | meta-dev | [P0-B1] 统一路径引用：将 §3.2 目录树、§3.3 确认点、§3.5 初始化流程、§4 接口、§5 异常处理、§6 测试方案、§10 open_items、§11 checklist 中所有 `doc/STATE.yaml`→`process/STATE.yaml`、`checkpoints/`→`process/checkpoints/`，`doc/` 目录创建→`process/checkpoints/`。gate-spec.md 同步完成对应修正。 |
| 1.2 | 2026-06-01 | meta-dev | [M1] 补全 meta-dev LLD 规范要求的 7 个缺失章节：Requirements (F/NF)、模块拆分与职责、数据模型与持久化设计、技术设计细节、安全与性能设计、实施步骤、风险/难点与预研建议。 |
| 1.3 | 2026-06-01 | meta-dev | [M5] STATE.yaml 设计补充 `current_step` 字段（步骤级粒度），与 `current_phase`（阶段级）互补，支持 MFQ 阶段中途中断后精确恢复。 |

---

## 1. 概述

将 `agents/ptm-tde.md` 的框架描述从 **11 步线性状态机 + 12 个 CP** 重写为 **三阶段框架 + 5 Gate** 体系。本 Story 只修改 Agent 的流程描述层（框架编排逻辑），不修改：
- Skill 的触发词映射指向（改为三阶段归属栏位）
- Skill 的调用逻辑或输入输出契约
- 18 个 Skill 的 SKILL.md 文件

**核心文件**：`agents/ptm-tde.md`（约 ±200 行框架部分）

---

## 2. 受影响文件清单

| 文件 | 变更类型 | 变更范围 |
|------|----------|----------|
| `agents/ptm-tde.md` | 框架重写 | 7 个章节（见 §3），其他章节保留不变 |

**不修改的章节**（保留原样）：
- `## 理论基础`（MFQ/PPDCS 方法论说明）
- `## CAE 三元组`
- `## 公共因子库`
- `## 测试因子、拓扑角色与真实组网对象分层`
- `## 目录层级规范`
- `## 物理用例字段规范`
- `## 交付物`
- `## 扩展分支`（内容保留，位置跟随流程描述）

---

## 3. 变更方案

### 3.1 变更 1：「状态机」→「三阶段框架」

**章节定位**：`## 状态机`（第 44-62 行）

**变更要点**：删除 11 步 ASCII 流程图和编号列表，替换为三阶段框架表格，保留追踪链声明。

**改前**（当前内容）：
```markdown
## 状态机

工具按以下 11 步主流程执行：

 ```
 # 追踪链：SR → TP(C/A/E) → LC → 组合方案 → PC（物理用例）

  1. input         CP01自检 + 特性文件解析 + 三~五级目录生成             [checkpoint-manager + feature-parser]
  2. scenario      场景再发现 + 操作路径建模 + Topology + atomic-ops + CP02自检/确认 [scenario-discovery + CP02]
  ...
 11. delivery      输出测试方案和测试用例总表                            [deliverable-renderer + CP12]
```
```

**改后**：
```markdown
## 三阶段框架

ptm-tde 按以下三阶段 + 入口/出口门控体系推进：

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

### 阶段与 Gate 总览

| 阶段 | 包含步骤 | 关键 Skill | 入口 Gate | 出口 Gate | 产物目录 |
|------|----------|-----------|-----------|-----------|----------|
| **KYM**（Know Your Mission） | feature-parser → scenario-discovery | `feature-parser`、`scenario-discovery` | GATE-1 Entry Gate（纯自检） | GATE-2 KYM Exit Gate（自检+人工） | `kym/feature-input/`、`kym/scenarios/` |
| **MFQ**（M/F/Q Analysis） | m-analyzer → f-analyzer → q-analyzer → test-point-integrator → design-planner | `m-analyzer`、`f-analyzer`、`q-analyzer`、`test-point-integrator`、`design-planner` | GATE-2（通过后进入） | GATE-3 MFQ Exit Gate（自检+人工） | `mfq/m-analysis/`、`mfq/f-analysis/`、`mfq/q-analysis/`、`mfq/integration/`、`mfq/factor-usage/`、`process/plan/` |
| **PPDCS**（Design & Delivery） | design-ppdcs-analyzer + 5设计Skill → PC → coverage-verifier → deliverable-renderer | `design-ppdcs-analyzer`、5设计Skill、`coverage-verifier`、`deliverable-renderer` | GATE-3（通过后进入） | GATE-4 PPDCS Exit Gate（自检+人工） | `ppdcs/ppdcs/`、`ppdcs/pc/`、`ppdcs/coverage/`、`ppdcs/delivery/` |

### Gate 门控总览

| Gate | 名称 | 类型 | 触发时机 | 产物 |
|------|------|------|----------|------|
| **GATE-1** | Entry Gate | 纯自检 | 项目启动时 | `process/checkpoints/GATE-1-Entry.md` |
| **GATE-2** | KYM Exit Gate | 自检 + 人工确认 | KYM 阶段完成后 | `process/checkpoints/GATE-2-KYM-Exit-auto.md` + `manual.md` |
| **GATE-3** | MFQ Exit Gate | 自检 + 人工确认 | MFQ 阶段完成后 | `process/checkpoints/GATE-3-MFQ-Exit-auto.md` + `manual.md` |
| **GATE-4** | PPDCS Exit Gate | 自检 + 人工确认 | PPDCS 阶段完成后 | `process/checkpoints/GATE-4-PPDCS-Exit-auto.md` + `manual.md` |
| **GATE-5** | Exit Gate | 纯自检 | GATE-4 通过后 | `process/checkpoints/GATE-5-Exit.md` |

### 阶段内滚动自检

MFQ 和 PPDCS 阶段的每个 Skill 完成后，主 Agent 触发 checkpoint-manager 执行阶段内滚动自检（对应旧 CP03-CP07 和 CP08/CP10 逻辑），写入 `process/checkpoints/` 或日志。自检项参照 `docs/ptm-tde/gate-spec.md` 中对应 Gate 的 Checklist。

### CP↔Gate 映射

| 旧 CP | 新体系 | 说明 |
|-------|--------|------|
| CP01 | GATE-1 Entry Gate | input 自检 |
| CP02 | GATE-2 KYM Exit Gate | 场景自检 + 人工确认 |
| CP03 | MFQ 阶段内滚动自检 | M 分析完整性 |
| CP04 | MFQ 阶段内滚动自检 | F 分析完整性 |
| CP05 | MFQ 阶段内滚动自检 | Q 分析完整性 |
| CP06 | MFQ 阶段内滚动自检 | 整合完整性 |
| CP07 | MFQ 阶段内滚动自检 | 设计计划完整性 |
| — | GATE-3 MFQ Exit Gate | 新增：MFQ 出口人工确认 |
| CP08 | PPDCS 阶段内滚动自检 | PPDCS 设计完整性 |
| CP09 | GATE-4 PPDCS Exit Gate | PPDCS 设计确认 |
| CP10 | PPDCS 阶段内滚动自检 | PC 生成完整性 |
| CP11 | GATE-4 PPDCS Exit Gate | 覆盖率确认 |
| CP12 | GATE-5 Exit Gate | 交付自检 |

### 追踪链

```
SR（系统需求）→ TP(C/A/E + topology_role_refs) → LC（因子-取值表 + topology_bindings + 动作路径）→ 组合（数据×路径×拓扑绑定）→ PC（物理用例）
```

每条物理用例可反向追踪：`PC → topology_bindings / 组合 → LC → TP → SR`；PC 中的真实设备、端口和链路还必须能追踪到 `kym/scenarios/confirmed-scenarios.md`。
```

---

### 3.2 变更 2：「运行时工作目录」→ 新目录结构

**章节定位**：`## 运行时工作目录`（第 69-129 行）

**变更要点**：将旧 `analysis/`/`design/` 分区替换为阶段级目录 `kym/`/`mfq/`/`ppdcs/`/`process/`。注意：`process/plan/` 和 `process/` 目录需要与 ptm-team 的运行时目录 `process/` 区分清楚（参见下方 Gotchas）。

**改前目录树**（缩略）：
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

**改后目录树**：
```text
<feature-project-root>/
├── input/                                    # 原始输入，只读
│   ├── <特性需求文件>.md
│   ├── <防火墙topo>.yaml
│   ├── <耦合矩阵>.xlsx
│   └── <其他参考资料>/
├── kym/                                      # KYM 阶段产物
│   ├── feature-input/                        # 解析后的结构化需求与目录
│   └── scenarios/                            # 已确认场景、Topology、atomic-ops
│       └── confirmed-scenarios.md            # 已确认场景与真实设备/端口/链路基线
├── mfq/                                      # MFQ 阶段产物
│   ├── m-analysis/                           # M 测试点、PPDCS 标注
│   ├── f-analysis/                           # F 耦合测试点
│   ├── q-analysis/                           # Q 质量测试点
│   ├── integration/                          # 整合层：LC、factor_bindings、topology_bindings
│   └── factor-usage/                         # 公共因子库 lock、binding、候选提案和解析报告
├── ppdcs/                                    # PPDCS 阶段产物
│   ├── ppdcs/                                # 每个逻辑用例的 PPDCS 设计过程
│   │   └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
│   ├── pc/                                   # 每个逻辑用例的物理用例
│   │   └── <三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
│   ├── coverage/                             # 双层覆盖率报告
│   └── delivery/                             # 最终交付物
│       ├── <特性名>特性测试方案.md
│       └── <特性名>特性测试用例.md
├── process/                                  # 跨阶段边界产物
│   └── plan/                                 # 设计计划（MFQ 阶段 design-planner 写入，PPDCS 阶段读取）
│   ├── checkpoints/                          # Gate 检查点结果
│   └── STATE.yaml                            # 当前特性项目运行状态
```

**目录迁移对照表**：

| 旧路径 | 新路径 | 所属阶段 |
|--------|--------|----------|
| `analysis/feature-input/` | `kym/feature-input/` | KYM |
| `analysis/scenarios/` | `kym/scenarios/` | KYM |
| `analysis/m-analysis/` | `mfq/m-analysis/` | MFQ |
| `analysis/f-analysis/` | `mfq/f-analysis/` | MFQ |
| `analysis/q-analysis/` | `mfq/q-analysis/` | MFQ |
| `analysis/integration/` | `mfq/integration/` | MFQ |
| `analysis/factor-usage/` | `mfq/factor-usage/` | MFQ |
| `analysis/plan/` | `process/plan/` | 跨阶段边界 |
| `analysis/coverage/` | `ppdcs/coverage/` | PPDCS |
| `design/ppdcs/` | `ppdcs/ppdcs/` | PPDCS |
| `design/pc/` | `ppdcs/pc/` | PPDCS |
| `delivery/` | `ppdcs/delivery/` | PPDCS |

**路径规则更新**（CRITICAL）：
1. 禁止创建或写入 `.output/`。
2. `input/` 只读，任何分析产物都不能写入 `input/`。
3. KYM 分析写入 `kym/`，MFQ 分析写入 `mfq/`（含 `mfq/factor-usage/`），跨阶段计划写入 `process/plan/`，PPDCS 设计与交付写入 `ppdcs/`，检查点写入 `process/checkpoints/`，状态写入 `process/STATE.yaml`。
4. `ppdcs/ppdcs/` 和 `ppdcs/pc/` 均按每个逻辑用例单文件输出，文件名固定为 `<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md`，不创建深层模块目录。
5. `ppdcs/delivery/` 只允许输出 `<特性名>特性测试方案.md` 和 `<特性名>特性测试用例.md`。
6. `process/plan/` 是跨阶段边界产物：MFQ 阶段的 design-planner 写入，PPDCS 阶段的 Skill 读取。主 Agent 在 PPDCS 阶段启动时检查 plan 存在性。

**关键描述文字变更**：

将运行时目录开篇描述从：
```markdown
一个特性对应一个特性项目。ptm-tde 在当前特性项目根目录工作，读取 `input/`，并将运行产物直接写入项目根目录下的规范目录；不再创建或使用 `.output/`。

- **`analysis/`** — MFQ 分析中间产物，按阶段分为 `feature-input/`、`scenarios/`、`m-analysis/`、`f-analysis/`、`q-analysis/`、`integration/`、`plan/`、`factor-usage/`、`coverage/`。
```

改为：
```markdown
一个特性对应一个特性项目。ptm-tde 在当前特性项目根目录工作，读取 `input/`，并将运行产物直接写入项目根目录下的阶段级规范目录；不再创建或使用 `.output/`。

- **`kym/`** — KYM（Know Your Mission）阶段产物：`feature-input/`、`scenarios/`。
- **`mfq/`** — MFQ 分析阶段产物：`m-analysis/`、`f-analysis/`、`q-analysis/`、`integration/`、`factor-usage/`。
- **`ppdcs/`** — PPDCS 设计与交付阶段产物：`ppdcs/`、`pc/`、`coverage/`、`delivery/`。
- **`process/plan/`** — 跨阶段边界产物：设计计划（MFQ 阶段 design-planner 写入，PPDCS 阶段读取+验证）。
```

同时更新 `factor-usage/` 和 `scenarios/confirmed-scenarios.md` 的路径引用：
- 所有 `analysis/factor-usage/` → `mfq/factor-usage/`
- `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`

简记更新：
```text
✅ 正确：D:\workspace\myproject\kym\feature-input\raw-requirements.md
❌ 错误：D:\workspace\myproject\analysis\feature-input\raw-requirements.md
❌ 错误：D:\workspace\myproject\.output\feature-input\raw-requirements.md
```
> **简记**：读 `input/`，按阶段写入 `kym/`、`mfq/`、`process/plan/`、`ppdcs/`、`process/checkpoints/`、`process/STATE.yaml`。

**交叉引用更新**：
- 「用户确认点」章节中所有路径引用（如 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`）
- 「测试因子、拓扑角色与真实组网对象分层」中的路径引用
- 「公共因子库」章节中 `analysis/factor-usage/` → `mfq/factor-usage/`

---

### 3.3 变更 3：「用户确认点」→ Gate 确认点

**章节定位**：`## 用户确认点`（第 196-212 行）

**变更要点**：将 "CP02 / CP09 / CP11" 三个确认点改写为 "GATE-2 / GATE-3 / GATE-4" 三个 Gate 确认点，不改变确认内容和决策收集规则。

**改前表格**：
```markdown
| 节点 | 确认内容 | 确认方式 |
| CP02 | 目录结构 + Seed-to-Scenario Mapping + ... | 收集全部 `confirmation_gaps` 并以统一决策清单呈现 |
| CP09 | 每个逻辑用例的 PPDCS 特征、设计方法、逻辑步骤和数据设计 | ... |
| CP11 | 覆盖率报告 | ... |
```

**改后表格**：
```markdown
| Gate | 确认内容 | 确认方式 |
|------|---------|---------|
| GATE-2 KYM Exit Gate | 目录结构 + Seed-to-Scenario Mapping + Scenario Chain / Operation Path / Topology / atomic-ops / Knowledge Reference / 待确认缺口 | 主 Agent 收集全部 `confirmation_gaps` 并以统一决策清单呈现（每项含推荐方案 + 至少 1 个备选方案 + 优劣分析），展示 GATE-2 自动自检结果（`process/checkpoints/GATE-2-KYM-Exit-auto.md`），等待用户确认 |
| GATE-3 MFQ Exit Gate（**新增**） | M/F/Q 分析质量、LC 整合一致性、设计计划、公共因子消费 | 主 Agent 收集全部 MFQ 阶段决策项并以统一清单呈现（每项含推荐方案 + 至少 1 个备选方案 + 优劣分析），展示 GATE-3 自动自检结果（`process/checkpoints/GATE-3-MFQ-Exit-auto.md`）和上下游 Warning，等待用户确认 |
| GATE-4 PPDCS Exit Gate | PPDCS 设计、覆盖率报告、PC 物化结果 | 主 Agent 收集全部设计决策项并以统一清单呈现（每项含推荐方案 + 至少 1 个备选方案 + 优劣分析），展示 GATE-4 自动自检结果（`process/checkpoints/GATE-4-PPDCS-Exit-auto.md`），等待用户确认 |
```

**确认点通用规则**保持不变（5 条规则不变，只更新引用编号）：
1. 决策收集 — 不变
2. 备选方案 — 不变
3. 决策清单格式 — 不变
4. 回退路径 — 不变
5. Deferred Ideas — 不变

---

### 3.4 变更 4：「Skill 触发词映射」→ 更新阶段归属列

**章节定位**：`## Skill 触发词映射`（第 214-237 行）

**变更要点**：将 `<阶段>` 列从旧步骤名（`input`/`scenario`/`m-analysis`/`f-analysis`/`q-analysis`/`integration`/`plan`/`design-ppdcs`/`design-pc`/`coverage`/`checkpoint`/`delivery`/`扩展`）改为新阶段归属（`KYM`/`MFQ`/`PPDCS`/`共享`/`扩展`）。

**改后表格**：

| Skill | 触发词 | PPDCS | 阶段 |
|-------|--------|-------|------|
| `feature-parser` | 解析特性、解析需求、导入特性文件 | KYM | KYM |
| `scenario-discovery` | 场景分析、搜索场景、应用场景、场景链 | KYM | KYM |
| `m-analyzer` | M分析、功能分析、模块分析、PPDCS标注 | M+TCO | MFQ |
| `f-analyzer` | F分析、耦合分析、耦合矩阵、特性交互 | F | MFQ |
| `q-analyzer` | Q分析、质量分析、HTSM、质量属性 | Q | MFQ |
| `test-point-integrator` | 整合测试点、测试点合并、逻辑用例 | — | MFQ |
| `design-planner` | 设计计划、PPDCS匹配、方法推荐 | PPDCS | MFQ |
| `process-design` | 流程图、流程图法、路径分析 | P-Process | PPDCS |
| `parameter-design` | 判定表、因果图、参数规则、决策树 | P-Parameter | PPDCS |
| `data-design` | 等价类、边界值、数据分析 | D-Data | PPDCS |
| `combination-design` | 数据组合、Pairwise、正交、因子组合 | C-Combination | PPDCS |
| `state-design` | 状态图、状态机、状态迁移 | S-State | PPDCS |
| `design-ppdcs-analyzer` | PPDCS设计、逻辑用例设计、单文件设计 | PPDCS | PPDCS |
| `coverage-verifier` | 覆盖检查、覆盖率、覆盖验证 | — | PPDCS |
| `checkpoint-manager` | GATE-1、GATE-2、GATE-3、GATE-4、GATE-5、自检、检查点 | — | 共享工具 |
| `deliverable-renderer` | 生成交付物、输出文档、测试方案 | — | PPDCS |
| `case-retriever` | 检索用例、按需求查用例、按LC查用例、按标签查用例 | — | PPDCS 后回查 |
| `change-impact-analyzer` | 需求变更、变更分析、增量分析 | — | 扩展 |
| `bug-gap-analyzer` | 问题单、缺陷分析、覆盖盲区 | — | 扩展 |

**变更说明**：
- `checkpoint-manager` 的触发词新增 `GATE-1`、`GATE-2`、`GATE-3`、`GATE-4`、`GATE-5`（保留旧 `CP01`、`自检`、`检查点`、`输入检查` 作为兼容别名）
- `checkpoint-manager` 的阶段归属从 `checkpoint` 改为 `共享工具`（因为它不仅服务 ptm-tde，还服务 Meta Flow 通用 CP0-CP8）
- `design-planner` 的阶段归属从 `plan` 改为 `MFQ`（作为 MFQ 阶段的最后一个 Skill）

---

### 3.5 变更 5：「初始化流程」→ 新目录创建

**章节定位**：`## 初始化流程`（第 239-246 行）

**变更要点**：将目录创建步骤从创建 `analysis/` 和 `design/` 子目录改为创建阶段级目录 `kym/`、`mfq/`、`ppdcs/` 和 `process/plan/`。

**改前**：
```markdown
## 初始化流程

1. 创建目录结构：
   - `input/`（用户输入，如已存在则跳过）
   - `analysis/feature-input/`、`analysis/scenarios/`、`analysis/m-analysis/`、`analysis/f-analysis/`、`analysis/q-analysis/`、`analysis/integration/`、`analysis/plan/`、`analysis/coverage/`
   - `design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/`
2. 初始化 `doc/STATE.yaml`（记录当前步骤为 `input`）
3. 提示用户将特性需求文件放入 `input/` 目录
4. 调用 `checkpoint-manager` 执行 CP01 input 自检，通过后调用 `feature-parser` 开始分析（输出写入 `analysis/feature-input/`）
```

**改后**：
```markdown
## 初始化流程

1. 创建目录结构：
   - `input/`（用户输入，如已存在则跳过）
   - `kym/feature-input/`、`kym/scenarios/`
   - `mfq/m-analysis/`、`mfq/f-analysis/`、`mfq/q-analysis/`、`mfq/integration/`、`mfq/factor-usage/`
   - `ppdcs/ppdcs/`、`ppdcs/pc/`、`ppdcs/coverage/`、`ppdcs/delivery/`
   - `process/plan/`、`process/checkpoints/`
2. 初始化 `process/STATE.yaml`（记录 `current_phase: kym`，并将 GATE-1 状态置为 `pending`）
3. 提示用户将特性需求文件放入 `input/` 目录
4. 调用 `checkpoint-manager` 执行 GATE-1 Entry Gate 自检，通过后更新 `process/STATE.yaml`（记录 GATE-1 结果），调用 `feature-parser` 开始分析（输出写入 `kym/feature-input/`）
```

**STATE.yaml 状态取值**：

| 字段 | 粒度 | 取值 | 说明 |
|------|------|------|------|
| `current_phase` | 阶段级 | `kym` / `mfq` / `ppdcs` / `exit` / `completed` | 由主 Agent 在各 Gate 通过后更新。阶段内所有步骤完成后才切换到下一阶段。 |
| `current_step` | 步骤级 | `feature-parser` / `scenario-discovery` / `m-analyzer` / `f-analyzer` / `q-analyzer` / `test-point-integrator` / `design-planner` / `design-ppdcs` / `pc` / `coverage` / `delivery` | 由主 Agent 在每个 Skill 执行后更新。**用途**：MFQ 阶段中途中断后，通过 `current_step` 可定位到具体 Skill，避免仅靠 `current_phase=mfq` 无法区分中断位置。 |

**设计理由**：`current_phase` 提供阶段级宏观视图（用于 Gate 路由和进度展示），`current_step` 提供步骤级精确恢复点（用于中断恢复和调试）。两个字段互补，不互相替代。

---

### 3.6 变更 6：「追踪链」→ 更新路径引用

**章节定位**：`## 追踪链`（第 285-290 行）

**变更要点**：将追链中的 `analysis/scenarios/confirmed-scenarios.md` 替换为 `kym/scenarios/confirmed-scenarios.md`。

**改前**：
```markdown
每条物理用例可反向追踪：`PC → topology_bindings / 组合 → LC → TP → SR`；PC 中的真实设备、端口和链路还必须能追踪到 `analysis/scenarios/confirmed-scenarios.md`。
```

**改后**：
```markdown
每条物理用例可反向追踪：`PC → topology_bindings / 组合 → LC → TP → SR`；PC 中的真实设备、端口和链路还必须能追踪到 `kym/scenarios/confirmed-scenarios.md`。
```

---

### 3.7 变更 7：「约束」→ 更新路径规则

**章节定位**：`## 约束`（第 297-304 行）

**变更要点**：保留全部 6 条约束不变（它们与 Skill 行为相关，不受框架改造影响），不新增或删除任何约束条目。

**最终约束列表**（不变）：
- 不修改用户的原始需求文件
- 变更和问题单分析时，不修改未受影响的用例
- 设计方法选择基于 PPDCS 特征匹配，尽量避免直接分析法
- 所有 Mermaid 图使用标准语法，确保可渲染
- 当场景目标、前置条件、原子操作、观察点、atomic-ops 或知识引用不确定时，必须先向用户确认，禁止猜测后继续推进
- 在任一确认节点暂停前，必须收集全部待确认问题并以统一决策清单呈现；每个决策项含推荐方案、至少 1 个备选方案（2 个为宜）和优劣分析；禁止逐条分散确认

---

## 4. 接口与契约

本 Story 仅修改主 Agent 的框架描述，不涉及新的接口或契约变更。现有接口保持不变：
- checkpoint-manager 仍从主 Agent 接收 gate/cp 参数
- 18 个阶段 Skill 的触发词映射和调用方式不变
- `process/STATE.yaml` 的 `current_phase` 取值变更从旧步骤名改为阶段名

**契约更新清单**（主 Agent 内部描述变更，不影响对接方）：
- checkpoint-manager 触发词新增 Gate 系列（保留旧触发词）
- `process/STATE.yaml` 的 `current_phase` 取值语义变更：`input`→`kym`、`scenario`→`kym`（合并）、`m-analysis`/`f-analysis`/`q-analysis`/`integration`/`plan`→`mfq`（合并）、`design-ppdcs`/`design-pc`/`coverage`→`ppdcs`（合并）、`delivery`→`exit`/`completed`

---

## 5. 异常与失败处理

| 场景 | 处理 |
|------|------|
| 目录创建失败（路径冲突/无权限） | GATE-1 Checklist #6 已覆盖；输出 BLOCKING 项，提示用户解决权限问题 |
| `process/STATE.yaml` 的 `current_phase` 更新失败 | 主 Agent 报错并停止推进，提示用户检查写权限 |
| Gate 检查失败 | 主 Agent 收集失败项（BLOCKING / Warning），输出确认稿；用户 reject 后回到对应阶段修复 |
| 旧路径在 Skill 中残留引用 | 主 Agent 框架部分已完成路径声明更新；Skill 中的残留由 CR-011/012/013 解决，本 CR 不在主 Agent 中做后台路径重定向 |

---

## 6. 测试方案

| 测试项 | 验证方式 | 预期结果 |
|--------|----------|----------|
| 三阶段框架表格完整性 | 读取 `agents/ptm-tde.md`，检查是否包含 3 阶段、5 Gate、CP↔Gate 映射表 | 表格存在，Gate 数量和命名与 `gate-spec.md` 一致 |
| 目录结构一致性 | 抽取主 Agent 中的所有路径引用（`kym/`、`mfq/`、`ppdcs/`、`process/plan/`），对照 HLD §8.2 目录迁移表 | 每个路径引用都指向新目录，无旧 `analysis/` 或 `design/` 残留 |
| Gate 确认点完整性 | 检查「用户确认点」章节包含 GATE-2、GATE-3、GATE-4 三个确认点，每个含确认内容和确认方式 | 3 个 Gate 确认点完整，GATE-3 明确标注为新增 |
| Skill 阶段归属 | 检查「Skill 触发词映射」表格的 `<阶段>` 列仅取值 KYM / MFQ / PPDCS / 共享工具 / 扩展 | 全部 18 个 Skill 的阶段归属已更新，无旧步骤名 |
| 初始化流程 | 检查初始化目录创建列表包含全部 12 个子目录 | 目录列表与目录迁移表一致 |
| STATE.yaml 取值 | 检查 `process/STATE.yaml` 的 `current_phase` 取值说明 | 取值为 `kym` / `mfq` / `ppdcs` / `exit` / `completed` |
| 旧编号消除 | `grep -c "CP01\|CP02\|CP03\|CP04\|CP05\|CP06\|CP07\|CP08\|CP09\|CP10\|CP11\|CP12" agents/ptm-tde.md` | 仅在 CP↔Gate 映射表中出现旧 CP 编号（作为历史参考） |
| 11 步消除 | `grep -c "11 步\|11步\|第 1 步\|第1步\|第 11 步\|第11步" agents/ptm-tde.md` | 0 |
| 公共因子库路径引用 | `grep -n "analysis/factor-usage" agents/ptm-tde.md` | 0（应全部替换为 `mfq/factor-usage`） |
| confirmed-scenarios.md 路径 | `grep -n "analysis/scenarios/confirmed-scenarios" agents/ptm-tde.md` | 0（应全部替换为 `kym/scenarios/confirmed-scenarios`） |

---

## 7. 回滚方案

| 回滚方式 | 操作 |
|----------|------|
| git revert | `git revert <commit-hash>`，将 `agents/ptm-tde.md` 恢复到改造前状态 |
| 手动回退 | 从 git 历史中提取旧版 `agents/ptm-tde.md` 覆盖当前文件 |
| 部分回退 | 若仅某个章节有问题（如目录结构），可单独 re-copy 该章节的旧版内容 |

**回退影响**：
- `agents/ptm-tde.md` 的回退不影响 `docs/ptm-tde/gate-spec.md`（独立新建文件）
- 若 STORY-010-05/010-06 已完成并回退，其文档中的新路径/新 Gate 引用会指向已回退的旧框架，造成不一致。因此本 Story 回退时需同步回退 STORY-010-05/010-06。

---

## 8. tier（复杂度）

**tier = M**

判定依据：
- 文件数：1 个（`agents/ptm-tde.md`）
- 变更行数：±200 行（框架部分重写）
- 变更类型：框架层结构改造，不涉及逻辑实现或 Skill 修改
- 风险等级：中（需逐条对照旧版确保不遗漏路径规则）

---

## 9. shared_fragments（共享片段引用）

| 片段 | 来源 | 用途 |
|------|------|------|
| CP↔Gate 映射表 | `docs/ptm-tde/gate-spec.md` §CP↔Gate 映射表 | 主 Agent「三阶段框架」章节引用，保持一致 |
| 目录迁移表 | `process/HLD-CR-010.md` §8 目录结构对比 | 主 Agent「运行时工作目录」章节引用，保持一致 |
| Gate 检查内容摘要 | `docs/ptm-tde/gate-spec.md` 各 Gate 的 Checklist 和人工确认项 | 主 Agent「用户确认点」章节引用 |
| 三阶段 + Gate 总览文本 | `process/HLD-CR-010.md` §4 推荐方案总览 | 主 Agent「三阶段框架」章节的基础文本 |

---

## 10. open_items（待确认项）

| ID | 问题 | 状态 | 说明 |
|----|------|------|------|
| O-02-01 | `process/plan/` 目录的 `process/` 与 ptm-team 运行时 `process/` 目录同名但语义不同（前者是特性项目根目录下的运行时产物，后者是 ptm-team 工作流管理目录）—— 主 Agent 中是否需要显式加注区分？ | OPEN | 当前方案不额外加注，因为主 Agent 的描述语境明确是"特性项目根目录下的 `process/plan/`"。若用户反馈混淆，可在 Gotchas 中增加说明。 |
| O-02-02 | `process/STATE.yaml` 的 `current_phase` 字段取值从旧步骤名改为阶段名后，是否存在消费 STATE.yaml 的外部工具？ | OPEN | 当前未知。若有外部工具依赖旧取值，需在 CR-011/012/013 实施时适配。本 CR 仅做框架声明。 |

---

## 11. 验证 checklist

- [ ] 三阶段框架表格包含完整的 3 阶段 + 5 Gate 描述
- [ ] CP↔Gate 映射表与 `gate-spec.md` 一致
- [ ] 目录树中无 `analysis/`、`design/`、`delivery/` 作为阶段产物路径
- [ ] 初始化流程中的目录创建列表覆盖全部 12 个子目录
- [ ] Skill 触发词映射表的阶段列全部更新为 KYM / MFQ / PPDCS / 共享工具 / 扩展
- [ ] 用户确认点章节包含 GATE-2、GATE-3、GATE-4 三个 Gate 确认点
- [ ] `grep "11 步\|11步" agents/ptm-tde.md` 返回 0
- [ ] `grep "CP0[1-9]\|CP1[0-2]" agents/ptm-tde.md` 仅在 CP↔Gate 映射表中出现
- [ ] `grep "analysis/factor-usage\|analysis/scenarios/confirmed-scenarios" agents/ptm-tde.md` 返回 0
- [ ] 扩展分支章节内容完整保留
- [ ] 理论基础、CAE 三元组、公共因子库、测试因子分层、目录层级规范、物理用例字段规范、交付物章节内容不变
- [ ] `process/STATE.yaml` 的 `current_phase` 取值说明正确

---

## 12. 依赖与门控

| 依赖项 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| STORY-010-01 | contract | done | `docs/ptm-tde/gate-spec.md` 已存在，Gate 编号、命名、Checklist 内容已被本 Story 引用 |
| STORY-010-05 | runtime | pending | 本 Story 完成后，STORY-010-05 才能据此更新核心文档中的路径和 Gate 描述 |
| STORY-010-06 | runtime | pending | 本 Story 完成后，STORY-010-06 才能据此更新索引和需求文件 |

---

## 13. DEV-LOG 预留

实现时在此记录：
- 实现步骤序号
- 每处变更的精确行号范围
- 与旧版的差异对比
- 意外发现的边界情况和处理

---

## 14. Gotchas

1. **`process/plan/` 不与 ptm-team 运行时 `process/` 混淆**：主 Agent 描述的是特性项目根目录下的目录结构。特性项目根目录下的 `process/plan/` 与 ptm-team 仓库根目录下的 `process/`（工作流管理）是不同路径，含义完全不同。主 Agent 上下文已明确这一点，但文档读者可能混淆——在运行时目录树图和描述中通过注释区分。

2. **旧路径残留风险**：本 Story 在 `agents/ptm-tde.md` 中全面替换路径引用，但「公共因子库」、「测试因子、拓扑角色与真实组网对象分层」、「交付物」等章节中有分散的路径引用（如 `analysis/factor-usage/`、`analysis/scenarios/confirmed-scenarios.md`、`delivery/`）。需逐章节把每个旧路径替换为新路径，不可遗漏。

3. **CP 编号只保留在映射表中**：主 Agent 中 CP01-CP12 只能出现在 CP↔Gate 映射表里（作为历史兼容参考），其他任何章节不得直接引用 CP 编号作为主流程引用。若「理论基础」或「CAE 三元组」等章节中隐藏了旧 CP 编号引用，需要一并清理。

4. **扩展分支章节的归属**：当前「扩展分支」紧跟「状态机」之后，在新框架中应紧跟「三阶段框架」之后，作为独立于三阶段的补充流程描述。

5. **checkpoint-manager 触发词兼容**：新增 GATE-X 触发词的同时，保留 `CP01`、`自检`、`检查点`、`输入检查` 作为兼容别名，确保旧触发词仍然可用。

6. **STATE.yaml 的 current_phase 语义变更**：原每个步骤都有独立取值（`input`、`scenario`、`m-analysis` 等），现在合并为阶段级取值（`kym`、`mfq`、`ppdcs`）。这意味着在 KYM 阶段内部，STATE.yaml 不会在 feature-parser 和 scenario-discovery 之间切换 phase——只有通过 Gate 后才更新 phase。

7. **GATE-3 人工确认点是新增的**：主 Agent 框架新增 GATE-3，需要确保「用户确认点」章节明确标注 GATE-3 为新增确认点，并在确认流程中实现以下行为：
   - GATE-3 自动自检后，输出 W1/W2（上下游 Warning）但不阻断
   - 人工确认稿中区分"阻断问题"和"Warning 提示"
   - 用户 reject → 回到 MFQ 阶段修复（不是 GATE-2）

---

## 补充章节：Requirements（Functional / Non-Functional）

> 本部分补全 meta-dev LLD 规范要求的章节，内容来自 CR-010 与 HLD-CR-010。

### Functional Requirements

| # | 需求 | 来源 |
|---|------|------|
| FR-02-01 | 主 Agent 流程描述从 11 步线性状态机改为三阶段框架（KYM → MFQ → PPDCS）+ 5 Gate 门控（GATE-1 至 GATE-5） | CR-010 §实施步骤 1 |
| FR-02-02 | CP↔Gate 映射表在「三阶段框架」章节显式列出，旧 CP 编号仅出现在此表中作为历史参考 | CR-010 §检查点→门控 |
| FR-02-03 | 运行时工作目录树从 `analysis/`/`design/` 全面替换为 `kym/`/`mfq/`/`ppdcs/`/`process/`，共 12 个子目录 | CR-010 §目录结构迁移 |
| FR-02-04 | 「用户确认点」章节从 3 个 CP 确认点改为 3 个 Gate 确认点（GATE-2/3/4），GATE-3 标注为新增 | CR-010 §新增 MFQ Exit Gate |
| FR-02-05 | Skill 触发词映射表的 `<阶段>` 列从旧步骤名改为 KYM / MFQ / PPDCS / 共享工具 / 扩展 | CR-010 §Skill 归属 |
| FR-02-06 | 初始化流程从创建 `analysis/`/`design/` 改为创建 `kym/`/`mfq/`/`ppdcs/`/`process/plan/`/`process/checkpoints/`，STATE.yaml 写入 `current_phase` 和 `current_step` | CR-010 §初始化 |
| FR-02-07 | 追踪链中的 `confirmed-scenarios.md` 路径从 `analysis/scenarios/` 改为 `kym/scenarios/` | CR-010 §目录结构迁移 |

### Non-Functional Requirements

- **兼容性**：保留 CP↔Gate 映射表作为历史参考，checkpoint-manager 触发词保持旧 CP 别名兼容
- **一致性**：所有路径引用（目录树、确认点、初始化流程、追踪链、Skill 映射、公共因子库）必须与新目录结构一致，禁止残留旧路径
- **可读性**：三阶段框架 ASCII 流程图与原 11 步流程图长度相当，不增加认知负担

---

## 补充章节：模块拆分与职责

本 Story 仅修改 1 个文件 `agents/ptm-tde.md` 中的 7 个章节，不涉及模块拆分。各章节的职责：

| 章节（agents/ptm-tde.md） | 变更职责 |
|---------------------------|----------|
| `## 状态机` → `## 三阶段框架` | 删除 11 步流程，替换为三阶段 + 5 Gate ASCII 流程图 + 阶段/Gate 总览表 + CP↔Gate 映射表 + 追踪链 |
| `## 运行时工作目录` | 目录树从 `analysis/`/`design/` 替换为 `kym/`/`mfq/`/`ppdcs/`/`process/`；更新路径规则和交叉引用 |
| `## 用户确认点` | CP02/CP09/CP11 → GATE-2/3/4；新增 GATE-3 确认内容；保留确认点通用规则 |
| `## Skill 触发词映射` | `<阶段>` 列从旧步骤名改为 KYM / MFQ / PPDCS / 共享工具 / 扩展；checkpoint-manager 触发词新增 Gate 系列 |
| `## 初始化流程` | 目录创建列表更新；STATE.yaml 路径和字段名更新 |
| `## 追踪链` | `confirmed-scenarios.md` 路径更新 |
| `## 约束` | 保持不变（不修改） |

其余 8 个章节（理论基础、CAE 三元组、公共因子库等）保留不修改。

---

## 补充章节：数据模型与持久化设计

本 Story 不涉及数据模型或持久化存储的新增。涉及的运行时状态变更：

| 对象 | 字段 | 变更 |
|------|------|------|
| `process/STATE.yaml` | `current_phase` | 取值从旧步骤名（`input`/`scenario`/...）改为阶段名（`kym`/`mfq`/`ppdcs`/`exit`/`completed`） |
| `process/STATE.yaml` | `current_step` | **新增**：步骤级 Skill 名（`feature-parser`/`scenario-discovery`/...），用于中断恢复 |
| `process/STATE.yaml` | 文件路径 | 从 `doc/STATE.yaml` 迁移至 `process/STATE.yaml` |

---

## 补充章节：技术设计细节

本 Story 为纯文本框架改写，不涉及算法或数据结构。关键设计决策：

- **ASCII 流程图**：使用固定宽度字符画三阶段 + Gate 流程，保持与旧 11 步图相同的可读性
- **CP↔Gate 映射表**：格式为 Markdown 表格，与 `gate-spec.md` 保持同步；旧 CP 编号只出现在此表中
- **目录树缩进**：使用 4 空格缩进 + `├──`/`└──` 符号，与旧目录树风格一致
- **路径替换策略**：使用 grep 逐章节扫描旧路径（`analysis/`、`design/`、`delivery/`、`checkpoints/`、`doc/STATE.yaml`），逐条替换；不依赖全局搜索替换以避免误伤

---

## 补充章节：安全与性能设计

本 Story 为纯文档改写，不涉及运行时代码执行路径变更，无新增安全风险或性能影响。

- **安全**：不涉及命令执行、文件写入权限变更或用户输入处理。约束条目中「不修改用户原始需求文件」保持不变。
- **性能**：ASCII 流程图和表格均为静态 Markdown，不影响 Agent 加载或解析性能。

---

## 补充章节：实施步骤

| 步骤 | 操作 | 验证方式 |
|------|------|----------|
| 1 | 修改 `## 状态机` → `## 三阶段框架` | 检查三阶段 ASCII 图 + 阶段/Gate 总览表 + CP↔Gate 映射表完整 |
| 2 | 修改 `## 运行时工作目录` | `grep "analysis/\|design/" agents/ptm-tde.md` 在框架部分返回 0 |
| 3 | 修改 `## 用户确认点` | 检查 GATE-2/3/4 三个确认点，GATE-3 标注为新增 |
| 4 | 修改 `## Skill 触发词映射` | 检查 `<阶段>` 列仅取值 KYM / MFQ / PPDCS / 共享工具 / 扩展 |
| 5 | 修改 `## 初始化流程` | 检查目录列表包含全部 12 个子目录，STATE.yaml 写入新路径 |
| 6 | 修改 `## 追踪链` | `confirmed-scenarios.md` 路径指向 `kym/scenarios/` |
| 7 | 逐章节扫描残留旧路径引用 | `grep -n "CP01\|CP02\|...\|CP12"` 仅在映射表中出现；`grep "analysis/factor-usage\|analysis/scenarios/confirmed-scenarios"` 返回 0 |

---

## 补充章节：风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 |
|-------------|------|----------|
| 旧路径残留遗漏 | 中 — 若「公共因子库」或「交付物」等非框架章节中残留旧路径，会导致文档不一致 | 实施步骤 7 逐章节 grep 扫描；验证 checklist 第 9 项覆盖 |
| 扩展分支位置调整 | 低 — 从紧跟「状态机」改为紧跟「三阶段框架」，若遗漏会导致章节顺序混乱 | 实施时明确标注扩展分支的新位置 |
| GATE-3 新增内容不足 | 低 — 若「用户确认点」中 GATE-3 的描述与 gate-spec.md 不一致 | 使用 shared_fragments 交叉引用 gate-spec.md 内容 |
| STATE.yaml current_step 缺位 | 中 — M5 修复已补充 `current_step` 字段设计 | §3.5 已更新为两字段模型 |
