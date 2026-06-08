---
name: deliverable-renderer
description: >-
  将 MFQ 分析、完整 PPDCS 设计过程和覆盖结果渲染为最终交付物，
  输出四份 Markdown：测试方案、测试用例、原子操作候选对比表、测试因子候选对比表。
  触发词包括：生成交付物、输出文档、测试方案、测试用例文档。
  适用场景：MFQ 分析的 delivery 阶段。
argument-hint: "特性名称"
user-invokable: true
status: active
---

## 目标

读取 `kym/`、`mfq/`、`ppdcs/ppdcs/`、`ppdcs/pc/`、`ppdcs/coverage/` 产物，通过 `ppdcs/delivery/` 形成交付闭环：

1. `<特性名>特性测试方案.md`
2. `<特性名>特性测试用例.md`

渲染时必须：

- 消费 `ppdcs/ppdcs/` 和 `ppdcs/pc/` 的**每 LC 单文件过程工件**，不能只看最终 PC；
- 保留 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `topology_role_refs`, `topology_bindings`, `topology_role`, `source`, `confirmation_gap_refs`, `fact_status`；
- 当上游存在 `topology_ref` 时，在测试方案的场景章节中保留对应组网引用与产物路径，并在测试用例中保留角色到真实设备/端口/链路的绑定来源。

## 适用范围

- 适用阶段：MFQ 的 delivery 阶段
- 输入：`mfq/integration/`、`ppdcs/coverage/`、`ppdcs/ppdcs/`、`ppdcs/pc/`
- 输出：`ppdcs/delivery/`

## 前置条件

- [ ] 覆盖报告已生成
- [ ] `logic-cases.md`、`test-data.md` 已存在
- [ ] `kym/scenarios/confirmed-scenarios.md` 已存在；依赖组网的 LC 已有 `topology_bindings`
- [ ] `ppdcs/ppdcs/` 与 `ppdcs/pc/` 下各 LC 单文件已存在
- [ ] 上游已保留 trace / gap / topology / fact_status 字段

## 必须消费的输入契约

### 1. 覆盖与整合层

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `coverage-summary.md` / `requirement-coverage.md` / `test-point-coverage.md` | 覆盖统计、`requirement_gaps`, `test_point_gaps`, `feature_tags`, `trace_refs`, `fact_status` | 方案文档中的覆盖章节 |
| `kym/scenarios/confirmed-scenarios.md` | `scenario_id`, `topology_ref`, `topology_role`, `device_id`, `port_id`, `link_id`, `source`, `fact_status` | 方案场景章节和真实组网来源 |
| `all-test-points.md` | `TP-ID`, `关联SR`, `scenario_refs`, `action_source_refs`, `factor_refs`, `topology_role_refs`, `trace_refs`, `fact_status` | 测试点分析表 |
| `logic-cases.md` | `LC-ID`, `source_tp_ids`, `关联SR`, `scenario_refs`, `scenario_chain_refs`, `action_source_refs`, `factor_refs`, `topology_role_refs`, `topology_bindings`, `topology_binding_status`, `trace_refs`, `confirmation_gap_refs`, `fact_status`, `动作路径`, `因子-取值表`, `CAE聚合规则` | 交付主骨架与拓扑绑定表 |
| `test-data.md` | `TD-ID`, `logic_case_id`, `factor_ref`, `value_set`, `topology_binding_refs`, `trace_refs`, `confirmation_gap_refs`, `status` | 设计过程与数据回链 |

### 2. STORY-06 / STORY-07 设计层（必须全量消费）

| 来源 | 必收字段 | 用途 |
|------|----------|------|
| `ppdcs/ppdcs/<basename>.md` | 推荐方法、图/规则/等价类/组合/状态迁移、覆盖策略、触发数据、`topology_role_refs`, `topology_binding_refs`, `trace_refs`, `scenario_refs`, `action_source_refs`, `confirmation_gap_refs`, `fact_status` | 渲染完整 PPDCS 设计过程 |
| `ppdcs/pc/<basename>.md` | `physical_case_id`, `logic_case_id`, `requirement_ids`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_refs`, `topology_bindings`, `topology_role`, `source`, `confirmation_gap_refs`, `fact_status` | 渲染最终物理用例 |

> 若某 PC 缺少 `feature_tags` 或某 LC 无法回链到 `requirement_ids / trace_refs`，renderer 必须在交付物中显式暴露缺口，不得自行脑补。
> 若某 PC 使用真实端口但无法回链到 LC `topology_bindings` 和 `confirmed-scenarios.md`，renderer 必须保留为 `needs-confirmation`，不得把该端口展示为因子或确认事实。

## 执行流程

### 步骤 0：交付确认（HARD-STOP）

⛔ 在渲染交付物之前，必须使用 `AskUserQuestion` 发起交付确认。禁止跳过此步骤直接生成文件。

**AskUserQuestion 参数**：

- `question`: "确认生成 ptm-tde 默认交付物？"
- `header`: "Delivery"
- `multiSelect`: false（单选）
- `options`:
  1. `label`: "全部生成", `description`: "测试方案 + 测试用例 + 原子操作候选对比表 + 测试因子候选对比表"

> 如需排除某项，用户可选中后通过 Other 输入"修改: 仅生成测试方案"等。

⛔ **禁止将以下中间产物作为交付选项**：
- "逻辑用例文档" — `mfq/integration/` 中的中间产物，其内容已包含在测试用例中
- "覆盖率报告" — `ppdcs/coverage/` 中的中间产物，其摘要已包含在测试方案中
- 原始候选 YAML — 原子操作和测试因子候选应加工为对比表后交付，不应直接输出原始 YAML

**AskUserQuestion 不可用时的回退文本**：

```
## 交付确认

ptm-tde 默认交付物：特性测试方案 + 特性测试用例 + 原子操作候选对比表 + 测试因子候选对比表

回复 "approve" 确认全部生成，或 "修改: 仅生成测试方案" 调整。
```

### 步骤 1：装配交付基线

1. 读取覆盖报告；
2. 读取 `mfq/integration/logic-cases.md`、`mfq/integration/test-data.md`；
3. 枚举 `ppdcs/ppdcs/*.md` 与 `ppdcs/pc/*.md`；
4. 按相同 basename 建立 `LC → PPDCS过程 → PC` 的完整映射；
5. 建立 `topology_role_refs → topology_bindings → PC materialization` 的回链；
6. 为每个 PC 汇总可直接进入交付文档的字段。

### 步骤 2：渲染 `<特性名>特性测试方案.md`

测试方案至少包含：

1. 特性概述
2. 应用场景分析
   - 若存在 Topology，列出 `topology_ref` 与 `kym/scenarios/<scene-id>/topology.{mmd,yaml}` 引用
   - 列出 `topology_role`、真实设备/端口/链路绑定、`source`、`fact_status`，并标明未确认绑定
3. 需求分析
4. M 分析
5. F 分析
6. Q 分析
7. 测试点整合
8. 覆盖率报告

覆盖章节必须区分：

- 需求层覆盖
- 测试点层覆盖
- 未覆盖项 / `needs-confirmation` 项
- topology binding gaps / 未确认真实组网对象

### 步骤 3：渲染 `<特性名>特性测试用例.md`

#### 3a. 统一 PC 汇总表（全文最前）

从所有 `ppdcs/pc/*.md` 中提取 PC 行，合并为一张 **16 列统一汇总表**（全文仅此一张 PC 表）。汇总表放在追踪链总览之后、各 LC 详情之前。

```
| 三级目录 | 四级目录 | 五级目录 | 用例名称* | 用例编号 | 用例级别* | 组网描述* | 组网约束 | 预置条件 | 测试步骤* | 预期结果* | 首次创建版本* | 最后变更版本 | 关键词 | 测试类型* | 是否自动化* |
```

**汇总规则**：

1. 遍历 `ppdcs/pc/*.md`，逐文件提取每个 PC 行（16 列完整行，含三级/四级/五级目录列）
2. 按 `三级目录 → 四级目录 → 五级目录 → 用例编号` 排序
3. 同一 LC 的 PC 行连续排列，中间不插入分页或重复表头
4. PC 行中 `fact_status=needs-confirmation` 的，在用例名称末尾追加 ` ⚠️待确认`
5. 汇总表表头只出现一次，放在全文最前

#### 3b. 各 LC 详情（全文后部）

按 **四级目录（H2）→ 五级目录（H3）→ 逻辑用例（H4）** 组织。

每个 LC 渲染：

1. `ppdcs/ppdcs/<basename>.md` 的推荐上下文与完整过程
2. `topology_role_refs → topology_bindings → PC materialization` 绑定表
3. PC 引用行（不重复渲染 PC 表）：
   ```
   > 物理用例：见上方统一 PC 汇总表，用例编号 PC-XXX-XXX-001 ~ PC-XXX-XXX-NNN
   ```

按设计 Skill 分类保留过程内容：

| 设计 Skill | 必渲染内容 |
|------------|------------|
| `process-design` | 流程图、节点清单、路径枚举、覆盖策略、触发数据 |
| `state-design` | 状态图、状态/迁移表、守卫条件、路径选择、迁移数据 |
| `parameter-design` | factor catalog、规则表、判定结构、data row |
| `data-design` | factor catalog、等价类/边界值表、独立性检查、data row |
| `combination-design` | factor catalog、约束表、压缩策略、组合表、pair coverage checklist / fallback 记录 |

### 步骤 4：渲染原子操作候选对比表

消费 `mfq/ptm-atomic-usage/candidate-ptm-atomic.yaml`，生成对比分析表。

**输入字段**：`op_id`（候选操作 ID）、`match_attempt`（L1-L4 匹配 + score）、`source`（来源场景/步骤）、`scenario_refs`

| 候选 op_id | 操作描述 | L1名称 | L2参数 | L3输出 | L4错误码 | 综合得分 | 现有库匹配 | 匹配结果 | 来源场景 |
|------------|---------|--------|--------|--------|----------|:---:|---------|:---:|---------|
| CAND-OP-001 | 删除日志服务器 | fw_log_server_delete | --id | success\|error | 2xx\|4xx | 85 | fw_log_server_delete | ✅ 已匹配 | SCN-LOG-001 |

- **匹配结果**：`✅ 已匹配`（score ≥ 80）、`⚠️ 部分匹配`（50-79）、`❌ 未匹配`（< 50 或无匹配）
- **未匹配候选**在表后附摘要：”本次分析共发现 N 个新候选原子操作，建议提交 ptm-tae 进行工具开发”

### 步骤 5：渲染测试因子候选对比表

消费 `mfq/f-analysis/coupling-test-points.md` 末尾的耦合因子候选列表 + `mfq/m-analysis/candidate-factor-proposals.yaml`，合并去重后生成对比分析表。

| factor_id | 候选名称 | data_domain | 来源类型 | 现有公共因子 | 匹配结果 | 所属 TSP | 来源场景 |
|-----------|---------|-------------|:---:|-----------|:---:|---------|---------|
| FAC-F-CAND-001 | 规则冲突处理结果 | 冲突/未冲突/部分冲突 | new-coupling | — | 🆕 新增 | TSP-M2-001 | SCN-COUP-001 |
| FAC-M-CAND-005 | 接口工作模式 | L2/L3/接口对 | new-candidate | FAC-INTF-MODE | ✅ 已匹配 | TSP-M1-003 | SCN-INTF-001 |

- **来源类型**：`new-coupling`（F 分析耦合发现）、`new-candidate`（M 分析因子候选）
- **匹配结果**：`✅ 已匹配`（公共库中存在等价因子）、`🆕 新增`（无匹配，建议入库）
- **未匹配候选**在表后附摘要：”本次分析共发现 N 个新候选测试因子，建议提交 ptm-tde 因子库维护流程进行评审入库”

## 输出文件

所有交付物输出到 `ppdcs/delivery/`：

| 文件 | 内容 |
|------|------|
| `ppdcs/delivery/<特性名>特性测试方案.md` | 覆盖测试方案、场景、分析与覆盖摘要 |
| `ppdcs/delivery/<特性名>特性测试用例.md` | 统一 16 列 PC 汇总表（全文最前） + 按 LC 组织的完整设计过程（全文后部，不重复渲染 PC 表） |
| `ppdcs/delivery/<特性名>原子操作候选对比表.md` | 候选 ptm-atomic 与现有库的匹配对比（L1-L4 + score），标注已匹配/部分匹配/未匹配 |
| `ppdcs/delivery/<特性名>测试因子候选对比表.md` | 候选测试因子与公共因子库的匹配对比，标注已匹配/新增，按 TSP 和来源类型组织 |

## 渲染规则

1. **不丢过程**：必须带出 STORY-06 / STORY-07 完整设计过程
2. **统一 PC 表**：全文仅一张 16 列 PC 汇总表，来自所有 `ppdcs/pc/*.md` 的 PC 行合并
3. **不丢字段**：不得删掉 trace / gap / topology / fact_status；若存在 `topology_ref`，不得在场景章节中丢失
4. **候选对比表独立交付**：原子操作和测试因子候选对比表以独立 Markdown 输出，不嵌入测试方案/用例中
5. **不混淆对象**：测试因子、拓扑角色和真实组网对象分开展示；`DUT.port1`、`TG.port1`、link 实例不得进入”因子-取值表”。
6. **不提升状态**：`fact_status=needs-confirmation` 或 `topology_binding_status=needs-confirmation` 的条目必须原样进入交付物，不能因已生成 PC 改为 confirmed。PC 汇总表中 needs-confirmation 的条目在用例名称末尾追加 ` ⚠️待确认`。

## 公共因子库补充契约

- deliverable-renderer 必须读取 `mfq/factor-usage/`，在测试方案中输出“因子库与样本策略”小节。
- 小节至少包含公共库 `library_id / version / checksum`、关键 factor groups、配置/功能样本策略、物化策略。
- 最终物理用例展示 `materialized_value`；随机样本必须记录 deterministic seed。
- `factor_bindings` 是主契约，`factor_refs` 仅作兼容摘要。
- 接口类型、接口能力可以作为因子或约束展示；真实 `DUT.port1` / `TG.port1` / link 实例只能展示在拓扑绑定小节或 PC 组网字段，不能展示为公共因子值。

## 拓扑绑定补充契约

- deliverable-renderer 必须读取 LC / PC 中的 `topology_bindings`，并在交付物中保留 `topology_role / device_id / port_id / link_id / source / fact_status`。
- 测试方案的场景章节展示来源链：`confirmed-scenarios.md -> topology_ref/topology.yaml -> LC topology_bindings -> PC materialization`。
- 测试用例总表的组网描述和组网约束可展示真实端口，但必须标注来源；若 `fact_status` 或 `topology_binding_status` 为 `needs-confirmation`，交付物必须显式暴露确认缺口。
- “因子库与样本策略”小节只展示公共测试因子和样本策略，不得混入真实端口、真实链路或项目专属 topology instance。

## Gotchas

- `feature_tags` 若缺失，应在交付中列为 gap，而不是用模块名临时替代
- `fact_status=needs-confirmation` 的 LC / PC 条目必须原样进入交付物
- `DUT.port1`、`TG.port1` 和 link 实例是 topology materialization，不是 factor materialization

## 验收标准

- [ ] 输出四份交付物：测试方案 + 测试用例 + 原子操作候选对比表 + 测试因子候选对比表
- [ ] 测试用例文档全文仅一张 16 列 PC 汇总表（来自所有 `ppdcs/pc/*.md` 的 PC 行合并）
- [ ] 汇总表覆盖 `ppdcs/pc/` 下所有 PC 文件的全部 PC 行
- [ ] 各 LC 详情不重复渲染 PC 表（改为 PC 编号引用行）
- [ ] `fact_status=needs-confirmation` 的 PC 在用例名称末尾标注 ` ⚠️待确认`
- [ ] 原子操作候选对比表包含 op_id、match_attempt、score、匹配结果、来源场景
- [ ] 测试因子候选对比表包含 factor_id、data_domain、来源类型、匹配结果、TSP
- [ ] 未匹配候选附摘要说明（数量 + 建议后续动作）
- [ ] 测试用例文档消费 STORY-06 / STORY-07 的完整过程文档，而非仅最终 PC
- [ ] 交付物保留 `requirement_ids`, `logic_case_id`, `feature_tags`, `trace_refs`, `scenario_refs`, `action_source_refs`, `factor_bindings`, `factor_refs`, `topology_role_refs`, `topology_bindings`, `topology_role`, `source`, `confirmation_gap_refs`, `fact_status`
- [ ] 交付物不把真实端口、真实链路或 `DUT.port1` / `TG.port1` 展示为因子
- [ ] 不生成工具分析表或 `case-index.yaml`
