---
cr_id: "CR-008"
status: "approved"
impact_level: "medium"
rollback_to: "solution-design"
approval_result: "approved-by-user"
created_at: "2026-04-24T13:52:55+08:00"
created_by: "meta-po"
approved_by: "user"
approved_at: "2026-04-24T13:52:55+08:00"
source: "user"
linked_issue: ""
---

## 变更描述

用户要求在"项目应用场景确认"环节新增**组网建模（Topology Modeling）**能力，使场景讨论阶段可产出可视化组网图并纳入人工确认。需在 `process/HLD.md` v7 基础上增量刷新到 v7.1，将组网建模作为场景模型的子结构固化为正式设计对象。

## 组网对象范围

- **设备类型**：DUT（防火墙，被测对象）、TG（流量发生器）、MOCK（可为服务端或客户端的模拟器）、Switch（交换机）
- **端口 Port**：每设备含 1 个或多个 Port，每 Port 有属性（类型/IP/VLAN/Zone/速率/状态）
- **链路 Link**：Port 之间的连线，两端点恰好各 1 个 Port
- **编号规则**：多实例场景下 `DUT1/DUT2`、`DUT1.Port1/DUT1.Port2`、`Link1/Link2` 全局唯一
- **属性矩阵**：按设备 kind 区分必填/可选属性集

## 五维度影响分析

| 维度 | 评估问题 | 受影响对象 | 结论 | 处理动作 |
|------|----------|-----------|------|---------|
| 需求层 | 是否新增 REQ-* | `process/REQUIREMENTS.md` | true | 新增 REQ-028「场景组网建模」，由 meta-pm 在 HLD 刷新后同步 |
| 场景层 | 是否改变场景模型 | `process/USE-CASES.md` / SCENARIO-CHAIN | true | USE-CASES 新增 Topology 子结构，最小逻辑链引用 `topology_ref` |
| 计划层 | 是否改变 Phase/Wave/Story | `process/STORY-BACKLOG.md` | true | 新增 Story：Topology 建模规范 / scenario-discovery skill 扩展 / topology 校验器（可选合并） |
| 安全层 | 是否引入新权限或高风险动作 | 安全边界 | false | 组网图为纯建模与 Mermaid/YAML 文本产物，无执行权限扩展 |
| 交付层 | 是否需新增交付物或回归子集 | `delivery/` / `skills/scenario-discovery/templates/` | true | 新增 `skills/scenario-discovery/templates/topology.yaml.tmpl`、`skills/scenario-discovery/templates/topology.mmd.tmpl`；最小回归覆盖 scenario-discovery 产出 |

## 回退决策

- **影响范围**：局部（场景建模层 + scenario-discovery skill）
- **回退到阶段**：`solution-design`
- **需要重新确认的对象**：
  - `process/HLD.md`（增量至 v7.1，新增 §3.7 场景组网建模）
  - `process/USE-CASES.md`（新增 3 类组网样例：单 DUT 双端口 / 双 DUT HA / 带 Switch）
  - `skills/scenario-discovery/SKILL.md`（产出契约扩展）
  - `process/STORY-BACKLOG.md`（追加 Topology 相关 Story）

## 设计约束（HLD 增量必须包含）

1. **对象模型**：Topology / Device / Port / Link 四级结构，字段对齐 kind 特化矩阵
2. **命名规则**：`<KIND><N>` / `<DeviceID>.Port<N>` / `Link<N>`，多实例强制编号
3. **可视化**：Mermaid `flowchart` 为主（L1 逻辑拓扑），YAML 结构化同源双出；必要时 L2 端口级子图
4. **追踪链闭合**：Topology 与 Scenario Chain / Action Source / 工具分析表 / PPDCS-State 的映射关系显式化
5. **校验规则**：Link 两端点约束、Port 归属唯一、DUT ≥2 Port、ID 全局唯一
6. **确认产物**：设备清单表 + 端口清单表 + 链路清单表 + Mermaid 图 + 人工确认清单（4 项）
7. **输出路径**：`.output/scenarios/<scene-id>/topology.{mmd,yaml}`，不落入项目根目录

## 不在本次范围

- 拓扑仿真/链路实时探测
- 图数据库持久化
- 跨场景拓扑复用的继承/模板机制（留待 v8 评估）

## 下一步

- [x] meta-po 起 CR 并更新 STATE（本文件）
- [ ] meta-se 刷新 `process/HLD.md` → v7.1，补入 §3.7
- [ ] 用户确认 v7.1 后，meta-se 追加 Story 至 BACKLOG，进入 story-planning
