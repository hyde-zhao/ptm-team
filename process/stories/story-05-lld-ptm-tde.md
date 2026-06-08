---
story_id: "STORY-05"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T11:05:36+08:00"
author: "meta-dev"
tier: "application"
shared_fragments:
  - "ppdcs-reasoning-format"
open_items:
  - "reasoning 明细文件名在实现时与 renderer 对齐"
depends_on:
  - "STORY-04"
---

# STORY-05 LLD：Design Planner — CAE→PPDCS 完整推断与设计计划

## 1. 目标

升级 `design-planner`，让其从“只给推荐方法”升级为“输出完整推断与分析过程”。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-012 | reasoning、候选特征、排除理由、推荐方法 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| 规则评估层 | 分析 CAE 与场景链信号 |
| reasoning 组装层 | 输出主信号、候选、排除与推荐 |
| 计划表层 | 形成可确认的设计计划 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `skills/design-planner/SKILL.md` | 主体升级 |
| `agents/ptm-tde.md` | 设计计划确认提示（如需） |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| reasoning | `primary_signal`, `candidate_features`, `excluded_features`, `recommended_method`, `scenario_refs`, `test_object_refs`, `factor_refs` |

## 6. API / Interface 设计

- 输入：LC、测试数据、trace refs、`test_object_refs`、`factor_refs`
- 输出：设计计划表 + reasoning 明细

## 7. 核心处理流程

1. 读取 LC；
2. 评估 CAE / 场景链信号；
3. 生成候选特征；
4. 输出排除理由；
5. 形成推荐方法与确认表。

## 8. 技术设计细节

- reasoning 明细与计划表分层输出；
- 混合特征采用“主 / 辅”表达，不做模糊折中；
- 方法推荐时需要显式利用 STORY-04 产出的测试对象和测试因子。

## 9. 安全与性能设计

- 不允许 silent fallback 到“默认 D-Data”；
- 不确定时必须显式标记待确认。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| reasoning 字段完整性 | 结构检查 |
| 主/辅特征输出 | 样例验证 |
| 排除理由存在 | 文本审阅 |

## 11. 实施步骤

1. 对齐 reasoning 骨架；
2. 增加候选与排除字段；
3. 对齐计划表输出；
4. 增加混合特征表达。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| reasoning 过长难读 | 计划表与明细文件分层 |
| 混合特征判定不稳 | 主/辅特征显式化并交给用户确认 |

## 13. 回滚与发布策略

- 可回滚到仅输出推荐方法的旧骨架；
- 但不应丢失上游 trace。

## 14. Definition of Done

- [ ] 每条 LC 都有 reasoning
- [ ] reasoning 含候选与排除理由
- [ ] 计划表可直接用于设计确认
