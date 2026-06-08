---
story_id: "STORY-011-02"
title: "KYM 阶段路径迁移"
story_slug: "kym-path-migration"
lld_version: "1.0"
tier: "S"
status: "ready-for-review"
confirmed: false
created_by: "meta-dev"
created_at: "2026-06-02T15:00:00+08:00"
confirmed_by: ""
confirmed_at: ""
shared_fragments: []
open_items: 0
---

# LLD: STORY-011-02 — KYM 阶段路径迁移

> 文件名格式：`STORY-011-02-kym-path-migration-LLD.md`
>
> 本文档是 STORY-011-02 的低层设计（Low-Level Design），需纳入全部目标 Story 的 LLD 统一确认后方可进入实现。

## 1. Goal

将 KYM 阶段两个 Skill（feature-parser、scenario-discovery）中所有 `analysis/feature-input/` 和 `analysis/scenarios/` 路径引用一次性替换为 `kym/feature-input/` 和 `kym/scenarios/`，不保留过渡期，不触碰 MFQ/PPDCS 路径。

## 2. Requirements（Functional / Non-Functional）

### 2.1 Functional

- [AC-01] `skills/feature-parser/SKILL.md` 中所有 `analysis/feature-input/` 替换为 `kym/feature-input/`
- [AC-02] `skills/scenario-discovery/SKILL.md` 中所有 `analysis/feature-input/` 替换为 `kym/feature-input/`
- [AC-03] `skills/scenario-discovery/SKILL.md` 中所有 `analysis/scenarios/` 替换为 `kym/scenarios/`
- [AC-04] 不修改 `analysis/m-analysis/`、`analysis/f-analysis/`、`design/ppdcs/` 及其他非 KYM 阶段路径
- [AC-05] 验证命令 `grep -rn "analysis/feature-input\|analysis/scenarios" skills/feature-parser/SKILL.md skills/scenario-discovery/SKILL.md` 返回 0 结果

### 2.2 Non-Functional

- [NF-01] 一次完成，无过渡期（不保留旧路径别名或兼容映射）
- [NF-02] 旧目录 `analysis/feature-input/` 和 `analysis/scenarios/` 不主动删除（保留 git 历史），但后续不再写入
- [NF-03] 保持文档格式完整性——替换路径后 Markdown 代码围栏、表格、列表格式不变

## 3. 模块拆分与职责

| 模块 / 文件组 | 职责 | 说明 |
|---|---|---|
| `skills/feature-parser/SKILL.md` | feature-parser 的输出路径迁移 | 5 处替换，纯文本替换（`analysis/feature-input/` → `kym/feature-input/`） |
| `skills/scenario-discovery/SKILL.md` | scenario-discovery 的输入/输出/示例路径迁移 | 8 处替换（`analysis/feature-input/` → `kym/feature-input/` x2 + `analysis/scenarios/` → `kym/scenarios/` x6） |

模块边界：
- 不创建新文件，不删除旧文件
- 不修改 `skills/kym/SKILL.md`（该文件使用新路径，无需迁移，归属 STORY-011-01）
- 不修改 `skills/README.md`、`docs/ptm-tde/skill-references.md`（归属 STORY-011-01 / STORY-011-04）
- 不修改 MFQ/PPDCS Skill 路径（归属 CR-012/013）

## 4. 代码结构与文件影响范围

> 严格使用确定性动词。

| 动作 | 文件路径 | 变更内容 |
|---|---|---|
| 修改 | `skills/feature-parser/SKILL.md` | 5 处 `analysis/feature-input/` → `kym/feature-input/`：第 21 行（适用范围-输出）、第 36 行（前置条件）、第 104 行（步骤 5-输出持久化）、第 134 行（Gotchas）、第 145 行（验收标准） |
| 修改 | `skills/scenario-discovery/SKILL.md` | 8 处替换：第 51 行和 136 行 `analysis/feature-input/` → `kym/feature-input/`；第 34 行(x2)、52、53、80、453 行 `analysis/scenarios/` → `kym/scenarios/` |

## 5. 数据模型与持久化设计

无新增数据模型 / 持久化变更。本 Story 仅涉及文本路径替换，不改变任何数据结构或持久化行为。

## 6. API / Interface 设计

| 接口 / 入口 | 输入 | 输出 | 调用方 | 说明 |
|---|---|---|---|---|
| feature-parser 输出写入 | 结构化需求数据 | `kym/feature-input/raw-requirements.md` + `directory-structure.md` | feature-parser 用户/Agent | 迁移前输出到 `analysis/feature-input/` |
| scenario-discovery 输出写入 | 场景发现结果 | `kym/scenarios/confirmed-scenarios.md` | scenario-discovery 用户/Agent | 迁移前输出到 `analysis/scenarios/` |
| scenario-discovery 输入读取 | `kym/feature-input/` + `kym/scenarios/`（样例） | 场景发现上下文 | scenario-discovery | 迁移后从新路径读取 |

> 第 6 节接口条目与第 10 节测试覆盖关系：TC-01 验证 feature-parser 输出路径，TC-03 验证 scenario-discovery 输出路径。

## 7. 核心处理流程

本 Story 的实现是纯文本替换操作，无复杂处理流程：

1. 读取 `skills/feature-parser/SKILL.md`，将所有 `analysis/feature-input/` 替换为 `kym/feature-input/`
2. 读取 `skills/scenario-discovery/SKILL.md`，将所有 `analysis/feature-input/` 替换为 `kym/feature-input/`，将所有 `analysis/scenarios/` 替换为 `kym/scenarios/`
3. 运行验证命令确认替换完成
4. 不生成任何中间产物、不修改任何其他文件

> 无 Mermaid 图需求：本 Story 仅涉及文本替换，不跨越模块、无异步/补偿路径、无异常分支。

## 8. 技术设计细节

### 8.1 逐行替换明细

#### feature-parser/SKILL.md（5 处替换，结构 = `analysis/feature-input/` → `kym/feature-input/`）

| 行号 | 原文本片段 | 替换后 |
|------|-----------|--------|
| 21 | `输出：\`analysis/feature-input/\` 目录下的结构化文件` | `输出：\`kym/feature-input/\` 目录下的结构化文件` |
| 36 | `\`analysis/feature-input/\` 与 \`doc/STATE.yaml\` 已初始化` | `\`kym/feature-input/\` 与 \`doc/STATE.yaml\` 已初始化` |
| 104 | `将结果写入 \`analysis/feature-input/\`：` | `将结果写入 \`kym/feature-input/\`：` |
| 134 | `输出路径必须是 \`analysis/feature-input/\`（相对于特性项目根），不是 \`analysis/feature-input/\`，也不是 \`analysis/feature-input/\`。例如 cwd=\`D:\project\` 时，正确绝对路径是 \`D:\project\analysis\feature-input\raw-requirements.md\`` | `输出路径必须是 \`kym/feature-input/\`（相对于特性项目根），不是 \`kym/feature-input/\`，也不是 \`kym/feature-input/\`。例如 cwd=\`D:\project\` 时，正确绝对路径是 \`D:\project\kym\feature-input\raw-requirements.md\`` |
| 145 | `\`raw-requirements.md\` 和 \`directory-structure.md\` 已写入 \`analysis/feature-input/\`` | `\`raw-requirements.md\` 和 \`directory-structure.md\` 已写入 \`kym/feature-input/\`` |

#### scenario-discovery/SKILL.md（8 处替换）

| 行号 | 原路径模式 | 替换为 |
|------|-----------|--------|
| 34 | `analysis/scenarios/scenario-analysis.md`、`analysis/scenarios/scenario-deployment-<feature>.md` | `kym/scenarios/scenario-analysis.md`、`kym/scenarios/scenario-deployment-<feature>.md` |
| 51 | `analysis/feature-input/` | `kym/feature-input/` |
| 52 | `analysis/scenarios/scenario-deployment-policy-route.md` | `kym/scenarios/scenario-deployment-policy-route.md` |
| 53 | `analysis/scenarios/scenario-analysis.md` | `kym/scenarios/scenario-analysis.md` |
| 80 | `analysis/scenarios/scenario-deployment-policy-route.md` | `kym/scenarios/scenario-deployment-policy-route.md` |
| 136 | `analysis/feature-input/` | `kym/feature-input/` |
| 453 | `analysis/scenarios/confirmed-scenarios.md` | `kym/scenarios/confirmed-scenarios.md` |

### 8.2 不触碰的路径引用（MFQ/PPDCS）

经 grep 验证，`skills/feature-parser/SKILL.md` 和 `skills/scenario-discovery/SKILL.md` 中均不含 `analysis/m-analysis/`、`analysis/f-analysis/`、`design/ppdcs/` 引用。无遗漏风险。

### 8.3 依赖选择与复用点

- **纯文本替换**：不涉及结构化解析或 AST 操作。使用 `sed` 或逐行替换即可。
- **不依赖任何外部工具或 Skill**

### 8.4 兼容性处理

- **路径引用一致性**：所有路径替换基于精确字符串匹配（含反引号内路径），不使用通配符
- **Gotchas 中的重复路径**：第 134 行 Gotchas 是同一条文本中包含 3 个 `analysis/feature-input/` 实例，需全部替换（作为一处替换操作中的多实例）
- **Git diff 最小化**：只修改路径字符串，不修改任何描述文字或段落结构

## 9. 安全与性能设计

| 维度 | 设计措施 | 验证方式 |
|---|---|---|
| 安全 | 纯文本替换，不涉及命令执行、文件删除或权限变更 | 不适用 |
| 性能 | 两个文件共 13 处替换，文本操作 < 1s | 不适用 |

## 10. 测试设计

| 测试场景 | 前置条件 | 操作 | 预期结果 | 验证方式 |
|---|---|---|---|---|
| TC-01: feature-parser 路径迁移 | feature-parser SKILL.md 原始内容含 5 处 `analysis/feature-input/` | 执行全部 5 处替换 | `grep "analysis/feature-input" skills/feature-parser/SKILL.md` 返回 0；`grep "kym/feature-input" skills/feature-parser/SKILL.md` 返回 5 | grep 命令验证 |
| TC-02: feature-parser 未丢失内容 | 替换完成 | 检查 SKILL.md 行数 | 总行数不变（147 行），只改了 5 处路径字符串 | `wc -l` 或 diff 对比 |
| TC-03: scenario-discovery 路径迁移 | scenario-discovery SKILL.md 原始内容含 2 处 `analysis/feature-input/` + 6 处 `analysis/scenarios/` | 执行全部 8 处替换 | `grep "analysis/feature-input\|analysis/scenarios" skills/scenario-discovery/SKILL.md` 返回 0 | grep 命令验证 |
| TC-04: scenario-discovery 未丢失内容 | 替换完成 | 检查 SKILL.md 行数 | 总行数不变（583 行），只改了 8 处路径字符串 | `wc -l` 或 diff 对比 |
| TC-05: KYM 边界无越界修改 | 替换完成 | 检查两个文件 | 确认无 `analysis/m-analysis`、`analysis/f-analysis`、`design/ppdcs` 等 MFQ/PPDCS 路径被误改 | grep 验证 |
| TC-06: 路径引用格式一致性 | 替换完成 | 检查所有新路径 | 所有 `kym/feature-input/` 和 `kym/scenarios/` 引用与 kym Skill（STORY-011-01）和 Agent（STORY-011-04）中使用的路径一致 | 人工对比 |

## 11. 实施步骤

> 严格使用 TASK-ID + 确定性动词。

| TASK-ID | 动作 | 目标文件 | 详细描述 | 对应测试 |
|---|---|---|---|---|
| TASK-011-02-01 | 修改 | `skills/feature-parser/SKILL.md` | 将第 21、36、104、134、145 行的 `analysis/feature-input/` 全部替换为 `kym/feature-input/`。第 134 行 Gotchas 含 3 个实例，全部替换 | TC-01, TC-02 |
| TASK-011-02-02 | 修改 | `skills/scenario-discovery/SKILL.md` | 将第 51、136 行的 `analysis/feature-input/` 替换为 `kym/feature-input/`；将第 34(x2)、52、53、80、453 行的 `analysis/scenarios/` 替换为 `kym/scenarios/` | TC-03, TC-04 |
| TASK-011-02-03 | 验证 | `skills/feature-parser/SKILL.md` `skills/scenario-discovery/SKILL.md` | 运行 `grep -rn "analysis/feature-input\|analysis/scenarios" skills/feature-parser/SKILL.md skills/scenario-discovery/SKILL.md`，预期返回 0 | TC-01, TC-03, TC-05 |
| TASK-011-02-04 | 验证 | 两个文件 | 检查 `git diff` 确认只修改了路径字符串，无其他意外变更 | TC-02, TC-04, TC-06 |

## 12. 风险、难点与预研建议

### 12.1 实现灰区与取舍记录

| Clarification ID | 问题 | 选项与推荐 | 决策 / 答案 | 影响面 | 证据 | 重访条件 |
|---|---|---|---|---|---|---|
| — | 无 | — | — | — | — | — |

> 本 Story 为纯文本替换，实现在 HLD v1.1 AGA-04（路径迁移范围边界）中已全部确认。无新增灰区。

| 风险 / 难点 | 影响 | 缓解措施 / 预研建议 |
|---|---|---|
| R1: Gotchas 中重复实例替换不完整 | feature-parser 第 134 行 Gotchas 含 3 个 `analysis/feature-input/` 实例，易遗漏 | TASK-011-02-01 明确标注 3 个实例；TC-01 grep 验证 0 残留 |
| R2: scenario-discovery 中存在非 KYM 阶段的 `analysis/` 路径被误改 | MFQ/PPDCS 路径被修改会导致跨阶段引用断裂（CR-012/013 按原计划各自迁移） | TASK-011-02-02 明确区分 KYM vs MFQ/PPDCS 路径；TC-05 验证无越界；grep 确认无 `analysis/m-analysis/` 或 `design/ppdcs/` 引用 |
| R3: 与 CR-010 已修改的路径产生合并冲突 | CR-010 若已修改同一文件的同一行附近（当前基线 feature-parser 和 scenario-discovery 路径未在 CR-010 中修改，风险低）| 采用 `git merge` 三路合并；如冲突则手动解决。CR-010 不修改 feature-parser 和 scenario-discovery 的 SKILL.md 输出路径 |

### OPEN / Spike 跟踪

| ID | 类型（OPEN / Spike） | 问题 | 下一动作 | 责任方 |
|---|---|---|---|---|
| — | — | 本 Story 无 OPEN / Spike 项 | — | — |

## 13. 回滚与发布策略

- **发布方式**：通过 git 提交 feature-parser 和 scenario-discovery 两个 SKILL.md 的路径替换变更。与 STORY-011-01（kym Skill 新建）同属 Wave A，可合并提交或分两个 commit。
- **回滚触发条件**：验证命令返回非 0（路径替换不完整）、或 MFQ/PPDCS 路径被误改、或 CP5 全量确认未通过。
- **回滚动作**：`git revert` 回退 STORY-011-02 对应 commit（还原两个 SKILL.md 的路径替换）。回退后 feature-parser 和 scenario-discovery 恢复写入 `analysis/` 路径，kym Skill（STORY-011-01）不受影响（kym Skill 从 `kym/feature-input/` 读取，但 feature-parser 回退后写回 `analysis/`，导致 kym Skill 阶段零无法预填数据——降级为全部询问用户）。

## 14. Definition of Done

- [ ] 14 个章节全部填写完成
- [ ] `skills/feature-parser/SKILL.md` 中无 `analysis/feature-input/` 残留
- [ ] `skills/scenario-discovery/SKILL.md` 中无 `analysis/feature-input/` 和 `analysis/scenarios/` 残留
- [ ] MFQ/PPDCS 路径（`analysis/m-analysis/`、`analysis/f-analysis/`、`design/ppdcs/`）未被修改
- [ ] `git diff` 只包含路径字符串修改，无意外变更
- [ ] 文件影响范围、接口、测试与实施步骤可直接指导编码
- [ ] 实现灰区与取舍记录已回填（本 Story 无新增灰区，已显式写"无"）
- [ ] `confirmed=false` 时不进入实现
- [ ] frontmatter 已填写 `tier=S`
- [ ] OPEN / Spike 已清点（已显式写"无"）

## 人工确认区

> **CP5 — Story LLD 可实现性门**
> meta-dev 先写入 `process/checks/CP5-STORY-011-02-kym-path-migration-LLD-IMPLEMENTABILITY.md` 自动预检结果。
> meta-po 收齐全部目标 Story 的 LLD、CP4 自动预检摘要和 CP5 自动预检后，再生成并提示用户审查 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-011.md`。
> 用户统一确认全部目标 Story 的 LLD 后，仍需满足当前 Wave、依赖门控与文件所有权门控方可进入实现。

**CP5 checklist 摘要**：

| # | 检查项 | 状态 | 证据 |
|---|---|---|---|
| 1 | LLD 覆盖 AC | 待检查 | 第 2 / 10 / 14 节（AC-01~AC-05 + NF-01~NF-03 均有对应测试和实施步骤）|
| 2 | 与 HLD / ADR 一致 | 待检查 | 第 8.1/8.2 节（路径迁移映射与 HLD §18.3 完全一致；不触碰 MFQ/PPDCS 路径）|
| 3 | 文件影响范围明确 | 待检查 | 第 4 / 11 节（2 文件 13 处替换，4 个 TASK-ID）|
| 4 | 接口契约完整 | 待检查 | 第 6 节（feature-parser 输出 / scenario-discovery 输入输出 / 跨 Story 契约）|
| 5 | 测试与 dev_gate 可计算 | 待检查 | 第 10 / 14 节（6 条 TC + DoD checklist）|
| 6 | clarification queue 已收敛 | 待检查 | 第 12.1 节（显式写"无"，无 blocks_lld 项）|

**人工确认回复**：

请直接回复以下任一整行：

```text
approve
修改: <具体修改点>
reject
```

- `approve`：LLD 设计合理，允许进入实现（需全量 CP5 统一确认后方可）。
- `修改: <具体修改点>`：指出具体修改点后由 meta-dev 更新重提。
- `reject`：设计方向有根本问题，需重新设计。

**人工审查结果回填**：

- 结论：`approved | changes_requested | rejected`
- 审查人：
- 审查时间：
- 修改意见：
- 风险接受项：
