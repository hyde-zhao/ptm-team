# ptm-tde 检查点规范

## 检查点矩阵

| CP | 阶段 | 类型 | 文件 |
|---|---|---|---|
| CP01 | input | auto | `checkpoints/CP01_input_auto.md` |
| CP02 | scenario | manual | `checkpoints/CP02_scenario_manual.md` |
| CP03 | m-analysis | auto | `checkpoints/CP03_m-analysis_auto.md` |
| CP04 | f-analysis | auto | `checkpoints/CP04_f-analysis_auto.md` |
| CP05 | q-analysis | auto | `checkpoints/CP05_q-analysis_auto.md` |
| CP06 | integration | auto | `checkpoints/CP06_integration_auto.md` |
| CP07 | plan | auto | `checkpoints/CP07_plan_auto.md` |
| CP08 | design-ppdcs | auto | `checkpoints/CP08_design-ppdcs_auto.md` |
| CP09 | design-ppdcs | manual | `checkpoints/CP09_design-ppdcs_manual.md` |
| CP10 | design-pc | auto | `checkpoints/CP10_design-pc_auto.md` |
| CP11 | coverage | manual | `checkpoints/CP11_coverage_manual.md` |
| CP12 | delivery | auto | `checkpoints/CP12_delivery_auto.md` |

人工确认点只保留 CP02、CP09、CP11。其他 checkpoint 只做可机器判定的完整性、路径、字段和 trace 检查。

## CP01 Input 自检

CP01 在 input 阶段执行，结果写入：

```text
checkpoints/CP01_input_auto.md
```

状态写入：

```text
doc/STATE.yaml
```

## 检查项

| # | 检查项 | 通过条件 | 阻断处理 |
|---|---|---|---|
| 1 | 需求文件存在 | 显式路径、本地 `input/` 或 wiki 中可找到需求/接口文档 | 提示用户提供需求文件 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 | 提示用户提供特性名 |
| 3 | 原子操作可用 | 全局命令 `atomic-ops` 可执行，或 wiki 有原子操作描述与特性接口文档 | 提示用户补充命令或 wiki 文档 |
| 4 | 防火墙 topo 可用 | 本地 `input/` 或 wiki 可找到 topo | 提示用户提供 topo |
| 5 | 耦合矩阵可用 | 本地 `input/` 或 wiki 可找到耦合矩阵/耦合关系 | 提示用户提供耦合矩阵 |
| 6 | 输出目录就绪 | `analysis/`、`design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/` 可创建 | 路径冲突或无权限时阻断 |

## 脚本

```text
skills/checkpoint-manager/scripts/run_checkpoint.py
```

示例：

```bash
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py CP01 --project-root .
```

## 状态

检查项状态：

| 状态 | 含义 |
|---|---|
| `PASS` | 检查通过 |
| `BLOCKING` | 缺少必要输入或路径不可用 |
| `WAIVED` | 用户接受风险后放行 |

整体结论：

| 状态 | 含义 |
|---|---|
| `PASS` | 可进入 feature-parser |
| `BLOCKED` | 不可继续，需补充输入或修复路径 |
