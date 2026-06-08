---
change_id: CR-016-atomic-ops-consumption-gap
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-05T00:00:00+08:00"
created_by: meta-po（po-zhao）
status: closed
approved_at: "2026-06-06T00:00:00+08:00"
closed_at: "2026-06-06T00:00:00+08:00"
impact_level: medium
complexity: standard
rollback_to: story-planning
approval_source: user-request
depends_on:
  - CR-011 (closed, committed)
  - CR-015 (closed, committed)
  - CR-017 (closed, committed: Step 1.5 铺路)
  - atomic-ops P0+P1+P2 (VERIFIED: 79 ops, tags + parameters_summary + aliases; 32/79 ops 含 aliases)
commits:
  - "24c0a0b: 初始实现（5 文件 +192/-18）"
  - "44e8aa1: 切换到 atomic-ops aliases 字段"
  - "f3e7a73: 彻底移除硬编码同义词残留"
cp5_approved: "2026-06-06 (CP5-DQ-01/02/05 all approved)"
cp6: "process/checks/CP6-STORY-016-01-atomic-ops-consumption-gap-CODING-DONE.md (8/8 PASS)"
cp7: "process/checks/CP7-CR-016-global-VERIFICATION-DONE.md (14/14 PASS)"
cross_references:
  - CR-017-factor-library-discovery-gap (同类问题，共享 Step 1.5 资源发现设计模式。CR-017 先启动，CR-016 在此基础上追加 atomic-ops 发现)
---

# CR-016 — m-analyzer 原子操作消费缺口修复

## 变更请求摘要

m-analyzer 在 Step 2C（检查原子操作支撑）声称"消费全局 atomic-ops（全部 op_id）"，但**实际没有任何机制运行 `atomic-ops list`** 查询已有原子操作清单。导致分析过程中将三条实际已存在的原子操作误标为"候选"：

| 候选（误标） | 应映射到 | 原因 |
|---|---|---|
| AO-CAND-005 `fw_config_subinterface` | `fw_config_interface` | params.type 区分 bvi/subinterface/bond |
| AO-CAND-006 `fw_config_trunk_interface` | `fw_config_interface` | params.type 区分 trunk |
| AO-CAND-007 `fw_config_lag_interface` | `fw_config_interface` | params.type 区分 bond |

## 背景与根因

### 四层根因分析

1. **工具链未集成**（设计层）：m-analyzer Step 2C 的消费表（第 141 行）列出"全局 atomic-ops（全部 op_id）"，但只是概念性声明，没有实际 CLI 调用指令
2. **因子 vs 原子操作机制不对等**（架构层）：因子库有完整的三层机制（`mfq/factor-usage/` 下的 lock → bindings → resolution-report），原子操作完全没有对应跟踪
3. **候选生成无回查**（实现层）：`candidate-atomic-ops.yaml` 写入后无后续步骤运行 `atomic-ops list` 做去重
4. **信息不对称**（语义层）：m-analyzer 从场景推理出 `fw_config_subinterface`，但 atomic-ops 库实际用的是统一操作名 `fw_config_interface`

### 关键发现

- m-analyzer Step 2C（SKILL.md 第 186-197 行）的"检查原子操作支撑"逻辑只有两层：直接引用 `action_source_ref`（精确）或标记候选（全部未匹配），**完全没有中间语义匹配层**
- Factor-usage 跟踪目录完整（lock + bindings + resolution-report），atomic-ops 缺少对应的 `mfq/atomic-op-usage/`
- `atomic-ops` CLI 提供 `list --format json`、`show`、`validate` 命令，缓存于 `~/.cache/atomic-ops/repo/`

## atomic-ops CLI 前置依赖（外部仓库）

CR-016 的语义匹配依赖 `atomic-ops list --format json` 提供完整的操作元数据。经分析，当前 `OperationSummary` dataclass 只有 5 个字段，**缺少语义匹配所需的关键维度**：

| 语义匹配维度 | 权重 | 当前 list 输出 | 缺失影响 |
|------------|:----:|:------------:|---------|
| `op_id` 分词 | 3.0 | ✅ | — |
| `description` 分词 | 1.0 | ✅ | — |
| `tags` 分词 | 2.0 | ❌ | 权重第二高的维度完全缺失，无法区分同类操作 |
| `parameters` 名/类型 | 1.5 | ❌ | 无法利用参数信息辅助匹配（如 `type: subinterface/bond/bvi`） |

**结论**：若不修复，m-analyzer 每次语义匹配需为 74 个 op 逐条调用 `atomic-ops show`，极不经济且不可靠。

### 需要 atomic-ops 仓库完成的改动（P0+P1，~25 行）

| 优先级 | 改动 | 文件 | 工作量 |
|:---:|------|------|:---:|
| P0 | `OperationSummary` 增加 `tags: list[str]` 字段 | `src/atomic_ops/repository.py` | ~10 行 |
| P1 | `OperationSummary` 增加 `parameters_summary: list[dict]`（含 `name/type/required`） | `src/atomic_ops/repository.py` | ~15 行 |

P0+P1 落地后，CR-016 的 m-analyzer 一次 `list --format json` 即可覆盖全部四维评分（权重合计 7.5），仅弱匹配候选（3.0-5.9 分）需按需调用 `show` 查参数描述做最终验证。

### 降级兼容

若 atomic-ops 尚未完成 P0+P1，m-analyzer 仍可降级工作：
- 用当前 `list`（只有 op_id + description）做粗筛 → 对所有候选逐条 `show` 拿 tags + parameters → 再做完整评分
- 降级模式下候选误标风险升高（tags 权重 2.0 缺失），但不会阻断流程

**本 CR 以 atomic-ops P0+P1 完成为启动前提**（见下方执行时间线）。

## 五维度影响分析

### 1. 需求影响

| 维度 | 影响 |
|------|------|
| 现有需求 | 不变。m-analyzer 的功能定位不变（MFQ 分析中的 M 分析器），本次只修正已有声明但未实现的消费契约 |
| 新增需求 | 隐式新增：m-analyzer 须能从 CLI 查询真实 atomic-ops 清单并做语义匹配 |
| 需求冲突 | 无 |

### 2. 设计影响

| 维度 | 影响 |
|------|------|
| 架构决策 | 新增设计与现有架构一致的机制：atomic-op-usage 跟踪目录与 factor-usage 平行但独立 |
| HLD 影响 | 不改变 HLD（M/F/Q 分析的职责边界不变），但需要更新 data-flow-spec.md（Entity 8 消费卡片）和 gate-spec.md（GATE-1 #3 + GATE-3 M8） |
| ADR 影响 | 新增一条设计决策：语义匹配用加权分词重叠，不用 embedding |

### 3. Story/实现影响

| 维度 | 影响 |
|------|------|
| 受影响文件 | 5 个（详见下方） |
| Story 拆解 | 按 Phase 拆为 3-4 个 Story（P0 主修复 + P1 跟踪机制 + P1 交叉验证 + P2 规范更新），1-2 Waves |
| 实现复杂度 | 中。核心难点在语义匹配算法的可调参设计和同义词表维护 |

### 4. 安全/权限影响

| 维度 | 影响 |
|------|------|
| CLI 调用 | 新增 `atomic-ops list --format json` 和 `atomic-ops show` 调用，均为只读命令 |
| 目录创建 | 新增 `mfq/atomic-op-usage/` 子目录，权限与现有 `mfq/` 一致 |
| 风险 | CLI 不可用时优雅降级（回退现有逻辑 + WARNING 输出），无阻断风险 |

### 5. 交付影响

| 维度 | 影响 |
|------|------|
| 安装器 | 不变（atomic-ops CLI 已在 GATE-1 #3 中作为先决条件检查） |
| 文档 | 更新 gate-spec.md（GATE-1 #3 + GATE-3 新增 M8）和 data-flow-spec.md（Entity 8 + 新增 8.8） |
| 向后兼容 | 完全兼容。CLI 可用时启用新逻辑，不可用时回退现有逻辑 |

## 修改文件清单

| 优先级 | 文件 | 变更范围 | 预计行数 |
|--------|------|---------|---------|
| P0 | `skills/m-analyzer/SKILL.md` | Pre-2C 步骤新增 + Step 2C 重写（分级匹配 C1-C4）+ 输出文件 8→9 + Gotchas/验收标准更新 | ~120 行 |
| P1 | `skills/test-point-integrator/SKILL.md` | Step 7.5.3 新增（原子操作候选交叉验证）+ atomic-op-bindings 写入 + Gotchas 更新 | ~60 行 |
| P1 | `agents/ptm-tde.md` | 目录布局增加 `mfq/atomic-op-usage/` | ~10 行 |
| P2 | `docs/ptm-tde/gate-spec.md` | GATE-1 #3 更新（记录 CLI 版本和 cache 状态）+ GATE-3 新增 M8 检查项 | ~15 行 |
| P2 | `docs/ptm-tde/data-flow-spec.md` | Entity 8 消费卡片更新（增加 CLI 查询字段）+ 新增 8.8 小节 | ~30 行 |

### 文档处理决策

| 受影响文档 | 决策 | 说明 |
|-----------|------|------|
| `skills/m-analyzer/SKILL.md` | 原文档增量更新 | 保留现有 v3.0 结构，追加修订记录 |
| `skills/test-point-integrator/SKILL.md` | 原文档增量更新 | 在 Step 7.5 后追加 7.5.3 |
| `agents/ptm-tde.md` | 原文档增量更新 | 目录树中追加 atomic-op-usage 子目录 |
| `docs/ptm-tde/gate-spec.md` | 原文档增量更新 | 追加修订记录，更新 GATE-1 #3 和 GATE-3 |
| `docs/ptm-tde/data-flow-spec.md` | 原文档增量更新 | 追加修订记录，更新 Entity 8 和新增 8.8 |

## 复杂度判定

**判定：standard**。不满足 fast-lane 条件：

- 涉及 5 个产品文件（>2）
- 引入新机制（atomic-ops CLI 查询、加权分词语义匹配、atomic-op-usage 跟踪目录）
- 跨 Skill 协调（m-analyzer + test-point-integrator）
- 修改架构文档（gate-spec.md + data-flow-spec.md）
- 新增 mfq/ 子目录结构

## 文件所有权冲突分析

当前存在两个未提交 CR 与 CR-016 的文件目标重叠：

| CR | 状态 | 与 CR-016 重叠文件 |
|----|------|-------------------|
| CR-011 | closed，待 CP8 人工终验 + commit | `agents/ptm-tde.md`、`docs/ptm-tde/gate-spec.md`、`docs/ptm-tde/data-flow-spec.md` |
| CR-015 | active，fast-lane，待 CP8 人工终验 + commit | `skills/test-point-integrator/SKILL.md`、`agents/ptm-tde.md` |

**推荐策略**：先完成 CR-011 和 CR-015 的 CP8 人工终验并 commit 基线，再将 CR-016 基于最新基线启动。此策略避免了 CR-on-CR 的复杂合并和文件冲突协调。

**备选 A**：CR-016 基于当前 working tree（含 CR-011 + CR-015 未提交变更）启动。需人工确认合并策略并增加文件所有权协调步骤。

**备选 B**：单独抽出无冲突的 P0 文件（`skills/m-analyzer/SKILL.md`）作为 CR-016-A fast-lane 先行修复，P1/P2 等 CR-011/CR-015 提交后再推进。

## 执行时间线

| 步骤 | 动作 | 阻塞条件 |
|------|------|---------|
| 0 | **atomic-ops 仓库完成 P0+P1**（`list --format json` 增加 `tags` + `parameters_summary`） | ⛔ CR-016 启动硬前置 |
| 1 | 用户完成 CR-011 + CR-015 CP8 人工终验，commit 基线 | ⛔ CR-016 启动前提 |
| 2 | 启动 CR-016：Phase 2 HLD 设计（meta-se，CP3 自动预检 + 人工确认） | |
| 3 | HLD 通过后：Story 拆解 + Wave 计划 + CP4 自动预检 | |
| 4 | 全量 LLD 并行设计 + CP5 全量自动预检 + CP5 全量人工确认 | |
| 5 | Wave 编排实施 + CP6/CP7 滚动 | |
| 6 | 交付文档更新 + CP8 自动预检 + 人工终验 | |

## 验证方法

详见计划文件 `/home/hyde/.claude/plans/atomic-ops-fw-config-interface-swift-abelson.md` 的「验证方法」章节。

关键验证点：
1. 创建含"创建子接口"步骤的测试场景（无 `action_source_ref`），验证 m-analyzer 正确匹配 `fw_config_interface` 为 `strong-semantic-match` 且不生成 AO-CAND-005
2. 验证 `mfq/atomic-op-usage/` 下三个文件正常生成
3. 验证 test-point-integrator Step 7.5.3 交叉验证正确标记候选覆盖

---

## Decision Brief（CR intake）

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| CR016-DQ-01 | scope | 是否批准启动 CR-016（standard 模式） | **approve**：批准 CR-016 启动，进入 Phase 2 HLD 设计。推荐先完成 CR-011 + CR-015 CP8 终验和 commit，再以干净基线启动 | 备选 A：基于当前 working tree（含未提交 CR-011/CR-015 变更）直接启动 | 推荐方案文件所有权清晰，无合并风险，但需等待用户完成两个 CP8 终验。备选 A 可立即启动，但需处理 4 个文件的未提交变更冲突 | 推荐：中等（等待两个 CP8 终验，预计 1 轮确认）。备选 A：中高（需额外文件所有权协调和合并步骤） |
| CR016-DQ-02 | architecture | 语义匹配算法阈值设计：加权分词重叠 vs embedding | **推荐方案 A**：加权分词重叠（op_id 权重 3.0 + description 1.0 + tags 2.0 + params 1.5），阈值 ≥6.0 强匹配，3.0-5.9 弱匹配 | 备选 B：基于 embedding 向量相似度 | 推荐方案：轻量、可解释、无额外依赖，但依赖同义词表质量。备选 B：语义理解更准确，但增加模型依赖和延迟，对短操作描述收益不明显 | 实现复杂度：推荐低，备选中。可验证性：推荐高（阈值可调），备选低（黑盒）。维护成本：推荐需维护同义词表，备选需维护模型 |
| CR016-DQ-03 | architecture | 原子操作跟踪目录（`mfq/atomic-op-usage/`）是否与 factor-usage 完全平行 | **推荐方案 A**：完全平行（独立 lock + bindings + resolution-report），文件格式仿照 factor-usage 但独立维护 | 备选 B：合并到 factor-usage 目录（factor-usage/ 同时跟踪因子和原子操作） | 推荐方案：职责清晰，因子和原子操作是完全不同类型的资产。备选 B：减少目录数但语义混合 | 推荐：设计清晰但增加一个子目录。备选 B：看似简洁但因子和原子操作的状态生命周期不同，混合维护反而增加复杂度 |
| CR016-DQ-04 | follow_up_tracking | P2 阶段的 Gate Spec 和 Data Flow Spec 更新是否纳入 CR-016 范围 | **推荐方案 A**：纳入 CR-016 范围，作为 P2 Wave 的最后一步 | 备选 B：延迟到独立 CR 或后续台账跟踪 | 推荐方案：P2 修改量小（~45 行），文档更新与代码修改同步完成，交付完整。备选 B：减少 CR-016 范围，但文档与行为不一致的窗口期较长 | 推荐：P2 只是规范对齐工作，修改量小，纳入主 CR 避免后续碎片化 CR |

### 不授权项

- 不授权修改 `mfq/factor-usage/` 目录结构或文件格式
- 不授权修改 `candidate-atomic-ops.yaml` 的外部消费格式（仅内增 `match_attempt` 元数据）
- 不授权在 CLI 不可用时阻断流程（必须优雅降级）
- 不授权修改除上述 5 个文件外的任何产品文件

### 风险与回退

| 风险 | 等级 | 缓解 | 回退路径 |
|------|------|------|---------|
| 语义匹配假阳性 | 高 | 弱匹配（3.0-5.9）标记人工审查；atomic-ops show 验证后提升 | 调整匹配阈值；回退到 action_source_ref 模式 |
| 语义匹配假阴性 | 中 | 同义词表可扩展；integrator 交叉验证二次把关 | 同现有行为（生成候选），不劣化 |
| CLI 不可用 | 低 | 回退现有逻辑 + 输出 WARNING | 无影响（完全向后兼容） |
| 中英文语义鸿沟 | 低-中 | 同义词表覆盖最常见领域映射，可迭代 | 扩展同义词表 |
| 文件所有权冲突 | 中 | 先完成 CR-011 + CR-015 commit | 若选择备选 A，需增加文件协调步骤和 merge owner 指定 |

### 后续 CR 候选

| 编号 | 描述 | 优先级 | 状态 |
|------|------|--------|------|
| T-01 | 同义词表扩展为独立配置文件（`resource/atomic-op-synonyms.yaml`），支持用户自定义 | P2 | candidate |
| T-02 | `atomic-ops show` 结果缓存，减少重复 CLI 调用 | P2 | candidate |
| T-03 | integrator 交叉验证的语义匹配与 m-analyzer 共享同一匹配函数（抽取到共享模块） | P3（重构） | candidate |

---

## 参考

- 计划文件：`/home/hyde/.claude/plans/atomic-ops-fw-config-interface-swift-abelson.md`
- 问题工作流：WF-PTM-TEAM-20260520-001
- 关联 CR：CR-011（KYM 阶段，closed）、CR-015（AskUserQuestion，active）
- 关键文件：`skills/m-analyzer/SKILL.md` Step 2C（第 186-197 行 + 消费表第 141 行）
