# ptm-tde 组件手册

## 定位

ptm-tde 是 ptm-team 体系中的 MFQ&PPDCS 测试设计组件。它只维护 Agent 与 Skill 的调用关系、运行产物契约和组件级说明；安装器、安装清单、平台投影和公共 resource 安装由 ptm-team 统一控制。

## 主流程

| 步骤 | 阶段 | 主要 Skill | 产物目录 |
|---|---|---|---|
| 1 | input | `checkpoint-manager`、`feature-parser` | `checkpoints/`、`analysis/feature-input/` |
| 2 | scenario | `scenario-discovery` | `analysis/scenarios/` |
| 3 | m-analysis | `m-analyzer` | `analysis/m-analysis/` |
| 4 | f-analysis | `f-analyzer` | `analysis/f-analysis/` |
| 5 | q-analysis | `q-analyzer` | `analysis/q-analysis/` |
| 6 | integration | `test-point-integrator` | `analysis/integration/` |
| 7 | plan | `design-planner` | `analysis/plan/` |
| 8 | design-ppdcs | `design-ppdcs-analyzer` + 五类设计 Skill | `design/ppdcs/` |
| 9 | design-pc | 五类设计 Skill | `design/pc/` |
| 10 | coverage | `coverage-verifier` | `analysis/coverage/` |
| 11 | delivery | `deliverable-renderer` | `delivery/` |

## 使用边界

- 输入目录 `input/` 只读。
- 所有运行产物直接生成在特性项目根目录下的规范目录。
- 禁止使用 `.output/`。
- 最终交付只包含测试方案和测试用例。
- 安装由 ptm-team 控制；安装 `ptm-tde` agent 时，安装器同时读取 `resource/component-resource-links.yaml` 并安装关联公共因子库。
- 公共因子库是仓库级 `resource/` 资产，不是 ptm-tde 私有目录；项目运行时只在 `analysis/factor-usage/` 记录 lock、binding、候选提案和解析报告。
- 真实设备、端口和链路不是公共因子；它们必须通过 `topology_role_refs -> topology_bindings -> PC materialization` 链路从已确认场景进入 LC 和 PC。

## 关键调用关系

1. `checkpoint-manager` 执行 CP01 input 自检。
2. `feature-parser` 解析需求并固化目录结构。
3. `scenario-discovery` 从需求或 functional scenario seed 重新发现部署型场景，构建 Scenario Chain、Operation Path、Topology、atomic-ops 和 Knowledge Reference。
4. `m-analyzer` 先读取公共因子库，生成 `factor_bindings`、复用/扩展/候选报告，并在 CAE 中只保留 `topology_role_refs`。
5. `test-point-integrator` 归集为逻辑用例和测试数据，透传 `factor_bindings`，并从 `analysis/scenarios/confirmed-scenarios.md` 生成 LC `topology_bindings`。
6. `design-planner` 选择 PPDCS 方法，同时消费因子约束和拓扑绑定状态。
7. `design-ppdcs-analyzer` 统一调度五类 PPDCS 方法 Skill，并收敛单文件输出。
8. 五类设计 Skill 消费 LC `topology_bindings`，PC 中真实端口必须能回链到 LC 和已确认场景。
9. `coverage-verifier` 校验覆盖、拓扑绑定回链和 `needs-confirmation` 状态。
10. `deliverable-renderer` 渲染最终两份 Markdown，并保留 `topology_bindings / topology_role / source / fact_status`。

## 拓扑绑定契约

| 阶段 | 允许写入 | 不允许写入 |
|---|---|---|
| M/F/Q CAE | `topology_role_refs` | 真实 `DUT.port1`、`TG.port1`、link 实例 |
| integration LC | `topology_bindings`、`source`、`fact_status` | 将真实端口写入 `factor_bindings` |
| PPDCS / PC | 从 LC 绑定表物化的 `device_id / port_id / link_id` | 无来源的真实端口 |
| coverage / delivery | 保留绑定链路和未确认状态 | 用统计或渲染把 `needs-confirmation` 改为 confirmed |
