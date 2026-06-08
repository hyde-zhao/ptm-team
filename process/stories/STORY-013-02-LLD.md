---
story_id: STORY-013-02
name: coverage-verifier 路径迁移
tier: S
wave: A
change_id: CR-013-ptm-tde-ppdcs-phase
lld_version: "1.0"
status: ready-for-review
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
---

# STORY-013-02 LLD：coverage-verifier 路径迁移

## 1. 概述

对 coverage-verifier Skill 执行路径字符串替换（~23 处），这是 PPDCS 阶段单文件改动量最大的 Skill（跨阶段读取 kym/mfq/ppdcs 全部产出）。

## 2. 模块拆分

| 子任务 | 文件 | TASK-ID |
|--------|------|---------|
| A | `skills/coverage-verifier/SKILL.md` | TASK-013-02-A |

单文件单任务，无子模块拆分。

## 3. 文件影响范围

### 3.1 coverage-verifier（TASK-013-02-A）

**路径替换**（~23 处）：

| 搜索字符串 | 替换为 | 预估出现次数 |
|-----------|--------|:---:|
| `analysis/scenarios/` | `kym/scenarios/` | ~4 |
| `analysis/integration/logic-cases.md` | `mfq/integration/logic-cases.md` | ~3 |
| `analysis/integration/test-data.md` | `mfq/integration/test-data.md` | ~2 |
| `analysis/factor-usage/` | `mfq/factor-usage/` | ~3 |
| `analysis/m-analysis/` | `mfq/m-analysis/` | ~2 |
| `design/ppdcs/` | `ppdcs/ppdcs/` | ~3 |
| `design/pc/` | `ppdcs/pc/` | ~4 |
| `analysis/coverage/` | `ppdcs/coverage/` | ~2 |

## 4. 数据模型

无新增数据模型。

## 5. 接口与契约

| 接口 | 方向 | 变更 |
|------|------|------|
| 读取 `kym/scenarios/` | 输入 | 旧路径 `analysis/scenarios/` → 新路径 |
| 读取 `mfq/integration/` | 输入 | 旧路径 `analysis/integration/` → 新路径 |
| 读取 `mfq/factor-usage/` | 输入 | 旧路径 `analysis/factor-usage/` → 新路径 |
| 读取 `ppdcs/ppdcs/` | 输入 | 旧路径 `design/ppdcs/` → 新路径 |
| 读取 `ppdcs/pc/` | 输入 | 旧路径 `design/pc/` → 新路径 |
| 写入 `ppdcs/coverage/` | 输出 | 旧路径 `analysis/coverage/` → 新路径 |

## 6. 处理流程

```
1. Read skills/coverage-verifier/SKILL.md
2. grep 确认所有旧路径位置
3. 逐类替换路径字符串（8 类映射）
4. 特别注意：覆盖率报告产出路径从 analysis/coverage/ → ppdcs/coverage/（生产路径变更）
5. 验证：grep "analysis/\|design/" 无残留
```

## 7. 异常处理

| 异常 | 处理 |
|------|------|
| 路径替换后发现残留 | 回退并逐行审查 |
| `analysis/coverage/` 替换影响非路径上下文 | 只替换文件路径引用 |

## 8. 测试设计

- `grep -rn "analysis/\|design/" skills/coverage-verifier/SKILL.md` = 0
- 新路径 `ppdcs/coverage/` 在文件中出现 ≥ 2 次
- 原始执行流程和验收标准保持不变

## 9. 实施步骤

1. 读取文件，grep 确认替换位置
2. 执行 8 类路径替换
3. 全局验证
4. 提交

## 10. 风险

| 风险 | 缓解 |
|------|------|
| 遗漏某类路径引用 | 使用 grep 穷举所有 `analysis/` 和 `design/` 出现 |
| coverage-verifier 输出路径变更影响下游 | STORY-013-03 deliverable-renderer 同步更新 |

## 11. 发布与回滚

- **发布**：单文件提交
- **回滚**：git revert

## 12. 实现灰区与待确认

无。coverage-verifier 路径映射与 HLD-CR-013 §3.2 完全一致。

## 13. 验收标准

- [ ] 旧路径 grep = 0
- [ ] 新路径引用正确
- [ ] 输出路径 `ppdcs/coverage/` 已更新
- [ ] 原始内容未被修改

## 14. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-03 | meta-po | 初始 LLD |
