# ptm-te · 测试执行工程师

> 状态：⬜ 未开始 · 所属项目：ptm-team · Step 1 规划中

## 角色定位

**手工测试执行工程师**。执行终端——是规划层调度和感知层反馈的实际触发者，产出的固化步骤是 ptm-tae 自动化框架的原料。

## 核心职责

| 职责 | 说明 |
|---|---|
| 任务领取 | 从禅道领取测试任务，确认范围和工作量 |
| 用例执行 | 解析用例 → 提取配置步骤和 Check 点 → 调用原子能力执行 |
| 环境准备 | 根据逻辑 Topo 映射物理资源，切换组网 |
| 结果判定 | 配置回显 + 流量结果 + 日志 → Pass/Fail + 判定依据 |
| 执行记录 | 结构化执行日志（配置/流量/结果/异常上下文） |
| 工具反馈 | 执行中发现工具缺失 → 提需求给 ptm-tae |

## 专属 Skill

| Skill | 功能 | 状态 |
|---|---|---|
| `test-execution-skill` | 按行动计划调用工具执行：配置下发 → 流量发送 → Check 结果 | ⬜ 待开发 |

## 调用的公共 Skill 链

```
ptm-te 一次测试执行
  ├── testcase-parse-skill      → 解析用例，提取步骤和 Check 点
  ├── firewall-config-skill     → 下发防火墙配置
  ├── topo-config-skill         → 切换测试组网
  ├── 流量工具                   → 发送测试流量
  ├── result-perception-skill   → 判定 Pass/Fail
  ├── debug-skill（异常时）     → 定位根因
  └── knowledge-base-skill      → 沉淀测试经验
```

## 演进路线

| Step | 能力 |
|---|---|
| Step 1 | ⬜ 角色定义、执行 Skill 开发 |
| Step 2 | 人工主导执行 + 执行记录输出 |
| Step 3 | Agent 主导执行，人工辅助 Check |
| Step 4 | 全自动执行 |

## 依赖

- 上游：ptm-tde（用例输出）、ptm-tae（工具和原子能力）
- 下游：ptm-tae（执行记录 → 自动化翻译原料）
- 公共 Skill：原子能力（防火墙配置/仪表打流）、Topo 管理

## 相关文档

- 蓝图：`docs/ptm-team-blueprint.md` §2.5
