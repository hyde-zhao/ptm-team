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
- 输入：`analysis/m-analysis/` + `analysis/f-analysis/` + `analysis/q-analysis/`
- 输出：`analysis/integration/` 目录下多个文件

## 前置条件

- [ ] M 分析完成（`analysis/m-analysis/test-points.md` 存在）
- [ ] F 分析完成（`analysis/f-analysis/coupling-test-points.md` 存在）
- [ ] Q 分析完成（`analysis/q-analysis/quality-test-points.md` 存在）
- [ ] 上游 TP 已包含 `trace_refs / scenario_refs / action_source_refs / test_object_refs / factor_refs`
- [ ] 上游工具评估文件存在，或明确标记为“无工具分析结果”

## 输入契约（Story-04）

integrator 必须消费并透传以下字段：

| 来源 | 必收字段 |
|------|----------|
| M/F/Q TP | `trace_refs`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `knowledge_refs`, `confirmation_gap_refs`, `test_object_refs`, `factor_refs`, `fact_status` |
| M 对象/因子 | `object_id`, `factor_id`, `data_domain`, `related_object_id` |
| F/Q 工具评估 | `Existing Tool Summary`, `Tool Capability Gap` |
| 场景链 | `minimal_logic_chain`, `atomic-ops`, `Knowledge Reference`, `confirmation_gaps` |

## 执行流程

### 步骤 1：测试点归集

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

归集时不得丢掉上游 trace；同一 TP 被多个场景、atomic-ops 或 gap 触达时，取并集。

### 步骤 2：覆盖检查

**需求层覆盖**（逐条核验）：

| 检查项 | 方法 |
|--------|------|
| 每条 SR 至少 1 个测试点 | 遍历 SR 列表，检查 TP 的关联需求字段 |
| SR 描述的每个功能行为 | 逐条比对 SR 描述与 TP 描述的语义覆盖 |

**场景层覆盖**：
- 每个已确认场景的关键路径至少 1 个测试点
- `minimal_logic_chain` 中每个关键原子操作至少映射到 1 个 TP 或 1 个显式未覆盖项

**atomic-ops 覆盖**：
- 每个 `action_source_ref` 至少落到 1 个 TP / LC / TD，或显式标注为 `仅场景存在，未形成测试资产`

**确认缺口覆盖**：
- 所有 `confirmation_gap_refs` 必须出现在 LC/TD 中，或在未覆盖清单中说明为何中止

**覆盖判定规则**（CF-05）：
- `新增用例`：必须设计用例的测试点
- `合并`：合并到某条逻辑用例中（注明合并目标）
- `不设计用例`：例外情况，应极少出现，需标注理由

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
| `action_source_refs` | 关联 atomic-ops `op_id` |
| `trace_refs` | 继承 LC trace |
| `confirmation_gap_refs` | 未确认边界 |
| `status` | `ready / needs-confirmation` |

若某测试数据只能写成 `[待确认]`，必须保留对应 `confirmation_gap_refs`，不得在 integrator 阶段自行定值。

### 步骤 6：工具分析归并（Story-04 新增）

汇总 `analysis/f-analysis/tool-analysis.md` 与 `analysis/q-analysis/tool-analysis.md`，
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
| `action_source_refs` | 关联 atomic-ops `op_id` |
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

### 步骤 8：输出

写入 `analysis/integration/` 目录：

| 文件 | 内容 |
|------|------|
| `all-test-points.md` | M+F+Q 按四/五级目录归集的全量 CAE 测试点 |
| `logic-cases.md` | 逻辑用例（按四/五级目录分节，含因子-取值表+动作路径+覆盖TP） |
| `test-data.md` | TD 清单（含 factor/value/trace/gap） |
| `tool-analysis.md` | 归并后的 Existing Tool Summary + Tool Capability Gap（renderer 别名已对齐） |
| `coverage-matrix.md` | `SR→Scenario→TP→LC→TD` 的追踪矩阵 |

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

| TP-ID | C 条件 | A 动作 | E 预期 | 来源 | `scenario_refs` | `action_source_refs` | `factor_refs` | 归属LC |
|-------|--------|--------|--------|------|-----------------|----------------------|---------------|--------|
| TP-M-CFG-SRV-001 | 无服务器；合法参数 | 新建表单填写参数，点击确定 | 创建成功；列表新增条目 | M | SCN-LOG-001 | fw_config_log_server | FAC-IP,FAC-PORT | LC-CFG-SRV-001 |
| TP-M-CFG-SRV-002 | 已配置5台（上限） | 新建第6台，点击确定 | 提示超出上限；创建失败 | M | SCN-LOG-001 | fw_config_log_server | FAC-SERVER-COUNT | LC-CFG-SRV-001 |
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

## Gotchas

- 覆盖检查必须是逐条语义对比，不能只看编号关联
- 合并时注意保留所有来源的追踪关系
- F 分析的耦合测试点可能跨模块，需要决定归属到哪个模块
- Q 分析的测试点可能适用于多个模块，需在每个相关模块都有体现
- integrator 不得吞掉 `confirmation_gap_refs`
- 工具分析只做归并和字段对齐，不补写上游没有给出的接口/行为

## 验收标准

- [ ] M+F+Q 测试点全部归集且无遗漏
- [ ] 需求覆盖率 = 100%（所有 SR 至少 1 个 TP）
- [ ] 每个逻辑用例包含：测试逻辑描述 + 因子-取值表 + 动作路径 + 覆盖测试点明细
- [ ] 每个 LC 保留 `source_tp_ids / scenario_refs / action_source_refs / factor_refs / trace_refs`
- [ ] 每个 TD 保留 `factor_ref / scenario_refs / action_source_refs / confirmation_gap_refs`
- [ ] 输出按四/五级目录分节，每个五级目录至少有 1 个逻辑用例
- [ ] 合并判定表含优先级列和规则编号（规则0~规则3）
- [ ] 规则优先级明确：规则3 > 规则2 > 规则1
- [ ] 每个 LC 包含 `CAE聚合规则` 标注（规则0-直接 / 规则1-参数化 / 规则2-状态变体 / 规则3-步骤序列）
- [ ] 输出 `tool-analysis.md`，字段可直接被 STORY-08 renderer 消费
- [ ] 追踪矩阵 `SR→Scenario→TP→LC→TD` 链路完整
- [ ] 输出文件写入 `analysis/integration/`
