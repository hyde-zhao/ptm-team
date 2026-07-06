# Skills

ptm-team 平台下所有 Skill 的索引、使用帮助与跨阶段契约。本文件覆盖 ptm-tde 测试设计工具链（含门控 checkpoint-manager）、自动化工厂（2 个运维 Skill）和扩展工具（流量生成、ptm-atomic 构建、反馈采集、NGFW 安装），共 25 个 Skill。

## 使用说明

- **安装**：通过 `ptm-team install claude --agent ptm-tde` 一键安装 ptm-tde Agent 及其关联的全部 Skill 和公共因子库。
- **调用**：Skill 由 ptm-tde Agent 按三阶段框架自动调度，用户只需在 Gate 确认点（GATE-2/GATE-3/GATE-4）确认输出。
- **索引**：下方 Skill Index 列出每个 Skill 的角色和在流程中的位置，Cross-Stage Contracts 定义 Skill 间的数据契约。
- **版本**：Skill 当前未独立版本化，以 ptm-tde Agent 版本和 CR 变更记录为准（参见 `process/STATE.md` 人类摘要、`process/changes/CR-INDEX.json` CR 索引；机器状态入口 `process/state/STATE.current.json` 待建立后切换）。

## Skill Index

- `ptm-atomic-builder-restapi`: 将浏览器 F12 / DevTools 抓到的防火墙 REST API 数据转换为 ptm-atomic 的 atomic specs、adapter profile、runner/CLI、测试和发布缓存刷新流程。
- `feature-parser`: 解析 ptm-tde 输入需求，生成结构化需求与三至五级目录。
- `kym`: 执行 Know Your Mission（使命理解），使用 CIDTESTD 8 维度结构化访谈产出 mission-statement.md。
- `scenario-discovery`: 重新发现部署型场景，生成 Scenario Chain、Operation Path、Topology、ptm-atomic、Knowledge Reference 和 `confirmed-scenarios.md`。
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
- `checkpoint-manager`: ptm-tde 三阶段门控检查管理，按阶段执行 Gate 检查（Entry/KYM Exit/MFQ Exit/PPDCS Exit/Exit Gate），含 `.input` resolver、多特性阻断与字段级 machine-baseline。
- `tde-feedback`: ptm-tde 真实使用反馈采集与同步，支持 collect/submit 采集包、GitLab 同步、feedback pull，并自动登记 RUN-EXEC / ISSUE / coverage gap。
- `traffic-skill`: 操作 Ixia-C 发流 agent，通过 traffic CLI 发起 L2-L4 流量、收集统计、校验丢包率，按 ptm-atomic TG 原子操作规范消费结果。
- `ngfw-install`: 通过串口对指定 ngfw（tgfw/防火墙）设备进行卸载和安装。
- `auto-factory-env`: 自动化工厂固化环境信息查询，获取设备的串口、管理 IP 和型号等信息。

## ptm-tde Cross-Stage Contracts

- `factor_bindings` 是公共因子消费主契约；接口类型、接口能力、配置字段、流量属性、状态和 oracle 可作为公共因子。
- `topology_bindings` 与 `factor_bindings` 并行存在，用于真实组网对象回链，不替换公共因子规则。
- CAE / TP 阶段只引用 `topology_role_refs`；真实 `DUT.port1`、`TG.port1` 和 link 实例只能从 `kym/scenarios/confirmed-scenarios.md` 进入 LC `topology_bindings`。
- PPDCS / PC 阶段消费 LC `topology_bindings` 进行物化；PC 中任何真实端口必须能回链到 LC 和 `confirmed-scenarios.md`。
- coverage / delivery 阶段必须保留 `topology_bindings / topology_role / source / fact_status`，不得把 `needs-confirmation` 提升为 `confirmed`。
- 真实端口和真实链路不得写入公共因子 `values`、`sample_id`、样例值或 factor group。
