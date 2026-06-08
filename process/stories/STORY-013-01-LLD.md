---
story_id: STORY-013-01
name: 5 设计 Skill 路径迁移 + 方法论占位
tier: M
wave: A
change_id: CR-013-ptm-tde-ppdcs-phase
lld_version: "1.0"
status: ready-for-review
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-01 LLD：5 设计 Skill 路径迁移 + 方法论占位

## 1. 概述

对 5 个 PPDCS 设计 Skill 执行路径字符串替换（`analysis/*`/`design/*` → `kym/`/`mfq/`/`ppdcs/`/`process/plan/`），并在每个 Skill 末尾增加方法论占位节。

## 2. 模块拆分

| 子任务 | 文件 | 改动 | TASK-ID |
|--------|------|------|---------|
| A | `skills/process-design/SKILL.md` | 路径迁移 + 方法论占位 | TASK-013-01-A |
| B | `skills/parameter-design/SKILL.md` | 路径迁移 + 方法论占位 | TASK-013-01-B |
| C | `skills/data-design/SKILL.md` | 路径迁移 + 方法论占位 | TASK-013-01-C |
| D | `skills/combination-design/SKILL.md` | 路径迁移 + 方法论占位 | TASK-013-01-D |
| E | `skills/state-design/SKILL.md` | 路径迁移 + 方法论占位 | TASK-013-01-E |

## 3. 文件影响范围

### 3.1 process-design（TASK-013-01-A）

**路径替换**（~12 处）：

| 搜索字符串 | 替换为 |
|-----------|--------|
| `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` |
| `analysis/integration/test-data.md` | `mfq/integration/test-data.md` |
| `analysis/plan/design-plan.md` | `process/plan/design-plan.md` |
| `analysis/plan/design-planner-reasoning.md` | `process/plan/design-planner-reasoning.md` |
| `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |

**方法论占位**：追加到 §验收标准之前。

### 3.2 parameter-design（TASK-013-01-B）

路径替换（~11 处），同 process-design 模式，额外增加：
- `analysis/m-analysis/ppdcs-annotation.md` → `mfq/m-analysis/ppdcs-annotation.md`
- `analysis/factor-usage/` → `mfq/factor-usage/`

### 3.3 data-design（TASK-013-01-C）

路径替换（~10 处），同 parameter-design 模式。

### 3.4 combination-design（TASK-013-01-D）

路径替换（~10 处），同 parameter-design 模式。

### 3.5 state-design（TASK-013-01-E）

路径替换（~13 处），同 process-design 模式（需消费 `confirmed-scenarios.md` 和 `ppdcs-annotation.md`）。

## 4. 数据模型

无新增数据模型。路径字符串为本次变更的唯一数据对象。

## 5. 接口与契约

| 接口 | 消费方 | 变更 |
|------|--------|------|
| 输入路径（读 `mfq/integration/`） | 5 设计 Skill | 旧路径 → 新路径 |
| 输出路径（写 `ppdcs/ppdcs/`、`ppdcs/pc/`） | 5 设计 Skill | 旧路径 → 新路径 |
| 方法论占位节 | 用户（后续手动填充） | 新增 |

## 6. 处理流程

```
对每个 Skill 文件：
  1. Read 文件内容
  2. 执行 grep 搜索旧路径引用，确认替换位置
  3. 逐项替换路径字符串
  4. 在 §验收标准 之前插入方法论占位节
  5. 验证：grep "analysis/\|design/" 无残留
  6. 输出变更 diff
```

## 7. 异常处理

| 异常 | 处理 |
|------|------|
| 某个旧路径在文件中不存在 | 记录为 `skipped`，不报错（该 Skill 不使用此路径） |
| 替换后发现残留旧路径 | 回退该文件，重新分析遗漏位置 |
| 方法论占位节与已有章节冲突 | 统一放在 §验收标准之前，§Gotchas 之后 |

## 8. 测试设计

- 每个 Skill 替换后运行 `grep -rn "analysis/\|design/" skills/<name>/SKILL.md`
- 每个 Skill 验证新路径引用计数与预期一致
- 方法论占位节存在性检查

## 9. 实施步骤

1. TASK-013-01-A：process-design 路径迁移 + 方法论（可并行）
2. TASK-013-01-B：parameter-design 路径迁移 + 方法论（可并行）
3. TASK-013-01-C：data-design 路径迁移 + 方法论（可并行）
4. TASK-013-01-D：combination-design 路径迁移 + 方法论（可并行）
5. TASK-013-01-E：state-design 路径迁移 + 方法论（可并行）
6. 全局验证：`grep -rn "analysis/\|design/" skills/<name>/SKILL.md` 全部 5 文件无残留

## 10. 风险

| 风险 | 缓解 |
|------|------|
| 路径替换不完整 | 逐文件 grep 验证 |
| 误替换（如 `analysis` 出现在注释/说明中） | 只替换路径引用上下文中的出现 |
| 方法论占位模板不一致 | 使用统一模板，5 文件 diff 交叉校验 |

## 11. 发布与回滚

- **发布**：5 文件一次性提交
- **回滚**：git revert，无数据迁移

## 12. 实现灰区与待确认

| # | 问题 | 状态 |
|---|------|------|
| LCQ-013-01-01 | `analysis/` 路径引用可能与注释/文档说明中的描述性文字重叠（如 "analysis 阶段"），是否需要额外人工判断？ | open（推荐方案 A：仅替换路径格式的引用，描述性文字保留） |

## 13. 验收标准

- [ ] 5 个 Skill 文件旧路径残留 = 0
- [ ] 5 个 Skill 文件新路径引用数正确
- [ ] 5 个 Skill 文件均含方法论占位节
- [ ] 原始章节和内容未被修改
- [ ] 文件总 diff 在预期范围内（~130 行）

## 14. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-03 | meta-po | 初始 LLD |
