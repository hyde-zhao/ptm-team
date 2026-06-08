---
story_id: STORY-013-04
name: GATE-4 增强（gate-spec.md + checkpoint-manager）
tier: M
wave: B
change_id: CR-013-ptm-tde-ppdcs-phase
lld_version: "1.0"
status: ready-for-review
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-04 LLD：GATE-4 增强

## 1. 概述

将 PPDCS Exit Gate（GATE-4）从骨架升级为完整检查项，并同步更新 checkpoint-manager 中的引用。

## 2. 模块拆分

| 子任务 | 文件 | 改动 | TASK-ID |
|--------|------|------|---------|
| A | `docs/ptm-tde/gate-spec.md` | GATE-4 充实 | TASK-013-04-A |
| B | `skills/checkpoint-manager/SKILL.md` | 路径更新 + GATE-4 对齐 | TASK-013-04-B |

## 3. 文件影响范围

### 3.1 gate-spec.md（TASK-013-04-A）

**位置**：`docs/ptm-tde/gate-spec.md` 的 GATE-4 章节（当前骨架位置）

**改动**：将 7 项骨架 Checklist 替换为 P1-P7 完整自检项，人工确认项从 3 项扩展为 4 项。

**P1-P7 自检项定义**：

| # | 检查项 | 通过条件 |
|---|--------|----------|
| P1 | PPDCS 设计过程完整 | `ppdcs/ppdcs/` 下每个 LC 都有设计过程文件，PPDCS 方法与 plan 推荐一致 |
| P2 | PC 文件完整 | `ppdcs/pc/` 下每个 LC 都有物理用例文件，16 列格式正确 |
| P3 | PC 拓扑绑定回链 | PC 中所有真实设备、端口、链路能回链到 LC `topology_bindings` → `kym/scenarios/confirmed-scenarios.md` |
| P4 | 双层覆盖率验证 | `ppdcs/coverage/` 存在覆盖率报告：需求覆盖 = 100%，测试点覆盖 ≥ 95% |
| P5 | 因子覆盖验证 | 所有 `factor_bindings` 的因子在 PC 中有覆盖 |
| P6 | 交付物完整 | `ppdcs/delivery/` 包含且仅包含测试方案和测试用例两个文件 |
| P7 | 交付物字段保留 | 交付物保留 `topology_bindings / topology_role / source / fact_status` |

**人工确认项**：

| 确认项 | 说明 |
|--------|------|
| PPDCS 设计方法 | 每个 LC 的 PPDCS 方法选择是否合理，设计步骤是否完整 |
| 物理用例质量 | PC 编号、组网描述、测试步骤、预期结果是否满足标准 |
| 覆盖率结果 | 需求覆盖率、测试点覆盖率是否达标，未覆盖项是否可接受 |
| 拓扑绑定 | needs-confirmation 项是否已处理或记录为风险 |

### 3.2 checkpoint-manager（TASK-013-04-B）

**路径迁移**（~7 处）：

| 搜索字符串 | 替换为 |
|-----------|--------|
| `analysis/` | 分阶段路径（`kym/`、`mfq/`、`ppdcs/`） |
| `design/` | `ppdcs/` |

**GATE-4 对齐**：更新 GATE-4 描述，引用 gate-spec.md 的 P1-P7 自检项和人工确认项。

## 4. 数据模型

无新增数据模型。Gate 检查项为文档描述。

## 5. 接口与契约

| 接口 | 说明 |
|------|------|
| gate-spec.md → checkpoint-manager | checkpoint-manager 的 GATE-4 描述需与 gate-spec 的 GATE-4 章节对齐 |
| gate-spec.md → ptm-tde 主 Agent | 主 Agent 在执行 GATE-4 时读取 gate-spec.md 的检查项定义 |

## 6. 处理流程

```
TASK-013-04-A：gate-spec.md
  1. Read gate-spec.md 的 GATE-4 章节
  2. 定位 7 项骨架 Checklist → 替换为 P1-P7 完整自检项
  3. 定位 3 项人工确认 → 扩展为 4 项
  4. 保留 Entry Criteria 不变
  5. 不修改 GATE-1~GATE-3 内容

TASK-013-04-B：checkpoint-manager
  1. Read checkpoint-manager SKILL.md
  2. 执行路径替换（~7 处）
  3. 更新 GATE-4 描述与 gate-spec 对齐
```

## 7. 异常处理

| 异常 | 处理 |
|------|------|
| gate-spec.md 中 GATE-4 位置变动 | 通过章节标题 "GATE-4" 定位，不依赖行号 |
| checkpoint-manager 路径替换遗漏 | grep 验证 |

## 8. 测试设计

- gate-spec.md GATE-4 含 P1-P7 + 4 项人工确认
- checkpoint-manager 旧路径 grep = 0
- checkpoint-manager GATE-4 描述含 P1-P7 引用
- GATE-1~GATE-3 内容未变

## 9. 实施步骤

1. TASK-013-04-A：修改 gate-spec.md
2. TASK-013-04-B：修改 checkpoint-manager
3. 交叉一致性验证

## 10. 风险

| 风险 | 缓解 |
|------|------|
| P1-P7 自检项与其他 Gate 检查项重复 | 逐项对比 GATE-1~GATE-4，确保无重复 |
| checkpoint-manager 旧路径替换不完整 | grep 全局扫描 |

## 11. 发布与回滚

- **发布**：2 文件提交
- **回滚**：git revert

## 12. 实现灰区与待确认

| # | 问题 | 状态 |
|---|------|------|
| LCQ-013-04-01 | GATE-4 的 "人工确认项" 是否需要与现有 GATE-2 的确认项格式保持一致？ | open（推荐方案 A：保持一致格式） |

## 13. 验收标准

- [ ] gate-spec.md GATE-4 含完整 P1-P7 + 4 项人工确认
- [ ] checkpoint-manager 旧路径 = 0
- [ ] checkpoint-manager GATE-4 描述与 gate-spec 对齐
- [ ] GATE-1~GATE-3 内容不变

## 14. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-03 | meta-po | 初始 LLD |
