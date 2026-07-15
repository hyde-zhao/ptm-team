# ptm-tde v1.0 发布说明

> 版本：v1.0 · 发布日期：2026-06-06 · 项目：ptm-team

---

## 概述

**ptm-tde**（测试设计工程师）是 ptm-team 六 Agent 体系中首个交付的 AI Agent。基于 **MFQ&PPDCS** 方法论，从需求文档出发，经过系统化分析，输出完整的测试方案和测试用例。

本次 v1.0 发布覆盖了三阶段框架（KYM → MFQ → PPDCS）的完整实现，共 7 条 CR、23 个 Story。

---

## 版本演进

| 版本 | 日期 | CR | 内容 |
|---|---|---|---|
| v0.1 | 2026-05-20 | CR-20260520-001 | scenario-discovery 参考对象修正 |
| v0.2 | 2026-05-21 | CR-20260521-001 | factor-library 资源安装 + topology-role/factor 分离 |
| v0.3 | 2026-05-28 | CR-20260528-001 | 场景发现方法论增强 |
| v0.4 | 2026-06-02 | CR-010 | 三阶段框架改造（结构层，6 Stories） |
| v0.5 | 2026-06-02 | CR-011 | KYM 阶段改造（内容层，4 Stories） |
| v0.6 | 2026-06-02 | CR-012 | MFQ 阶段改造（扩展范围，8 Stories） |
| v0.7 | 2026-06-04 | CR-013 | PPDCS 阶段改造（4 Stories） |
| v1.0-rc1 | 2026-06-06 | CR-015 | AskUserQuestion 交互增强（fast-lane） |
| v1.0-rc2 | 2026-06-06 | CR-017 | 因子库发现机制修复 |
| **v1.0** | **2026-06-06** | **CR-016** | **原子操作消费缺口修复 + 全面交付** |

## 新增功能

### 三阶段框架（CR-010/011/012/013）

- **KYM 阶段**：Know Your Method，GATE-1/GATE-2 入口检查 + 方法论确认
- **MFQ 阶段**：M 分析（单功能拆分，10 步，场景步骤驱动）+ F 分析（耦合分析，9 步）+ Q 分析（质量属性，6 步，逐 TSP 驱动）+ GATE-3 出口门控
- **PPDCS 阶段**：P-Process/P-Parameter/D-Data/C-Combination/S-State 五特征建模 + 8 个设计 Skill + GATE-4 增强（P1-P7）+ 候选汇总 + GATE-5 交付确认
- **12 步主流程**：feature-parser → scenario-discovery → m/f/q-analyzer → test-point-integrator → design-planner → 5 个 PPDCS 设计 Skill → coverage-verifier → deliverable-renderer
- **5 个人工检查点**：场景确认、目录结构确认、设计计划确认、耦合点确认、最终交付确认

### 交互增强（CR-015）

- Claude Code 平台引入 `AskUserQuestion` 交互模式
- test-point-integrator、f-analyzer、q-analyzer 纯适配
- kym、design-planner 混合模式（结构化选择 + 自由文本）

### 原子操作集成（CR-016）

- Step 1.6 atomic-ops CLI 查询，支持 79 个原子操作
- Step 2C L1-L4 五维语义匹配（使用 atomic-ops aliases 字段）
- test-point-integrator 4.5.1.6 交叉验证
- 跟踪目录 `atomic-op-usage/`

### 因子库发现（CR-017）

- Step 1.5 m-analyzer 因子库清单加载
- Step 2B match_confidence 分级（high/medium/low/none）
- test-point-integrator 4.5.1.5 因子库反查
- GATE-3 M8 因子库覆盖检查

## 核心文件

| 文件 | 说明 |
|---|---|
| `agents/ptm-tde.md` | 主 Agent 定义，含 12 步流程和并行执行规则 |
| `skills/` | 30+ 个 Skill（6 个分析 Skill + 8 个设计 Skill + 覆盖验证 + 交付渲染等） |
| `docs/ptm-tde/` | 用户手册、组件手册、Gate 规约、数据流规约、运行时产物等 |
| `resource/` | 因子库资源文件 |

## 质量摘要

| 门控 | 结果 |
|---|---|
| CP3 HLD 一致性 | 4 个 CR 级自动预检全部 PASS（33/33 等） |
| CP5 LLD 可实现性 | 4 个 batch 全部 approved，约 25 个 Story LLD PASS |
| CP6 编码完成 | 约 28 个 Story PASS，Agent Dispatch Evidence 完整 |
| CP7 验证完成 | 约 12 个全局/Story PASS，无 BLOCKER 遗留 |
| CP8 交付就绪 | 4 个 CR 级自动预检 PASS，人工终验 approved |

## 已知限制

1. CP0-CP5 通过 gate_inheritance 继承自 ptm-tde 源仓库，未在本仓库重新执行完整流程
2. 低风险 Story 缺少独立 IMPLEMENTATION.md 实现执行证据文件
3. atomic-ops aliases 覆盖 32/79 ops，剩余 47 个无歧义 op 按需补充
4. 其余 5 个 Agent（ptm-tm/tse/te/tae/qa）尚未开始或处于早期阶段

## 后续计划

| 项目 | 状态 | 说明 |
|---|---|---|
| CR-011-T-01 断点恢复 | candidate | 跟踪：`process/changes/CR-011-FOLLOW-UP-TRACKING-2026-06-02.md` |
| CR-011-T-02 关键词调优 | candidate | 同上 |
| CR-015-T-01 Codex 整改 | candidate | 跟踪：`process/changes/CR-015-FOLLOW-UP-TRACKING-2026-06-04.md` |
| atomic-ops aliases 补充 | spike_candidate | 47 个无歧义 op 按需补充 |
| ptm-tm/tse/te/tae/qa 开发 | 待启动 | 参见 `docs/ptm-team-blueprint.md` |

---

*本发布说明由 meta-po 生成，覆盖 ptm-tde v1.0 全部 7 条 CR 交付范围。*
