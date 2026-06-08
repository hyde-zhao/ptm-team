---
discussion_id: CP3-HLD-CR-017
cr_id: CR-017-factor-library-discovery-gap
created_at: "2026-06-06T00:00:00+08:00"
created_by: meta-se（hld-designer Skill）
mode: inline（单角色分析，平台无多 Agent 调度能力）
status: complete
---

# CP3 HLD 讨论日志 — CR-017

## 讨论 Context

CR-017 为 m-analyzer 的增量修复，范围小（1 Story，3 文件），架构灰区集中在"新步骤插入位置"和"与下游/CR-016 的衔接"。

## Architecture Gray Areas 讨论

### AGA-01：Step 1.5 插入位置与 CR-016 兼容性

**问题**：Step 1.5 的命名和结构需要为 CR-016 的 atomic-ops 发现步骤留出扩展点。

**分析**（lane-architecture）：
- 当前 Step 布局：Step 1（加载 KYM）→ Step 2（场景步骤分析）
- Step 1.5 负责"资源清单加载"这一通用模式
- CR-016 需要类似步骤加载 atomic-ops 清单
- 方案：Step 1.5 命名明确为"因子库清单加载"，CR-016 在此之后插入 Step 1.6"原子操作清单加载"
- 两个步骤共享模式但加载不同资源类型

**结论**：adopted — 推荐方案。Step 1.5 的 5 个子步骤（索引读取→遍历加载→状态处理→锁文件→完整性校验）是通用资源发现模式，CR-016 可复用。

### AGA-02：candidate 状态因子匹配策略

**问题**：如何区分 active 命中（source=public-library, match_confidence=high）和 candidate 命中（source=public-library, match_confidence=medium）？

**分析**（lane-product）：
- CR intake DQ-02 已 approved（match_confidence 分级）
- 用户选择：active→high，candidate→medium，均匹配但区分置信度
- 不需要在 HLD 阶段重新讨论

**结论**：resolved — 沿用 CR intake 决策。Step 2B 匹配逻辑新增 match_confidence 字段。

### AGA-03：Lock 文件策略

**问题**：首次运行自动创建 vs 要求手动创建？不一致时 WARNING vs HARD-STOP？

**分析**（lane-quality）：
- 当前因子库版本为 v0.1.x，checksum=pending
- 严格 lock 校验在没有版本管理基础的情况下过于激进
- HLD 推荐"首次自动创建 + 变更 WARNING 不阻断"
- 这是 CR intake 未覆盖的新决策点

**结论**：proposed — 推荐 WARNING 不阻断。需用户 CP3 确认（Q1）。

### AGA-04：test-point-integrator 反查时机

**问题**：因子库反查在 Step 4.5 候选汇总之前还是之后？

**分析**（lane-architecture + lane-product）：
- 在候选汇总之前反查：用户看到的是已去重的候选列表，减少确认负担
- 在候选汇总之后反查：不改变现有 Step 4.5 结构，但需两轮用户交互
- 推荐在之前，作为 Step 4.5.1.5 插入

**结论**：adopted — 推荐"之前"方案。反查结果直接影响 4.5.2 去重合并和优先级判定。

## 场景模拟结果

- SIM-01（首次运行，9 库就位）：PASS
- SIM-02（candidate 库命中）：PASS
- SIM-03（integrator 反查去重）：PASS

全部 3 个场景模拟通过，无阻断项。

## Deferred Ideas

- DAI-01：因子库定期同步机制（后续台账 T-01）
- DAI-02：match_confidence 在下游的显式处理 UI（后续台账 T-02）
- DAI-03：按 domain 按需过滤（性能优化，当前不需要）

## 待用户确认项（转 CP3 Decision Brief）

1. Q1：Lock 变更策略（WARNING vs HARD-STOP）
2. Q2：match_confidence=medium 在下游的展示方式
3. Q3：mfq/factor-usage/ 目录创建策略
