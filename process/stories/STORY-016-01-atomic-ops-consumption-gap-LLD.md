---
story_id: "STORY-016-01"
title: "m-analyzer 原子操作消费缺口修复 + 语义匹配"
story_slug: "atomic-ops-consumption-gap"
lld_version: "2.0"
tier: "M"
status: "ready-for-review"
confirmed: false
created_by: "meta-dev（lld-designer Skill）"
created_at: "2026-06-06T00:00:00+08:00"
updated_at: "2026-06-06T00:00:00+08:00"
open_items: 0
---

# LLD: STORY-016-01 — 原子操作消费缺口修复

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-06 | meta-dev | 初始 LLD，四维加权分词 + 内嵌同义词表 |
| 2.0 | 2026-06-06 | meta-dev | 迁移到 atomic-ops aliases：五维评分（ALIASES_WEIGHT=1.5），删除硬编码同义词，清理 §7.1 草稿 |

## 1. Goal

在 CR-017 Step 1.5 之后插入 Step 1.6「原子操作清单加载」——运行 `atomic-ops list --format json` 获取全部 79 个操作元数据，构建 op_id 索引。重写 Step 2C 为 L1-L4 四级语义匹配（加权分词重叠算法），消除 `fw_config_subinterface` 等 3 个假阳性候选。建立 `mfq/atomic-op-usage/` 平行跟踪目录。

## 2. Requirements

### 2.1 Functional

- [F1] Step 1.6.1：运行 `atomic-ops list --format json`（支持 --device/--package 过滤）
- [F2] Step 1.6.2：解析 OperationSummary（op_id/description/tags[]/parameters_summary[]/device_type/since_version）
- [F3] Step 1.6.3：构建内存索引 op_id→{description,tags,params_list,device_type}
- [F4] Step 1.6.4：生成/校验 `mfq/atomic-op-usage/atomic-op-lock.yaml`
- [F5] Step 1.6.5：CLI 不可用时降级（回退现有逻辑 + WARNING）
- [F6] Step 2C L1：action_source_ref 精确匹配 → strong-exact-match
- [F7] Step 2C L2：加权分词重叠 ≥6.0 → strong-semantic-match
- [F8] Step 2C L3：加权分词 3.0-5.9 → weak-semantic-match（人工审查）
- [F9] Step 2C L4：<3.0 或 0 匹配 → 候选
- [F10] test-point-integrator Step 7.5.3：原子操作候选交叉验证

### 2.2 Non-Functional

- [NF1] CLI 降级：不可用时 WARNING + 回退现有逻辑，不阻断
- [NF2] 权重可调：算法参数（3.0/1.0/2.0/1.5/6.0）作为常量集中声明
- [NF3] 向后兼容：新增匹配层，不删除现有精确匹配

## 3. 模块拆分

| 模块 | 职责 |
|------|------|
| m-analyzer Step 1.6（新增） | CLI 查询 + JSON 解析 + 索引 + lock |
| m-analyzer Step 2C（重写） | L1-L4 分级语义匹配 |
| m-analyzer Step 7（修改） | 输出 9→10 文件 |
| test-point-integrator Step 7.5.3（新增） | 原子操作候选交叉验证 |
| agents/ptm-tde.md（修改） | 目录布局追加 atomic-op-usage/ |
| gate-spec.md（修改） | GATE-1#3 + GATE-3 M9 |
| data-flow-spec.md（修改） | Entity 8 + 8.8 |

## 4. 文件影响范围

| 动作 | 文件 | 变更 |
|------|------|------|
| 修改 | `skills/m-analyzer/SKILL.md` | 插入 Step 1.6 + 重写 Step 2C + 修改 Step 7 + 更新消费表/Gotchas/验收标准 |
| 修改 | `skills/test-point-integrator/SKILL.md` | 新增 Step 7.5.3 |
| 修改 | `agents/ptm-tde.md` | 目录布局 +atomic-op-usage/ |
| 修改 | `docs/ptm-tde/gate-spec.md` | GATE-1#3 + GATE-3 M9 |
| 修改 | `docs/ptm-tde/data-flow-spec.md` | Entity 8 + 8.8 |

## 5. 数据模型

### 内存索引

```
atomic_ops_index: dict[str, dict]
  key: op_id (str)
  value:
    description: str
    tags: list[str]
    params: list[dict]  # [{name, type, required}]
    device_type: str
    since_version: str
    idempotent: bool
```

### 新增持久化

| 文件 | 格式 | 内容 |
|------|------|------|
| `mfq/atomic-op-usage/atomic-op-lock.yaml` | YAML | CLI 版本快照（commit_sha + total_ops + timestamp） |
| `mfq/atomic-op-usage/atomic-op-bindings.yaml` | YAML | Step 2C 匹配结果（candidate→matched op_id + score） |
| `mfq/atomic-op-usage/atomic-op-resolution-report.md` | 文本 | 匹配统计（精确/强语义/弱语义/候选 各级计数） |

## 6. 接口设计

| 接口 | 输入 | 输出 | 调用方 |
|------|------|------|------|
| `atomic-ops list --format json` | — | 79 个 OperationSummary JSON | m-analyzer Step 1.6.1 |
| Step 1.6 → Step 2C | 内存索引 | 语义匹配查询 | m-analyzer 内部 |
| m-analyzer → integrator | candidate-atomic-ops.yaml | 候选交叉验证 | test-point-integrator 7.5.3 |
| atomic-op-resolution-report → GATE-3 | N_total / N_matched | M9 自检 | checkpoint-manager |

## 7. 核心流程

### 7.1 语义匹配算法（五维加权分词重叠）

```
1. 候选分词：
   按下划线/驼峰/数字边界分词 + 英文词根分解
   词根分解示例：
     subinterface → [sub, interface]
     lag          → [link, aggregation]
     trunk        → trunk（单 token 无分解）

2. 权重参数（可调常量）：
   OP_ID_WEIGHT       = 3.0
   DESC_WEIGHT        = 1.0
   TAGS_WEIGHT        = 2.0
   ALIASES_WEIGHT     = 1.5   # 来自 atomic-ops list --format json
   PARAMS_WEIGHT      = 1.5
   STRONG_THRESHOLD   = 6.0
   WEAK_THRESHOLD     = 3.0

3. 对每个 op_id 计算五维总分：
   op_id_score   = |候选tokens ∩ op_id_tokens| / max(|候选tokens|, |op_id_tokens|) × 3.0
   desc_score    = |候选tokens ∩ desc_tokens|   / max(|候选tokens|, 1) × 1.0
   tags_score    = |候选tokens ∩ tags_tokens|   / max(|候选tokens|, 1) × 2.0
   aliases_score = |候选tokens ∩ aliases_tokens|/ max(|候选tokens|, 1) × 1.5
   params_score  = 参数名命中 / max(1, 候选参数数) × 1.5
   total_score   = op_id_score + desc_score + tags_score + aliases_score + params_score

4. 分级：
   total_score ≥ 6.0 → L2 strong-semantic-match（直接复用）
   3.0 ≤ < 6.0       → L3 weak-semantic-match（人工审查）
   < 3.0             → L4 no-match（生成候选）

5. aliases 数据来源：
   来自 Step 1.6 atomic-ops list --format json 的 aliases 字段，
   由 atomic-ops 仓库统一定义和维护。CR-016 交付时覆盖 32/79 个 op，
   覆盖范围由「有子类型参数 → 必须写 aliases」规则决定。
   单义 op（如 OSPFv2 系列、BFD 系列）无需 aliases。
```

**核心用例验证（真实数据，CR-016 交付时）**：

| 候选 | 最佳匹配 | 得分 | 级别 | aliases 命中 |
|------|---------|:--:|:--:|------|
| `fw_config_subinterface` | `fw_config_interface` | 3.8 | L3-weak | subinterface, interface |
| `fw_config_trunk_interface` | `fw_config_interface` | 3.8 | L3-weak | trunk, interface |
| `fw_config_lag_interface` | `fw_config_interface` | 3.8 | L3-weak | lag, interface |

### 7.2 Step 1.6 流程图

```
Step 1.5（因子库清单加载，CR-017）
         │
         ▼
Step 1.6 🆕 原子操作清单加载
  ├─ 1.6.1: atomic-ops list --format json
  │   失败 → 降级: WARNING + 回退现有逻辑
  ├─ 1.6.2: 解析 JSON → 提取 79 个 OperationSummary（含 aliases）
  ├─ 1.6.3: 构建 op_id → {desc, tags, aliases, params} 索引
  ├─ 1.6.4: atomic-op-lock.yaml 管理
  └─ 1.6.5: CLI 版本信息记录
         │
         ▼
Step 2（含修改后的 Step 2C）
```

## 8. 技术细节

- **分词策略**：下划线/驼峰/数字边界分词 + 英文词根分解（如 subinterface→[sub, interface]、lag→[link, aggregation]）
- **别名数据**：来自 atomic-ops `list --format json` 返回的 `aliases` 字段，由 atomic-ops 仓库统一定义和维护。交付时 32/79 个 op 含 aliases，覆盖 interface/policy_route/nat/object/bandwidth/acl/static_route/black_white_list/batch 族
- **五维权重**：op_id=3.0 / description=1.0 / tags=2.0 / aliases=1.5 / params=1.5，strong_threshold=6.0，weak_threshold=3.0
- **降级兼容**：CLI 不可用时输出 WARNING，Step 2C 回退现有精确匹配逻辑

## 9. 安全与性能

| 维度 | 措施 |
|------|------|
| 安全 | `atomic-ops list` 只读命令；CLI 输出 JSON 解析不执行代码 |
| 性能 | 一次 CLI 调用（~200ms）+ 79 个 op 内存比较 |

## 10. 测试设计

| # | 场景 | 预期 |
|---|------|------|
| T1 | 首次运行，CLI 可用 | 79 op 加载，32 个含 aliases，lock 创建 |
| T2 | "创建子接口" 无 action_source_ref | 五维算法匹配 fw_config_interface，score=3.8 (L3-weak)，aliases 命中 subinterface+interface |
| T3 | "配置 SNAT" 无 action_source_ref | 五维算法匹配 fw_config_nat，aliases 命中 snat → L3-weak |
| T4 | action_source_ref 精确匹配 | L1 strong-exact-match |
| T5 | CLI 不可用 | WARNING + 回退 L1 精确匹配 only |
| T6 | integrator 交叉验证 | 读取 atomic-ops aliases 做反查，正确标记 [已有可覆盖] |

## 11. 实施步骤

| TASK-ID | 动作 | 文件 | 详细描述 |
|---|---|---|---|
| TASK-016-01-01 | 修改 | m-analyzer SKILL.md | 在 Step 1.5 后插入 Step 1.6（5 子步骤） |
| TASK-016-01-02 | 修改 | m-analyzer SKILL.md | 重写 Step 2C 为 L1-L4 四级语义匹配（五维加权分词算法，aliases 维度来自 atomic-ops） |
| TASK-016-01-03 | 修改 | m-analyzer SKILL.md | Step 7 输出 9→10 + 消费表/Gotchas/验收标准更新 |
| TASK-016-01-04 | 修改 | test-point-integrator SKILL.md | 新增 Step 7.5.3 原子操作候选交叉验证 |
| TASK-016-01-05 | 修改 | agents/ptm-tde.md | 目录布局追加 atomic-op-usage/ |
| TASK-016-01-06 | 修改 | gate-spec.md | GATE-1#3 更新 + GATE-3 M9 + 修订记录 |
| TASK-016-01-07 | 修改 | data-flow-spec.md | Entity 8 消费卡片更新 + 新增 8.8 |

## 12. 风险与灰区

| 风险 | 缓解 |
|------|------|
| atomic-ops aliases 未覆盖全部操作（32/79） | 47 个无歧义 op 无需 aliases，按「有子类型参数→必须写 aliases」规则按需补充 |
| 中英文语义鸿沟（候选 op 名来自中文需求推理） | 英文分词 + aliases 覆盖标准术语变体；弱匹配人工审查兜底 |
| 与 CR-017 同一文件修改 | 修改区域不同（Step 1.6+2C vs Step 1.5+2B），顺序推进 |

## 13. 回滚

- **发布**：git commit 5 个产品文件
- **回滚**：`git revert`，回退后行为与当前完全一致（纯精确匹配）

## 14. DoD

- [x] 14 章节完整
- [x] 7 TASK-ID 覆盖 5 文件
- [x] 0 OPEN/Spike
- [ ] confirmed=false 时不实现

## CP5 预检摘要

| # | 检查项 | 状态 |
|---|--------|:--:|
| 1 | LLD 覆盖 AC | 待检查 |
| 2 | HLD 一致 | 待检查 |
| 3 | 文件范围明确 | 待检查 |
| 4 | 接口完整 | 待检查 |
| 5 | 测试可执行 | 待检查 |
| 6 | 0 未决项 | PASS |

## 人工确认区

**回复**：`approve` / `修改: ...` / `reject`

- 结论：`pending` | 审查人： | 审查时间：
