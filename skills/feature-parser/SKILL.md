---
name: feature-parser
description: >-
  解析用户提供的特性需求文件，提取结构化需求条目，构建三~五级目录结构。
  触发词包括：解析特性、解析需求、导入特性文件、特性解析。
  适用场景：MFQ 分析的第一步（input 阶段）。
argument-hint: "特性需求文件路径"
user-invokable: true
status: active
---

## 目标

从用户提供的特性需求文件中提取结构化需求条目（编号/所属模块/SR名称/描述），
构建三级（特性）→四级（模块）→五级（子模块）目录结构，为后续 MFQ 分析建立基础。

## 适用范围

- 适用阶段：MFQ 分析的 input 阶段
- 输入：特性需求文件（Markdown/Word/Excel/PDF）
- 输出：`kym/feature-input/` 目录下的结构化文件

## 支持的输入格式

| 格式 | 处理方式 |
|------|---------|
| Markdown (.md) | 直接解析 |
| Word (.docx) | 先用 `file-to-markdown` 转换为 MD，再解析 |
| Excel (.xlsx) | 先用 `file-to-markdown` 转换为 MD，再解析 |
| PDF (.pdf) | 先用 `file-to-markdown` 转换为 MD，再解析 |

## 前置条件

- [ ] CP01 input 自检已通过，或已明确记录阻断项
- [ ] 用户已提供特性需求文件路径，或 CP01 已从 `input/` / wiki 找到需求文件
- [ ] `kym/feature-input/` 与 `doc/STATE.yaml` 已初始化
- [ ] `file-to-markdown` Skill 可用（用于非 MD 格式的预转换）

## 执行流程

### 步骤 1：文件预处理

1. 检查文件格式，非 Markdown 文件先调用 `file-to-markdown` 转换
2. 读取 Markdown 内容

### 步骤 2：需求条目提取

从文件中识别和提取以下字段：

| 字段 | 说明 | 提取策略 |
|------|------|---------|
| 编号 | 需求唯一标识（如 SR-001） | 从编号列或序号列提取 |
| 所属模块 | 需求归属的功能模块 | 从模块列或标题层级推断 |
| SR 名称 | 系统需求名称 | 从名称列提取 |
| 描述 | 需求详细描述 | 从描述列提取 |

**提取策略优先级**：
1. 表格格式：识别 Markdown 表格，按列名映射字段
2. 列表格式：识别编号列表，按格式模式匹配
3. 标题格式：识别 Markdown 标题层级，按层级推断模块归属

### 步骤 3：查询特性树获取规范目录

⛔ **HARD-STOP**：禁止在未查询特性树的情况下自行发明四级/五级目录名称。特性树是目录命名的唯一真相源（source of truth）。

**特性树查找顺序**：
1. `resource/coupling-matrix/tgfw-feature-tree.yaml`（开发态仓库）
2. `~/.ptm-team/resource/coupling-matrix/tgfw-feature-tree.yaml`（已安装）
3. `$PTM_TEAM_RESOURCE_HOME/coupling-matrix/tgfw-feature-tree.yaml`（团队共享）
4. `input/` 下的特性树文件（用户手动放置）

**匹配流程**：
1. 从步骤 2 提取的「所属模块」字段中获取模块路径（如 `/TGFW-03数通组件/TGFW-03.04 三层组件/TGFW-03.04.06 策略路由`）
2. 在特性树中按 `level3` 字段匹配当前特性（如 `策略路由`）
3. 在该特性节点下查找 `level4` 和 `level5` 作为规范的四级/五级目录
4. 将每个 SR 按描述内容映射到匹配的规范目录节点
5. 记录匹配来源：`source: feature-tree`（特性树匹配）或 `source: model-inference`（模型推理）

**未匹配处理**：
- 若特性树中找不到对应特性 → 标记 `source: model-inference`，由模型根据需求语义聚合生成
- 若特性树中有特性但部分 SR 无法匹配到五级节点 → 保留 `source: model-inference`，并在确认时特别标注
- 模型推理生成的目录必须在确认时与特性树来源目录明确区分

### 步骤 4：目录结构构建

根据特性树规范目录和提取的需求条目，构建三~五级目录结构：

```
<特性名>（三级）
├── <模块A>（四级）
│   ├── <子模块A1>（五级）
│   └── <子模块A2>（五级）
└── <模块B>（四级）
    ├── <子模块B1>（五级）
    └── <子模块B2>（五级）
```

**构建规则**：
- 三级目录 = 特性名称，优先级为用户显式提供 > 需求标题 > 项目目录最后一级
- 四级目录 = **优先从特性树 `level4` 匹配**，未命中时从需求"所属模块"字段去重（标记 `model-inference`）
- 五级目录 = **优先从特性树 `level5` 匹配**，未命中时按功能子类聚合（标记 `model-inference`）
- 每个目录节点必须标注 `source` 字段：`feature-tree` 或 `model-inference`

### 步骤 5：用户确认

将构建的目录结构展示给用户，使用 `ask_user` 工具发起结构化确认：

```
## 目录结构确认

特性：<特性名>

├── <模块A>
│   ├── <子模块A1>（N 条需求）
│   └── <子模块A2>（M 条需求）
└── <模块B>
    └── <子模块B1>（K 条需求）
```

**ask_user 选项**：
1. ✅ 确认通过 — 目录结构正确，保存并进入场景发现
2. ✏️ 需要修改 — 请输入需要调整的模块或子模块，调整后重新确认
3. ➕ 需要补充 — 请输入需要新增的模块或子模块，补充后重新确认

### 步骤 6：输出持久化

将结果写入 `kym/feature-input/`：

#### raw-requirements.md 格式

```markdown
# <特性名> — 结构化需求列表

| 编号 | 所属模块 | 子模块 | SR 名称 | 描述 |
|------|---------|--------|---------|------|
| SR-001 | 模块A | 子模块A1 | ... | ... |
| SR-002 | 模块A | 子模块A2 | ... | ... |
```

#### directory-structure.md 格式

```markdown
# <特性名> — 目录结构

## 三级：<特性名>

### 四级：<模块A>
- 五级：<子模块A1>
- 五级：<子模块A2>

### 四级：<模块B>
- 五级：<子模块B1>
```

## Gotchas

- **⛔ 禁止自行发明目录名**：四级/五级目录必须优先从 `tgfw-feature-tree.yaml` 匹配，禁止凭语义直觉自创分类。特性树未命中时才允许模型推理（标记 `model-inference`）。
- **⚠️ 输出路径必须是 `kym/feature-input/`**：正确绝对路径为 `<项目根>\kym\feature-input\raw-requirements.md`
- Excel 转换后可能出现 `NaN`、`Unnamed` 等伪值，需清洗
- 合并单元格转换后模块归属可能丢失，需从上下文推断
- 部分需求文件没有明确的模块分类，需通过功能语义聚合——但仍须先查特性树
- 中文文件名需注意编码问题

## 验收标准

- [ ] 所有需求条目均被提取（编号/模块/名称/描述 四字段完整）
- [ ] 目录结构包含三级/四级/五级三个层级
- [ ] 用户已确认目录结构
- [ ] `raw-requirements.md` 和 `directory-structure.md` 已写入 `kym/feature-input/`
- [ ] 更新 `doc/STATE.yaml` 的 `current_step` 为下一步
