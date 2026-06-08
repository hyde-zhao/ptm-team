# 耦合矩阵

## 定位

本目录是 `ptm-team` 公共耦合矩阵的 canonical source。耦合矩阵是仓库级 `resource`，供 `ptm-tde` 在 F 分析（耦合分析）阶段消费，也用于入口检查时的特性目录划分。

耦合矩阵描述了 TGFW 产品各特性之间的强耦合关系，是测试设计中发现功能交叉影响的核心输入。

## 目录

```
resource/coupling-matrix/
├── README.md                        # 本文件
├── index.yaml                       # 耦合矩阵索引（版本、状态、消费者）
├── tgfw-feature-tree.yaml           # TGFW 特性分层树（1115 条）
├── tgfw-coupling-matrix.yaml        # TGFW 产品耦合矩阵（562 条耦合关系）
├── tgfw-platform-diff.yaml          # TGFW 形态差异矩阵（平台支持矩阵）
│
├── _templates/                      # 新增耦合矩阵模板
│   └── README.md
└── _inbox/                          # 待入库的原始耦合矩阵文件
    └── README.md
```

## 数据说明

### tgfw-feature-tree.yaml

TGFW 产品特性分层树，从官方特性树 Excel 提取。包含一级至五级目录、特性定义、英文名称、特性 ID、风险等级、优先级。

**消费场景**：
- ptm-tde 入口检查时，四级/五级目录划分优先从此文件读取
- 特性树中不存在的层级由模型推理生成（fallback）

### tgfw-coupling-matrix.yaml

TGFW 产品耦合关系矩阵，合并自数通&高可用域和安全&系统域。每条记录包含：

| 字段 | 说明 |
|------|------|
| `source_feature` | 源特性全路径（如 `物理接口 > 接口管理`） |
| `target_feature` | 目标特性名称 |
| `coupling_level` | 耦合强度，当前全部为 `strong`（来源标记为 √） |
| `domain` | 来源域：`datacom-ha` 或 `security-system` |

**消费场景**：
- ptm-tde F 分析阶段，从矩阵基线出发发现耦合关系
- 三源合并（矩阵基线 + 场景推理 + 代码依赖）的最低基线

### tgfw-platform-diff.yaml

TGFW 各特性在不同硬件平台（J1900/C236/EP/ARM）上的支持情况。

> ⚠ **当前状态**：平台差异数据尚未填入，仅有特性结构骨架。数据填充工作待后续完成。

## 使用方式

### 安装

安装 `ptm-tde` agent 时，安装器会将关联的耦合矩阵和特性树同步安装到用户级公共资源目录：

```text
~/.ptm-team/resource/coupling-matrix/
```

也可通过 `PTM_TEAM_RESOURCE_HOME` 指向团队共享资源目录。

### ptm-tde 入口检查规则

1. 先检查 `input/` 目录是否有耦合矩阵和特性树
2. 若缺失，查询 `resource/coupling-matrix/`
3. 耦合矩阵与特性树**两者至少一个存在**即视为检查通过
4. 使用阶段需对比两个文档进行场景设计和 MFQ 分析

## 维护

- 新增耦合关系：通过 Excel 工具回写或直接编辑 YAML
- 新增特性：更新 `tgfw-feature-tree.yaml` 并同步更新耦合矩阵
- 待入库的原始文件放入 `_inbox/`

## 兼容消费者

| 消费者 | 资源 | 用途 |
|--------|------|------|
| ptm-tde | 全部 | 入口检查、场景设计、F 分析耦合发现 |
