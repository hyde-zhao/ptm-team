---
name: reverse-analysis
description: 对清洗后的问题单数据执行资格检查、可信输入建立与六维分析引擎，构建分析就绪的证据线集合，产出区分事实/假设/证据支撑/人工确认状态的审计级分析报告。覆盖根因四层状态机、产品质量、流出控制矩阵、漏测 PPDCS 归类、改进 CA/PA 候选和环比同比六个维度。不自动确认根因，不直接分发 CA/PA，不允许无分母称密度。
argument-hint: "<batch_ref | ticket_id> [--mode s1|s2] [--comparison-batch <ref>]"
user-invokable: false
status: active
shared: true
shared_writers:
  - ST-RA-01（§1-§2：资格检查、可信输入建立与证据分类）
  - ST-RA-02（§3-§5：六维分析引擎、根因状态机、指标定义与降级）
  - ST-RA-05.3（§6：S1 分析管线 — 逐单/批量分析、AnalysisRunManifest、报告草案输出与 reviewer 发布路径）
  - ST-NRA-01（§7：三线阈值阻断与证据缺口硬限制）
  - ST-NRA-02（§8：权限边界拒绝与越权保护）
  - ST-RA-06.2（§9：S2 增量重算与差异报告 — 变更消费、受影响维度判定、增量/全量重算引擎、差异报告、环比同比、措施刷新提示与完整管线串联）
version: "1.6"
source_cr: "CR-030, CR-031"
source_feature: "FEAT-RA-ANALYSIS"
source_lld:
  - "process/stories/STORY-RA-01-qualification-evidence-LLD.md"
  - "process/stories/STORY-RA-02-six-dim-analysis-engine-LLD.md"
  - "process/stories/STORY-RA-05.3-ANALYZE-s1-pipeline-LLD.md"
  - "process/stories/STORY-NRA-02-permission-boundary-denial.md"
---

# reverse-analysis: 逆向问题分析

## 目标

对 ITR 现网问题单执行结构化逆向分析，产出区分事实、假设、证据支撑和人工确认状态的审计级报告。本 Skill 是 ptm-tse Agent 的专用分析能力，由 Agent 编排调用，不直接面向最终用户。

**当前版本实现状态**：
- ST-RA-01：入口资格控制与可信输入建立（§1-§2）— 已完成
- ST-RA-02：六维分析引擎、根因四层状态机与指标定义（§3-§5）— 已完成
- ST-RA-05.3：S1 分析管线 — 逐单/批量分析、AnalysisRunManifest 管理、报告草案输出与 reviewer 发布路径（§6）— 已完成
- ST-NRA-01：证据不足保护 — 阈值硬阻断二次校验、缺失证据分类、证据不足报告、禁止行为清单（§7）— 已完成
- ST-NRA-02：权限边界拒绝与越权保护 — deny-by-default 总则、外部访问拒绝（外部连接/凭据/HTTP 写入）、生产操作拒绝（自动分发 CA/PA/下游任务/关闭工单）、越权检测与阻断、审计日志与禁止行为扩展（§8）— 已完成
- 后续章节（§9）由 ST-RA-06.2 补全（S2 增量重算与差异报告）。

## 前置条件

1. **数据就绪**：`data/schema.sql` 中 `ticket`、`ingestion_batch`、`ticket_version` 表已创建且包含清洗后数据（ST-RA-INGEST-DB 负责）。
2. **DAO 可用**：`data/dao.py` 可导入，提供以下只读查询接口和受限写入接口：
   - `get_tickets_by_batch(conn, batch_ref)` — 按批次获取 quality_flag='clean' 的 ticket 列表
   - `get_ticket_by_batch_ref(conn, batch_ref)` — 按批次引用获取 ticket（通过 ticket_version 关联）
   - `get_batch(conn, batch_id)` — 查询批次质量状态
   - `get_ticket_by_source_id(conn, source_ticket_id)` — 按 ID 获取单条 ticket
   - `get_tickets_by_time_range(conn, start, end)` — 按时间范围查询 ticket
   - `get_tickets_by_product(conn, product)` — 按产品查询 ticket
   - **analysis_run 管理接口**（受限写入）：
     - `insert_analysis_run(conn, run_dict)` — 创建分析运行记录（初始状态 `created`）
     - `get_analysis_run(conn, run_id)` — 按 ID 查询分析运行
     - `get_runs_by_batch(conn, batch_ref)` — 按批次查询分析运行列表
     - `update_analysis_run_draft(conn, run_id, status, report_refs)` — 更新草案状态（created/in_progress/completed/failed）
     - `reviewer_publish_analysis_run(conn, run_id, reviewer_ref)` — reviewer 发布（completed → published）
3. **权限**：Skill 调用方（ptm-tse Agent）对 SQLite 拥有受限访问权限：
   - `ticket`、`ticket_version`、`ingestion_batch` 表：只读（SELECT only）
   - `analysis_run` 表：可通过 DAO 受限写入（仅 INSERT + UPDATE draft status）；发布仅 reviewer 专用接口
   - 不得直接执行 INSERT/UPDATE/DELETE/DDL
4. **字段依赖**：
   - `ticket.severity`：取值为 P1/P2/P3/P4 或空
   - `ticket.quality_flag`：取值为 clean/incomplete/anomaly/blocked
   - `ticket.is_internal`：布尔字段，标识内部问题（当前 schema 尚未包含，缺失时视为 false）
   - `ticket.source_ticket_id`：非空且稳定
   - 证据字段：`root_cause`、`test_missed_analysis`、`test_missed_phase`、`improvement_measures`、`title`、`description`、`module`、`status`、`priority`

## 运行数据治理契约

本 Skill 只读消费安装后的 `ptm-tse` 项目中的清洗数据。`runtime_root` 默认是该安装项目根；`data_root` 必须是 `<runtime-root>/data/`。本文中的 `data/...` 引用均相对于该根，绝不回退到 `ptm-team` 源码根、全局用户目录或任意 CWD。

调用前必须取得 ptm-tse Agent 生成的 `RuntimeDataGovernanceReport`。只有 `status=compliant` 才能读取 SQLite、创建分析草案或更新 `analysis_run` 草案状态。`blocked` 或 `needs-user-authorization` 时必须返回阻断项和修复建议，不读取 `raw_json`，不创建或发布报告，也不执行任何权限修复、删除、迁移、导出或保留操作。

含问题单材料的 RA Report、差异报告和 `analysis_run.report_refs` 所指文件属于敏感运行数据，必须位于 `<runtime-root>/data/` 的受限子目录，目录为 `0700`、文件为 `0600`。本 Skill 可在已合规的运行根中创建本次草案；不得自行修复既有文件权限。没有可信分母、证据或数据治理预检时的降级/阻断规则仍优先适用。

---

## §1 资格检查

### 1.1 触发条件

ptm-tse Agent 收到分析请求时，第一步执行资格检查。输入为 `batch_ref`（批次引用）或 `ticket_id`（单条问题单引用）。

### 1.2 执行步骤

#### Step 1: 获取 ticket 数据

```
从 SQLite 读取目标 ticket 记录：
- 按 batch_ref 查询：调用 get_tickets_by_batch(conn, batch_ref)
  → 返回 quality_flag='clean' 的 ticket 列表
- 按 source_ticket_id 查询：调用 get_ticket_by_source_id(conn, source_ticket_id)
  → 返回单条 ticket 记录或 None
```

**读取字段**（仅清洗后字段，不读取 `raw_json`）：

| 字段 | 来源列 | 用途 |
|------|--------|------|
| `source_ticket_id` | `ticket.source_ticket_id` | 唯一标识，非空校验 |
| `severity` | `ticket.severity` | 优先级判定（P1/P2/P3/P4） |
| `product` | `ticket.product` | 产品归属（不用于资格判定，仅记录） |
| `status` | `ticket.status` | 问题单当前状态（不用于资格判定，仅记录） |
| `quality_flag` | `ticket.quality_flag` | 质量标记（clean/incomplete/anomaly/blocked） |
| `is_internal` | `ticket.is_internal` | 内部问题标记（当前 schema 尚未包含，缺失时视为 false） |

**禁止读取**：
- `ticket.raw_json`（原始 ITR 响应体，不进入分析正文）
- 任何认证凭据、环境变量、配置文件

#### Step 2: 空值与关键字段校验

在进入优先级判定前，先校验关键字段是否存在且有效：

```
if source_ticket_id 为空或类型非 str:
    → 资格状态: blocked
    → 原因: "缺少有效的 source_ticket_id"
    → 停止分析，不创建 analysis_run
```

#### Step 3: 质量前置检查

```
if quality_flag == 'blocked':
    → 资格状态: blocked
    → 原因: "关联的 IngestionQualityReport 标记为 blocked，数据不可用于分析"
    → 输出: IngestionQualityReport 引用（如果可获取）
    → 停止分析，不创建 analysis_run

if quality_flag 缺失或不在 (clean, incomplete, anomaly, blocked) 中:
    → 资格状态: blocked（保守策略，不确定则阻断）
    → 原因: "quality_flag 值无效或缺失"
    → 停止分析
```

仅 `quality_flag` 为 `clean`、`incomplete` 或 `anomaly` 的 ticket 可以继续资格判定。其中 `incomplete` 和 `anomaly` 通过时附加风险标记。

#### Step 4: 优先级判定

按 severity 字段分派资格状态：

```
if severity == 'P1':
    → 资格状态: eligible
    → 原因: "P1 事件，必做分析"
    → 进入证据分类（§2）

elif severity == 'P2':
    → 资格状态: eligible_on_request
    → 原因: "P2 事件需显式确认后进入分析"
    → 暂停，输出确认提示，等待用户选择:
        - 用户确认 → eligible，进入证据分类
        - 用户拒绝 → rejected，停止分析

elif severity == 'P3' or severity == 'P4':
    → 资格状态: rejected
    → 原因: "P{severity} 事件不自动进入逆向分析"
    → 输出建议: "建议使用人工流程处理该优先级事件"
    → 停止分析，不创建 analysis_run

elif severity 为空:
    → 资格状态: rejected（默认视为最低优先级）
    → 原因: "severity 字段为空，默认拒绝分析"
    → 停止分析
```

**注意**：severity 字段当前在 schema 中为 `TEXT` 类型且无 CHECK 约束。若遇到非 P1/P2/P3/P4 的值，视为 severity 为空处理（默认拒绝）。

#### Step 5: 内部问题识别

```
if is_internal == true:
    → 资格状态: deferred
    → 原因: "标记为内部问题，不适用于现网逆向分析"
    → 输出补充说明:
        - 当前不适用的分析维度
        - 重新立项条件（例如：问题转为外部可见后）
        - 建议流程（例如：内部复盘流程）
    → 停止分析
```

**当前 schema 状态**：`is_internal` 列尚未在 `data/schema.sql` 中定义。在列缺失时，所有 ticket 视为 `is_internal=false`（不触发 defer）。该列由上游 Story 负责添加。

#### Step 6: 无效 source_ticket_id 与数据缺口

除 Step 2 的空值校验外，还需检查：

```
if ticket 记录不存在（get_ticket_by_source_id 返回 None）:
    → 资格状态: blocked
    → 原因: "source_ticket_id 在数据库中不存在"
    → 输出缺失记录清单

if batch_ref 指向的 batch 在 ingestion_batch 中无记录:
    → 资格状态: blocked
    → 原因: "batch_ref 对应的摄取批次不存在"
    → 输出缺失 batch 引用
```

### 1.3 资格结果枚举

| 状态 | 含义 | 后续动作 |
|------|------|---------|
| `eligible` | 通过资格检查，可进入证据分类 | 进入 §2 可信输入建立 |
| `eligible_on_request` | 需要用户显式确认（P2 事件） | 暂停等待确认 |
| `rejected` | 不符合分析条件（P3/P4/severity 缺失） | 停止分析，输出拒绝原因 |
| `deferred` | 内部问题，不适用分析 | 停止分析，输出重新立项条件 |
| `blocked` | 数据质量或完整性不满足最低要求 | 中止分析，输出 blockage 原因 |

### 1.4 资格判定矩阵速查

| severity | is_internal | quality_flag | source_ticket_id | → 结果 |
|----------|-------------|-------------|-----------------|--------|
| P1 | false | clean/incomplete/anomaly | 有效 | **eligible** |
| P2 | false | clean/incomplete/anomaly | 有效 | **eligible_on_request** |
| P3/P4 | — | — | 有效 | **rejected** |
| — | true | — | — | **deferred** |
| — | — | blocked | — | **blocked** |
| 空 | — | — | — | **rejected** |
| — | — | — | 空/无效 | **blocked** |

---

## §2 可信输入建立

### 2.1 触发条件

资格检查结果为 `eligible` 后，自动进入可信输入建立阶段。本节定义如何从 SQLite 的清洗后字段构建分析就绪的证据线集合。

### 2.2 只读数据获取

**仅读取清洗后字段，不读取 `raw_json`**。

从 ticket 记录中提取以下字段作为证据线来源：

| 来源列 | 证据线类型 | 说明 |
|--------|----------|------|
| `root_cause` | 根因线 | ITR 中已填写的根因描述 |
| `test_missed_analysis` | 漏测分析线 | 测试遗漏分析 |
| `test_missed_phase` | 漏测阶段线 | 测试遗漏发生的阶段 |
| `improvement_measures` | 改进措施线 | 已提议或已实施的改进措施 |
| `description` | 描述线 | 问题详细描述，包含现象、环境、复现步骤等 |
| `title` | 标题线 | 问题单标题，提供概要信息 |
| `module` | 模块归属线 | 问题发生的模块/组件 |
| `status` | 状态线 | 问题单当前状态 |
| `priority` | 优先级线 | 问题单业务优先级 |
| `openeddate` | 时间线 | 问题单创建时间 |
| `resolveddate` | 时间线 | 问题单解决时间 |

**禁止**：
- 读取 `raw_json` 中未映射到列的原始字段
- 从快照文件直接读取 JSON
- 根据字段名推断敏感信息

### 2.3 五条证据线分类

#### 2.3.1 证据线定义

本次分析使用**五条证据线**框架（来源：HLD §1.1 + Feature DESIGN §2.1）：

| 线编号 | 名称 | 典型来源字段 | 说明 |
|--------|------|------------|------|
| L1 | 根因证据 | `root_cause` | 问题发生的直接/根本原因 |
| L2 | 漏测证据 | `test_missed_analysis`, `test_missed_phase` | 测试环节为何未能捕获 |
| L3 | 改进措施证据 | `improvement_measures` | 已采取或建议的改进措施 |
| L4 | 现象/环境证据 | `description`, `title` | 问题现象、环境、影响范围 |
| L5 | 上下文/归属证据 | `module`, `status`, `priority`, `openeddate`, `resolveddate` | 模块归属、状态和时序信息 |

#### 2.3.2 分类规则

每条证据线按以下规则标注 `category`（类别）和 `validity`（有效性）：

**category 分类**：

```
if 字段值非空 AND 可追溯到原始 ITR 记录 AND 值可信:
    → category: fact
elif 字段值非空 AND 需要 AI 进一步分析或判断:
    → category: hypothesis
elif 字段值存在但矛盾（同一字段在两处来源给出不同值）或不可信（如包含占位符 "TBD"/"N/A"/"待补充" 等）:
    → category: unknown
elif 字段值为空或无法从现有数据推导:
    → category: gap
```

**validity 判定**：

```
if category ∈ {fact, hypothesis}:
    if 值有明确来源 AND 长度 ≥ 5 字符 AND 不完全是占位符:
        → validity: valid
    else:
        → validity: incomplete

if category ∈ {unknown, gap}:
    → validity: invalid（unknown 类）或 N/A（gap 类）
```

**来源标注**：每条证据线标注具体来源字段名。如果没有字段可用，标记来源为 `none`。

**gap_owner**：当 `category=gap` 时，标注补充责任人：
- 根因/漏测/措施相关 gap → owner: "PTM-TSE/测试架构师"
- 现象/环境/上下文 gap → owner: "ITR 录入方/产品团队"
- 无法确定 → owner: "待确认"

**clarification_status**：
- `clear` — 证据线值清晰，无需澄清
- `needs_clarification` — 值存在但模糊、矛盾或需要补充信息

#### 2.3.3 证据线输出结构

每条证据线的输出格式（对应 LLD §2.3）：

```yaml
evidence_lines:
  - line_id: "L1"
    category: fact          # fact | hypothesis | unknown | gap
    validity: valid          # valid | incomplete | invalid
    source: "root_cause"     # 引用来源字段
    gap_owner: null          # 当 category=gap 时的补充责任人
    clarification_status: clear  # clear | needs_clarification
    summary: "根因字段值的摘要（不超过 200 字符）"
```

### 2.4 三线阈值检查

#### 2.4.1 有效线计数

在所有五条证据线中，满足以下条件的计入 `valid_count`：

```
条件: category ∈ {fact, hypothesis} AND validity = valid
```

#### 2.4.2 阈值判定

```
if valid_count >= 3:
    → 阈值结果: passed
    → 根因四层可进入: evidence-backed（在 ST-RA-02 中实现，此处仅标记）
    → 输出: "证据充足，valid_count = {N}"

if valid_count < 3:
    → 阈值结果: insufficient
    → 根因四层上限: AI candidate（在 ST-RA-02 中实现，此处仅标记）
    → 输出:
        - valid_count 值
        - 缺口清单（所有 category=gap 或 validity≠valid 的证据线）
        - 建议：在进入 evidence-backed 前补充至少 {3 - valid_count} 条有效证据线
    → 资格状态: 仍为 eligible，但标记 eligible_with_gaps
```

**重要**：
- 三线阈值检查不影响资格状态（eligible 仍为 eligible）
- 阈值不足只限制下游根因状态机的跃迁上限
- 不自动阻断分析，不自动降级资格

### 2.5 输出结构

资格检查与证据分类完成后，输出以下结构：

```yaml
eligibility:
  status: eligible           # eligible | eligible_on_request | rejected | deferred | blocked
  reason: "P1 事件，必做分析"
  ticket_ref: "ITR-2026-0001"
  quality_batch_ref: "batch_20260716_001"
  threshold:
    valid_count: 4
    result: passed           # passed | insufficient
    max_rc_state: evidence-backed  # evidence-backed | AI candidate

evidence_set:
  lines:
    - line_id: "L1"
      category: fact
      validity: valid
      source: "root_cause"
      gap_owner: null
      clarification_status: clear
      summary: "..."
    - line_id: "L2"
      category: hypothesis
      validity: valid
      source: "test_missed_analysis"
      gap_owner: null
      clarification_status: needs_clarification
      summary: "..."
    # ... L3-L5
  gap_report:
    - line_id: "L4"
      reason: "description 字段为空"
      recommended_action: "从 ITR 补全问题描述后再分析"
      gap_owner: "ITR 录入方/产品团队"
```

### 2.6 错误处理

| 场景 | 处理方式 | 降级输出 |
|------|---------|---------|
| 所有证据字段（root_cause/description 等）全为空 | 五条线全部标记 gap | valid_count=0, threshold=insufficient |
| 部分字段为空 | 对应线标记 gap，其余分类 | 缺口清单 + 有效线正常计算 |
| 字段含不可信值（"TBD"/"N/A"/空字符串） | 标记为 unknown + validity=invalid | 不进入 valid_count |
| 字段值超长（>5000 字符） | 截断至 200 字符摘要 | 原始值引用保留在 source 字段中 |

---

## §3 六维分析引擎

### 3.1 分析维度总览

六维分析引擎接收 §2 输出的资格结果和证据线集合，对每条 ticket（或 ticket 集合）执行以下六个维度的分析。各维度的输入、方法和输出契约如下：

| 维度 | 代号 | 输入 | 分析方法 | 输出要求 |
|------|------|------|---------|---------|
| 根因分析 | RC | `ticket.root_cause` + §2 证据线集合 | 5 Whys / 鱼骨图候选生成 + 事实/假设分离 | `RootCauseAnalysis`：raw_statement, ai_candidates[], evidence_support, reviewer_status |
| 产品质量分析 | PQ | `ticket.product`, `ticket.module`, `ticket.severity`, `ticket.status`, `ticket.openeddate` | 按维度聚合 → 数量/占比/Pareto/趋势 | `ProductQualityAnalysis`：top_risk_modules[], quality_trend, defect_density（仅当有可信分母） |
| 流出分析 | ESC | 测试/发布/监控控制证据（来自 §2.3 证据线 L4-L5 + 人工补充字段） | 控制层逃逸矩阵 | `EscapeAnalysis`：escape_points[], nearest_intercept_point, candidate_layers[], confirmed_layers[] |
| 漏测分析 | TM | `ticket.test_missed_analysis`, `ticket.test_missed_phase` | PPDCS 归类 | `TestMissedAnalysis`：ppdcs_category, missed_pattern, recommended_test_method, unknown_fields[] |
| 改进分析 | IMP | `ticket.improvement_measures` + 分析结论 | CAPA 候选草案生成 | `ImprovementCandidates`：capa_items[]（纠正/预防 + Owner + 验收 + 有效性检查） |
| 环比同比分析 | CMP | `ticket.openeddate`, `ticket.resolveddate` + 版本化状态 | 完整月份/季度窗口同口径聚合 | `ComparisonAnalysis`：baseline, current, absolute_change, change_rate, credibility, na_reasons[] |

**关键约束**：
- 所有维度必须基于 §1-§2 的资格检查和证据分类结果
- 不得跳过证据不足的维度——证据不足时输出"gap report"而非虚假结论
- AI 提供的分析结论始终标记置信度（high/medium/low），不得假装确定

### 3.2 逐维度分析规则

#### 3.2.1 根因维度（RC）

**目标**：从原始根因描述中提取结构化的根因分析，区分 AI 假设和事实支撑。

**执行步骤**：

```
Step RC-1: 提取 raw_statement
  从 ticket.root_cause 读取原始根因描述。若字段为空，raw_statement = "no_statement_available"。

Step RC-2: AI 候选生成
  对 raw_statement 执行以下分析（根据内容复杂度选择方法）：

  a) 5 Whys 方法（适用于描述清晰的单因问题）：
     连续追问 5 次"为什么"，每一次的答案作为下一轮追问的基础。
     输出：从表面现象到根本原因的因果链。

  b) 鱼骨图方法（适用于多因素复杂问题）：
     按类别分组分析：人/机/料/法/环/测。
     输出：每个类别下的潜在原因。

  c) 组合方法（raw_statement 含多个独立问题线索时使用）：
     先用鱼骨图分类，再对主要分支做 5 Whys 深挖。

  输出格式（每个候选）：
    - hypothesis: 候选根因描述
    - confidence: high | medium | low
    - method: 5whys | fishbone | combined
    - supporting_evidence: 引用 §2 中 category=fact 的证据线 line_id 列表
    - contradicting_evidence: 引用 §2 中与该候选矛盾的证据线 line_id 列表

Step RC-3: 置信度判定规则
  根据证据支撑情况判定置信度：
    - high：有 3 条以上 fact 类证据线直接支撑该候选，且无矛盾证据
    - medium：有 1-2 条 fact 或 hypothesis 类证据线支撑，可能有轻微矛盾
    - low：无直接证据支撑，或存在显著矛盾证据

  注意：confidence 与根因状态机的 current_level 是独立概念。
  confidence 是 AI 对其候选质量的自我评估；current_level 是状态机的位置。

Step RC-4: 输出
  将分析结果写入 ra-report.yaml 的 sections.root_cause 段。
  详见 §4 根因状态机的完整转换规则。
```

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| `ticket.root_cause` | raw_statement 原始内容 | 标记 "no_statement_available" |
| §2 evidence_set.lines[L1]（根因证据） | 支撑/矛盾证据 | 不阻断分析，confidence 降到 low |
| §2 evidence_set.lines[L4-L5]（现象/上下文） | 辅助分析上下文 | 不阻断分析 |

#### 3.2.2 产品质量维度（PQ）

**目标**：从版本化问题单数据中提取产品质量趋势和风险分布，在有可信分母时计算缺陷密度。

**执行步骤**：

```
Step PQ-1: 按维度聚合
  对 ticket 集合按以下维度分组统计：
    - product（产品）
    - module（模块）
    - severity（严重级别：P1/P2/P3/P4）
    - status（问题单状态）

Step PQ-2: 生成数量与占比
  每组输出：
    - count: 该组问题数量
    - percentage: 该组占比（相对于总 ticket 数）

Step PQ-3: 生成 Pareto 排序
  将模块维度的问题数量按降序排列生成 top_risk_modules[]。
  输出格式（每个模块）：
    - product: 产品名
    - module: 模块名
    - count: 问题数量
    - percentage: 占总数百分比
    - trend_direction: rising | stable | falling

Step PQ-4: 缺陷密度计算（条件触发）
  仅当满足以下全部条件时才计算缺陷密度：
    a) MetricDefinition 的 denominator.trusted = true
    b) 分母字段（如单位时间代码量）可获取且经过验证
    c) 分母值与 numerator 的过滤条件和窗口对齐

  如果任一条件不满足：
    → 应用 degraded_output（参见 §5.2 降级策略）
    → 在 ra-report.yaml 的 degraded_notice 字段写入降级原因
    → 绝不在输出中将降级数据标记为"缺陷密度"、"DPMO"等
```

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| `ticket.product` | 产品分组 | 标记为 "unknown_product" |
| `ticket.module` | 模块分组 | 标记为 "unknown_module" |
| `ticket.severity` | 严重级别分组 | 排除该条记录不参与分组 |
| `ticket.status` | 状态分组 | 排除该条记录不参与状态分组 |
| `ticket.openeddate` | 趋势分析（时间序列） | 不生成趋势图，标记 "no_temporal_data" |

#### 3.2.3 流出维度（ESC）

**目标**：识别问题在哪些质量控制层被遗漏——应该在哪个环节被捕获、实际为何流出到了线上。

**执行步骤**：

```
Step ESC-1: 识别控制层集合
  质量控制层标准集合：
    - 需求评审 Requirements Review
    - 设计评审 Design Review
    - 代码评审 Code Review
    - 单元测试 Unit Test
    - 集成测试 Integration Test
    - 系统测试 System Test
    - 验收测试 Acceptance Test
    - 发布检查 Release Gate
    - 监控告警 Production Monitoring

Step ESC-2: 判定每个控制层的逃逸状态
  对于每个控制层，检查是否存在控制证据（来自 §2 证据线或人工补充字段）：

  if 存在明确证据证明该层执行了完整检查，且检查范围覆盖了此问题类型：
      → status: confirmed
      → 标记为 confirmed_layers[]
      → 记录 evidence_ref（证据引用）

  else（缺少证据，或证据不足以证实检查覆盖了此问题类型）：
      → status: candidate
      → 标记为 candidate_layers[]
      → 附注 reasoning（推断理由，如"问题特征表明本应在代码评审中发现"）

Step ESC-3: 确定最近拦截点
  基于 confirmed escape layers，推理 nearest_intercept_point：
    - 问题的特征（如逻辑错误 → 单元测试；接口不匹配 → 集成测试）
    - 最早发现问题的阶段
    - 实际产生影响的阶段
  如果所有 escape layers 都是 candidate（无 confirmed），nearest_intercept 标注"无法确定，缺少控制证据"
```

**关键规则**：
- **candidate/confirmed 分离**：无控制证据时只输出 candidate，不可标为 confirmed
- **不推测控制层的执行质量**：即使某个控制层被标记为 confirmed escape，不自动推断该层的执行质量差——只陈述"问题在此层未被捕获"
- **nearest_intercept 不是 blame 工具**：目的是帮助团队找到最经济的改进切入点

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| 人工补充的控制证据字段（来自 ITR 或以其他方式提供） | 判定 escape layer 的 confirmed 状态 | 所有 escape layers 标记 candidate |
| §2 evidence_set.lines（L4-L5，现象/上下文/归属） | 辅助推理 nearest_intercept | 不阻断分析 |

#### 3.2.4 漏测维度（TM）

**目标**：归类漏测原因到 PPDCS 框架（Prevention/Protection/Detection/Containment/Sustainment），并输出建议的测试设计方法。

**PPDCS 框架定义**：

| 类别 | 含义 | 典型场景 |
|------|------|---------|
| **Prevention** | 预防：设计/需求阶段本可预防 | 需求遗漏、设计缺陷、接口定义不完整 |
| **Protection** | 保护：防御性机制本可减轻影响 | 缺少超时、缺少降级、缺少熔断 |
| **Detection** | 检测：测试环节本应发现 | 测试用例覆盖不足、测试环境差异、测试数据不充分 |
| **Containment** | 围堵：发布/灰度环节本应拦截 | 灰度范围不足、监控指标缺失、发布检查不完整 |
| **Sustainment** | 维持：运维阶段的持续保障不足 | 缺少巡检、告警阈值不当、日志级别不够 |

**执行步骤**：

```
Step TM-1: 读取输入
  从 ticket.test_missed_analysis 和 ticket.test_missed_phase 提取原始漏测分析文本。

Step TM-2: 归类到 PPDCS
  分析漏测文本中描述的原因特征，映射到 PPDCS 类别：

  Prevention 关键词信号：需求遗漏、设计未考虑、边界条件遗漏、文档不完整
  Protection 关键词信号：缺少校验、无降级、无兜底、未加超时、无幂等
  Detection 关键词信号：用例未覆盖、环境差异、数据构造不足、未自动化
  Containment 关键词信号：灰度未覆盖、发布无检查、监控未配置、缺少回滚验证
  Sustainment 关键词信号：巡检缺失、告警漏配、日志级别不足、容量未评估

Step TM-3: 缺失字段处理
  若 test_missed_analysis 或 test_missed_phase 为空：
    → ppdcs_category 标记为 "unknown"
    → 在 unknown_fields[] 中记录缺失字段名
    → 不强行归类（不猜测缺失信息）

Step TM-4: 输出建议的测试设计方法
  基于 ppdcs_category 和 missed_pattern，推荐对应的测试方法：
    - Prevention 漏测 → 需求评审 checklist、边界值分析、等价类划分
    - Protection 漏测 → 故障注入测试、混沌工程、负面测试
    - Detection 漏测 → 组合测试、场景测试、探索性测试
    - Containment 漏测 → 灰度验证清单、生产就绪检查、金丝雀发布验证
    - Sustainment 漏测 → 巡检脚本回归、告警演练、容量压测
```

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| `ticket.test_missed_analysis` | 漏测原因文本 | 标记 unknown_fields[] |
| `ticket.test_missed_phase` | 漏测阶段 | 标记 unknown_fields[] |

#### 3.2.5 改进维度（IMP）

**目标**：基于已确认的根因、流出分析和漏测分析，生成纠正/预防措施候选草案。不批准、不分发——批准状态由 ST-RA-03 管理。

**执行步骤**：

```
Step IMP-1: 前置条件检查
  以下任一条件满足才生成 CA/PA 候选：
    - 根因分析至少到达 ai_candidate 状态（confidence 不限）
    - 流出分析有 confirmed 或 candidate escape layers
    - 漏测分析有 ppdcs_category（非 unknown）
  若以上都不满足 → 不生成 CA/PA 候选，标记 "insufficient_basis"

Step IMP-2: 生成纠正措施（Corrective Action）
  基于已确认的根因，为当前问题的修复和短期止血提出纠正措施：
    - type: corrective
    - basis: 引用根因分析的确认结论作为依据
    - target: 要修复的具体问题点
    - owner_candidate: 建议的执行 Owner（基于模块归属推测）
    - priority: P0 | P1 | P2 | P3（基于 severity 和影响范围）
    - acceptance_criteria: 可验证的完成标准
    - effectiveness_check: 如何验证措施有效（如"下一版本同类问题重复出现率"）

Step IMP-3: 生成预防措施（Preventive Action）
  基于流出分析和漏测分析，为长期流程/工具/方法改进提出预防措施：
    - type: preventive
    - basis: 引用流出分析和漏测分析的确认结论
    - target: 要改进的流程、工具或方法
    - owner_candidate: 建议的流程 Owner
    - priority: P1 | P2 | P3（预防类默认不低于 P3）
    - acceptance_criteria: 可验证的改进完成标准
    - effectiveness_check: 如何验证改进有效性

Step IMP-4: 输出
  将 CA/PA 候选写入 ra-report.yaml 的 sections.improvement_candidates.capa_items[]。
  注意：不修改 ticket 表，不写入 measure_link 表。
  capa_items[] 只含 draft 候选——批准状态和正式 tracking 由 ST-RA-03 追加。
```

**CA/PA 候选生成约束**：
- 每个候选必须关联到具体的分析结论（不能无依据生成"通用改进措施"）
- 每项 CA/PA 必须包含六个必填字段：type, basis, target, owner_candidate, priority, acceptance_criteria, effectiveness_check
- 不得自动将候选状态设为 approved 或 in-progress
- 不得将 capa_items[] 中的内容直接写入 measure_link 表

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| `ticket.improvement_measures` | 参考 ITR 中已填写的改进措施 | 不阻断 CA/PA 生成，作为补充参考 |
| §3.2.1 根因分析结果 | CA 的 basis | 前置不满足时不生成 CA |
| §3.2.3 流出分析 + §3.2.4 漏测分析 | PA 的 basis | 前置不满足时不生成 PA |

#### 3.2.6 环比同比维度（CMP）

**目标**：对两个完整同口径时间窗口的问题单数据进行聚合比较，输出基数、绝对变化、变化率和可信度评估。

**前提条件**：
- 分析模式为 S2（增量重算），有 comparison_batch_ref 提供对比数据集
- 当前窗口和基期窗口均为完整月份或完整季度
- 同口径数据（相同的 product/severity 过滤条件、相同的质量标记要求）

**执行步骤**：

```
Step CMP-1: 窗口验证
  检查当前窗口和基期窗口：
    - 检查窗口是否为完整自然月或完整自然季度
    - 非完整窗口 → comparison.mode = "none"，na_reasons[] 记录原因
    - 注意：当前 Skill 默认使用自然月/自然季度对齐；自定义窗口需扩展

Step CMP-2: 样本量检查
  对每个指标计算基期和当期的同口径样本量：
  if max(基期样本量, 当期样本量) < 10:
      → 标记 "sample_insufficient"
      → credibility = low
      → na_reasons[] 记录样本不足
      → 不计算变化率（避免小样本误导）
  注意：最小样本量阈值 10 是默认值（OPEN-RA02-02），可在 CP5 确认时调整。

Step CMP-3: 同口径聚合
  按相同维度分组（product/module/severity/status），分别聚合基期和当期的统计数据。

  对于每个聚合指标输出：
    - metric_name: 指标名称
    - baseline_value: 基期值
    - current_value: 当期值
    - absolute_change: 绝对变化（当前 - 基期）
    - change_rate: 变化率（(当前 - 基期) / 基期 × 100%），仅当基期值 > 0 时计算
    - direction: increased | decreased | unchanged
    - credibility: high | medium | low | na（见 Step CMP-4）

Step CMP-4: 可信度评估
  综合窗口完整性、样本量和数据一致性判定可信度：
    - high：完整窗口 + 样本量充足（>= 30）+ 数据一致性高
    - medium：完整窗口 + 样本量基本满足（10-29）
    - low：窗口完整但样本不足（< 10），或非完整窗口但可接受
    - na：无基期数据（first batch），或无同口径可比数据

Step CMP-5: 输出
  将结果写入 ra-report.yaml 的 sections.comparison 段。
  若 comparison.mode = "none"，comparison.changes[] 为空，na_reasons[] 必填。
```

**数据来源**：
| 来源字段 | 用途 | 缺失行为 |
|---------|------|---------|
| `ticket.openeddate` | 时间窗口归属 | 排除该条记录 |
| `ticket.resolveddate` | 已解决 ticket 的时间窗口 | 不影响未解决 ticket 的归属 |
| `ingestion_batch.created_at` | 基期/当期窗口界定 | 上下文提供 |
| 版本化状态（来自 ticket_version） | 同口径过滤 | 无版本时以 ticket 当前值为准 |

### 3.3 事实/假设分离规则

六维分析引擎的输出必须严格区分以下四类信息。该规则贯穿所有六个维度。

#### 3.3.1 分类标准

| 类别 | 英文 | 定义 | 判定规则 |
|------|------|------|---------|
| **事实** | fact | 可追溯到 SQLite 清洗后字段的明确信息 | 字段值非空 + 来源可追溯 + 无矛盾 + 不含占位符（"TBD"/"N/A"/"待补充"） |
| **假设** | hypothesis | AI 基于事实推导的分析结论 | 由 AI 生成 + 未经 reviewer 确认 + 必须标注 confidence |
| **未知** | unknown | 字段存在但值矛盾/不可信 | 字段有值但矛盾（多处不一致）或含占位符 |
| **缺口** | gap | 字段为空或无法从现有数据推导 | 字段值为空或关键信息不可获取 |

#### 3.3.2 各维度的分类应用

| 维度 | fact 示例 | hypothesis 示例 | unknown 示例 | gap 示例 |
|------|----------|----------------|-------------|---------|
| RC | raw_statement 原始文本 | AI 候选根因（hypothesis + confidence） | root_cause 含占位符 | root_cause 为空 → "no_statement_available" |
| PQ | severity=P1 的统计数量 | 某模块趋势是 rising（AI 判断） | module 字段值与另一表矛盾 | module 字段为空 |
| ESC | 控制证据明确记载某层检查已执行 | candidate escape layer | — | 完全没有控制证据字段 |
| TM | test_missed_phase = "单元测试"（明确字段值） | PPDCS 归类（AI 分析归类） | test_missed_analysis 含 "TBD" | test_missed_analysis 为空 |
| IMP | improvement_measures 中的已实施措施描述 | CA/PA 候选 draft（待 reviewer 确认） | — | 无法确定措施 Owner |
| CMP | 基期和当期 ticket 计数（SQLite 查询结果） | 趋势方向 rising/falling（AI 判断） | — | 缺少同口径基期数据 → N/A |

#### 3.3.3 强制规则

- **hypothesis 不得标记为 fact**：AI 生成的所有分析结论必须使用 hypothesis 标签 + confidence 标注
- **confirmed 结论不得由 AI 自动生成**：只有 reviewer 人工确认后的结论才能从 hypothesis 升级为 confirmed 状态
- **unknown 和 gap 必须输出补充建议**：两类信息不能只是标注——必须附带补充数据来源建议、澄清方向或 gap_owner
- **所有不在上述四类中的分析内容默认标记 hypothesis**：deny-by-default 时未知即假设

---

## §4 根因状态机

### 4.1 四层递进

根因分析遵循严格四层状态机，确保所有结论可追溯、可审计。

```
raw_statement ──(AI 自动分析)──► ai_candidate
                                      │
                            ┌─(evidence >= 3 lines)──► evidence_backed
                            │                              │
                            │                    ┌─(reviewer 人工确认)──► reviewer_confirmed
                            │                    │
                            └─(evidence < 3 lines)──► 停留在 ai_candidate（输出 gap report）
```

| 状态 | 含义 | 进入条件 | 退出条件 |
|------|------|---------|---------|
| `raw_statement` | 原始 ITR 字段内容，未经 AI 分析 | 初始状态（从 ticket.root_cause 读取后自动进入） | AI 自动分析完成后进入 `ai_candidate` |
| `ai_candidate` | AI 生成候选根因列表 + 置信度 | AI 分析完成（自动触发） | evidence >= 3 lines → `evidence_backed`；evidence < 3 → **保持** + gap report；reviewer 拒绝候选 → 回退到 `raw_statement` |
| `evidence_backed` | 有 3 条以上有效证据线支撑的根因 | evidence_lines 中 category ∈ {fact, hypothesis} AND validity = valid 的条数 >= 3 | reviewer 人工确认 → `reviewer_confirmed` |
| `reviewer_confirmed` | 经人工 reviewer 显式确认的结论 | reviewer 显式确认操作 | 不可自动退出；仅 reviewer 可回退到任一前置状态 |

### 4.2 状态转换规则与门控条件

#### 4.2.1 转换规则表

| 转换 | 触发方式 | 前置条件 | 门控规则 | 证据要求 |
|------|---------|---------|---------|---------|
| `raw_statement` → `ai_candidate` | **自动**（AI 分析） | raw_statement 已提取 | 无额外条件 | 无 |
| `ai_candidate` → `evidence_backed` | **阈值触发**（非自动跃迁） | 见§4.2.2 | 证据线硬阈值检查 | valid evidence lines >= 3 |
| `evidence_backed` → `reviewer_confirmed` | **人工确认** | evidence_backed 状态下 | 仅 reviewer 显式操作 | reviewer 确认记录 |
| `ai_candidate` → `raw_statement` | **人工回退** | reviewer 拒绝所有候选 | 仅 reviewer 显式操作 | reviewer 拒绝理由 |
| `evidence_backed` → `ai_candidate` | **人工回退** | reviewer 认为证据不足 | 仅 reviewer 显式操作 | reviewer 回退理由 |

#### 4.2.2 自动跃迁限制（不可自动跃迁规则）

以下跃迁**绝不可**由 AI 自动执行：

| 禁止的自动跃迁 | 原因 | 执行者 |
|--------------|------|--------|
| `ai_candidate` → `evidence_backed` | 必须有三条有效证据线支撑（阈值检查）；AI 不得自行决定"证据足够" | 阈值触发（自动检测阈值条件满足后可跃迁，但 AI 不得跳过阈值检查） |
| `evidence_backed` → `reviewer_confirmed` | 确认是人的决策，影响后续 CA/PA 分发 | 仅 reviewer |

**澄清**：`ai_candidate` → `evidence_backed` 的"自动"是指一旦 evidence_lines 累计 >= 3 条有效线，状态**自动**更新；但 AI **不能**将证据不足的情况标记为 evidence_backed。这不是"AI 可以自己决定跃迁"——而是"阈值检查通过后自动推进"。

#### 4.2.3 状态转换日志

每次状态转换必须记录 transition_log 条目：

```yaml
transition_log:
  - from_level: raw_statement
    to_level: ai_candidate
    trigger: auto          # auto | manual | threshold_met
    timestamp: "2026-07-16T10:30:00Z"
    detail: "AI 分析完成，生成 2 个候选根因（confidence: 1 medium, 1 low）"
```

### 4.3 三线阈值硬阻断

#### 4.3.1 有效证据线计数

从 §2 证据分类结果中计算 `valid_count`：

```
valid_count = COUNT(evidence_line WHERE category ∈ {fact, hypothesis} AND validity = valid)
```

**注意**：
- 只有 `category=fact` 或 `category=hypothesis` 且 `validity=valid` 的证据线才计入
- `category=unknown` 或 `category=gap` 不计入
- `validity=incomplete` 或 `validity=invalid` 不计入

#### 4.3.2 阈值判定规则

```
if valid_count >= 3:
    → 阈值结果: passed
    → 根因状态机上限: evidence_backed（满足条件后可跃迁）
    → 输出: "证据充足，valid_count = {N}，根因状态可推进至 evidence_backed"

if valid_count < 3:
    → 阈值结果: insufficient
    → 根因状态机硬上限: ai_candidate（不得超越）
    → 输出:
        - valid_count 值
        - gap_report: 缺口清单（所有 category=gap 或 validity≠valid 的证据线）
        - 建议: 在进入 evidence_backed 前补充至少 {3 - valid_count} 条有效证据线
    → 根因分析停留在 ai_candidate，confidence 不高于 medium
```

**硬阻断声明**：
- `valid_count < 3` 时，根因状态的 `current_level` **不得** 设为 `evidence_backed` 或 `reviewer_confirmed`
- 即使 AI 分析生成了 high confidence 的候选根因，没有证据支撑也不得推进状态
- 本 §4.3 只定义状态机内的门控条件；完整的三线阈值阻断策略（含证据缺口最小补充清单、禁止 confirmed 的硬编码检查和重新分析触发条件）由 ST-NRA-01（§7）实现

---

## §5 指标定义与降级

### 5.1 MetricDefinition 契约

六维分析中所有可量化的指标必须使用标准化的 MetricDefinition 模板进行定义和管理。

#### 5.1.1 模板字段

MetricDefinition 模板文件位于 `skills/reverse-analysis/templates/metric-definition.yaml`。每个指标定义包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `metric_id` | string | 是 | 指标唯一标识，格式 `m-{category}-{name}`，如 `m-p1p2-count` |
| `name` | string | 是 | 指标人类可读名称 |
| `dimension` | enum | 是 | 所属维度：root_cause / product_quality / escape / test_missed / improvement / comparison |
| `numerator.field` | string | 是 | 分子来源字段路径，如 `ticket.severity` |
| `numerator.filter` | string | 是 | 分子过滤条件，如 `severity in ('P1', 'P2')` |
| `denominator.field` | string | 否 | 分母来源字段路径；无分母指标此字段为空 |
| `denominator.filter` | string | 否 | 分母过滤条件 |
| `denominator.trusted` | boolean | 是 | 分母是否可信；**默认 false**，仅当外部提供且经过验证后才设为 true |
| `window.start` | date | 是 | 分析窗口起始（ISO 8601） |
| `window.end` | date | 是 | 分析窗口结束（ISO 8601） |
| `window.type` | enum | 是 | month / quarter / custom |
| `cutoff_date` | date | 是 | 数据截止日期（ISO 8601） |
| `metric_version` | string | 是 | 口径版本号，格式 `major.minor`（如 `1.0`） |
| `na_condition` | string | 是 | 何时标记 N/A（如"分母字段不可获取"） |
| `degraded_output` | string | 是 | 无可信分母或无窗口数据时的降级输出方式 |

#### 5.1.2 版本化规则

- **metric_version 变更必须触发 S2 全量重算**：当 MetricDefinition 的口径（numerator/denominator/filter/window 定义）发生变化时，metric_version 递增。
- **分析运行记录版本绑定**：`analysis_run.metric_versions` 记录本次分析使用的各项指标版本号。
- **版本追溯**：metric-definition.yaml 中以 YAML 多文档格式（`---` 分隔）记录每个指标的历史版本。

#### 5.1.3 指标管理约束

- **只读引用**：六维分析引擎只读取 MetricDefinition，不修改。
- **新增指标**：在 metric-definition.yaml 中添加新文档块，初始 metric_version = "1.0"。
- **修改口径**：不得直接修改已有版本；新增一个文档块，metric_version 递增。

### 5.2 无可信分母降级策略

#### 5.2.1 降级触发条件

以下任一条件满足时，触发降级输出：

| 条件 | 触发场景 |
|------|---------|
| `denominator.trusted = false` | 分母默认不可信，或外部提供的分母数据未通过验证 |
| 分母字段不可获取 | 如单位时间代码量、版本规模、测试用例总数等字段不存在或为空 |
| 分母与分子窗口不对齐 | 分母数据的时间窗口与分子数据不匹配 |
| `cutoff_date` 之前分母数据缺失 | 数据源不完整 |

#### 5.2.2 降级输出规则

降级时，分析只能输出以下四类信息：

| 允许输出 | 禁止输出 |
|---------|---------|
| **绝对数量**：如 "P1/P2 问题 12 个" | "缺陷密度"、"DPMO"、"每千行代码缺陷数" |
| **占比**：如 "模块 A 占总量 35%" | 任何以"密度"命名的指标 |
| **Pareto 分布**：按数量降序的模块/产品分布 | 以速率或比率为单位的输出（当分母不可信时） |
| **趋势方向**：rising/stable/falling（不给出具体幅度） | 变化率数值（仅当分子和分母都可信时方可输出变化率） |

#### 5.2.3 降级声明模板

当触发降级时，必须在 ra-report.yaml 的 `degraded_notice` 字段写入降级声明：

```
"因无法获取可信的{分母指标名称}，本报告仅输出绝对数量、Pareto 分布和趋势方向。
不得将此数据标注为'缺陷密度'或任何以密度/速率命名的指标。
如需启用密度计算，请提供经过验证的{分母数据源}并进行可信标记。"
```

#### 5.2.4 质量趋势降级

当时间序列数据不完整时：

| 条件 | 处理 |
|------|------|
| `ticket.openeddate` 缺失比例 > 30% | 不生成趋势图，标记 "no_temporal_data" |
| 连续两个窗口数据缺失 | 不生成趋势，标记 "insufficient_temporal_samples" |
| 单个窗口有数据但质量标记为 incomplete | 可生成趋势但附加 `trend_credibility: low` |

### 5.3 流出证据分类

#### 5.3.1 candidate vs confirmed escape layer 分离

流出分析的核心原则：**无控制证据不称 confirmed**。

```
confirmed escape layer 的条件（全部满足）：
  1. 存在该控制层的执行证据（如测试报告、评审记录、检查清单）
  2. 证据显示检查覆盖了与该问题相关的内容范围
  3. 证据来源可追溯（非匿名、非推测）

candidate escape layer 的条件（任一满足）：
  1. 缺少该控制层的执行证据
  2. 有执行证据但无法确认覆盖了该问题相关的范围
  3. 证据来自推断而非直接记录
```

#### 5.3.2 默认行为

当完全没有控制证据字段或所有控制证据都不足以 confirm 时：
- 所有 escape point 标记为 candidate
- `nearest_intercept` 标注 "无法确定，缺少控制证据"
- 输出说明："当前未提供各控制层的执行证据。以下逃逸点分析基于问题特征推断，标注为 candidate。如需确认，请提供各控制层的实际执行记录。"

#### 5.3.3 与 ra-report.yaml 的映射

```
EscapeAnalysis 输出映射：
  - 有证据支撑的控制层 → escape_analysis.confirmed_layers[]
  - 无证据的控制层 → escape_analysis.candidate_layers[]
  - 推理出的最近拦截点 → escape_analysis.nearest_intercept
```

**注意**：同一控制层不可同时出现在 confirmed_layers 和 candidate_layers 中。

---

## §6 S1 分析管线

### 6.1 管线入口

#### 6.1.1 触发条件与入口判定

S1 分析管线是 `reverse-analysis` Skill 的分析执行层，在资格检查（§1）、证据分类（§2）和六维分析引擎（§3-§5）就绪后，由 ptm-tse Agent 编排调用。入口判定规则：

```
输入类型判定:
  if 输入包含单个 source_ticket_id:
      → 进入 逐单分析管线（§6.2）
  elif 输入包含 batch_id 或时间窗口参数:
      → 进入 批量分析管线（§6.3）
  else:
      → blocked（"无法识别输入类型，请提供 source_ticket_id 或 batch_id"）
```

#### 6.1.2 输入验证

在进入管线前，必须完成以下验证：

| 验证项 | 规则 | 失败行为 |
|--------|------|---------|
| 数据就绪 | 调用 `get_batch(conn, batch_ref)` 确认批次存在 | blocked（"批次 {batch_ref} 不存在"） |
| 质量过滤 | ticket 必须满足 `quality_flag='clean'` | 过滤掉非 clean 的 ticket，在报告中记录 `skipped_tickets[]` |
| Schema 版本 | 从 `ingestion_batch.schema_version` 获取，缺失时降级为 `"unknown"` | 在 manifest 中标记 `schema_version = "unknown"` |
| 批次锁定 | 同一 batch_ref 已有 `in_progress` 状态的 analysis_run 时，阻止重复启动 | blocked（"批次 {batch_ref} 已有进行中的分析运行"） |

#### 6.1.3 批次锁定检查

```
def check_batch_lock(conn, batch_ref):
    existing_runs = get_runs_by_batch(conn, batch_ref)
    for run in existing_runs:
        if run["status"] in ("in_progress",):
            return False, run["run_id"]
    return True, None
```

批次锁定只阻止同批次并发分析；不同批次可并行执行。

---

### 6.2 逐单分析流程

#### 6.2.1 流程概览

```
输入: source_ticket_id + batch_ref
输出: ra-report（single_ticket 类型）+ analysis_run 记录

Step 1: 数据获取
Step 2: 资格检查（复用 §1）
Step 3: 证据分类（复用 §2）
Step 4: 六维分析（复用 §3-§5）
Step 5: 创建 AnalysisRunManifest 与 analysis_run 记录
Step 6: 输出报告草案
```

#### 6.2.2 Step 1: 数据获取

```
调用 get_ticket_by_source_id(conn, source_ticket_id)

if ticket 不存在:
    → blocked（"source_ticket_id {source_ticket_id} 在数据库中不存在"）
    → 不创建 analysis_run

if ticket.quality_flag != 'clean':
    → 状态取决于 quality_flag 值:
      - 'blocked': blocked（输出 IngestionQualityReport 引用）
      - 'incomplete'/'anomaly': 允许继续，附加风险标记
    → 非 blocked 情况继续分析

调用 get_batch(conn, batch_ref) 获取批次元数据:
  - schema_version: ticket.schema 版本
  - batch_id: 批次标识
```

**禁止**：读取 `ticket.raw_json` 列进入分析正文。

#### 6.2.3 Step 2: 资格检查（复用 §1）

执行 §1 定义的完整资格检查流程——获取 ticket 数据、空值与关键字段校验、质量前置检查、优先级判定、内部问题识别、无效 source_ticket_id 检查。

```
资格判定结果:
  - eligible → 继续 Step 3
  - eligible_on_request → 暂停，输出确认提示，等待 ptm-tse 回传确认结果
  - rejected → 停止，输出拒绝原因（不创建 analysis_run）
  - deferred → 停止，输出重新立项条件（不创建 analysis_run）
  - blocked → 停止，输出 blockage 原因（不创建 analysis_run）
```

#### 6.2.4 Step 3: 证据分类（复用 §2）

调用 §2 可信输入建立流程，产出：
- `EligibilityResult`：资格状态、阈值结果、max_rc_state
- `EvidenceLineSet`：五条证据线的分类（fact/hypothesis/unknown/gap）、validity、gap_report

#### 6.2.5 Step 4: 六维分析（复用 §3-§5）

逐单模式下依次执行六个维度。**逐单限制**：
- 根因维度（§3.2.1）：可执行完整流程
- 产品质量维度（§3.2.2）：单 ticket 无聚合意义，只输出该 ticket 的严重度/模块/状态信息，不计算 Pareto/趋势
- 流出维度（§3.2.3）：可执行完整流程
- 漏测维度（§3.2.4）：可执行完整流程
- 改进维度（§3.2.5）：可执行完整流程
- **环比同比维度（§3.2.6）：逐单模式不适用**，因为需要两个完整时间窗口的同口径对比数据。输出 `comparison.mode = "none"`，`na_reasons = ["逐单分析不支持环比同比，请使用批量分析模式"]`

逐单模式下的降维处理：

| 维度 | 逐单行为 |
|------|---------|
| RC | 正常执行（单个 ticket 的根因分析） |
| PQ | 仅输出 ticket 基础信息（product/module/severity/status），不生成 Pareto/趋势/密度 |
| ESC | 正常执行 |
| TM | 正常执行 |
| IMP | 正常执行 |
| CMP | **跳过** — comparison.mode="none" |

#### 6.2.6 Step 5: 创建 AnalysisRunManifest 与 analysis_run 记录

```
生成 analysis_run_id:
  格式: {batch_ref}-{timestamp}-{short_uuid}
  示例: batch_20260716_001-20260716T103000Z-a3f2

创建 AnalysisRunManifest（参见 §6.5）:
  - recompute_mode = "full"
  - report_refs 包含 1 条记录: type=single_ticket, ticket_refs=[source_ticket_id]

插入 analysis_run 记录:
  insert_analysis_run(conn, {
    "run_id": manifest.analysis_run_id,
    "batch_ref": manifest.batch_ref,
    "comparison_batch_ref": null,
    "schema_version": manifest.schema_version,
    "mapping_version": manifest.mapping_version,
    "rule_version": manifest.rule_version,
    "time_window_start": manifest.window.start,
    "time_window_end": manifest.window.end,
    "recompute_mode": "full",
    "report_refs": manifest.report_refs,
    "metric_versions": manifest.rule_version
  })

状态初始为 'created'，分析进行中更新为 'in_progress'，分析完成后更新为 'completed'
```

**注意**：`insert_analysis_run` 返回的 `status` 列由 DAO 默认值设为 `'created'`。Skill 调用方必须在分析步骤开始时通过 `update_analysis_run_draft` 更新为 `'in_progress'`，完成后更新为 `'completed'` 或 `'failed'`。

#### 6.2.7 Step 6: 输出报告草案

逐单分析输出结构：

```yaml
# ra-report（single_ticket 类型）草案结构
report_id: "{analysis_run_id}-single"
report_type: single_ticket
analysis_run_id: "{analysis_run_id}"
ticket_ref: "ITR-2026-0001"
created_at: "2026-07-16T10:30:00Z"

eligibility:
  status: eligible
  reason: "P1 事件，必做分析"
  threshold:
    valid_count: 4
    result: passed
    max_rc_state: evidence-backed

sections:
  root_cause:
    raw_statement: "..."
    current_level: ai_candidate
    ai_candidates: [...]
    transition_log: [...]

  product_quality:
    ticket_info:
      product: "ProductA"
      module: "ModuleX"
      severity: "P1"
      status: "resolved"
    note: "逐单模式，不生成聚合统计"

  escape_analysis:
    confirmed_layers: []
    candidate_layers: [...]
    nearest_intercept: "..."

  test_missed:
    ppdcs_category: "Detection"
    missed_pattern: "..."
    recommended_test_method: "..."

  improvement_candidates:
    capa_items: [...]

  comparison:
    mode: none
    na_reasons: ["逐单分析不支持环比同比，请使用批量分析模式"]

degraded_notice: null
```

---

### 6.3 批量分析流程

#### 6.3.1 流程概览

```
输入: batch_id 或时间窗口参数
输出: ra-report（batch_summary 类型）+ per-ticket ra-reports + analysis_run 记录

Step 1: 批量数据获取
Step 2: 逐单资格检查
Step 3: 逐单六维分析
Step 4: 聚合分析
Step 5: 创建 AnalysisRunManifest 与 analysis_run 记录
Step 6: 输出聚合报告
```

#### 6.3.2 Step 1: 批量数据获取

```
调用 get_tickets_by_batch(conn, batch_ref)
  → 该 DAO 方法已内置 quality_flag='clean' 过滤，通过 ticket_version 关联
  → 返回 ticket 列表

if 返回空列表:
    → blocked（"批次 {batch_ref} 中没有 quality_flag='clean' 的可分析 ticket"）
    → 不创建 analysis_run

调用 get_batch(conn, batch_ref) 获取:
  - schema_version
  - batch_id
```

**批量规模提示**：当 ticket 数量 > 100 时，应输出性能提示："批量分析 {N} 条 ticket，建议分批执行或预期较长处理时间"（OPEN-RA053-03）。

#### 6.3.3 Step 2: 逐单资格检查

对批量中每条 ticket 独立执行 §1 资格检查：

```
for each ticket in tickets:
    eligibility = eligibility_check(ticket)
    if eligibility.status == "eligible":
        eligible_queue.append(ticket)
    elif eligibility.status == "eligible_on_request":
        pending_confirm_queue.append(ticket)
    else:
        skipped_tickets.append({
            "ticket_ref": ticket.source_ticket_id,
            "eligibility": eligibility.status,
            "reason": eligibility.reason
        })
```

`eligible_on_request`（P2 事件）的处理策略：
- 批量模式下，P2 事件默认不阻塞管线
- 在报告中列出 `pending_confirm_queue[]`（状态为 `eligible_on_request` 的 ticket）
- 后续 ptm-tse 可单独对这些 ticket 发起逐单确认
- 批量报告正文仅覆盖 `eligible` 的 ticket

#### 6.3.4 Step 3: 逐单六维分析

对每个 eligible ticket 独立执行 §3-§5 六维分析。

批量模式下的维度行为：

| 维度 | 逐单阶段行为 | 聚合阶段行为 |
|------|------------|------------|
| RC | 每个 ticket 独立根因分析 | 高频根因模式识别（见 §6.3.5） |
| PQ | 每个 ticket 记录 product/module/severity/status | 模块/严重度聚合 → Pareto + 趋势（见 §6.3.5） |
| ESC | 每个 ticket 独立流出分析 | 逃逸模式聚合（见 §6.3.5） |
| TM | 每个 ticket 独立 PPDCS 归类 | PPDCS 归类统计（见 §6.3.5） |
| IMP | 每个 ticket 独立 CA/PA 候选 | CA/PA 去重与优先级排序（见 §6.3.5） |
| CMP | — | **批量下可用**：按时间窗口聚合环比同比（见 §6.3.5） |

**维度错误处理**：

| 场景 | 处理方式 |
|------|---------|
| 某 ticket 的某个维度分析失败 | 跳过该维度，其余维度继续 |
| 某 ticket 的所有维度都失败 | 该 ticket 标记为 `failed`，在报告中记录 `failed_tickets[]` |
| 全部 ticket 的某个维度都失败 | 该维度在聚合报告中标记 `skipped` |

逐单分析完成后，输出每个 ticket 的 per-ticket sections，存储为中间结果供聚合使用。

#### 6.3.5 Step 4: 聚合分析

基于所有 eligible ticket 的逐单分析结果，执行跨 ticket 聚合：

**4a. 根因聚合**：

```
收集所有 ticket 的根因分析结果:
  - 将所有 ai_candidates 按 hypothesis 文本相似度聚类
  - 输出高频根因模式:
      pattern: "高频根因描述"
      frequency: 出现次数
      affected_tickets: [ticket_refs...]
      confidence_distribution: {high: N, medium: N, low: N}

输出: root_cause_patterns[]
```

**4b. 产品质量聚合**：

```
按维度分组聚合（复用 §3.2.2 方法）:
  - 按 product 分组 → product_distribution[]
  - 按 module 分组 → top_risk_modules[]（Pareto 排序）
  - 按 severity 分组 → severity_distribution[]
  - 按 status 分组 → status_distribution[]
  - 按 openeddate 时间序列 → quality_trend（rising/stable/falling）

输出: product_quality_aggregation
```

**4c. 流出聚合**：

```
收集所有 ticket 的流出分析:
  - 统计各控制层被标记为 candidate/confirmed 的频次
  - 识别高频逃逸点:
      escape_layer: "单元测试"
      candidate_count: 12
      confirmed_count: 3

输出: escape_point_frequency[]
```

**4d. 漏测聚合**：

```
统计 PPDCS 分类分布:
  - Prevention: N tickets
  - Protection: N tickets
  - Detection: N tickets
  - Containment: N tickets
  - Sustainment: N tickets
  - unknown: N tickets

输出: ppdcs_distribution[]
```

**4e. 改进聚合**：

```
收集所有 ticket 的 CA/PA 候选:
  - 按 target 相似度去重
  - 按 priority 排序（P0 > P1 > P2 > P3）
  - 按出现频率排序（同一 target 被多个 ticket 提出时提升优先级）

输出: aggregated_capa_items[]
  注意: 所有 capa_items 状态为 draft，候选的批准仍需要 reviewer 确认
```

**4f. 环比同比（批量模式可用）**：

批量模式下，如果提供了 `comparison_batch_ref`，执行完整的 §3.2.6 环比同比分析。

调用 `get_tickets_by_batch(conn, comparison_batch_ref)` 获取基期数据，按完整时间窗口执行同口径聚合。

如果未提供 `comparison_batch_ref`：
- `comparison.mode = "none"`
- `na_reasons = ["未提供 comparison_batch_ref"]`

#### 6.3.6 Step 5: 创建 AnalysisRunManifest 与 analysis_run 记录

```
生成 analysis_run_id:
  格式: {batch_ref}-{timestamp}-{short_uuid}

创建 AnalysisRunManifest:
  - recompute_mode = "full"
  - report_refs 包含:
      1 条 batch_summary 类型的聚合报告
      N 条 single_ticket 类型（每个 eligible ticket 一条，可选单独释放）

插入 analysis_run 记录（同逐单模式 §6.2.6 Step 5）

调用 update_analysis_run_draft 更新状态:
  - created → in_progress（分析开始时）
  - in_progress → completed（分析成功完成）
  - in_progress → failed（任一步骤失败）
```

#### 6.3.7 Step 6: 输出聚合报告

批量分析输出结构：

```yaml
# ra-report（batch_summary 类型）草案结构
report_id: "{analysis_run_id}-batch"
report_type: batch_summary
analysis_run_id: "{analysis_run_id}"
batch_ref: "batch_20260716_001"
ticket_count: 50
eligible_count: 45
skipped_count: 3
failed_count: 2

sections:
  root_cause:
    patterns: [...]

  product_quality:
    product_distribution: [...]
    top_risk_modules: [...]
    severity_distribution: [...]
    quality_trend: "stable"

  escape_analysis:
    escape_point_frequency: [...]

  test_missed:
    ppdcs_distribution: [...]

  improvement_candidates:
    aggregated_capa_items: [...]

  comparison:
    mode: full  # 或 none
    changes: [...]  # 环比同比结果

skipped_tickets:
  - ticket_ref: "ITR-2026-0005"
    reason: "P3 事件，自动拒绝"
  - ticket_ref: "ITR-2026-0008"
    reason: "标记为内部问题（deferred）"

failed_tickets:
  - ticket_ref: "ITR-2026-0012"
    failed_dimensions: ["root_cause"]
    reason: "根因字段为空，无法执行分析"

pending_confirm:
  - ticket_ref: "ITR-2026-0015"
    status: eligible_on_request
    reason: "P2 事件，需显式确认"

degraded_notice: null
```

---

### 6.4 analysis_run 管理

#### 6.4.1 状态生命周期

```
created ──► in_progress ──► completed
                │
                └──► failed（任一步骤失败）
```

| 状态 | 含义 | 进入条件 | 退出条件 | 操作者 |
|------|------|---------|---------|--------|
| `created` | analysis_run 记录已创建，未开始分析 | `insert_analysis_run()` 完成 | 开始执行分析 → `in_progress` | Skill（通过 DAO） |
| `in_progress` | 分析管线执行中 | 任何分析步骤开始 | 所有步骤完成 → `completed`；任一步骤失败 → `failed` | Skill（通过 DAO） |
| `completed` | 分析完成，ra-report 已生成 | 所有维度分析成功 | reviewer 确认 → `published` | Skill（通过 DAO） |
| `failed` | 分析过程中错误 | 资格拒绝/数据不可用/六维异常/SQLite 写入失败 | 不可自动重试；需重新发起新的 analysis_run | Skill（通过 DAO） |
| `published` | reviewer 人工确认发布 | `reviewer_publish_analysis_run()` | 不可回退 | reviewer（通过 DAO） |

#### 6.4.2 状态转换 API

所有状态转换必须通过 `data/dao.py` 的公共接口执行，禁止直接 SQL：

| 转换 | API | 说明 |
|------|-----|------|
| 创建 run | `insert_analysis_run(conn, run_dict)` | 初始状态为 `created`（DAO 默认值） |
| created → in_progress | `update_analysis_run_draft(conn, run_id, "in_progress", report_refs)` | 分析开始时调用 |
| in_progress → completed | `update_analysis_run_draft(conn, run_id, "completed", report_refs)` | 分析成功完成时调用 |
| in_progress → failed | `update_analysis_run_draft(conn, run_id, "failed", report_refs)` | 分析失败时调用 |
| completed → published | `reviewer_publish_analysis_run(conn, run_id, reviewer_ref)` | **仅 reviewer 可调用** |

#### 6.4.3 状态转换安全约束

| 约束 | 规则 |
|------|------|
| **不可自动发布** | `update_analysis_run_draft` 禁止将 status 设为 `'published'`；DAO 层有硬编码检查，传入 `'published'` 会抛出 `ValueError` |
| **不可跨状态跳转** | created 不能直接到 completed，必须经过 in_progress |
| **不可从 failed 恢复** | failed 状态的 run 不可重新激活；需新建 run |
| **不可修改已完成/已发布的 run** | completed 和 published 状态的 run 不可通过 `update_analysis_run_draft` 修改 |

#### 6.4.4 错误处理与回退

| 场景 | analysis_run 状态 | 输出 |
|------|-----------------|------|
| 批次无 clean ticket | —（不创建 run） | "批次 {batch_ref} 中没有可分析数据" |
| 全部 ticket 资格拒绝 | —（不创建 run） | skipped_tickets 清单 |
| 数据获取失败（SQLite 连接错误） | failed | 错误详情 |
| analysis_run INSERT 失败 | —（未创建） | SQLite 写入错误 |
| 某维度分析部分失败 | completed（部分完成） | 失败维度标记 skipped + 原因 |

---

### 6.5 AnalysisRunManifest

#### 6.5.1 模板定义

AnalysisRunManifest 是每次分析运行的元数据记录，模板文件位于 `skills/reverse-analysis/templates/analysis-run-manifest.yaml`。

完整字段定义：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `analysis_run_id` | string | 是 | 分析运行唯一标识，格式 `{batch_ref}-{timestamp}-{short_uuid}` |
| `batch_ref` | string | 是 | 数据来源批次引用，对应 `ingestion_batch.batch_id` |
| `comparison_batch_ref` | string \| null | 否 | 环比同比对比批次引用；S1 逐单为 null，S1 批量可选，S2 必填 |
| `schema_version` | string | 是 | SQLite schema 版本，来自 `ingestion_batch.schema_version`；缺失时降级为 `"unknown"` |
| `mapping_version` | string | 是 | 字段映射规则版本；缺失时降级为 `"unknown"` |
| `rule_version` | string | 是 | 分析规则版本，来自 `metric-definition.yaml` 的 `metric_version` |
| `window` | object | 是 | 分析时间窗口 |
| `window.start` | date | 是 | 分析窗口起始（ISO 8601，含） |
| `window.end` | date | 是 | 分析窗口结束（ISO 8601，含） |
| `recompute_mode` | enum | 是 | 重算模式：`full`（全量）或 `incremental`（增量）；S1 固定为 `full` |
| `full_recompute_reason` | string \| null | 否 | 当 `recompute_mode=full` 时的重算原因；非 S1 首次分析时填写 |
| `status` | enum | 是 | 分析运行状态：`created` / `in_progress` / `completed` / `failed` / `published` |
| `report_refs` | array | 是 | 关联的报告引用列表 |
| `report_refs[].report_id` | string | 是 | 报告唯一标识，格式 `{analysis_run_id}-{type}` |
| `report_refs[].type` | enum | 是 | 报告类型：`single_ticket` / `batch_summary` / `difference`（S2） |
| `report_refs[].ticket_refs` | array | 是 | 关联的 ticket 引用（source_ticket_id 列表）；batch_summary 时列出所有 ticket |
| `created_at` | datetime | 是 | 清单创建时间（ISO 8601） |
| `created_by` | string | 是 | 调用方标识（ptm-tse Agent 标识） |

#### 6.5.2 逐单与批量的差异

| 字段 | 逐单分析 | 批量分析 |
|------|---------|---------|
| `comparison_batch_ref` | `null` | `null`（S1）或指定批次（需环比同比时） |
| `recompute_mode` | `full` | `full` |
| `report_refs` | 1 条（type=single_ticket） | 1 条 batch_summary + N 条 single_ticket（可选） |
| `report_refs[].ticket_refs` | `[source_ticket_id]` | batch_summary 时列出所有 eligible ticket；single_ticket 时各自独立 |

#### 6.5.3 Manifest 与 DAO 的映射

Manifest 字段到 `insert_analysis_run` 参数的映射：

```python
insert_analysis_run(conn, {
    "run_id": manifest.analysis_run_id,
    "batch_ref": manifest.batch_ref,
    "comparison_batch_ref": manifest.comparison_batch_ref,  # S1 为 None
    "schema_version": manifest.schema_version,
    "mapping_version": manifest.mapping_version,
    "rule_version": manifest.rule_version,
    "time_window_start": manifest.window.start,
    "time_window_end": manifest.window.end,
    "recompute_mode": manifest.recompute_mode,
    "full_recompute_reason": manifest.full_recompute_reason,  # S1 首次分析通常为 None
    "report_refs": json.dumps(manifest.report_refs),
    "metric_versions": manifest.rule_version,
})
```

**注意**：`report_refs` 在 DAO 中以 JSON 字符串存储；manifest 中为结构化 YAML 对象，传入 DAO 前需序列化为 JSON 字符串。`created_at` 由 DAO 的 `DEFAULT (datetime('now'))` 自动生成，不在 manifest 写入时指定。

---

### 6.6 报告草案输出

#### 6.6.1 报告类型

| 类型 | 产生场景 | 包含内容 |
|------|---------|---------|
| `single_ticket` | S1 逐单分析 | 单 ticket 的六维分析结果 + eligibility + evidence_set |
| `batch_summary` | S1 批量分析 | 聚合趋势 + 模式识别 + per-ticket 子引用 + skipped_tickets + pending_confirm |
| `difference` | S2 增量分析 | 当前 vs 基期的 difference report（ST-RA-06.2 实现） |

#### 6.6.2 输出结构契约

所有报告草案必须包含以下顶层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `report_id` | string | 报告唯一标识 |
| `report_type` | enum | single_ticket / batch_summary / difference |
| `analysis_run_id` | string | 关联的 analysis_run.run_id |
| `created_at` | datetime | 报告生成时间（ISO 8601） |
| `sections` | object | 六维分析结果（维度名 → 分析输出） |
| `degraded_notice` | string \| null | 降级声明（无可信分母/数据不完整时必填） |

#### 6.6.3 reports_refs 关联

每条报告在 AnalysisRunManifest 的 `report_refs[]` 中对应一条记录：

```yaml
report_refs:
  - report_id: "batch_20260716_001-20260716T103000Z-a3f2-batch"
    type: batch_summary
    ticket_refs:
      - "ITR-2026-0001"
      - "ITR-2026-0002"
      - "ITR-2026-0003"
  - report_id: "batch_20260716_001-20260716T103000Z-a3f2-single-0001"
    type: single_ticket
    ticket_refs:
      - "ITR-2026-0001"
  - report_id: "batch_20260716_001-20260716T103000Z-a3f2-single-0002"
    type: single_ticket
    ticket_refs:
      - "ITR-2026-0002"
```

**注意**：per-ticket single_ticket 报告是可选的单独释放。默认推荐：聚合报告中内嵌 per-ticket sections，通过 batch_summary 的 ticket_refs 引用所有 ticket；仅在需要独立传递时单独释放 single_ticket 报告文件（OPEN-RA053-02）。

---

### 6.7 reviewer 发布路径

#### 6.7.1 发布流程

```
completed ──(reviewer_publish_analysis_run)──► published
```

Analysis run 的发布是**人工门控操作**，由 reviewer 通过 ptm-tse Agent 显式确认后执行。

#### 6.7.2 API 调用

```
reviewer_publish_analysis_run(conn, run_id, reviewer_ref)

前置条件:
  - analysis_run 当前状态必须为 'completed'
  - reviewer_ref 非空

成功:
  - analysis_run.status → 'published'
  - analysis_run.published_by ← reviewer_ref
  - analysis_run.published_at ← 当前时间

失败:
  - run_id 不存在 → 返回 False
  - 当前状态不是 'completed' → 抛出 ValueError("只能发布状态为 'completed' 的分析运行")
```

#### 6.7.3 安全约束

| 约束 | 说明 |
|------|------|
| **不可自动发布** | Skill 内任何步骤不得调用 `reviewer_publish_analysis_run`；该接口只能由 ptm-tse Agent 在 reviewer 显式确认后调用 |
| **不可通过草案接口发布** | `update_analysis_run_draft` 在 DAO 层硬编码拒绝 `status='published'`，传入即抛出 `ValueError` |
| **不可从未完成状态发布** | `reviewer_publish_analysis_run` 在 DAO 层校验 `current["status"] != "completed"` 时抛出 `ValueError` |
| **不可回退** | published 状态没有回退到 completed/draft 的 API；如需修正，必须创建新的 analysis_run |
| **发布前检查** | reviewer 应在调用发布接口前完成以下人工检查：六维覆盖完整性、阈值通过情况、权限合规、敏感信息脱敏 |

#### 6.7.4 发布前人工检查清单

reviewer 确认发布前，应验证：

1. 六维分析覆盖完整（无意外 skip）
2. 根因状态机推进合理（evidence_backed 或 reviewer_confirmed 有依据）
3. 阈值检查通过（valid_count >= 3）或 gap report 已充分说明
4. 无可信分母时降级声明已写入 degraded_notice
5. 流出分析的 candidate/confirmed 分离正确
6. CA/PA 候选草案的 basis 可追溯
7. 报告不含 ticket.raw_json 等敏感字段
8. 环比同比（如有）的基期/当期窗口同口径对齐

---

## §7 证据不足保护

> **实现者**：ST-NRA-01（证据不足保护 — 拒绝虚假根因）
>
> 本章是本 Skill 的负向防护层。不新增分析功能，只在证据不足时强制执行降级输出，禁止 AI 伪造结论。
> 前置依赖：§2 可信输入建立（证据线分类与 gap_owner）、§4 根因状态机（三线阈值硬阻断）。

### 7.1 证据线阈值硬阻断

#### 7.1.1 阻断规则

```
在以下条件全部满足时，触发证据不足硬阻断：

条件 A：valid_count < 3
  - valid_count = COUNT(evidence_line WHERE category ∈ {fact, hypothesis} AND validity = valid)
  - 来源：§2.4 三线阈值检查、§4.3 三线阈值硬阻断

条件 B：missing_lines 中存在 category=gap 且 gap_owner 已明确的证据线
  - 来源：§2.3.2 gap_owner 分类

触发结果：
  → 根因状态机硬上限: ai_candidate（不得超越）
  → 根因 current_level 已被 §4.3 限制；本 §7.1 追加二次校验
  → 置信度上限: medium（即使 AI 分析生成了 high confidence 的候选根因）
```

#### 7.1.2 二次校验步骤

§4.3 已在状态机层级设置 `max_rc_state = ai_candidate`，但为避免跨模块调用时遗漏检查，本 Skill 在以下两个时机执行二次校验：

| 校验时机 | 触发条件 | 校验内容 | 失败动作 |
|---------|---------|---------|---------|
| **分析输出前** | 即将写入 `ra-report.yaml` 的 `sections.root_cause.current_level` | 再次计算 `valid_count`，确认 `valid_count < 3` 时 `current_level` 不得为 `evidence_backed` 或 `reviewer_confirmed` | 强制覆盖 `current_level = ai_candidate`，追加 `transition_log` 项注明 "hard-blocked by §7.1" |
| **report_refs 写入前** | 即将更新 `analysis_run.report_refs` | 扫描所有关联报告的 `sections.root_cause.current_level`，确认无 `evidence_backed` 或 `reviewer_confirmed` 出现在 `valid_count < 3` 的 ticket 上 | 拒绝写入，输出阻断清单，要求调用方修复后重试 |

#### 7.1.3 阈值不可降级

```
禁止行为：
  ❌ 不得因"valid_count 接近 3"而放宽阈值
  ❌ 不得将 category=unknown 的证据线手动升级为 hypothesis 以凑数
  ❌ 不得将 validity=incomplete 的证据线标记为 valid 以凑数
  ❌ 不得将非结构化推测包装为 fact 类证据线
  ❌ 不得因 reviewer 催促而绕过阈值

允许行为：
  ✅ 在 ra-report 中输出 gap_report，明确缺少哪些证据线（来源：§2.5 gap_report）
  ✅ 在 ra-report 的 degraded_notice 中声明"证据不足，根因分析停留在 ai_candidate"
  ✅ 输出最小补充清单（至少需要 N 条有效证据线才能推进到 evidence_backed）
```

### 7.2 缺失证据分类

#### 7.2.1 扩展 gap_owner 分类

§2.3.2 已定义基础 `gap_owner` 分类（"PTM-TSE/测试架构师"、"ITR 录入方/产品团队"、"待确认"）。本节从保护视角扩展为四类 gap_source，用于生成证据不足报告时的根因分析：

| gap_source | 含义 | 典型场景 | 补充方向 |
|-----------|------|---------|---------|
| **ITR 缺失** | ITR 问题单中相关字段为空或未填写 | `root_cause`、`description`、`test_missed_analysis`、`improvement_measures` 为空 | 回溯 ITR 录入流程，要求提交人补充 |
| **测试缺失** | 测试环节未产生可用的分析证据 | 无测试报告、无漏测分析记录、无测试用例覆盖数据 | 补充对应版本的测试执行记录和漏测复盘 |
| **流程缺失** | 相关控制层（需求评审/设计评审/代码评审/发布检查）未执行或未留痕 | 流出分析的所有控制层都是 candidate 状态（§5.3.2） | 补充控制层执行证据或流程改进记录 |
| **外部依赖** | 所需数据来自外部系统，当前不可获取 | 代码量数据（分母）、监控告警记录、部署记录 | 从数据源获取或标记为不可获取后降级处理 |

#### 7.2.2 与 §2.3.2 gap_owner 的关系

§2.3.2 的 `gap_owner` 回答"谁负责补充"（人员维度），§7.2.1 的 `gap_source` 回答"缺失原因"（根因维度）。两者在证据不足报告中**同时输出**：

```yaml
# 证据不足报告中的缺口条目示例
gap_item:
  line_id: "L1"
  category: gap
  gap_owner: "PTM-TSE/测试架构师"       # 来自 §2.3.2
  gap_source: "ITR 缺失"                 # 来自 §7.2.1
  detail: "root_cause 字段为空，无法建立根因证据线"
  min_supplement: "从 ITR-2026-0001 的问题描述中提取根因信息，或要求提交人补充 root_cause 字段"
```

#### 7.2.3 缺口分类优先级

当一条证据线同时命中多个 gap_source 时，按以下优先级归入最根本的原因：

```
优先级: ITR 缺失 > 测试缺失 > 流程缺失 > 外部依赖

示例：
  - L2（漏测证据）的 test_missed_analysis 为空 → 首先检查是否为 ITR 缺失
  - 如果 test_missed_analysis 有值但测试报告不可获取 → 归入测试缺失
  - 如果测试执行了但无留痕 → 归入流程缺失
```

### 7.3 证据不足降级输出

#### 7.3.1 证据不足报告结构

当 §7.1 硬阻断触发（`valid_count < 3`）时，Skill 不得输出标准的 ra-report 分析结论。替代输出结构如下：

```yaml
# 证据不足报告（替代标准 ra-report sections）
report_id: "{analysis_run_id}-insufficient-evidence"
report_type: insufficient_evidence    # 专用报告类型
analysis_run_id: "{analysis_run_id}"
ticket_ref: "ITR-2026-0001"
created_at: "2026-07-16T10:30:00Z"

insufficient_evidence:
  threshold:
    valid_count: 2
    required: 3
    result: insufficient

  current_state:
    root_cause_level: ai_candidate    # 硬上限，不可超越
    max_confidence: medium            # 置信度硬上限
    blocked_at: "2026-07-16T10:30:00Z"
    blocked_by: "§7.1 证据不足硬阻断"

  gap_summary:
    total_lines: 5
    valid_lines: 2                     # L4（现象/环境）、L5（上下文/归属）
    missing_lines: 3                   # L1（根因）、L2（漏测）、L3（改进措施）
    min_supplement_needed: 1           # 还需 1 条有效证据线方可推进

  gap_details:
    - line_id: "L1"
      evidence_type: "根因证据"
      gap_owner: "PTM-TSE/测试架构师"
      gap_source: "ITR 缺失"
      reason: "root_cause 字段为空"
      supplement_action: "要求 ITR 提交人补充根因描述，或从 description 字段提取根因线索"

    - line_id: "L2"
      evidence_type: "漏测证据"
      gap_owner: "PTM-TSE/测试架构师"
      gap_source: "ITR 缺失"
      reason: "test_missed_analysis 字段为空"
      supplement_action: "补充测试遗漏分析记录"

    - line_id: "L3"
      evidence_type: "改进措施证据"
      gap_owner: "PTM-TSE/测试架构师"
      gap_source: "ITR 缺失"
      reason: "improvement_measures 字段为空"
      supplement_action: "补充已采取或建议的改进措施"

  available_evidence:                  # 仍输出已有证据线，不丢弃
    - line_id: "L4"
      category: fact
      validity: valid
      source: "description"
      summary: "..."
    - line_id: "L5"
      category: fact
      validity: valid
      source: "module"
      summary: "..."

  degraded_notice: >
    证据不足：仅有 2/5 条有效证据线（需要 ≥3 条）。
    根因分析停留在 ai_candidate，未生成 evidence_backed 或 reviewer_confirmed 结论。
    补充至少 1 条有效证据线后，可重新触发分析以推进根因状态。
    本次分析不产生 CA/PA 候选（来源：§3.2.5 Step IMP-1，前置条件不满足）。

prohibited_outputs:                    # 明确声明未生成的内容
  - "evidence_backed 根因"
  - "reviewer_confirmed 根因"
  - "CA/PA 候选草案"
  - "缺陷密度或 DPMO 指标"
  - "confirmed escape layer"
```

#### 7.3.2 与标准报告的关系

| 场景 | 输出类型 | `sections` 内容 |
|------|---------|----------------|
| `valid_count >= 3` | 标准 ra-report（`single_ticket` 或 `batch_summary`） | 完整六维 sections（§6.2.7） |
| `valid_count < 3` | 证据不足报告（`insufficient_evidence`） | 仅 `insufficient_evidence` 段 + `available_evidence` |
| 部分 ticket 证据不足（批量模式） | 标准 ra-report + 内嵌证据不足标记 | 逐 ticket 输出，证据不足的 ticket 在 `failed_tickets[]` 中标记 "insufficient_evidence_line"，其余正常分析 |

#### 7.3.3 重新分析触发条件

证据不足报告不是终点。满足以下**全部**条件后，可重新发起分析：

```
1. 缺失的证据线已被补充（至少 1 条，使得 valid_count >= 3）
2. 补充的证据线来源可追溯（明确来自 ITR 字段补充、测试记录回溯或流程证据补录）
3. 补充后的 evidence_set 经过 §2.3 重新分类
4. 新的 analysis_run 创建（不可复用原失败的 run；§6.4.3 不可从 failed 恢复）
5. 重新分析不跳过资格检查（§1）和证据分类（§2）
```

### 7.4 禁止行为清单

本节定义证据不足场景下的强制禁止项。违反任一条，调用方（ptm-tse Agent）必须判定分析无效并拒绝发布。

#### 7.4.1 禁止伪造结论

| 编号 | 禁止行为 | 触发条件 | 严重度 |
|------|---------|---------|--------|
| P-01 | 禁止在 `valid_count < 3` 时将根因状态设为 `evidence_backed` 或 `reviewer_confirmed` | `valid_count < 3` | **阻断** |
| P-02 | 禁止在有 `category=gap` 的证据线未补充前，宣称"根因已确认" | 存在未补充的 gap 线 | **阻断** |
| P-03 | 禁止在 gap_report 非空时，输出完整六维 sections（假装分析已完成） | `gap_report` 存在且 `gap_details[].line_id` 覆盖 L1/L2/L3 | **阻断** |
| P-04 | 禁止在 `valid_count < 3` 时生成 CA/PA 候选（即使 §3.2.5 Step IMP-1 条件看似满足） | `valid_count < 3` | **阻断** |

#### 7.4.2 禁止填补缺失证据

| 编号 | 禁止行为 | 原因 | 严重度 |
|------|---------|------|--------|
| P-05 | 禁止 AI 为空的 `root_cause`、`test_missed_analysis` 等字段生成虚构值 | AI 无权限无依据"创作"证据，属于伪造 | **阻断** |
| P-06 | 禁止从 `raw_json` 中提取未映射到清洗后列的数据作为证据线 | `raw_json` 不入分析正文（§1.2 Step 1 禁止读取） | **阻断** |
| P-07 | 禁止用"典型场景推测"填充缺失的 `description` 或 `module` | 推测不是证据，必须标注 hypothesis + confidence=low | **阻断** |
| P-08 | 禁止将其他 ticket 的证据线"借用"到当前 ticket 补齐缺口 | 每 ticket 证据独立，不得跨单补证 | **阻断** |

#### 7.4.3 禁止降级阈值

| 编号 | 禁止行为 | 原因 | 严重度 |
|------|---------|------|--------|
| P-09 | 禁止将三线阈值从 3 降为 2 或 1 | Threshold=3 来自 HLD §1.1 设计基准，不可运行时修改 | **阻断** |
| P-10 | 禁止将 `valid_count >= 3` 的逻辑用 `>= 2` 替代 | 等价于降级阈值 | **阻断** |
| P-11 | 禁止接受"validity=incomplete"或"category=unknown"的证据线计入 valid_count | §2.4.1 明确定义只有 valid 且 fact/hypothesis 才计入 | **阻断** |

#### 7.4.4 违规检测与上报

Skill 本身不执行运行时违规检测（检测由 ptm-tse Agent 在调用 Skill 前后执行），但本 §7.4 的禁止清单是**强契约**。任何调用方（ptm-tse Agent、reviewer）在发现违反上述禁止项时，必须：

1. 标记当前 analysis_run 为 `failed`
2. 在 `transition_log` 中记录违反的 P-xx 编号和现场
3. 不调用 `reviewer_publish_analysis_run`
4. 创建新的 analysis_run 重新分析（不可复用失败 run）

### 7.5 本 §7 的适用范围

| 维度 | 适用范围 |
|------|---------|
| **覆盖分析模式** | S1 逐单分析（§6.2）、S1 批量分析（§6.3） |
| **覆盖报告类型** | `single_ticket`、`batch_summary`、`insufficient_evidence` |
| **覆盖根因状态** | `raw_statement`、`ai_candidate`（硬阻断生效时最多到此） |
| **不覆盖** | S2 增量分析（ST-RA-06.2 实现，但 S2 复用的 evidence_set 分类规则本应继承 §7 的硬阻断） |
| **不覆盖** | CA/PA 批准与分发（ST-RA-03）、measure_link 写入（ST-RA-06.3-TRACK） |

### 7.6 与其他章节的关系

| 章节 | 关系 | 说明 |
|------|------|------|
| §2.4 三线阈值检查 | **复用 + 增强** | §2.4 计算 valid_count，§7.1 基于此执行二次校验 |
| §2.3.2 gap_owner | **扩展** | §2.3.2 定义基础 gap_owner，§7.2 扩展 gap_source 分类 |
| §2.5 gap_report | **消费** | §7.3 的证据不足报告引用 §2.5 的 gap_report 结构 |
| §4.3 三线阈值硬阻断 | **互补** | §4.3 在状态机层限制 max_rc_state，§7.1 在输出层追加二次校验 |
| §5.2 无可信分母降级 | **并列** | §5.2 处理分母不可信的降级，§7 处理证据线不足的降级；互不覆盖 |
| §6 S1 分析管线 | **消费** | §7.3 的证据不足报告是 §6.6 报告输出的一个变体 |

---

## §8 权限边界拒绝与越权保护

> **实现者**：ST-NRA-02（权限边界拒绝 — 外部访问/生产操作）
>
> 本章是本 Skill 的权限边界防护层。在 deny-by-default 原则下，明确定义所有禁止的外部访问、生产操作和越权行为，并提供检测逻辑、拒绝响应和审计日志格式。与 §7（证据不足保护）共同构成本 Skill 的双层负向防护体系。
> 前置依赖：HLD REV-03 可信治理约束（无凭据、无外部写入、无自动确认）、CR-030 授权策略（NO_CREDENTIAL_READ、ITR_READ_GET_ONLY、NO_PRODUCTION_WRITE、NO_EXTERNAL_PUBLISH）、Feature DESIGN §5 安全与治理约束。

### 8.1 deny-by-default 总则

#### 8.1.1 核心原则

本 Skill 对以下四类操作采取 **deny-by-default** 策略——所有未显式授权的操作一律拒绝，不设"默认允许"的兜底规则：

| 操作类别 | 默认策略 | 例外条件 | 授权来源 |
|---------|---------|---------|---------|
| **外部系统连接** | 拒绝 | 仅限 DAO 通过 SQLite 本地文件访问；从不由 Skill 主动发起网络连接 | 无例外 |
| **凭据读取** | 拒绝 | 不存在"可读取凭据"的授权；Skill 不访问环境变量、配置文件、密钥存储 | 无例外 |
| **生产数据写入** | 拒绝 | DAO 受限写入仅限 `analysis_run` 表（草案状态）；不写入 `ticket`、`ingestion_batch`、`ticket_version` 等源数据表 | 无例外 |
| **自动化操作分发** | 拒绝 | CA/PA 只生成候选草案（`status=draft`）；不发起审批、不创建下游任务、不修改工单状态 | 无例外 |

任何未在本 Skill「安全与禁止事项」节「允许事项」表中列出的操作，自动视为拒绝。

#### 8.1.2 三层防护体系

本 Skill 的三道防护层按顺序执行，任一层触发拒绝则后续分析不执行：

| 检查层 | 职责 | 章节 | 检查范围 |
|--------|------|------|---------|
| **入口资格** | 数据就绪与质量判定 | §1 | 输入数据质量、优先级判定、内部问题识别 |
| **证据保护** | 分析可信度保护 | §7 | 证据线阈值、缺失证据分类、降级输出、禁止伪造 |
| **权限边界** | 操作安全保护 | §8 | 外部访问、生产操作、数据边界、越权检测 |

#### 8.1.3 越权分类

本 Skill 定义三类越权场景：

| 越权类型 | 英文标识 | 判定依据 | 严重度 |
|---------|---------|---------|--------|
| **外部访问越权** | `external_access` | 试图连接外部系统（非 ITR endpoint）、读取凭据、执行 HTTP 写入 | 阻断 |
| **生产操作越权** | `production_write` | 试图自动分发 CA/PA、自动创建下游任务、自动关闭工单、修改源数据表 | 阻断 |
| **数据边界越权** | `data_boundary` | 试图读取 `raw_json`、跨产品读取无权数据、输出敏感字段 | 阻断 |

### 8.2 外部访问拒绝类别

#### 8.2.1 禁止外部系统连接

```
禁止行为：
  - 通过 HTTP/HTTPS 连接任何外部系统（包括但不限于 ITR API、内部服务、第三方服务）
  - 通过 TCP/UDP socket 连接外部系统
  - 通过任何网络协议发起出站连接
  - ITR 固定 GET 已由 FEAT-RA-INGESTION 的 itr-ticket-ingestion Skill 处理，不在 reverse-analysis 范围

检测逻辑：
  if 调用中包含 http:// 或 https:// URL:
      → denial_type: external_access
      → reason: "deny-by-default: 禁止外部系统连接"
      → response: "reverse-analysis Skill 不发起网络连接。所有数据通过 SQLite 本地文件访问。
                   如需获取 ITR 数据，请使用 ptm-tse Agent 的 ptm-atomic 工具。"

例外检查（全部不满足时拒绝）：
  - 无例外。本 Skill 永不发起网络连接。
```

**来源**：HLD REV-03 §12「安全性 0 个未授权外部路径」；ST-RA-05.1-INGEST LLD §2.1 allowlist 白名单（URL pattern + 参数白名单 + 拒绝认证头）。

#### 8.2.2 禁止凭据读取

```
禁止行为：
  - 读取环境变量（os.environ、process.env 等）
  - 读取配置文件中的认证信息（token、password、api_key、secret 等字段）
  - 读取密钥存储或凭据管理器的任何条目
  - 从文件系统读取 .env、.credentials、.secrets 等路径
  - 接受包含 credential、token、api_key、password 字段或认证头的输入

检测逻辑：
  if 操作涉及以下任一模式:
      - 访问环境变量（env、environ、getenv 等关键词）
      - 访问包含 "token"、"password"、"api_key"、"secret"、"credential"、"auth" 字段的文件或输入
      - 访问 .env / .credentials / .secrets 路径
      → denial_type: external_access
      → reason: "deny-by-default: 禁止凭据读取"
      → response: "reverse-analysis Skill 遵循无凭据原则。不读取任何认证凭据。
                   所有分析仅基于 SQLite 清洗后数据。如需要凭据保护的操作，请发起独立 runtime/security CR。"

例外检查（全部不满足时拒绝）：
  - 无例外。本 Skill 永不读取凭据。
```

**来源**：HLD REV-03 §12「安全性 0 个未授权凭据路径」；ST-RA-01 LLD §2.2 输入校验（凭据字段检测），ST-RA-01 LLD §8 安全与权限（deny-by-default 入口守卫，测试 ID T-RA01-03）。

#### 8.2.3 禁止 HTTP 写入

```
禁止行为：
  - 通过 HTTP POST/PUT/PATCH/DELETE 向外部系统写入数据
  - 通过 Webhook 推送分析结果
  - 通过 API 回调更新外部系统状态
  - 向任何外部 endpoint 发送分析报告或 ra-report

检测逻辑：
  if 调用中包含 HTTP 方法 POST/PUT/PATCH/DELETE:
      → denial_type: external_access
      → reason: "deny-by-default: 禁止 HTTP 写入"
      → response: "reverse-analysis Skill 不执行任何外部写入操作。
                   分析结果仅写入本地 analysis_run 表和 ra-report 草案。"

例外检查（全部不满足时拒绝）：
  - 无例外。本 Skill 永不执行 HTTP 写入。
```

**来源**：HLD REV-03 §12「NO_PRODUCTION_WRITE」授权策略；Feature DESIGN §5 安全约束「分析结论与源数据分离」。

### 8.3 生产操作拒绝类别

#### 8.3.1 禁止自动分发 CA/PA

```
禁止行为：
  - 将 capa_items[] 中的候选 CA/PA 自动标记为 approved 或 in-progress
  - 自动向改进跟踪系统推送 CA/PA（如连接 TAPD/Jira/measure_link 等外部系统）
  - 自动生成工单或任务单以跟踪 CA/PA 执行
  - 以任何方式绕过 reviewer 人工确认环节
  - 将 capa_items[] 内容直接写入 measure_link 表

检测逻辑：
  if 输出中的 capa_items[].status 被设为 "approved" 或 "in-progress":
      → denial_type: production_write
      → reason: "deny-by-default: 禁止自动分发 CA/PA"
      → response: "CA/PA 只生成候选草案（status=draft）。
                   批准和分发必须由 reviewer 通过 ptm-tse Agent 显式确认后，
                   由 improvement-tracker 产出已批准改进输入，下游 Agent 消费。"

  if capa_items[] 内容被写入 measure_link 表或外部系统:
      → denial_type: production_write
      → reason: "deny-by-default: 禁止自动分发 CA/PA"
      → response: "measure_link 写入由 ST-RA-06.3-TRACK 负责，不在本 Skill 范围。"

例外检查（全部不满足时拒绝）：
  - 无例外。CA/PA 草案与分发操作严格分离。
```

**来源**：ST-RA-03 LLD §5 状态机（CA/PA 只产出 draft，不自动分发），ST-RA-03 LLD §8 安全（文件化只读交接），测试 ID T-IMP-07（禁止自动分发）。

#### 8.3.2 禁止自动创建下游任务

```
禁止行为：
  - 自动创建分析后续任务（如自动重新分析、自动数据补录任务）
  - 自动触发其他 Skill 或 Agent 的执行
  - 自动创建定时任务或 cron job 以定期分析
  - 自动生成通知或告警

检测逻辑：
  if Skill 输出中包含 "创建任务"、"触发执行"、"自动调用"、"定时运行"、"schedule" 等操作意图:
      → denial_type: production_write
      → reason: "deny-by-default: 禁止自动创建下游任务"
      → response: "reverse-analysis Skill 仅产出分析报告草案（ra-report）。
                   不自动创建下游任务。目标任务创建由 ptm-tse Agent 编排层负责。"

例外检查（全部不满足时拒绝）：
  - 无例外。下游任务的创建属于 Agent 编排层职责。
```

**来源**：HLD REV-03 §4.3 Agent 编排职责边界；Feature DESIGN §5「Agent 只编排，Skill 不独立发起工作流」。

#### 8.3.3 禁止自动关闭工单

```
禁止行为：
  - 修改 ticket 表中任何行的 status 字段
  - 变更 ticket 的 quality_flag
  - 通过写回 ITR 系统关闭或更新问题单
  - 自动生成问题单的关闭报告或结单摘要
  - 执行任何 UPDATE/INSERT/DELETE/DROP/ALTER/TRUNCATE 到源数据表

检测逻辑：
  if 试图执行 UPDATE ticket SET status = ...:
      → denial_type: production_write
      → reason: "deny-by-default: 禁止自动关闭工单"
      → response: "ticket 表为只读消费。不修改源数据。
                   工单关闭由 ITR 系统和人工流程控制。"

  if 试图执行 UPDATE ticket SET quality_flag = ...:
      → denial_type: production_write
      → reason: "deny-by-default: 禁止修改 ticket 质量标记"
      → response: "quality_flag 由 ST-RA-05.2-CLEAN 设定。
                   本 Skill 只消费该标记，不修改。"

例外检查（全部不满足时拒绝）：
  - 无例外。ticket、ingestion_batch、ticket_version 表完全只读。
```

**来源**：HLD REV-03 §12「NO_PRODUCTION_WRITE」授权策略；ST-RA-01 LLD §1.2 Step 2「只读消费，不修改源数据」。

### 8.4 越权检测与阻断

#### 8.4.1 二次越权检查

在 §1 资格检查之外，本 Skill 在以下三个时机执行二次越权检查：

| 检查时机 | 检查内容 | 失败动作 |
|---------|---------|---------|
| **分析入口** | 验证数据来源是否为 SQLite 本地文件（非外部系统）、验证未读取 `raw_json` 列、验证未读取凭据或环境变量 | 拒绝执行，输出 `denial_record`（参见 §8.5） |
| **分析输出前** | 验证 ra-report 不含敏感字段（`raw_json` 片段、凭据、环境变量值）、验证 CA/PA 状态为 `draft`、验证未写入 ticket 表 | 拒绝写入，输出阻断清单 |
| **报告生成后** | 扫描 ra-report 中的内容，确认不包含禁止输出的数据类型 | 发现违规则标记 `analysis_run` 为 `failed`，追加 `transition_log` 项注明 "hard-blocked by §8.4" |

#### 8.4.2 越权检测规则表

| 检测项 | 检测方式 | denial_type | 拒绝响应码 |
|--------|---------|-------------|-----------|
| 读取 `raw_json` 列 | 检查 SQL 查询是否包含 `raw_json` | `data_boundary` | `DENIED-RAW-JSON-READ` |
| 写入 ticket/ingestion_batch/ticket_version 表 | 检查是否执行 UPDATE/INSERT/DELETE 到源数据表 | `production_write` | `DENIED-TICKET-WRITE` |
| 读取凭据/环境变量 | 检查调用中是否包含 `os.environ`、`.env` 等模式 | `external_access` | `DENIED-CREDENTIAL-READ` |
| HTTP 网络连接 | 检查调用中是否包含 `http://`、`https://` URL | `external_access` | `DENIED-HTTP-ACCESS` |
| CA/PA 状态变更 | 检查 `capa_items[].status` 是否为非 `draft` 值 | `production_write` | `DENIED-CAPA-DISTRIBUTION` |
| HTTP 写入 | 检查调用中是否包含 POST/PUT/PATCH/DELETE 方法 | `external_access` | `DENIED-HTTP-WRITE` |
| 下游任务创建 | 检查输出中是否包含任务创建/调度/触发意图 | `production_write` | `DENIED-DOWNSTREAM-TASK` |
| 工单状态修改 | 检查是否执行 `UPDATE ticket SET status` 等操作 | `production_write` | `DENIED-TICKET-CLOSURE` |
| 输出敏感字段 | 检查 ra-report 是否包含 `password`/`token`/`secret`/`credential` 字段名 | `data_boundary` | `DENIED-SENSITIVE-OUTPUT` |
| 自动确认根因 | 检查是否绕过 reviewer 直接标记 `reviewer_confirmed` | `production_write` | `DENIED-AUTO-CONFIRM` |

#### 8.4.3 拒绝响应结构

当越权检测触发时，Skill 输出标准化拒绝响应（不执行任何分析）：

```yaml
denial_record:
  id: "deny-{timestamp}-{short_uuid}"
  type: external_access           # external_access | production_write | data_boundary
  denial_code: "DENIED-HTTP-ACCESS"
  requested_action: "HTTP GET https://itr.example.com/api/v1/tickets"
  reason: "deny-by-default: 禁止外部系统连接（HLD REV-03 §12）"
  alternative_path: "使用 ptm-atomic 工具获取 ITR 数据后，通过 SQLite 本地文件进行分析"
  cr_suggestion: "如需新增外部数据源，请发起 runtime/security CR 评估授权范围"
  timestamp: "2026-07-16T10:30:00Z"
  policy_ref: "HLD REV-03 §12 可信治理约束"
  rule_ref: "§8.2.1 禁止外部系统连接"
  ticket_context: null             # 如操作与特定 ticket 有关则填写 source_ticket_id
  analysis_run_id: null            # 如操作在分析运行上下文中则填写 run_id
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 拒绝记录唯一标识，格式 `deny-{timestamp}-{short_uuid}` |
| `type` | enum | 是 | 越权类型：`external_access` / `production_write` / `data_boundary` |
| `denial_code` | string | 是 | 拒绝响应码（参见 §8.4.2 检测规则表） |
| `requested_action` | string | 是 | 被拒绝的操作描述 |
| `reason` | string | 是 | 拒绝原因，格式 `"deny-by-default: <说明>（<策略引用>）"` |
| `alternative_path` | string | 是 | 建议的替代路径 |
| `cr_suggestion` | string | 否 | 建议创建的 CR 类型（如 `runtime/security CR`） |
| `timestamp` | datetime | 是 | 拒绝时间（ISO 8601） |
| `policy_ref` | string | 是 | 引用的策略文档 |
| `rule_ref` | string | 是 | 引用的 Skill 规则章节 |
| `ticket_context` | string \| null | 否 | 相关 ticket 引用（如 `ITR-2026-0001`） |
| `analysis_run_id` | string \| null | 否 | 相关 analysis_run 标识 |

### 8.5 权限边界审计日志

#### 8.5.1 审计事件记录

所有越权拒绝事件必须记录审计日志。拒绝记录（`denial_record`）**即**审计事件——§8.4.3 定义的 `denial_record` 结构同时承担拒绝响应和审计日志双重职责。

#### 8.5.2 审计日志存储

```
存储位置:
  1. 分析上下文中的拒绝:
     拒绝记录的引用写入 analysis_run 的 audit_log 字段（JSON 数组），
     完整 denial_record 存储为独立日志条目。

  2. 非分析上下文中的拒绝（analysis_run 创建之前）:
     Skill 返回 denial_record 给调用方（ptm-tse Agent），
     由 Agent 负责持久化到会话日志。

  3. Skill 自身不直接写入文件系统或日志系统——
     拒绝记录通过返回值传递给调用方。
```

#### 8.5.3 拒绝记录与 §7 证据不足报告的协同

| 场景 | §7 行为 | §8 行为 | 协同输出 |
|------|---------|---------|---------|
| 正常分析请求 | 不触发 | 不触发 | 标准 ra-report |
| 证据不足（`valid_count < 3`） | 输出 insufficient_evidence 报告 | 不触发（数据来源合法） | insufficient_evidence + `prohibited_outputs` 列表 |
| 越权请求（凭据/外部访问/生产写入） | 不触发（未进入分析） | 输出 `denial_record` | denial_record，不执行分析 |
| 越权 + 证据不足同时存在 | 不触发（越权优先拦截） | 先触发拒绝 | denial_record，证据不足检查跳过 |

**优先级**：§8 权限边界检查优先于 §7 证据不足检查。越权请求直接在入口处拒绝，不进入证据分类流程。

#### 8.5.4 禁止行为清单扩展

本节追加 §7.4 禁止行为清单中的权限边界相关项（编号延续 §7 的 P-11）：

| 编号 | 禁止行为 | 触发条件 | 严重度 |
|------|---------|---------|--------|
| P-12 | 禁止发起任何 HTTP/HTTPS 网络连接 | 调用中包含 `http://` 或 `https://` URL | **阻断** |
| P-13 | 禁止读取凭据、token、password、api_key 等认证信息 | 访问环境变量或包含认证字段的输入/文件 | **阻断** |
| P-14 | 禁止自动将 CA/PA 候选草案标记为 `approved` 或 `in-progress` | `capa_items[].status` 设为非 `draft` 值 | **阻断** |
| P-15 | 禁止向 `ticket`/`ingestion_batch`/`ticket_version` 表执行写入操作 | 任何 UPDATE/INSERT/DELETE/DROP/ALTER/TRUNCATE 到源数据表 | **阻断** |
| P-16 | 禁止读取 `ticket.raw_json` 列进入分析正文 | SQL 查询中包含 `raw_json` 列 | **阻断** |
| P-17 | 禁止在 ra-report 中输出包含 `password`/`token`/`secret`/`credential` 字段名的内容 | 报告草案中出现敏感字段名 | **阻断** |
| P-18 | 禁止自动创建下游任务（含重新分析、定时任务、通知、告警） | 输出中包含任务创建/调度/触发意图 | **阻断** |
| P-19 | 禁止修改 ticket 的 `status` 或 `quality_flag` 字段 | 执行 UPDATE 到 ticket 表 | **阻断** |

#### 8.5.5 违规检测与上报

Skill 本身不执行运行时违规检测（检测由 ptm-tse Agent 在调用 Skill 前后执行），但本 §8 的禁止清单（P-12 至 P-19）连同 §7 的 P-01 至 P-11 是**强契约**。任何调用方在发现违反上述禁止项时，必须：

1. 标记当前操作/analysis_run 为拒绝或失败
2. 输出标准化 `denial_record`（§8.4.3）
3. 不调用 `reviewer_publish_analysis_run`（如适用）
4. 在 `transition_log` 中记录违反的 P-xx 编号和现场

### 8.6 拒绝矩阵速查

| 请求类别 | 拒绝条件 | `type` | 拒绝响应码 | 替代路径 |
|---------|---------|--------|-----------|---------|
| 凭据/认证 | 请求包含 credential、token、api_key、password 字段或认证头 | `external_access` | `DENIED-CREDENTIAL-READ` | 使用脱敏摘要；独立发起 runtime/security CR |
| 非 ITR 外部系统访问 | 尝试 HTTP GET/POST/PUT 到非 allowlist URL | `external_access` | `DENIED-HTTP-ACCESS` | ITR 固定 GET 由 itr-ticket-ingestion 处理，不在 reverse-analysis 范围 |
| HTTP 写入 | 尝试 POST/PUT/PATCH/DELETE 到外部系统 | `external_access` | `DENIED-HTTP-WRITE` | ra-report 仅写入本地 analysis_run 表 |
| 自动分发 CA/PA | `capa_items[].status` 设为非 `draft` 值或写入外部跟踪系统 | `production_write` | `DENIED-CAPA-DISTRIBUTION` | improvement-tracker 产出已批准改进输入，下游 Agent 消费 |
| 创建下游任务 | 输出中包含任务创建/调度/定时/告警意图 | `production_write` | `DENIED-DOWNSTREAM-TASK` | 下游任务由 ptm-tse Agent 编排层负责 |
| 关闭工单 | 修改 ticket 表 `status` 或 `quality_flag` | `production_write` | `DENIED-TICKET-CLOSURE` | 工单关闭由 ITR 系统和人工流程控制 |
| 自动确认根因 | 绕过 reviewer 标记 `reviewer_confirmed` | `production_write` | `DENIED-AUTO-CONFIRM` | 必须人工 reviewer 操作（见 §7.4 P-01 + ST-RA-02 LLD §5 根因四层状态机） |
| 读取 raw_json | SQL 查询包含 `raw_json` 列 | `data_boundary` | `DENIED-RAW-JSON-READ` | 仅使用清洗后字段（见 §1.2 Step 1 + §7.4 P-06） |
| 输出敏感字段 | ra-report 含 `password`/`token`/`secret` 字段名 | `data_boundary` | `DENIED-SENSITIVE-OUTPUT` | 脱敏后输出 |

### 8.7 适用范围

| 维度 | 适用范围 |
|------|---------|
| **覆盖分析模式** | S1 逐单分析（§6.2）、S1 批量分析（§6.3） |
| **覆盖操作阶段** | 分析入口前（资格检查并行）、分析执行中（六维引擎）、分析输出后（报告生成） |
| **覆盖拒绝类型** | `external_access`、`production_write`、`data_boundary` |
| **不覆盖** | Agent 编排层的任务创建与调度（由 ptm-tse Agent 自身的安全边界控制） |
| **不覆盖** | ITR 数据摄取阶段的 allowlist 白名单（由 ST-RA-05.1-INGEST 的 itr-ticket-ingestion Skill 负责） |
| **不覆盖** | CA/PA 批准后的分发与跟踪（由 ST-RA-03 improvement-tracker 和 ST-RA-06.3-TRACK 负责） |

### 8.8 与其他章节的关系

| 章节 | 关系 | 说明 |
|------|------|------|
| §1 资格检查 | **并列 + 互补** | §1 检查数据就绪与质量，§8 检查操作权限；两者在分析入口并行执行 |
| §2 可信输入建立 | **消费** | §2 的只读数据获取原则与 §8 的 deny-by-default 一致，§8 追加禁止读取 `raw_json` 的硬阻断 |
| §3-§5 六维分析引擎 | **消费** | 分析引擎的输出受 §8 约束——CA/PA 不得自动分发、分析结论不得自动确认 |
| §6 S1 分析管线 | **消费** | 分析管线的入口、执行中、输出后三个时机均受 §8 二次越权检查 |
| §7 证据不足保护 | **并列 + 互补** | §7 保护分析可信度，§8 保护操作安全；两者构成本 Skill 的双层负向防护。§8 检查优先于 §7 执行 |
| 安全与禁止事项 | **具体化** | 安全与禁止事项定义整体安全边界，§8 追加每类禁止操作的检测逻辑、拒绝响应结构和审计日志格式 |

### 8.9 正向 LLD 覆盖追溯

本 §8 的每类拒绝规则均有正向 Story LLD 的精确覆盖，确保「拒绝行为」与「授权行为」契约一致：

| 拒绝类别 | 正向 LLD 覆盖位置 | 覆盖章节 | 关联测试 ID | 接口定义 |
|---------|------------------|---------|------------|---------|
| 凭据/认证拒绝 | `ST-RA-01-LLD.md` | §2.2 输入校验（凭据字段检测），§8 安全与权限（deny-by-default 入口守卫） | T-RA01-03（非法输入拒绝） | `validate_input()` 拒绝包含 credential/token/api_key/password 的输入 |
| 非 ITR 外部系统访问 | `ST-RA-05.1-INGEST-LLD.md` | §2.1 allowlist 白名单（URL pattern + 参数白名单 + 拒绝认证头），§8 安全（禁止凭据推断） | T-ING-01（allowlist 拒绝非 ITR URL） | `validate_request(url, params)` → ValueError for non-allowlist |
| 生产写入/操作 | `ST-RA-03-LLD.md` | §5 状态机（CA/PA 只产出 draft，不自动分发），§8 安全（文件化只读交接） | T-IMP-07（禁止自动分发） | Approved Improvement Input 不可变 + 下游只读 |
| 自动确认 | `ST-RA-02-LLD.md` | §5 根因四层状态机（raw_statement → AI candidate → evidence-backed → reviewer-confirmed），§8（三线阈值硬阻断） | T-RA02-05（无证据不确认） | `confirm_root_cause()` 仅 reviewer 角色可调用 |

---

## §9 S2 增量重算与差异报告

### 9.1 增量重算触发

#### 9.1.1 S2 入口判定

S2 增量重算在以下条件**全部**满足时触发：

```
判断逻辑：
  if 输入中包含 new_batch_id AND baseline_batch_id AND change_set:
      → 进入 S2 增量重算管线（§9）
  elif 输入为 batch_id 或 source_ticket_id（无 baseline_batch_id）:
      → 进入 S1 分析管线（§6）
  else:
      → blocked（"无法识别分析模式，请提供有效的输入组合"）
```

S2 由 ptm-tse Agent 在以下时机编排调用：

| 触发场景 | 输入来源 | 说明 |
|---------|---------|------|
| 新摄取批次完成 | ST-RA-06.1-DETECT 变更检测输出 | 新 batch 数据已清洗，change_set 已生成 |
| 周期复盘 | 时间窗口 + 历史运行记录 | 月度/季度环比同比分析 |
| 措施刷新 | 已批准 CA/PA + 新分析结果 | 判断措施是否需更新或完成 |

#### 9.1.2 change_set 消费

change_set 由 ST-RA-06.1-DETECT 产出，存储在 `change_history` 表中。S2 通过以下接口消费：

```
从 SQLite 读取变更集:
  调用 get_changes_by_batch(conn, new_batch_ref)
    → 返回 change_history 列表，每条记录包含:
      - ticket_id: ticket 主键
      - batch_ref: 批次引用
      - change_type: new | modified | unchanged | conflict
      - affected_fields: JSON 数组字符串（变更字段名列表）
      - resolution: auto_merged | manual_queue | rejected
```

**change_set 消费规则**：

| change_type | 处理方式 |
|-------------|---------|
| `new` | 新增 ticket → 该 ticket 全维度分析（等同 S1 逐单） |
| `modified` | 已变更 ticket → 根据 affected_fields 映射受影响维度 |
| `unchanged` | 未变化 ticket → 跳过分析，从 baseline ra-report 复制引用 |
| `conflict` | 冲突 ticket → 标记为 skipped_tickets，不进入分析 |

**resolution 过滤**：仅 `resolution='auto_merged'` 的变更自动进入重算管线；`resolution='manual_queue'` 和 `resolution='rejected'` 的变更在报告中列出但不自动重算。

#### 9.1.3 前置校验

进入 S2 管线前必须完成以下校验：

| 校验项 | 规则 | 失败行为 |
|--------|------|---------|
| baseline batch 存在 | 调用 `get_batch(conn, baseline_batch_ref)` 确认 | blocked（"基线批次 {baseline_batch_ref} 不存在"） |
| baseline analysis_run 存在 | 调用 `get_runs_by_batch(conn, baseline_batch_ref)` 至少 1 条 completed 或 published 记录 | blocked（"基线批次无已完成的分析运行"） |
| 新 batch 存在 | 调用 `get_batch(conn, new_batch_ref)` 确认 | blocked（"新批次 {new_batch_ref} 不存在"） |
| change_set 非空 | `get_changes_by_batch` 返回非空列表 | 跳过所有维度重算，输出空差异报告（见 §9.6.2） |
| 批次锁定 | 同一 `new_batch_ref` 已有 `in_progress` 状态的 S2 analysis_run | blocked（"批次已有进行中的 S2 分析运行"） |

---

### 9.2 受影响维度判定

#### 9.2.1 变更字段 → 分析维度映射表

仅当 `recompute_mode='incremental'` 时执行维度映射。遍历 change_set 中每条 `change_type='modified'` 的记录的 `affected_fields`，按以下映射表判定受影响的分析维度：

| 变更字段（ticket 表） | 影响的分析维度 | 重算范围 | 说明 |
|----------------------|-------------|---------|------|
| `root_cause` | **根因（RC）** | 单 ticket 根因重算 + 聚合根因统计 | 根因描述变化 → 所有 AI 候选需要重新生成 |
| `product` | **产品质量（PQ）** | 新/旧 product 聚合 + Pareto | 产品归属变化 → 两个产品的模块分布均受影响 |
| `module` | **产品质量（PQ）** | 新/旧 module 聚合 + Pareto | 模块归属变化 → 两个模块的风险排序均受影响 |
| `severity` | **产品质量（PQ）、根因（RC）** | 严重度分布 + 根因优先级 | 严重度变化 → 统计分布变更 + 根因关注度调整 |
| `status` | **产品质量（PQ）、流出（ESC）** | 状态分布 + 逃逸分析 | 状态变化 → 影响各状态比例 + 逃逸时间线 |
| `title` | **根因（RC）** | 单 ticket 根因上下文 | 标题变化 → 可能影响 AI 对根因的理解 |
| `description` | **根因（RC）、流出（ESC）** | 单 ticket 根因 + 逃逸上下文 | 描述变化 → 影响现象/环境证据线 |
| `test_missed_analysis` | **漏测（TM）** | PPDCS 归类重算 | 漏测分析变化 → 归类可能改变 |
| `test_missed_phase` | **漏测（TM）** | 漏测阶段重算 | 漏测阶段变化 → 影响缺失阶段统计 |
| `improvement_measures` | **改进（IMP）** | CA/PA 候选刷新 | 改进措施变化 → 新候选生成 + 旧候选失效判定 |
| `openeddate` | **环比同比（CMP）** | 窗口内聚合重算 | 时间变化 → 影响窗口归属 |
| `resolveddate` | **环比同比（CMP）** | 解决时间统计 | 解决时间变化 → 影响已解决 ticket 统计 |
| `priority` | **产品质量（PQ）** | 优先级分布 | 优先级变化 → 分布统计变更 |

#### 9.2.2 受影响维度计算流程

```
Step DM-1: 初始化受影响维度集合
  affected_dimensions = set()

Step DM-2: 遍历 change_set
  for each change in change_set:
      if change.change_type == 'new':
          → 新增 ticket 影响全部维度
          → affected_dimensions 加入所有维度（RC, PQ, ESC, TM, IMP, CMP）

      elif change.change_type == 'modified':
          → affected_fields ← 解析 change.affected_fields（JSON 数组）
          → 遍历 affected_fields 中的每个字段名
          → 按 §9.2.1 映射表查找对应维度
          → 将对应维度加入 affected_dimensions

      elif change.change_type == 'unchanged':
          → 跳过（不加入受影响维度）

      elif change.change_type == 'conflict':
          → 在 skipped_tickets 中记录
          → 不加入受影响维度

Step DM-3: 合并去重
  affected_dimensions = 去重后的维度列表
  按维度代号排序: RC, PQ, ESC, TM, IMP, CMP

Step DM-4: 空集判定
  if affected_dimensions 为空（所有变更都是 unchanged 或全部被 resolution 过滤）:
      → 跳过重算
      → 输出空差异报告（§9.6.2）
```

#### 9.2.3 受影响 ticket 集合

除维度映射外，还需维护受影响的 ticket 列表：

```
affected_tickets:
  - 所有 change_type='new' 的 ticket
  - 所有 change_type='modified' 且 resolution='auto_merged' 的 ticket

unaffected_tickets:
  - 所有 change_type='unchanged' 的 ticket

skipped_tickets:
  - 所有 change_type='conflict' 的 ticket
  - 所有 resolution='manual_queue' 或 'rejected' 的 ticket
```

---

### 9.3 增量重算策略

#### 9.3.1 增量重算总原则

增量模式下，**仅对受影响维度和受影响 ticket 执行重算**，未受影响的数据从 baseline ra-report 中复制引用。

```
增量重算三大原则:
  原则 1 — 最小重算：只重算受变更影响的维度，不确定则保守重算
  原则 2 — 引用复用：未受影响的维度从 baseline 引用，不重复计算
  原则 3 — 聚合隔离：单 ticket 变更只影响该 ticket 所在聚合组的统计；
              不影响其他组的独立统计
```

#### 9.3.2 逐维度增量策略

| 维度 | 受影响时重算内容 | 未受影响时的处理 |
|------|----------------|----------------|
| **RC（根因）** | 仅重算受影响 ticket 的根因分析（重新执行 §3.2.1 完整流程：raw_statement → AI 候选生成 → 置信度判定）；批量模式下追加高频根因模式聚合 | 从 baseline ra-report 的 `sections.root_cause` 复制 |
| **PQ（产品质量）** | 重算受影响 product/module/severity/status 分组的所有聚合统计（数量/占比/Pareto/趋势）；**注意**：单 ticket 的 module 变更会影响新旧两个 module 的统计 | 未受影响的 product/module 分组统计从 baseline 复制 |
| **ESC（流出）** | 仅重算受影响 ticket 的流出分析（控制层逃逸判定 + nearest_intercept） | 未受影响的 ticket 流出分析从 baseline 复制 |
| **TM（漏测）** | 仅重算受影响 ticket 的 PPDCS 归类；批量模式下追加 PPDCS 分布聚合 | 未受影响的 ticket 漏测分析从 baseline 复制 |
| **IMP（改进）** | 重算受影响 ticket 的 CA/PA 候选；批量模式下追加 CA/PA 去重与优先级排序 | 未受影响的 ticket 改进候选从 baseline 复制；注意跨 ticket 去重需合并新旧候选 |
| **CMP（环比同比）** | **始终重算**——窗口数据变化即使字段级不受影响也可能影响聚合结果；同时对新 batch 的完整窗口和 baseline 窗口重新执行 §3.2.6 计算 | 无（环比同比始终重算） |

**环比同比特殊处理**：环比同比维度比较的是两个完整时间窗口的聚合数据，即使所有 ticket 的字段都没有变化（全部 unchanged），只要窗口时间推进，环比同比结果就会变化。因此 CMP 在 S2 中**始终重算**，不受 affected_dimensions 判定结果的约束。

#### 9.3.3 增量重算的执行流程

```
Step IR-1: 获取基线数据
  从 baseline analysis_run 关联的 ra-report 中读取:
    - baseline sections（六维分析结果）
    - baseline ticket_refs（关联的 ticket 列表）
    - baseline 环比同比 comparison 数据

Step IR-2: 初始化新 sections
  创建与 baseline 相同结构的新 sections 骨架:
    - 所有维度的 baseline 值先完整复制
    - affected_tickets 中对应的 per-ticket 数据清空（将覆盖新值）

Step IR-3: 逐维度重算
  for each dimension in affected_dimensions:
      3a. 收集该维度的"新数据":
          - new_tickets: change_type='new' 的 ticket
          - modified_tickets: change_type='modified' 且该维度受影响的 ticket
      3b. 调用对应维度的分析方法（§3.2.1–§3.2.5），仅对新数据和修改数据执行
      3c. 将分析结果合并到新 sections 中（覆盖 old values）
      3d. 对于聚合维度（PQ/IMP/TM），重算受影响分组后与未受影响的 baseline 分组合并

Step IR-4: 环比同比重算
  始终重算（不受 affected_dimensions 判定约束）:
    - 调用 §3.2.6 环比同比计算
    - 当前窗口: new batch 数据
    - 基期窗口: comparison_batch_ref 数据

Step IR-5: 输出新 sections
  输出完整的新 sections:
    - 受影响维度 → 包含新计算结果
    - 未受影响维度 → 引用 baseline（标记 `source: baseline_run_{run_id}`）
    - 环比同比 → 新计算结果
```

#### 9.3.4 聚合维度增量合并规则

对于需要跨 ticket 聚合的维度（PQ/TM/IMP），增量合并规则如下：

**产品质量（PQ）合并规则**：

```
合并前:
  baseline PQ: { product_A: {count: 10, modules: [X: 5, Y: 5]} }

变更: ticket ITR-001 的 module 从 X 变为 Z
  → 新 module: Z, 旧 module: X

合并后:
  1. 从 baseline 减去旧值: product_A.modules.X -= 1
  2. 加入新值: product_A.modules.Z += 1
  3. 重算 product_A 的 Pareto 排序
  4. 重算所有 module 的百分比
```

**漏测（TM）合并规则**：

```
合并前:
  baseline PPDCS: { Prevention: 3, Detection: 5, Containment: 2 }

变更: ticket ITR-002 的 test_missed_analysis 从 Detection 变为 Protection

合并后:
  1. Detection -= 1
  2. Protection += 1
  3. 重算各分类占比
```

**改进（IMP）合并规则**：

```
合并前:
  baseline CA/PA: [item_1, item_2, item_3]（已去重 + 排序）

变更: ticket ITR-003 的 improvement_measures 变更 → 产生新候选 item_4, 旧候选 item_2 不再适用

合并后:
  1. 移除与 baseline 冲突的旧候选（item_2 标记失效）
  2. 加入新候选 item_4
  3. 全集（item_1, item_3, item_4）重新去重和优先级排序
```

---

### 9.4 comparison_batch_ref 管理

#### 9.4.1 comparison_batch_ref 概述

`comparison_batch_ref` 是 analysis_run 记录中用于环比同比的对比批次引用。在 S2 增量重算中，该字段指向基线（上一次 S1 分析或上一次成功的 S2 分析）的 batch。

| 场景 | comparison_batch_ref 值 | 说明 |
|------|------------------------|------|
| S1 逐单分析 | `null` | 逐单模式不支持环比同比 |
| S1 批量分析（首次） | `null` 或 `null` | 首次分析无历史对比 |
| S1 批量分析（有对比） | 指定的历史 batch_id | 用户显式指定对比窗口 |
| S2 增量重算 | `baseline_batch_ref`（输入参数） | S2 默认对比 baseline 批次 |
| S2 全量重算 | `baseline_batch_ref`（输入参数） | 全量重算也保留对比引用 |

#### 9.4.2 对比批次合法性校验

```
Step CB-1: 存在性校验
  调用 get_batch(conn, comparison_batch_ref)
  if 返回 None:
      → comparison.mode = "none"
      → na_reasons 追加 "comparison_batch_not_found"
      → 不阻断 S2 分析（环比同比缺失不影响其他维度）

Step CB-2: 同口径校验
  比较当前 batch 和 comparison_batch 的 schema_version:
  if schema_version 不同:
      → comparison.mode = "none"
      → na_reasons 追加 "schema_version_mismatch"
      → 详细说明: "当前 schema_version={current}, 对比 schema_version={comparison}"

Step CB-3: 窗口完整性校验
  比较当前 batch 和 comparison_batch 的数据窗口:
  if 窗口不完整或不可比较:
      → 见 §9.5.6 环比同比 N/A 判定
```

#### 9.4.3 analysis_run 中的 comparison_batch_ref

创建 S2 analysis_run 时，`comparison_batch_ref` 字段写入：

```python
# 插入 S2 analysis_run
insert_analysis_run(conn, {
    "run_id": s2_run_id,
    "batch_ref": new_batch_ref,
    "comparison_batch_ref": baseline_batch_ref,  # S2 必填
    "schema_version": schema_version,
    "mapping_version": mapping_version,
    "rule_version": rule_version,
    "time_window_start": window_start,
    "time_window_end": window_end,
    "recompute_mode": recompute_mode,              # 'incremental' 或 'full'
    "full_recompute_reason": full_recompute_reason, # full 模式时必填
    "report_refs": report_refs_json,
    "metric_versions": metric_versions,
})
```

**与 S1 的差异**：S1 的 `comparison_batch_ref` 通常为 `null`（除非 S1 批量分析显式指定对比批次）；S2 的 `comparison_batch_ref` 始终指向 baseline batch，作为差异报告的对比基线。

---

### 9.5 recompute_mode 判定

#### 9.5.1 判定流程

```
S2 入口 ──► 规则版本变更检测
                 │
                 ├─► 任一规则版本变更 → recompute_mode = 'full'
                 │       ├─► mapping_rule_version 变更 → full
                 │       ├─► analysis_rule_version 变更 → full
                 │       └─► schema_version 变更 → full
                 │
                 ├─► 规则版本未变 + 有受影响维度 → recompute_mode = 'incremental'
                 │
                 └─► 规则版本未变 + 无受影响维度 → 跳过重算
                         └─► 输出空差异报告（§9.6.2）
```

#### 9.5.2 规则版本变更检测

规则版本变更是指以下任一版本号发生改变——此时所有已计算的指标口径都可能变化，必须全量重算以确保一致性：

| 检查项 | 来源 | 变更含义 | 重算原因 |
|--------|------|---------|---------|
| `mapping_rule_version` | `ingestion_batch.mapping_version`（新 batch vs baseline batch） | 字段映射规则变更 | 清洗后字段的语义可能变化，所有维度的输入都可能受影响 |
| `analysis_rule_version` | `metric-definition.yaml` 的 `metric_version`（当前 vs baseline analysis_run 的 `rule_version`） | 分析口径变更（指标定义、聚合规则、阈值等） | 指标定义变化，所有已计算的指标需要按新口径重新计算 |
| `schema_version` | `ingestion_batch.schema_version`（新 batch vs baseline batch） | SQLite schema 变更 | 列定义变化，数据模型不可比，必须全量重算 |

**检测步骤**：

```
Step RV-1: 获取版本信息
  新 batch:
    schema_version = get_batch(conn, new_batch_ref)["schema_version"]
    mapping_version = get_batch(conn, new_batch_ref)["mapping_version"]

  基线:
    获取 baseline analysis_run（最近一次 completed 或 published 的 run）:
      baseline_run = get_analysis_run(conn, baseline_run_id)
      baseline_schema_version = baseline_run["schema_version"]
      baseline_mapping_version = baseline_run["mapping_version"]
      baseline_analysis_rule_version = baseline_run["rule_version"]

  当前分析规则版本:
    从 metric-definition.yaml 读取当前所有指标的 metric_version
    取最大值作为 current_analysis_rule_version

Step RV-2: 比较版本
  version_changes = []
  if schema_version != baseline_schema_version:
      version_changes.append(f"schema_version: {baseline_schema_version} → {schema_version}")
  if mapping_version != baseline_mapping_version:
      version_changes.append(f"mapping_rule_version: {baseline_mapping_version} → {mapping_version}")
  if current_analysis_rule_version != baseline_analysis_rule_version:
      version_changes.append(f"analysis_rule_version: {baseline_analysis_rule_version} → {current_analysis_rule_version}")

Step RV-3: 判定
  if version_changes 非空:
      → recompute_mode = 'full'
      → full_recompute_reason = "; ".join(version_changes)
  else:
      → 进入受影响维度判定（§9.2）
```

**注意**：上述版本检测属于 OPEN-RA062-01 的范围。当前默认策略：任一版本不同即触发全量重算（保守策略）。

#### 9.5.3 full 模式 vs incremental 模式

| 特性 | `full`（全量重算） | `incremental`（增量重算） |
|------|------------------|------------------------|
| **触发条件** | 规则版本变更 | 规则版本未变 + 有受影响维度 |
| **重算范围** | 所有维度 + 所有 ticket | 仅 affected_dimensions + affected_tickets |
| **baseline 引用** | 不引用 baseline（全量重算） | 未受影响维度引用 baseline |
| **环比同比** | 执行完整计算 | 执行完整计算（始终重算） |
| **差异报告** | 新结果 vs baseline 全量对比 | 新结果 vs baseline 增量对比 |
| **耗时** | 与 S1 批量分析相当 | 远小于 S1 批量分析 |
| **analysis_run.recompute_mode** | `'full'` | `'incremental'` |
| **analysis_run.full_recompute_reason** | 必填（版本变更原因） | `null` |

#### 9.5.4 无受影响维度时的处理

当 `recompute_mode='incremental'` 且 `affected_dimensions` 为空时：

```
Step NDA-1: 判定
  if affected_dimensions 为空 AND 环比同比无变化:
      → 跳过所有维度重算

Step NDA-2: 输出空差异报告
  创建 difference ra-report，所有 dimension_diffs[] 为空，
  change_summary.recompute_mode = 'incremental'，
  change_summary.full_recompute_reason = null

Step NDA-3: 环比同比仍执行
  即使无维度变更，环比同比仍需计算（窗口变化后聚合可能不同）

Step NDA-4: 创建 analysis_run
  仍创建 analysis_run 记录（保留审计追溯），
  report_refs 指向空差异报告 + comparison 结果
```

#### 9.5.5 差异报告的 before/after 来源

| 字段 | full 模式来源 | incremental 模式来源 |
|------|-------------|-------------------|
| `before` 值 | baseline ra-report（完整 sections） | baseline ra-report（完整 sections） |
| `after` 值 | 全量重算结果 | 增量重算结果（受影响维度新值 + 未受影响维度 baseline 引用） |

#### 9.5.6 环比同比 N/A 判定

环比同比计算在以下任一条件满足时标记为 N/A（`comparison.mode = "none"`）：

| N/A 条件 | 检测方式 | na_reason |
|----------|---------|-----------|
| 无 comparison_batch_ref | `comparison_batch_ref` 为 null 或 comparison batch 不存在 | `"no_comparison_batch"` |
| schema_version 不一致 | 新 batch 与 comparison batch 的 `schema_version` 不同 | `"schema_version_mismatch"` |
| 窗口不完整 | 当前窗口或基期窗口不是完整自然月/自然季度 | `"incomplete_window"` |
| 样本量不足 | 基期或当期样本量 < 最小阈值（默认 10，OPEN-RA062-02） | `"insufficient_sample_size"` |
| 口径变更 | 分析规则版本（metric_version）变更 | `"metric_version_changed"` |
| 分母定义不一致 | `denominator.trusted` 状态在 baseline 和当前冲突（一个为 true，另一个为 false） | `"denominator_definition_mismatch"` |
| 零基线 | 基期值为 0（无法计算变化率） | `"zero_baseline"`（change_rate = N/A，但其他指标仍计算） |

**样本量阈值**：最小同口径样本阈值默认 10（OPEN-RA062-02），即 `max(基期样本量, 当期样本量) < 10` 时标记 N/A。此阈值可在 metric-definition.yaml 中以 `min_sample_size` 字段覆盖。

---

### 9.6 差异报告生成

#### 9.6.1 差异计算流程

```
Step DR-1: 确定比较对象
  before_sections = baseline ra-report 的 sections
  after_sections = 新计算的 sections（增量重算结果）

Step DR-2: 逐维度比较
  for each dimension in [RC, PQ, ESC, TM, IMP]:
      2a. 提取 before 和 after 中该维度的关键指标
      2b. 计算变化:
          - absolute_change: after_value - before_value
          - change_rate: (after_value - before_value) / before_value * 100%（当 before_value > 0 时）
          - direction: increased | decreased | unchanged
      2c. 判断显著变化:
          显著变化条件（任一满足）:
            - |change_rate| >= 20%（默认阈值，OPEN-RA062-05）
            - 新增/删除 ticket 数量 > 0
            - PPDCS 归类变化（分类变更）
            - CA/PA 候选新增或失效
      2d. 显著变化 → 标记 significance flag = true + significance_reason

Step DR-3: 环比同比独立计算
  环比同比比较两个完整窗口，计算逻辑见 §3.2.6。
  S2 中环比同比始终重算，不受 affected_dimensions 约束。

Step DR-4: 生成 dimension_diffs[]
  逐维度输出 before_summary、after_summary、significant_changes
```

#### 9.6.2 空差异报告

当 `affected_dimensions` 为空且环比同比无变化时，输出空差异报告：

```yaml
# 空差异报告（所有维度无变化）
report_id: "{analysis_run_id}-diff"
report_type: difference
analysis_run_id: "{analysis_run_id}"
created_at: "2026-07-16T10:30:00Z"

change_summary:
  new_tickets: 0
  modified_tickets: 0
  unchanged_tickets: {N}
  affected_dimensions: []
  recompute_mode: incremental
  full_recompute_reason: null
  note: "本批次无有效变更，所有维度与基线一致"

dimension_diffs: []
  # 空数组——所有维度无变化

comparison:
  mode: full                          # 环比同比仍计算
  metrics: [...]
  na_reasons: []

skipped_tickets:
  - ticket_ref: "ITR-2026-0099"
    reason: "conflict resolution，未自动合并"
```

#### 9.6.3 显著变化阈值

差异报告中 `significant_changes` 的判定阈值：

| 变化类型 | 判定条件 | 默认阈值 |
|---------|---------|---------|
| 数量变化 | `\|change_rate\| >= 20%` | 20%（OPEN-RA062-05） |
| 新增 ticket | `new_tickets > 0` | 任何新增 |
| 维度分布变化 | PPDCS 分类变更 或 Pareto 排序变化 | 任何分类变更 |
| CA/PA 候选变化 | 新候选生成 或 旧候选失效 | 任何候选变化 |
| 根因 current_level 变化 | 状态机跃迁（如 ai_candidate → evidence_backed） | 任何跃迁 |
| 环比同比可信度变化 | credibility 级别变更（high↔medium↔low） | 任何级别变更 |

**绝对数量兜底**：当变化率精确但分母极小（如从 1 变为 2 → change_rate = +100%）时，同时要求 `|absolute_change| >= 2` 才标记显著变化，避免小样本误导。

#### 9.6.4 措施刷新提示

差异报告生成后，对基线中已批准的 CA/PA 措施输出刷新建议：

```
Step MR-1: 获取已批准措施
  从 improvement-tracker（ST-RA-03）获取当前已批准的 CA/PA 候选列表
  （仅 status='approved' 或 reviewer_confirmed）

Step MR-2: 关联分析
  对每条已批准措施，根据维度变更判断受影响程度:
    - 措施关联的根因是否因 root_cause 变更而失效？
    - 措施关联的漏测归类是否因 test_missed_analysis 变更而调整？
    - 措施关联的改进目标是否因 improvement_measures 变更而过时？

Step MR-3: 输出建议
  每条措施的刷新建议:
    - keep: 措施仍有效，无需变更
    - complete: 措施目标已达成（如问题不再出现），建议标记为完成
    - needs_review: 措施可能已受影响，建议 reviewer 人工复核
    - invalidated: 措施的 basis 已变更（如根因重新归类），建议废弃
```

**禁止自动操作**：措施刷新提示为**只读建议**，不自动修改 `measure_link` 表的任何字段。措施的正式状态变更由 ST-RA-06.3-TRACK 消费提示后执行。

---

### 9.7 差异报告输出格式

#### 9.7.1 完整差异报告结构

```yaml
report_id: "{analysis_run_id}-diff"
report_type: difference
analysis_run_id: "{analysis_run_id}"
batch_ref: "new_batch_20260716_002"
comparison_batch_ref: "baseline_batch_20260709_001"
created_at: "2026-07-16T10:30:00Z"

change_summary:
  new_tickets: 3                     # 新增 ticket 数量
  modified_tickets: 7                # 已修改 ticket 数量
  unchanged_tickets: 40              # 未变化 ticket 数量
  skipped_tickets: 2                 # 被跳过的 ticket 数量
  affected_dimensions:               # 受影响的维度名称列表
    - root_cause
    - product_quality
    - test_missed
  recompute_mode: incremental        # incremental | full
  full_recompute_reason: null        # full 模式时必填
  significant_change_count: 4        # 标记为显著的变更数量

dimension_diffs:
  - dimension: root_cause
    affected_ticket_count: 3
    before_summary:
      total_analyzed: 50
      rc_state_distribution:
        raw_statement: 0
        ai_candidate: 35
        evidence_backed: 12
        reviewer_confirmed: 3
    after_summary:
      total_analyzed: 50
      rc_state_distribution:
        raw_statement: 0
        ai_candidate: 33
        evidence_backed: 14
        reviewer_confirmed: 3
    significant_changes:
      - metric: "evidence_backed_count"
        before_value: 12
        after_value: 14
        absolute_change: +2
        change_rate: "+16.7%"
        significance: false
        significance_reason: "change_rate < 20%"
      - metric: "ai_candidate_count"
        before_value: 35
        after_value: 33
        absolute_change: -2
        change_rate: "-5.7%"
        significance: false
        significance_reason: "change_rate < 20%"

  - dimension: product_quality
    affected_ticket_count: 2
    before_summary:
      top_risk_modules:
        - module: ModuleX
          count: 15
          percentage: "30%"
        - module: ModuleY
          count: 10
          percentage: "20%"
    after_summary:
      top_risk_modules:
        - module: ModuleX
          count: 14
          percentage: "28%"
        - module: ModuleZ
          count: 12
          percentage: "24%"
        - module: ModuleY
          count: 10
          percentage: "20%"
    significant_changes:
      - metric: "top_risk_modules.pareto_order"
        before_value: "[ModuleX, ModuleY]"
        after_value: "[ModuleX, ModuleZ, ModuleY]"
        absolute_change: null
        change_rate: null
        significance: true
        significance_reason: "Pareto 排序变化：ModuleZ 从无进入 top 3"

  - dimension: test_missed
    affected_ticket_count: 2
    before_summary:
      ppdcs_distribution:
        Prevention: 10
        Protection: 5
        Detection: 20
        Containment: 8
        Sustainment: 7
    after_summary:
      ppdcs_distribution:
        Prevention: 10
        Protection: 6
        Detection: 19
        Containment: 8
        Sustainment: 7
    significant_changes:
      - metric: "ppdcs_distribution.Protection"
        before_value: 5
        after_value: 6
        absolute_change: +1
        change_rate: "+20.0%"
        significance: true
        significance_reason: "change_rate >= 20%"
      - metric: "ppdcs_distribution.Detection"
        before_value: 20
        after_value: 19
        absolute_change: -1
        change_rate: "-5.0%"
        significance: false
        significance_reason: "change_rate < 20%"

  # ESC, IMP 维度同理（按需展开）
  - dimension: escape_analysis
    affected_ticket_count: 0
    before_summary: {}
    after_summary: {}
    significant_changes: []
    note: "未受影响，引用 baseline"

  - dimension: improvement
    affected_ticket_count: 0
    before_summary: {}
    after_summary: {}
    significant_changes: []
    note: "未受影响，引用 baseline"

comparison:
  mode: mom                          # yoy | mom | none
  window_type: month                 # month | quarter | custom
  baseline_period:
    start: "2026-06-01"
    end: "2026-06-30"
    total_count: 48
  current_period:
    start: "2026-07-01"
    end: "2026-07-31"
    total_count: 50
  metrics:
    - metric_id: "m-total-tickets"
      name: "问题单总数"
      baseline_value: 48
      current_value: 50
      absolute_change: +2
      change_rate: "+4.2%"
      direction: increased
      credibility: high
    - metric_id: "m-p1p2-count"
      name: "P1/P2 问题数"
      baseline_value: 12
      current_value: 10
      absolute_change: -2
      change_rate: "-16.7%"
      direction: decreased
      credibility: high
  na_reasons: []

improvement_refresh:
  affected_measures:
    - measure_ref: "CAPA-2026-0001"
      current_status: approved
      suggestion: keep
      reason: "关联根因和漏测分类未变化"
    - measure_ref: "CAPA-2026-0003"
      current_status: approved
      suggestion: needs_review
      reason: "关联 ticket ITR-2026-0005 的 root_cause 变更，需确认措施 basis 是否仍然有效"
    - measure_ref: "CAPA-2026-0007"
      current_status: approved
      suggestion: complete
      reason: "相关 ticket 已全部 resolved，措施目标已达成"
  new_candidates:
    - capa_item:
        type: corrective
        target: "ModuleZ 的接口校验缺失"
        basis: "新增 ticket ITR-2026-0051 的根因分析"
        priority: P1
        status: draft
    - capa_item:
        type: preventive
        target: "Protection 类漏测的自动化测试覆盖"
        basis: "漏测分析聚合：Protection 类占比上升"
        priority: P2
        status: draft

degraded_notice: null

skipped_tickets:
  - ticket_ref: "ITR-2026-0088"
    change_type: conflict
    reason: "conflict resolution，未自动合并"
    recommended_action: "人工处理后重新触发变更检测"

  - ticket_ref: "ITR-2026-0099"
    change_type: modified
    resolution: manual_queue
    reason: "manual_queue 状态，需人工确认后进入重算"
    recommended_action: "确认变更内容后将其 resolution 更新为 auto_merged"
```

#### 9.7.2 与 S1 报告的差异

| 字段 | S1 ra-report | S2 difference ra-report |
|------|-------------|------------------------|
| `report_type` | `single_ticket` 或 `batch_summary` | `difference` |
| `change_summary` | 不存在 | **必须** — 变更摘要 |
| `sections` | 六维分析完整结果 | `dimension_diffs[]` 替代（逐维度前后差异） |
| `comparison` | `mode: none`（S1 逐单）或选项（S1 批量） | S2 必算，始终执行 |
| `improvement_refresh` | 不存在 | **必须** — 措施刷新提示 |
| `skipped_tickets` | 资格拒绝的 ticket | 资格拒绝 + conflict + manual_queue |
| 未受影响维度 | 不存在此概念 | 从 baseline 引用（`note: "未受影响，引用 baseline"`） |

#### 9.7.3 分析运行（analysis_run）创建

S2 分析完成后，创建新的 analysis_run 记录：

```
创建 analysis_run:
  run_id: "{new_batch_ref}-{timestamp}-{short_uuid}"
  batch_ref: new_batch_ref
  comparison_batch_ref: baseline_batch_ref     # S2 特有
  schema_version: new_batch 的 schema_version
  mapping_version: new_batch 的 mapping_version
  rule_version: 当前 analysis_rule_version
  time_window_start: 当前窗口起始
  time_window_end: 当前窗口结束
  recompute_mode: 'incremental' 或 'full'
  full_recompute_reason: 版本变更原因（full 模式时）或 null（incremental 模式时）
  report_refs:
    - report_id: "{run_id}-diff"
      type: difference
      ticket_refs: [所有 ticket 引用]
  metric_versions: 当前 metric_version

状态流转:
  1. insert_analysis_run(conn, run_dict)
     → 初始状态 'created'
  2. update_analysis_run_draft(conn, run_id, 'in_progress', report_refs_json)
     → 分析开始
  3. 分析成功后:
     update_analysis_run_draft(conn, run_id, 'completed', report_refs_json)
     → 等待 reviewer 发布（reviewer_publish_analysis_run）
```

#### 9.7.4 S2 管线步骤总览

将 §9.1–§9.7 串联为完整 S2 管线：

```
输入: new_batch_ref, baseline_batch_ref, change_set

Step S2-1: 前置校验（§9.1.3）
  - baseline batch 存在性
  - baseline analysis_run 存在性
  - 新 batch 存在性
  - 批次锁定检查

Step S2-2: 规则版本变更检测（§9.5.2）
  - 比较 schema_version, mapping_version, analysis_rule_version
  - 任一变更 → recompute_mode = 'full'
  - 均未变更 → 进入 Step S2-3

Step S2-3: 受影响维度判定（§9.2）
  - 仅 incremental 模式执行
  - 应用 §9.2.1 映射表
  - 输出 affected_dimensions[] + affected_tickets[]

Step S2-4: 创建 analysis_run（§9.7.3）
  - insert_analysis_run() → status = 'created'
  - update_analysis_run_draft() → status = 'in_progress'

Step S2-5: 执行重算（§9.3）
  - full 模式: 全量重算所有维度（等同 S1 批量分析）
  - incremental 模式: 仅重算 affected_dimensions
  - 环比同比始终重算

Step S2-6: 生成差异报告（§9.6）
  - 逐维度 before/after 比较
  - 显著变化标记（20% 阈值）
  - 环比同比计算
  - 措施刷新提示

Step S2-7: 输出（§9.7）
  - difference ra-report 草案
  - update_analysis_run_draft() → status = 'completed'
  - 等待 reviewer 确认发布
```

---

### 9.8 错误处理与降级

| 场景 | recompute_mode | 处理方式 | 输出 |
|------|---------------|---------|------|
| change_set 为空（全部 unchanged） | incremental | 跳过所有维度重算 | 空差异报告（§9.6.2），环比同比仍计算 |
| baseline batch 不存在 | — | blocked | 错误信息：基线批次缺失 |
| baseline analysis_run 不存在 | — | blocked | 错误信息：基线分析运行缺失 |
| 某维度重算异常 | incremental/full | 跳过该维度，其余维度继续 | 该维度 marked skipped + 详细错误原因 |
| 全部维度重算异常 | incremental/full | analysis_run → 'failed' | failed_tickets 清单 |
| comparison_batch 不可用 | — | 环比同比标记 N/A | comparison.mode = 'none' + na_reasons |
| 窗口数据不足 | — | 环比同比降级 | comparison.credibility = low |
| 某 ticket 数据不完整 | incremental/full | 该 ticket 跳过，其余继续 | 在 skipped_tickets 中记录 |
| SQLite 连接异常 | — | analysis_run → 'failed'（如果已创建） | 错误详情 |
| analysis_run INSERT 失败 | — | 不创建 run | SQLite 写入错误 |

---

### 9.9 安全与禁止事项

#### 9.9.1 S2 专属禁止项

除本 Skill 所有安全约束（见「安全与禁止事项」节）外，S2 增量重算额外约束：

| 编号 | 禁止行为 | 触发条件 | 严重度 |
|------|---------|---------|--------|
| P-S2-01 | 禁止覆盖 baseline ra-report 或 baseline analysis_run | S2 写入时目标包含 baseline 引用 | **阻断** |
| P-S2-02 | 禁止自动修改 measure_link 的 status 字段（即使 suggestion='complete'） | 差异报告中生成 improvement_refresh | **阻断** |
| P-S2-03 | 禁止在环比同比 N/A 时填充推算值 | 窗口不足/样本不足/口径变更 | **阻断** |
| P-S2-04 | 禁止在无对比数据时生成虚假环比趋势 | comparison_batch_ref 为 null | **阻断** |
| P-S2-05 | 禁止跳过规则版本检测直接使用 incremental 模式 | S2 入口未执行 §9.5.2 规则版本检测 | **阻断** |
| P-S2-06 | 禁止在 change_set 的 resolution='rejected' 时仍执行重算 | change.change_type 为 modified 但 resolution='rejected' | **阻断** |

#### 9.9.2 S2 允许的操作范围

| 操作 | 范围 | 说明 |
|------|------|------|
| SELECT 读取 ticket/ingestion_batch/ticket_version 表 | 新 batch + baseline batch 的清洗后字段 | 不读取 raw_json |
| SELECT 读取 change_history 表 | 按 batch_ref 查询 | 消费 ST-RA-06.1-DETECT 产出 |
| SELECT 读取 analysis_run 表 | 基线 analysis_run 查询 | 获取 baseline ra-report 引用 |
| INSERT 创建新 analysis_run | 仅通过 DAO `insert_analysis_run()` | 新 run_id，不覆盖历史 |
| UPDATE 更新分析运行草案状态 | 仅通过 DAO `update_analysis_run_draft()` | 仅 created/in_progress/completed/failed |
| 生成 CA/PA 候选草案 | 仅候选状态（draft） | 不批准不分发 |
| 输出 measure 刷新建议 | improvement_refresh.suggestion | 只读提示，不写入 |
| 同比环比计算 | 基于 SQLite 查询的纯数据聚合 | 不推断缺失数据 |

---

### 9.10 与相邻模块的集成契约

#### 9.10.1 上游依赖

| 上游 Story | 输出 | S2 消费方式 |
|-----------|------|------------|
| ST-RA-05.3-ANALYZE（S1 管线） | baseline ra-report + baseline analysis_run | 通过 `get_runs_by_batch(conn, baseline_batch_ref)` 获取最新 completed/published run，读取其 report_refs |
| ST-RA-06.1-DETECT（变更检测） | change_history 表 | 通过 `get_changes_by_batch(conn, new_batch_ref)` 获取变更集 |
| ST-RA-02（六维引擎） | 六维分析方法（§3-§5） | 同 Skill 内复用，增量模式下仅对受影响维度调用 |
| ST-RA-INGEST-DB（数据库） | SQLite schema + DAO 接口 | 通过 `data/dao.py` 公共接口访问 |

#### 9.10.2 下游消费

| 下游 Story | 消费内容 | 传递方式 |
|-----------|---------|---------|
| ST-RA-06.3-TRACK（措施基线管理） | 差异报告中的 `improvement_refresh`（措施刷新提示） | ra-report difference 文件的 `improvement_refresh` 段 |
| ST-RA-03（改进输入治理） | 差异报告中的 `improvement_refresh.new_candidates`（新 CA/PA 候选） | ra-report difference 文件的 `improvement_refresh.new_candidates[]` |
| ST-RA-07（质量报告看板） | 环比同比 comparison 数据 | ra-report difference 文件的 `comparison` 段 |

#### 9.10.3 与 §6 S1 管线的边界

| 边界 | S1（§6） | S2（§9） |
|------|---------|---------|
| 入口条件 | batch_id 或 source_ticket_id（无 baseline） | new_batch_id + baseline_batch_id + change_set |
| 分析模式 | 逐单分析 或 批量分析（首次） | 增量重算 或 全量重算 |
| 报告类型 | single_ticket / batch_summary | difference |
| baseline 概念 | 不存在（首次分析） | 必须（对比基线） |
| 环比同比 | 可选（S1 批量模式） | 必须（始终重算） |
| 措施提示 | 不存在 | 必须（improvement_refresh） |
| recompute_mode | 固定 'full' | 'incremental' 或 'full' |

---

### 9.11 开放项与假设

| ID | 类型 | 描述 | 状态 | 重访条件 |
|----|------|------|------|---------|
| OPEN-RA062-01 | decision | 规则版本变更的精确判定范围（仅 analysis_rule_version？还是 mapping_rule_version 也触发？schema_version 呢？） | OPEN | 当前保守策略：任一不同即全量重算 |
| OPEN-RA062-02 | decision | 环比同比 N/A 的最小同口径样本阈值 | OPEN | 默认 10，可在 metric-definition.yaml 中覆盖 |
| OPEN-RA062-03 | decision | change_set 的传递格式（已确认：SQLite change_history 表） | RESOLVED | ST-RA-06.1-DETECT 使用 change_history 表 |
| OPEN-RA062-04 | 假设 | 措施刷新提示不自动修改状态，由 ST-RA-06.3-TRACK 消费 | OPEN | improvement_refresh.suggestion 为只读提示 |
| OPEN-RA062-05 | 假设 | 差异报告中 "significant change" 的变化率阈值为 20% | OPEN | 可作为可配置参数 |

---

### 9.12 测试设计

#### 9.12.1 正向场景

| ID | 场景 | 前置条件 | 预期结果 |
|----|------|---------|---------|
| T-S2-01 | 规则版本未变 + root_cause 字段变更 → 增量重算 | new_batch 的 rule_version 与 baseline 一致，1 条 ticket 的 root_cause 变更 | recompute_mode='incremental'，仅 RC 维度重算，PQ/ESC/TM/IMP 引用 baseline |
| T-S2-02 | 规则版本变更（analysis_rule_version 递增）→ 全量重算 | new_batch 的 rule_version > baseline rule_version | recompute_mode='full'，所有维度全部重算，full_recompute_reason 非空 |
| T-S2-03 | 环比同比 mom 计算 | 当前月 vs 上月窗口，样本量 >= 10 | comparison.mode='mom'，指标含 baseline/current/change_rate/credibility |
| T-S2-04 | 环比同比 yoy 计算 | 当前季 vs 去年同季窗口，样本量 >= 10 | comparison.mode='yoy'，同口径聚合 |
| T-S2-05 | 差异报告显著变化标记 | 某维度 change_rate >= 20% | significance=true + significance_reason |
| T-S2-06 | 措施刷新提示（keep） | 已批准措施关联的根因未变更 | suggestion='keep' |
| T-S2-07 | 新增 ticket 全维度分析 | change_type='new' | 该 ticket 执行完整六维分析，所有维度标记受影响 |

#### 9.12.2 负向/边界场景

| ID | 场景 | 前置条件 | 预期结果 |
|----|------|---------|---------|
| T-S2-08 | baseline batch 不存在 | baseline_batch_ref 指向不存在的 batch | blocked，错误信息输出 |
| T-S2-09 | change_set 全部 unchanged | 所有 ticket 的 change_type='unchanged' | 空差异报告，dimension_diffs=[]，环比同比仍计算 |
| T-S2-10 | 环比同比窗口不足 | 基期窗口不是完整自然月 | comparison.mode='none'，na_reasons='incomplete_window' |
| T-S2-11 | 环比同比样本量不足 | 基期样本量 < 10 | comparison.credibility='low' 或 comparison.mode='none'（取决于阈值） |
| T-S2-12 | 环比同比零基线 | baseline_value=0 | change_rate='N/A'，标注 zero_baseline |
| T-S2-13 | 某维度重算异常 | 受影响维度的重算过程中出错 | 该维度 marked skipped，其余维度正常 |
| T-S2-14 | change_set 含 conflict ticket | 部分 ticket 的 change_type='conflict' | 在 skipped_tickets 中记录，不进入重算 |

#### 9.12.3 Fixture 设计

| Fixture | 覆盖场景 | 关键数据 |
|---------|---------|---------|
| `fixtures/s2_incremental_root_cause_change.json` | T-S2-01 | 2 个 batch（baseline + new），1 条 ticket 的 root_cause 变更，rule_version 不变 |
| `fixtures/s2_full_recompute_rule_version.json` | T-S2-02 | 2 个 batch，rule_version 递增 |
| `fixtures/s2_comparison_mom.json` | T-S2-03 | 上月 + 本月窗口，各 >= 10 条 ticket |
| `fixtures/s2_empty_change_set.json` | T-S2-09 | 新 batch 与 baseline 完全相同（所有 unchanged） |
| `fixtures/s2_insufficient_window.json` | T-S2-10 | 基期窗口为半月（非完整自然月） |
| `fixtures/s2_zero_baseline.json` | T-S2-12 | baseline 某指标值为 0 |
| `fixtures/s2_improvement_refresh.json` | T-S2-06 | 已批准 CA/PA + 变更前后对比 |

---

### 9.13 与 §6 S1 管线的协同

S1 和 S2 管线在本 Skill 中协同工作：

| 协同场景 | S1 角色 | S2 角色 |
|---------|--------|---------|
| 首次批次分析 | 执行完整 S1 批量分析 → ra-report（batch_summary） | 不触发（无 baseline） |
| 后续批次分析 | 不执行（跳过） | 消费 S1 ra-report 作为 baseline → S2 增量重算 |
| 周期复盘 | 不执行（跳过） | 消费历史 S1/S2 ra-report 作为 baseline → 环比同比 |
| 措施效果评估 | 不执行（跳过） | 消费已批准措施 + 新数据 → improvement_refresh |

**入口路由规则**：

```
ptm-tse Agent 调用时:
  if 输入包含 baseline_batch_ref:
      → 路由到 S2 管线（§9）
  else:
      → 路由到 S1 管线（§6）
```

S1 和 S2 不并行执行：同一个 batch 要么走 S1（首次分析），要么走 S2（对比分析），不能同时执行。

---

## §10 Gotchas

> 本节记录 reverse-analysis Skill 的常见误用、陷阱和必须注意的边界行为。每一条均来自设计契约中的显式约束（三线阈值、状态机门控、降级策略、权限边界）或已知踩坑记录。

### G-RA-01: evidence_backed 状态不可由 AI 自动跃迁

**现象**：根因分析结果显示 `current_level = evidence_backed`，但实际上 `valid_count < 3`。

**原因**：根因状态机（§4.2.2）明确规定 `ai_candidate → evidence_backed` 的跃迁必须有三条有效证据线支撑（阈值检查），且 §7.1 追加了二次校验。但如果在实现时跳过阈值检查，或误将 `category=unknown` 的证据线计入 `valid_count`，就会产生"证据不足却显示有证据支撑"的假象。

**规避**：
1. 在每次更新 `current_level` 前，必须重新计算 `valid_count`（§2.4.1）
2. `category=unknown` 或 `validity=incomplete` 的证据线**绝不**计入 `valid_count`
3. 在输出 ra-report 前，执行 §7.1.2 定义的二次校验：如果 `valid_count < 3` 且 `current_level` 为 `evidence_backed` 或 `reviewer_confirmed`，强制覆盖为 `ai_candidate` 并追加 `transition_log`
4. 不要在 `valid_count` 接近 3（如 2）时放宽阈值（P-09 明确禁止）

**检测信号**：ra-report 的 `sections.root_cause.current_level = evidence_backed` 但 `eligibility.threshold.valid_count < 3`。

---

### G-RA-02: 无可信分母时必须降级为数量/占比，不能称密度

**现象**：产品质量分析报告中出现"缺陷密度"、"DPMO"、"每千行代码缺陷数"等术语，但分母数据未经验证。

**原因**：§5.2.2 明确规定：当 `denominator.trusted = false` 或分母字段不可获取时，只能输出绝对数量、占比、Pareto 分布和趋势方向。但 AI 在自然语言生成中可能不经意使用"密度"措辞，即使数值本身是按数量计算的。

**规避**：
1. 在 ra-report 生成时检查 `denominator.trusted` 字段，若为 `false`，在报告顶部显式写入降级声明（§5.2.3 模板）
2. 生成文本结论前，用关键词扫描（"密度"、"DPMO"、"每千行"、"速率"）并替换为"数量"、"占比"
3. 在 `degraded_notice` 中明确"不得将此数据标注为缺陷密度"
4. 如果用户特别要求密度指标，必须指明需要补充哪些分母数据并进行可信标记

**检测信号**：ra-report 中包含"密度"、"DPMO"、"每千行"字样，且 `degraded_notice` 为空或 `denominator.trusted = false`。

---

### G-RA-03: escape layer 默认必须为 candidate，不可在无证据时标 confirmed

**现象**：流出分析中所有控制层都被标记为 `confirmed_layers[]`，但实际没有任何控制层执行证据。

**原因**：§5.3.2 明确规定"当完全没有控制证据字段或所有控制证据都不足以 confirm 时，所有 escape point 标记为 candidate"。confirmed 需要同时满足三个条件：存在执行证据、证据覆盖了与问题相关的范围、来源可追溯。AI 可能在推理时过于自信，将"本应在代码评审中发现"推断为"代码评审已执行但未发现"。

**规避**：
1. 在 §8.4 越权检测的输出前检查中，扫描 `escape_analysis.confirmed_layers[]`，确认每条记录都有对应的 `evidence_ref`
2. 如果没有任何控制层有 evidence_ref，`confirmed_layers[]` 必须为空数组
3. 在 ra-report 中显式输出说明："当前未提供各控制层的执行证据。以下逃逸点分析基于问题特征推断，标注为 candidate。如需确认，请提供各控制层的实际执行记录。"
4. 不要将"典型流程中通常会执行"等同于"本次已执行且有记录"

**检测信号**：`escape_analysis.confirmed_layers[]` 非空但其中的条目缺少 `evidence_ref`。

---

### G-RA-04: S2 规则版本变化触发全量重算，性能影响显著

**现象**：S2 增量重算时，仅 1 条 ticket 的 `title` 字段变更，但触发了全部 500 条 ticket 的全量重算（`recompute_mode = full`）。

**原因**：§9.5.2 规则版本变更检测采用**保守策略**：`schema_version`、`mapping_version` 或 `analysis_rule_version` 任一不同即触发全量重算。这是因为规则版本变更可能导致所有已计算指标的口径变化，增量重算无法保证一致性。

**规避**：
1. 在修改 `field-mapping.yaml`、`metric-definition.yaml` 或 `schema.sql` 前，评估是否真的需要版本递增
2. 对于向后兼容的规则扩展（如新增一个可选字段映射，不改变已有映射），可以保持版本号不变
3. 如果必须全量重算，在 analysis_run 的 `full_recompute_reason` 中记录具体变更内容，供审计追溯
4. 预期：S2 全量重算的耗时与 S1 批量分析相当（大样本 > 100 条时可能需要较长处理时间，OPEN-RA053-03）

**检测信号**：`recompute_mode = full` 且 `full_recompute_reason` 包含 `rule_version` 变更，但变更仅涉及新增可选字段。

---

### G-RA-05: 环比同比样本量 < 10 时标记 N/A，小样本容易误导

**现象**：某产品本月只有 3 条 P1 问题，上月有 8 条 P1，变化率计算为 -62.5%，看起来改善显著——但实际是因为分母太小导致的统计噪声。

**原因**：§3.2.6 Step CMP-2 定义了最小样本量阈值（默认 10）。`max(基期样本量, 当期样本量) < 10` 时标记 `sample_insufficient`，credibility 降为 `low`，且当所有指标都样本不足时 `comparison.mode = "none"`（§9.5.6）。

**规避**：
1. 不要将 `credibility = low` 的环比同比结果作为决策依据
2. 如果产品线样本量持续偏低（< 10），建议拉长分析窗口（月度 → 季度）以增加样本量
3. 在报告中显式输出 `na_reasons[]`："样本量不足：基期 N1 条，当期 N2 条，最小阈值 10"
4. 最小阈值可通过 `metric-definition.yaml` 的 `min_sample_size` 覆盖（OPEN-RA062-02）

**检测信号**：`comparison.metrics[].credibility = low` 或 `comparison.mode = none` + `na_reasons = ["insufficient_sample_size"]`。

---

### G-RA-06: 差异报告不自动发布，缺少 reviewer 确认会被静默忽略

**现象**：S2 差异报告生成后 `analysis_run.status = completed`，但下游消费方（如看板、改进跟踪）没有收到更新。

**原因**：§6.7.1 明确定义：`completed → published` 的跃迁是**人工门控操作**，必须由 reviewer 通过 `reviewer_publish_analysis_run()` 显式确认后才能发布。状态停留在 `completed` 时，报告的 ra-report 和 difference 数据虽然存在，但未被正式"发布"给下游消费。

**规避**：
1. 在分析完成后输出提示："差异报告已生成（analysis_run: {id}，状态: completed）。请 reviewer 确认发布后方可进入下游消费。"
2. 不要在所有步骤完成后自动调用 `reviewer_publish_analysis_run`（§6.7.3 明确禁止）
3. 通过 DAO `get_runs_by_batch()` 定期查询 `status = completed` 但未发布的 run，通知 reviewer
4. 下游消费方应配置为只消费 `status = published` 的 analysis_run

**检测信号**：`analysis_run.status = completed` 超过预期时间窗口（如 24 小时）仍未变为 `published`。

---

### G-RA-07: raw_json 被误读入分析正文

**现象**：ra-report 的分析结论中出现了原始 ITR 响应的 JSON 片段（如 `"custom_fields": {"internal_note": "..."}`），违反了敏感信息不入正文的安全约束。

**原因**：§1.2 Step 1 明确禁止读取 `ticket.raw_json` 列进入分析正文。但以下场景可能导致误读：
- DAO 查询时 `SELECT *` 包含了 `raw_json` 列
- LLM 在分析报告生成时引用了传入的完整 ticket 字典（含 raw_json）
- 从快照文件中直接读取的 JSON 被传给了分析引擎

**规避**：
1. DAO 查询明确字段列表，不包含 `raw_json`
2. 在传给六维分析引擎之前，显式从 ticket 字典中删除 `raw_json` 键
3. 在 §8.4 越权检测的输出前检查中扫描 ra-report，禁止出现 `password`、`token`、`secret`、`credential` 等字段名（P-17）以及原始 JSON 结构特征（`{` 开头的非结构化文本）
4. 测试覆盖（T-RA01-03）：验证 `raw_json` 不入分析正文

**检测信号**：ra-report 的 `sections` 中出现 JSON 结构文本或 `raw_json` 字样。

---

### G-RA-08: P-xx 禁止规则触发后的拒绝响应格式不标准

**现象**：当 §7.4 或 §8.5 的禁止规则触发时（如 P-01 "valid_count < 3 时试图输出 evidence_backed"），Skill 返回的错误信息格式不符合 `denial_record` 标准（§8.4.3），下游调用方（ptm-tse Agent）无法解析。

**原因**：§7 和 §8 分别定义了不同的拒绝输出格式：§7.3 的证据不足报告使用 `report_type: insufficient_evidence` 结构，§8.4.3 的越权拒绝使用 `denial_record` 结构。如果在实现时没有按正确格式输出，调用方的错误处理逻辑可能无法识别拒绝类型（是证据不足还是越权）。

**规避**：
1. 禁止规则 P-01 至 P-11（§7.4）触发时，输出 §7.3.1 定义的 `insufficient_evidence` 报告结构
2. 禁止规则 P-12 至 P-19（§8.5.4）触发时，输出 §8.4.3 定义的 `denial_record` 结构（含 `denial_code`）
3. 不要混用两种格式——例如 P-10（阈值降级）是 §7 的禁止项，不应使用 §8 的 `denial_code`
4. 在 Skill 入口处先执行 §8 越权检查，再执行 §7 证据检查（§8.5.3 优先级规则）

**检测信号**：返回的拒绝消息中缺少 `report_type: insufficient_evidence`（对于 §7 禁止项）或缺少 `denial_code`（对于 §8 禁止项）。

---

### G-RA-09: evidence_set 中 category=gap 的证据线未正确设置 gap_owner

**现象**：证据不足报告中所有 gap 的 `gap_owner` 都是"待确认"，导致无法明确补充责任人。

**原因**：§2.3.2 定义了三个默认 gap_owner 分类（"PTM-TSE/测试架构师"、"ITR 录入方/产品团队"、"待确认"），但未提供明确的自动分类规则。实现时可能将所有无法判定的 gap 都设为"待确认"，降低了报告的可操作性。

**规避**：
1. 按以下规则自动分类 gap_owner：
   - 缺失字段为 `root_cause`、`test_missed_analysis`、`improvement_measures` → owner: "PTM-TSE/测试架构师"
   - 缺失字段为 `description`、`title` → owner: "ITR 录入方/产品团队"
   - 缺失字段为 `module`、`status` → 根据问题上下文判定，默认"ITR 录入方/产品团队"
   - 无法确定 → owner: "待确认"
2. 在 §7.2 的 gap_source 分类中同时输出根因维度（ITR 缺失/测试缺失/流程缺失/外部依赖），与 gap_owner 互补

**检测信号**：`gap_report` 中所有条目的 `gap_owner = "待确认"`，但缺失字段属于可分类范围。

---

### G-RA-10: MetricDefinition 版本号递增后未更新关联的 analysis_run

**现象**：修改了 `metric-definition.yaml` 的指标口径并递增了 `metric_version`，但已完成的 `analysis_run` 记录中 `rule_version` 仍指向旧版本，导致规则版本变更检测（§9.5.2）对比时出现不一致。

**原因**：`metric_version` 作为 MetricDefinition 的版本标识，在 §5.1.2 中定义为"变更时必须递增"。但 `analysis_run.rule_version` 是在分析运行时**快照**的当时版本，不应事后修改。如果新分析检测到 `rule_version` 变化但 baseline 记录仍为旧版本，这正是规则版本变更检测的预期行为——触发全量重算。

**规避**：
1. 已完成（`completed`/`published`）的 analysis_run 中的 `rule_version` **不可修改**（§6.4.3）
2. 修改 metric-definition.yaml 后，下一个增量或周期分析将自动检测到版本变更并触发全量重算
3. 不要在修改 metric-definition 后手动回填旧 analysis_run 的版本号
4. 版本追溯通过 metric-definition.yaml 的 YAML 多文档格式（`---` 分隔）实现，不依赖 analysis_run

**检测信号**：新 S2 分析的 `baseline_run.rule_version != current_rule_version`，这是正常触发全量重算的信号，不是错误。

### 允许事项

| 操作 | 范围 |
|------|------|
| SELECT 读取 ticket/ingestion_batch/ticket_version 表 | 仅清洗后字段，不读取 raw_json |
| 调用 DAO 公共只读接口 | `get_tickets_by_batch()`, `get_batch()`, `get_ticket_by_source_id()`, `get_tickets_by_time_range()`, `get_tickets_by_product()` |
| 在内存中构建 EligibilityResult 和 EvidenceLineSet | 单次调用生命周期内 |
| 在内存中执行六维分析（根因/产品质量/流出/漏测/改进/环比同比） | 单次分析运行生命周期内 |
| 生成 RA Report 草案（ra-report.yaml 格式） | 仅草案状态，不发布 |
| 生成 CA/PA 候选草案 | 仅候选状态（draft），不批准不分发 |
| 输出分析结果到 analysis_run 表 | 仅通过 DAO `insert_analysis_run()` / `update_analysis_run_draft()`（草案状态 created/in_progress/completed/failed） |
| 查询已有分析运行记录 | 通过 DAO `get_analysis_run()` / `get_runs_by_batch()` |
| 引用 MetricDefinition 模板进行计算 | 只读引用，不修改模板定义 |

### 禁止事项

| 禁止操作 | 原因 |
|----------|------|
| 直接执行 SQL（INSERT/UPDATE/DELETE/DDL） | 只能通过 DAO 公共接口访问数据库 |
| 修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore` | 属于 FEAT-RA-INGESTION 的写入范围 |
| 读取 `ticket.raw_json` 进入分析正文 | 原始响应体可能含敏感信息，不进入分析管线 |
| 连接外部系统（HTTP/网络请求） | deny-by-default，不允许出站连接 |
| 读取环境变量、配置文件、认证凭据 | 无凭据原则 |
| 自动确认根因（将状态设为 evidence-backed 或 reviewer-confirmed） | 必须经过三线阈值 + reviewer 人工确认 |
| 自动分发 CA/PA | 改进措施只生成候选列表，不发起审批或分发 |
| 修改 ticket 表（含 quality_flag、状态等） | 只读消费，不修改源数据 |
| 修改 ticket_version 或 ingestion_batch 表 | 只读消费 |
| 自动调用 `reviewer_publish_analysis_run` | 发布操作仅 reviewer 通过 ptm-tse Agent 显式确认后执行 |
| 通过 `update_analysis_run_draft` 将状态设为 `published` | DAO 层硬编码拒绝，会抛出 ValueError |
| 从 `failed` 状态恢复 analysis_run | failed 不可重试；必须创建新的 analysis_run |
| 将 `raw_statement` 直接展示为分析结论 | 必须经过 AI candidate 标注 |
| 将降级数据标注为"缺陷密度"或"DPMO" | 无可信分母时只能输出数量/占比/Pareto/趋势 |
| 将无控制证据的 escape layer 标记为 confirmed | 必须严格区分 candidate/confirmed escape layer |
| 跳过证据不足的维度或输出虚假结论 | 证据不足时输出 gap report，不输出虚假结论 |
| 在 `valid_count < 3` 时输出 `evidence_backed` 或 `reviewer_confirmed` 根因 | §7.1 硬阻断，最高 `ai_candidate`（P-01） |
| 为空的证据字段（root_cause/description 等）生成虚构值 | AI 无权限"创作"证据（P-05） |
| 从 `raw_json` 提取未映射数据补证据缺口 | `raw_json` 不入正文，且证据必须来自清洗后字段（P-06） |
| 在 `RuntimeDataGovernanceReport` 非 `compliant` 时读取、创建或发布问题单材料 | 先阻断并返回治理缺口；不得以分析降级绕过权限/分类预检 |
| 修改既有运行数据权限、删除/迁移/导出或改变保留状态 | 仅安装项目的 Agent 在用户明确本地运行授权下可走独立修复路径；本 Skill 不执行 |
| 将阈值从 3 降为 2 或 1 | 三线阈值来自 HLD 设计基准，不可运行时修改（P-09） |
| 将 `validity=incomplete` 或 `category=unknown` 的证据线计入 `valid_count` | §2.4.1 明确定义，不可放宽（P-11） |
| 将其他 ticket 的证据线"借用"到当前 ticket | 每 ticket 证据独立，不得跨单补证（P-08） |
| 在证据不足时生成 CA/PA 候选 | §3.2.5 Step IMP-1 前置条件 + §7.4 P-04 双重门控，禁产虚假改进措施 |

### 安全声明

> 本 Skill 遵循 HLD REV-03 可信治理约束：
> - **deny-by-default**：无凭据、无外部写入、无自动确认
> - **只读分析**：不修改源数据，分析结论与源数据分离
> - **事实与假设分离**：所有输出区分事实（fact）、假设（hypothesis）、未知（unknown）和缺口（gap）
> - **不可自动跃迁**：根因状态机的 evidence_backed 和 reviewer_confirmed 状态不可由 AI 自动设置
> - **不可无分母称密度**：denominator.trusted = false 或无分母数据时，只能输出数量/占比/Pareto/趋势，绝不允许标注为"缺陷密度"、"DPMO"或类似密度指标
> - **不可无证据称 confirmed**：流出分析的 escape layer 在没有控制证据时只能标记为 candidate
> - **敏感字段不入正文**：raw_json 和未经清洗的字段不进入分析输出

---

## 平台差异

| 平台 | 差异项 | 影响 | 处理 |
|------|--------|------|------|
| Claude Code | Skill 发现：`skills/reverse-analysis/SKILL.md` | 无差异 | 标准文件路径 |
| Codex | Skill 发现：`.agents/skills/reverse-analysis/SKILL.md`（安装后） | 安装路径不同 | 安装器负责映射；Skill 内使用 `skills/reverse-analysis/` canonical 路径 |
| Qoder | Skill 发现：`.qoder/skills/reverse-analysis/SKILL.md`（安装后） | 同上 | 同上 |

**结论**：本 Skill 的资格检查、证据分类、六维分析引擎和根因状态机逻辑在所有平台一致，不依赖平台特定能力。

---

## 不适用边界

| 场景 | 说明 |
|------|------|
| 非 ITR 来源的问题单 | 本 Skill 假定数据来自 ITR 系统，使用 ITR 特定字段。其他来源的问题单可能缺少 severity、root_cause 等字段，导致大量 gap |
| 实时在线分析 | 本 Skill 基于 SQLite 离线数据分析，不支持实时 ITR 查询 |
| 自动化 CA/PA 分发 | 本 Skill 只生成候选措施列表，不连接改进跟踪系统 |
| 跨 Feature 数据写入 | 本 Skill 不直接写入 FEAT-RA-TRACKING 的 measure_link 表 |
| 无控制证据的分析 | 缺少控制层执行证据时，流出分析只能产出 candidate escape layers |
| 无分母的质量度量 | 无法获取可信分母时，不输出缺陷密度指标（降级为数量/占比/Pareto/趋势） |
| 运行数据不合规 | `RuntimeDataGovernanceReport` 非 `compliant` 时不读取、分析或发布；由 ptm-tse Agent 在安装项目中说明所需授权与修复路径 |

---

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|---------|
| 1.0 | 2026-07-16 | meta-dev | 初始版本，§1 资格检查（P1/P2/P3/P4 判定、内部问题识别、质量前置检查）+ §2 可信输入建立（五条证据线分类、三线阈值检查）+ §3-§8 占位符。来源：ST-RA-01 LLD v1.1。 |
| 1.1 | 2026-07-16 | meta-dev | ST-RA-02 实现：§3 六维分析引擎（六大维度逐维度分析规则 + 事实/假设分离）+ §4 根因状态机（四层递进 + 状态转换规则与门控 + 三线阈值硬阻断）+ §5 指标定义与降级（MetricDefinition 契约 + 无可信分母降级策略 + 流出证据分类）。原 §5-§8 占位符重新编号为 §6-§9。新建 templates/ra-report.yaml 和 templates/metric-definition.yaml。更新允许/禁止事项和安全声明。来源：ST-RA-02 LLD v1.1。 |
| 1.2 | 2026-07-16 | meta-dev | ST-RA-05.3 实现：§6 S1 分析管线（逐单/批量分析流程、analysis_run 创建与管理、AnalysisRunManifest 定义、报告草案输出与 reviewer 发布路径）。更新前置条件 DAO 接口列表（新增 analysis_run 管理接口）、权限声明（从只读扩展为受限写入）、允许/禁止事项表。新建 templates/analysis-run-manifest.yaml。来源：ST-RA-05.3-ANALYZE LLD v1.2。 |
| 1.3 | 2026-07-16 | meta-dev | ST-NRA-01 实现：§7 证据不足保护（证据线阈值硬阻断二次校验 + 缺失证据四类 gap_source 扩展 + 证据不足报告结构定义 + 禁止行为 11 项清单 P-01 至 P-11）。原 §7 占位符替换为完整防护章。负向防护逻辑，不新增分析功能。来源：ST-NRA-01 technical-note。 |
| 1.4 | 2026-07-16 | meta-dev | ST-NRA-02 实现：§8 权限边界拒绝与越权保护（deny-by-default 四类操作总则 + 外部访问拒绝 3 类：外部系统连接/凭据读取/HTTP 写入 + 生产操作拒绝 3 类：自动分发 CA/PA/自动创建下游任务/自动关闭工单 + 越权检测与阻断 10 项检测规则 + denial_record 审计日志格式 + 拒绝矩阵速查 9 类 + 禁止行为扩展 P-12 至 P-19）。原 §8 占位符替换为完整防护章。与 §7 共同构成本 Skill 的双层负向防护体系。来源：ST-NRA-02 technical-note（Story 卡片 STORY-NRA-02-permission-boundary-denial.md）。 |
| 1.5 | 2026-07-16 | meta-dev | ST-RA-06.2 实现：§9 S2 增量重算与差异报告（§9.1 增量重算触发 + §9.2 受影响维度判定 — 变更字段→维度映射表 + §9.3 增量重算策略 — 逐维度最小重算原则 + §9.4 comparison_batch_ref 管理 + §9.5 recompute_mode 判定 — 规则版本变更→全量重算 + §9.6 差异报告生成 — before/after 对比 + 20% 显著变化阈值 + §9.7 差异报告输出格式 — 完整 difference ra-report 结构）。含措施刷新提示、环比同比始终重算规则、空差异报告、S2 管线八步串联、安全禁止项 P-S2-01/06、上下游集成契约、14 条测试场景、7 组 Fixture 和 S1/S2 路由协同。原 §9 占位符替换为完整 S2 章。来源：ST-RA-06.2-REFRESH LLD v1.1。 |
| 1.6 | 2026-07-17 | host-orchestrator | CR-031：增加安装项目运行根、预检阻断、敏感报告输出权限和不实施本地数据修复的契约。 |
