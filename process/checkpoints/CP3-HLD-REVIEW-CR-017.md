---
checkpoint_id: "CP3"
checkpoint_name: "CR-017 HLD 架构评审 — 人工终验"
type: "auto_precheck_then_manual"
status: "approved"
approved_by: "user"
approved_at: "2026-06-06T00:00:00+08:00"
owner: "meta-po（po-zhao）"
depends_on:
  auto_precheck: "process/checks/CP3-HLD-CONSISTENCY-CR-017.md"
  hld: "process/HLD-CR-017.md"
  discussion_log: "process/discussions/CP3-HLD-DISCUSSION-LOG-CR-017.md"
  discussion_checkpoint: "process/checks/CP3-DISCUSSION-CHECKPOINT-CR-017.json"
  cr: "process/changes/CR-017-factor-library-discovery-gap.md"
---

# CP3：CR-017 HLD 架构评审 — 人工终验

## 自动预检摘要

| 检查类别 | 结论 | 详情 |
|---|---|---|
| HLD 章节完整性（18 项） | PASS | 18/18 章节通过 |
| 设计一致性（10 项） | PASS | 候选方案有真实差异、场景模拟全部 PASS、拆分信号评估完成 |
| CR-017 专项检查（5 项） | PASS | CR intake 决策全部兑现、与 CR-016 兼容性已考虑、不授权项未被覆盖 |
| **总计** | **PASS** | **33/33** 检查项通过 |

自动预检详细结果见：`process/checks/CP3-HLD-CONSISTENCY-CR-017.md`

---

## Decision Brief

### 变更概要

CR-017 修复 m-analyzer 因子库发现缺口：在现有 7 步流程中插入 Step 1.5（因子库清单加载），使 m-analyzer 能发现全部 9 个已注册因子库（当前仅扫描 2 个），修复 18/35 候选因子假阳性问题。

- **推荐方案**：方案 A — Step 1.5 因子库清单加载 + match_confidence 分级 + lock 文件
- **复杂度**：standard（3 文件，1 Story，1 Wave）
- **工作量**：~108 行净增（m-analyzer ~75 行 + test-point-integrator ~25 行 + gate-spec ~8 行）

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| CP3-DQ-01 | architecture | 是否接受"首次运行自动创建 factor-library-lock.yaml，后续不一致时 WARNING 不阻断"的策略？（HLD Q1） | **WARNING 不阻断**：首次自动创建，后续校验不一致时输出 WARNING 继续执行 | 备选 A：HARD-STOP 阻断——不一致时停止 m-analyzer，要求用户手动解决 | 推荐方案适应当前因子库 v0.1.x 成熟度，不阻断正常流程但保留可见提示。备选 A 更严格但当前 checksum=pending，阻断过于激进 | 推荐：低风险。备选 A：在因子库版本不稳定的情况下频繁阻断，用户体验差。当所有库 version ≥ 1.0 且 checksum 非 pending 时切换 |
| CP3-DQ-02 | architecture | 是否接受"match_confidence=medium 的因子在下游 test-point-integrator 候选汇总时仍展示但降级提示"？（HLD Q2） | **展示但降级**：medium 因子在候选汇总表中标记置信度，用户可逐项确认或批量接受 | 备选 A：medium 与 high 无区别对待——candidate 库因子与 active 库因子在 UI 上完全一致 | 推荐方案保留区分度，用户知道哪些因子来自未充分验证的 candidate 库。备选 A 减少 UI 复杂度但丢失重要信息 | 推荐：用户决策负担轻微增加（多一列置信度标记）。备选 A：candidate 因子静默通过可能导致测试点质量问题 |
| CP3-DQ-03 | implementation | `mfq/factor-usage/` 目录是否允许 m-analyzer 在不存在时自动创建？（HLD Q3） | **禁止 Agent 自动 mkdir**：遵循 STOP-04 HARD-STOP 协议，目录不存在时输出错误信息终止并提示用户创建 | 备选 A：允许 Agent 自动创建目录 | 推荐方案与现有 STOP-04 协议一致。m-analyzer SKILL.md §步骤 7 已明确"写入前校验父目录存在，禁止 Agent 手动 mkdir"。备选 A 违反现有协议 | 推荐：与 GATE-1 #8（KYM 产物目录就绪检查）一致，目录结构由用户或安装器管理 |

### 推荐决策

- **推荐动作**：`approve`
- **理由**：CR-017 HLD 33/33 自动预检 PASS，场景模拟全部通过，CR intake 3 项决策全部兑现。推荐方案 A 完整修复因子库发现缺口，同时为 CR-016 提供可复用的 Step 1.5 设计模式。3 个待确认问题的推荐方案都与现有 ptm-tde 协议一致（WARNING 不阻断 / 置信度区分 / STOP-04 禁止 mkdir）。

### 备选方案

1. **修改**：`修改: <决策ID>=<具体修改点>` — 调整单项决策
2. **reject**：驳回，需说明驳回范围和原因

### 优劣分析

| 候选方案 | 优势 | 代价 | 适用条件 |
|---|---|---|---|
| 推荐（approve） | 完整修复，33/33 PASS，为 CR-016 铺路 | 3 个 Q 需确认（均为轻量决策） | 用户接受推荐策略 |
| 修改 | 充分保障质量 | 增加修订轮次 | 用户对某个策略有不同偏好 |
| reject | 阻止不成熟设计推进 | 阻塞修复，18 个假阳性持续存在 | 用户认为方案有根本性问题 |

### 影响维度

| 维度 | 评估 |
|---|---|
| 用户价值 | 高：M 分析候选精度从 49% 提升到 >90%，减少下游人工确认负担 |
| 实现复杂度 | 低（纯指令修改，~108 行 SKILL.md 新增） |
| 可验证性 | 高（运行 m-analyzer 后检查 factor-resolution-report.md 扫描库数 = 9） |
| 维护成本 | 低（新增 60 行 m-analyzer 指令，5 个子步骤清晰） |
| 平台兼容 | 不涉及跨平台适配 |
| 安全 / 权限 | 纯本地文件读取，无新增权限需求 |
| 交付影响 | 为 CR-016 提供 Step 1.6 插入点和可复用设计模式 |

### 风险与回退

| 风险 | 等级 | 接受条件 | 回退方式 |
|---|---|---|---|
| candidate 因子未经充分验证被大规模复用 | 中 | match_confidence=medium 标记 + 下游显式确认 | 提升匹配阈值或改为仅 active 可匹配 |
| index.yaml 格式变更 | 低 | 当前格式稳定 | 适配 Step 1.5 解析逻辑 |
| 与 CR-016 同一文件修改冲突 | 低 | 修改不同区域（Step 1.5+2B vs Step 1.6+2C） | CR-016 承担合并适配成本 |

---

## 关闭范围与不授权项

### 关闭范围（CP3 批准后进入 Phase 3 LLD）

- m-analyzer Step 1.5（5 个子步骤：索引读取→遍历加载→状态处理→锁文件→完整性校验）
- m-analyzer Step 2B 修改（match_confidence 分级匹配规则）
- test-point-integrator Step 4.5.1.5（因子库反查去重）
- gate-spec.md GATE-3 M8（因子库扫描完整性检查）
- 后续 CR-016 在此基础上插入 Step 1.6

### 不授权项

- 不授权修改现有因子库文件内容
- 不授权修改 candidate-factor-proposals.yaml 的外部消费格式
- 不授权删除或降级任何现有 candidate 状态因子
- 不授权修改 resource/factor-libraries/index.yaml 中的库状态
- 不授权实现因子库定期同步机制（CR-017 后续台账 T-01）
- 不授权实现 match_confidence 在下游的显式处理 UI（CR-017 后续台账 T-02）
- 不授权 m-analyzer 自动创建 mfq/factor-usage/ 目录（STOP-04 协议）

---

## 回复选项

- `approve` — 接受全部 3 项推荐方案，HLD 进入 approved 状态，推进到 Phase 3 LLD 设计
- `修改: <决策ID>=<具体修改点>` — 调整单项决策
  - 示例：`修改: CP3-DQ-01=改为 HARD-STOP`
- `reject` — 驳回，需说明驳回范围和原因

---

## 人工审查结果

> 以下区域由用户（或用户授权的 meta-po）填写。

| 决策 ID | 用户结论 | 备注 |
|---|---|---|
| CP3-DQ-01（lock 变更策略） | `approved` | 接受推荐：WARNING 不阻断 |
| CP3-DQ-02（medium 置信度展示） | `approved` | 接受推荐：展示但降级提示 |
| CP3-DQ-03（目录创建策略） | `approved` | 接受推荐：保持 STOP-04，目录由主 Agent 初始化流程创建 |

| 字段 | 值 |
|---|---|
| 审查人 | user |
| 审查时间 | 2026-06-06T00:00:00+08:00 |
| 最终结论 | **APPROVED** — CP3 全部 3 项决策 approved。CR-017 HLD 进入 approved 状态，推进到 Phase 3 LLD 设计。 |
| 批准来源 | 用户人工终验对话确认 |
