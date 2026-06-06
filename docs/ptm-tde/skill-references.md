# ptm-tde Skill 引用说明

## 文档定位

本文说明 `ptm-tde` 主 Agent 在当前 `ptm-team` 项目中引用的 Skill 清单、阶段归属和职责边界。

引用关系以以下文件为准：

- `agents/ptm-tde.md`：主 Agent 流程、阶段和触发映射。
- `skills/*/SKILL.md`：各 Skill 的职责、输入输出和执行约束。

## 相关设计文档

| 文档 | 用途 |
|------|------|
| `docs/ptm-tde/gate-spec.md` | 门控规范：GATE-1 至 GATE-5 检查项、人工确认项和跨阶段拓扑绑定检查 |
| `docs/ptm-tde/data-flow-spec.md` | 数据实体信息流规格：覆盖全流程 8 个数据实体的生产→消费链路（含已实现和前瞻标注） |

本文件替代源项目中的交付索引视角，只描述组件运行时的 Skill 引用关系，不记录源项目过程状态、变更单或交付清单。

## 主流程 Skill

| 阶段 | Skill | 职责 |
|------|-------|------|
| KYM | `checkpoint-manager` | 执行 GATE-1 Entry Gate 和 GATE-2 KYM Exit Gate 自检与人工确认；保留旧 CP 编号兼容路由。 |
| KYM | `kym` | 执行使命理解访谈（CIDTESTD 8 维度框架），产出 mission-statement.md（用户画像、测试项、风险等结构化信息） |
| KYM | `feature-parser` | 解析特性需求文件，提取结构化需求并生成三至五级目录结构。 |
| KYM | `scenario-discovery` | 重新发现部署型场景，生成 Scenario Chain、Operation Path、Topology、atomic-ops、Knowledge Reference 和确认缺口。 |
| MFQ | `m-analyzer` | 执行 M 分析 v3.0（场景步骤驱动）：逐场景步骤发现测试对象/因子/原子操作，产出 TSP + Scenario-TSP 覆盖矩阵 + 场景步骤标签 + CAE 测试点 + 候选列表。CAE 只引用 `topology_role_refs`，不写真实端口。 |
| MFQ | `f-analyzer` | 执行 F 分析 v3.0（逐 TSP 驱动）：消费覆盖矩阵中 [F→] 标签线索，逐 TSP 场景耦合推理 + 代码依赖 + 耦合矩阵三源合并，生成 CAE 耦合测试点与耦合因子候选。 |
| MFQ | `q-analyzer` | 执行 Q 分析 v3.0（逐 TSP 驱动）：消费覆盖矩阵中 [Q→] 标签线索，逐 TSP 逐 HTSM 维度评估，生成 CAE 质量测试点、工具覆盖评估与质量因子候选。 |
| MFQ | `test-point-integrator` | 整合 M/F/Q 测试点，消费 `factor_bindings`，从 `kym/scenarios/confirmed-scenarios.md` 生成 LC `topology_bindings`，输出逻辑用例、测试数据、工具分析归并和覆盖关系。执行候选汇总：三源候选去重合并与用户批量确认。 |
| MFQ | `design-planner` | 根据 LC、测试数据、CAE 信号、公共因子库约束和 `topology_binding_status` 推荐 PPDCS 设计方法，并输出推断过程。 |
| PPDCS | `design-ppdcs-analyzer` | 协调 PPDCS 逻辑设计，按 LC 统一收敛 PPDCS 设计过程文件和 PC 文件，并要求 PC 真实端口回链到 LC `topology_bindings`。 |
| PPDCS | `process-design` | 针对 P-Process 类型 LC 执行流程图法设计，输出流程模型、路径枚举、触发数据和物理用例。 |
| PPDCS | `parameter-design` | 针对 P-Parameter 类型 LC 执行参数规则设计，输出规则提取、判定结构、参数组和物理用例。 |
| PPDCS | `data-design` | 针对 D-Data 类型 LC 执行等价类与边界值设计，输出值域、等价类、边界选点和物理用例。 |
| PPDCS | `combination-design` | 针对 C-Combination 类型 LC 执行组合设计，输出因子值域、约束、组合压缩策略和物理用例。 |
| PPDCS | `state-design` | 针对 S-State 类型 LC 执行状态图设计，输出状态模型、迁移表、守卫条件和物理用例。 |
| PPDCS | `coverage-verifier` | 执行 SR 到 LC 到 PC、TP 到 PC 的双层覆盖验证，校验公共库因子覆盖，并校验 PC 真实端口能回链到 LC `topology_bindings` 与 `kym/scenarios/confirmed-scenarios.md`。 |
| PPDCS | `deliverable-renderer` | 汇总分析、设计和覆盖结果，生成最终测试方案和测试用例总表，输出因子库版本、样本策略摘要，并保留 `topology_bindings / topology_role / source / fact_status`。 |

### MFQ 候选汇总

test-point-integrator 在整合 M/F/Q 测试点后，将三源候选列表（M 分析的因子候选+原子操作候选、F 分析的耦合因子候选、Q 分析的质量因子候选）去重合并，提交给用户批量确认。确认后的候选因子和原子操作存放在 `mfq/candidates/` 目录。

| 输出文件 | 内容 |
|------|------|
| `mfq/candidates/factor-candidates.md` | M/F/Q 三源因子候选合并（按 `factor_id` 去重），含来源分析器、优先级和用户确认结果 |
| `mfq/candidates/atomic-op-candidates.md` | M 分析原子操作候选，含操作描述、关联对象和确认结果 |

## 公共 Resource 关联

`ptm-tde` 不私有化因子库。公共因子库归档在仓库级 `resource/factor-libraries/`，组件关联由 `resource/component-resource-links.yaml` 声明。安装 `ptm-tde` agent 时，ptm-team 安装器同步安装关联的 `required` / `recommended` factor libraries；卸载时按 `installed_for` 引用关系删除或保留资源。

接口类型、接口能力、配置字段、流量属性和 oracle 可以作为公共因子；真实 `DUT.port1`、`TG.port1` 和 link 实例不是公共因子，必须通过 `topology_role_refs -> topology_bindings -> PC materialization` 链路流转。`topology_bindings` 不替代 `factor_bindings`，两者由不同 Skill 并行消费和校验。

## 交付后回查 Skill

| 阶段 | Skill | 职责 |
|---|---|---|
| delivery 后回查 | `case-retriever` | 基于最终测试用例总表，按需求编号、逻辑用例编号和 feature tag 检索用例。 |

## 扩展分支 Skill

| 分支 | Skill | 职责 |
|---|---|---|
| 需求变更 | `change-impact-analyzer` | 分析需求变更影响范围，支持增量 MFQ、增量设计、增量覆盖验证和交付物更新。 |
| 问题单分析 | `bug-gap-analyzer` | 分析问题单覆盖盲区，回溯遗漏环节，定位补充用例范围并输出流程优化建议。 |

## 资产边界

本轮迁移只维护 Skill 定义文件和必要脚本：

- 保留并同步 `skills/*/SKILL.md`。
- 保留 `skills/checkpoint-manager/scripts/run_checkpoint.py`。
- 不迁移源项目的 `skills/*/templates/*`。
- 删除当前项目旧的 `templates/ptm-tde/` 顶层模板目录。
