---
name: checkpoint-manager
description: >-
  ptm-tde 运行检查点管理：执行 CP01 input 自检和 CP02 scenario 场景自检，
  校验运行目录、需求文件、atomic-ops、wiki 兜底、防火墙 topo、耦合矩阵、
  场景再发现、Topology Catalog、Seed-to-Scenario Mapping 与确认缺口。
  触发词包括：CP01、CP02、自检、场景自检、检查点、输入检查、checkpoint。
  适用场景：MFQ input 阶段和阶段切换前的运行产物校验。
argument-hint: "可选：feature_name=<特性名> requirement=<需求文件路径>"
user-invokable: true
status: active
---

## 目标

在特性项目根目录执行检查点，确保 ptm-tde 后续分析有足够输入事实。当前必须实现 CP01 input 自检，并维护 CP02 scenario 场景自检与人工确认口径。

ptm-tde 只维护 Agent 与 Skill 调用关系，不负责安装。检查点脚本属于本 Skill 私有资产，路径固定为：

```text
skills/checkpoint-manager/scripts/run_checkpoint.py
```

不得把 checkpoint 脚本放到仓库根 `scripts/`。

## CP01 Input 自检

### Entry Criteria

| 条目 | 要求 |
|---|---|
| 特性项目根目录 | 当前 cwd 是单个特性项目根目录 |
| 输入目录 | `input/` 存在且只读对待 |
| 状态目录 | `doc/` 可创建，状态写入 `doc/STATE.yaml` |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| 1 | 需求文件存在 | 用户显式路径存在，或 `input/` 下存在需求文件，或 wiki 可找到特性接口/需求文档 | 若三处均不存在，提示用户提供需求文件 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 | 无法确定时提示用户给出特性名 |
| 3 | 原子操作入口可用 | 全局命令 `atomic-ops` 可执行 | 不可用时查 wiki 中原子操作描述文档和特性接口文档 |
| 4 | 防火墙 topo 可用 | `input/` 下存在 topo 文件，或 wiki 可找到 topo 描述 | 两者均不存在时提示用户提供 |
| 5 | 耦合矩阵可用 | `input/` 下存在耦合矩阵，或 wiki 可找到耦合矩阵/耦合关系文档 | 两者均不存在时提示用户提供 |
| 6 | 输出目录就绪 | 可创建 `analysis/`、`design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/` | 无权限或路径冲突时阻断 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 检查结果 | `checkpoints/CP01_input_auto.md` 已生成 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `doc/STATE.yaml` 记录 `current_step: input` 与 CP01 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| CP01 检查结果 | `checkpoints/CP01_input_auto.md` |
| 状态文件 | `doc/STATE.yaml` |

## Wiki 兜底规则

当本地 `input/` 中缺少原子操作、topo 或耦合矩阵信息时，必须按以下顺序查询 wiki：

1. 原子操作描述文档；
2. 特性接口文档；
3. 防火墙 topo / 组网描述；
4. 耦合矩阵或功能耦合关系文档。

wiki 查询结果只能作为只读引用写入检查点证据，不得回写 wiki。

## 脚本用法

```bash
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py CP01 --project-root .
```

可选参数：

```bash
--feature-name "<特性名>"
--requirement "input/<需求文件>"
--wiki-index "<wiki导出索引或检索结果>"
```

## Gotchas

- `atomic-ops` 是全局命令，不允许硬编码某个项目路径。
- CP01 发现 wiki 缺失时应提示用户提供材料，不得虚构 topo、接口或耦合矩阵。
- 检查点文件属于特性项目运行产物，写入 `checkpoints/`，不是 ptm-tde 仓库 `process/checks/`。
- `input/` 只读；若需派生 Markdown 或结构化摘要，写入 `analysis/feature-input/`。

## 验收标准

- [ ] CP01 覆盖需求文件、特性名、atomic-ops、wiki 兜底、topo、耦合矩阵和输出目录
- [ ] 检查结果写入 `checkpoints/CP01_input_auto.md`
- [ ] 脚本位于 `skills/checkpoint-manager/scripts/run_checkpoint.py`
- [ ] 不依赖安装器或安装清单

## CP02 Scenario 场景自检

CP02 在 `scenario-discovery` 完成后执行，先生成场景自检结果，再进入人工确认。CP02 必须防止功能种子被直接当作最终场景交付。

### Entry Criteria

| 条目 | 要求 |
|---|---|
| 场景产物存在 | `analysis/scenarios/confirmed-scenarios.md` 或用户指定的部署型场景文件存在 |
| 目录结构可读 | `analysis/feature-input/directory-structure.md` 或等价目录结构产物可读 |
| 输入分类完成 | 场景产物包含 `input_document_classification` 或等价输入文档类型识别 |
| 组网输入已处理 | 若存在 `input/TGFW测试组网图集合.md` 或 topo 文件，场景产物必须说明读取结果 |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| 1 | 输入文档类型识别 | 覆盖 raw requirement / functional scenario seed / deployment scenario draft / confirmed scenario artifact，且每份输入有处理动作 | 缺失时回到 `scenario-discovery` 补分类 |
| 2 | 功能种子再发现 | functional scenario seed 已进入场景再发现、头脑风暴、重构与范围收敛，不存在 seed 一对一改写 | 阻断进入 M 分析，要求补 `Seed-to-Scenario Mapping` |
| 3 | Seed-to-Scenario Mapping | 每个 seed 有 split / merge / expand / narrow / out_of_scope / confirmation_gap 处理结论 | 未映射 seed 必须补齐或进入缺口 |
| 4 | 范围收敛 | 用户约束已进入 `scope_constraints`；被排除内容进入 `out_of_scope_candidates`，例如 IPv6 不在 IPv4-only 范围内 | 缺失时要求补范围决策 |
| 5 | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源、Mermaid、设备/端口/链路表；优先使用 TGFW 组网集合 | 缺失拓扑或自造拓扑时阻断 |
| 6 | atomic-ops 唯一口径 | `source_type=atomic-ops`；`action_source_ref` 直接引用 atomic-ops `op_id`；REST API / CLI / tool-method 未作为独立引用类型 | 出现旧口径时阻断并要求替换 |
| 7 | 场景链完整 | 每个场景包含 `scenario_goal / principle / preconditions / atomic_operations / observation_points / expected_state / minimal_logic_chain / exit_action` | 缺字段时补场景链 |
| 8 | 正常路径可追溯 | `normal_path` 包含 `step_id / sub_step_ids / operation / necessity / description`，且 `necessity` 仅使用 `必要 / 可选 / 至少选择一项` | 缺失字段或取值不规范时补路径建模 |
| 9 | 选择组完整 | 所有 `至少选择一项` 步骤列出可选择子步骤，并说明不能全部跳过；`minimal_logic_chain` 未把选择组或可选步骤写成必做链路 | 选择关系丢失时回到 `scenario-discovery` 补结构化语义 |
| 10 | 异常路径可追溯 | 每条异常路径包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`；`related_normal_steps` 可解析到正常路径步骤或说明来源 | 缺少追溯时补异常路径或进入确认缺口 |
| 11 | Knowledge Reference 三态 | 知识引用保留 `resolved / missing / unavailable`，不得把缺失知识当作已确认事实 | 缺失时补三态或确认缺口 |
| 12 | Tool Gap | 未满足的 atomic-ops 或工具能力进入 `Tool Abstraction Draft` 或 `confirmation_gaps` | 缺口未记录时阻断 |
| 13 | Confirmation Gaps | 所有不确定事实显式列出，并区分可下传缺口和必须先确认缺口 | 未分类时不得进入 M 分析 |
| 14 | 输出质量检查 | 场景产物末尾包含 scenario-discovery 输出质量检查结果，且覆盖路径必要性、选择组、异常追溯和最小逻辑链一致性 | 缺失时补自检结果 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 自动自检结果 | `checkpoints/CP02_scenario_auto.md` 或等价自检结果已生成 |
| 人工确认稿 | `checkpoints/CP02_scenario_manual.md` 已生成并展示给用户 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `doc/STATE.yaml` 记录 `current_step: scenario` 与 CP02 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| 场景自检结果 | `checkpoints/CP02_scenario_auto.md` |
| 场景人工确认稿 | `checkpoints/CP02_scenario_manual.md` |
| 场景产物 | `analysis/scenarios/confirmed-scenarios.md` 或用户指定部署型场景文件 |

### Gotchas

- CP02 不是只看“有场景列表”；必须验证场景是否从 seed 经过再发现和收敛。
- `action_source_refs` 是兼容字段，但其值必须是 atomic-ops `op_id`。
- REST API / CLI / tool-method 只能作为 atomic-op 的调用或观测契约，不能作为独立引用类型。
- TGFW 组网集合存在时不得绕过；集合外拓扑只能进入 `confirmation_gaps`。
- CP02 必须检查 `normal_path` 大步骤/子步骤结构、必要性枚举和 `abnormal_path.related_normal_steps`，避免场景链变成不可追溯的线性流程。
- 可选步骤和 `至少选择一项` 选择组必须下传到 `minimal_logic_chain` 与结构化补充；不允许在自检中被视为普通必做步骤。
- CP02 人工确认前必须把必须先确认的缺口和可下传缺口分开。
