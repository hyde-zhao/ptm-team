---
checkpoint: "HLD"
status: "confirmed"
source_hld: "process/HLD.md"
version: "7.1"
created_at: "2026-04-24T14:20:28+08:00"
created_by: "meta-po"
confirmed_by: "user (implicit via continuing testing and delivery after CR-008 HLD refresh)"
confirmed_at: "2026-04-24T14:20:28+08:00"
---

# HLD 检查点：ptm-tde v7.1

## 本次设计结论

1. 平台范围收缩为 **Claude Code + Codex**。
2. 安装范围细化为 **project scope + user scope**，其中 user scope 采用规则文件合并策略。
3. 应用场景升级为 **原子操作 - 观察点 - 最小逻辑链** 模型，并把 REST API / CLI 工具契约纳入动作源输入。
4. PPDCS 五类设计方法统一要求输出**完整分析过程**。
5. 用例检索收敛为 **需求 / 逻辑用例 / 功能分类标签** 三类结构化检索。
6. 知识链路收敛为 **只读 staged query**，不承担知识入库和远端索引维护。
7. 最终交付新增 **工具分析表**，明确区分“已使用工具”和“待实现工具”。
8. 场景确认阶段新增 **Topology Modeling** 子结构：按 `Topology / Device / Port / Link` 建模，并输出 `topology.mmd + topology.yaml + 三张清单表`。
9. 保持**单 Agent** 架构，不拆分 HLD。

## 重点评审项

| 项目 | 当前方案 | 你需要确认什么 |
|---|---|---|
| 平台范围与安装 | Claude Code + Codex，支持 project / user 两种 scope | 是否认可按“project 先落地，user 合并后补”的策略推进 |
| 场景模板 | 原子操作 + 观察点 + 最小逻辑链 + 动作源契约 | 是否认可把 REST API / CLI 工具说明作为正式输入 |
| 知识治理 | 只读 staged query | 是否认可当前阶段不做知识入库、索引维护和知识写回 |
| 设计输出 | 五类 PPDCS 方法均输出完整分析过程 | 是否满足你对“过程可审计”的要求 |
| 用例检索 | 独立 Skill + 轻量结构化索引 | 是否认可只保留需求 / LC / 功能分类标签检索 |
| 工具分析交付 | 新增 `<feature>-工具分析表.md`，并分别输出已使用工具与待实现工具的用途、接口和行为 | 是否认可把工具分析表作为正式交付件，并采用“双分区 + 场景回链”模型 |
| Topology 建模 | `scenario-discovery` 在场景确认时同时输出 Mermaid/YAML 组网图、`topology_ref` 和设备/端口/链路清单 | 是否认可把组网确认并入场景确认，而不是后置到设计阶段 |
| HLD 拆分 | 保持单份 HLD | 是否认可当前不拆分 |

## 进入下一阶段的条件

- 你确认 `process/HLD.md` v7.1 可接受；
- 若有修改意见，回到 HLD 修订；
- 只有在 HLD confirmed 后，才会进入 `story-planning`。
