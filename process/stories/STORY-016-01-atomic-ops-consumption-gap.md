---
story_id: STORY-016-01
story_slug: atomic-ops-consumption-gap
cr_id: CR-016-atomic-ops-consumption-gap
name: "m-analyzer 原子操作消费缺口修复 + 语义匹配"
tier: M
wave: A
status: ready-for-lld
created_at: "2026-06-06T00:00:00+08:00"
product_files:
  - skills/m-analyzer/SKILL.md
  - skills/test-point-integrator/SKILL.md
  - agents/ptm-tde.md
  - docs/ptm-tde/gate-spec.md
  - docs/ptm-tde/data-flow-spec.md
---

# STORY-016-01：原子操作消费缺口修复 + 语义匹配

## 摘要

在 CR-017 Step 1.5 之后插入 Step 1.6「原子操作清单加载」（运行 `atomic-ops list --format json` → 构建 op_id 索引）。重写 Step 2C 为 L1-L4 四级语义匹配（精确→加权分词强匹配→弱匹配→候选）。建立 `mfq/atomic-op-usage/` 平行跟踪目录。test-point-integrator 新增 Step 7.5.3 原子操作候选交叉验证。更新 gate-spec.md 和 data-flow-spec.md。

## AC

- [ ] m-analyzer 新增 Step 1.6（5 子步骤：CLI 查询→解析→索引→lock→降级），~55 行
- [ ] m-analyzer Step 2C 重写为 L1-L4 四级语义匹配，~45 行
- [ ] m-analyzer Step 7 输出文件 9→10（新增 atomic-op-lock.yaml）
- [ ] test-point-integrator 新增 Step 7.5.3 原子操作候选交叉验证，~40 行
- [ ] agents/ptm-tde.md 目录布局新增 atomic-op-usage/，~10 行
- [ ] gate-spec.md GATE-1#3 更新 + GATE-3 新增 M9，~15 行
- [ ] data-flow-spec.md Entity 8 更新 + 8.8 小节，~30 行
- [ ] `fw_config_subinterface` 等 3 个误标候选正确匹配到 `fw_config_interface`

## NF

- CLI 不可用时优雅降级（回退现有逻辑 + WARNING）
- 与 CR-017 Step 1.5 模式一致（命名 Step 1.6）
- 语义匹配权重可调

## 文件影响

| 文件 | 优先级 | 变更量 |
|------|:--:|:---:|
| `skills/m-analyzer/SKILL.md` | P0 | ~120 行 |
| `skills/test-point-integrator/SKILL.md` | P1 | ~40 行 |
| `agents/ptm-tde.md` | P1 | ~10 行 |
| `docs/ptm-tde/gate-spec.md` | P2 | ~15 行 |
| `docs/ptm-tde/data-flow-spec.md` | P2 | ~30 行 |

## 设计输入

- HLD：`process/HLD-CR-016.md` v1.0
- CR intake：`process/changes/CR-016-atomic-ops-consumption-gap.md`
- 参考：CR-017 Step 1.5 设计模式
