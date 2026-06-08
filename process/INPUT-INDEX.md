# PTM Team 输入索引

> 版本：v1.0 · 更新：2026-06-08

---

## 项目输入

| 输入 | 路径 | 类型 | 状态 |
|---|---|---|---|
| 原始请求 | `process/REQUEST.md` | Markdown | 已就绪 |
| 蓝图 | `docs/ptm-team-blueprint.md` | Markdown | v1.0 |
| ptm-tde 需求 | `docs/ptm-tde/REQUIREMENTS.md` | Markdown | v6.2（28 条） |
| ptm-tde 用例 | `docs/ptm-tde/USE-CASES.md` | Markdown | 已迁移 |

## 外部输入

| 输入 | 来源 | 说明 |
|---|---|---|
| MFQ&PPDCS 方法论 | 测试设计方法论 | ptm-tde 核心方法论基础 |
| atomic-ops CLI | 独立 Python 工具 | 79 个原子操作 |
| 因子库 YAML | `resource/` 目录 | 策略路由因子等 |
| 组网规范 v1.0 | `research/network-topology/` | 11 个拓扑模板 |
| 自动化工厂 | auto_factory_agent | ptm-tae 现有资产 |

## CR 输入

| CR | 输入来源 | 说明 |
|---|---|---|
| CR-010~017 | ptm-tde 源仓库基线 | 三阶段框架改造需求 |
| CR-20260520-001~20260528-001 | 早期迭代 | 参考对象修正、资源安装、方法论增强 |

## 输出产物

| 产物 | 路径 | 状态 |
|---|---|---|
| ptm-tde Agent | `agents/ptm-tde.md` | ✅ |
| Skill 集合（30+） | `skills/` | ✅ |
| 因子库资源 | `resource/` | ✅ |
| 用户手册 | `docs/ptm-tde/USER-MANUAL.md` | ✅ |
| 部署检查清单 | `docs/release/DEPLOY-CHECKLIST.md` | ✅ |

---

*本索引跟踪 ptm-team 项目的输入来源和输出产物。*
