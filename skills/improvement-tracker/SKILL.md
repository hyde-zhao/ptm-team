---
name: improvement-tracker
description: 基于已确认的逆向分析结论（analysis-confirmed RA Report）生成结构化 CA/PA 提案草案，执行人工 reviewer 批准门控，产出不可变的 Approved Improvement Input 供下游 Agent 只读消费。覆盖 CA/PA 草案生成、批准状态机（draft→approved/rejected）、未批准门控拒绝、消费者映射（target_agent→consumer_status）和不可变输入产出。不自动批准 CA/PA，不自动分发到下游，不直接创建下游任务，不修改分析结论。
argument-hint: "<ra_report_id> [--mode generate-proposal|review-proposal|publish-input|check-gate] [--proposal-id <id>]"
user-invokable: false
status: active
shared: true
shared_writers:
  - ST-RA-03（§3：CA/PA 治理 — 草案生成、批准状态机、Approved Input 生成、消费者映射）
  - ST-RA-04（§4：闭环跟踪）
  - ST-RA-06.3-TRACK（§5：措施基线管理与刷新提示）
version: "1.3"
source_cr: "CR-030, CR-031"
source_feature: "FEAT-RA-IMPROVEMENT"
---

# improvement-tracker

## 目标

基于已确认的逆向分析结论（`analysis-confirmed` 状态的 RA Report），生成结构化的 CA/PA 提案草案，经人工 reviewer 批准后产出不可变的 Approved Improvement Input，供下游 Agent 只读消费。

**核心原则**：
- **deny-by-default**：未确认的分析结论不生成 CA/PA；未批准的 CA/PA 不产出 Approved Input
- **人工 reviewer 唯一批准者**：系统（Skill/AI）不得自动批准或拒绝 CA/PA
- **审批后不可回退**：`approved` 和 `rejected` 是终态
- **产出不可变**：Approved Improvement Input 生成后所有字段不可修改
- **不自动分发**：不调用下游 Skill 工具，不自动创建下游任务

**当前版本实现状态**：
- ST-RA-03：CA/PA 治理 — 草案生成、批准状态机、Approved Input 生成、消费者映射（§3）— 已实现
- ST-RA-04：闭环跟踪 — 行动项管理、有效性检查、观察窗、关闭决策四条件（§4）— 当前实现
- ST-RA-06.3-TRACK：措施基线管理与刷新提示 — MeasureBaseline 创建、基线版本控制、刷新提示规则、reviewer 唯一状态变更者、禁止行为（§5）— 已实现

## 前置条件

1. **RA Report 就绪**：上游 `reverse-analysis` Skill 已产出 `analysis-confirmed` 状态的 RA Report，且包含：
   - `analysis_status = "analysis-confirmed"`
   - `confirmed_by` 非空（已由人工 reviewer 确认）
   - `confirmed_at` 非空
   - 包含改进维度的分析结论（root_cause_analysis、escape_analysis 等）
2. **模板可用**：`skills/improvement-tracker/templates/capa-proposal.yaml` 和 `approved-input.yaml` 存在且通过 schema 校验
3. **调用方**：ptm-tse Agent（测试架构师），通过 Skill 触发词调用本 Skill

## 运行数据治理契约

本 Skill 的运行根由 ptm-tse Agent 解析：默认是安装后的 `ptm-tse` 项目根，`data_root` 固定为 `<runtime-root>/data/`。不得把 `ptm-team` 源码根、全局用户目录或任意 CWD 作为输出位置。

调用方必须先提供 `RuntimeDataGovernanceReport`。仅 `status=compliant` 时可在已受限的 `<runtime-root>/data/` 子目录保存含问题单材料的 CA/PA 草案、Approved Improvement Input、行动项、有效性检查或措施基线；相关目录必须为 `0700`、相关文件必须为 `0600`。本 Skill 不执行运行数据预检修复，也不对已有文件执行 `chmod`、删除、迁移、导出或保留清理；报告非 `compliant` 时必须拒绝生成或发布并返回治理缺口。

## 触发条件与适用场景

### 触发条件

本 Skill 由 ptm-tse Agent 在以下场景触发调用：

| 场景 | 触发描述 | 前置条件 |
|------|----------|----------|
| 生成 CA/PA 草案 | 用户要求为已确认的 RA Report 生成改进措施草案 | RA Report `analysis_status = "analysis-confirmed"` |
| 审查提案 | reviewer 审查 CA/PA 草案并做出批准/拒绝决定 | CA/PA Proposal 处于 `draft` 状态 |
| 发布改进输入 | 批准后生成 Approved Improvement Input | CA/PA Proposal `approval_status = "approved"` |
| 门控检查 | 验证前置条件是否满足 | 提供 analysis_ref 或 proposal_id |

### 执行模式

| 模式 | 触发词 | 输入 | 输出 | 失败行为 |
|------|--------|------|------|----------|
| `generate-proposal` | "为 RA Report 生成 CA/PA 草案" | RA Report ID + analysis_run ID | `capa-proposal.yaml` 草案 | 未确认 RA → 拒绝生成，提示原因 |
| `review-proposal` | "审查 CA/PA 提案" | proposal_id + 审批决定（approve/reject） | 更新 approval_status 和 approval_ref | 提案非 draft 状态 → 拒绝操作 |
| `publish-input` | "发布改进输入" | proposal_id（已批准） | `approved-input.yaml` | 提案未批准 → 拒绝生成 |
| `check-gate` | "检查门控状态" | analysis_ref 或 proposal_id | 通过/拒绝 + 原因 | 前置条件不满足 → 返回拒绝原因 |

---

## §1 输入契约

### 上游输入（来自 reverse-analysis Skill）

从 `reverse-analysis` Skill 接收的 RA Report 必须满足以下契约：

```yaml
# 必须条件
analysis_status: "analysis-confirmed"           # 人工 reviewer 已确认分析结论
confirmed_by: string                            # 非空，reviewer 标识
confirmed_at: datetime                          # 非空，ISO 8601 格式

# 必须数据
ra_report_id: string                            # 非空，RA Report 唯一标识
root_cause_analysis: object                     # 含 confirmed root cause
escape_analysis: object                         # 含 confirmed escape points
improvement_dimensions: list                    # 待改进维度列表
```

不满足时必须返回拒绝原因，不生成 CA/PA 草案。

### 输出契约

| 执行模式 | 输出文件 | 位置 | 说明 |
|----------|----------|------|------|
| `generate-proposal` | `capa-proposal.yaml` | `<runtime-root>/data/improvement/` | CA/PA 草案，approval_status=draft，敏感文件 `0600` |
| `publish-input` | `approved-input.yaml` | `<runtime-root>/data/improvement/` | 不可变 Approved Input，敏感文件 `0600` |

---

## §2 数据模型

### §2.1 CA/PA Proposal 模板

详见 `skills/improvement-tracker/templates/capa-proposal.yaml`。

必填字段：`proposal_id`、`analysis_ref`、`kind`、`title`、`basis`、`target`、`owner`、`due_date`、`priority`、`validation_method`。

约束：
- `proposal_id` 全局唯一，不可变，格式 `PROPOSAL-{timestamp}-{seq}`
- `kind` 枚举：`corrective`（纠正措施）| `preventive`（预防措施）
- `priority` 枚举：`P0` | `P1` | `P2`
- `approval_status` 仅可由人工 reviewer 改变
- `approval_ref` 仅在 `approval_status=approved` 时必填

### §2.2 Approved Improvement Input 模板

详见 `skills/improvement-tracker/templates/approved-input.yaml`。

必填字段：`input_id`、`source_ra`、`proposal_id`、`kind`、`title`、`target_agent`、`scope`、`acceptance_criteria`、`priority`、`constraints`、`approval_ref`。

约束：
- `input_id` 全局唯一，不可变，格式 `INPUT-{timestamp}-{seq}`
- 必须在关联 `proposal_id` 的 `approval_status=approved` 时才能生成
- 生成后所有字段不可变（`immutable: true`）
- `target_agent` 枚举：`ptm-tde` | `ptm-te` | `ptm-tae` | `ptm-qa`
- `consumer_status` 默认值：`pending-consumer`

---

## §3 CA/PA 治理（本 Story 实现）

### §3.1 CA/PA 草案生成

#### 输入

- `ra_report_id`：已确认的 RA Report ID
- `analysis_run_id`：关联的分析运行 ID

#### 执行步骤

1. **前置校验**：读取 RA Report，检查 `analysis_status == "analysis-confirmed"`
   - 不满足 → 拒绝，输出："分析结论未确认，请先由 reviewer 确认 RA Report"
2. **必填字段检查**：确认 RA Report 包含 root_cause_analysis、escape_analysis、improvement_dimensions
   - 缺失 → 拒绝，输出缺失字段列表
3. **草案构造**：从分析结论中提取改进维度，填充提案字段：
   - `proposal_id`：按 `PROPOSAL-{timestamp}-{seq}` 生成
   - `analysis_ref.ra_report_id`：引用 RA Report ID
   - `analysis_ref.analysis_run_id`：引用 analysis_run ID
   - `kind`：根据改进维度判定 `corrective` 或 `preventive`
   - `title`：简洁描述改进目标
   - `basis`：引用分析结论中的具体发现
   - `target`：量化改进目标
   - `owner`：单一负责人标识
   - `due_date`：建议完成日期
   - `priority`：P0/P1/P2
   - `validation_method`：如何验证措施有效
   - `side_effects`：潜在副作用和风险
   - `approval_status`：初始化为 `draft`
   - `created_at`：当前时间戳
   - `updated_at`：当前时间戳
4. **去重检查**：检查同一 analysis_ref 是否已有关联的 draft/approved proposal
   - 已存在 → 提示已有草案，返回已有 proposal 引用
5. **输出**：写入 `capa-proposal.yaml`（draft 状态）

#### 输出格式

参见 `skills/improvement-tracker/templates/capa-proposal.yaml`。

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 未确认 RA | `analysis_status != "analysis-confirmed"` | 拒绝生成 | "分析结论未确认，请先由 reviewer 确认 RA Report" |
| 缺少必填字段 | basis/target/owner 等为空 | 拒绝生成 | 提示缺失字段列表 |
| 重复 proposal | 同一 analysis_ref 已有关联 proposal | 提示已有草案 | 返回已有 proposal 引用 |

---

### §3.2 批准状态机

#### 状态定义

```
                 ┌─── reviewer approve ───► approved ───► [可生成 Approved Input]
                 │
draft ──────────┤
                 │
                 └─── reviewer reject ────► rejected ───► [保留，不生成 Input，不出现在 active 候选]
```

#### 状态迁移规则

| 源状态 | 目标状态 | 触发者 | 条件 | 操作 |
|--------|----------|--------|------|------|
| `draft` | `approved` | 人工 reviewer | reviewer 身份 + 审批意见（comments 可选） | 填充 approval_ref.{reviewer, approved_at, comments} |
| `draft` | `rejected` | 人工 reviewer | reviewer 身份 + 拒绝理由（comments 必填） | 填充 approval_ref.{reviewer, approved_at, comments} |
| `approved` | — | — | 终态，不可回退 | 拒绝任何状态变更请求 |
| `rejected` | — | — | 终态，不可回退 | 拒绝任何状态变更请求 |

#### 强制约束

1. 只有人工 reviewer 能改变 `approval_status`
2. 系统（Skill/AI）不得自动批准或拒绝
3. `approved` 和 `rejected` 是终态，不可回退为 `draft` 或互转
4. 若需修改已批准的 CA/PA，必须创建新 proposal（新 proposal_id）并重新走批准流程
5. 旧 proposal 保留，不出现在 active 候选

#### 执行步骤（review-proposal 模式）

1. **读取提案**：根据 `proposal_id` 读取 CA/PA Proposal
2. **状态校验**：检查当前 `approval_status == "draft"`
   - 非 draft → 拒绝："提案状态非 draft（当前: {status}），无法审查"
3. **审批决定校验**：
   - `approve`：确认 reviewer 身份（非空）
   - `reject`：确认 reviewer 身份（非空）+ 拒绝理由（非空）
4. **执行迁移**：
   - `approve` → `approval_status = "approved"`，填充 `approval_ref.{reviewer, approved_at, comments}`
   - `reject` → `approval_status = "rejected"`，填充 `approval_ref.{reviewer, approved_at, comments}`（comments 必填）
5. **更新 `updated_at`**：当前时间戳
6. **输出**：更新后的 proposal

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 非 draft 状态审查 | `approval_status != "draft"` | 拒绝操作 | "提案状态非 draft（当前: {status}），无法审查" |
| 批准缺少 reviewer | approve 但 reviewer 为空 | 拒绝操作 | "批准操作必须提供 reviewer 标识" |
| 拒绝缺少理由 | reject 但 comments 为空 | 拒绝操作 | "拒绝操作必须提供拒绝理由（comments）" |

---

### §3.3 Approved Improvement Input 生成

#### 输入

- `proposal_id`：已批准的 CA/PA Proposal ID（`approval_status = "approved"`）

#### 前置门控

1. CA/PA Proposal 存在
2. `approval_status == "approved"`
3. `approval_ref.reviewer` 非空
4. `approval_ref.approved_at` 非空

不满足任一条件 → 拒绝生成。

#### 执行步骤（publish-input 模式）

1. **读取批准提案**：根据 `proposal_id` 读取已批准 CA/PA Proposal
2. **门控校验**：确认 `approval_status == "approved"` 且 `approval_ref` 完整
   - 不满足 → 拒绝："CA/PA 未批准，无法生成改进输入"
3. **输入构造**：从已批准 proposal 提取字段：
   - `input_id`：按 `INPUT-{timestamp}-{seq}` 生成
   - `source_ra`：proposal 的 `analysis_ref.ra_report_id`
   - `proposal_id`：关联 proposal ID
   - `kind`：proposal 的 `kind`
   - `title`：proposal 的 `title`
   - `target_agent`：由 proposal 的 `owner` 字段映射或 reviewer 指定
   - `scope`：proposal 的 `target` + `basis` 组合
   - `acceptance_criteria`：proposal 的 `validation_method` 转化
   - `priority`：proposal 的 `priority`
   - `constraints`：proposal 的 `side_effects`
   - `approval_ref`：proposal 的 `approval_ref` 引用
   - `consumer_status`：初始化为 `pending-consumer`（§3.4 进一步判定）
   - `created_at`：当前时间戳
   - `immutable`：固定为 `true`
4. **消费者映射**：执行 §3.4 的 target_agent → consumer_status 判定
5. **不可变标记**：写入 `immutable: true`
6. **输出**：写入 `approved-input.yaml`

#### 输出格式

参见 `skills/improvement-tracker/templates/approved-input.yaml`。

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 未批准生成 | `approval_status != "approved"` | 拒绝生成 | "CA/PA 未批准，无法生成改进输入。当前状态: {status}" |
| 已拒绝生成 | `approval_status == "rejected"` | 拒绝生成 | "CA/PA 已被拒绝，无法生成改进输入" |
| approval_ref 不完整 | reviewer 或 approved_at 为空 | 拒绝生成 | "批准引用不完整，无法生成改进输入" |

---

### §3.4 消费者映射

#### 映射逻辑

将 `target_agent` 字段映射为 `consumer_status`：

```text
target_agent 映射表:
  "ptm-tde" → consumer_status = "pending-consumer"
  "ptm-te"  → consumer_status = "pending-consumer"
  "ptm-tae" → consumer_status = "pending-consumer"
  "ptm-qa"  → consumer_status = "pending-consumer"
  其他      → consumer_status = "blocked"（原因: "未识别的消费者 Agent: {value}"）
```

#### 设计约束

- 首版不检查下游 Agent 是否真正就绪（无运行时能力检测）
- `blocked` 仅因 target_agent 不在合法枚举值中触发
- 下游就绪检测是未来的运行时增强（需独立 runtime CR）
- `consumer_status` 后续由 ST-RA-04 的闭环跟踪更新（pending-consumer → consumed/superseded）

#### 下游消费约束

| 约束 | 说明 |
|------|------|
| 只读消费 | 下游 Agent 不得修改 Approved Input 内容 |
| 状态感知 | 下游只能消费 `consumer_status != blocked` 的 Input |
| 回写路径 | 下游处理完成后可回写 `consumer_status: consumed`（通过 improvement-tracker 更新），但不修改 Input 内容 |
| 无自动分发 | 本 Skill 不调用下游 Skill 工具，不创建下游任务 |

---

## §4 闭环跟踪与有效性决策（本 Story 实现）

### §4.1 行动项管理

#### 概述

基于已批准的 CA/PA Proposal（§3 产出），创建结构化行动项（Action Item），管理执行状态、实施证据和过期检测。行动项是闭环跟踪的最小可追踪单元。

**模板文件**：`skills/improvement-tracker/templates/action-item.yaml`

#### 执行步骤

1. **读取已批准提案**：根据 `proposal_id` 读取 `approval_status="approved"` 的 CA/PA Proposal
2. **读取 Approved Input**：根据 `proposal_id` 读取对应的 Approved Improvement Input
3. **创建行动项**：基于提案内容生成 Action Item：
   - `action_id`：按 `ACTION-{proposal_id}-{seq}` 生成
   - `proposal_ref`：关联 Proposal ID
   - `input_ref`：关联 Approved Input ID
   - `owner`：取自 Proposal 的 `owner` 字段
   - `due_date`：取自 Proposal 的 `due_date` 字段
   - `status`：初始化为 `not-started`
   - `description`：基于 Proposal 的 `basis` 和 `target` 构造具体行动描述
   - `blockers`：初始化为 `[]`
4. **状态管理**：Owner/Reviewer 可手动更新状态（见状态机规则）
5. **过期检测**：系统在每次查询时动态计算 overdue 状态

#### 行动项状态机

```
not-started ──(手动标记开始)──► in-progress ──(手动标记完成)──► done
     │                               │
     │   ┌──(now > due_date)─────────┘
     │   ▼
     └─ overdue ◄──(now > due_date)── in-progress

                               overdue ──(手动标记完成)──► done
```

**状态迁移规则：**

| 源状态 | 目标状态 | 触发者 | 条件 |
|---|---|---|---|
| `not-started` | `in-progress` | Owner/Reviewer | 手动标记开始 |
| `in-progress` | `done` | Owner/Reviewer | 手动标记完成 |
| `not-started` | `overdue` | 系统自动 | `now > due_date`（动态计算，不持久化） |
| `in-progress` | `overdue` | 系统自动 | `now > due_date`（动态计算，不持久化） |
| `overdue` | `done` | Owner/Reviewer | 手动标记完成 |

**禁止迁移：**
- `done` → 任何状态（`done` 是终态，不可逆行）
- `overdue` → `not-started` / `in-progress`（只能转向 `done`）
- Skill/AI → `done`（只有 Owner/Reviewer 能标记完成）

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 无已批准提案 | proposal 非 `approved` | 拒绝创建 | "关联的 CA/PA 提案未批准，无法创建行动项" |
| 提案不存在 | `proposal_ref` 指向不存在的 proposal | 拒绝创建 | "关联的 CA/PA 提案不存在" |
| 无效状态迁移 | 尝试 `done` → 其他状态 | 拒绝操作 | "done 是终态，不可回退" |
| Skill 自动完成 | Skill/AI 尝试设置 `status="done"` | 拒绝操作 | "行动项完成需 Owner/Reviewer 手动标记" |

---

### §4.2 有效性检查

#### 概述

在行动项全部完成后评估改进措施的实际有效性。包含观察窗口管理、复发统计查询和人工 reviewer 的结果判定。

**模板文件**：`skills/improvement-tracker/templates/effectiveness-check.yaml`

#### 执行步骤

1. **前置检查**：确认所有关联 Action Items 的 `status="done"`
   - 不满足 → 提示 "存在未完成的行动项，建议完成后再创建有效性检查"
   - 不强制阻断（允许在行动项全部 done 前预创建，但 result 保持 `planned`）
2. **创建检查**：为每个 Action Item 或提案创建 Effectiveness Check：
   - `check_id`：按 `EFF-CHECK-{action_id}-{seq}` 生成
   - `action_ref`：关联 Action Item ID
   - `method`：取自 CA/PA Proposal 的 `validation_method` 字段，由 reviewer 确认或调整
   - `window_days`：默认 30，可由 reviewer 根据业务场景调整
   - `result`：初始化为 `planned`
3. **等待观察窗**：观察窗从 `checked_at` 开始计时，满足条件：经过天数 ≥ `window_days`
   - reviewer 可在 `notes` 中声明观察窗豁免（如观察期已过但未记录起始时间）
   - 豁免需注明原因，记录在 `notes` 中
4. **收集复发数据**：从 SQLite `measure_link` 表只读查询复发统计：
   - `same_category_count`：同一 `proposal_ref` 的问题单数
   - `total_observation_count`：观察窗内总问题单数
   - `recurrence_rate`：`same_category_count / total_observation_count`（total>0 时）
   - `total_observation_count = 0` 时，不填 `recurrence_measure`
5. **reviewer 评估**：人工 reviewer 填写 `result`、`checked_by`、`checked_at` 和 `notes`
   - `passed`：有效性确认通过
   - `failed`：有效性不通过
   - `inconclusive`：证据不足以判断

#### 有效性 result 判定规则

| 结果 | 含义 | 对关闭条件 2 影响 | 后续动作 |
|---|---|---|---|
| `planned` | 等待评估 | 阻断关闭 | 等待观察窗满足或 reviewer 评估 |
| `passed` | 有效性通过 | 满足条件 2 | 可进入关闭决策 |
| `failed` | 有效性不通过 | 阻断关闭 | 需分析原因、调整措施或重走改进流程 |
| `inconclusive` | 证据不足 | 阻断关闭 | 需补充数据后重新评估 |

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 无关联行动项 | `action_ref` 指向不存在的 Action Item | 拒绝创建 | "关联的行动项不存在" |
| Skill 自动判定 | Skill/AI 尝试设置 `result` | 拒绝操作 | "有效性结果需人工 reviewer 评估" |
| 复发查询失败 | SQLite `measure_link` 不可读 | 降级处理 | `recurrence_measure` 留空，提示 "复发数据暂不可用" |

---

### §4.3 观察窗逻辑

#### 观察窗定义

观察窗是改进措施生效后的观察期，用于判断措施是否真正有效。核心参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `window_days` | 30 | 观察窗口天数，可由 reviewer 调整 |
| 起始点 | `checked_at` | 从 reviewer 填写检查结果时开始计时 |
| 满足条件 | `now - checked_at >= window_days` | 经过天数达到或超过窗口天数 |

#### 观察窗豁免

当业务场景中存在以下情况时，reviewer 可声明观察窗豁免：

- 观察期已过，但未记录起始时间（如改进措施已实施数月后才开始跟踪）
- 业务特性要求更短的观察周期（如紧急修复措施）
- 外部约束导致无法等待完整观察期（如项目节点限制）

豁免规则：
1. reviewer 在 Effectiveness Check 的 `notes` 中声明豁免原因
2. 豁免后对应的 `observation_window_satisfied` 在关闭决策中可手动设为 `true`
3. 豁免不影响其他三个关闭条件的评估
4. 豁免记录保留在 `notes` 中作为审计证据

---

### §4.4 关闭决策

#### 概述

在行动项完成、有效性检查和观察窗满足后，由人工 reviewer 执行关闭决策。关闭基于有效性而非完成率：**所有条件同时满足才可关闭，任一不足则保持开放**。

**模板文件**：`skills/improvement-tracker/templates/closure-decision.yaml`

#### 关闭四条件

| 条件 | 字段 | 判定逻辑 | 数据来源 |
|---|---|---|---|
| 条件 1 | `all_actions_complete` | 所有关联 Action Items 的 `status="done"` | Action Items |
| 条件 2 | `effectiveness_passed` | 所有关联 Effectiveness Checks 的 `result="passed"` | Effectiveness Checks |
| 条件 3 | `observation_window_satisfied` | 所有 Effectiveness Checks 的观察窗满足（或 reviewer 已豁免） | Effectiveness Checks |
| 条件 4 | `no_same_category_recurrence` | 所有 Effectiveness Checks 的 `recurrence_rate == 0` | Effectiveness Checks |

#### 执行步骤

1. **收集数据**：从 Action Items 和 Effectiveness Checks 汇总四个条件的评估结果
2. **条件评估**：逐项检查四个条件是否满足
3. **输出决策**：
   - 四条件全部 `true` → `decision="closed"`（`residual_risks` 和 `follow_up_actions` 可为 N/A）
   - 任一条件 `false` → `decision="open"`（`residual_risks` 和 `follow_up_actions` 必填）
4. **reviewer 签名**：人工 reviewer 填写 `reviewer` 和 `decided_at`
5. **输出**：写入 `closure-decision.yaml`

#### 四条件硬断言

以下规则硬编码，不可由 Skill/AI 覆盖：

```text
if decision == "closed":
    assert conditions.all_actions_complete == True
    assert conditions.effectiveness_passed == True
    assert conditions.observation_window_satisfied == True
    assert conditions.no_same_category_recurrence == True

if decision == "open":
    assert len(residual_risks) > 0 or len(follow_up_actions) > 0
```

违反规则时拒绝写入，返回具体不满足的条件和修复建议。

#### 关闭条件不可绕过示例

| 场景 | 条件 1 | 条件 2 | 条件 3 | 条件 4 | 决策 |
|---|---|---|---|---|---|
| 全部满足（理想情况） | true | true | true | true | **closed** |
| 全部 done 但有效性 failed | true | **false** | true | true | **open** |
| 全部 done 但有同类复发 | true | true | true | **false** | **open** |
| 观察窗不足 | true | false (planned) | **false** | true | **open** |
| 有未完成行动项 | **false** | true | true | true | **open** |

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| 无关联提案 | `proposal_id` 不存在 | 拒绝操作 | "关联的 CA/PA Proposal 不存在" |
| 自动关闭尝试 | Skill/AI 试图设置 `decision="closed"` | 拒绝写入 | "关闭决定需人工 reviewer 确认，拒绝自动关闭" |
| 条件断言失败 | decision="closed" 但条件不满足 | 拒绝写入 | 返回不满足的条件列表 + 修复建议 |
| open 但无 follow_up | decision="open" 但 residual_risks 和 follow_up_actions 均为空 | 拒绝写入 | "保持开放时必须提供剩余风险和后续行动" |

#### 消费者映射更新

关闭决策完成后，应更新对应 Approved Improvement Input 的 `consumer_status`：
- `decision="closed"` → `consumer_status = "consumed"`
- `decision="open"` → `consumer_status` 保持当前值（`pending-consumer` 或后续状态）

此更新通过 improvement-tracker Skill 的回写路径执行，不修改 Input 的其他内容。

---

## §5 措施基线管理与刷新提示（本 Story 实现）

### §5.1 MeasureBaseline 概念

MeasureBaseline 是 HLD REV-03 七项可信治理契约之一，记录已批准 CA/PA 提案在执行后的措施基线，包含版本、范围、审批证据、实施证据、有效性证据和观察窗等关键信息。

**核心原则**：
- **无基线 = needs-baseline**：如果关联的 proposal 尚无基线，只标记 `needs-baseline`，不判定措施失效
- **reviewer 是唯一状态变更者**：系统只产出 `proposed_status` 和 `refresh_hint` 提示字段，不自动修改正式 `status`
- **不自动创建基线**：基线创建需 reviewer 确认后执行
- **不判失效**：系统不主动将措施状态标记为失效；即使检测到同类复发，也只输出提示供 reviewer 决策

**模板文件**：`skills/improvement-tracker/templates/measure-baseline.yaml`

### §5.2 基线创建

#### 前置条件

基线只能由人工 reviewer 在以下条件下创建：

1. 关联的 CA/PA Proposal `approval_status = "approved"`（来源：§3.2）
2. 关联的 Approved Improvement Input 已生成（来源：§3.3）
3. 系统已输出 `proposed_status = "needs-baseline"` 提示（来源：S2 变更检测渠道）

#### 执行步骤（reviewer 操作）

1. **读取提示**：系统在 S2 变更检测时，对尚无基线的已批准 proposal 置 `proposed_status = "needs-baseline"`、`refresh_hint = "需先建立措施基线"`
2. **创建基线**：reviewer 确认后调用 `insert_measure_link()` 创建 MeasureBaseline：
   - `baseline_id`：按 `BASELINE-{proposal_id}-{version}` 生成
   - `proposal_ref`：关联的 Proposal ID
   - `version`：首次为 1
   - `scope`：措施适用范围，取自 proposal 的 `target` + `basis`
   - `approval_ref`：proposal 的 `approval_ref` 引用
   - `implementation_evidence`：实施证据引用
   - `effectiveness_evidence`：有效性证据引用
   - `observation_window_start` / `observation_window_end`：观察窗起止日期
   - `status`：创建时设置为 `active`
3. **更新状态**：reviewer 调用 `reviewer_update_measure_status()` 将正式 `status` 变更为 `active`，同时清除 `proposed_status`

#### 失败处理

| 失败场景 | 触发条件 | 行为 | 输出 |
|----------|----------|------|------|
| proposal 不存在 | `proposal_ref` 指向不存在的 proposal | 拒绝创建 | "关联的 CA/PA Proposal 不存在" |
| proposal 未批准 | `proposal_ref` 指向的 proposal `approval_status != "approved"` | 拒绝创建 | "关联的 CA/PA Proposal 未批准，无法创建基线" |
| 基线已存在 | 同一 `proposal_ref` 已有基线 | 拒绝创建 | "该 proposal 已有基线 version={n}，如需更新请创建新版本" |
| 系统尝试自动创建 | Skill/AI 直接调用 `insert_measure_link()` 并设置 `status=active` | 拒绝操作 | "基线创建需人工 reviewer 确认" |

### §5.3 刷新提示规则

系统在以下事件发生时产出 `proposed_status` 和 `refresh_hint`。**系统只能调用 `update_measure_refresh_hint()` 写入提示字段，正式 `status` 仅可由 reviewer 调用 `reviewer_update_measure_status()` 变更。**

#### 触发规则

| 触发条件 | proposed_status | refresh_hint | 触发来源 | 说明 |
|---|---|---|---|---|
| 关联 proposal 无 MeasureBaseline | `needs-baseline` | "需先建立措施基线" | S2 变更检测首次关联 | 基线缺失，reviewer 需创建基线 |
| S2 检测到新相关问题单 | `needs-review` | "新问题可能影响措施有效性" | ST-RA-06.2-REFRESH 差异报告 | 提示 reviewer 重新核查措施范围 |
| 关联 Action Items 全部 done | `completed` | "可进入观察期" | ST-RA-04 闭环跟踪事件 | 提示 reviewer 确认进入有效性观察 |
| 观察窗通过 + 无复发 | `active` | "观察窗已满足，措施持续有效" | ST-RA-04 关闭决策事件 | 提示 reviewer 确认措施保持有效 |
| S2 检测到同类问题复发 | `needs-review` | "同类复发，措施可能失效" | ST-RA-06.2-REFRESH 差异报告 | 提示 reviewer 重新评估措施有效性 |
| 措施被新的 CA/PA 取代 | `superseded` | "被新 proposal {new_proposal_id} 取代" | S2 增量重算 | 提示 reviewer 确认取代关系 |

#### 系统写入约束

调用 `update_measure_refresh_hint(proposal_ref, updates)` 时必须遵守：

1. **只能写入提示字段**：`proposed_status`、`refresh_hint`、`refreshed_at`、`refreshed_by`、`refresh_reason`
2. **禁止写入正式字段**：`status`、`approval_ref`、`baseline_id` 不在允许集合中，DAO 层会拒绝并抛出 `ValueError`
3. **proposal_ref 必须存在**：不存在时 DAO 层抛出 `LookupError`
4. **并发刷新**：同时多个事件触发刷新时，最后一次 wins，但所有 `refresh_reason` 记录都应保留

#### 正式状态变更（仅 reviewer）

| 操作 | 调用接口 | 说明 |
|---|---|---|
| needs-baseline → active | `reviewer_update_measure_status(proposal_ref, "active", reviewer_ref)` | reviewer 确认创建基线后变更 |
| active → needs-review | `reviewer_update_measure_status(proposal_ref, "needs-review", reviewer_ref)` | reviewer 确认措施需重新评估 |
| needs-review → active | `reviewer_update_measure_status(proposal_ref, "active", reviewer_ref)` | reviewer 审查后认为措施仍有效 |
| active → completed | `reviewer_update_measure_status(proposal_ref, "completed", reviewer_ref)` | reviewer 确认措施实施完成 |
| → superseded | `reviewer_update_measure_status(proposal_ref, "superseded", reviewer_ref)` | reviewer 确认措施被新 proposal 取代 |

### §5.4 reviewer 是唯一状态变更者

#### 权限模型

| 操作 | 触发者 | 权限 |
|---|---|---|
| 检测事件并生成 proposed_status + refresh_hint | 系统 | 自动（仅写入提示字段，不修改正式 status） |
| 创建 MeasureBaseline | 人工 reviewer | 需手动确认（基于系统 proposed_status=needs-baseline 提示） |
| 正式 status 变更 | 人工 reviewer | 需手动确认（基于系统 refresh_hint） |
| 改版 scope/approval_ref | 人工 reviewer | 需重新批准（创建新 version 基线） |

#### 调用路径

```
[事件发生] → 系统检测
     │
     ├── 调用 update_measure_refresh_hint()  ← 系统只能调用此接口
     │    写入: proposed_status, refresh_hint, refreshed_at, refreshed_by, refresh_reason
     │    禁止: status, approval_ref, baseline_id
     │
     └── reviewer 看到提示后决策
           │
           └── 调用 reviewer_update_measure_status()  ← 只有 reviewer 可调用
                变更: status = "active" | "needs-review" | "completed" | "superseded"
```

### §5.5 禁止行为

以下行为在任何场景下均被禁止：

1. **禁止系统自动创建 MeasureBaseline**：只能提示 `needs-baseline`，不能直接调用 `insert_measure_link()`
2. **禁止系统自动改变正式 status**：只能调用 `update_measure_refresh_hint()`，不能调用 `reviewer_update_measure_status()`
3. **禁止无基线时判措施失效**：只标记 `needs-baseline`，不将 status 设为失效或 supplanted
4. **禁止通过 update_measure_refresh_hint 修改正式字段**：DAO 层的 `forbidden` 集合（`status`, `approval_ref`, `baseline_id`）会硬性拒绝
5. **禁止自动修改下游任务**：刷新提示不触发下游任务变更
6. **禁止修改 Approved Improvement Input**：Approved Input 的 `immutable: true` 属性不变
7. **禁止绕过运行数据治理预检或修复既有文件**：`RuntimeDataGovernanceReport` 非 `compliant` 时拒绝输出；本 Skill 不执行 chmod、删除、迁移、导出或保留清理

---

## Gotchas

1. **不要把 CA/PA 草案直接交给下游**：必须经过批准门。任何 `approval_status != "approved"` 的 proposal 都不能生成 Approved Input。
2. **不要自动批准**：只有人工 reviewer 能改变 `approval_status`。Skill 内部的任何逻辑不得自动将 `approval_status` 设为 `approved`。
3. **不要把 Approved Input 当作下游任务**：Approved Input 是改进输入的不可变描述，下游 Agent 自行决定如何处理和调度。
4. **不要让拒绝的 proposal 消失**：`rejected` 状态的 proposal 必须保留，作为审计记录。不接受删除操作。
5. **不要假设消费者立即可用**：`consumer_status` 的首版映射不检测下游就绪状态。下游可能尚未安装或不可用，这不影响 Approved Input 的生成。
6. **不要在 SKILL.md 之外定义章节**：ST-RA-03、ST-RA-04、ST-RA-06.3-TRACK 写入独立章节（§3/§4/§5），各 Story 不得跨章节修改，确保串行写入安全。
7. **不要修改 Approved Input**：Approved Input 生成后 `immutable: true`，任何修改请求必须拒绝。如需更新，reviewer 应创建新 proposal → 批准 → 生成新 Approved Input。
8. **不要混淆 CA 和 PA**：Corrective Action（纠正措施）针对已发生问题的消除原因；Preventive Action（预防措施）针对潜在问题的预防。生成草案时必须明确区分，`kind` 字段是强校验枚举值。
9. **不要在缺失分析结论时推测**：CA/PA 草案的 `basis` 字段必须引用分析结论中的具体发现，不得在分析结论缺失时推测或填充通用描述。
10. **不要绕过 proposal_id 唯一性**：`PROPOSAL-{timestamp}-{seq}` 格式，同一 analysis_ref 不可生成重复 proposal_id；去重逻辑必须在 §3.1 执行。
11. **不要按完成率关闭**：关闭决策基于四条件硬断言，不是行动项完成率。全部 done 但有效性 failed → 保持 open。此规则是 LLD 中的核心安全约束，不可绕过。
12. **不要把 overdue 当做 done**：overdue 仅表示行动项超期，不代表完成。overdue 状态下的行动项仍会导致 `all_actions_complete != true`，必须由 Owner/Reviewer 手动标为 done 后才能计入完成。
13. **不要让 done 状态回退**：done 是终态，不可回退到 not-started、in-progress 或 overdue。任何试图回退 done 的请求都必须拒绝。若需重新执行，应创建新 Action Item。
14. **不要把观察窗豁免默认为 true**：观察窗豁免必须由 reviewer 显式在 Effectiveness Check 的 notes 中声明原因。不可因观察窗不足而自动设置 observer_window_satisfied=true。
15. **不要让 Skill/AI 执行有效性判定**：result、checked_by、checked_at 字段仅可由人工 reviewer 填写。Skill/AI 可汇总数据、计算复发率，但不可设置最终 result。
16. **不要混淆 action_id 和 check_id 的作用域**：一个提案可有多个 Action Items，每个 Action Item 可有多个 Effectiveness Checks。关闭决策汇总本提案下所有 Action Items 和 Checks，而非仅看单个对象。
17. **不要把 recurrence_measure 缺失误读为零复发**：total_observation_count = 0 表示观察窗内无问题单，不设置 recurrence_measure。这与 recurrence_rate = 0 的含义不同；在关闭决策中，无观察数据无法满足条件 4（no_same_category_recurrence），应保持 open。
18. **不要把 proposed_status 当作正式 status**：`proposed_status` 是系统提示，`status` 是正式状态。下游消费和门控判断以 `status` 为准，`proposed_status` 仅供 reviewer 参考。任何时候系统都不得通过 `update_measure_refresh_hint()` 修改 `status` 字段。
19. **不要把 needs-baseline 当作措施失效**：无基线只表示尚未建立 MeasureBaseline，不表示 CA/PA 措施已失效。reviewer 看到 `needs-baseline` 提示后，确认即可创建基线并将 status 改为 `active`；不存在"措施因无基线而自动失效"的状态路径。
20. **不要自动创建基线**：即使检测到 proposal 已批准，系统也不能自动调用 `insert_measure_link()`。基线创建操作必须由 reviewer 通过改善跟踪界面或 Skill 的 reviewer 操作路径显式执行。
21. **不要把 refresh_hint 当作操作指令**：`refresh_hint` 是人类可读的提示文本，不是结构化操作指令。下游系统不得解析 `refresh_hint` 文本来自动触发状态变更、任务创建或其他副作用。
22. **不要让 superseded 状态的基线消失**：被取代的基线必须保留 `status="superseded"` 记录，作为审计证据。不接受删除 MeasureBaseline 的操作。新基线通过新 `baseline_id`（新 version）创建，旧基线标记 superseded 保留。
23. **不要把提案输出写入 Skill 安装目录**：`skills/improvement-tracker/outputs/` 不是运行数据目录。含问题单材料的输出必须进入已合规的 `<runtime-root>/data/improvement/`，并使用受限权限。

---

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-07-16 | meta-dev (ST-RA-03) | 初始版本：§1 输入契约、§2 数据模型、§3 CA/PA 治理（草案生成、批准状态机、Approved Input 生成、消费者映射）、§4-§5 占位符、Gotchas |
| 1.1 | 2026-07-16 | meta-dev (ST-RA-04) | §4 闭环跟踪与有效性决策（行动项状态机、有效性检查、观察窗逻辑、关闭决策四条件硬断言）；新增模板 action-item/effectiveness-check/closure-decision.yaml；新增 Gotchas #11-#17 |
| 1.2 | 2026-07-16 | meta-dev (ST-RA-06.3-TRACK) | §5 措施基线管理与刷新提示（MeasureBaseline 概念、基线创建、刷新提示规则、reviewer 唯一状态变更者、禁止行为）；新增模板 measure-baseline.yaml；新增 Gotchas #18-#22 |
| 1.3 | 2026-07-17 | host-orchestrator | CR-031：增加安装项目运行根、治理预检、受限输出位置和不实施本地数据修复的契约。 |
