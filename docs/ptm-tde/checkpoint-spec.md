# ptm-tde 检查点规范

## 检查点矩阵

| CP | 阶段 | 类型 | 文件 |
|---|---|---|---|
| CP01 | input | auto | `checkpoints/CP01_input_auto.md` |
| CP02 | scenario | auto + manual | `checkpoints/CP02_scenario_auto.md` + `checkpoints/CP02_scenario_manual.md` |
| CP03 | m-analysis | auto | `checkpoints/CP03_m-analysis_auto.md` |
| CP04 | f-analysis | auto | `checkpoints/CP04_f-analysis_auto.md` |
| CP05 | q-analysis | auto | `checkpoints/CP05_q-analysis_auto.md` |
| CP06 | integration | auto | `checkpoints/CP06_integration_auto.md` |
| CP07 | plan | auto | `checkpoints/CP07_plan_auto.md` |
| CP08 | design-ppdcs | auto | `checkpoints/CP08_design-ppdcs_auto.md` |
| CP09 | design-ppdcs | manual | `checkpoints/CP09_design-ppdcs_manual.md` |
| CP10 | design-pc | auto | `checkpoints/CP10_design-pc_auto.md` |
| CP11 | coverage | manual | `checkpoints/CP11_coverage_manual.md` |
| CP12 | delivery | auto | `checkpoints/CP12_delivery_auto.md` |

人工确认点只保留 CP02、CP09、CP11。其他 checkpoint 只做可机器判定的完整性、路径、字段和 trace 检查。

## CP01 Input 自检

CP01 在 input 阶段执行，结果写入：

```text
checkpoints/CP01_input_auto.md
```

状态写入：

```text
doc/STATE.yaml
```

## 检查项

| # | 检查项 | 通过条件 | 阻断处理 |
|---|---|---|---|
| 1 | 需求文件存在 | 显式路径、本地 `input/` 或 wiki 中可找到需求/接口文档 | 提示用户提供需求文件 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 | 提示用户提供特性名 |
| 3 | 原子操作可用 | 全局命令 `atomic-ops` 可执行，或 wiki 有原子操作描述与特性接口文档 | 提示用户补充命令或 wiki 文档 |
| 4 | 防火墙 topo 可用 | 本地 `input/` 或 wiki 可找到 topo | 提示用户提供 topo |
| 5 | 耦合矩阵可用 | 本地 `input/` 或 wiki 可找到耦合矩阵/耦合关系 | 提示用户提供耦合矩阵 |
| 6 | 输出目录就绪 | `analysis/`、`design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/` 可创建 | 路径冲突或无权限时阻断 |

## 脚本

```text
skills/checkpoint-manager/scripts/run_checkpoint.py
```

示例：

```bash
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py CP01 --project-root .
```

## 状态

检查项状态：

| 状态 | 含义 |
|---|---|
| `PASS` | 检查通过 |
| `BLOCKING` | 缺少必要输入或路径不可用 |
| `WAIVED` | 用户接受风险后放行 |

整体结论：

| 状态 | 含义 |
|---|---|
| `PASS` | 可进入 feature-parser |
| `BLOCKED` | 不可继续，需补充输入或修复路径 |

## CP02 Scenario 场景自检与确认

CP02 在 `scenario-discovery` 完成后执行。该检查点必须先完成自动场景自检，再进入人工确认。

结果写入：

```text
checkpoints/CP02_scenario_auto.md
checkpoints/CP02_scenario_manual.md
```

## CP02 自动自检项

| # | 检查项 | 通过条件 | 阻断处理 |
|---|---|---|---|
| 1 | 输入文档类型识别 | 场景产物明确区分 raw requirement / functional scenario seed / deployment scenario draft / confirmed scenario artifact | 回到 `scenario-discovery` 补输入分类 |
| 2 | 场景再发现 | functional scenario seed 已经过头脑风暴、重构、归并、拆分和范围收敛 | 禁止把 seed 一对一改写为最终场景 |
| 3 | Seed-to-Scenario Mapping | 每个 seed 均有映射、排除或缺口记录 | 未映射 seed 必须补齐 |
| 4 | 范围收敛 | 用户约束进入 `scope_constraints`，排除项进入 `out_of_scope_candidates` | 范围不明时阻断 |
| 5 | Topology Catalog | 依赖组网的场景均有 `topology_ref`、来源、Mermaid、设备/端口/链路表 | 缺拓扑时阻断 |
| 6 | TGFW 组网集合 | 存在 `input/TGFW测试组网图集合.md` 时已读取并优先复用 | 未读取时阻断 |
| 7 | atomic-ops 唯一口径 | `source_type=atomic-ops`，`action_source_ref` 直接引用 atomic-ops `op_id` | 出现 REST API / CLI / tool-method 独立引用类型时阻断 |
| 8 | 场景链字段完整 | 每个场景包含目标、原理、前置条件、原子操作、观察点、预期状态、最小逻辑链、退出动作 | 缺字段时补齐 |
| 9 | 正常路径可追溯 | `normal_path` 包含 `step_id / sub_step_ids / operation / necessity / description`，且 `necessity` 仅使用 `必要 / 可选 / 至少选择一项` | 缺字段或取值不规范时补齐 |
| 10 | 选择语义保留 | `至少选择一项` 步骤列出可选子步骤；`minimal_logic_chain` 未把可选步骤或选择组写成必做链路 | 选择语义丢失时补齐 |
| 11 | 异常路径可追溯 | 每条异常路径包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling`，且 `related_normal_steps` 可解析或说明来源 | 缺少异常追溯时补齐 |
| 12 | Knowledge Reference 三态 | 保留 `resolved / missing / unavailable` | 混写或缺失时补齐 |
| 13 | 工具缺口 | 缺失 atomic-ops 或工具能力进入 Tool Abstraction Draft 或 confirmation gaps | 缺口未记录时阻断 |
| 14 | 缺口分类 | `confirmation_gaps` 区分可下传缺口和必须先确认缺口 | 不分类时不得进入 M 分析 |

## CP02 人工确认项

| 确认项 | 说明 |
|---|---|
| 目录结构 | 三级/四级/五级目录是否支撑后续 M/F/Q 分析 |
| 场景列表 | 部署、扩容、维护、可靠性、性能、易用性、配置顺序、异常路径是否覆盖目标范围 |
| Seed-to-Scenario Mapping | 功能初稿如何重构为部署型场景是否可接受 |
| Operation Path | 正常路径的大步骤、子步骤、必要性和选择组是否符合真实操作流程 |
| Topology | `topology_ref`、Mermaid、设备/端口/链路是否符合实际组网 |
| atomic-ops | 每个 `action_source_ref` 是否为真实 atomic-ops `op_id`，能力状态是否合理 |
| Abnormal Path | 异常项是否追溯到具体正常步骤、子步骤、前置条件、环境故障或退出动作 |
| Knowledge Reference | resolved / missing / unavailable 三态是否符合事实 |
| Confirmation Gaps | 哪些缺口必须先补，哪些可下传到 M/F/Q |

整体结论：

| 状态 | 含义 |
|---|---|
| `PASS` | 可进入 M 分析 |
| `BLOCKED` | 场景事实不足，不可继续 |
| `WAIVED` | 用户接受风险后放行，并记录风险项 |
