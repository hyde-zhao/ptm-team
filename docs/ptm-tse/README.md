# ptm-tse · 测试架构师 / 逆向分析引擎

> 状态：✅ CR-030 交付就绪待 CP8 人工终验 · 所属项目：ptm-team

## 角色定位

**测试架构师 / 团队技术 Owner**。技术方向的最终决策者，对用例质量、执行策略、工具架构三个方向都有评审权。

## 核心职责

| 职责 | 说明 |
|---|---|
| 需求分析 | 接收 ptm-tm 下发的需求分析任务，分解特性维度，识别测试点 |
| 策略制定 | 制定测试策略（优先级/深度/广度/分层） |
| 用例评审 | 评审 ptm-tde 的用例覆盖度和设计质量 |
| 执行策略评估 | 评审 ptm-te 的执行策略和资源分配 |
| 工具框架评估 | 评审 ptm-tae 的工具架构和技术选型 |
| ITR 摄取与保存 | 在固定 allowlist 内通过 GET 获取问题单，清洗、质量门控、版本化保存 |
| 逆向分析 | 基于已保存问题单完成根因、产品质量、流出、漏测、改进、环比同比六维分析 |
| 改进治理 | 生成 CA/PA 草案与刷新提示；仅 reviewer 可批准、变更状态或关闭 |

## 专属 Skill

| Skill | 功能 | 状态 |
|---|---|---|
| `itr-ticket-ingestion` | ITR allowlist GET、快照、清洗、质量报告、变更检测与版本合并 | ✅ |
| `reverse-analysis` | 资格检查、证据约束、六维分析、S1/S2 报告与差异解释 | ✅ |
| `improvement-tracker` | CA/PA 草案、闭环跟踪、有效性检查、措施基线刷新提示 | ✅ |

## 关键评审链

```
ptm-tse
  ├── ITR 摄取 -> SQLite 受限存储 -> 逆向分析 -> reviewer
  ├── 评审 ptm-tde 的用例
  ├── 评审 ptm-te 的执行策略
  └── 评审 ptm-tae 的工具框架
```

## 演进路线

| Step | 能力 |
|---|---|
| CR-030 v1 | ✅ ITR 问题单摄取、S1/S2 逆向分析、改进措施草案与人工治理 |
| 后续 | 受控环境 runtime smoke test、真实 ITR schema 适配、反馈驱动优化 |

## 依赖

- 上游：ptm-tm（任务下发）
- 下游：ptm-tde（用例评审）、ptm-te（执行策略评审）、ptm-tae（工具框架评审）

## 相关文档

- 蓝图：`docs/ptm-team-blueprint.md` §2.3
- 使用手册：`docs/ptm-tse/USER-MANUAL.md`
- Agent 定义：`agents/ptm-tse.md`
- 发布范围与限制：`docs/release/RELEASE-NOTES.md`
