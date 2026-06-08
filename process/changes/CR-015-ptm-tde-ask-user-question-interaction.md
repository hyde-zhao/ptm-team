---
change_id: CR-015-ptm-tde-ask-user-question-interaction
name: "引入 AskUserQuestion 交互层，增强 ptm-tde Claude Code 用户选择体验"
status: closed
workflow_id: WF-PTM-TEAM-20260520-001
workflow_mode: fast-lane
created: "2026-06-04"
closed: "2026-06-06"
created_by: meta-po（po-zhao）
impact_level: low
product_files: 7
cp8_manual_approved: "2026-06-06T00:00:00+08:00"
---

# CR-015：引入 AskUserQuestion 交互层

> **流程模式**：fast-lane — 纯指令添加，低风险轻量实现，跳过 CP0-CP5。
> **范围**：仅 Claude Code 环境。Codex 留待 CR-016 follow-up。

## 1. 变更动机

ptm-tde 项目当前所有用户交互均使用**纯文本标记**（`( )` 单选 / `[ ]` 多选 / `>>>` 开放式），用户需打字回复。这种模式交互效率低、易出错，且与 Claude Code 原生 TUI 风格不一致。

Claude Code 已内置 `AskUserQuestion` 工具，支持终端原生 TUI 选择器（键盘导航、单选/多选、Other 自定义输入），可直接在 ptm-tde 的交互点中使用。

**核心限制**：每次 ≤4 问题，每问题 ≤4 选项，header ≤12 字符。

## 2. 设计决策

### D1：规则分层架构

| 层级 | 位置 | 内容 |
|------|------|------|
| 通用规则 | `agents/ptm-tde.md` | 触发决策树、参数约束、Gate 映射、回退策略 |
| 具体调用 | 各 `skills/*/SKILL.md` | 该 Skill 特定交互点的 AskUserQuestion 参数 |

理由：`agents/ptm-tde.md` 是 ptm-tde 主 Agent，所有 Skill 的编排入口，安装到用户项目 `.claude/agents/`。各 SKILL.md 自包含具体调用指令，独立安装后仍可工作。不放在 CLAUDE.md（不会安装到用户项目）。

### D2：选项 > 4 时的拆分策略

| 场景 | 原选项数 | 拆分方式 |
|------|---------|---------|
| C-Customers 角色多选 | 5 | 问题 1：4 个核心角色多选 → 问题 2：是否有其他角色？（Yes→Other 输入） |
| S-Schedule 交付项多选 | 7（5 默认选中） | 展示 5 项已默认选中的提示，问题 1：是否有额外交付项？（Yes→Other 输入） |
| D-Deliverables 类型多选 | 6 | 同 S-Schedule 模式 |
| 维度地图 5 种操作 | 5（排他性） | 语义不可拆分 → 保留文本标记 |

### D3：Gate 确认语义映射

| AskUserQuestion label | 语义等同 | 实现方式 |
|----------------------|---------|---------|
| `Approve` | `approve` | 直接映射 |
| `Modify` | `修改:` | 利用 AskUserQuestion 内置 Other 机制，用户输入具体修改内容 |
| `Reject` | `reject` | 直接映射 |

### D4：回退判定规则

```
选项 ≤ 4 且无开放式需求 → AskUserQuestion
选项 > 4 → 尝试拆分，无法拆分 → 文本标记
需开放式输入 → >>> 文本格式
AskUserQuestion 工具不可用 → 文本标记
```

## 3. 变更范围

### 修改的产品文件（7 个）

| 优先级 | 文件 | 交互点 | 改造量 |
|--------|------|--------|--------|
| P0 | `skills/test-point-integrator/SKILL.md` | 步骤 4.5.3：候选汇总确认（4 单选） | ~10 行 |
| P0 | `skills/f-analyzer/SKILL.md` | 步骤 5（3 单选）+ 步骤 8（2 单选） | ~14 行 |
| P0 | `skills/q-analyzer/SKILL.md` | 步骤 1 末尾：OPEN 项确认（4 单选） | ~10 行 |
| P1 | `skills/design-planner/SKILL.md` | 步骤 5：设计计划确认（3 单选） | ~10 行 |
| P1 | `skills/kym/SKILL.md` | 阶段一+阶段三+阶段四（混合模式） | ~30 行 |
| — | `agents/ptm-tde.md` | 新增「用户交互层」小节 | ~40 行 |
| — | `skills/checkpoint-manager/SKILL.md` | Gate 人工确认节 | ~15 行 |

### 不修改的文件

- `scenario-discovery`、PPDCS 设计 Skill：交互极少或不匹配，暂不改造
- `CLAUDE.md`、`docs/ptm-tde/`：不会安装到用户项目

## 4. 实施记录

| 步骤 | 文件 | 状态 |
|------|------|:----:|
| 1 | `agents/ptm-tde.md` | ✅ done |
| 2 | P0: test-point-integrator | ✅ done |
| 3 | P0: f-analyzer | ✅ done |
| 4 | P0: q-analyzer | ✅ done |
| 5 | P1: design-planner | ✅ done |
| 6 | P1: kym | ✅ done |
| 7 | checkpoint-manager | ✅ done |
| CP6 | 编码完成检查 | ✅ PASS（10/10） |
| CP7 | 验证完成检查 | ✅ PASS（8/8） |
| CP8 | 自动预检 | ✅ PASS（10/10） |
| CP8 | 人工终验 | ⏳ pending |

## 5. 后续

- **CR-016-follow-up**：Codex 平台等价交互整改（pending，待用户研究方案）

## 修订记录

| 日期 | 事件 |
|------|------|
| 2026-06-04 | CR 创建，fast-lane 模式启动 |
