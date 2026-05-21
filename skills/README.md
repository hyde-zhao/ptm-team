# skills

Skills 使用帮助，待补充。

## Skill Index

- `atomic-ops-builder-restapi`: 将浏览器 F12 / DevTools 抓到的防火墙 REST API 数据转换为 atomic-ops 的 atomic specs、adapter profile、runner/CLI、测试和发布缓存刷新流程。
- `feature-parser`: 解析 ptm-tde 输入需求，生成结构化需求与三至五级目录。
- `scenario-discovery`: 重新发现部署型场景，生成 Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference 和 `confirmed-scenarios.md`。
- `m-analyzer`: 执行 M 分析，消费公共因子库并输出 `factor_bindings`；CAE 只保留 `topology_role_refs`，不写真实端口。
- `f-analyzer`: 执行 F 分析，合并耦合矩阵、场景耦合和可选代码依赖，生成 CAE 耦合测试点。
- `q-analyzer`: 执行 Q 分析，基于 HTSM 质量属性生成 CAE 质量测试点。
- `test-point-integrator`: 整合 M/F/Q 测试点，生成 LC、测试数据、覆盖关系，并从 `confirmed-scenarios.md` 生成 LC `topology_bindings`。
- `design-planner`: 根据 LC、测试数据、CAE 信号、公共因子约束和拓扑绑定状态推荐 PPDCS 设计方法。
- `design-ppdcs-analyzer`: 协调五类 PPDCS 设计 Skill，按 LC 收敛 PPDCS 设计过程和 PC 输出。
- `process-design`: 针对 P-Process 类型 LC 生成流程模型、路径枚举、触发数据和物理用例。
- `parameter-design`: 针对 P-Parameter 类型 LC 生成规则提取、判定结构、参数组和物理用例。
- `data-design`: 针对 D-Data 类型 LC 生成等价类、边界值、选点结果和物理用例。
- `combination-design`: 针对 C-Combination 类型 LC 生成因子组合、约束、压缩策略和物理用例。
- `state-design`: 针对 S-State 类型 LC 生成状态模型、迁移表、守卫条件和物理用例。
- `coverage-verifier`: 执行 SR→LC→PC、TP→PC 双层覆盖验证，校验公共因子覆盖和 PC 真实端口到 LC `topology_bindings` / `confirmed-scenarios.md` 的回链。
- `deliverable-renderer`: 生成最终测试方案和测试用例总表，保留 `factor_bindings`、`topology_bindings`、`topology_role`、`source`、`fact_status`。
- `case-retriever`: 交付后按需求编号、逻辑用例编号和 feature tag 检索测试用例。
- `change-impact-analyzer`: 分析需求变更影响范围，支持增量 MFQ、设计、覆盖和交付更新。
- `bug-gap-analyzer`: 根据问题单回溯覆盖盲区，定位补充用例范围。

## ptm-tde Cross-Stage Contracts

- `factor_bindings` 是公共因子消费主契约；接口类型、接口能力、配置字段、流量属性、状态和 oracle 可作为公共因子。
- `topology_bindings` 与 `factor_bindings` 并行存在，用于真实组网对象回链，不替换公共因子规则。
- CAE / TP 阶段只引用 `topology_role_refs`；真实 `DUT.port1`、`TG.port1` 和 link 实例只能从 `analysis/scenarios/confirmed-scenarios.md` 进入 LC `topology_bindings`。
- PPDCS / PC 阶段消费 LC `topology_bindings` 进行物化；PC 中任何真实端口必须能回链到 LC 和 `confirmed-scenarios.md`。
- coverage / delivery 阶段必须保留 `topology_bindings / topology_role / source / fact_status`，不得把 `needs-confirmation` 提升为 `confirmed`。
- 真实端口和真实链路不得写入公共因子 `values`、`sample_id`、样例值或 factor group。
