# ptm-tde 运行产物契约

## 目录结构

```text
<feature-project-root>/
├── input/
├── analysis/
│   ├── feature-input/
│   ├── scenarios/
│   ├── m-analysis/
│   ├── f-analysis/
│   ├── q-analysis/
│   ├── integration/
│   ├── plan/
│   ├── factor-usage/
│   └── coverage/
├── design/
│   ├── ppdcs/
│   └── pc/
├── checkpoints/
├── delivery/
└── doc/STATE.yaml
```

## 输入

`input/` 放置原始输入，ptm-tde 不修改该目录。

推荐输入：

- 特性需求文件；
- 防火墙 topo 文件；
- 耦合矩阵；
- 外部接口、CLI 或工具方法参考资料。

## 公共因子库消费记录

公共因子库主库不存放在特性项目 `analysis/` 中。主库由 `ptm-team` 归档在仓库级 `resource/factor-libraries/`，安装后位于 `~/.ptm-team/resource/factor-libraries/` 或 `PTM_TEAM_RESOURCE_HOME/factor-libraries/`。

特性项目仅保存本次消费记录：

```text
analysis/factor-usage/
├── factor-library-lock.yaml
├── factor-bindings.md
├── candidate-factor-proposals.yaml
└── factor-resolution-report.md
```

| 文件 | 内容 |
|---|---|
| `factor-library-lock.yaml` | 本项目锁定的公共因子库 `library_id / version / checksum / source / locked_at` |
| `factor-bindings.md` | TP/LC/TD/PC 对公共因子的实际引用，包含 `factor_id / sample_id / usage_context / materialized_stage` |
| `candidate-factor-proposals.yaml` | 未命中或需扩展的候选因子、样本、约束和目标库建议 |
| `factor-resolution-report.md` | 查库、复用、扩展、候选、冲突和降级处理报告 |

`ptm-tde` 不得在项目运行期间直接修改公共主库；候选因子必须通过公共库维护流程回流到 `resource/factor-libraries/_proposals/`。

真实设备、端口和链路不写入 `analysis/factor-usage/`。它们属于拓扑绑定链路，由 `analysis/scenarios/confirmed-scenarios.md`、LC `topology_bindings` 和 PC 物化字段承载。

## 场景产物字段

`analysis/scenarios/` 下的部署型场景产物必须保留 Scenario Details 与结构化补充两层信息。

Scenario Details 中每个场景至少包含：

| 字段 | 说明 |
|---|---|
| `scenario_goal` | 场景目标 |
| `principle` | 场景原理依据 |
| `preconditions` | 使用该场景前必须成立的条件 |
| `topology_ref` | 关联 Topology；不依赖组网时填 `n/a` 并说明理由 |
| `normal_path` | 正常路径，包含 `step_id / sub_step_ids / operation / necessity / description` |
| `abnormal_path` | 异常路径，包含 `abnormal_item / related_normal_steps / input_or_state / expected_handling` |
| `atomic_operations` | 主流程原子操作序列，直接引用 atomic-ops `op_id` |
| `observation_points` | 观察点 |
| `expected_state` | 预期状态 |
| `minimal_logic_chain` | 最小逻辑链；必须保留可选步骤和 `至少选择一项` 选择语义 |
| `data_overlay_slots` | 后续可叠加测试数据的位置 |
| `exit_action` | 场景结束、清理、回滚或稳定化动作 |

`normal_path.necessity` 只能使用 `必要 / 可选 / 至少选择一项`。异常路径必须通过 `related_normal_steps` 追溯到正常路径的大步骤或子步骤；无法追溯时必须说明异常来源并进入确认缺口或风险说明。

### 确认场景与拓扑绑定基线

`analysis/scenarios/confirmed-scenarios.md` 是真实组网对象的回链基线，至少保留：

| 字段 | 说明 |
|---|---|
| `scenario_id` | 已确认场景编号 |
| `review_status` | 必须为 `confirmed` 才能作为真实端口来源 |
| `topology_ref` | 关联 `topology.yaml` / `topology.mmd` |
| `topology_role` | CAE/LC 使用的抽象角色 |
| `device_id` / `port_id` / `link_id` | 已确认真实组网对象 |
| `source` | 来源，例如 `confirmed-scenarios`、用户确认的 topology 文件或外部 topo 输入 |
| `fact_status` | `confirmed / needs-confirmation` |
| `topology_gap_refs` | 未确认或不可解析对象的缺口编号 |

LC 必须通过 `topology_bindings` 把 `topology_role_refs` 绑定到真实对象；PC 只能消费 LC 绑定表进行物化。

## 分析产物

| 目录 | 内容 |
|---|---|
| `analysis/feature-input/` | 结构化需求与三~五级目录 |
| `analysis/scenarios/` | Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference |
| `analysis/m-analysis/` | M 分析测试点、PPDCS 标注、对象与因子 |
| `analysis/f-analysis/` | 耦合图、耦合测试点 |
| `analysis/q-analysis/` | 质量属性测试点 |
| `analysis/integration/` | 全量测试点、逻辑用例、测试数据、设计计划输入；LC 中保留 `factor_bindings` 与 `topology_bindings` |
| `analysis/plan/` | PPDCS 推断 reasoning |
| `analysis/factor-usage/` | 公共因子库 lock、binding、候选提案和解析报告 |
| `analysis/coverage/` | 需求层与测试点层覆盖报告 |

## 设计产物

每个逻辑用例使用同一个 basename 输出两份设计文件：

```text
design/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
design/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
```

命名规则：

- 四段均来自已确认目录结构和 LC 名称；
- 去除路径分隔符和控制字符；
- 同名冲突追加 `-<LC-ID>`；
- 不创建 `design/<module>/<sub-module>/` 深目录。

### PC 拓扑物化字段

`design/pc/<basename>.md` 中若出现真实组网对象，必须同时保留以下字段：

| 字段 | 说明 |
|---|---|
| `topology_binding_refs` | 回链到 LC `topology_bindings.binding_id` |
| `topology_role` | 角色名，例如 `client`、`dut-ingress`、`dut-egress` |
| `device_id` / `port_id` / `link_id` | 已物化真实对象 |
| `source` | 来源基线，必须能回链到 `confirmed-scenarios.md` |
| `fact_status` | 确认状态，未确认时保留 `needs-confirmation` |

`DUT.port1`、`TG.port1` 或 link 实例不得写入 `factor_bindings`、公共因子 `values` 或公共因子 `sample_id`。

## 交付产物

`delivery/` 只输出：

```text
<特性名>特性测试方案.md
<特性名>特性测试用例.md
```

测试方案是分析过程总结；测试用例是所有测试用例总表。交付物必须保留 `topology_bindings / topology_role / source / fact_status`，并把拓扑绑定展示在组网字段或拓扑绑定小节，不得混入因子取值表。
