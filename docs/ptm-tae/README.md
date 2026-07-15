# ptm-tae · 自动化工程师

> 状态：🔄 Step 1 进行中 · 所属项目：ptm-team

## 角色定位

**自动化工程师 / 工具开发 / 公共基础设施维护者**。团队的基础设施层，所有公共 Skill 和工具的唯一开发和维护方。

## 核心职责

| 职责 | 说明 |
|---|---|
| 工具开发 | 开发防火墙配置/仪表打流/Topo 管理等原子能力和 Skill |
| 自动化框架 | 管理自动化用例库、调度执行、分析失败并自修复 |
| 回归执行 | 每日版本转测自动触发回归 |
| 自动化翻译 | 读取 ptm-te 执行记录 → 翻译为 Python 自动化脚本 |
| 公共基础设施 | 统一维护公共 Skill 和工具，所有 Agent 按需调用 |

## 专属 Skill

| Skill | 功能 | 优先级 | 状态 |
|---|---|---|---|
| `automation-framework-skill` | 管理自动化用例库、调度执行、分析失败并自修复 | 高 | ⬜ |
| `tool-dev-skill` | AI 辅助编写工具代码（Python/PowerShell） | 高 | ⬜ |
| `script-regression-skill` | 每日版本转测自动触发回归 | 中 | ⬜ |
| `lab-environment-skill` | 实验室设备台账查询、仪表可用性检查 | 中 | ⬜ |
| `device-install-skill` | PXE 工具完成防火墙裸机安装、固件升级 | 必选 | ⬜ |

## AI 测试工作流（4 阶段流水线）

| 阶段 | 名称 | 状态 | 进度 |
|---|---|---|---|
| 01 | Guided Execution — 指导 AI 完成手工测试 | ✅ | 4/4 |
| 02 | Intent Capture — 完善测试意图与行为 | 🔄 | 2/4 |
| 03 | Knowledge Distillation — Agent 阅读、总结、沉淀 | ⬜ | 0/4 |
| 04 | Automation Crystallization — 单文件 Python 脚本产出 | ⬜ | 0/4 |

> 总体进度：38%

## 现有资产（auto_factory_agent）

| 类别 | 内容 |
|---|---|
| Skills | `auto-factory-env`、`ngfw-install`、`env-check`、`task-mng`、`report-mng`、`case-mng` |
| 脚本 | `export_factory_history.py`、`find_nearest_testcase.py`、`fix_duplicate_pytest_case_name.py`、`update_marks.py`、`skills_manager.py` |

## 依赖

- 上游：ptm-te（执行记录原料）
- 下游：全部 Agent（公共 Skill 和工具消费方）
- 外部：防火墙硬件、仪表、交换机

## 相关文档

- 蓝图：`docs/ptm-team-blueprint.md` §2.6
