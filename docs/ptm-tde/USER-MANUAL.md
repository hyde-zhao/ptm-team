# 用户使用手册

## 1. 文档定位

本手册面向使用 `ptm-tde` 的测试架构师、测试工程师、测试经理和平台集成人员，说明当前正式可交付能力、组件定位、工作流使用方式、Skill 触发方法以及交付物结构。

> 组件定位：**ptm-team 统一安装和投影，ptm-tde 维护 Agent / Skill 调用关系与运行时产物契约**
> 运行时目录规则：**读当前特性的 `.input/`，按阶段写入 `.input` 父目录 `feature_workspace_root` 下的 `kym/`、`mfq/`、`ppdcs/`、`process/`**

## 2. 角色说明

| 角色 | 职责 | 触发方式 |
|------|------|---------|
| 测试架构师 | 导入需求、确认目录与 Scenario Chain、评审设计计划与覆盖率 | 通过 `@ptm-tde ...` 发起分析、在 GATE-2/GATE-3/GATE-4 确认检查点 |
| 测试工程师 | 执行 MFQ 分析、查看 PPDCS 设计过程、落地物理用例 | 使用主流程或定向触发设计类 Skill |
| 测试经理 | 检查覆盖率、风险、交付完整性和检索可用性 | 在 coverage / delivery 阶段确认结果 |
| 平台集成人员 | 通过 ptm-team 管理 ptm-tde 的安装、投影、升级、卸载和现场反馈采集同步 | 使用 ptm-team 统一工具完成组件管理和反馈闭环 |

## 3. 组件与运行约定

### 3.1 安装入口归属

`ptm-tde` 后续作为 `ptm-team` 的一个组件交付，不再独立维护安装入口、project/user scope 投影脚本或卸载流程。安装、升级、卸载、平台目录投影、dry-run 和安装漂移检查均由 `ptm-team` 统一控制。

常用命令：

```bash
uv run python script/install.py install codex --agent ptm-tde
uv run python script/install.py install claude --agent ptm-tde
uv run python script/install.py check codex --agent ptm-tde
uv run python script/install.py check claude --agent ptm-tde
```

安装 `ptm-tde` agent 时，安装器会同步维护平台规则托管块：Codex 写入 `AGENTS.md`，Claude Code 写入 `CLAUDE.md`；文件不存在则创建，文件存在则只追加或替换 `ptm-tde-workflow` managed block，不覆盖用户已有规则。

`check <platform> --agent ptm-tde` 会读取 `.ptm-team-manifest.json`，检查 agent、skill、规则 managed block 和共享 resource 是否仍与 manifest 一致，并检查源仓库 hash 是否变化。发现 `INSTALLED_DRIFT`、`SOURCE_DRIFT` 或 `MISSING` 时返回非 0，建议重新安装。

安装 `ptm-tde` agent 时，ptm-team 安装器同时安装 `resource/component-resource-links.yaml` 中声明的公共因子库。因子库默认安装到：

```text
~/.ptm-team/resource/factor-libraries/
```

如需团队共享目录，可设置：

```text
PTM_TEAM_RESOURCE_HOME=/path/to/shared/ptm-team/resource
```

`ptm-tde` 自身只维护：

- 主 Agent 与 Skill 的调用关系
- Skill 私有模板、脚本与 schema 的同树资产关系
- 特性项目运行时目录和检查点契约
- 最终测试方案与测试用例交付口径
- 公共因子库消费契约、项目 lock、binding 和候选回流口径

### 3.2 特性工作区建议

推荐一个特性一个工作区。标准输入目录为 `.input/`，`.input` 的父目录就是当前特性的 `feature_workspace_root`。如果一个仓库下有多个特性，可以让每个特性拥有独立子目录：

```text
/home/hyde/projects/ptm-work/<repo>/
├── feature-a/
│   └── .input/
└── feature-b/
    └── .input/
```

分析 `feature-a` 时，所有输出都写入 `feature-a/kym`、`feature-a/mfq`、`feature-a/ppdcs`、`feature-a/process`；分析 `feature-b` 时写入 `feature-b/*`。如果同一仓库发现多个 `.input/` 且用户未指定目标，ptm-tde 必须暂停并要求用户选择，不能自动选择第一个目录。

### 3.3 运行时目录规则

```text
<feature_workspace_root>/
├── .input/          # 用户原始输入，只读
├── kym/            # KYM 阶段产物：feature-input / scenarios
├── mfq/            # MFQ 阶段产物：M/F/Q / integration / factor-usage
│   └── factor-usage/ # 公共因子库 lock、binding、候选提案和解析报告
├── process/
│   ├── plan/       # MFQ→PPDCS 跨阶段设计计划
│   ├── checkpoints/# 自动和人工检查点记录
│   └── STATE.yaml  # 当前特性项目运行状态
├── ppdcs/          # PPDCS 阶段产物：ppdcs / pc / coverage / delivery
│   ├── ppdcs/      # 每个逻辑用例一份 PPDCS 设计过程
│   ├── pc/         # 每个逻辑用例一份物理用例设计
│   ├── coverage/   # 覆盖率报告
│   └── delivery/   # 最终测试方案与测试用例总表
```

强约束：

1. `.input/` 只读，不回写分析产物
2. 不创建、不写入 `.output/`
3. 阶段产物按目录归档，最终交付只写入 `ppdcs/delivery/`
4. PPDCS 与 PC 均采用扁平文件，不再使用多级嵌套目录
5. 公共因子库主库只在 `ptm-team/resource/` 和用户级公共资源目录归档，项目内不得复制为主库

### 3.4 现场反馈一键采集与 GitLab 同步

发布后真实使用中发现的问题，不建议靠口头描述或手工整理模板回传。`ptm-tde` 在交付或真实运行结束时会通过 `tde-feedback` Skill 询问“本次 ptm-tde 使用是否有问题需要反馈？”。使用者确认有问题后，Skill 会调用 `script/field_feedback.py collect / submit / publish` 生成标准采集包并同步到 GitLab；维护侧用 `pull` 拉回原始材料后再生成 RUN-EXEC、ISSUE、覆盖盲区分析和质量看板。

推荐 GitLab 落点：

| 项 | 推荐值 |
|---|---|
| 仓库 | `git@<IP_ADDRESS>:<INTERNAL_GIT_PATH>/ptm-team-feedback.git` |
| 本地仓库 | `../ptm-team-feedback` |
| 分支 | `main` |
| 目录 | `tde-feedback/<feature>/<COLLECT-ID>/` |
| 备选 | 使用其他独立反馈仓库，目录结构不变 |

`publish` 只调用本机已有 Git 配置和远端，不直接处理 GitLab Token、密码或访问凭据。需要推送权限时，由使用者按团队 GitLab 规范提前配置 SSH key、HTTPS credential 或 CI token。

`tde-feedback` 的必问入口在 Claude Code 环境优先使用 `AskUserQuestion` 选项卡：

```text
本次 ptm-tde 使用是否有问题需要反馈？

A. 无问题反馈
B. 有问题，仅采集
C. 有问题，采集并上传
D. 上传已有采集包
```

其中选择“有问题，采集并上传”或“上传已有采集包”即表示授权 `--push` 到默认反馈仓库；选择“有问题，仅采集”时只生成 `COLLECT-*` 包，不提交、不推送。

维护者首次初始化默认反馈仓库：

```bash
uv run python script/field_feedback.py repo-init --root . --push
```

使用者侧一键采集：

```bash
uv run python /path/to/ptm-team/script/field_feedback.py collect \
  --root /path/to/ptm-team \
  --workspace /home/user/ptm-tde/test/policy_route_rt_verify \
  --feature policy_route \
  --platform claude \
  --result fail \
  --gate GATE-4 \
  --summary "GATE-4 BLOCKED: ppdcs/coverage 缺失"
```

默认采集以下运行材料：

```text
process/STATE.yaml
process/checkpoints/
process/checks/
process/execution/
ppdcs/coverage/
ppdcs/delivery/
ppdcs/pc/
ppdcs/ppdcs/
```

采集包示例：

```text
process/field-feedback/collections/COLLECT-20260615-policy_route-001/
├── FEEDBACK.md
├── MANIFEST.json
└── artifacts/
```

如需追加采集其他工作区相对路径，可重复传入 `--include <workspace-relative-path>`。

使用者侧发布到独立反馈仓库：

```bash
uv run python /path/to/ptm-team/script/field_feedback.py publish \
  --root /path/to/ptm-team \
  --collection /path/to/ptm-team/process/field-feedback/collections/COLLECT-20260615-policy_route-001 \
  --commit \
  --push
```

采集并推送也可以合并为一条命令：

```bash
uv run python /path/to/ptm-team/script/field_feedback.py submit \
  --root /path/to/ptm-team \
  --workspace /home/user/ptm-tde/test/policy_route_rt_verify \
  --feature policy_route \
  --platform claude \
  --result fail \
  --gate GATE-4 \
  --summary "GATE-4 BLOCKED: ppdcs/coverage 缺失" \
  --commit \
  --push
```

维护侧拉取 GitLab 原始反馈材料：

```bash
uv run python script/field_feedback.py pull \
  --root .
```

维护侧分析时，以 `COLLECT-*` 包为入口：先登记 RUN-EXEC，再把失败项生成 ISSUE，补 coverage_status、category、severity、stage 和 regression_asset，最后刷新 `docs/quality/FIELD-QUALITY-DASHBOARD.md`。脚本完整命令见 `script/README.md`。

## 4. 当前能力总览

### 4.1 主追踪链

```text
SR
→ Scenario Chain
  ↳ Topology (`topology_ref`)
→ atomic-ops
→ Factor Library (`factor_bindings`)
→ TP(CAE + `topology_role_refs`)
→ LC(`factor_bindings` + `topology_bindings`)
→ PC
→ ppdcs/delivery/<特性名>特性测试用例.md
```

### 4.2 公共因子库

公共因子库是 `ptm-team` 仓库级 resource，直接挂在 `resource/factor-libraries/`，不是 ptm-tde 私有资产。`ptm-tde` 通过以下流程消费：

1. 读取 `PTM_TEAM_RESOURCE_HOME/factor-libraries` 或 `~/.ptm-team/resource/factor-libraries`。
2. 根据用户指定、项目 lock 或特性领域选择公共库。
3. 在项目内写入 `mfq/factor-usage/factor-library-lock.yaml`。
4. `m-analyzer` 查库后生成 `factor_bindings`。
5. 未命中的因子写入 `candidate-factor-proposals.yaml`，由公共库维护流程评审后回流到 `ptm-team/resource/`。

项目运行不得直接修改公共因子库主库。

### 4.2.1 测试因子、拓扑角色和真实组网对象

`ptm-tde` 把测试变量和组网实例分开管理：

| 类型 | 用户看到的含义 | 可以放入公共因子库吗 | 示例 |
|---|---|---|---|
| 测试因子 | 可复用的测试设计变量、值域、样本或约束 | 可以 | 接口类型、接口能力、规则协议、流量匹配状态 |
| 拓扑角色 | 测试逻辑里的抽象位置 | 不作为因子值；作为角色引用 | client、server、dut-ingress、dut-egress |
| 真实组网对象 | 已确认场景里的设备、端口、链路实例 | 不可以 | `DUT.port1`、`TG.port1`、`LINK-001` |

链路如下：

```text
topology_role_refs -> topology_bindings -> PC materialization
```

使用者需要重点确认：

- CAE 只表达测试逻辑和拓扑角色，不直接写真实端口。
- LC 阶段从 `kym/scenarios/confirmed-scenarios.md` 绑定真实设备、端口和链路。
- PC 中出现的真实端口必须能回链到 LC `topology_bindings` 和已确认场景。
- 未确认的端口绑定会以 `needs-confirmation` 保留，覆盖率和交付物不会自动把它改成 confirmed。

### 4.3 场景模型升级

当前场景阶段输出的是 **Scenario Chain**，不是旧版“原理/路径/测试数据”弱结构模板。

每条场景链至少包含：

- `scenario_goal`
- `principle`
- `preconditions`
- `topology_ref`
- `normal_path`
- `abnormal_path`
- `atomic_operations`
- `observation_points`
- `minimal_logic_chain`
- `data_overlay_slots`
- `review_status`

操作路径口径：

- GATE-2 自动自检会逐 `scenario_id` / 场景标题检查每条 confirmed scenario 的 `normal_path` 和 `abnormal_path`，文件级出现字段名不能替代场景内链路。
- `normal_path` 必须包含 `step_id / sub_step_ids / operation / necessity / description`。
- `normal_path` 每个步骤必须包含 `action_source_ref(s)`、`atomic_op` 或 `op_id`，并能回链场景级 `action_source_refs`。
- `necessity` 只能使用 `必要 / 可选 / 至少选择一项`。
- `至少选择一项` 必须列出可选子步骤，并在 `minimal_logic_chain` 中保留选择约束。
- `abnormal_path` 必须包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`；异常项应能追溯到正常路径步骤、子步骤、前置条件、环境故障或退出动作；无异常路径时必须写明 N/A 理由。
- `abnormal_path` 每个异常步骤同样必须包含可回链的原子操作引用。

atomic-ops 口径：

- atomic-ops 是唯一原子操作引用对象。
- `action_source_ref` 直接引用 atomic-ops `op_id`。
- 发现新增原子操作时只能作为候选展示给用户确认；用户需决定新增、复用已有、修改后新增或拒绝。
- REST API、CLI、tool-method 只能作为 atomic-op 的底层调用或观测契约，不作为独立引用类型输出。

### 4.4 Topology Modeling（CR-008）

对依赖明确组网的场景，`scenario-discovery` 会在 `kym/scenarios/<scene-id>/` 下同步输出：

- `topology.mmd`
- `topology.yaml`
- 设备 / 端口 / 链路三张清单表

最低校验口径：

| 规则 | 说明 |
|---|---|
| 双端点 | 每条链路必须恰好连接两个端口 |
| 唯一性 | `device_id` / `port_id` / `link_id` 在同一 Topology 内唯一 |
| DUT 端口数 | `DUT` 至少具备两个可参与业务的端口 |
| 目标解析 | atomic-op 的 `target` 应能解析到 `DUT<n>` 或 `DUT<n>.Port<n>` |
| 绑定回链 | PC 中真实端口必须能回链到 LC `topology_bindings` 与 `kym/scenarios/confirmed-scenarios.md` |

### 4.5 MCP 只读 staged query / tri-state 契约

场景发现阶段按以下顺序发起只读查询：

1. 防火墙主应用场景
2. 特性应用场景
3. 特性主功能

返回结果必须显式区分三态：

| 状态 | 含义 |
|---|---|
| 查询成功 | 找到可引用知识，保留来源与查询时间 |
| 知识缺失 | 接口正常，但知识库中无对应内容 |
| 接口不可用 | MCP / 网关 / 上游服务不可达或失败 |

> ⚠️ **v2.0 实现限制**：`scripts/mcp_query_client.py` 当前仅交付 `--transport mock`
> 通道，三态返回值完全由 `--mock-state success|knowledge_missing|interface_unavailable`
> 驱动，真实 MCP transport（HTTP / stdio 等）尚未实现。在落地项目上建议先通过
> mock 完成 Scenario Chain 的三态演练；真实知识库接入由后续迭代补齐。

### 4.6 五类 PPDCS 设计输出

| 方法 | 必须输出 |
|---|---|
| P-Process | 流程图、路径枚举、覆盖策略、路径触发数据、物理用例 |
| P-Parameter | 规则提取、约束关系、判定结构、规则触发参数组、物理用例 |
| D-Data | 取值范围、等价类、边界值策略、选点结果、物理用例 |
| C-Combination | 因子与取值范围、组合压缩策略、约束条件、组合结果、物理用例 |
| S-State | 状态图、状态/迁移表、守卫条件、迁移触发数据、物理用例 |

## 5. Skill 使用指南

### feature-parser
- **触发词**：解析特性、解析需求、导入特性文件、特性解析
- **适用场景**：将输入需求转成三级/四级/五级目录结构
- **输入**：需求文件、参考文档
- **输出**：结构化目录树、需求线索
- **示例**：`@ptm-tde 解析 .input/feature.md`

### scenario-discovery
- **触发词**：场景分析、搜索场景、应用场景、场景链
- **适用场景**：从需求或 functional scenario seed 重新发现部署型场景，生成 Scenario Chain、Operation Path、Topology、原子操作、观察点、最小逻辑链
- **输入**：目录结构、只读 MCP、atomic-ops 能力说明、REST API / CLI / tool-method 底层契约说明
- **输出**：场景链、正常/异常操作路径、`topology.mmd/yaml`、atomic-ops 目录、知识引用、缺口项
- **示例**：`@ptm-tde 结合 MCP 和 REST API 配置做场景分析`

### m-analyzer
- **触发词**：M分析、功能分析、模块分析、PPDCS标注
- **适用场景**：单功能拆分、PPDCS 标注、CAE 测试点生成
- **输入**：目录结构、已确认 Scenario Chain
- **输出**：M 测试点、PPDCS 标注表、`topology_role_refs`
- **示例**：`@ptm-tde 对已确认场景执行 M 分析`

### f-analyzer
- **触发词**：F分析、耦合分析、耦合矩阵、特性交互
- **适用场景**：三源耦合分析
- **输入**：Excel 耦合矩阵、场景耦合、可选代码依赖
- **输出**：耦合视图、耦合测试点
- **示例**：`@ptm-tde 读取 .input/coupling-matrix.xlsx 做 F 分析`

### q-analyzer
- **触发词**：Q分析、质量分析、HTSM、质量属性
- **适用场景**：质量属性相关性评估
- **输入**：功能点、场景链、HTSM 维度
- **输出**：质量测试点、相关性评估
- **示例**：`@ptm-tde 对该特性执行 Q 分析`

### test-point-integrator
- **触发词**：整合测试点、测试点合并、逻辑用例、测试点归集
- **适用场景**：合并 M/F/Q 测试点，输出 LC
- **输入**：M/F/Q 测试点
- **输出**：逻辑用例、测试数据、覆盖关系、从已确认场景生成的 `topology_bindings`
- **示例**：`@ptm-tde 整合测试点并生成逻辑用例`

### design-planner
- **触发词**：设计计划、PPDCS匹配、方法推荐、测试设计计划
- **适用场景**：为每条 LC 推荐设计方法并输出推断过程
- **输入**：LC、测试数据、CAE 信号
- **输出**：设计计划表、主信号/候选/排除理由
- **示例**：`@ptm-tde 生成设计计划并给出推断过程`

### process-design
- **触发词**：流程图、流程图法、路径分析、P-Process
- **适用场景**：顺序型流程逻辑
- **输入**：P-Process 类型 LC
- **输出**：流程图、路径分析、物理用例
- **示例**：`@ptm-tde 对 LC-001 使用 P-Process 设计`

### parameter-design
- **触发词**：判定表、因果图、参数规则、决策树、P-Parameter
- **适用场景**：参数规则判定
- **输入**：P-Parameter 类型 LC
- **输出**：规则提取、约束、判定结构、物理用例
- **示例**：`@ptm-tde 对 LC-002 使用判定表法`

### data-design
- **触发词**：等价类、边界值、数据分析、D-Data
- **适用场景**：独立数据范围验证
- **输入**：D-Data 类型 LC
- **输出**：等价类、边界值、物理用例
- **示例**：`@ptm-tde 对 LC-003 使用等价类和边界值法`

### combination-design
- **触发词**：数据组合、Pairwise、正交、因子组合、C-Combination
- **适用场景**：多因子组合覆盖
- **输入**：C-Combination 类型 LC
- **输出**：因子表、约束、组合结果、物理用例
- **示例**：`@ptm-tde 对 LC-004 做 Pairwise 组合设计`

### state-design
- **触发词**：状态图、状态机、状态迁移、S-State
- **适用场景**：多状态迁移对象
- **输入**：S-State 类型 LC
- **输出**：状态图、迁移表、物理用例
- **示例**：`@ptm-tde 对 LC-005 使用状态图法`

### coverage-verifier
- **触发词**：覆盖检查、覆盖率、覆盖验证、需求覆盖
- **适用场景**：需求层和测试点层双层覆盖检查
- **输入**：需求、TP、LC、PC、`kym/scenarios/confirmed-scenarios.md`、LC `topology_bindings`
- **输出**：覆盖率报告、未覆盖项清单、拓扑绑定缺口；不会把 `needs-confirmation` 提升为 `confirmed`
- **示例**：`@ptm-tde 生成双层覆盖率报告`

### deliverable-renderer
- **触发词**：生成交付物、输出文档、测试方案、测试用例文档
- **适用场景**：生成最终测试方案与测试用例总表
- **输入**：全部分析与设计产物、因子绑定、拓扑绑定和覆盖结果
- **输出**：`ppdcs/delivery/<特性名>特性测试方案.md`、`ppdcs/delivery/<特性名>特性测试用例.md`；保留 `topology_bindings / topology_role / source / fact_status`
- **示例**：`@ptm-tde 输出最终交付文档`

### case-retriever
- **触发词**：检索用例、查询用例、按需求查询、按标签查询
- **适用场景**：交付后按结构化条件反查用例
- **输入**：最终测试用例总表、需求编号 / 逻辑用例编号 / feature tag
- **输出**：命中 LC/PC 与 trace refs
- **示例**：`@ptm-tde 按 REQ-013 检索用例`

### tde-feedback
- **触发词**：收集反馈、上传反馈、推送反馈、同步到 GitLab、拉取反馈材料、真实运行反馈
- **适用场景**：交付或真实运行结束后询问用户是否有问题反馈，并把问题反馈采集为 `COLLECT-*` 包，同步到 `ptm-team-feedback` 仓库或从反馈仓库拉取材料供评估分析
- **输入**：feature、特性工作区路径、platform、result、gate、summary、expected、actual，以及用户对 `--push` 的明确授权
- **输出**：`process/field-feedback/collections/COLLECT-*` 采集包、GitLab `tde-feedback/<feature>/<COLLECT-ID>/` 目录，或本地 `process/field-feedback/inbox/gitlab-materials`
- **示例**：`@ptm-tde 使用 tde-feedback 收集本次真实运行反馈并上传`

### change-impact-analyzer
- **触发词**：需求变更、变更分析、增量分析、需求修改
- **适用场景**：只对受影响资产做增量 MFQ / 设计 / 覆盖
- **输入**：变更单、既有基线、最终测试用例总表
- **输出**：受影响场景链、LC/PC、补充或修订范围
- **示例**：`@ptm-tde 分析 CR-001 的变更影响`

### bug-gap-analyzer
- **触发词**：问题单、缺陷分析、覆盖盲区、遗漏分析
- **适用场景**：根据问题单定位遗漏环节
- **输入**：问题单、复现步骤、既有测试方案与测试用例总表
- **输出**：遗漏阶段、补齐建议、补充资产
- **示例**：`@ptm-tde 对 DEFECT-123 做覆盖盲区分析`

## 6. 测试用例总表 / feature tags / case-retriever

### 6.1 总表检索字段

`deliverable-renderer` 会在 `ppdcs/delivery/<特性名>特性测试用例.md` 中保留结构化检索字段，核心字段包括：

| 字段 | 说明 |
|---|---|
| `requirement_ids` | 需求编号集合 |
| `logic_case_id` | 逻辑用例编号 |
| `physical_case_id` | 物理用例编号 |
| `feature_tags` | 功能分类标签 |
| `trace_refs` | 回链到 Scenario / TP / LC / PC 的引用 |
| `action_source_refs` | PC 步骤中 `atomic_op.op_id` 的回链集合 |
| `case_steps` | PC 的结构化步骤源契约，包含 `step_name / target / atomic_op / expected_result` |
| `topology_bindings` | 拓扑角色到真实设备、端口和链路的绑定 |
| `source` / `fact_status` | 真实组网对象来源和确认状态 |

### 6.2 检索入口

`case-retriever` 首版仅支持三类精确过滤：

1. 按需求编号检索
2. 按逻辑用例编号检索
3. 按功能分类标签检索

示例：

```text
@ptm-tde 按 REQ-018 检索用例
@ptm-tde 查询 LC-007
@ptm-tde 按 feature tag=日志过滤 检索
```

## 7. 工具与 atomic-ops 分析口径

### 7.1 已使用工具 / atomic-ops

| 名称 | 类型 | 主要用法 | 用途 | 适用场景 |
|---|---|---|---|---|
| atomic-ops | atomic-ops | 以 `op_id` 表示可执行原子操作 | 场景链建模、观察点落地、后续 TP/LC trace | 标准/复杂场景 |
| `ptm-team` 统一安装工具 | atomic-op backend | 作为 atomic-op 的底层实现通道完成安装、升级、卸载和平台投影 | 组件生命周期管理 | 安装与初始化 |
| `excel_coupling_tool.py` | atomic-op backend | 作为 atomic-op 的底层实现通道读取耦合矩阵基线 | F 分析耦合输入 | 有耦合矩阵的标准/复杂分析 |
| `mcp-query-client.py / MCP Gateway` | atomic-op backend | 作为 atomic-op 的底层实现通道执行只读 staged query | 领域/特性/功能知识引用 | 有知识库入口的标准/复杂分析 |
| 用户提供 REST API | atomic-op backend | 只能作为 atomic-op 的底层调用或观测契约 | 场景链建模与观察点落地 | 复杂场景 |
| 用户提供 CLI 工具 | atomic-op backend | 只能作为 atomic-op 的底层调用或观测契约 | 支撑原子操作和结果观察 | 复杂场景 |
| `topology.mmd` / `topology.yaml` | model artifact | 固化设备/端口/链路关系 | 场景确认与组网回链 | 有明确组网要求的标准/复杂分析 |
| `case-retriever` | atomic-op backend | 作为 atomic-op 的底层实现通道消费最终测试用例总表的结构化字段 | 交付后反查用例 | 交付与维护阶段 |

### 7.2 待实现工具 / 工具抽象

当现有工具不足时，分析过程会记录工具抽象草案，并在测试方案中汇总需要用户补齐或后续实现的缺口。工具抽象至少包含以下字段：

| 字段 | 说明 |
|---|---|
| API / CLI 接口 | 调用入口、参数、鉴权或命令格式 |
| 功能描述 | 该工具需要覆盖的测试动作或观察能力 |
| 输入/输出契约 | 请求、响应、日志、状态变化 |
| 处理逻辑 | 不同输入/输出条件下的行为矩阵 |
| 输出内容 | 返回值、日志、观察点 |
| 适用场景 | 对应 Scenario Chain / 因子 / 用例 |

约束：

- 不在交付阶段脑补未实现能力
- 若工具缺口未被真实补齐，状态保持 `gap / planned`
- 工具分析不再作为单独最终交付物输出，最终交付只包含测试方案和测试用例总表

## 8. 工作流典型路径

### 8.1 Simple 路径

```text
用户：分析 .input/feature.md
Agent：解析目录结构，请确认
用户：确认
Agent：输出 Scenario Chain + Topology，请确认
用户：确认
Agent：完成 MFQ、设计计划、五类设计、覆盖验证
Agent：输出测试方案 / 测试用例总表
```

### 8.2 Standard 路径

```text
用户：分析 .input/feature.md，并读取 .input/coupling-matrix.xlsx
Agent：解析目录，请确认
用户：确认
Agent：调用只读 MCP，按 staged query 生成场景链和 Topology，请确认
用户：补充 1 个观察点后确认
Agent：执行 M/F/Q、生成设计计划
用户：确认 PPDCS 逻辑设计
Agent：生成覆盖报告和最终交付
```

### 8.3 Complex 路径

```text
用户：除需求外，再提供 REST API 配置和现有 CLI 工具说明
Agent：解析目录并请求确认
用户：确认
Agent：识别 atomic-ops，发现 2 个工具缺口，请求补充
用户：补充 1 个 CLI 契约，另 1 个保留待实现
Agent：输出 Scenario Chain、Topology 与工具抽象草案，请确认
用户：确认
Agent：执行 MFQ、五类 PPDCS 设计、双层覆盖
Agent：输出测试方案和测试用例总表，并支持按 feature tag 检索
```

## 9. 交付物说明

最终交付只包括：

| 交付物 | 说明 |
|---|---|
| `ppdcs/delivery/<特性名>特性测试方案.md` | 汇总需求、Scenario Chain、MFQ 分析、设计计划、覆盖率和工具缺口 |
| `ppdcs/delivery/<特性名>特性测试用例.md` | 汇总所有物理用例，使用唯一标准 16 列 PC 表，并保留 requirement / LC / feature tag / trace refs / case_steps / action_source_refs 等检索与执行字段 |

`kym/`、`mfq/` 与 `ppdcs/ppdcs/` 下的 Topology、PPDCS 设计过程、PC 设计过程属于过程资产；测试方案引用并汇总这些资产，但不把它们作为独立最终交付文档。

交付物展示约束：

- “因子库与样本策略”只展示公共测试因子和样本策略。
- “拓扑绑定 / 组网约束”展示真实设备、端口、链路及其来源。
- `DUT.port1`、`TG.port1`、link 实例不得出现在因子取值表或公共因子样本中。
- `needs-confirmation` 的拓扑绑定必须原样展示为未确认项。
- PC 文件必须保留 `case_steps`，每一步必须同时包含人类可读 `step_name` 和可执行 `atomic_op.op_id`。
- `case_steps[].atomic_op.op_id` 必须进入 `action_source_refs`；执行层不再负责从自然语言测试步骤中反向猜测原子操作。
- 最终测试用例总表的 `测试步骤*` 单元格必须渲染 `原子操作：<op_id> <args>`；表头必须等于标准 16 列，所有数据行必须恰好 16 列。

## 10. 常见问题

### Q1：为什么平台只写 Claude Code 和 Codex？
因为当前正式支持范围已收敛到这两个平台，其他平台口径已移除，不再作为交付范围。

### Q2：为什么要求读 `.input/`，但不再写 `.output/`？
这是新的特性工作区运行约定：`.input/` 保护原始输入，分析、设计、检查点、交付和状态分别写入 `.input` 父目录 `feature_workspace_root` 下的专用目录，避免再套一层 `.output/`。

### Q3：Scenario Chain 与旧场景模板有什么区别？
Scenario Chain 强调“原子操作 + 观察点 + 最小逻辑链”，并可通过 `topology_ref` 绑定组网结构，直接连接到 LC 与物理用例，不再停留在概念性描述。

### Q4：为什么现在要在场景阶段确认 Topology？
因为很多 atomic-ops、观察点和工具分析都依赖明确的设备/端口归属；把 Topology 放到场景确认阶段，能更早暴露组网缺口，避免后续设计链回退。

### Q4a：真实端口和接口类型有什么区别？
接口类型、接口能力是可复用测试变量，可以作为公共因子；真实端口是当前项目的组网实例，例如 `DUT.port1`，只能通过 `topology_bindings` 进入 LC 和 PC，不能写入公共因子值域。

### Q5：MCP 为什么不能直接写知识库？
当前契约仅支持只读引用，避免把知识治理、索引维护和测试设计工作流混在一起。

### Q6：如果用户已有工具不够用怎么办？
系统不会伪造能力，而是输出待实现工具抽象，明确 API/CLI、行为矩阵、输出内容和适用场景。

### Q7：组合设计一定依赖外部 Pairwise 工具吗？
不一定。若现有工具可用则消费；若不可用，系统保留组合策略与待确认回退口径，但不会虚构已实现工具。

### Q8：如何检索历史用例？
通过 `case-retriever` 读取最终测试用例总表，并使用三类条件：需求编号、逻辑用例编号、feature tag。

### Q9：变更或问题单会重算全部内容吗？
不会。`change-impact-analyzer` 和 `bug-gap-analyzer` 只命中受影响场景链、LC/PC 与最终测试用例总表中的相关行，不改动未受影响资产。

### Q10：别人真实使用后的问题怎么反馈？
让使用者触发 `tde-feedback` Skill，先回答是否有问题反馈；确认有问题后，Skill 会在工作区执行 `field_feedback.py submit` 生成 `COLLECT-*` 采集包并推送到 `ptm-team-feedback.git` 的 `main` 分支；也可以先执行 `collect`，确认材料后再执行 `publish`。维护者在 `ptm-team` 执行 `field_feedback.py pull --root .` 拉回原始材料，然后把采集包路径交给分析流程生成 RUN-EXEC、ISSUE、覆盖盲区分析和回归资产。

## 11. 文档缺口清单

| 缺口类型 | 影响项 | 严重程度 | 建议处理 |
|---------|--------|---------|---------|
| 无 | 当前手册已覆盖组件定位、特性项目运行目录、Scenario Chain + Topology、MCP 只读三态、五类 PPDCS、检索闭环、工具与 atomic-ops 分析口径、`tde-feedback` 现场反馈采集、GitLab 同步和 field-feedback 闭环 | 低 | 后续若 ptm-team 统一安装手册、field-feedback 脚本参数或新增 Topology 校验器变更，再同步扩展本手册 |

## 12. 近期变更同步

本节同步 `process/changes/CR-20260520-001.md` 与 `process/changes/CR-20260521-001.md` 的已确认变更。原章节继续有效；以下内容是面向使用者的增量说明。

### 12.1 场景再发现、atomic-ops 与 GATE-2

CR-20260520-001 已将场景阶段从“整理输入”强化为“再发现与部署型场景重构”。

使用者需要关注：

- 如果输入是 functional scenario seed，系统不会直接把 seed 改写成最终场景，而会先做头脑风暴、归并、拆分和范围收敛。
- 输出必须包含 Seed-to-Scenario Mapping，用来说明每个 seed 被映射为部署型场景、排除项或确认缺口。
- Topology Catalog 和 Topology Source Mapping 会在场景阶段提前确认，避免后续 LC/PC 设计时才发现组网缺口。
- atomic-ops 是唯一原子操作引用对象；REST API、CLI、tool-method 只能作为 atomic-op 的底层调用或观测契约。
- `action_source_refs` 直接引用 atomic-ops `op_id`。
- GATE-2 现在包含自动自检和人工确认，自动检查再发现、Topology、atomic-ops、Operation Path、异常追溯和缺口分类。

Operation Path 的使用口径：

| 内容 | 用户确认重点 |
|---|---|
| `normal_path` | 每个 confirmed scenario 的大步骤、子步骤、操作描述是否符合真实操作流程 |
| `necessity` | `必要 / 可选 / 至少选择一项` 是否准确 |
| 选择组 | 可选子步骤是否完整，是否存在“不能全部跳过”的约束 |
| `abnormal_path` | 每个 confirmed scenario 的异常项是否能追溯到正常路径步骤或明确 N/A 理由 |
| 步骤级 atomic-op | 正常链和异常链每个步骤是否都有 `action_source_ref(s)` / `atomic_op` / `op_id` 并回链场景级 `action_source_refs` |
| `minimal_logic_chain` | 是否保留可选步骤和选择语义，没有被压平成全必做链路 |

策略路由类分析中，用户应重点检查 forwarding action 与 match dimensions 是否拆开建模。

### 12.2 公共因子库安装、消费与回流

CR-20260521-001 已将因子库定义为 `ptm-team` 公共 resource，后续不只服务 `ptm-tde`。

当前口径：

| 项 | 说明 |
|---|---|
| 公共主库 | `resource/factor-libraries/` |
| 组件关联 | `resource/component-resource-links.yaml` |
| 默认安装位置 | `~/.ptm-team/resource/factor-libraries/` |
| 团队共享覆盖 | `PTM_TEAM_RESOURCE_HOME` |
| 项目消费目录 | `mfq/factor-usage/` |

安装 `ptm-tde` agent 时，安装器同步安装关联因子库；卸载时只移除当前项目内的 agent、skill 和规则 managed block，不删除用户级共享 resource。如需清理共享资源，应使用单独的显式资源清理流程。

项目运行时只记录消费结果：

```text
mfq/factor-usage/
├── factor-library-lock.yaml
├── factor-bindings.md
├── candidate-factor-proposals.yaml
└── factor-resolution-report.md
```

使用者需要关注：

- `factor-library-lock.yaml` 记录本项目使用的公共库版本和 checksum。
- `factor-bindings.md` 是下游设计链正式消费的因子绑定。
- `candidate-factor-proposals.yaml` 记录公共库未覆盖的新因子、样本、值域或约束建议。
- `factor-resolution-report.md` 记录查库、复用、扩展、候选和冲突处理结果。
- GATE-3 会检查候选测试因子和候选原子操作是否已经展示给用户，并在 `mfq/candidates/` 中保留逐项确认结果。候选归集阶段可以先写 `decision=pending-review`，但这只表示待评审；存在候选但缺少最终 `decision=confirmed/rejected/modified` 时会阻断。

拓扑绑定与因子绑定并行存在：

```text
kym/scenarios/confirmed-scenarios.md
  -> LC topology_bindings
  -> PC device_id / port_id / link_id
```

接口类型、接口能力可以沉淀为公共因子；真实 `DUT.port1`、`TG.port1` 和链路实例必须保留在拓扑绑定链路中。

生产和更新流程：

```text
来源采集 → 候选建模 → 去重归一 → 因子设计 → 评审激活 → 发布归档 → 安装同步 → 项目消费 → 候选回流
```

生命周期：

| 状态 | 含义 |
|---|---|
| `proposed` | 项目或维护流程提出的候选 |
| `candidate` | 可用于分析草稿，但进入最终 PC 前必须确认或记录风险 |
| `active` | 可被项目正式 lock 和消费 |
| `rejected` | 经评审不进入公共库 |
| `deprecated` | 不再用于新设计，但保留历史追溯和替代关系 |

`ptm-tde` 不直接修改公共主库。项目中发现的新因子必须先写入候选提案，再由公共库维护流程评审后回流到 `ptm-team/resource/`。

---

**修订记录**

| 日期 | 变更 | 处理人 |
|------|------|--------|
| 2026-06-15 | 增补 `tde-feedback` Skill 的问题反馈询问入口、现场反馈一键采集、GitLab 同步、feedback pull 和 field-feedback 闭环说明；同步 `ptm-team-feedback.git` 默认仓库配置与 `submit` 命令。 | Codex |
| 2026-06-01 | CR-010 全局验证修复：§12.1 中 CP02 引用更新为 GATE-2，与三阶段 Gate 门控体系保持一致。 | meta-dev |
