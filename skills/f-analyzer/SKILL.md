---
name: f-analyzer
description: >-
  F 分析（功能交互/耦合分析）：三源合并耦合关系（Excel 矩阵 + 场景耦合 + 代码依赖），
  构建内存图模型，生成耦合测试点。
  触发词包括：F分析、耦合分析、耦合矩阵、特性交互、功能耦合。
  适用场景：MFQ 分析的第四步（f-analysis 阶段）。
argument-hint: "可选：耦合矩阵 Excel 路径"
user-invokable: true
status: active
---

## 目标

从三个数据源收集耦合关系，构建内存图模型，分析当前特性与其他特性/模块的交互点，
生成带 trace chain v6 的耦合测试点，并对耦合场景涉及的现有工具/动作源进行覆盖性评估。
新发现的耦合点经用户确认后可回写到耦合矩阵。

## 适用范围

- 适用阶段：MFQ 分析的 f-analysis 阶段
- 输入：`analysis/m-analysis/` + `analysis/scenarios/confirmed-scenarios.md` + `input/` 中的耦合矩阵 / 外部配置
- 输出：`analysis/f-analysis/` 目录下多个文件（含耦合测试点与工具评估）

## 前置条件

- [ ] M 分析已完成（`analysis/m-analysis/test-points.md` 存在）
- [ ] `analysis/m-analysis/test-objects-factors.md` 可用，或 TP 中已包含 `test_object_refs / factor_refs`
- [ ] `analysis/scenarios/confirmed-scenarios.md` 存在
- [ ] `scripts/excel_coupling_tool.py` 可用
- [ ] 上游 `confirmation_gaps` 已区分“允许透传”与“必须回退确认”

## 三源数据模型

### 源 1：Excel 矩阵基线（最低基线）

调用 Excel 工具读取耦合矩阵：

```bash
python scripts/excel_coupling_tool.py read "<excel_path>" --output "analysis/f-analysis/coupling-graph.json"
```

从中提取当前特性相关的耦合关系：

```bash
python scripts/excel_coupling_tool.py query "analysis/f-analysis/coupling-graph.json" --feature "<特性名>"
```

### 源 2：场景耦合推理

从已确认的应用场景中推理功能交互：

1. 读取 `analysis/scenarios/confirmed-scenarios.md`
2. 分析每个场景的 `precondition_operations / atomic_operations / minimal_logic_chain`
3. 将 `action_source_refs / knowledge_refs / confirmation_gap_refs` 一并纳入耦合边上下文
4. 如果一个场景跨越多个模块/特性，则这些模块/特性之间存在场景耦合

推理规则：
- 场景处理逻辑中依次经过的功能模块 → 顺序耦合
- 场景异常路径涉及的故障隔离 → 容错耦合
- 场景数据在模块间的传递 → 数据耦合
- 不同原子操作共享同一 `action_source_ref` 或同一测试对象/因子 → 接口/资源耦合

### 源 3：代码依赖（首版简化）

首版通过手动输入接口，由用户或开发人员提供代码级别的依赖关系：

```
请提供当前特性代码中依赖的其他特性/模块的接口列表（可选，首版非必填）：
```

## 执行流程

### 步骤 1：矩阵基线读取

1. 查找耦合矩阵 Excel 文件（用户提供或从配置获取）
2. 调用 `excel_coupling_tool.py read` 生成图模型
3. 调用 `excel_coupling_tool.py query` 提取当前特性耦合点
4. 记录基线耦合点数量

### 步骤 2：场景耦合推理

1. 读取已确认场景
2. 按推理规则生成候选耦合边
3. 为每条候选边补充：
   - `scenario_refs`
   - `scenario_chain_refs`
   - `action_source_refs`
   - `knowledge_refs`
   - `confirmation_gap_refs`
   - `test_object_refs / factor_refs`
4. 标注来源为 `scenario-coupling`

### 步骤 3：代码依赖收集（可选）

1. 提示用户输入代码依赖（如有）
2. 将输入转换为耦合边
3. 标注来源为 `code-dependency`

### 步骤 4：三源合并

合并规则：
1. 以 `(source_feature, target_feature)` 为 key 去重
2. 相同功能点对的多源耦合合并，保留所有来源标注
3. 耦合强度取最高值（strong > normal > weak）
4. `confirmation_gap_refs` 取并集；存在 gap 时不允许把耦合描述提升为“已确认事实”

输出合并后的图模型到 `analysis/f-analysis/coupling-graph.yaml`

### 步骤 5：候选耦合点确认

将新发现的耦合点（不在矩阵基线中的）呈现给用户，使用 `ask_user` 工具发起结构化确认：

```
## 新发现的耦合关系

| # | 当前特性模块 | 耦合目标 | 耦合类型 | 来源 | 描述 |
|---|------------|---------|---------|------|------|
| 1 | ... | ... | 场景耦合 | SCN-001 | ... |
| 2 | ... | ... | 代码依赖 | 用户输入 | ... |
```

**ask_user 选项**：
1. ✅ 全部确认成立 — 所有新耦合关系有效，继续生成耦合测试点，并询问是否回写矩阵
2. ✏️ 部分确认 — 请指出不成立的耦合关系编号，其余确认成立
3. ❌ 全部不成立 — 新发现的耦合关系均不成立，跳过回写，仅使用基线矩阵

### 步骤 6：耦合测试点生成

对每个已确认或允许带 gap 透传的耦合关系，生成 CAE + trace 格式的耦合测试点：

| 字段 | 说明 |
|------|------|
| TP-ID | `TP-F-<源模块缩写>-<目标缩写>-NNN` |
| 所属模块 | 四级目录（归属当前特性的模块） |
| 所属子模块 | 五级目录 |
| C 条件 | 触发耦合交互的前置状态和环境条件（含耦合目标的前置状态；多个用"；"分隔） |
| A 动作 | 施加的操作（操作当前特性，触发耦合效果；不得直接操作耦合目标） |
| E 预期 | 可观测的耦合行为预期（包含对耦合目标的影响） |
| 来源 | matrix-baseline / scenario-coupling / code-dependency |
| 耦合强度 | strong / normal / weak |
| `scenario_refs` | 来源场景 |
| `scenario_chain_refs` | 涉及的 PRE / AO / 最小逻辑链节点 |
| `action_source_refs` | 关联动作源 |
| `knowledge_refs` | 支撑耦合判断的知识引用 |
| `confirmation_gap_refs` | 未确认事实引用 |
| `test_object_refs` | 被影响对象 |
| `factor_refs` | 关键耦合因子 |
| `trace_refs` | 汇总 trace |
| `fact_status` | `confirmed / needs-confirmation` |

**CAE 字段约束（耦合测试点）**：
- C：包含触发耦合交互的前置状态和环境条件（含耦合目标的前置状态）
- A：操作当前特性（触发耦合效果），不得直接操作耦合目标
- E：包含耦合目标的可观测行为；E="待定" 时须附批注 `[待定原因: <如"被耦合目标行为规格待确认">]`
- 如耦合判断依赖 `Knowledge Reference=missing/unavailable` 或 `Action Source=gap/unknown`，必须保留原状态并标记 `fact_status=needs-confirmation`

### 步骤 7：工具覆盖评估（Story-04 新增）

对每个耦合测试点，评估现有工具/动作源是否能够：

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
| `action_source_refs` | 依赖的动作源 |
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
| `action_source_refs` | 关联动作源 |
| `factor_refs` | 关联因子 |
| `status` | `gap / needs-confirmation` |

> `Tool Capability Gap` 同样必须保留以上原名字段，供 integrator 在保留原名的同时生成标准化别名；不得仅保留说明性文字而省略 `covered_objects / covered_factors / io_behavior_matrix`。

### 步骤 8：可选回写

若步骤 5 中用户选择了"全部确认成立"或"部分确认"，使用 `ask_user` 询问是否回写矩阵：

**ask_user 选项**：
1. ✅ 同意回写 — 将已确认的新耦合点写入 Excel 耦合矩阵
2. ❌ 暂不回写 — 本次仅用于测试点生成，不更新矩阵基线

若用户同意回写，执行：

```bash
python scripts/excel_coupling_tool.py write "<excel_path>" --source "analysis/f-analysis/new-coupling-points.json"
```

## 输出文件

> 追踪链：`SR → Scenario Chain → Action Source / Knowledge Reference → TP-F(CAE + coupling trace) → LC → Test Data → PC`

| 文件 | 说明 |
|------|------|
| `analysis/f-analysis/coupling-graph.json` | 完整图模型（所有源合并后） |
| `analysis/f-analysis/matrix-baseline.yaml` | Excel 矩阵基线摘要 |
| `analysis/f-analysis/coupling-test-points.md` | F 分析产出的耦合测试点（CAE+trace，按四/五级目录分节） |
| `analysis/f-analysis/tool-analysis.md` | Existing Tool Summary + Tool Capability Gap |
| `analysis/f-analysis/new-coupling-points.json` | 新发现的耦合点（用于回写） |

**`coupling-test-points.md` 输出格式**：

```markdown
# <特性名> — F 分析耦合测试点

## <四级目录>

### <五级目录>

| TP-ID | C 条件 | A 动作 | E 预期 | `scenario_refs` | `action_source_refs` | `factor_refs` | 来源 | 耦合强度 |
|-------|--------|--------|--------|-----------------|----------------------|---------------|------|---------|
| TP-F-CFG-BCK-001 | 日志归并功能已开启；日志服务器已配置 | 删除已配置的日志服务器 | 日志归并功能不受影响；归并日志继续正常记录 | SCN-LOG-001 | AS-DEL-001 | FAC-SERVER-STATE | matrix-baseline | strong |
```

**`tool-analysis.md` 输出格式**：

```markdown
# <特性名> — F 分析工具覆盖评估

## Existing Tool Summary

| tool_id | tool_name | main_usage | purpose | scenario_refs | action_source_refs | covered_objects | covered_factors | status |
|---------|-----------|------------|---------|---------------|--------------------|-----------------|-----------------|--------|
| TOOL-001 | log-cli | `log-cli server delete --id ...` | 删除日志服务器以触发耦合 | SCN-LOG-001 | AS-DEL-001 | OBJ-LOG-SERVER | FAC-SERVER-ID | ready |

## Tool Capability Gap

| tool_id | tool_name | covered_objects | covered_factors | missing_ops | proposed_interface | function_desc | io_behavior_matrix | output_contract | scenario_refs | action_source_refs | factor_refs | status |
|---------|-----------|-----------------|-----------------|-------------|--------------------|---------------|--------------------|-----------------|---------------|--------------------|-------------|--------|
| GAP-TOOL-001 | traffic-injector | OBJ-PEER-ALARM | FAC-ALARM-TYPE,FAC-ALARM-TIMELINE | 观测对端告警联动 | CLI: `traffic-injector observe --target ...` | 输出耦合告警状态与时间线 | 目标可达→返回告警状态与时间线；目标不可达→返回不可观测原因与错误码 | stdout/json + return code + alarm timeline | SCN-LOG-001 | AS-OBS-001 | FAC-ALARM-TYPE,FAC-ALARM-TIMELINE | gap |
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
- 工具评估只基于已给定 Action Source / Existing Tool Usage Seed / Tool Draft，不能自行发明现有工具能力

## 验收标准

- [ ] Excel 矩阵基线已成功读取
- [ ] 场景耦合推理已执行
- [ ] 三源合并后无重复耦合边
- [ ] 新耦合点已呈现给用户并获得确认
- [ ] 耦合测试点包含完整 CAE 三字段（C/A/E 均不为空）
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 每个 TP-F 包含 `scenario_refs / action_source_refs / factor_refs / trace_refs`
- [ ] 工具评估输出 `Existing Tool Summary` 和 `Tool Capability Gap`
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式保留
- [ ] 输出文件按四/五级目录分节，格式符合规范
- [ ] 输出文件写入 `analysis/f-analysis/`
