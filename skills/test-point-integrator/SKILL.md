---
name: test-point-integrator
description: >-
  整合 M+F+Q 三维分析的测试点，按模块归集、覆盖检查、同逻辑测试点合并，
  输出逻辑用例列表和测试数据。
  触发词包括：整合测试点、测试点合并、逻辑用例、测试点归集。
  适用场景：MFQ 分析的第六步（integration 阶段）。
argument-hint: "无需参数，自动读取 m/f/q-analysis 目录"
user-invokable: true
status: active
---

## 目标

将 M 分析、F 分析、Q 分析产出的测试点按模块归集，
执行完整覆盖检查，将具有相同测试逻辑的测试点合并为逻辑用例，
并为每个逻辑用例分配可追踪的测试数据，同时归并上游工具分析结果，
形成 STORY-08 可直接消费的 trace chain v6 中间资产。

## 适用范围

- 适用阶段：MFQ 分析的 integration 阶段
- 输入：`mfq/m-analysis/` + `mfq/f-analysis/` + `mfq/q-analysis/`
- 输出：`mfq/integration/` 目录下多个文件

## 前置条件

- [ ] M 分析完成（`mfq/m-analysis/test-points.md` 存在）
- [ ] F 分析完成（`mfq/f-analysis/coupling-test-points.md` 存在）
- [ ] Q 分析完成（`mfq/q-analysis/quality-test-points.md` 存在）
- [ ] `kym/scenarios/confirmed-scenarios.md` 存在，且包含已确认 TOPO / 组网实例或明确标记无组网约束
- [ ] 上游 TP 已包含 `trace_refs / scenario_refs / action_source_refs / test_object_refs / factor_refs / topology_refs / topology_role_refs`
- [ ] 上游工具评估文件存在，或明确标记为”无工具分析结果”
- [ ] M 分析覆盖矩阵存在（`mfq/m-analysis/scenario-tsp-coverage.md` 存在）
- [ ] M 分析候选文件存在（`mfq/m-analysis/candidate-factor-proposals.yaml` 和 `mfq/m-analysis/candidate-ptm-atomic.yaml` 存在）

## 输入契约（Story-04）

integrator 必须消费并透传以下字段：

| 来源 | 必收字段 |
|------|----------|
| M/F/Q TP | `trace_refs`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `knowledge_refs`, `confirmation_gap_refs`, `test_object_refs`, `factor_refs`, `topology_refs`, `topology_role_refs`, `topology_binding_status`, `topology_gap_refs`, `fact_status` |
| M 对象/因子 | `object_id`, `factor_id`, `data_domain`, `related_object_id` |
| F/Q 工具评估 | `Existing Tool Summary`, `Tool Capability Gap` |
| 场景链 | `minimal_logic_chain`, `ptm-atomic`, `Knowledge Reference`, `confirmation_gaps`, `TOPO` / 组网实例 |

## 三层绑定边界

- **测试因子**：业务/配置/数据/报文取值，继续由 `factor_bindings` 作为主契约承载。
- **拓扑角色**：测试逻辑位置，来自 TP 的 `topology_role_refs`，例如 `MATCH_INGRESS_IF`。
- **真实组网对象**：confirmed-scenarios.md 中已确认的 TOPO 实例，integrator 只能从该文件绑定，不得从裸端口文本猜测。

`DUT.port1`、`TG.port1`、link 实例不得进入 LC 因子-取值表或 TD `value_set`。若上游 TP 混入裸端口，必须保留为拓扑待确认缺口，不得继承为测试因子。

## 执行流程

### 步骤 1：测试点归集

**加载输入文件**：

1. 读取 M/F/Q 测试点文件（`mfq/m-analysis/`、`mfq/f-analysis/`、`mfq/q-analysis/` 下对应文件）
2. 读取 `kym/scenarios/confirmed-scenarios.md` 获取已确认场景和 TOPO 实例
3. **读取覆盖矩阵**：加载 `mfq/m-analysis/scenario-tsp-coverage.md`，解析视角 A 的覆盖矩阵（场景→TSP，含 covered/uncovered/excluded 统计）。**若该文件不存在，报错并终止：`mfq/m-analysis/scenario-tsp-coverage.md 不存在，请先执行 M 分析（STORY-012-03）`**
4. **声明候选列表文件路径**（用于候选归集步骤）：
   - M 因子候选：`mfq/m-analysis/candidate-factor-proposals.yaml`
   - M 原子操作候选：`mfq/m-analysis/candidate-ptm-atomic.yaml`
   - F 耦合因子候选：嵌入在 `mfq/f-analysis/coupling-test-points.md` 末尾的「耦合因子候选列表汇总」节
   - Q 质量因子候选：嵌入在 `mfq/q-analysis/quality-test-points.md` 末尾的「质量因子候选列表汇总」节
   - **若 M/F/Q 任一候选列表文件不存在，报错并终止：`<文件路径> 不存在，请先执行对应的分析器`**

按四级/五级目录归集所有来源的测试点：

```
模块 A
├── 子模块 A1
│   ├── TP-M-A1-001 (M分析)
│   ├── TP-M-A1-002 (M分析)
│   ├── TP-F-A1-B2-001 (F分析 - 与B2的耦合)
│   └── TP-Q-REL-001 (Q分析 - 可靠性)
└── 子模块 A2
    ├── TP-M-A2-001 (M分析)
    └── TP-Q-SEC-001 (Q分析 - 安全性)
```

归集时不得丢掉上游 trace；同一 TP 被多个场景、ptm-atomic 或 gap 触达时，取并集。

### 步骤 2：覆盖检查

**需求层覆盖**（逐条核验）：

| 检查项 | 方法 |
|--------|------|
| 每条 SR 至少 1 个测试点 | 遍历 SR 列表，检查 TP 的关联需求字段 |
| SR 描述的每个功能行为 | 逐条比对 SR 描述与 TP 描述的语义覆盖 |

**场景层覆盖**：
- 每个已确认场景的关键路径至少 1 个测试点
- `minimal_logic_chain` 中每个关键原子操作至少映射到 1 个 TP 或 1 个显式未覆盖项

**ptm-atomic 覆盖**：
- 每个 `action_source_ref` 至少落到 1 个 TP / LC / TD，或显式标注为 `仅场景存在，未形成测试资产`

**确认缺口覆盖**：
- 所有 `confirmation_gap_refs` 必须出现在 LC/TD 中，或在未覆盖清单中说明为何中止

**覆盖判定规则**（CF-05）：
- `新增用例`：必须设计用例的测试点
- `合并`：合并到某条逻辑用例中（注明合并目标）
- `不设计用例`：例外情况，应极少出现，需标注理由

**覆盖矩阵视角 A 检查（SR→TSP→TP 覆盖链）**：

从步骤 1 加载的覆盖矩阵视角 A（场景→TSP）表格中提取：

```
对每个场景的步骤段：
  ├── covered → 通过 TSP 链接到对应 TP，检查 TP 是否有覆盖该步骤段
  │   └── 预期：每个 covered 步骤段在步骤 5（测试数据归集）或步骤 7（覆盖矩阵输出）的追踪矩阵中有对应 TP
  ├── uncovered → 该步骤段在 scope 内但未被任何 TSP 覆盖
  │   └── 逐条列出缺口，检查是否在测试点生成或覆盖检查中被标记为 ⚠️ 待补充
  └── excluded → 显式排除（UI操作/超出 test_items/dont_test）
      └── 检查排除理由与 M 分析步骤 2 子步骤 D 的排除判定一致
```

输出：
- 覆盖矩阵覆盖率 = covered / (total - excluded)
- uncovered 步骤段与 TP 的缺口对照表

> 该检查追加在 SR→TP 覆盖检查之后，作为第二层覆盖验证：SR→TP 从需求视角验证，覆盖矩阵检查从场景步骤视角验证 TSP→TP 链。若覆盖矩阵未在步骤 1 中成功加载（文件不存在），则本步骤不可达（步骤 1 已 fail-fast 报错终止）。

### 步骤 3：CAE 聚合规则与逻辑用例生成

读取所有 CAE 格式的测试点，按以下规则聚合为逻辑用例（LC）：

#### 合并判定规则

按优先级从高到低依次检测，命中即停止：

| 优先级 | 规则编号 | 场景 | 判定条件 | 合并策略 |
|--------|---------|------|---------|---------|
| 1（最高）| **规则3-步骤序列** | 多个TP的A动作有明确先后依赖关系（如创建→修改→删除） | A动作间存在依赖链 | 合并为 1 个 LC；A动作按顺序构成动作路径 |
| 2 | **规则2-状态变体** | A动作相同，C条件是不同业务前置状态 | C中包含"对象处于状态X"等状态描述，状态互斥 | 合并为 1 个 LC；各状态作为因子取值 |
| 3 | **规则1-参数化** | A动作相同，C条件是同一参数的不同取值 | C中包含相同参数名，取值不同 | 合并为 1 个 LC；提取因子-取值表 |
| 4（最低）| **规则0-直接** | A动作完全不同（测试的功能无关） | 无法命中规则1~3 | 各自独立 LC（无聚合） |

> ⚠️ **优先级处理**：当一组 TP 同时满足多条规则时，取优先级最高的规则（规则3 > 规则2 > 规则1）。
> 合并时必须记录聚合规则来源（规则0/1/2/3），并标注合并来源 TP 列表。

聚合时必须同步合并：

- `source_tp_ids`
- `scenario_refs`
- `scenario_chain_refs`
- `action_source_refs`
- `knowledge_refs`
- `confirmation_gap_refs`
- `test_object_refs`
- `factor_refs`
- `trace_refs`
- `topology_refs`
- `topology_role_refs`
- `topology_binding_status`
- `topology_gap_refs`

### 步骤 3.5：组网绑定（来自 confirmed-scenarios.md）

每个 LC 必须固定输出 **组网绑定（来自 confirmed-scenarios.md）** 章节，绑定规则如下：

1. 从合并后的 TP `topology_role_refs` 收集本 LC 涉及的拓扑角色。
2. 按 `scenario_refs + topology_refs + topology_role_refs` 回查 `kym/scenarios/confirmed-scenarios.md` 中的 TOPO / 组网实例。
3. 为每个角色生成 `topology_bindings`，至少包含：

| 字段 | 说明 |
|------|------|
| `topology_binding_id` | LC 内唯一绑定编号 |
| `topology_role_ref` | 逻辑角色，如 `MATCH_INGRESS_IF` |
| `role_expression` | CAE 角色占位，如 `{{topo_role:MATCH_INGRESS_IF}}` |
| `topology_ref` | confirmed-scenarios.md 中 TOPO 实例引用 |
| `bound_object` | 真实组网对象，仅来自 confirmed-scenarios.md |
| `binding_source` | 回链位置，如 `confirmed-scenarios.md#TOPO-FLOW-001` |
| `binding_status` | `confirmed / needs-confirmation / unbound` |
| `confirmation_gap_refs` | 不唯一、缺失或冲突时的 gap |

4. 能唯一回链时，`binding_status=confirmed`，并在动作路径中使用“角色 + 绑定说明”，例如 `{{topo_role:MATCH_INGRESS_IF}}（绑定 TOPO-FLOW-001:DUT.port1）`。
5. 无法唯一绑定、绑定缺失或上游出现裸端口但无法回链时，保留 `binding_status=needs-confirmation`，把缺口并入 LC `confirmation_gap_refs` 与 `topology_gap_refs`。
6. 动作路径不得继承裸端口作为无来源文本；必须写角色占位和绑定说明，或写 `[拓扑绑定待确认: <gap_ref>]`。

### 步骤 4：逻辑用例结构化输出

每个逻辑用例按以下结构生成，按**四级目录（H2）→ 五级目录（H3）**分节：

```markdown
## <四级目录>

### <五级目录>

#### LC-<模块缩写>-<子模块缩写>-001：<逻辑用例标题>

**测试逻辑**：<简述验证什么功能以及覆盖哪类场景（正常/边界/异常）>

**因子-取值表（来自 C 条件）**：

| 因子（数据名称） | 取值列表 | 因子类型 | 等价类 |
|--------------|---------|---------|--------|
| 服务器数量 | 无服务器 | 环境状态 | 有效 |
| 服务器数量 | 配置5台（上限） | 环境状态 | 边界 |
| IP地址 | <IP_ADDRESS> | 参数 | 有效 |
| IP地址 | 256.0.0.1 | 参数 | 无效 |

**动作路径**：

- 路径 P1（唯一路径 / P-Parameter 时通常只有一条）：
  进入配置页面 → 填写参数 → 点击确定 → 观测响应和列表

**组网绑定（来自 confirmed-scenarios.md）**：

| topology_binding_id | topology_role_ref | role_expression | topology_ref | bound_object | binding_source | binding_status | confirmation_gap_refs |
|---------------------|-------------------|-----------------|--------------|--------------|----------------|----------------|-----------------------|
| TB-LC-001-01 | MATCH_INGRESS_IF | `{{topo_role:MATCH_INGRESS_IF}}` | TOPO-FLOW-001 | DUT.port1 | `confirmed-scenarios.md#TOPO-FLOW-001` | confirmed | — |
| TB-LC-001-02 | DUT_EGRESS_IF | `{{topo_role:DUT_EGRESS_IF}}` | TOPO-FLOW-001 | DUT.port2 | `confirmed-scenarios.md#TOPO-FLOW-001` | confirmed | — |

**trace refs**：

| 字段 | 内容 |
|------|------|
| `source_tp_ids` | TP-M-CFG-SRV-001, TP-M-CFG-SRV-002 |
| `scenario_refs` | SCN-LOG-001 |
| `scenario_chain_refs` | PRE-01, AO-01 |
| `action_source_refs` | fw_config_log_server |
| `knowledge_refs` | KR-001 |
| `confirmation_gap_refs` | GAP-001 |
| `test_object_refs` | OBJ-LOG-SERVER |
| `factor_refs` | FAC-IP, FAC-SERVER-COUNT |
| `topology_role_refs` | MATCH_INGRESS_IF, DUT_EGRESS_IF |
| `topology_refs` | TOPO-FLOW-001 |
| `topology_bindings` | TB-LC-001-01, TB-LC-001-02 |
| `topology_gap_refs` | GAP-TOPO-001 |

**覆盖测试点**：

| TP-ID | C 条件（关键） | A 动作（关键） | E 预期（关键） | 来源 | 测试类型 |
|-------|-------------|-------------|-------------|------|---------|
| TP-M-CFG-SRV-001 | 无服务器；合法IP/端口/协议 | 路径P1 | 正常创建 | M | 功能 |
| TP-M-CFG-SRV-002 | 已配置5台（上限） | 路径P1 | 创建失败 | M | 边界 |

**关联SR**：SR-001, SR-002
**PPDCS 特征**：P-Parameter（来自 ppdcs-annotation.md）
**CAE聚合规则**：规则1-参数化（来源TP：TP-M-CFG-SRV-001, TP-M-CFG-SRV-002）
**fact_status**：confirmed / needs-confirmation
```

> ⚠️ **完整性要求**：每个五级目录节点必须至少有一个逻辑用例覆盖，不允许跳过。

### 步骤 4.5：候选汇总与用户确认

⛔ **HARD-STOP（STOP-02）**：禁止 Agent 自行判定候选因子/原子操作为"全部确认"。必须展示候选汇总表，等待用户选择确认选项。候选表必须使用 `( )` 单选标记区分选项。

#### 4.5.1 三源候选归集

从以下路径读取候选列表（文件路径与步骤 1 中声明的候选列表路径一致）：

- M 因子候选：`mfq/m-analysis/candidate-factor-proposals.yaml`
- M 原子操作候选：`mfq/m-analysis/candidate-ptm-atomic.yaml`
- F 耦合因子候选：`mfq/f-analysis/coupling-test-points.md` 末尾「耦合因子候选列表汇总」节
- Q 质量因子候选：`mfq/q-analysis/quality-test-points.md` 末尾「质量因子候选列表汇总」节

若以上文件**全部不存在**，输出 `⚠️ Warning：无可候选汇总数据，跳过本步骤` 并继续步骤 5。
若部分文件存在但格式不一致，输出 Warning 并展示原始内容，继续流程。

##### 4.5.1.5 因子库反查去重

> 在去重合并之前，用公共因子库对候选因子做反查，消除因 m-analyzer 扫描遗漏导致的假阳性候选。

**反查逻辑**：

```
1. 重建因子库索引：
   a. 优先读取 mfq/m-analysis/factor-resolution-report.md 中的命中记录（含 N_scanned）
   b. 若 resolution-report 不可用 → 重建索引：
      读取 resource/factor-libraries/index.yaml → 遍历各库 factor-library.yaml → 构建 factor_id 索引
   c. 若 index.yaml 不可读 → ⚠️ Warning："无法读取因子库索引，跳过反查去重"，继续现有流程

2. 对每个候选因子执行反查：
   a. 在因子库索引中按 factor_id / factor_name / aliases 检索
   b. 命中（已在公共库中存在）：
      → 标记 "已在公共因子库中存在"（library_id + factor_id + match_confidence）
      → 优先级降级为 low，加入候选汇总时标记 [库中已存在]
      → 说明：该因子可能因 m-analyzer 扫描遗漏而被误标为候选
   c. 未命中 → 保留为候选，按现有优先级规则处理

3. 输出反查结果摘要：
   - 反查前候选数 / 反查命中数 / 反查后候选数
   - 命中明细：每个命中项的 candidate_id → library_id.factor_id → match_confidence
```

**反查后的处理**：

- 反查命中的候选仍展示在汇总表中，但标记为 `[库中已存在]` 且优先级为 low
- 用户可在 Step 4.5.3 确认时将其移除或拒绝
- 反查未命中的候选按现有流程进入优先级判定

##### 4.5.1.6 原子操作候选交叉验证

> 用 ptm-atomic CLI 对候选原子操作做反向查询，验证是否有已存在的操作可覆盖该候选。

**交叉验证逻辑**：

```
1. 读取候选列表：
   - M 原子操作候选：mfq/m-analysis/candidate-ptm-atomic.yaml

2. 若 ptm-atomic CLI 可用：
   a. 执行 ptm-atomic list --format json，获取全部操作的 op_id / description / tags / aliases
   b. 对每个候选原子操作：
      → 用 candidate_op_name 的分词在全部 op 的 op_id / description / tags / aliases 中做关键词匹配
      → aliases 字段由 ptm-atomic 仓库定义和维护，integrator 直接从 CLI 输出消费，不做本地映射
   c. 命中已有操作：
      → 标记 "已有原子操作可覆盖"（matched_op_id + match_source）
      → 优先级降级为 low，汇总时标记 [已有可覆盖]
      → 记录到 ptm-atomic-bindings.yaml
   c. 未命中 → 保留为候选，按现有流程处理

3. 若 CLI 不可用 → ⚠️ Warning："ptm-atomic CLI 不可用，跳过候选交叉验证"，继续
```

**交叉验证结果**：

- 写入 `mfq/ptm-atomic-usage/ptm-atomic-bindings.yaml`（命中绑定时）
- 交叉验证命中的候选仍展示在汇总表，标记为 `[已有可覆盖]` 且优先级 low

#### 4.5.2 去重合并与优先级判定

**因子候选去重**：

1. 以 `factor_id` 为主 key 合并因子候选；若 `factor_id` 缺失，以 `factor_name` 为 fallback key。
2. 同名但不同数据域（`data_domain`）的因子候选保留多条，标注差异。
3. 同名同数据域的因子候选合并为 1 条，`source` 字段记录所有来源分析器（如 `M, Q`）。
4. 同 key 条目在不同源中描述或取值域不同时，保留差异并标记 `[待用户裁决]`。

**原子操作候选去重**：

以 `candidate_op_name` 为 key 合并；当前仅 M 分析产出原子操作候选，暂不涉及跨源去重。

**优先级判定规则**：

| 条件 | 优先级 |
|------|:---:|
| M 分析来源，且 `relevance=high` / `priority=high` | **高** |
| F 分析来源，且标记为关键耦合（`coupling_strength=strong`） | **中** |
| Q 分析来源，且标记为强相关维度（`relevance=strong`） | **中** |
| M 分析来源，`relevance=medium` / `priority=medium` | **中** |
| M 分析来源，`relevance=low` / `priority=low` | **低** |
| F/Q 分析来源，非关键/非强相关 | **低** |

#### 4.5.3 用户批量确认

展示因子候选汇总表和原子操作候选汇总表后，输出确认选项。

**平台交互协议**：Claude Code 环境且 `AskUserQuestion` 可用时，优先使用结构化选择：
- question: "请确认候选汇总的处理方式："
- header: "Candidate act"
- multiSelect: false
- options:
  1. label: "Confirm all", description: "所有候选转为已确认，写入最终产物"
  2. label: "Item by item", description: "逐项标记确认/拒绝/修改，按项处理"
  3. label: "Batch modify", description: "提供修改意见，统一调整后确认"
  4. label: "Reject all", description: "丢弃所有候选，不写入最终产物"

Codex 或 `AskUserQuestion` 不可用时，回退到 STOP-05 文本标记：

```markdown
## 候选汇总确认

请选择以下操作之一：

( ) ✅ 全部确认 — 所有候选转为已确认，写入最终产物
( ) ✏️ 逐项确认 — 逐项标记确认/拒绝/修改，按项处理
( ) 📝 批量修改 — 提供修改意见，统一调整后确认
( ) ❌ 全部拒绝 — 丢弃所有候选，不写入最终产物
```

⛔ **HARD-STOP（STOP-02）**：禁止 Agent 自行判定。必须展示汇总表并等待用户选择。

#### 4.5.4 确认后回写

根据用户选择执行：

| 用户选择 | 执行动作 |
|---------|---------|
| ✅ 全部确认 | 所有候选 `decision=confirmed`，写入 `mfq/candidates/factor-candidates.md` 和 `mfq/candidates/ptm-atomic-candidates.md` |
| ✏️ 逐项确认 | 逐项标记 `confirmed` / `rejected` / `modified`（含修改后内容），确认项写入最终产物，拒绝项保留决定记录 |
| 📝 批量修改 | 收集用户修改意见，批量调整后展示更新汇总表，再次等待确认 |
| ❌ 全部拒绝 | 所有候选 `decision=rejected`，不写入最终产物，在汇总表中保留决定记录 |

写入前必须校验目标父目录 `mfq/candidates/` 存在且为目录（非普通文件）。若父目录不存在，输出错误信息并提示用户，禁止 Agent 手动 mkdir。

### 步骤 5：测试数据归集（Story-04 新增）

每个 LC 必须生成可追踪的测试数据条目（TD）：

| 字段 | 说明 |
|------|------|
| `TD-ID` | `TD-<模块缩写>-<子模块缩写>-NNN` |
| `logic_case_id` | 所属 LC |
| `factor_ref` | 对应 `factor_id` |
| `value_set` | 取值 / 边界 / 组合说明 |
| `source_section` | `condition / action-input / observation / environment` |
| `scenario_refs` | 来源场景 |
| `action_source_refs` | 关联 ptm-atomic `op_id` |
| `trace_refs` | 继承 LC trace |
| `confirmation_gap_refs` | 未确认边界 |
| `status` | `ready / needs-confirmation` |

若某测试数据只能写成 `[待确认]`，必须保留对应 `confirmation_gap_refs`，不得在 integrator 阶段自行定值。

### 步骤 6：工具分析归并（Story-04 新增）

汇总 `mfq/f-analysis/tool-analysis.md` 与 `mfq/q-analysis/tool-analysis.md`，
输出 renderer 可消费的统一结构，并保留上游原名；**标准化只能增补别名，不能丢字段**：

| 归并字段 | 说明 |
|------|------|
| `tool_entry_id` | `tool_id` 的统一别名 |
| `tool_id` | 保留上游原始 `tool_id` |
| `tool_kind` | `existing-tool / tool-gap` |
| `tool_name` | 工具名称 |
| `main_usage` | 已使用工具的主要用法 |
| `purpose` | 用途 |
| `scenario_refs` | 关联场景 |
| `action_source_refs` | 关联 ptm-atomic `op_id` |
| `factor_refs` | 关联因子 |
| `covered_objects` | 保留上游原始覆盖对象字段 |
| `covered_object_refs` | `covered_objects` 的统一别名 |
| `covered_factors` | 保留上游原始覆盖因子字段 |
| `covered_factor_refs` | `covered_factors` 的统一别名 |
| `proposed_interface` | 保留上游原始接口建议字段（tool-gap） |
| `interface_contract` | `proposed_interface / invoke_contract` 的统一别名 |
| `function_desc` | 功能说明 |
| `io_behavior_matrix` | 行为矩阵 |
| `output_contract` | 输出契约 |
| `status` | `ready / partial / gap / needs-confirmation` |

归并规则补充：

1. `tool_entry_id = tool_id`，但 `tool_id` 原字段必须继续输出，供 STORY-08 renderer 和人工审阅双向回链。
2. `covered_objects` 与 `covered_factors` 必须原样透传；如需便于统一命名，再分别补 `covered_object_refs / covered_factor_refs`，不得用 `test_object_refs / factor_refs` 覆盖上游工具覆盖语义。
3. `interface_contract` 仅是 `proposed_interface / invoke_contract` 的别名；若上游给出 `proposed_interface`，归并结果必须同时保留 `proposed_interface` 与 `interface_contract`。
4. `io_behavior_matrix`、`output_contract` 为工具 gap 的必保留字段；即使 `status=needs-confirmation` 也不得删列。
5. 若上游工具条目带不确定性，只能通过 `status=needs-confirmation` 保留显式不确定性，不能通过删除 `covered_*` 或 `io_behavior_matrix` 来弱化缺口。

### 步骤 7：覆盖矩阵输出

生成 `SR → Scenario → TP → LC → TD` 的追踪矩阵：

| SR | `scenario_refs` | TP-IDs | LC-ID | TD-IDs | `action_source_refs` | 覆盖状态 |
|----|-----------------|--------|-------|--------|----------------------|---------|
| SR-001 | SCN-LOG-001 | TP-M-CFG-SRV-001, TP-M-CFG-SRV-003 | LC-CFG-SRV-001 | TD-CFG-SRV-001, TD-CFG-SRV-002 | fw_config_log_server | ✅ |
| SR-002 | SCN-LOG-001 | TP-M-CFG-SRV-002 | LC-CFG-SRV-001 | TD-CFG-SRV-003 | fw_config_log_server | ✅ |

### 步骤 7.5：候选归集（为候选汇总阶段准备数据）

> 本步骤只做归集和去重，不附加"建议确认"、"推荐通过"等自行判定语句。候选状态保留上游标注（`new-candidate` / `new-coupling-candidate` / `new-quality-candidate`）。为 STORY-012-07 候选汇总提供输入数据。

**读取三源候选列表**：

1. **M 因子候选**：读取 `mfq/m-analysis/candidate-factor-proposals.yaml`，提取 `candidate_id / factor_name / data_domain / source / scenario_refs`
2. **M 原子操作候选**：读取 `mfq/m-analysis/candidate-ptm-atomic.yaml`，提取 `candidate_id / op_name / op_desc / related_object_id / scenario_refs`
3. **F 耦合因子候选**：从 `mfq/f-analysis/coupling-test-points.md` 末尾的「耦合因子候选列表汇总」节提取 `factor_id / factor_name / data_domain / tsp_ref / coupling_ref / source`
4. **Q 质量因子候选**：从 `mfq/q-analysis/quality-test-points.md` 末尾的「质量因子候选列表汇总」节提取 `factor_id / factor_name / data_domain / tsp_ref / quality_dimension / source / generation_basis`

**去重规则**：

- **因子候选去重**（来源：M/F/Q 三源）：去重 key = `factor_id`（优先）或 `factor_name`（fallback）。同名但不同数据域的因子候选保留多条，标注差异。同名同数据域的因子候选合并为 1 条，标注多来源（如 `M+F`）
- **原子操作候选去重**（来源：仅 M 分析）：去重 key = `candidate_id`。当前仅 M 分析产出原子操作候选，暂不涉及跨源去重

**输出**：

| 文件 | 内容 |
|------|------|
| `mfq/candidates/factor-candidates.md` | M/F/Q 三源因子候选合并（按 `factor_id` 去重），含 `候选ID / 因子名称 / 数据域 / 来源分析器（M/F/Q）/ 关联 TSP / 优先级 / 原始来源` |
| `mfq/candidates/ptm-atomic-candidates.md` | M 分析原子操作候选，含 `候选ID / 操作名称 / 操作描述 / 关联对象 / 关联场景` |

> 写入前必须校验目标父目录 `mfq/candidates/` 存在且为目录（STOP-04 规则）。禁止 Agent 手动 mkdir。

### 步骤 8：输出

写入以下文件：

| 文件 | 内容 |
|------|------|
| `mfq/integration/all-test-points.md` | M+F+Q 按四/五级目录归集的全量 CAE 测试点 |
| `mfq/integration/logic-cases.md` | 逻辑用例（按四/五级目录分节，含因子-取值表+组网绑定+动作路径+覆盖TP） |
| `mfq/integration/test-data.md` | TD 清单（含 factor/value/trace/gap） |
| `mfq/integration/tool-analysis.md` | 归并后的 Existing Tool Summary + Tool Capability Gap（renderer 别名已对齐） |
| `mfq/integration/coverage-matrix.md` | `SR→Scenario→TP→LC→TD` 的追踪矩阵 |
| `mfq/candidates/factor-candidates.md` | M/F/Q 三源因子候选归集（按 `factor_id` 去重，为候选汇总阶段准备数据） |
| `mfq/candidates/ptm-atomic-candidates.md` | 原子操作候选归集（为候选汇总阶段准备数据） |

> 写入前必须校验目标父目录存在且为目录（STOP-04 规则）。禁止 Agent 手动 mkdir。

## 输出格式参考

### all-test-points.md

```markdown
# <特性名> — 测试点整合表

## 统计

| 来源 | 测试点数 |
|------|---------|
| M 分析 | N |
| F 分析 | M |
| Q 分析 | K |
| 合计 | N+M+K |

## <四级目录>

### <五级目录>

| TP-ID | C 条件 | A 动作 | E 预期 | 来源 | `scenario_refs` | `action_source_refs` | `factor_refs` | `topology_role_refs` | `topology_refs` | `topology_binding_status` | `topology_gap_refs` | 归属LC |
|-------|--------|--------|--------|------|-----------------|----------------------|---------------|----------------------|-----------------|---------------------------|---------------------|--------|
| TP-M-CFG-SRV-001 | 无服务器；合法参数 | 新建表单填写参数，点击确定 | 创建成功；列表新增条目 | M | SCN-LOG-001 | fw_config_log_server | FAC-IP,FAC-PORT | — | — | — | — | LC-CFG-SRV-001 |
| TP-M-FLOW-001 | `{{topo_role:MATCH_INGRESS_IF}}` 进入匹配流量 | 发送 TCP/443 报文 | `{{topo_role:DUT_EGRESS_IF}}` 转发 | M | SCN-FLOW-001 | fw_send_match_traffic | FAC-PROTO,FAC-DST-PORT | MATCH_INGRESS_IF,DUT_EGRESS_IF | TOPO-FLOW-001 | confirmed | — | LC-FLOW-001 |
```

### test-data.md

```markdown
# <特性名> — 测试数据归集表

| TD-ID | logic_case_id | factor_ref | value_set | scenario_refs | action_source_refs | confirmation_gap_refs | status |
|-------|---------------|------------|-----------|---------------|--------------------|-----------------------|--------|
| TD-CFG-SRV-001 | LC-CFG-SRV-001 | FAC-IP | `<IP_ADDRESS>` / `256.0.0.1` | SCN-LOG-001 | fw_config_log_server | — | ready |
| TD-CFG-SRV-002 | LC-CFG-SRV-001 | FAC-SERVER-COUNT | `0 / 5 / >5[待确认]` | SCN-LOG-001 | fw_config_log_server | GAP-001 | needs-confirmation |
```

### tool-analysis.md

```markdown
# <特性名> — 工具分析归并

| tool_entry_id | tool_id | tool_kind | tool_name | main_usage | purpose | scenario_refs | action_source_refs | factor_refs | covered_objects | covered_object_refs | covered_factors | covered_factor_refs | proposed_interface | interface_contract | function_desc | io_behavior_matrix | output_contract | status |
|---------------|---------|-----------|-----------|------------|---------|---------------|--------------------|-------------|-----------------|---------------------|-----------------|---------------------|--------------------|--------------------|---------------|--------------------|-----------------|--------|
| TOOL-001 | TOOL-001 | existing-tool | log-cli | `log-cli server add/delete` | 配置日志服务器 | SCN-LOG-001 | fw_config_log_server | FAC-IP,FAC-PORT | OBJ-LOG-SERVER | OBJ-LOG-SERVER | FAC-IP,FAC-PORT | FAC-IP,FAC-PORT | — | `log-cli server <subcommand>` | 已覆盖新增/删除/查询 | — | stdout/json + return code | ready |
| GAP-TOOL-001 | GAP-TOOL-001 | tool-gap | audit-exporter | — | 导出审计时间线 | SCN-AUDIT-001 | fw_export_audit_timeline | FAC-AUDIT-FIELD,FAC-AUDIT-TIMELINE | OBJ-AUDIT-LOG | OBJ-AUDIT-LOG | FAC-AUDIT-FIELD,FAC-AUDIT-TIMELINE | FAC-AUDIT-FIELD,FAC-AUDIT-TIMELINE | `audit-exporter trace --since ...` | `audit-exporter trace --since ...` | 补齐审计观测能力 | 指定时间窗且日志可读→返回完整时间线；字段缺失→返回缺失字段清单与失败状态 | stdout/json + timeline report | gap |
```

## 公共因子库补充契约

- integrator 必须消费并透传上游 `factor_bindings`，不能只合并 `factor_refs`。
- `factor_bindings` 是主契约，必须保留 `library_id / version或snapshot_id / factor_id_or_group_id / role / binding_mode / usage_context / sample_id / expr / materialized_stage / gap`。
- `factor_refs` 只作为兼容摘要，不得覆盖或替换 binding。
- 生成 LC 和 TD 时必须保留 `usage_context` 与 `sample_id`，不得在 integration 阶段提前物化随机表达式。
- 配置样本和功能样本分开合并；`rejected_config_samples` 不得作为功能用例前置。

## 拓扑绑定补充契约

- integrator 必须消费并透传上游 `topology_refs / topology_role_refs / topology_binding_status / topology_gap_refs`。
- `topology_bindings` 是与 `factor_bindings` 并行的主契约；不得把拓扑角色或真实组网对象写入 `factor_bindings`。
- `topology_bindings` 只能绑定到 `kym/scenarios/confirmed-scenarios.md` 的 TOPO 实例；无法唯一绑定时保留 `needs-confirmation`，并写入 `confirmation_gap_refs`。
- LC 动作路径必须使用拓扑角色和绑定说明，不得输出无来源裸端口。

## Gotchas

- 覆盖检查必须是逐条语义对比，不能只看编号关联
- 合并时注意保留所有来源的追踪关系
- F 分析的耦合测试点可能跨模块，需要决定归属到哪个模块
- Q 分析的测试点可能适用于多个模块，需在每个相关模块都有体现
- integrator 不得吞掉 `confirmation_gap_refs`
- 工具分析只做归并和字段对齐，不补写上游没有给出的接口/行为
- 组网绑定只来自 confirmed-scenarios.md；不要用端口命名习惯或场景标题推断 DUT/TG 真实接口
- 裸端口不是 LC 因子值；发现后应转成 topology gap，而不是放入因子-取值表
- 覆盖矩阵（`scenario-tsp-coverage.md`）不存在时，步骤 1 报错终止（fail-fast），不静默跳过
- 候选归集步骤只做归集和去重，不附加"建议确认"、"推荐通过"等自行判定语句；候选状态保留上游标注
- 候选汇总步骤（步骤 4.5）受 STOP-02 硬停止约束：禁止 Agent 自行判定全部确认或跳过用户确认交互；必须展示汇总表并等待用户选择后执行
- 候选汇总确认后写入 `mfq/candidates/` 前必须校验父目录存在且为目录（STOP-04）；禁止 Agent 手动 mkdir

## 验收标准

- [ ] M+F+Q 测试点全部归集且无遗漏
- [ ] 需求覆盖率 = 100%（所有 SR 至少 1 个 TP）
- [ ] 每个逻辑用例包含：测试逻辑描述 + 因子-取值表 + 动作路径 + 覆盖测试点明细
- [ ] 每个逻辑用例固定包含 `组网绑定（来自 confirmed-scenarios.md）` 章节；无组网约束时显式写 `无`
- [ ] 每个 LC 保留 `source_tp_ids / scenario_refs / action_source_refs / factor_bindings / factor_refs / topology_bindings / topology_role_refs / topology_refs / trace_refs`
- [ ] 每个 TD 保留 `factor_ref / scenario_refs / action_source_refs / confirmation_gap_refs`
- [ ] 无法唯一绑定的拓扑角色保留 `needs-confirmation` 与 `confirmation_gap_refs`
- [ ] LC 因子-取值表和 TD `value_set` 不包含 `DUT.port*`、`TG.port*` 或 link 实例
- [ ] 输出按四/五级目录分节，每个五级目录至少有 1 个逻辑用例
- [ ] 合并判定表含优先级列和规则编号（规则0~规则3）
- [ ] 规则优先级明确：规则3 > 规则2 > 规则1
- [ ] 每个 LC 包含 `CAE聚合规则` 标注（规则0-直接 / 规则1-参数化 / 规则2-状态变体 / 规则3-步骤序列）
- [ ] 输出 `tool-analysis.md`，字段可直接被 STORY-08 renderer 消费
- [ ] 追踪矩阵 `SR→Scenario→TP→LC→TD` 链路完整
- [ ] 输出文件写入 `mfq/integration/` 和 `mfq/candidates/`
- [ ] 覆盖矩阵被正确消费（步骤 1 加载 + 步骤 2 视角 A 检查）
- [ ] M/F/Q 三源候选列表被正确归集和去重（步骤 7.5）
- [ ] 覆盖矩阵或候选文件缺失时报错终止（fail-fast），不静默降级
