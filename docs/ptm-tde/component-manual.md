# ptm-tde 组件手册

## 定位

ptm-tde 是 ptm-team 体系中的 MFQ&PPDCS 测试设计组件。它只维护 Agent 与 Skill 的调用关系、运行产物契约和组件级说明，不处理安装器、安装清单或平台投影。

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
- 安装由 ptm-team 控制。

## 关键调用关系

1. `checkpoint-manager` 执行 CP01 input 自检。
2. `feature-parser` 解析需求并固化目录结构。
3. `scenario-discovery` 构建 Scenario Chain、Topology、Action Source 和 Knowledge Reference。
4. `m-analyzer`、`f-analyzer`、`q-analyzer` 分别生成 M/F/Q 测试点。
5. `test-point-integrator` 归集为逻辑用例和测试数据。
6. `design-planner` 选择 PPDCS 方法。
7. `design-ppdcs-analyzer` 统一调度五类 PPDCS 方法 Skill，并收敛单文件输出。
8. `coverage-verifier` 校验覆盖。
9. `deliverable-renderer` 渲染最终两份 Markdown。
