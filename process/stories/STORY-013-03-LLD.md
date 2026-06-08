---
story_id: STORY-013-03
name: design-ppdcs-analyzer + deliverable-renderer 路径迁移
tier: M
wave: B
change_id: CR-013-ptm-tde-ppdcs-phase
lld_version: "1.0"
status: ready-for-review
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-03 LLD：design-ppdcs-analyzer + deliverable-renderer 路径迁移

## 1. 概述

对 PPDCS 协调器和交付物渲染器执行路径迁移。这两个 Skill 是 PPDCS 阶段的顶层消费者，需要对齐 Wave A 已完成迁移的路径。

## 2. 模块拆分

| 子任务 | 文件 | 改动量 | TASK-ID |
|--------|------|:---:|---------|
| A | `skills/design-ppdcs-analyzer/SKILL.md` | ~19 处 | TASK-013-03-A |
| B | `skills/deliverable-renderer/SKILL.md` | ~16 处 | TASK-013-03-B |
| C | `ppdcs/delivery/` 目录创建 | 1 目录 + README | TASK-013-03-C |

## 3. 文件影响范围

### 3.1 design-ppdcs-analyzer（TASK-013-03-A）

| 搜索字符串 | 替换为 |
|-----------|--------|
| `analysis/integration/` | `mfq/integration/` |
| `analysis/plan/` | `process/plan/` |
| `analysis/scenarios/` | `kym/scenarios/` |
| `analysis/m-analysis/` | `mfq/m-analysis/` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |

### 3.2 deliverable-renderer（TASK-013-03-B）

| 搜索字符串 | 替换为 |
|-----------|--------|
| `analysis/scenarios/` | `kym/scenarios/` |
| `analysis/integration/` | `mfq/integration/` |
| `analysis/coverage/` | `ppdcs/coverage/` |
| `design/ppdcs/` | `ppdcs/ppdcs/` |
| `design/pc/` | `ppdcs/pc/` |
| `delivery/` | `ppdcs/delivery/` |

### 3.3 ppdcs/delivery/ 目录创建（TASK-013-03-C）

- 创建 `ppdcs/delivery/` 目录
- 创建 `ppdcs/delivery/.gitkeep`（确保空目录入库）
- 确保 deliverable-renderer 的 `ppdcs/delivery/` 路径有写入目标

## 4. 数据模型

无新增数据模型。

## 5. 接口与契约

| 接口 | 方向 | 变更 |
|------|------|------|
| design-ppdcs-analyzer 读 plan | 输入 | `analysis/plan/` → `process/plan/` |
| design-ppdcs-analyzer 读 LC/TD | 输入 | `analysis/integration/` → `mfq/integration/` |
| design-ppdcs-analyzer 写过程文件 | 输出 | `design/ppdcs/` → `ppdcs/ppdcs/` |
| design-ppdcs-analyzer 写 PC | 输出 | `design/pc/` → `ppdcs/pc/` |
| deliverable-renderer 读所有阶段 | 输入 | 全部旧路径 → 新路径 |
| deliverable-renderer 写交付物 | 输出 | `delivery/` → `ppdcs/delivery/` |

## 6. 处理流程

```
对每个 Skill 文件：
  1. Read 文件
  2. grep 确认旧路径位置
  3. 逐类替换（6 类映射 per file）
  4. 交叉验证：analyzer 的产出路径与 Wave A 5 设计 Skill 一致
  5. renderer 的消费路径与 coverage-verifier 产出路径一致
```

## 7. 异常处理

| 异常 | 处理 |
|------|------|
| 产出路径与 Wave A 不一致 | 回退，以 Wave A 实际迁移结果为准 |
| `delivery/` 替换影响非路径上下文 | 只替换文件路径引用 |

## 8. 测试设计

- `grep -rn "analysis/\|design/\|delivery/"` 确认仅保留正确的 ppdcs 引用
- analyzer 产出路径 = `ppdcs/ppdcs/` + `ppdcs/pc/`
- renderer 产出路径 = `ppdcs/delivery/`

## 9. 实施步骤

1. TASK-013-03-A：design-ppdcs-analyzer 路径迁移
2. TASK-013-03-B：deliverable-renderer 路径迁移
3. TASK-013-03-C：创建 `ppdcs/delivery/` 目录
4. 跨文件一致性验证

## 10. 风险

| 风险 | 缓解 |
|------|------|
| analyzer 产出路径与 5 设计 Skill 不一致 | Wave A 完成后记录实际路径，Wave B 对齐 |
| renderer 的 `delivery/` 路径遗漏 | 此路径为关键变更，额外验证 |

## 11. 发布与回滚

- **发布**：2 文件提交
- **回滚**：git revert

## 12. 实现灰区与待确认

无。路径映射已在 HLD-CR-013 §3.2 明确定义。

## 13. 验收标准

- [ ] design-ppdcs-analyzer 旧路径 = 0
- [ ] deliverable-renderer 旧路径 = 0
- [ ] deliverable-renderer 的 `delivery/` → `ppdcs/delivery/` 已更新
- [ ] 跨文件路径与 Wave A 一致

## 14. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-03 | meta-po | 初始 LLD |
