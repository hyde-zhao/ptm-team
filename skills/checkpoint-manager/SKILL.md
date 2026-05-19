---
name: checkpoint-manager
description: >-
  ptm-tde 运行检查点管理：执行 CP01 input 自检，校验运行目录、需求文件、
  atomic-ops、wiki 兜底、防火墙 topo 与耦合矩阵可用性。
  触发词包括：CP01、自检、检查点、输入检查、checkpoint。
  适用场景：MFQ input 阶段和阶段切换前的运行产物校验。
argument-hint: "可选：feature_name=<特性名> requirement=<需求文件路径>"
user-invokable: true
status: active
---

## 目标

在特性项目根目录执行检查点，确保 ptm-tde 后续分析有足够输入事实。当前必须实现 CP01 input 自检。

ptm-tde 只维护 Agent 与 Skill 调用关系，不负责安装。检查点脚本属于本 Skill 私有资产，路径固定为：

```text
skills/checkpoint-manager/scripts/run_checkpoint.py
```

不得把 checkpoint 脚本放到仓库根 `scripts/`。

## CP01 Input 自检

### Entry Criteria

| 条目 | 要求 |
|---|---|
| 特性项目根目录 | 当前 cwd 是单个特性项目根目录 |
| 输入目录 | `input/` 存在且只读对待 |
| 状态目录 | `doc/` 可创建，状态写入 `doc/STATE.yaml` |

### Checklist

| # | 检查项 | 通过条件 | 失败处理 |
|---|---|---|---|
| 1 | 需求文件存在 | 用户显式路径存在，或 `input/` 下存在需求文件，或 wiki 可找到特性接口/需求文档 | 若三处均不存在，提示用户提供需求文件 |
| 2 | 特性名可确定 | 用户提供 > 需求标题 > 项目目录最后一级 | 无法确定时提示用户给出特性名 |
| 3 | 原子操作入口可用 | 全局命令 `atomic-ops` 可执行 | 不可用时查 wiki 中原子操作描述文档和特性接口文档 |
| 4 | 防火墙 topo 可用 | `input/` 下存在 topo 文件，或 wiki 可找到 topo 描述 | 两者均不存在时提示用户提供 |
| 5 | 耦合矩阵可用 | `input/` 下存在耦合矩阵，或 wiki 可找到耦合矩阵/耦合关系文档 | 两者均不存在时提示用户提供 |
| 6 | 输出目录就绪 | 可创建 `analysis/`、`design/ppdcs/`、`design/pc/`、`checkpoints/`、`delivery/`、`doc/` | 无权限或路径冲突时阻断 |

### Exit Criteria

| 条目 | 要求 |
|---|---|
| 检查结果 | `checkpoints/CP01_input_auto.md` 已生成 |
| 阻断项 | 无 `BLOCKING` 项，或用户接受风险并记录 `WAIVED` |
| 状态更新 | `doc/STATE.yaml` 记录 `current_step: input` 与 CP01 结果 |

### Deliverables

| 产物 | 路径 |
|---|---|
| CP01 检查结果 | `checkpoints/CP01_input_auto.md` |
| 状态文件 | `doc/STATE.yaml` |

## Wiki 兜底规则

当本地 `input/` 中缺少原子操作、topo 或耦合矩阵信息时，必须按以下顺序查询 wiki：

1. 原子操作描述文档；
2. 特性接口文档；
3. 防火墙 topo / 组网描述；
4. 耦合矩阵或功能耦合关系文档。

wiki 查询结果只能作为只读引用写入检查点证据，不得回写 wiki。

## 脚本用法

```bash
uv run --python 3.11 python skills/checkpoint-manager/scripts/run_checkpoint.py CP01 --project-root .
```

可选参数：

```bash
--feature-name "<特性名>"
--requirement "input/<需求文件>"
--wiki-index "<wiki导出索引或检索结果>"
```

## Gotchas

- `atomic-ops` 是全局命令，不允许硬编码某个项目路径。
- CP01 发现 wiki 缺失时应提示用户提供材料，不得虚构 topo、接口或耦合矩阵。
- 检查点文件属于特性项目运行产物，写入 `checkpoints/`，不是 ptm-tde 仓库 `process/checks/`。
- `input/` 只读；若需派生 Markdown 或结构化摘要，写入 `analysis/feature-input/`。

## 验收标准

- [ ] CP01 覆盖需求文件、特性名、atomic-ops、wiki 兜底、topo、耦合矩阵和输出目录
- [ ] 检查结果写入 `checkpoints/CP01_input_auto.md`
- [ ] 脚本位于 `skills/checkpoint-manager/scripts/run_checkpoint.py`
- [ ] 不依赖安装器或安装清单
