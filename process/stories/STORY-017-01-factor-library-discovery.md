---
story_id: STORY-017-01
story_slug: factor-library-discovery
cr_id: CR-017-factor-library-discovery-gap
name: "m-analyzer 因子库发现机制修复"
tier: M
wave: A
status: ready-for-lld
created_at: "2026-06-06T00:00:00+08:00"
depends_on: []
blocks: []
product_files:
  - skills/m-analyzer/SKILL.md
  - skills/test-point-integrator/SKILL.md
  - docs/ptm-tde/gate-spec.md
---

# STORY-017-01：m-analyzer 因子库发现机制修复

## 摘要

在 m-analyzer Step 1 和 Step 2 之间插入 Step 1.5「因子库清单加载」，使 m-analyzer 能发现全部 9 个已注册因子库（当前仅扫描 2 个）。修改 Step 2B 匹配规则支持 candidate 状态因子 match_confidence 分级。test-point-integrator Step 4.5 新增因子库反查去重。gate-spec.md GATE-3 新增 M8 扫描完整性检查。

## 验收标准（AC）

- [ ] m-analyzer SKILL.md 新增 Step 1.5（5 个子步骤），约 +60 行
- [ ] m-analyzer SKILL.md Step 2B 修改匹配规则（match_confidence 字段），约 +15 行
- [ ] m-analyzer SKILL.md 输出文件数从 8 个增至 9 个（新增 factor-library-lock.yaml）
- [ ] test-point-integrator SKILL.md Step 4.5 新增 4.5.1.5 因子库反查去重，约 +25 行
- [ ] gate-spec.md GATE-3 Checklist 新增 M8：因子库扫描完整性（N_scanned == N_registered），约 +8 行
- [ ] m-analyzer 运行后 factor-resolution-report.md 显示扫描库数 = 9
- [ ] candidate 状态因子命中时 source=public-library, match_confidence=medium
- [ ] 18 个重复候选因子不再生成（source 从 new-candidate 变为 public-library）
- [ ] factor-library-lock.yaml 首次运行时自动创建，再次运行时校验不一致输出 WARNING
- [ ] 扫描不完整（N_scanned < N_registered）时 HARD-STOP 阻断

## 非功能需求（NF）

- [ ] 与 STOP-04 协议一致：不新增 Agent mkdir 行为
- [ ] 与 CR-016 兼容：Step 1.5 为 CR-016 Step 1.6 留出扩展点
- [ ] 向后兼容：新逻辑是旧逻辑的超集（多扫 7 个库，不改变其他行为）
- [ ] 全量 9 库加载性能可忽略（<200 因子，纯内存操作）

## 文件影响范围

| 文件 | 优先级 | 变更量 | 变更类型 |
|------|:--:|:---:|------|
| `skills/m-analyzer/SKILL.md` | P0 | ~75 行 | 新增 Step 1.5 + 修改 Step 2B |
| `skills/test-point-integrator/SKILL.md` | P1 | ~25 行 | 新增 Step 4.5.1.5 |
| `docs/ptm-tde/gate-spec.md` | P2 | ~8 行 | GATE-3 新增 M8 |

## 设计输入

- HLD：`process/HLD-CR-017.md` v1.0
- CR intake：`process/changes/CR-017-factor-library-discovery-gap.md`
- 参考：m-analyzer v3.0 SKILL.md Step 1 + Step 2 + Step 7
