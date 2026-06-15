---
name: m-analyzer
description: >-
  M 分析 v3.0（MD: Model-based Discrete Function）：按场景步骤驱动发现测试对象与因子，
  逐步骤评估关联度、匹配公共因子库、检查原子操作支撑、打场景步骤标签（[M]/[F→]/[Q→]），
  生成 Scenario-TSP 覆盖矩阵、TSP 描述（含 covered_scenario_segments + f_tags + q_tags）、
  PPDCS 特征标注和按关联度分级的 CAE 测试点，输出因子候选与原子操作候选列表。
  触发词包括：M分析、功能分析、模块分析、测试点分析、PPDCS标注。
  适用场景：MFQ 分析的第三步（m-analysis 阶段）。
argument-hint: "无需参数，自动读取 kym/ 和 mfq/ 目录"
user-invokable: true
status: active
---

## 目标

基于 KYM 阶段产出的结构化需求、已确认目录、已确认场景和 mission-statement，
**逐场景步骤驱动**发现测试对象与测试因子，评估对象关联度（高/中/低），匹配公共因子库（已有 vs 候选），
检查原子操作支撑（已有 vs 候选），对每个场景步骤打标签 `[M]` / `[F→]` / `[Q→]`，
建立 Scenario-TSP 覆盖矩阵，为每个单功能标注 PPDCS 主特征，
按对象关联度分级生成带 trace chain v6 的 CAE 测试点，
输出因子候选和原子操作候选列表供下游消费。

## 理论基础

M 分析即 MFQ 框架中的 **MD（Model-based Discrete Function）**：
> 将被测对象细分为可独立测试的单功能，使用 PPDCS 模型分析每个单功能的内在逻辑特征。

**PPDCS 五特征**（来源：《海盗派测试分析》P183-199）：

| 特征 | 识别条件 | 对应建模技术 |
|------|---------|-------------|
| **P-Process** | 需求有业务流程含义，多步骤有序约束 | 流程图/活动图 |
| **P-Parameter** | 参数参与业务规则判定，输入组合影响输出 | 判定表/因果图 |
| **D-Data** | 数据有明确取值范围，各数据项相对独立 | 等价类 + 边界值 |
| **C-Combination** | 多因子多状态，全组合不可枚举 | Pairwise/正交 |
| **S-State** | 对象有多状态可互转，存在状态生命周期 | 状态图/转换表 |

**区分规则**：
- Process vs State → 流程能否回退？不能 = Process，可以 = State
- Parameter vs Data → 参数间有业务规则？有 = Parameter，无/独立 = Data
- Data vs Combination → 因子独立验证够？够 = Data，需组合 = Combination

**MFQ 分层概念（强制）**：
- **测试因子**：只表示业务取值、配置取值、数据取值或报文取值，例如协议类型、端口号取值、状态枚举、阈值、字段值。
- **拓扑角色**：只表示测试逻辑位置，例如匹配流量入口、DUT 出口、流量发生端、观测端；CAE 中可写成 `{{topo_role:MATCH_INGRESS_IF}}`。
- **真实组网对象**：只表示 `kym/scenarios/confirmed-scenarios.md` 中已确认的 TOPO 实例，例如具体 DUT/TG/接口/link 绑定。

测试因子、拓扑角色、真实组网对象必须分层输出。禁止把 `DUT.port1`、`TG.port1`、link 实例或任何真实端口写成 factor value。

## 适用范围

- 适用阶段：MFQ 分析的 m-analysis 阶段（v3.0 场景步骤驱动模式）
- 输入路径：
  - `kym/feature-input/` + `kym/scenarios/confirmed-scenarios.md`
  - `kym/mission-understanding/mission-statement.md`
  - 公共因子库（`mfq/factor-usage/`）
- 输出路径（全部写入 `mfq/m-analysis/`）：
  - `test-points.md`、`ppdcs-annotation.md`、`test-objects-factors.md`
  - `scenario-tsp-coverage.md`（v3.0 新增：覆盖矩阵 + 标签汇总）
  - `tsp/<M编号>-tsp.md`（v3.0 新增：每个 M 的 TSP 描述）
  - `factor-resolution-report.md`
  - `candidate-factor-proposals.yaml`（v3.0 新增：因子候选列表）
  - `candidate-ptm-atomic.yaml`（v3.0 新增：原子操作候选列表）

## 前置条件

- [ ] `kym/feature-input/raw-requirements.md` 存在
- [ ] `kym/feature-input/directory-structure.md` 存在（用户已确认）
- [ ] `kym/scenarios/confirmed-scenarios.md` 存在（用户已确认）
- [ ] `kym/mission-understanding/mission-statement.md` 存在（KYM 产出可用）
- [ ] 全局 ptm-atomic 可用（GATE-1 #3 检查）
- [ ] 若 `confirmation_gaps` 仍存在，已明确哪些 gap 可继续下游透传，哪些必须先回到场景确认

⛔ **HARD-STOP（STOP-03）**：禁止 Agent 绕过本 Skill 直接生成 M 分析产物。M 分析必须通过 m-analyzer Skill 调用执行。不得跳过子步骤 A/B/C/D 中的任一步，不得使用旧版 v2.0 的"逐模块功能分析"模式替代场景步骤驱动模式。

## 场景输入契约（trace chain v6）

M 分析必须消费以下上游字段，不再假设"只有场景标题 + 简述"：

| 上游字段 | 用途 | 缺失处理 |
|------|------|------|
| `Scenario Chain` | 生成 TP 的场景上下文与最小逻辑链骨架 | 不得脑补，输出 `[待确认]` 并挂 `confirmation_gap_refs` |
| `precondition_operations` | 生成 C 条件与前置动作 trace | 缺失时仅保留已确认前置，不得伪造操作 |
| `atomic_operations` | 生成 A 动作、动作顺序和 `scenario_chain_refs` | 缺失时不得把"功能描述"直接当成可执行动作 |
| `ptm-atomic` | 关联 `action_source_refs`，识别 ptm-atomic `op_id` 依赖 | 若原子操作契约不清，仅标记 `unknown/gap` |
| `minimal_logic_chain` | 逻辑链步骤序列，逐步骤扫描的核心输入 | 缺失时场景步骤不完整，标记 `confirmation_gap_refs` |
| `observation_targets` | 附加到步骤上的观察点，辅助对象关联度判定 | 缺失时仅基于步骤描述判定 |
| `Knowledge Reference` | 记录需求/场景依据来源 | `missing/unavailable` 必须保留原状态 |
| `Existing Tool Usage Seed` | 保留已有工具线索供后续 F/Q/Integrator 使用 | 没有则留空，不做默认映射 |
| `Tool Abstraction Draft` | 标记能力缺口背景 | 仅引用已确认草案 |
| `confirmation_gaps` | 显式透传不确定事实 | 不得静默吞掉 |
| `TOPO` / 组网实例 | 为 CAE 拓扑角色提供可回链的真实绑定依据 | 只能引用 confirmed-scenarios.md 中已确认实例；缺失或不唯一时写入 `topology_gap_refs` |

## 执行流程

### 步骤 1：加载输入

**📥 消费**：

| 文件 | 消费字段 | 用途 |
|------|---------|------|
| `kym/feature-input/raw-requirements.md` | 全文 | 需求条目列表 |
| `kym/feature-input/directory-structure.md` | 四/五级目录层级 | 分析范围。**目录划分来源优先级**：① `resource/coupling-matrix/tgfw-feature-tree.yaml`（或 `~/.ptm-team/resource/coupling-matrix/`）匹配 → ② 模型推理生成（标记 `source: model-inference`） |
| `kym/scenarios/confirmed-scenarios.md` | Scenario Chain / precondition_operations / atomic_operations / minimal_logic_chain / observation_targets / Knowledge Reference / TOPO | 场景上下文与步骤序列 |
| `kym/mission-understanding/mission-statement.md` | `test_items.items` + `dont_test` | M 识别边界 |
| | `risks[].area` + `likelihood` + `impact` | 风险预填（步骤 5 用） |
| | `downstream_guidance.mfq.suggested_m_granularity` | M 拆分粒度建议 |

**🔄 处理逻辑**：

```
1. 读取需求条目，建立「需求条目 → 目录节点」的映射
2. 读取目录层级，获得分析范围（按四级→五级展开）
3. 读取场景链，将每个场景展开为操作步骤序列：
   - 提取 precondition_operations（前置步骤）
   - 提取 atomic_operations（执行步骤）
   - 提取 minimal_logic_chain（逻辑链）
   - 提取 observation_targets（观察点）
   - 按原始顺序拼接：precondition_ops → ptm_atomic → logic_chain
   - 为每个步骤分配 step_index（场景内顺序号）
4. 建立 scenario_ref → topology_refs → topology_role_refs 的可追溯索引
5. 校验每个场景是否包含必需的场景链、ptm-atomic、知识引用
6. 对影响后续分析的未确认事实，建立 confirmation_gap_refs 和 topology_gap_refs
7. 读取 mission-statement 的 test_items / dont_test / risks 用于后续边界判定
```

### 步骤 1.5：因子库清单加载

> 在进入因子匹配之前，先发现全部已注册因子库、加载所有因子到内存索引、管理 lock 文件、校验扫描完整性。

**📥 消费**：

| 消费数据 | 字段 | 用途 |
|---------|------|------|
| `$PTM_TEAM_RESOURCE_HOME/factor-libraries/index.yaml` → `~/.ptm-team/resource/factor-libraries/index.yaml` → `resource/factor-libraries/index.yaml` | libraries[].library_id / status / path / version | 库注册清单 |
| `$PTM_TEAM_RESOURCE_HOME/component-resource-links.yaml` → `~/.ptm-team/resource/component-resource-links.yaml` → `resource/component-resource-links.yaml` | library_id / install_policy | 确认全量消费意图 |
| 各库 `factor-library.yaml` | factors[].factor_id / factor_name / aliases / owner_object / factor_group / status | 因子定义 |

**🔄 处理逻辑**：

```
【1.5.1 读取库索引】
1. 按 `$PTM_TEAM_RESOURCE_HOME/factor-libraries/index.yaml` → `~/.ptm-team/resource/factor-libraries/index.yaml` → `resource/factor-libraries/index.yaml` 顺序读取库索引 → 获取全部已注册库的 library_id / status / path / version
2. 按 `$PTM_TEAM_RESOURCE_HOME/component-resource-links.yaml` → `~/.ptm-team/resource/component-resource-links.yaml` → `resource/component-resource-links.yaml` 顺序读取组件资源链接 → 确认 ptm-tde 组件的 library_id=all、install_policy=required
3. 记录 N_registered = index.yaml 中的库数量

【1.5.2 遍历加载各库】
1. 对索引中的每个库（无论 status=active 还是 candidate）：
   a. 进入子目录 <library_path>/，加载 factor-library.yaml
   b. 解析所有 factor：factor_id / factor_name / aliases / owner_object / factor_group / status
   c. 写入内存索引：factor_id → {library_id, library_status, factor_status, factor_group, ...}
2. 单个库 factor-library.yaml 不存在或解析失败 → ⚠️ WARNING（记录库名和错误原因），跳过该库，继续下一库
3. 全部库解析失败（成功加载数为 0）→ ⛔ 硬错误阻断："无法加载任何因子库，请检查 resource/factor-libraries/ 目录"

【1.5.3 candidate 状态处理】
1. library_status=candidate 的库 → 库中所有因子标记 match_confidence=medium
2. factor_status=candidate 的因子（在 active 库中） → 标记 match_confidence=medium
3. factor_status=active 的因子 → 标记 match_confidence=high
4. 区分逻辑：candidate 不是"跳过"，而是"可匹配但下游需显式确认"

【1.5.4 Lock 文件管理】
1. 检查 mfq/factor-usage/factor-library-lock.yaml 是否存在
2. 若不存在 → 创建之，记录当前所有库的 library_id / version / status / factor_count
3. 若已存在 → 校验一致性：逐库比对 library_id + version
   - 一致 → OK
   - 不一致（新增库 / 版本变化 / 库被移除）→ ⚠️ WARNING："factor-library-lock.yaml 与 index.yaml 不一致：<差异列表>"，继续执行
4. 写入前校验：mfq/factor-usage/ 父目录存在且为目录（非普通文件）；目录不存在时输出错误信息并终止（遵循 STOP-04 协议，禁止 Agent mkdir）

【1.5.5 扫描完整性校验】
1. 计算 N_scanned = 成功加载的库数量
2. 比较 N_scanned vs N_registered（来自 Step 1.5.1）
3. N_scanned == N_registered → ✅ PASS，进入 Step 2
4. N_scanned < N_registered → ⛔ HARD-STOP 阻断：
   "因子库扫描不完整: 成功加载 {N_scanned}/{N_registered} 个库，缺少：{未加载的库名列表}"
```

**📤 生产**：

| 产出 | 内容 |
|------|------|
| 内存索引 | factor_id → {library_id, library_status, library_display_name, factor_status, factor_name, aliases, owner_object, factor_group, match_confidence} |
| `mfq/factor-usage/factor-library-lock.yaml` | 运行时因子库版本快照（锁定当前加载的库列表和版本） |
| 扫描完整性校验结果 | N_scanned + 校验结论（PASS / HARD-STOP） |

### 步骤 1.6：原子操作清单加载

> 在进入原子操作支撑检查之前，查询 ptm-atomic CLI 获取全部已有操作的完整元数据，构建 op_id 索引。复用 Step 1.5 的资源发现模式。

**📥 消费**：

| 消费数据 | 来源 | 用途 |
|---------|------|------|
| ptm-atomic CLI | `ptm-atomic list --format json` | 获取全部 79 个 OperationSummary（op_id/description/tags/parameters_summary/device_type） |
| GATE-1 #3 检查结果 | checkpoint-manager | 确认 CLI 可用性 |

**🔄 处理逻辑**：

```
【1.6.1 运行 CLI 查询】
1. 执行 ptm-atomic list --format json
2. 若命令不存在或返回非零 → 降级处理（见 1.6.5）
3. 解析 JSON → 提取 operations[] 数组，记录 total_ops = len(operations)

【1.6.2 解析操作元数据】
对每个 OperationSummary 提取：
  - op_id（主键）
  - description
  - tags[]（如 ["firewall","capacity","interface","configuration"]）
  - aliases[]（如 ["subinterface","trunk","lag","bond","bvi"]）— 操作的业务别名，来自 ptm-atomic 仓库定义
  - parameters_summary[]（每项含 name/type/required）
  - device_type
  - since_version
  - idempotent

【1.6.3 构建内存索引】
1. 构建 op_id → {description, tags[], aliases[], params[name,type], device_type, since_version} 的字典索引
2. 为所有 op_id 预计算分词结果（按下划线/驼峰/数字边界分词 + 英文词根分解），aliases 中的每个值也分词后加入该 op 的 token 集合

【1.6.4 Lock 文件管理】
1. 检查 mfq/ptm-atomic-usage/ptm-atomic-lock.yaml 是否存在
2. 若不存在 → 创建，记录 CLI commit_sha + total_ops + timestamp
3. 若存在 → 校验一致性（比较 commit_sha 和 total_ops）
   - 一致 → OK
   - 不一致 → ⚠️ WARNING："ptm-atomic 版本已变更（旧: X ops @ sha1，新: Y ops @ sha2）"，继续
4. 写入前校验：mfq/ptm-atomic-usage/ 父目录存在且为目录（遵循 STOP-04）

【1.6.5 CLI 不可用降级】
1. ptm-atomic 命令未安装或执行失败：
   → ⚠️ WARNING："ptm-atomic CLI 不可用，原子操作支撑检查将仅使用精确匹配（action_source_ref）"
   → Step 2C 回退到现有逻辑（L1 精确匹配 only，L2-L4 跳过）
   → 不阻断流程
```

**📤 生产**：

| 产出 | 内容 |
|------|------|
| 内存索引 | op_id → {description, tags[], params[], device_type, since_version} |
| `mfq/ptm-atomic-usage/ptm-atomic-lock.yaml` | CLI 版本快照（commit_sha + total_ops + timestamp） |

### 步骤 2：场景步骤驱动的对象与因子发现

> 这是 M 分析最核心的步骤。逐场景、逐步骤扫描，在每一步中发现测试对象、测试因子和原子操作依赖，
> 区分"已有"和"候选"两类产出，打场景步骤标签，建立 Scenario→TSP 覆盖映射。

**📥 消费**：

| 消费数据 | 字段 | 用途 |
|---------|------|------|
| 步骤 1 的场景步骤序列 | precondition_operations / atomic_operations / minimal_logic_chain | 逐步骤扫描 |
| 步骤 1 的需求映射 | 需求条目 → 目录节点 | 判定步骤归属的子模块 |
| `confirmed-scenarios.md` | knowledge_ref / action_source_ref | 追溯来源 |
| 公共因子库 | factor_id / factor_name / aliases / owner_object | 匹配已有因子 |
| 全局 ptm-atomic | 全部 op_id | 匹配已有原子操作 |

**🔄 处理逻辑**：

```
对每个已确认的场景（Scenario Chain）：
  对场景中的每个操作步骤（precondition_operations + atomic_operations + minimal_logic_chain）：

    【子步骤 A：识别测试对象】
    1. 从步骤描述中识别操作目标（配置项、数据实体、协议报文、状态机、接口等）
    2. 判断该目标是否可作为一个"测试对象"：可独立配置/操作？可独立观测其状态变化？
       否 → 跳过，继续下一对象
    3. 评估该对象与当前特性的关联度：

       | 判定维度 | 高关联 | 中关联 | 低关联 |
       |---------|--------|--------|--------|
       | 操作频率 | 每个场景路径都操作该对象 | 部分场景操作该对象 | 仅初始化/清理时使用 |
       | 结果影响 | 对象状态直接决定测试结果 | 对象影响局部行为 | 对象不影响测试判定 |
       | 可替代性 | 不可替代 | 可部分替代（默认值） | 完全可替代 |
       | 需求明确度 | SR 明确描述该对象的预期行为 | SR 提及但未详述 | SR 未单独提及 |

       综合判定：满足 ≥2 条的高关联条件 → 高关联；满足 ≥2 条的低关联条件 → 低关联；其余 → 中关联。

       处理策略：
       - 高关联 → 标记为"已确认对象"，必须生成测试点（正常+边界+异常）
       - 中关联 → 标记为"已确认对象"，选择性生成测试点（至少正常功能）
       - 低关联 → 记录但不生成 M 测试点，供 F 分析参考
    4. 记录：object_id / object_name / object_type / 关联度 + 判定理由 /
       observation_targets / scenario_refs

    【子步骤 B：发现/匹配测试因子】
    1. 从该步骤的操作参数、输入数据、前置条件中提取候选因子：
       - 配置参数（IP、端口、协议类型、阈值...）
       - 数据字段（报文内容、字段值、编码格式...）
       - 状态值（ON/OFF、active/standby...）
       - 约束条件（数量上限、时间窗口...）
    2. 在公共因子库中检索每个候选因子（使用 Step 1.5 内存索引）：
       查找来源：Step 1.5 构建的内存索引（已覆盖全部已注册因子库）
       按 factor_id / factor_name / aliases / owner_object 检索
       - 命中 active 因子 → 标记为"已有因子"（source=public-library，match_confidence=high），直接复用
         · 如值域/样本/约束不足 → 记录扩展建议
       - 命中 candidate 因子 → 标记为"已有因子"（source=public-library，match_confidence=medium），复用但下游需显式确认
         · 如值域/样本/约束不足 → 记录扩展建议，同时标记"candidate 库因子，建议验证后使用"
       - 未命中 → 标记为"因子候选"（source=new-candidate），加入候选列表
    3. 记录：factor_id / factor_name / source_section（precondition/action-input/observation）/
       data_domain / related_object_id / source（public-library/new-candidate）/ match_confidence（high/medium/—） / scenario_refs

    【子步骤 C：检查原子操作支撑（L1-L4 分级语义匹配）】

    > 使用 Step 1.6 构建的 ptm-atomic 内存索引，对每个操作步骤执行四级匹配。

    **匹配分级规则**：

    | 级别 | 名称 | 条件 | 处理 | 置信度 |
    |------|------|------|------|:--:|
    | L1 | strong-exact-match | 步骤的 action_source_ref 精确等于某个 op_id | 直接引用，无需语义匹配 | confirmed |
    | L2 | strong-semantic-match | 语义匹配总分 ≥ 6.0 | 视为"已有原子操作"，直接引用 | high |
    | L3 | weak-semantic-match | 语义匹配总分 3.0-5.9 | 标记为"原子操作候选"但记录最佳匹配 op_id 和 score，供人工审查 | medium |
    | L4 | no-match | 总分 < 3.0 或 CLI 不可用 | 生成"原子操作候选" | low |

    **语义匹配算法（加权分词重叠）**：

    ```
    1. 候选分词：
       将步骤描述中的操作名称按 下划线/驼峰/数字边界 分词
       对每个 token 做英文词根分解（如 subinterface→[sub, interface]、lag→[link, aggregation]）
       词根分解可参考 Step 1.6 中目标 op 的 aliases 分词结果反向匹配

    2. 权重参数（可调常量）：
       OP_ID_WEIGHT       = 3.0   # op_id 分词命中权重
       DESC_WEIGHT        = 1.0   # description 分词命中权重
       TAGS_WEIGHT        = 2.0   # tags 命中权重
       PARAMS_WEIGHT      = 1.5   # 参数名命中权重
       ALIASES_WEIGHT     = 1.5   # aliases 分词命中权重（来自 ptm-atomic 定义）
       STRONG_THRESHOLD   = 6.0   # 强匹配阈值
       WEAK_THRESHOLD     = 3.0   # 弱匹配阈值

    3. 对索引中的每个 op_id 计算五维总分：
       op_id_score   = |候选tokens ∩ op_id_tokens| / max(|候选tokens|, |op_id_tokens|) × 3.0
       desc_score    = |候选tokens ∩ desc_tokens| / max(|候选tokens|, 1) × 1.0
       tags_score    = |候选tokens ∩ tags_tokens| / max(|候选tokens|, 1) × 2.0
       aliases_score = |候选tokens ∩ aliases_tokens| / max(|候选tokens|, 1) × 1.5
       params_score  = |候选参数名 ∩ op.params[].name| / max(1, |候选参数|) × 1.5
       total_score   = op_id_score + desc_score + tags_score + aliases_score + params_score

    4. 取 total_score 最高的 op_id 作为最佳匹配：
       - 若最高分 ≥ STRONG_THRESHOLD → L2（strong-semantic-match）
       - 若 WEAK_THRESHOLD ≤ 最高分 < STRONG_THRESHOLD → L3（weak-semantic-match）
       - 若最高分 < WEAK_THRESHOLD → L4（no-match）

    5. 操作别名（aliases）消费规则：
       别名数据来自 Step 1.6 构建的 ptm-atomic 内存索引中的 aliases 字段，
       由 ptm-atomic 仓库统一定义和维护（通过 ptm-atomic list --format json 返回），
       m-analyzer 不自行维护任何同义词映射表。
    ```

    **CLI 不可用降级**：
    - 若 Step 1.6 已降级（CLI 不可用），Step 2C 仅执行 L1 精确匹配和 L4 候选生成，跳过 L2/L3
    - 输出中标注"原子操作语义匹配未执行（CLI 不可用）"

    **记录的匹配元数据**：
    - 对每个操作步骤记录：match_level（L1/L2/L3/L4）、matched_op_id（如有）、match_score（如有）、match_details（各维度分项得分）

    **原子操作候选格式**（L3/L4 产出）：
       - candidate_op_name：建议操作名（动词 + 对象）
       - candidate_op_desc：行为描述
       - related_object_id
       - related_step
       - scenario_refs
       - match_attempt：{best_match_op_id, score, level}（L3 时记录最佳匹配）

    【子步骤 D：打标签 + 建立 Scenario→TSP 覆盖映射】
    1. 对当前步骤打标签（可多标签并存）：

       | 标签 | 含义 | 判定条件 | 消费方 |
       |------|------|---------|--------|
       | [M] | 纯单功能步骤 | 步骤仅涉及当前 M 内部逻辑 | M 分析自身 |
       | [F→目标] | 暗示跨 M 交互 | 操作目标属于其他 M / 外部系统 / 共享对象 / 引用了其他 M 的配置 / 共享其他 M 的 ptm-atomic op_id | F 分析（种子线索） |
       | [Q→维度] | 暗示质量属性 | 涉及异常恢复（掉电/重启/主备切换）→ [Q→可靠性]；涉及性能约束（响应时间/并发数/吞吐量）→ [Q→性能]；涉及安全校验（权限/加密/审计）→ [Q→安全性]；涉及长期运行/资源泄漏 → [Q→可靠性]；涉及版本升级/迁移 → [Q→可维护性] | Q 分析（相关性补充依据） |

       [F→] 和 [Q→] 标签由 M 分析生产、F 分析和 Q 分析消费。

    2. 判定该步骤被哪个 M 覆盖：
       - 若该步骤的测试对象已归属某 M → ✅ covered，记录 TSP 覆盖
       - 若无 M 覆盖但仍在本特性 scope 内 → ⚠️ uncovered（覆盖缺口）
       - 若超出 test_items 或 dont_test 范围 → ⚪ excluded（显式排除）

    3. 记录覆盖信息：scenario_ref + step_range / tsp_ref（若已确定）/ coverage_status / tags / directory_path / note
```

**汇总（所有场景的所有步骤分析完成后）**：

- 按四级目录（模块）→五级目录（子模块）聚合对象和因子
- 同一对象出现在多个场景中时，合并 scenario_refs
- 识别出所有单功能（M），形成 M 列表（M1, M2, M3...）
- 提取所有 [F→] 标签 → 形成"F 分析线索列表"
- 提取所有 [Q→] 标签 → 形成"Q 分析线索列表"
- 生成 Scenario-TSP 覆盖矩阵（视角 A 场景→TSP + 视角 B 目录→场景 + 覆盖率统计）

**📤 生产**：

| 产出 | 内容 |
|------|------|
| M 列表 | 每个 M 含名称、关联需求编号、关联场景编号 |
| 已确认测试对象表 | object_id / object_name / object_type / 关联度 / observation_targets / scenario_refs |
| 已有测试因子表 | factor_id / factor_name / source_section / data_domain / related_object_id / source=public-library |
| 因子候选列表 | factor_id / factor_name / data_domain / related_object_id / source=new-candidate / scenario_refs |
| 已有原子操作清单 | op_id / related_step / scenario_refs |
| 原子操作候选列表 | candidate_op_name / candidate_op_desc / related_object_id / related_step / scenario_refs |
| 场景步骤标签列表 | scenario_ref + step_range + tags + 判定依据 |
| Scenario-TSP 覆盖矩阵 | 视角 A（场景→TSP）+ 视角 B（目录→场景）+ F/Q 线索汇总表 |

### 步骤 3：TSP 描述生成

**📥 消费**：

| 数据 | 字段 | 用途 |
|------|------|------|
| 步骤 2 的 M 列表 + 测试对象表 + 覆盖记录 | M 名称/关联需求/关联场景 + object_name/object_type + coverage_status/tags | 为每个 M 生成 TSP，汇总 covered_scenario_segments + f_tags + q_tags |
| `mission-statement.md` | `test_items.items` | 交叉校验 M 识别边界 |

**🔄 处理逻辑**：

```
对步骤 2 识别出的每个 M（单功能）：
  1. Topic 提炼：一句话描述被测功能
  2. Scope 界定：输入输出边界（含排除范围），参考步骤 2 中该 M 关联的测试对象范围
  3. Purpose 提炼：测试意图（核心关注验证什么规则/行为/转换是正确的）
  4. 覆盖信息汇总：从步骤 2 子步骤 D 覆盖记录聚合 → covered_scenario_segments
  5. 标签汇总：从覆盖记录提取 → [F→] 汇总到 f_tags，[Q→] 汇总到 q_tags
```

**TSP YAML Schema**：

```yaml
tsp:
  id: "TSP-M<M编号>-NNN"
  m_id: "M2"
  topic: "根据优惠规则计算价格..."
  scope: "接收校验后商品数据..."
  purpose: "验证买二赠一/95折..."
  covered_scenario_segments:
    - scenario_ref: "SCN-SHOP-001"
      covered_steps: ["step-5", "step-6"]
      coverage_type: full
      coverage_note: "覆盖优惠规则计算核心步骤"
  f_tags: []
  q_tags: ["可靠性-数据一致性"]
```

**📤 生产**：每个 M 一个 TSP，写入 `mfq/m-analysis/tsp/<M编号>-tsp.md`

**TSP 的消费方**：

| 消费方 | 消费字段 | 用途 |
|--------|---------|------|
| m-analyzer（步骤 4） | `purpose` | 引导 PPDCS 主特征判断 |
| f-analyzer | `f_tags` + TSP 整体 | F 分析的驱动单元 |
| q-analyzer | `q_tags` + TSP 整体 | Q 分析的驱动单元 |
| design-planner | `covered_scenario_segments` + `scope` + `purpose` | 设计方法边界与交叉校验 |
| test-point-integrator | TSP 整体 | LC 组装时附着为元数据 |

### 步骤 4：PPDCS 特征标注

**📥 消费**：

| 数据 | 字段 | 用途 |
|------|------|------|
| 步骤 3 的 TSP | **`purpose`**（主要消费字段） | 引导 PPDCS 主特征判断 |
| 步骤 2 的测试对象表 | object_type + 功能描述 | 分析逻辑结构 |
| 步骤 2 的已有因子 + 因子候选 | factor_id + data_domain | 辅助判断 Data vs Combination |

**🔄 处理逻辑**：

```
对每个五级目录节点（单功能）：
  1. 优先读取 TSP.purpose 判断测试意图倾向：

     | Purpose 关注... | 倾向特征 | 理由 |
     |----------------|----------|------|
     | 步骤顺序/流程协调 | P-Process | 多步骤有序约束 |
     | 规则的输入输出正确性 | P-Parameter | 参数参与业务规则判定 |
     | 数据本身的合法性 | D-Data | 独立取值验证 |
     | 状态间的转换一致性 | S-State | 对象有多状态可互转 |
     | 参数太多需要压缩组合 | C-Combination | 因子组合爆炸 |

  2. 结合步骤 2 中的对象和因子数量验证：
     - 若对象涉及多状态且因子有 state 类型 → 加强 S-State
     - 若因子数量多且 constraints 中 require 多 → 加强 C-Combination
  3. 按以下优先级逐条判断：
     ├── 是否涉及多状态互转（可回退）？   → 标注 S-State
     ├── 是否有多步骤有序业务流程？       → 标注 P-Process
     ├── 参数间是否存在规则依赖？         → 标注 P-Parameter
     ├── 因子是否过多需组合压缩？         → 标注 C-Combination
     └── 数据是否独立可单独验证？         → 标注 D-Data
  4. 如有混合特征，标注主特征 + 辅特征
  5. 记录判定依据（引用 TSP.purpose 或需求描述）
```

**📤 生产**：PPDCS 特征标注表，写入 `mfq/m-analysis/ppdcs-annotation.md`

### 步骤 5：测试点生成（CAE 三元组 + trace chain v6）

**📥 消费**：

| 数据 | 字段 | 用途 |
|------|------|------|
| 步骤 2 的已确认测试对象 | 全部（高/中关联度） | 高关联度必须生成测试点；中关联度选择性生成 |
| 步骤 2 的已有因子 + 因子候选 | factor_id / data_domain | C 条件引用 |
| 步骤 3 的 TSP | id / topic / purpose | 测试点意图背景 |
| 步骤 4 的 PPDCS 特征 | 主特征 + 辅特征 | 标注在测试点上 |
| `confirmed-scenarios.md` | Scenario Chain / atomic_operations | trace 追溯 |
| KYM 产出 | `risks[].area` + `likelihood` + `impact` | 预填 risk_level |

**🔄 处理逻辑**：

```
**生成规则（基于步骤 2 的对象关联度）**：

- **高关联度对象**：必须生成正常+边界+异常测试点，使用已有因子填充 C 条件具体取值；若因子全为候选 → 降级处理
- **中关联度对象**：选择性生成（至少正常功能）；因子不足时在 C 条件中使用域引用 @domain.普通、@domain.边界、@domain.无效
- **低关联度对象**：不生成 M 测试点，记录供 F 分析参考

**因子全为候选降级处理**：TP 的 fact_status ← "needs-confirmation"，C 条件使用 @domain.xxx 域引用，test-points.md 中标注 [待确认]，确认后由 test-point-integrator 候选汇总步骤回填

**R 字段预填**：intent 从 TSP.purpose 生成，risk_level 从 KYM risks 匹配，rule_id/model_type/coverage 留待 PPDCS 阶段
```

每个测试点必须包含 **CAE 三元组**：

| 字段 | 说明 | 示例 |
|------|------|------|
| TP-ID | 测试点编号 | `TP-M-<模块缩写>-<子模块缩写>-NNN` |
| 所属模块 | 四级目录名称 | 配置管理 |
| 所属子模块 | 五级目录名称 | 日志服务器配置 |
| C 条件 | 触发该测试的前置状态、数据边界或环境约束 | 系统已配置5台日志服务器（达上限）；管理员已登录 |
| A 动作 | 可执行的测试操作，包含操作对象和内容 | 尝试新建第6台日志服务器，点击"确定" |
| E 预期 | 可观测的预期行为或系统响应 | 系统提示"超出最大服务器数量限制"；新建失败 |
| 关联需求 | 需求编号列表 | SR-001, SR-003 |
| `scenario_refs` | 场景编号列表 | SCN-XXX-001 |
| `scenario_chain_refs` | `PRE-* / AO-* / minimal_logic_chain` 引用 | PRE-01, AO-02 |
| `action_source_refs` | ptm-atomic `op_id` 引用 | fw_config_policy_route |
| `knowledge_refs` | 支撑该 TP 的知识引用 | KR-001 |
| `confirmation_gap_refs` | 上游未确认事实引用 | GAP-001 |
| `trace_refs` | 汇总 trace 引用 | 结构化 trace |
| `test_object_refs` | 关联测试对象 | OBJ-001 |
| `factor_refs` | 关联测试因子 | FAC-001, FAC-002 |
| `topology_refs` | 关联 confirmed-scenarios.md TOPO 实例 | TOPO-001 |
| `topology_role_refs` | 关联拓扑角色 | MATCH_INGRESS_IF, DUT_EGRESS_IF |
| `topology_binding_status` | 拓扑绑定状态 | confirmed / needs-confirmation / unbound |
| `topology_gap_refs` | 拓扑绑定缺口 | GAP-TOPO-001 |
| 来源 | M 分析 | M |
| 测试类型建议 | 功能/边界/异常/默认 | 边界 |
| `fact_status` | `confirmed / needs-confirmation` | confirmed |

**CAE 字段约束**：
- C 必须是可验证的前置状态，禁止模糊表述（如"正常情况下"）
- A 必须是可执行的操作，不能是"验证..."等描述性文字
- E 必须是可观测的结果，包含观测点和期望值
- **E="待定" 容错规则**：预期结果尚不明确时（如依赖硬件规格、待确认的产品行为），E 可填 `"待定"`，但必须追加批注 `[待定原因: <描述>]`；进入用例设计阶段前须补全。空值不允许。
- 若 A 依赖 ptm-atomic 但契约不完整，A 只能写已确认部分，并在 `confirmation_gap_refs` 中注明缺口
- 若 `Knowledge Reference` 为 `missing/unavailable`，仅记录状态，不得伪造理论依据
- C/A/E 涉及接口位置时必须优先写拓扑角色占位，例如 `{{topo_role:MATCH_INGRESS_IF}}`；不得把真实端口写成因子值
- C/A/E 出现真实端口时，必须同时写 `topology_refs` 并能回链 confirmed-scenarios.md；无法回链时 `topology_binding_status=needs-confirmation` 且 `fact_status=needs-confirmation`

**📤 生产**：M 分析测试点，按四级→五级分节输出，写入 `mfq/m-analysis/test-points.md`

### 步骤 6：覆盖初检（四维）

**📥 消费**：步骤 5 的 TP 清单 + 需求条目 + 步骤 2 的 Scenario-TSP 覆盖矩阵

**🔄 处理逻辑**：

```
1. 需求覆盖: 遍历每条 SR，检查是否至少关联 1 个 TP
   → 未覆盖的 SR 标记 ⚠️ 待补充

2. 场景步骤覆盖: 覆盖矩阵中每个 ✅ covered 步骤段是否至少关联 1 个 TP
   → 若某步骤段被 TSP 覆盖但无对应 TP → ⚠️ 覆盖缺口

3. 对象覆盖: 每个高关联度测试对象是否至少关联 1 个 TP
   → 未覆盖的高关联度对象标记 ⚠️ 待补充

4. 原子操作覆盖: 每个被引用的已有 ptm-atomic op_id 是否至少落到 1 个 TP
   → 未覆盖的 op_id 标记 ⚠️ 待补充

5. 视角 A/B 一致性校验:
   - sum_A(covered + uncovered + excluded) = total_steps（每个场景）
   - sum_B(TSP 覆盖步骤数) = count_A(covered 步骤)
   - [Q→] 标记步骤不计入 M 覆盖率
```

⛔ **HARD-STOP（GATE-3）**：覆盖初检结果中的 ⚠️ 缺口必须显式标注，**禁止 Agent 自行判定"覆盖完成"**。输出覆盖缺口清单后，等待用户审查（`approve` / `修改: ...` / `reject`）。

**📤 生产**：覆盖检查结果（嵌入 `test-points.md` 末尾的覆盖报告章节）

### 步骤 7：写入 M 分析产物

> 追踪链 v3.0：
> `SR → Scenario Chain → 步骤级发现（标签 [M]/[F→]/[Q→]）→ M → TSP(covered_scenario_segments + f_tags + q_tags) → 覆盖矩阵 → 测试对象(关联度) → 测试因子(已有/候选) → 原子操作(已有/候选) → TP(CAE + PPDCS + trace + topology) → LC → Test Data → PC`

⛔ **HARD-STOP（STOP-04）**：写入产物前必须校验目标父目录存在且为目录（非普通文件）。禁止 Agent 手动 mkdir 创建目录。若父目录不存在，输出错误信息并终止，等待用户确认目录结构。

**写入前校验**：

1. 校验目标父目录存在且为目录：`mfq/m-analysis/`、`mfq/m-analysis/tsp/`
2. 若父目录不存在或为普通文件 → **fail fast**，提示用户（禁止 Agent 手动 `mkdir`）
3. 若父目录存在 → 写入文件

**写入文件清单**（10 个文件）：

| 文件 | 内容 |
|------|------|
| `mfq/m-analysis/test-points.md` | 按四级→五级分节，CAE 表格 + 覆盖报告 |
| `mfq/m-analysis/ppdcs-annotation.md` | PPDCS 特征标注表 + 统计 |
| `mfq/m-analysis/test-objects-factors.md` | 测试对象表 + 已有因子表（含 match_confidence）+ 因子候选表 + 拓扑角色表 |
| `mfq/m-analysis/scenario-tsp-coverage.md` | 覆盖矩阵（视角 A 场景→TSP + 视角 B 目录→场景）+ F/Q 线索汇总表 |
| `mfq/m-analysis/tsp/<M编号>-tsp.md` | 每个 M 的 TSP 描述 |
| `mfq/m-analysis/factor-resolution-report.md` | 公共因子库命中/未命中统计（含 N_scanned 扫描库数） |
| `mfq/m-analysis/candidate-factor-proposals.yaml` | 因子候选列表 |
| `mfq/m-analysis/candidate-ptm-atomic.yaml` | 原子操作候选列表 |
| `mfq/factor-usage/factor-library-lock.yaml` | 运行时因子库版本快照（新增，CR-017） |
| `mfq/ptm-atomic-usage/ptm-atomic-lock.yaml` | ptm-atomic CLI 版本快照（新增，CR-016） |

**因子候选 YAML 格式**：

```yaml
candidate_factors:
  - candidate_id: "FAC-CAND-001"
    factor_name: "服务器数量上限"
    data_domain: "5（上限）/ 可配置"
    related_object_id: "OBJ-LOG-SERVER"
    source: "new-candidate"
    scenario_refs: ["SCN-LOG-001"]
    discovery_step: "Step 4-8"
    priority: "high"
```

**原子操作候选 YAML 格式**：

```yaml
candidate_ptm_atomic:
  - candidate_id: "AO-CAND-001"
    op_name: "fw_config_log_server_batch"
    op_desc: "批量创建日志服务器配置"
    related_object_id: "OBJ-LOG-SERVER"
    related_step: "Step 4"
    scenario_refs: ["SCN-LOG-001"]
```

**覆盖矩阵格式示例**（写入 `scenario-tsp-coverage.md`）：

视角 A — 场景→TSP：每行含 步骤范围 / 覆盖状态（✅/⚠️/⚪）/ TSP / 所属目录 / 标签 / 备注
视角 B — 目录→场景：按四级→五级目录组织，每行为 TSP 与覆盖的场景步骤列表
F 线索汇总：来源场景 / 步骤 / 标签 / 目标 M/系统 / 说明
Q 线索汇总：来源场景 / 步骤 / 标签 / 质量维度 / 说明

⛔ **HARD-STOP（GATE-3）**：写入完成后，输出 M 分析完成摘要和覆盖缺口清单，**等待用户审查覆盖初检结果**（`approve` / `修改: ...` / `reject`）。

## 测试点生成原则

1. **一个功能点至少一个测试点**
2. **正面优先**：先覆盖正常功能，再覆盖异常和边界
3. **粒度适中**：测试点应可独立验证
4. **可追溯**：每个测试点必须关联至少一条需求
5. **不预设设计方法**：M 分析只关注"测什么"和"什么特征"，不关注"怎么测"
6. **v3.0 关联度分级**：高关联度对象必须生成正常+边界+异常测试点；中关联度选择性生成（至少正常功能）；低关联度不生成 M 测试点
7. **候选因子降级**：测试点因子全为候选时，C 条件使用域引用 @domain.xxx，标注 [待确认]，fact_status=needs-confirmation
8. **候选列表不附确认建议**：因子候选和原子操作候选保持 source=new-candidate，禁止写入"建议全部确认"等自行判定语句。确认由 test-point-integrator 候选汇总步骤统一展示给用户

## 公共因子库补充契约

- M 分析是公共因子库首个强制消费者；提取测试因子前必须先执行 Step 1.5（因子库清单加载），按 `$PTM_TEAM_RESOURCE_HOME/factor-libraries` → `~/.ptm-team/resource/factor-libraries` → `resource/factor-libraries` 查找并读取 `index.yaml`，遍历加载各库 `factor-library.yaml`，构建内存索引。
- 公共库发现方式（v3.0+）：从已安装资源根或开发态 `resource/factor-libraries/index.yaml` 读取库注册清单 → 遍历每个已注册库（无论 active/candidate）→ 加载其 `factor-library.yaml` → 构建 factor_id → meta 内存索引。不得写死目标项目根下的 `resource/`；若已安装资源存在，应优先使用安装资源。
- 按 `factor_id / factor_name / aliases / owner_object / factor_group` 检索；命中 `active` 因子 → match_confidence=high，直接复用；命中 `candidate` 因子 → match_confidence=medium，复用但下游需显式确认。值域/样本/约束不足时输出扩展建议，未命中时写入 `mfq/m-analysis/candidate-factor-proposals.yaml`。
- 首次运行自动创建 `mfq/factor-usage/factor-library-lock.yaml` 锁定当前库版本快照；后续运行校验一致性，不一致时输出 WARNING 继续（不阻断）。
- 扫描完整性校验：N_scanned（成功加载的库数）必须等于 N_registered（index.yaml 注册库数），不等时 HARD-STOP 阻断。
- 项目运行不得直接修改公共主库；公共库归档和更新只能回流到 `resource/factor-libraries/`。
- CAE 中使用 `{{TF:FAC-ID|role=<role>|usage=<usage_context>|sample=<sample_id>}}`；下游主契约是 `factor_bindings`，`factor_refs` 只保留为兼容摘要。
- `factor_bindings` 至少包含 `library_id / factor_id_or_group_id / role / binding_mode / usage_context / sample_id / expr / materialized_stage / gap`。
- 禁止把 ptm-atomic、`scenario_refs`、`knowledge_refs`、`confirmation_gap_refs`、拓扑角色、真实端口、DUT/TG 实例或 link 实例当成测试因子。
- 必须输出 `mfq/m-analysis/factor-resolution-report.md`（含 N_scanned 字段）；如有未命中或需扩展内容，必须输出 `candidate-factor-proposals.yaml`。

## 拓扑绑定补充契约

- M 分析只产出拓扑角色约束和已能回链的 TOPO 引用，不负责最终唯一绑定；最终绑定由 integrator 根据 confirmed-scenarios.md 收敛。
- TP 必须透传 `topology_refs / topology_role_refs / topology_binding_status / topology_gap_refs`。
- `topology_role_refs` 只能表达逻辑位置约束，不得进入 `factor_bindings`。
- 若上游只给出裸端口且无法回链 confirmed-scenarios.md，保留原文证据，标记 `topology_binding_status=needs-confirmation` 与 `fact_status=needs-confirmation`。

## Gotchas

- 需求描述中隐含的功能也需要提取测试点
- 同一需求可能跨多个子模块
- 不要在 M 分析阶段引入耦合测试点（F 分析职责）
- PPDCS 标注时注意区分 Process 和 State 的双向性差异
- 一个子模块可能有混合特征，此时标注主特征+辅特征
- 不得把 `confirmation_gaps` 当作已确认事实
- `action_source_refs` 只引用上游已建模 ptm-atomic `op_id`，不重新命名为新的字段体系
- 拓扑角色不是测试因子；`MATCH_INGRESS_IF` 这类角色只能出现在 `topology_role_refs` 或 CAE 角色占位中
- 真实端口不是测试因子；出现 `DUT.port1` / `TG.port1` / link 实例时必须回链 confirmed-scenarios.md，否则降级为待确认
- **v3.0 新增 1**：步骤 2 必须对每个场景步骤打标签。遗漏 [F→] 标签会导致 F 分析缺少耦合分析线索，遗漏 [Q→] 标签会导致 Q 分析缺乏质量属性相关性依据
- **v3.0 新增 2**：候选因子和原子操作候选禁止自行确认。候选列表仅记录和透传，确认动作由 test-point-integrator 的候选汇总步骤统一完成
- **v3.0 新增 3**：覆盖矩阵视角 A 和视角 B 数据必须一致。视角 A 的 covered + uncovered + excluded = total_steps，视角 B 的 TSP 覆盖步骤数 = 视角 A 的 covered 步骤数
- **v3.0 新增 4**：Step 1.5 扫描完整性校验必须在进入 Step 2 前完成
- **v3.0 新增 5**：Step 1.6 ptm-atomic CLI 不可用时必须降级（WARNING + 回退精确匹配），不得阻断流程。语义匹配是增强而非替代——精确匹配（L1）始终可用

## 验收标准

- [ ] 每个五级目录节点至少有 1 个测试点，无跳过；无法覆盖的节点明确标注原因
- [ ] 每个高关联度测试对象均有对应测试点（正常+边界+异常）
- [ ] 每个 M 均有对应的 TSP 描述（含 `covered_scenario_segments` + `f_tags` + `q_tags`）
- [ ] 覆盖矩阵中每个场景的 covered + uncovered + excluded 步骤数等于 total_steps
- [ ] 覆盖矩阵视角 A 和视角 B 数据一致
- [ ] 覆盖缺口（uncovered 且无排除原因）已显式标记 ⚠️
- [ ] 每个场景步骤均打了标签（[M]/[F→]/[Q→]），F/Q 线索列表已生成
- [ ] 每个测试点包含完整的 CAE 三字段（C/A/E 均不为空、不模糊）
- [ ] C 字段为可验证状态，A 字段为可执行操作，E 字段为可观测结果
- [ ] E="待定" 必须附批注 `[待定原因: <描述>]`；空 E 字段不允许
- [ ] 每个 TP 包含完整的 trace 字段（`scenario_refs / action_source_refs / test_object_refs / factor_refs / trace_refs`）
- [ ] 已有因子和因子候选均已记录（source=public-library / new-candidate）
- [ ] 已有原子操作和原子操作候选均已记录
- [ ] 每个五级目录节点均有 PPDCS 主特征标注和判定依据
- [ ] 涉及组网的 TP 包含 `topology_refs / topology_role_refs / topology_binding_status / topology_gap_refs`
- [ ] `factor_bindings` 中不包含拓扑角色、真实端口、DUT/TG 实例或 link 实例
- [ ] CAE 中真实端口均可回链 `kym/scenarios/confirmed-scenarios.md`，否则 `fact_status=needs-confirmation`
- [ ] 未确认事实通过 `confirmation_gap_refs` 显式透传
- [ ] 输出 10 个文件：`test-points.md` / `ppdcs-annotation.md` / `test-objects-factors.md` / `scenario-tsp-coverage.md` / `tsp/<M>-tsp.md` / `factor-resolution-report.md` / `candidate-factor-proposals.yaml` / `candidate-ptm-atomic.yaml` / `factor-library-lock.yaml` / `ptm-atomic-lock.yaml`
- [ ] 步骤 6 覆盖初检结果显式标注 ⚠️ 缺口，禁止 Agent 自行判定"覆盖完成"
- [ ] 步骤 7 路径写入前校验父目录存在且为目录，禁止 Agent 手动 `mkdir`
- [ ] Step 1.5 因子库扫描完整性校验合格：factor-resolution-report.md 中 N_scanned 等于 index.yaml 注册库数
- [ ] 已有因子表包含 match_confidence 字段（high / medium），candidate 状态因子正确标记为 medium
- [ ] Step 1.6 ptm-atomic CLI 查询成功或已降级（CLI 不可用时 WARNING + 回退）
- [ ] Step 2C 每个操作步骤记录了 match_level（L1-L4）和最佳匹配 op_id/score
