---
checkpoint: CP8-manual
cr_id: CR-015-ptm-tde-ask-user-question-interaction
workflow_mode: fast-lane
created_at: "2026-06-04"
status: approved
---

# CP8-CR-015 — 交付就绪人工终验

> 自动预检结果：`process/checks/CP8-DELIVERY-READINESS-CR-015.md` — **10/10 PASS**

## Decision Brief

### 变更概要

CR-015 在 ptm-tde 的 7 个文件中引入 `AskUserQuestion` 工具，将关键交互点的纯文本标记升级为 Claude Code 原生 TUI 选择器。

- **7 个产品文件**：`agents/ptm-tde.md` + 6 个 Skill SKILL.md
- **约 130 行新增**：纯注解/指令添加，无逻辑变更
- **所有交互点保留 STOP-05 文本回退**：AskUserQuestion 不可用时自动降级

### P0 改造（纯适配，4 个交互点）

| Skill | 交互点 | 改造 |
|-------|--------|------|
| test-point-integrator | 候选汇总确认 | 4 选项 AskUserQuestion 单选 |
| f-analyzer 步骤 5 | 候选耦合点确认 | 3 选项 AskUserQuestion 单选 |
| f-analyzer 步骤 8 | 回写确认 | 2 选项 AskUserQuestion 单选 |
| q-analyzer 步骤 1 | OPEN 项确认 | 4 选项 AskUserQuestion 单选 |

### P1 改造（混合模式，3 个 Skill）

| Skill | 交互点 | 改造 |
|-------|--------|------|
| kym | 阶段一+阶段三+阶段四 | 3 选项 + 选项拆分策略 + Gate 确认映射 |
| design-planner | 步骤 5 设计计划确认 | 3 选项，升级已有 `ask_user` 占位 |
| checkpoint-manager | GATE-2/3/4 人工确认 | AskUserQuestion 优先 + STOP-06 降级规则 |

### 通用规则层

`agents/ptm-tde.md` 新增「用户交互层（AskUserQuestion）」小节：
- 触发决策树（选项 ≤4 / >4 拆分 / 开放式 / 回退）
- 参数约束（header ≤12、label 1-5 词、options ≤4）
- Gate 确认映射（Approve → approve / Modify → 修改: / Reject → reject）

---

## 待人工决策

| 决策 ID | 类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响/风险 |
|---------|------|-----------|---------|---------|----------|
| CP8-DQ-01 | scope | CR-015 交付就绪确认：7 文件 ~130 行，CP6/CP7/CP8 全部 PASS | **approve**：关闭 CR-015，进入 delivered | 修改：指出需调整的交互点 / reject：回退变更 | 关闭后 AskUserQuestion 指令生效，ptm-tde 在 Claude Code 环境使用 TUI 选择器 |
| CP8-DQ-02 | follow_up_tracking | CR-016 Codex 整改候选项进入台账 | **确认**：T-01 进入 CR-015-FOLLOW-UP 台账追踪 | 立即创建 CR-016 / 丢弃 | 台账跟踪不占执行锁 |

---

## 不授权项

- 不授权在 Codex 环境使用 AskUserQuestion（工具不存在）
- 不授权删除 STOP-05 文本标记（回退基线必须保留）
- 不授权修改 HARD-STOP 协议的 approve/modify/reject 语义

---

## 后续 CR 候选

| 编号 | 来源 | 说明 |
|------|------|------|
| CR-016 | CR-015-FOLLOW-UP T-01 | Codex 平台 AskUserQuestion 等价交互整改 |

---

## 回复选项

- `approve` — 接受全部推荐方案，关闭 CR-015
- `修改: <决策ID>=<具体修改点>` — 调整单项
- `reject` — 驳回

---

## 人工审查结果

| 字段 | 值 |
|------|-----|
| 审查人 | user |
| 审查时间 | 2026-06-06T00:00:00+08:00 |
| 审查结论 | **APPROVED** — CR-015 交付就绪，关闭。Codex 整改（T-01）进入台账跟踪。 |
| 备注 | 用户 approve 全部推荐方案。CR-016 Codex 整改候选项保持 candidate。 |
