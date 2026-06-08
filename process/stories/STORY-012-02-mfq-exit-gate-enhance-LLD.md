---
story_id: STORY-012-02
story_name: MFQ Exit Gate 增强（编号规范化 + HARD-STOP 机制）
lld_version: "1.0"
lld_status: draft
author: meta-dev
created_at: "2026-06-02"
confirmed: false
tier: S
wave: A
---

# STORY-012-02 LLD：MFQ Exit Gate 增强

## 1. Story 信息

| 字段 | 值 |
|------|-----|
| Story ID | STORY-012-02 |
| Story 名称 | MFQ Exit Gate 增强（编号规范化 + HARD-STOP 机制） |
| 所属变更 | CR-012-ptm-tde-mfq-phase |
| Tier | S（小型，~30 行改动，2 个文件） |
| Wave | A |
| 上游依赖 | 无 |
| 下游被依赖 | 无直接文件依赖（GATE-3 增强被后续 Story 间接使用） |
| 并行安全 | 是（与 STORY-012-01 无文件冲突） |
| 设计确认 | HLD v1.1 confirmed=true（CP3 人工确认通过），HLD §11 STOP-01~05 执行协议已确认 |

### Goal

将 `gate-spec.md` 和 `checkpoint-manager/SKILL.md` 中 GATE-3 MFQ Exit Gate 的 Checklist 自检项编号统一为 M1-M7 + W1-W2 前缀，注入 HLD §11 定义的 STOP-01~05 执行协议硬停止规则，并在人工确认项中增加 `⛔ HARD-STOP` 标记，防止 Agent 在人工门控上自行判定通过。

### Requirements

| 类型 | 要求 |
|------|------|
| Functional | GATE-3 Checklist #1-8 → M1-M7（合并 #8），上下游 Warning 保持 W1-W2 |
| Functional | 人工确认项每个确认项前增加 `⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。` |
| Functional | GATE-3 末尾增加「执行协议」小节，引用 STOP-01~05 规则摘要 |
| Functional | gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3 内容完全一致 |
| Non-Functional | 不改动 GATE-1/GATE-2/GATE-4/GATE-5 的内容 |
| Non-Functional | 不改动 checkpoint-manager 的检查执行框架代码、CP↔Gate 路由逻辑 |

### 编号映射表（来自 CR-012 Story 卡片）

| 旧编号 | 新编号 | 检查项内容 | 通过条件变更 |
|--------|--------|----------|-------------|
| #1 | **M1** | M 分析输出完整 | 不变 |
| #2 | **M2** | F 分析输出完整 | 不变 |
| #3 | **M3** | Q 分析输出完整 | 不变 |
| #4 | **M4** | 测试点整合完整 | 不变 |
| #5 | **M5** | LC topology_bindings 一致 | 不变 |
| #6 | **M6** | 设计计划存在 | 扩展：计划存在 + 格式符合 PPDCS 消费契约（吸收旧 #8） |
| #7 | **M7** | 公共因子库 lock 有效 | 不变 |
| #8 | **合并到 M6** | plan 存在性和格式 | 旧 #8 的 plan 存在性检查合并到 M6，格式检查由 M6 覆盖 |
| W1 | **W1** | KYM 场景下游可消费 | 不变 |
| W2 | **W2** | PPDCS 可消费 plan | 不变 |

---

## 2. 文件影响范围

| 文件 | 变更类型 | 改动量 | 改动说明 |
|------|----------|:---:|------|
| `docs/ptm-tde/gate-spec.md` | 修改 | ~18 行 | GATE-3 章节：编号重命名（8 行）、#8 合并（-1 行）、人工确认项增加 HARD-STOP（+4 行）、新增执行协议小节（+7 行）、修订记录追加（+1 行） |
| `skills/checkpoint-manager/SKILL.md` | 修改 | ~18 行 | GATE-3 章节：编号重命名（8 行）、#8 合并（-1 行）、人工确认项增加 HARD-STOP（+4 行）、新增执行协议小节（+7 行） |

**文件所有权**：`file_ownership` 中 2 个文件均属于本 Story，不与 STORY-012-01 冲突（后者改 5 个 Skill 文件）。

**不改动的范围**：
- `docs/ptm-tde/gate-spec.md` 中 GATE-1、GATE-2、GATE-4、GATE-5、跨阶段拓扑绑定检查、概述、CP↔Gate 映射表 等全部非 GATE-3 章节
- `skills/checkpoint-manager/SKILL.md` 中 GATE-1、GATE-2、GATE-4、GATE-5、Gotchas、验收标准、脚本用法 等全部非 GATE-3 章节
- checkpoint-manager 的 Python 脚本 `skills/checkpoint-manager/scripts/run_checkpoint.py`

---

## 3. 数据模型

本 Story 无新增数据实体。仅做文本修改：编号重命名 + 人工确认标记增强 + 执行协议引用追加。

---

## 4. 接口与契约

### 4.1 修改契约

#### gate-spec.md GATE-3 变更点

| 区域 | 当前状态 | 目标状态 | 契约约束 |
|------|---------|---------|---------|
| Checklist 表头 `#` 列 | `1, 2, 3, 4, 5, 6, 7, 8` | `M1, M2, M3, M4, M5, M6, M7` | M1-M7 连续，无跳过 |
| Checklist #8 行 | `\| 8 \| plan 存在性和格式 \| ... \|` | 删除整行 | M6 通过条件已扩展覆盖"格式符合 PPDCS 消费契约" |
| Checklist #6 (M6) 通过条件 | `process/plan/ 下有 CAE→PPDCS 推断和设计计划` | `process/plan/ 下有 CAE→PPDCS 推断和设计计划，格式符合 PPDCS 消费契约` | 扩展以吸收旧 #8 的格式检查 |
| 上下游 Warning 表头 `#` 列 | `W1, W2`（不变） | `W1, W2`（不变） | 仅确保与 Checklist 的 M1-M7 编号体系区分 |
| 人工确认项表 | 4 个确认项，以 `|` 开头 | 每行确认项的「说明」列文本前增加 `⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。` | 4 个确认项均追加 |
| GATE-3 末尾（Exit Criteria 与 Deliverables 之间或之后） | 无 | 新增 `### 执行协议` 小节，包含 STOP-01~05 摘要 | 引用 HLD §11 原文 |
| 文件头部修订记录 | 最后一行 `v1.3` | 追加 `v1.4 \| 2026-06-02 \| meta-dev \| [CR-012] GATE-3 Checklist 编号统一为 M1-M7+W1-W2，增加人工确认 HARD-STOP 标记和 STOP-01~05 执行协议引用` | 修订记录格式一致 |

#### checkpoint-manager SKILL.md GATE-3 变更点

与 gate-spec.md 完全一致的变更（双向同步）：

| 区域 | 与 gate-spec.md 对应 | 契约约束 |
|------|---------------------|---------|
| Checklist 概要表头 `#` 列 | 同步 | M1-M7，与 gate-spec.md 完全相同 |
| Checklist 概要 #8 行 | 同步 | 删除，M6 通过条件扩展 |
| 上下游 Warning 表头 | 同步 | W1-W2 |
| 人工确认项表 | 同步 | 每个确认项追加 HARD-STOP |
| GATE-3 末尾 | 同步 | 新增执行协议小节 |
| 文件头部 | 无需修改（checkpoint-manager 无修订记录表） | — |

### 4.2 STOP-01~05 执行协议引用内容

以下内容从 HLD §11 复制，追加到 gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3 末尾：

```markdown
### 执行协议

> 基于 HLD §11（CR-012 v1.1）定义的硬停止规则。GATE-3 人工确认必须遵守以下协议。

| 规则 ID | 适用场景 | 规则内容 |
|---------|---------|---------|
| STOP-01 | GATE-3 人工确认 | ⛔ HARD-STOP：禁止 Agent 在人工确认项上自行判定"通过"或"质量很高"。必须等待用户回复 `approve` / `修改: ...` / `reject`。未收到用户回复前不得推进到 PPDCS 阶段 |
| STOP-02 | 候选汇总确认 | ⛔ HARD-STOP：禁止 Agent 自行判定候选因子/原子操作为"全部确认"。必须展示候选汇总表，等待用户选择确认选项 |
| STOP-03 | Skill 调用链 | ⛔ HARD-STOP：禁止 Agent 绕过 Skill 直接生成 MFQ 产物。M/F/Q 分析必须通过对应的 Skill 调用执行 |
| STOP-04 | 路径写入校验 | ⛔ HARD-STOP：Skill 写入产物前必须校验目标父目录存在且为目录。禁止 Agent 手动 mkdir 创建目录 |
| STOP-05 | 确认选项视觉区分 | 所有需要用户选择的环节，必须使用 `( )` 单选 / `[ ]` 多选 / `>>>` 开放式 三类标记区分，禁止纯数字列表 |
```

### 4.3 人工确认项 HARD-STOP 标记格式

每个确认项的「说明」列文本前缀：

```
⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。
```

示例（以「M/F/Q 分析质量」确认项为目标）：

**修改前**：
```
| M/F/Q 分析质量 | 各维度分析是否覆盖完整 |
```

**修改后**：
```
| M/F/Q 分析质量 | ⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。各维度分析是否覆盖完整 |
```

**重要**：HARD-STOP 文本放在说明的最前面，后面跟原有说明文本，用句号分隔。不替换原说明文本。

### 4.4 契约不变项

- GATE-1/GATE-2/GATE-4/GATE-5 的编号体系（#1-N）保持不变
- checkpoint-manager 的 CP↔Gate 路由逻辑不变
- checkpoint-manager 的 `run_checkpoint.py` 脚本不变
- GATE-3 的 Entry Criteria、Exit Criteria、Deliverables 表内容不变
- 所有"实现深度说明"引用不变

---

## 5. 详细执行流程

### 流程图

```
开始
  │
  ├──→ 步骤 1: 修改 gate-spec.md（真相源）
  │     │
  │     ├──→ ST201: GATE-3 Checklist 编号重命名（#1-8 → M1-M7）
  │     ├──→ ST202: 删除旧 #8 行，扩展 M6 通过条件
  │     ├──→ ST203: 人工确认项追加 HARD-STOP 标记
  │     ├──→ ST204: GATE-3 末尾追加执行协议小节
  │     └──→ ST205: 修订记录追加 v1.4
  │
  ├──→ 步骤 2: 同步到 checkpoint-manager SKILL.md
  │     │
  │     ├──→ ST206: GATE-3 Checklist 概要编号重命名
  │     ├──→ ST207: 删除旧 #8 行，扩展 M6 通过条件
  │     ├──→ ST208: 人工确认项追加 HARD-STOP 标记
  │     └──→ ST209: GATE-3 末尾追加执行协议小节
  │
  ├──→ 步骤 3: 一致性校验（gate-spec.md ↔ checkpoint-manager）
  │     │
  │     ├── PASS → 步骤 4
  │     └── FAIL → 修正差异 → 重新步骤 3
  │
  ├──→ 步骤 4: 全体验收验证（AC01-AC08）
  │     │
  │     ├── PASS → 步骤 5
  │     └── FAIL → 定位失败项修正 → 重新步骤 4
  │
  └──→ 步骤 5: 输出 CP6 自检结果
```

### 步骤 1 详细：gate-spec.md 逐项修改

#### 子步骤 A：Checklist 编号重命名（ST201）

在 gate-spec.md 的 GATE-3 Checklist 表（`| # | 检查项 | 通过条件 | 失败处理 |` 开头的表格）中：

1. 行 `| 1 | M 分析输出完整 | ...` → `| M1 | M 分析输出完整 | ...`
2. 行 `| 2 | F 分析输出完整 | ...` → `| M2 | F 分析输出完整 | ...`
3. 行 `| 3 | Q 分析输出完整 | ...` → `| M3 | Q 分析输出完整 | ...`
4. 行 `| 4 | 测试点整合完整 | ...` → `| M4 | 测试点整合完整 | ...`
5. 行 `| 5 | LC topology_bindings 一致 | ...` → `| M5 | LC topology_bindings 一致 | ...`
6. 行 `| 6 | 设计计划存在 | ...` → `| M6 | 设计计划存在 | \`process/plan/\` 下有 CAE→PPDCS 推断和设计计划，格式符合 PPDCS 消费契约 | 缺失或格式错误时回到 plan |`（通过条件扩展）
7. 行 `| 7 | 公共因子库 lock 有效 | ...` → `| M7 | 公共因子库 lock 有效 | ...`
8. 删除行 `| 8 | plan 存在性和格式 | ...`（整行移除）

#### 子步骤 B：上下游 Warning 编号（ST202）

Warning 表头 `#` 列当前为 `#`，不需要改名（因为 W1、W2 已经是正确格式）。但需要确认：
- `| W1 | KYM 场景下游可消费 | ...` 保持不变
- `| W2 | PPDCS 可消费 plan | ...` 保持不变

#### 子步骤 C：人工确认项 HARD-STOP（ST203）

在 GATE-3 人工确认项的「说明」列中，为每个确认项追加 HARD-STOP 前缀。4 个确认项为：
1. M/F/Q 分析质量
2. LC 整合一致性
3. 设计计划
4. 公共因子消费

#### 子步骤 D：执行协议小节（ST204）

在 GATE-3 的 Deliverables 表之后、下一个 `---` 分隔线或 `## GATE-4` 之前，插入执行协议小节（内容见 §4.2）。

#### 子步骤 E：修订记录（ST205）

在 gate-spec.md 头顶修订记录表末尾追加一行：
```
| v1.4 | 2026-06-02 | meta-dev | [CR-012] GATE-3 Checklist 编号统一为 M1-M7+W1-W2，增加人工确认 HARD-STOP 标记和 STOP-01~05 执行协议引用 |
```

### 步骤 2 详细：checkpoint-manager SKILL.md 同步

与步骤 1 完全镜像操作，但注意 checkpoint-manager SKILL.md 的 GATE-3 章节使用的是「Checklist 概要」表（3 列：`# | 检查项 | 通过条件`），而 gate-spec.md 的 Checklist 表是 4 列（`# | 检查项 | 通过条件 | 失败处理`）。

**关键差异**：
- checkpoint-manager 的 GATE-3 Checklist 概要表**没有**「失败处理」列
- checkpoint-manager 的 M6 通过条件扩展时，只写到「通过条件」列：`\`process/plan/\` 下有 CAE→PPDCS 推断和设计计划，格式符合 PPDCS 消费契约`
- checkpoint-manager **没有**文件头部修订记录表，不做修订记录修改

---

## 6. 异常处理

| 异常场景 | 检测方式 | 处理 | 阻断级别 |
|---------|---------|------|---------|
| 两个文件 GATE-3 编号不一致 | 人工对比两个文件的 M1-M7 + W1-W2 编号 | 以 gate-spec.md 为真相源，重新同步 checkpoint-manager | BLOCKING |
| HARD-STOP 标记在两文件中位置/文本不一致 | 人工对比 | 统一修正 | BLOCKING |
| 执行协议小节在两文件中内容不一致 | diff 两个文件的执行协议段落 | 统一修正 | BLOCKING |
| GATE-1/GATE-2/GATE-4/GATE-5 被意外修改 | `git diff` 限定 GATE-3 区域 | 从 git 恢复非 GATE-3 区域 | BLOCKING |
| 误改其他文件 | `git diff --stat` | 从 git 恢复 | BLOCKING |
| STOP 协议内容与 HLD §11 不一致 | 对照 HLD §11 原文 | 以 HLD 为准修正 | BLOCKING |

**失败回退策略**：`git checkout -- docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md` 恢复到修改前状态，修正后重试。

---

## 7. 测试设计

### 7.1 自动化验收测试（8 项）

| AC | 命令 / 检查方法 | 预期结果 | 覆盖 LLD §4 |
|----|---------------|---------|------------|
| AC01 | `grep -c "M[1-7]\|W[1-2]" docs/ptm-tde/gate-spec.md` — 统计 GATE-3 章节内的 M/W 编号出现次数 | >= 9（M1-M7 各至少 1 次 + W1-W2 各至少 1 次） | §4.1 编号重命名 |
| AC02 | `grep -c "M[1-7]\|W[1-2]" skills/checkpoint-manager/SKILL.md` — 同上 | >= 9 | §4.1 编号重命名 |
| AC03 | `grep "⛔ HARD-STOP" docs/ptm-tde/gate-spec.md` | 存在且位于 GATE-3 人工确认项章节（至少 4 处，每个确认项 1 处） | §4.3 HARD-STOP 标记 |
| AC04 | `grep "⛔ HARD-STOP" skills/checkpoint-manager/SKILL.md` | 存在且位于 GATE-3 人工确认项章节 | §4.3 HARD-STOP 标记 |
| AC05 | 检查 gate-spec.md GATE-3 Checklist 表中 `#` 列 | 不再使用纯数字（1-8），全部使用 M1-M7 | §4.1 编号重命名 |
| AC06 | 检查 gate-spec.md GATE-3 上下游 Warning 表 `#` 列 | 使用 W1-W2（不变但确认） | §4.1 Warning 编号 |
| AC07 | 人工对比：checkpoint-manager 的 M1-M7 + W1-W2 编号与 gate-spec.md 完全一致 | checkpoint-manager GATE-3 Checklist 每行的新编号与 gate-spec.md 对应行完全相同 | §4.1 双向同步 |
| AC08 | `grep "STOP-0[1-5]" docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md` | 两个文件均在 GATE-3 相关章节含 STOP-01~05 引用 | §4.2 执行协议引用 |

### 7.2 正面测试

| 测试项 | 方法 | 覆盖 |
|--------|------|------|
| gate-spec.md GATE-3 章节开头可识别 | 查找 `## GATE-3 MFQ Exit Gate` 并在其之后定位 M1 | §4.1 |
| gate-spec.md 旧编号 #1-#8 不再出现在 GATE-3 Checklist 表的 # 列 | `sed -n '/## GATE-3/,/^## GATE-4/p' docs/ptm-tde/gate-spec.md \| grep "^\| [0-9]\+ \|"'` 在 GATE-3 区域内不匹配数字 | AC05 |
| checkpoint-manager 镜像一致 | diff GATE-3 相关段落：编号、HARD-STOP、执行协议 | AC07 |
| 两文件均含执行协议小节 | `grep -A30 "执行协议" docs/ptm-tde/gate-spec.md` 包含 STOP-01~05 表格 | §4.2 |
| gateway-spec.md 修订记录更新 | `grep "v1.4.*CR-012.*GATE-3" docs/ptm-tde/gate-spec.md` 存在 | §4.1 |

### 7.3 回归测试（非 GATE-3 区域不变）

| 测试项 | 方法 | 期望 |
|--------|------|------|
| GATE-1 Checklist #1-N 不变 | `sed -n '/## GATE-1/,/^## GATE-2/p' docs/ptm-tde/gate-spec.md \| grep "^\| [0-9]\+ \|"'` | 编号保持 #1-#9 |
| GATE-2 Checklist #1-N 不变 | `sed -n '/## GATE-2/,/^## GATE-3/p' docs/ptm-tde/gate-spec.md \| grep "^\| [0-9]\+ \|"'` | 编号保持 #1-#14 + N1-N4 |
| GATE-4/GATE-5 不变 | 同方法 | 编号保持 #1-#N |
| checkpoint-manager Gotchas 不变 | `grep -A3 "GATE-3" skills/checkpoint-manager/SKILL.md \| tail -20` | W1/W2 非阻断说明仍存在 |
| checkpoint-manager 验收标准不变 | `grep "GATE-3" skills/checkpoint-manager/SKILL.md \| tail -5` | 输出路径仍为 `process/checkpoints/GATE-3-MFQ-Exit-*` |

---

## 8. 实施步骤（含 TASK-ID）

| TASK-ID | 步骤 | 输入 | 操作 | 输出 | 验收 |
|---------|------|------|------|------|------|
| **TASK-STORY-012-02-01** | 环境准备 | 2 个目标文件 | 确认 2 个文件可读写；`git diff` 确认无未暂存修改 | 工作区状态确认 | 无脏文件 |
| **TASK-STORY-012-02-02** | 修改 gate-spec.md — 编号重命名 | `docs/ptm-tde/gate-spec.md` GATE-3 章节 | ST201: Checklist 编号 #1-8 → M1-M7（重命名 7 行 + 删除 #8 行 + 扩展 M6 通过条件）；ST202: 确认 W1-W2 不变 | gate-spec.md GATE-3 段落更新 | AC01/AC05/AC06 即时验证 |
| **TASK-STORY-012-02-03** | 修改 gate-spec.md — HARD-STOP | 同上 | ST203: 人工确认项 4 行每行追加 `⛔ HARD-STOP：...` | gate-spec.md GATE-3 人工确认项更新 | AC03 即时验证 |
| **TASK-STORY-012-02-04** | 修改 gate-spec.md — 执行协议 + 修订记录 | 同上 | ST204: GATE-3 末尾插入执行协议小节；ST205: 修订记录追加 v1.4 | gate-spec.md GATE-3 完整更新 | AC08 即时验证 |
| **TASK-STORY-012-02-05** | 修改 checkpoint-manager SKILL.md — 编号重命名 | `skills/checkpoint-manager/SKILL.md` GATE-3 章节 | ST206: Checklist 编号 #1-8 → M1-M7（注意 3 列表格格式）；ST207: 删除 #8 行 + 扩展 M6 通过条件 | checkpoint-manager GATE-3 段落更新 | AC02 即时验证 |
| **TASK-STORY-012-02-06** | 修改 checkpoint-manager SKILL.md — HARD-STOP + 执行协议 | 同上 | ST208: 人工确认项追加 HARD-STOP；ST209: GATE-3 末尾插入执行协议小节 | checkpoint-manager GATE-3 完整更新 | AC04/AC08 即时验证 |
| **TASK-STORY-012-02-07** | 双向一致性校验 | 2 个文件更新后 | 逐行对比 gate-spec.md 和 checkpoint-manager 的 GATE-3：M1-M7 编号、HARD-STOP 文本、执行协议内容 | 差异报告（期望：0 差异） | AC07 PASS |
| **TASK-STORY-012-02-08** | 回归验证 | 2 个文件更新后 | 验证 GATE-1/GATE-2/GATE-4/GATE-5 未被修改；验证 checkpoint-manager CP↔Gate 路由逻辑不变 | 回归结果 | §7.3 全部 PASS |
| **TASK-STORY-012-02-09** | CP6 自检 | 全部验证结果 | 调用 checkpoint-manager Skill 输出 CP6 | `process/checks/CP6-STORY-012-02-mfq-exit-gate-enhance-CODING-DONE.md` | CP6 PASS |

**任务依赖**：TASK-STORY-012-02-02、012-02-03、012-02-04 按顺序执行（gate-spec.md 真相源）。TASK-STORY-012-02-05、012-02-06 在 gate-spec.md 完成后执行（以真相源为参照）。TASK-STORY-012-02-07 依赖前 5 个任务全部完成。

---

## 9. 风险与缓解

| 风险 ID | 风险描述 | 概率 | 影响 | 缓解措施 | 触发信号 |
|---------|---------|------|------|---------|---------|
| R1 | gate-spec.md 和 checkpoint-manager 的 GATE-3 Checklist 表格式不同（4 列 vs 3 列），同步时复制了错误列数的行 | 中 | 中 | 实施前确认两文件 GATE-3 Checklist 表的列数；修改后 AC07 逐行对比 | AC07 FAIL |
| R2 | GATE-3 执行协议引用内容与 HLD §11 原文不一致 | 低 | 中 | LLD §4.2 已明确定义引用内容；实施时从 HLD §11 复制；AC08 grep 验证所有 5 条规则 | AC08 FAIL |
| R3 | HARD-STOP 标记中英文标点不一致（如中英文冒号） | 低 | 低 | LLD §4.3 已明确定义标准文本；AC03/AC04 explicit grep | AC03/AC04 FAIL |
| R4 | 修订记录 `v1.4` 日期错误（非 2026-06-02） | 低 | 低 | 实施时确认日期；人工复查 | N/A |
| R5 | GATE-4 或其他 Gate 的编号体系被误认为需要同步修改 | 极低 | 中 | LLD §4.4 明确契约不变项；§7.3 回归测试覆盖 | 回归测试 FAIL |

---

## 10. 发布与回滚

### 10.1 发布策略

- **发布方式**：不独立 commit。修改完成后标记 Story `ready-for-verification`，由 Wave A 统一管理 git 提交。
- **发布范围**：仅 2 个文件（`docs/ptm-tde/gate-spec.md` + `skills/checkpoint-manager/SKILL.md`）的 GATE-3 章节。
- **不发布项**：不修改 checkpoint-manager Python 脚本；不修改 gate-spec.md 非 GATE-3 章节。

### 10.2 回滚策略

| 回滚方式 | 操作 | 适用场景 |
|---------|------|---------|
| Git checkout | `git checkout -- docs/ptm-tde/gate-spec.md skills/checkpoint-manager/SKILL.md` | 发现验收失败或逻辑错误 |
| 整体 Wave revert | `git revert <Wave A commit>` | Wave A 整体出问题 |

**回滚验证**：
- gate-spec.md GATE-3 Checklist 恢复 #1-#8 编号
- 人工确认项恢复无 HARD-STOP 标记
- 无执行协议小节
- 修订记录无 v1.4 行

---

## 11. 依赖与前置条件

### 11.1 前置条件

| 条件 | 状态 | 验证方式 |
|------|------|---------|
| HLD v1.1 confirmed=true（含 STOP-01~05） | 已满足 | `process/HLD-CR-012.md` frontmatter `confirmed: true` |
| CP3 人工确认通过（含 AGA-05 GATE-3 硬停止方案） | 已满足 | `checkpoints/CP3-HLD-REVIEW-CR-012.md` |
| gate-spec.md 存在且 GATE-3 章节完整 | 需运行时确认 | `grep -c "GATE-3" docs/ptm-tde/gate-spec.md` >= 10 |
| checkpoint-manager SKILL.md 存在且 GATE-3 章节完整 | 需运行时确认 | `grep -c "GATE-3" skills/checkpoint-manager/SKILL.md` >= 10 |
| 无文件所有权冲突（STORY-012-01 不碰这 2 个文件） | 已满足 | 对比 `file_ownership` |

### 11.2 依赖类型

| 依赖 | 类型 | 状态 |
|------|------|------|
| HLD-CR-012.md（STOP-01~05 定义） | `contract`（接口冻结：执行协议内容从 HLD §11 引用） | 已确认 |
| CR-010（gate-spec.md 基线、GATE-3 框架） | `runtime` | 已完成 |
| STORY-012-01 | 无依赖（并行，文件不冲突） | Wave A 并行 |

---

## 12. 实现灰区

| ID | 灰区 | 决策 | 理由 | 影响面 | 重访条件 |
|----|------|------|------|--------|---------|
| GA-01 | gate-spec.md 的「实现深度说明」段落中提及 `checkpoint-manager 执行骨架检查`——此说明在 GATE-3 编号重命名后是否需要更新？ | 不需要更新。「实现深度说明」是阶段级说明，不引用 Checklist 具体编号 | 设计文档 v3.0 中 GATE-3 Checklist 使用 M1-M7 编号，实现深度说明引用 gate-spec.md 而非 Checklist 编号 | gate-spec.md 底部「实现深度说明」 | 若后续 CR 改变 checkpoint-manager 执行深度，更新该说明 |
| GA-02 | `checkpoint-manager SKILL.md` Gotchas 章节提到 `GATE-3 的上下游 Warning（W1、W2）是非阻断项`——编号重命名后此 Gotchas 是否需要更新？ | 不需要更新。W1/W2 编号不变，Gotchas 的说法在编号重命名后仍然正确 | Gotchas 引用的是 Warning 的行为（非阻断），而非编号 | checkpoint-manager Gotchas | W1/W2 编号若在后续 CR 中变更，需同步更新 Gotchas |
| GA-03 | checkpoint-manager SKILL.md 无修订记录表——GATE-3 变更如何追溯？ | 通过 git log 追溯。checkpoint-manager SKILL.md 作为 Skill 文件（非规范文档），其变更由 git 管理，不在文件内维护修订记录表 | gate-spec.md 是规范真相源且包含修订记录，checkpoint-manager 的 GATE-3 内容与之同步，变更原因和日期可在 gate-spec.md v1.4 修订记录中找到 | checkpoint-manager | checkpoint-manager 后续若需要独立修订记录，可通过 CR 追加 |

**澄清队列**：无。本 Story 范围明确：编号映射表来自 CR-012 Story 卡片，HARD-STOP 标记来自 HL D §11（已人工确认），执行协议内容直接从 HLD 复制。无需要澄清的实现灰区。

---

## 13. 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-02 | meta-dev | 初始 LLD，覆盖 2 个文件的 GATE-3 编号重命名、HARD-STOP 标记注入、STOP-01~05 执行协议引用追加、9 个 TASK-ID、8 项验收测试和双向同步策略 |

---

## 14. 验收清单

- [ ] gate-spec.md GATE-3 Checklist 使用 M1-M7（AC01 >= 9；AC05 无纯数字 #1-#8）
- [ ] checkpoint-manager SKILL.md GATE-3 Checklist 使用 M1-M7（AC02 >= 9）
- [ ] gate-spec.md GATE-3 人工确认项含 `⛔ HARD-STOP`（AC03，4 处）
- [ ] checkpoint-manager SKILL.md GATE-3 人工确认项含 `⛔ HARD-STOP`（AC04，4 处）
- [ ] 上下游 Warning 编号保持 W1-W2（AC06）
- [ ] 双向一致性：gate-spec.md 和 checkpoint-manager 的 GATE-3 编号、HARD-STOP、执行协议完全一致（AC07）
- [ ] STOP-01~05 执行协议在两文件的 GATE-3 章节中均存在（AC08）
- [ ] GATE-1/GATE-2/GATE-4/GATE-5 内容未被修改（§7.3 回归）
- [ ] checkpoint-manager CP↔Gate 路由逻辑不变
- [ ] gate-spec.md 修订记录已追加 v1.4
- [ ] CP6 自检通过（`process/checks/CP6-STORY-012-02-mfq-exit-gate-enhance-CODING-DONE.md`）
