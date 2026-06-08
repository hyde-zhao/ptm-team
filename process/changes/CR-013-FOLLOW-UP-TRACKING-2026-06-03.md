---
tracking_id: CR-013-FOLLOW-UP
source_change: CR-013-ptm-tde-ppdcs-phase
created_at: "2026-06-03T00:00:00+08:00"
created_by: meta-po（po-zhao）
status: active
---

# CR-013 后续跟踪台账

> 来源：CR-013 CP3 HLD 灰区讨论 — 灰区 1 决策：保持 CR-013 原范围，非 PPDCS Skill 的旧路径引用创建独立 CR 跟踪。

## 候选 CR

| 编号 | 名称 | 状态 | 来源 | 说明 |
|------|------|:---:|------|------|
| T-01 | change-impact-analyzer 路径迁移 | candidate | 灰区 1 | 6 处旧路径引用（`analysis/`、`design/`、`delivery/`）需迁移到新路径 |
| T-02 | bug-gap-analyzer 路径迁移 | candidate | 灰区 1 | 7 处旧路径引用（`analysis/`、`design/`）需迁移到新路径 |

## 后续 CR 创建条件

- change-impact-analyzer 和 bug-gap-analyzer 是变更管理和缺陷分析 Skill，独立于三阶段框架
- 建议合并为一个 CR-014（变更管理 Skill 路径对齐），tier=S
- CR-013 全部 Story verified 后可以启动 CR-014

## 修订记录

| 日期 | 事件 |
|------|------|
| 2026-06-03 | 台账创建，T-01/T-02 均为 candidate |
