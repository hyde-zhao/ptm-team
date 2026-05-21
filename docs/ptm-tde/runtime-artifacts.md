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

## 分析产物

| 目录 | 内容 |
|---|---|
| `analysis/feature-input/` | 结构化需求与三~五级目录 |
| `analysis/scenarios/` | Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference |
| `analysis/m-analysis/` | M 分析测试点、PPDCS 标注、对象与因子 |
| `analysis/f-analysis/` | 耦合图、耦合测试点 |
| `analysis/q-analysis/` | 质量属性测试点 |
| `analysis/integration/` | 全量测试点、逻辑用例、测试数据、设计计划输入 |
| `analysis/plan/` | PPDCS 推断 reasoning |
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

## 交付产物

`delivery/` 只输出：

```text
<特性名>特性测试方案.md
<特性名>特性测试用例.md
```

测试方案是分析过程总结；测试用例是所有测试用例总表。
