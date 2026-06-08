---
change_id: CR-010-ptm-tde三阶段框架改造
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-01T12:00:00+08:00"
created_by: meta-po
status: closed
closed_at: "2026-06-01T17:00:00+08:00"
approved_at: "2026-06-01T15:30:00+08:00"
approved_by: user
approved_decisions:
  - CR-DQ-01: 方案A (Gate主编号+CP兼容别名)
  - CR-DQ-02: 取消 (不适用)
  - CR-DQ-03: 方案A (MFQ内部为主+上下游Warning)
  - CR-DQ-04: 方案A (MFQ写入,PPDCS读取+验证)
  - CR-DQ-05: 方案A (保留共享工具Skill,各阶段调用)
impact_level: high
rollback_to: story-execution
approval_source: user-request
depends_on: n/a
followed_by:
  - CR-011-ptm-tde-kym-phase (KYM 阶段改造)
  - CR-012-ptm-tde-mfq-phase (MFQ 阶段改造)
  - CR-013-ptm-tde-ppdcs-phase (PPDCS 阶段改造)
---

# CR-010 — ptm-tde 三阶段框架改造（结构层）

## 变更请求摘要

将 ptm-tde 工作流从当前的 11 步状态机 + 12 个检查点（CP01-CP12）重构为**三阶段框架 + 入口/出口门控**体系。本 CR 只做结构层改造（主 Agent 框架重写、Gate 体系定义、目录创建、checkpoint spec 替换、checkpoint-manager 适配、全部文档更新），**不修改任何 Skill SKILL.md 文件**——Skill 路径迁移和内容改造由 CR-011/012/013 分别承接。

## 背景

### 当前结构

```
1.input(CP01) → 2.scenario(CP02) → 3.M(CP03) → 4.F(CP04) → 5.Q(CP05)
→ 6.integration(CP06) → 7.plan(CP07) → 8.design-ppdcs(CP08/CP09)
→ 9.design-pc(CP10) → 10.coverage(CP11) → 11.delivery(CP12)

目录：analysis/(feature-input|scenarios|m-analysis|f-analysis|q-analysis|integration|plan|factor-usage|coverage)
     design/(ppdcs|pc)  delivery/  checkpoints/  doc/STATE.yaml
```

### 目标结构

```
Entry Gate（纯自检）← 原 CP01
KYM Phase: [kym Skill →] feature-parser → scenario-discovery
  → KYM Exit Gate（自检+人工）← 原 CP02
MFQ Phase: m-analyzer → f-analyzer → q-analyzer → test-point-integrator → design-planner
  → MFQ Exit Gate（自检+人工，新增人工门）
PPDCS Phase: design-ppdcs-analyzer + 5设计Skill → PC → coverage-verifier → deliverable-renderer
  → PPDCS Exit Gate（自检+人工）← 原 CP09+CP11
Exit Gate（纯自检）← 原 CP12
```

### 目录结构迁移

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

### 检查点→门控映射

| 原检查点 | 新门控 | 类型 |
|----------|--------|------|
| CP01 | **Entry Gate** | 纯自检 |
| CP02 | **KYM Exit Gate** | 自检+人工 |
| CP03-CP07 | **MFQ 阶段内滚动自检** | 纯自检 |
| — | **MFQ Exit Gate** | 自检+人工（新增） |
| CP08-CP10 | **PPDCS 阶段内滚动自检** | 纯自检 |
| CP09+CP11 | **PPDCS Exit Gate** | 自检+人工 |
| CP12 | **Exit Gate** | 纯自检 |

## 用户已确认决策（CR 发起前）

| 决策项 | 结论 |
|--------|------|
| 门控粒度 | 方案 B：阶段内滚动自检 + 阶段出口正式门控 |
| MFQ 出口门控 | 自检+人工（新增人工确认点） |
| plan/ 目录位置 | `process/plan/`（跨阶段边界产物） |
| 目录结构 | 改为阶段级目录（kym/、mfq/、ppdcs/） |

## 五维度影响分析

| 维度 | 影响 |
|------|------|
| 需求 | 新增三阶段框架需求 + MFQ Exit Gate 需求 |
| 设计 | 主 Agent 重写 + Gate 体系替代 CP 体系 + 目录结构迁移 |
| 实现 | 分 4 条 CR 串行实施，本 CR 只做框架层 |
| 安全 | 无影响 |
| 交付 | 文档体系需更新，安装器不变 |

## 受影响文件（本 CR 直接修改）

### 核心文件

| 文件 | 变更类型 |
|------|----------|
| `agents/ptm-tde.md` | 框架重写（状态机→三阶段、门控定义、目录结构、Skill 触发表、初始化流程、路径规则） |
| `docs/ptm-tde/checkpoint-spec.md` | 归档为 `checkpoint-spec-v1-archived.md` |
| `docs/ptm-tde/gate-spec.md` | 新建（5 Gate 的 Entry Criteria / Checklist / Exit Criteria / Deliverables） |
| `skills/checkpoint-manager/SKILL.md` | 新增 Gate 模式 + CP↔Gate 映射表 |
| `skills/checkpoint-manager/scripts/run_checkpoint.py` | 新增 `--gate` 参数 + Gate 模式 |

### 文档文件

| 文件 | 变更要点 |
|------|----------|
| `docs/ptm-tde/README.md` | "11步"→"3阶段"，目录结构，检查点描述 |
| `docs/ptm-tde/USER-MANUAL.md` | 工作流路径，运行时目录规则 |
| `docs/ptm-tde/runtime-artifacts.md` | 产物目录结构替换 |
| `docs/ptm-tde/component-manual.md` | 主流程表替换 |
| `docs/ptm-tde/skill-references.md` | Skill 阶段归属更新 |
| `skills/README.md` | "11步"→"3阶段" |
| `agents/README.md` | Agent 说明更新 |
| `process/REQUIREMENTS-ptm-tde.md` | 新增 REQ-030（三阶段框架）+ REQ-031（MFQ Exit Gate） |

### 本 CR 不修改

18 个 Skill SKILL.md 文件——由 CR-011（KYM）/ CR-012（MFQ）/ CR-013（PPDCS）分别承接。

## 实施步骤

1. 归档 `docs/ptm-tde/checkpoint-spec.md` → `checkpoint-spec-v1-archived.md`
2. 新建 `docs/ptm-tde/gate-spec.md`（5 Gate 完整规范）
3. 重写 `agents/ptm-tde.md` 框架部分
4. 更新 `skills/checkpoint-manager/SKILL.md`（Gate 识别 + 路由）
5. 更新 `skills/checkpoint-manager/scripts/run_checkpoint.py`（`--gate` 模式）
6. 更新全部 `docs/ptm-tde/` 文档
7. 更新 `skills/README.md`、`agents/README.md`
8. 更新 `process/REQUIREMENTS-ptm-tde.md`
9. 验证：grep 确认框架文件引用新路径

## 验证方法

1. `grep -rn "11 步\|11步\|CP01\|CP02\|CP03\|CP04\|CP05\|CP06\|CP07\|CP08\|CP09\|CP10\|CP11\|CP12" agents/ptm-tde.md docs/ptm-tde/` — 框架文件中不再出现旧编号
2. `docs/ptm-tde/gate-spec.md` 存在且包含 5 个 Gate 完整规范
3. `skills/checkpoint-manager/SKILL.md` 包含 CP↔Gate 映射表
4. `process/REQUIREMENTS-ptm-tde.md` 包含 REQ-030 和 REQ-031

---

## 待人工决策清单

### CR-DQ-01：门控文件命名与编号体系

| 字段 | 内容 |
|---|---|
| **决策 ID** | CR-DQ-01 |
| **决策类型** | `architecture` |
| **待确认问题** | 5 个 Gate 的门控文件如何命名？是否保留 CP 编号映射？ |
| **推荐方案** | **Gate 主编号 + CP 兼容别名**：`GATE-1-Entry`、`GATE-2-KYM-Exit`、`GATE-3-MFQ-Exit`、`GATE-4-PPDCS-Exit`、`GATE-5-Exit`，同时维护 CP↔Gate 映射表，允许 `--cp CP02` 自动路由到 `--gate KYM-Exit` |
| **推荐理由** | 体系简洁（5 Gate vs 12 CP），兼容别名保护旧引用 |
| **备选方案 1** | 纯 CP 编号，阶段内嵌套（"阶段一 KYM：CP01-CP02"）。优势：零迁移风险。代价：MFQ Exit Gate 无合适 CP 编号 |
| **备选方案 2** | 纯 Gate 编号，不保留 CP 映射。优势：最干净。代价：破坏所有旧引用 |
| **影响与风险** | 影响门控文件命名、checkpoint-manager 路由、主 Agent 门控引用 |
| **回退条件** | 若映射表维护成本过高，可在后续 CR 中将 CP 兼容标记 deprecated |

### CR-DQ-02：现有 analysis/ 和 design/ 目录处理

| 字段 | 内容 |
|---|---|
| **决策 ID** | CR-DQ-02 |
| **决策类型** | `implementation` |
| **待确认问题** | 新阶段目录创建后，旧 `analysis/` 和 `design/` 如何处理？ |
| **推荐方案** | **并行共存 + 文档标记废弃**：本 CR 不删除旧目录，Skill 文件不做路径迁移（由 CR-011/012/013 负责）。旧目录加入 `README-DEPRECATED.md`。CR-013 完成后统一删除 |
| **推荐理由** | 每个 CR 独立可验证，不会出现"目录已删除但 Skill 还没改"的空窗期 |
| **备选方案 1** | 本 CR 即删除旧目录。优势：一步到位。代价：CR-011/012/013 完成前工作流不可用 |
| **备选方案 2** | 不创建新目录，只在主 Agent 中声明逻辑映射。优势：零文件系统变动。代价：目录结构与概念模型不一致 |
| **影响与风险** | 影响目录结构、Skill 运行时路径解析 |
| **回退条件** | 若新路径与 Skill 隐性假设冲突，回退到逻辑映射方案 |

### CR-DQ-03：MFQ Exit Gate 检查内容范围

| 字段 | 内容 |
|---|---|
| **决策 ID** | CR-DQ-03 |
| **决策类型** | `scope` |
| **待确认问题** | MFQ Exit Gate 只检查 MFQ 内部完整性，还是包含上下游衔接？ |
| **推荐方案** | **MFQ 内部完整性为主 + 上下游衔接作为 Warning**：核心检查 M/F/Q 输出完整性和 LC/plan 契约一致性；上下游衔接作为非阻断 Warning 提示但不阻断 |
| **推荐理由** | 聚焦 MFQ 质量，给用户上下游可见性但不强制阻断；Warning 可在 PPDCS Exit Gate 二次检查 |
| **备选方案 1** | 仅 MFQ 内部完整性。优势：Gate 职责单一。代价：缺口可能在 PPDCS 阶段才暴露 |
| **备选方案 2** | 全量 + 上下游强制检查。优势：端到端可追溯。代价：范围过大，可能 Gate 间死锁 |
| **影响与风险** | 影响 MFQ Exit Gate checklist 定义和用户确认体验 |
| **回退条件** | 若上下游缺口频繁导致返工，可将 Warning 升级为阻断项 |

### CR-DQ-04：process/plan/ 跨阶段消费契约

| 字段 | 内容 |
|---|---|
| **决策 ID** | CR-DQ-04 |
| **决策类型** | `architecture` |
| **待确认问题** | `process/plan/` 的写入和读取职责如何划分？ |
| **推荐方案** | **MFQ 写入（design-planner），PPDCS 读取+验证**：MFQ Exit Gate 检查 plan 存在性和格式，PPDCS 启动时读取，PPDCS Exit Gate 检查消费完整性 |
| **推荐理由** | 一个 Writer（design-planner），两个阶段各负责自己的 Gate 检查 |
| **备选方案 1** | 两阶段共同维护。优势：灵活。代价：缺乏单一 owner 可能冲突 |
| **备选方案 2** | 放入 ppdcs/plan/。优势：归属单一。代价：design-planner 在 MFQ 执行却写 PPDCS 目录 |
| **影响与风险** | 影响 design-planner 输出路径、MFQ/PPDCS Exit Gate 检查内容 |
| **回退条件** | 若频繁返工可增加 plan-review Gate 或采用共同维护模式 |

### CR-DQ-05：checkpoint-manager 改造策略

| 字段 | 内容 |
|---|---|
| **决策 ID** | CR-DQ-05 |
| **决策类型** | `implementation` |
| **待确认问题** | checkpoint-manager 完全替换为 Gate 还是增加双模式？ |
| **推荐方案** | **双模式并存**：新增 `gate` 模式与 `checkpoint` 模式平行。ptm-tde 检测到 gate-spec 时用 Gate 模式，其他工作流继续用 CP 模式。`run_checkpoint.py` 增加 `--gate` 和 `--mode` 参数 |
| **推荐理由** | 不影响非 ptm-tde 工作流，ptm-tde 无感切换 |
| **备选方案 1** | 完全替换为 Gate。优势：最干净。代价：破坏 Meta Flow CP0-CP8 |
| **备选方案 2** | Gate 作为 checkpoint 子类型。优势：零接口变更。代价：概念层次不清晰 |
| **影响与风险** | 影响 checkpoint-manager 代码结构和维护成本 |
| **回退条件** | 若双模式维护成本过高可统一回 CP 体系 |

---

## Decision Brief

**条件批准**：确认 5 项决策后进入实施。

### 不授权项

`approve` 不代表授权：删除旧目录、修改 18 个 Skill 文件、修改 Meta Flow 通用 CP0-CP8、热切换运行中工作流、修改安装脚本。

---

## 实施记录

| 时间 | 事件 |
|------|------|
| 2026-06-01 | CR 创建，状态 draft |
| 2026-06-01 | [P0-C1] 修正「检查点→门控映射」表：CP03-CP06→CP03-CP07（MFQ 阶段内滚动自检覆盖 CP03 至 CP07，含 design-planner 的 CP07）。 |
