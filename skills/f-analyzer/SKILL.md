---
name: f-analyzer
description: >-
  F 分析 v3.0（功能交互/耦合分析）：逐 TSP 驱动耦合分析，消费 M 分析产出的 TSP 列表
  和覆盖矩阵中的 [F→] 标签作为种子线索，逐 TSP 识别耦合关系、发现耦合对象/因子、
  三源合并（耦合矩阵基线 + 场景耦合 + 代码依赖）、生成按 TSP 组织的 CAE 耦合测试点。
  触发词包括：F分析、耦合分析、耦合矩阵、特性交互、功能耦合。
  适用场景：MFQ 分析的第四步（f-analysis 阶段）。
argument-hint: "可选：耦合矩阵 Excel 路径（无 Excel 时自动从 resource/coupling-matrix/ 加载 YAML 基线）"
user-invokable: true
status: active
---

## 目标

以 M 分析产出的 TSP 列表为核心驱动单元，消费覆盖矩阵中的 `[F→]` 标签作为耦合分析的种子线索，
逐 TSP 识别该 M 与其他 M（同特性或跨特性）的耦合关系、发现耦合对象和关联因子、
三源合并（耦合矩阵基线 + 场景耦合推理 + 代码依赖）后生成按 TSP 组织的 CAE 耦合测试点，
并产出耦合因子候选列表供下游候选汇总消费。新发现的耦合点经用户确认后可回写到耦合矩阵。

## 适用范围

- 适用阶段：MFQ 分析的 f-analysis 阶段（v3.0 逐 TSP 驱动）
- 输入：`mfq/m-analysis/tsp/*.md`（TSP 列表）+ `mfq/m-analysis/scenario-tsp-coverage.md`（覆盖矩阵，含 F 分析线索汇总表）+ `mfq/m-analysis/test-objects-factors.md`（测试对象与因子）+ `kym/scenarios/confirmed-scenarios.md`（已确认场景）+ 耦合矩阵 Excel / 外部配置
- 输出：`mfq/f-analysis/` 目录下多个文件（含耦合图、按 TSP 组织的耦合测试点、工具评估、耦合因子候选列表）

## 前置条件

- [ ] M 分析已完成（`mfq/m-analysis/test-points.md` 存在）
- [ ] M 分析的 TSP 列表可用（`mfq/m-analysis/tsp/*.md`，含每个 TSP 的 `id / m_id / topic / scope / purpose / f_tags / covered_scenario_segments`）
- [ ] M 分析的覆盖矩阵可用（`mfq/m-analysis/scenario-tsp-coverage.md`，含「F 分析线索汇总」表）
- [ ] M 分析的对象/因子可用（`mfq/m-analysis/test-objects-factors.md`，含已有因子和候选因子）
- [ ] `kym/scenarios/confirmed-scenarios.md` 存在
- [ ] `scripts/excel_coupling_tool.py` 可用
- [ ] 上游 `confirmation_gaps` 已区分"允许透传"与"必须回退确认"

⛔ **HARD-STOP（STOP-03）**：禁止 Agent 绕过本 Skill 直接生成 F 分析产物。F 分析必须通过 f-analyzer Skill 调用执行。

## 拓扑/因子分层 Guardrail

- 保持 trace chain v6、`factor_bindings` 和公共因子库规则；不得用真实组网对象替换逻辑因子。
- `factor_refs`、`factor_bindings`、耦合测试因子取值中禁止出现 `DUT.port*`、`TG.port*`、link 或 TOPO 实例。
- 若场景或耦合边必须引用真实组网对象，必须登记到 `topology_binding_refs` 或 `topology_source`，并保留 `source_ref / fact_status / confirmation_gap_refs`。
- 若真实组网对象来源、角色绑定或 TOPO 实例语义无法确认，相关耦合边、TP-F 或工具缺口必须降级为 `needs-confirmation`，不得包装成已确认因子。
- `test_object_refs` 可引用受影响对象编号；真实端口只能作为拓扑绑定或 PC 物化对象，不得混入 `covered_factors`。

## 三源数据模型

### 源 1：耦合矩阵基线（最低基线）

读取耦合矩阵基线（Excel 或 YAML），提取当前特性相关的耦合关系：

**Excel 路径**（用户提供时优先）：
```bash
python scripts/excel_coupling_tool.py read "<excel_path>" --output "mfq/f-analysis/coupling-graph.json"
python scripts/excel_coupling_tool.py query "mfq/f-analysis/coupling-graph.json" --feature "<特性名>"
```

**YAML 路径**（无 Excel 时 fallback）：
直接读取 `tgfw-coupling-matrix.yaml`，按 `domain` 字段过滤当前特性所在域，构建等价的 `matrix-baseline.yaml`。查找顺序：`resource/coupling-matrix/` → `~/.ptm-team/resource/coupling-matrix/` → `$PTM_TEAM_RESOURCE_HOME/coupling-matrix/`。

### 源 2：场景耦合推理（v3.0 逐 TSP 驱动）

不再全局扫描场景，而是以 M 分析产出的 TSP 列表为迭代器，对每个 TSP 独立分析其关联的场景步骤，
从中发现该 TSP 与其他 TSP/外部系统/共享对象的交互关系。优先展开覆盖矩阵中 M 分析预标记的 `[F→]` 标签（种子线索），
再自主发现未标记的耦合关系。

### 源 3：代码依赖（首版简化）

首版通过手动输入接口，由用户或开发人员提供代码级别的依赖关系：

```
请提供当前特性代码中依赖的其他特性/模块的接口列表（可选，首版非必填）：
```

## 执行流程

### 步骤 1：加载 TSP 列表、覆盖矩阵与矩阵基线

**📥 消费**：

| 消费数据 | 消费字段 | 用途 |
|---------|---------|------|
| M 分析的 TSP 列表 | 全部 TSP（`id / m_id / topic / scope / purpose / f_tags / covered_scenario_segments`） | **F 分析的核心驱动单元** |
| M 分析的覆盖矩阵 | **F 分析线索汇总表**（所有 `[F→]` 标签行：`来源场景 / 步骤 / 标签 / 目标 M/系统 / 说明`） | **耦合分析的种子线索**，优先展开已标记的耦合点 |
| 耦合矩阵 Excel 文件或 YAML 基线 | 全部 | 已有耦合关系基线 |

**🔄 处理逻辑**：

1. 读取矩阵基线（按优先级尝试）：
   a. **Excel 矩阵（优先）**：若用户提供了 Excel 路径：
   ```bash
   python scripts/excel_coupling_tool.py read "<excel_path>" \
     --output "mfq/f-analysis/coupling-graph.json"
   python scripts/excel_coupling_tool.py query \
     "mfq/f-analysis/coupling-graph.json" --feature "<特性名>"
   ```
   b. **YAML 基线（fallback）**：若无 Excel，读取 `resource/coupling-matrix/tgfw-coupling-matrix.yaml`，按 `domain` 字段过滤当前特性所在域，构建矩阵基线。若 `resource/` 不可用，检查 `~/.ptm-team/resource/coupling-matrix/` 或 `$PTM_TEAM_RESOURCE_HOME/coupling-matrix/`。
   输出 `matrix-baseline.yaml`（矩阵基线摘要）。

2. 加载 TSP 列表，建立 `TSP → M` 映射和 `TSP → covered_scenario_segments` 索引。

3. 加载覆盖矩阵中的「F 分析线索汇总」表，提取所有 `[F→]` 标签行，建立 F 线索索引：
   - 以 TSP 为主键，建立 `TSP → [F→标签列表]` 映射
   - 每条线索包含：`来源场景 / 步骤 / 标签（[F→目标]）/ 目标 M/系统 / 说明`

   示例线索：
   ```
   | TSP | 来源场景 | 步骤 | 标签 | 目标 M/系统 | 说明 |
   |-----|---------|------|------|-----------|------|
   | TSP-M2-001 | SCN-LOG-001 | Step 9 | [F→外部] | 外部日志服务器 | 日志发送涉及外部系统交互 |
   | TSP-M1-001 | SCN-LOG-002 | Step 4 | [F→M3] | M3-安全策略管理 | 配置关联安全策略 |
   ```

4. **F 线索指向不存在的 TSP**：若 F 线索中的目标 TSP 在 TSP 列表中不存在，
   记录为 `confirmation_gap`（标注 gap 类型 `f-tag-target-tsp-missing`）+ 警告提示，
   不阻断分析流程。该线索不纳入种子线索索引。

5. 分析结构确认：
   - TSP 列表 = `[TSP-M1, TSP-M2, TSP-M3, ...]`
   - F 线索 = M 分析预标记的跨 M 交互迹象（种子）
   - F 分析 = 对每个 TSP，从种子线索出发，识别它与其他 TSP 的交互关系
   - 种子线索之外的新发现耦合点 → 同样纳入分析，标注 `discovery_source=scenario-inference`

**📤 生产**：

| 产出 | 文件路径 |
|------|---------|
| 图模型 JSON + 矩阵基线摘要 | `mfq/f-analysis/coupling-graph.json` + `mfq/f-analysis/matrix-baseline.yaml` |
| TSP 驱动的分析框架 + F 线索索引 | 内存中，`TSP 列表 + F 线索 → 待分析的交互关系` |

### 步骤 2：逐 TSP 场景耦合推理——含耦合对象与因子发现

> 这是 v3.0 的核心变更。不再全局扫描场景，而是逐 TSP 进行交互分析。对每个 TSP，
> 从种子线索（F 标签）出发，识别耦合关系、发现耦合对象、匹配/生成耦合因子。

**📥 消费**：

| 消费数据 | 消费字段 | 用途 |
|---------|---------|------|
| 步骤 1 的 TSP 列表 | `id / m_id / topic / scope / f_tags / covered_scenario_segments` | 逐个 TSP 驱动分析 |
| 步骤 1 的 F 线索索引 | `TSP → [F→标签列表]` | 种子线索优先展开 |
| `kym/scenarios/confirmed-scenarios.md` | 全部 atomic_operations / minimal_logic_chain / precondition_operations | 逐步骤分析跨模块交互 |
| M 分析的测试对象表 | `object_id / object_name / object_type / 关联度 / scenario_refs` | 识别耦合涉及的对象 |
| M 分析的因子表（已有 + 候选） | `factor_id / data_domain / related_object_id / source` | 匹配耦合因子 |
| 公共因子库 `resource/factor-library/` | 全部 factor_id / factor_name / aliases / owner_object | 补充检索 |

**🔄 处理逻辑**：

```
对每个 TSP（TSP-M1, TSP-M2, TSP-M3, ...）：
  ┌─ TSP 级交互分析 ─────────────────────────────────────────────┐
  │ 当前 TSP：TSP-M2（topic: "根据优惠规则计算价格并输出购物清单"）│
  │ 该 TSP 的 f_tags：["可靠性-数据一致性"]（来自 M 分析标签）    │
  │                                                               │
  │   【子步骤 A：识别该 TSP 的耦合关系】                          │
  │   1. 优先从 F 种子线索出发：                                    │
  │      - 读取步骤 1 中该 TSP 对应的 [F→] 标签列表                │
  │      - 这些线索是 M 分析从场景步骤中已观察到的跨 M 交互迹象     │
  │      - 先展开这些已标记的耦合点，验证并补充细节                 │
  │      - 标注 discovery_source=f-tag-seed                        │
  │                                                               │
  │   2. 再在场景步骤序列中自主发现未标记的耦合关系：                │
  │      - 查找当前 TSP 关联的操作步骤（covered_scenario_segments） │
  │      - 判断每个步骤是否与以下对象发生交互：                      │
  │        · 同特性内的其他 TSP（TSP-M1、TSP-M3...）                │
  │        · 其他特性的 TSP（来自耦合矩阵 + 代码依赖）              │
  │        · 外部系统/环境                                         │
  │        · 共享同一 ptm-atomic op_id 或测试对象                   │
  │      - 发生交互时，标注 discovery_source=scenario-inference     │
  │                                                               │
  │   3. 确定耦合类型和强度：                                       │
  │      - 操作 A 模块的配置影响了 B 模块的行为 → 顺序耦合          │
  │      - 数据在模块间传递 → 数据耦合                             │
  │      - 异常路径涉及故障隔离 → 容错耦合                         │
  │      - 共享 ptm-atomic op_id 或测试对象 → 接口/资源耦合         │
  │      - coupling_strength：strong / normal / weak               │
  │                                                               │
  │   4. 记录耦合关系：                                             │
  │      - source_tsp / target_tsp                                 │
  │      - coupling_type（顺序/数据/容错/接口资源）                  │
  │      - coupling_strength（strong / normal / weak）             │
  │      - scenario_refs（回链到场景步骤）                          │
  │      - discovery_source（f-tag-seed / scenario-inference）      │
  │        同一耦合关系可能同时被 F 标签标记和自主发现，则取并集     │
  │      - confirmation_gap_refs（如有未确认事实）                  │
  │                                                               │
  │   【子步骤 B：发现该 TSP 的耦合对象】                          │
  │   对当前 TSP 的每条耦合关系：                                   │
  │     1. 识别交互中涉及的测试对象：                               │
  │        - 从 M 分析的测试对象表（test-objects-factors.md）中查找  │
  │        - 若已有 → 直接引用，标注 source=M-analysis              │
  │        - 若无对应对象 → 新建耦合对象记录，                      │
  │          标注 source=new-coupling-discovery                     │
  │     2. 记录耦合对象信息：                                       │
  │        - coupled_object_id / coupled_object_name                │
  │        - tsp_ref（所属 TSP）                                    │
  │        - object_role_in_coupling（枚举：触发方 / 受影响方 / 共享资源）│
  │        - source（M-analysis / new-coupling-discovery）          │
  │        - scenario_refs（回链）                                  │
  │                                                               │
  │   【子步骤 C：发现/匹配该 TSP 的耦合因子】                      │
  │   对当前 TSP 的每个耦合对象：                                   │
  │     1. 从 M 分析的因子表中查找关联因子：                        │
  │        - 已有因子（source=public-library）→ 直接引用            │
  │        - 候选因子（source=new-candidate）→ 引用并标记            │
  │     2. 若耦合对象无对应因子：                                   │
  │        → 从耦合步骤的操作参数/数据中提取                        │
  │        → 在公共因子库中检索                                     │
  │        → 未命中 → 生成"耦合因子候选"                            │
  │     3. 记录耦合因子候选：                                      │
  │        - factor_id / factor_name / data_domain                 │
  │        - related_coupled_object_id                             │
  │        - tsp_ref（所属 TSP）                                    │
  │        - coupling_ref（所属耦合关系）                            │
  │        - discovery_source（f-tag-seed / scenario-inference）    │
  │        - source=new-coupling-candidate                         │
  └───────────────────────────────────────────────────────────────┘

汇总（所有 TSP 分析完成后）：
  - 以 (source_tsp, target_tsp) 为 key 内部去重合并
  - 同一耦合关系出现在不同 TSP 视角时合并来源和 discovery_source
  - discovery_source 取并集（例如同一耦合既被 F 标签标记又被自主发现 → [f-tag-seed, scenario-inference]）
```

**📤 生产**：

| 产出 | 内容 |
|------|------|
| 逐 TSP 耦合关系表 | `tsp_ref → [(target_tsp, coupling_type, coupling_strength, scenario_refs, discovery_source), ...]` |
| 耦合对象列表 | `coupled_object_id / tsp_ref / object_role_in_coupling（触发方/受影响方/共享资源）/ source（M-analysis / new-coupling-discovery）` |
| **耦合因子候选列表**（初始记录） | `factor_id / factor_name / data_domain / tsp_ref / related_coupled_object_id / coupling_ref / discovery_source / source=new-coupling-candidate` |

### 步骤 3：代码依赖收集（可选）

**📥 消费**：用户手动输入的代码级依赖关系

**🔄 处理逻辑**：
1. 提示用户输入代码依赖（如有，可跳过）：
   ```
   请提供当前特性代码中依赖的其他特性/模块的接口列表（可选，首版非必填）：
   ```
2. 将用户输入的依赖关系转换为耦合边
3. 标注来源为 `code-dependency`

**📤 生产**：代码依赖耦合边列表

### 步骤 4：三源合并

**📥 消费**：步骤 1（矩阵基线，Excel 或 YAML）+ 步骤 2（场景推理）+ 步骤 3（代码依赖）

**🔄 处理逻辑**：

```
1. 以 (source_tsp, target_tsp) 为 key 去重
2. 同 key 多源合并，保留所有来源标注
3. 耦合强度取最高值：strong > normal > weak
4. confirmation_gap_refs 取并集；存在 gap 时不提升为"已确认"
5. discovery_source 取并集：
   - 仅在 F 标签种子中发现 → [f-tag-seed]
   - 仅自主推理发现 → [scenario-inference]
   - 两者皆有 → [f-tag-seed, scenario-inference]
```

**📤 生产**：`mfq/f-analysis/coupling-graph.yaml`（三源合并后的完整耦合图，标注 `tsp_ref` + `discovery_source`）

### 步骤 5：候选耦合点确认

将新发现的耦合点（不在矩阵基线中的）呈现给用户确认。

**🔄 处理逻辑**：

```
## 新发现的耦合关系

| # | 当前 TSP | 耦合目标 TSP | 耦合类型 | 耦合强度 | discovery_source | 来源场景 | 描述 |
|---|---------|------------|---------|:---:|------------------|---------|------|
| 1 | TSP-M2-001 | TSP-M3-001 | 顺序耦合 | strong | f-tag-seed | SCN-001 | ... |
| 2 | TSP-M1-001 | TSP-M2-001 | 数据耦合 | normal | scenario-inference | SCN-002 | ... |
```

⛔ **HARD-STOP（STOP-02）**：禁止 Agent 自行判定候选全部确认。必须展示候选表并等待用户回复。

**平台交互协议**：Claude Code 环境且 `AskUserQuestion` 可用时，优先使用结构化选择：
- question: "请确认新发现的耦合关系："
- header: "Coupling"
- multiSelect: false
- options:
  1. label: "Confirm all", description: "所有新耦合关系有效，继续生成耦合测试点并询问是否回写矩阵"
  2. label: "Partial", description: "请指出不成立的耦合关系编号（用逗号分隔），其余确认成立"
  3. label: "Reject all", description: "新发现的耦合关系均不成立，跳过回写，仅使用基线矩阵"

Codex 或 `AskUserQuestion` 不可用时，回退到 STOP-05 文本标记：

```
( ) ✅ 全部确认成立 — 所有新耦合关系有效，继续生成耦合测试点，并询问是否回写矩阵
( ) ✏️ 部分确认 — 请指出不成立的耦合关系编号（用逗号分隔），其余确认成立
( ) ❌ 全部不成立 — 新发现的耦合关系均不成立，跳过回写，仅使用基线矩阵
```

**📤 生产**：确认后的有效耦合点集合

### 步骤 6：耦合测试点生成

对每个已确认或允许带 gap 透传的耦合关系，生成 CAE + trace 格式的耦合测试点。

**📥 消费**：

| 消费数据 | 用途 |
|---------|------|
| 步骤 4/5 的有效耦合关系 | 测试点来源 |
| 步骤 2 的耦合对象 + 耦合因子 | C 条件和 factor_refs |
| M 分析的测试对象/因子 | 补充引用 |
| `kym/scenarios/confirmed-scenarios.md` + 全局 ptm-atomic | trace 和 A 动作 |

**🔄 处理逻辑**：

对每个已确认的耦合关系生成耦合测试点，**按 TSP 组织**：

```
## TSP-M2-001：根据优惠规则计算价格并输出购物清单

### 耦合关系：TSP-M2-001 → TSP-M1-001（配置管理）

| TP-ID | C 条件 | A 动作 | E 预期 | ... |
|-------|--------|--------|--------|-----|
| TP-F-M2-M1-001 | ... | ... | ... | ... |

### 耦合关系：TSP-M2-001 → TSP-M3-001（安全策略）

| TP-ID | C 条件 | A 动作 | E 预期 | ... |
|-------|--------|--------|--------|-----|
| TP-F-M2-M3-001 | ... | ... | ... | ... |

---
## TSP-M1-001：配置日志服务器
...
```

每个耦合测试点包含的字段：

| 字段 | 说明 |
|------|------|
| TP-ID | `TP-F-<源TSP缩写>-<目标TSP缩写>-NNN` |
| 所属 TSP | `tsp_ref`（当前所在 TSP） |
| C 条件 | 触发耦合交互的前置状态和环境条件（含耦合目标的前置状态；多个用"；"分隔）。已有因子用具体域，候选因子用域引用（如 `@domain.普通`） |
| A 动作 | 操作当前特性（触发耦合效果），**不得直接操作耦合目标** |
| E 预期 | 可观测的耦合行为预期（包含对耦合目标的影响）。E="待定" 时须附批注 `[待定原因: <描述>]` |
| 来源 | `matrix-baseline / scenario-coupling / code-dependency` |
| 耦合强度 | `strong / normal / weak` |
| `discovery_source` | `f-tag-seed / scenario-inference` |
| `scenario_refs` | 来源场景 |
| `scenario_chain_refs` | 涉及的 PRE / AO / 最小逻辑链节点 |
| `action_source_refs` | 关联 ptm-atomic `op_id` |
| `knowledge_refs` | 支撑耦合判断的知识引用 |
| `confirmation_gap_refs` | 未确认事实引用 |
| `test_object_refs` | 被影响对象 |
| `factor_refs` | 关键耦合因子 |
| `topology_binding_refs` | 真实端口、link 或 TOPO 实例的来源绑定；无则写 `—` |
| `trace_refs` | 汇总 trace |
| `fact_status` | `confirmed / needs-confirmation` |

**耦合因子全候选降级规则**：

当某个耦合测试点的所有关联因子 `source` 均为 `new-coupling-candidate`（即无已有因子支撑）：
- 该 TP 的 `fact_status` 降级为 `needs-confirmation`
- C 条件中使用因子域引用（如 `@domain.普通`）而非具体值
- 在候选汇总确认前，测试点标记为 `[待确认]`

**CAE 字段约束（耦合测试点）**：
- C：包含触发耦合交互的前置状态和环境条件（含耦合目标的前置状态）
- A：操作当前特性（触发耦合效果），**不得直接操作耦合目标**
- E：包含耦合目标的可观测行为；E="待定" 时须附批注 `[待定原因: <如"被耦合目标行为规格待确认">]`
- 若耦合判断依赖 `Knowledge Reference=missing/unavailable` 或 `ptm-atomic=gap/unknown`，必须保留原状态并标记 `fact_status=needs-confirmation`
- 若耦合判断依赖 `DUT.port*`、`TG.port*`、link 或 TOPO 实例，必须通过 `topology_binding_refs` 回链来源；不得写入 `factor_refs`

**📤 生产**：

| 产出 | 文件路径 |
|------|---------|
| 耦合测试点（按 TSP 组织） | `mfq/f-analysis/coupling-test-points.md` |
| 耦合因子候选列表（汇总记录，供步骤 9 使用） | 内存中积累 |

### 步骤 7：工具覆盖评估

对每个耦合测试点，评估现有工具/ptm-atomic 是否能够：

1. 触发耦合前置与主动作
2. 观察耦合目标状态
3. 校验耦合结果

输出两类结构化结果：

#### Existing Tool Summary

| 字段 | 说明 |
|------|------|
| `tool_id` | 工具编号 |
| `tool_name` | 工具名称 |
| `main_usage` | 主要用法 |
| `purpose` | 在当前耦合场景中的用途 |
| `scenario_refs` | 关联场景 |
| `action_source_refs` | 依赖的 ptm-atomic `op_id` |
| `covered_objects` | 已覆盖对象 |
| `covered_factors` | 已覆盖因子 |
| `status` | `ready / partial / needs-confirmation` |

> `Existing Tool Summary` 是 integrator 的正式上游契约。字段名必须原样保留；`covered_objects / covered_factors` 优先填写对象/因子编号列表，无法确认时保留 `[待确认]` 并将 `status` 置为 `needs-confirmation`，不得静默删列或改名。

#### Tool Capability Gap

| 字段 | 说明 |
|------|------|
| `tool_id` | 工具编号 |
| `tool_name` | 工具名称或候选名称 |
| `covered_objects` | 已覆盖对象 |
| `covered_factors` | 已覆盖因子 |
| `missing_ops` | 缺失操作 / 观察 / 校验能力 |
| `proposed_interface` | 建议 CLI/API/method 入口 |
| `function_desc` | 能力说明 |
| `io_behavior_matrix` | 不同输入/输出条件下的处理逻辑 |
| `output_contract` | 输出内容与观察点契约 |
| `scenario_refs` | 关联场景 |
| `action_source_refs` | 关联 ptm-atomic `op_id` |
| `factor_refs` | 关联因子 |
| `status` | `gap / needs-confirmation` |

> `Tool Capability Gap` 同样必须保留以上原名字段，供 integrator 在保留原名的同时生成标准化别名；不得仅保留说明性文字而省略 `covered_objects / covered_factors / io_behavior_matrix`。

**📤 生产**：

| 产出 | 文件路径 |
|------|---------|
| Existing Tool Summary + Tool Capability Gap | `mfq/f-analysis/tool-analysis.md` |

### 步骤 8：可选回写

若步骤 5 中用户确认了新耦合点，询问是否回写矩阵：

⛔ **HARD-STOP（STOP-02）**：禁止 Agent 自行决定回写。必须展示确认选项并等待用户回复。

**平台交互协议**：Claude Code 环境且 `AskUserQuestion` 可用时，优先使用结构化选择：
- question: "是否将已确认的新耦合点回写到耦合矩阵？"
- header: "Write back"
- multiSelect: false
- options:
  1. label: "Write back", description: "将已确认的新耦合点写入 Excel 耦合矩阵"
  2. label: "Skip", description: "本次仅用于测试点生成，不更新矩阵基线"

Codex 或 `AskUserQuestion` 不可用时，回退到 STOP-05 文本标记：

```
请选择回写操作：

( ) ✅ 同意回写 — 将已确认的新耦合点写入 Excel 耦合矩阵
( ) ❌ 暂不回写 — 本次仅用于测试点生成，不更新矩阵基线
```

若用户同意回写，执行：

```bash
python scripts/excel_coupling_tool.py write "<excel_path>" --source "mfq/f-analysis/new-coupling-points.json"
```

**📤 生产**：`mfq/f-analysis/new-coupling-points.json` + 更新后的 Excel

### 步骤 9：耦合因子候选列表汇总

> 🆕 **v3.0 新增步骤**：汇总步骤 2 子步骤 C 中所有 `source=new-coupling-candidate` 的耦合因子候选，按 TSP 组织，供下游候选汇总消费。

**📥 消费**：步骤 2 子步骤 C 记录的耦合因子候选列表

**🔄 处理逻辑**：

1. 从步骤 2 的原始记录中提取所有 `source=new-coupling-candidate` 的条目
2. 若步骤 6 中部分候选已被确认（如通过用户确认补充了因子信息），仅汇总未确认的候选
3. 按 TSP 组织输出为表格：

```
## 耦合因子候选列表

> 以下因子候选由 F 分析步骤 2 逐 TSP 耦合推理中发现，M 分析因子表中无对应已有因子。
> 标注 tsp_ref 和 coupling_ref，供候选汇总步骤统一确认。

### TSP-M2-001：根据优惠规则计算价格并输出购物清单

| factor_id | factor_name | data_domain | tsp_ref | coupling_ref | discovery_source | 说明 |
|-----------|-------------|-------------|---------|-------------|-------------------|------|
| FAC-F-CAND-001 | 优惠规则冲突处理结果 | 冲突/未冲突/部分冲突 | TSP-M2-001 | COUP-M2-M1 | scenario-inference | 规则冲突时的跨模块处理行为 |
| FAC-F-CAND-002 | 外部价格同步状态 | 已同步/未同步/超时 | TSP-M2-001 | COUP-M2-EXT | f-tag-seed | 外部价格源同步的耦合状态 |

### TSP-M1-001：配置日志服务器
...
```

**📤 生产**：

| 产出 | 文件路径 | 说明 |
|------|---------|------|
| 耦合因子候选列表 | 追加到 `mfq/f-analysis/coupling-test-points.md` 末尾 | 标注 `tsp_ref / coupling_ref / discovery_source`，供 test-point-integrator → 候选汇总（STORY-012-07）消费 |

## 输出文件

> 追踪链：`SR → Scenario Chain → ptm-atomic / Knowledge Reference → TSP → TP-F(CAE + coupling trace) → LC → Test Data → PC`

全部写入 `mfq/f-analysis/`：

| 文件 | 内容 | 主要消费方 |
|------|------|-----------|
| `coupling-graph.json` | 图模型 JSON（仅 Excel 源产出） | 内部消费 |
| `matrix-baseline.yaml` | 耦合矩阵基线摘要（Excel 或 YAML 源统一格式） | 内部消费 |
| `coupling-graph.yaml` | 三源合并后的完整耦合图（标注 `tsp_ref` + `discovery_source`） | test-point-integrator（STORY-012-06） |
| `coupling-test-points.md` | 耦合测试点（**按 TSP 组织**，每个 TSP 下列出其耦合关系和 CAE+trace）+ **耦合因子候选列表**（末尾汇总） | test-point-integrator（STORY-012-06）+ 候选汇总（STORY-012-07） |
| `tool-analysis.md` | Existing Tool Summary + Tool Capability Gap | test-point-integrator（STORY-012-06） |
| `new-coupling-points.json` | 新发现的耦合点（用于回写，仅当用户同意回写时生成） | Excel 工具 |

**`coupling-test-points.md` 输出格式示例**：

```markdown
# <特性名> — F 分析耦合测试点

> v3.0：按 TSP 组织，每个 TSP 下的耦合关系和测试点独立列出。

## TSP-M2-001：根据优惠规则计算价格并输出购物清单

### 耦合关系：TSP-M2-001 → TSP-M1-001（配置管理，discovery_source: f-tag-seed）

| TP-ID | C 条件 | A 动作 | E 预期 | scenario_refs | action_source_refs | factor_refs | 来源 | 耦合强度 | fact_status |
|-------|--------|--------|--------|---------------|--------------------|-------------|------|:---:|-------------|
| TP-F-M2-M1-001 | 日志归并功能已开启；日志服务器已配置 | 删除已配置的日志服务器 | 日志归并功能不受影响；归并日志继续正常记录 | SCN-LOG-001 | fw_delete_log_server | FAC-SERVER-STATE | matrix-baseline | strong | confirmed |
| TP-F-M2-M1-002 | ... | ... | ... | ... | ... | ... | scenario-coupling | normal | needs-confirmation |
```

> 若 TP-F 需要暴露真实端口或 TOPO 实例，在表后附 `topology_binding_refs` 明细表；主表 `factor_refs` 仍只保留逻辑因子。

**`tool-analysis.md` 输出格式**：

```markdown
# <特性名> — F 分析工具覆盖评估

## Existing Tool Summary

| tool_id | tool_name | main_usage | purpose | scenario_refs | action_source_refs | covered_objects | covered_factors | status |
|---------|-----------|------------|---------|---------------|--------------------|-----------------|-----------------|--------|
| TOOL-001 | log-cli | `log-cli server delete --id ...` | 删除日志服务器以触发耦合 | SCN-LOG-001 | fw_delete_log_server | OBJ-LOG-SERVER | FAC-SERVER-ID | ready |

## Tool Capability Gap

| tool_id | tool_name | covered_objects | covered_factors | missing_ops | proposed_interface | function_desc | io_behavior_matrix | output_contract | scenario_refs | action_source_refs | factor_refs | status |
|---------|-----------|-----------------|-----------------|-------------|--------------------|---------------|--------------------|-----------------|---------------|--------------------|-------------|--------|
| GAP-TOOL-001 | traffic-injector | OBJ-PEER-ALARM | FAC-ALARM-TYPE,FAC-ALARM-TIMELINE | 观测对端告警联动 | CLI: `traffic-injector observe --target ...` | 输出耦合告警状态与时间线 | 目标可达→返回告警状态与时间线；目标不可达→返回不可观测原因与错误码 | stdout/json + return code + alarm timeline | SCN-LOG-001 | fw_observe_peer_alarm | FAC-ALARM-TYPE,FAC-ALARM-TIMELINE | gap |
```

## 耦合分析维度

### 特性内耦合

同一特性内不同模块/子模块之间的交互：
- 配置变更传播：模块 A 的配置变更是否影响模块 B
- 数据共享：模块间共享的数据结构/缓存/数据库
- 状态依赖：模块 A 的状态变化是否影响模块 B 的行为

### 特性间耦合

当前特性与其他特性之间的交互：
- 功能依赖：当前特性依赖其他特性的功能
- 资源竞争：与其他特性共享系统资源
- 事件触发：当前特性的事件可能触发其他特性的行为

## Gotchas

- Excel 批注中混有审阅批注和格式说明，需要语义过滤
- 耦合矩阵的行列可能使用不同粒度的名称，需做名称规范化
- 场景耦合推理可能产生误报，需用户确认
- 不要漏掉"反向耦合"：A→B 存在时检查 B→A
- `confirmation_gaps` 影响耦合成立性时，允许输出候选 TP，但不能包装成已确认耦合
- `coupling-graph.yaml`、`coupling-test-points.md` 与 `tool-analysis.md` 必须使用同一 `fact_status` 口径；任一耦合边或 TP 依赖 `confirmation_gaps`、候选因子、推理型 coupling、缺失知识引用或拓扑来源不明时，必须降级为 `needs-confirmation`
- `confirmed` 只允许用于已确认场景链、已存在耦合矩阵/显式需求依据、已确认因子和已确认拓扑来源同时成立的耦合点；不得因“合理推测”或“看起来应当耦合”写成 confirmed
- 工具评估只基于已给定 ptm-atomic / Existing Tool Usage Seed / Tool Draft，不能自行发明现有工具能力
- 不得把 `DUT.port1/TG.port2`、link 或 TOPO 实例写入 `factor_refs / factor_bindings / covered_factors`；真实组网对象必须登记拓扑来源，来源不明则降级 `needs-confirmation`
- **（v3.0 新增）F 线索指向不存在的 TSP**：当覆盖矩阵的 F 线索汇总表中某行的目标 TSP 在 TSP 列表中不存在时，记录 `confirmation_gap`（类型 `f-tag-target-tsp-missing`）并警告，不阻断分析。该线索不作为种子线索参与步骤 2 的优先展开
- **（v3.0 新增）同一耦合关系多 TSP 视角去重**：某耦合关系 `TSP-M1 ↔ TSP-M2` 可能同时在 TSP-M1 和 TSP-M2 的分析中被发现。步骤 2 汇总时以 `(source_tsp, target_tsp)` 为 key 内部去重，步骤 4 三源合并时再次去重。`discovery_source` 取并集
- **（v3.0 新增）全候选降级的确认依赖**：当某耦合测试点的所有关联因子 `source` 均为 `new-coupling-candidate` 时，`fact_status` 降级为 `needs-confirmation`。该 TP 在候选汇总确认前不可作为已确认测试点用于下游

## 验收标准

- [ ] M 分析的 TSP 列表已加载（每个 TSP 的 `id / m_id / topic / scope / purpose / f_tags` 完整）
- [ ] 覆盖矩阵中的 F 分析线索汇总表已读取，F 线索索引（`TSP → [F→标签列表]`）已建立
- [ ] 耦合矩阵基线已成功加载（Excel 或 YAML 源，至少一个可用）
- [ ] 步骤 2 逐 TSP 耦合推理已执行（每个 TSP 独立完成子步骤 A→B→C）
- [ ] 每个耦合关系已标注 `discovery_source`（`f-tag-seed` / `scenario-inference`）
- [ ] 耦合对象已发现（标注 `object_role_in_coupling`：触发方/受影响方/共享资源 + `source`：M-analysis/new-coupling-discovery）
- [ ] 耦合因子候选已记录（`source=new-coupling-candidate`，标注 `tsp_ref` + `coupling_ref`）
- [ ] 三源合并后无重复耦合边（以 `(source_tsp, target_tsp)` 为 key 去重）
- [ ] 新耦合点已呈现给用户并获得确认（HARD-STOP：禁止 Agent 自行判定）
- [ ] 耦合测试点包含完整 CAE 三字段（C/A/E 均不为空）
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 耦合测试点**按 TSP 组织**（每个 TSP 一个子节）
- [ ] 耦合因子全候选的 TP 已降级 `fact_status=needs-confirmation`
- [ ] `coupling-graph.yaml` 与 `coupling-test-points.md` 的 `fact_status` 一致，未确认耦合未被升格为 `confirmed`
- [ ] A 动作不得直接操作耦合目标
- [ ] 每个 TP-F 包含 `scenario_refs / action_source_refs / factor_refs / trace_refs / discovery_source`
- [ ] `factor_refs / factor_bindings / covered_factors` 未混入真实端口、link 或 TOPO 实例；涉及真实组网对象时已登记拓扑来源或降级 `needs-confirmation`
- [ ] 工具评估输出 `Existing Tool Summary` 和 `Tool Capability Gap`
- [ ] 步骤 9 耦合因子候选列表已汇总（追加到 `coupling-test-points.md` 末尾，标注 `tsp_ref / coupling_ref / discovery_source`）
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式保留
- [ ] 输出文件路径全部为 `mfq/f-analysis/`
- [ ] 写入前校验目标父目录 `mfq/f-analysis/` 存在且为目录；若不存在则提示用户，禁止 Agent 自行 mkdir
