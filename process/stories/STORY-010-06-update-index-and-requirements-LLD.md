# LLD — STORY-010-06 更新索引与需求文件

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|----------|
| 1.0 | 2026-06-01 | meta-dev | 初始 LLD，定义 3 个索引/需求文件的变更方案。 |
| 1.1 | 2026-06-01 | meta-dev | [M1] 补全 meta-dev LLD 规范要求的 7 个缺失章节：Requirements (F/NF)、模块拆分与职责、数据模型与持久化设计、技术设计细节、安全与性能设计、实施步骤、风险/难点与预研建议。 |

---

## 1. 概述

将 ptm-team 项目级的索引文件（`skills/README.md`、`agents/README.md`）和需求基线文件（`process/REQUIREMENTS-ptm-tde.md`）中的 **11 步 + CP 体系**引用更新为 **三阶段 + Gate 体系**，并新增 REQ-030（三阶段框架）和 REQ-031（MFQ Exit Gate）需求条目。

**核心文件**（3 个）：
1. `skills/README.md` — Skill 索引
2. `agents/README.md` — Agent 说明
3. `process/REQUIREMENTS-ptm-tde.md` — 需求基线

本 Story 是 CR-010 的最后一个实现类 Story，完成后整个框架改造的文档体系已闭环，剩余 STORY-010-07（grep 验证）为纯验证任务。

---

## 2. 受影响文件清单

| 文件 | 变更类型 | 变更范围 | 预计行数变化 |
|------|----------|----------|------------|
| `skills/README.md` | 更新 | 使用说明文本 + Cross-Stage Contracts 路径引用 | ±15 行 |
| `agents/README.md` | 更新 | ptm-tde 章节描述 | ±5 行 |
| `process/REQUIREMENTS-ptm-tde.md` | 更新 | frontmatter + 新增 REQ-030 + REQ-031 + 修订记录 | +50 行 |

---

## 3. 变更方案

### 3.1 skills/README.md 变更

**章节定位**：`skills/README.md`（当前 42 行）

#### 3.1.1 使用说明文本更新

**位置**：`## 使用说明`（第 7-9 行）

改前：
```markdown
- **调用**：Skill 由 ptm-tde Agent 按 11 步主流程自动调度，用户只需在人工检查点（CP02/CP09/CP11）确认输出。
```

改后：
```markdown
- **调用**：Skill 由 ptm-tde Agent 按三阶段框架自动调度，用户只需在 Gate 确认点（GATE-2/GATE-3/GATE-4）确认输出。
```

#### 3.1.2 Cross-Stage Contracts 路径更新

**位置**：`## ptm-tde Cross-Stage Contracts`（第 36-42 行）

变更：
- 第 38 行：`analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`
- 第 39 行：同上（LC topology_bindings 来源引用）

改前：
```markdown
- CAE / TP 阶段只引用 `topology_role_refs`；真实 `DUT.port1`、`TG.port1` 和 link 实例只能从 `analysis/scenarios/confirmed-scenarios.md` 进入 LC `topology_bindings`。
```

改后：
```markdown
- CAE / TP 阶段只引用 `topology_role_refs`；真实 `DUT.port1`、`TG.port1` 和 link 实例只能从 `kym/scenarios/confirmed-scenarios.md` 进入 LC `topology_bindings`。
```

---

### 3.2 agents/README.md 变更

**章节定位**：`agents/README.md`（当前 56 行）

#### 3.2.1 ptm-tde 章节说明更新

**位置**：`## ptm-tde`（第 53-55 行）

改前：
```markdown
## ptm-tde

MFQ&PPDCS 测试用例设计工具，详细说明见 [docs/ptm-tde/README.md](../docs/ptm-tde/README.md)。
```

改后：
```markdown
## ptm-tde

MFQ&PPDCS 测试用例设计工具，基于三阶段框架（KYM → MFQ → PPDCS）+ 入口/出口门控（GATE-1 至 GATE-5）推进完整测试分析与用例设计流程。详细说明见 [docs/ptm-tde/README.md](../docs/ptm-tde/README.md)。
```

---

### 3.3 process/REQUIREMENTS-ptm-tde.md 变更

**章节定位**：`process/REQUIREMENTS-ptm-tde.md`（当前 105 行）

#### 3.3.1 Frontmatter 更新

改前：
```yaml
---
status: confirmed
version: "6.2"
confirmed_by: "user (CR-20260528-001 approved)"
confirmed_at: "2026-05-28T19:30:00+08:00"
...
total_requirements: 29
source_inputs:
  ...
  - process/changes/CR-20260528-001.md
---
```

改后：
```yaml
---
status: confirmed
version: "7.0"
confirmed_by: "user (CR-010 approved)"
confirmed_at: "2026-06-01T15:30:00+08:00"
target_artifact_type: agent
governance_mode: conditional
review_policy: light
total_requirements: 31
source_inputs:
  - process/USE-CASES.md
  - process/REQUEST.md
  - user-feedback-2026-04-23
  - user-feedback-2026-04-23-kb-mcp
  - user-feedback-2026-04-23-hld-refine
  - user-feedback-2026-04-24-tool-analysis
  - process/changes/CR-008.md
  - process/changes/CR-20260528-001.md
  - process/changes/CR-010-ptm-tde三阶段框架改造.md
---
```

#### 3.3.2 新增 REQ-030（三阶段框架）

**插入位置**：在 REQ-029 之后，`## 风险与假设` 之前

```markdown
| REQ-030 | 功能 | 系统应采用三阶段框架（KYM / MFQ / PPDCS）替换当前 11 步线性状态机，并按入口/出口门控（GATE-1 至 GATE-5）管理阶段转换：GATE-1 Entry Gate 为纯自检（入口检查），GATE-2 KYM Exit Gate 和 GATE-4 PPDCS Exit Gate 为自检+人工确认，GATE-3 MFQ Exit Gate 为自检+人工确认（新增），GATE-5 Exit Gate 为纯自检（出口检查）。MFQ 和 PPDCS 阶段内部保留阶段内滚动自检。 | P0 | Given 用户启动 ptm-tde，When 推进到阶段边界，Then 执行对应 Gate 的自动自检；GATE-2/3/4 需要人工确认时展示统一决策清单并等待用户回复。 | CR-010 / UC-02 至 UC-06 |
| REQ-031 | 功能 | 系统应在 MFQ 阶段完成后新增 MFQ Exit Gate（GATE-3）作为自检+人工确认点，检查 M/F/Q 分析完整性、LC 整合一致性、设计计划存在性和公共因子消费记录；上下游衔接以非阻断 Warning 提示并在人工确认稿中区分展示。 | P0 | Given MFQ 阶段所有 Skill 已执行完成，When 触发 GATE-3 MFQ Exit Gate，Then 执行 8 项 Checklist 自动自检并生成确认稿；上下游 Warning 不影响 Exit Criteria 判定。 | CR-010 / UC-04 |
```

#### 3.3.3 风险与假设 — 更新路径引用

**位置**：`## 风险与假设` 表格中

变更：
- RA-09 中 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`（当前为 "拓扑绑定通过 `kym/scenarios/confirmed-scenarios.md` 承载"）

当前 RA-09 行：
```markdown
| RA-09 | 风险 | 组网图若缺少设备端口归属... | REQ-028 | 在场景确认时同时展示 Mermaid、YAML 和三张清单表... |
```

无旧路径引用需更新，保持不变。

#### 3.3.4 产品文档路径引用（如有）

当前 REQUIREMENTS-ptm-tde.md 中无旧 `analysis/` 或 `design/` 路径引用，不需要更新。

#### 3.3.5 修订记录追加

**位置**：`## 变更记录` 表格末尾

追加一行：
```markdown
| 7.0 | confirmed | 按 CR-010 新增 REQ-030（三阶段框架 + 5 Gate 门控体系）和 REQ-031（MFQ Exit Gate 自检+人工确认点）。 | meta-po | 2026-06-01T15:30:00+08:00 |
```

---

## 4. 接口与契约

本 Story 仅修改文档和需求声明，不引入新接口。

**需求文件变更影响**：
- `process/REQUIREMENTS-ptm-tde.md` 的 `total_requirements` 从 29 增至 31
- REQ-030 定义了架构级需求（三阶段 + Gate），对下层 Story（CR-011/012/013）提供需求追溯
- REQ-031 定义了新增功能需求（GATE-3 MFQ Exit Gate），对 GATE-3 的 Checklist 细节提供需求追溯

---

## 5. 异常与失败处理

| 场景 | 处理 |
|------|------|
| REQ-030/REQ-031 编号与已有需求冲突 | 现有需求编号为 REQ-001 至 REQ-029，REQ-030/031 为连续递增，无冲突 |
| Frontmatter `total_requirements` 更新遗漏 | 验证脚本检查 `total_requirements` 值与需求表格行数是否一致 |
| 修订记录中新行与其他 CR 时间线不一致 | 修订记录按时间降序排列，新行插入在 v6.2 之后 |

---

## 6. 测试方案

| 测试项 | 验证方式 | 预期结果 |
|--------|----------|----------|
| skills/README.md 旧编号消除 | `grep "11 步\|CP02\|CP09\|CP11" skills/README.md` | 0（除历史记录外） |
| skills/README.md 路径更新 | `grep "analysis/scenarios/confirmed-scenarios" skills/README.md` | 0 |
| agents/README.md 包含三阶段描述 | `grep "三阶段框架\|KYM\|MFQ\|PPDCS\|GATE" agents/README.md` | 匹配到新描述 |
| REQUIREMENTS frontmatter 版本号 | `grep "version:" process/REQUIREMENTS-ptm-tde.md` | 输出 `"7.0"` |
| REQUIREMENTS total_requirements 计数 | 统计表格中 REQ 条目数 | 返回 31 |
| REQ-030 存在且可追溯 | 检查 REQ-030 包含三阶段 + 5 Gate + 检查点类型描述 | 包含完整功能描述 |
| REQ-031 存在且可追溯 | 检查 REQ-031 包含 GATE-3 Checklist + Warning 处理 | 包含完整功能描述 |
| 修订记录包含 v7.0 | `grep "7.0" process/REQUIREMENTS-ptm-tde.md` | 匹配到修订记录行 |

---

## 7. 回滚方案

| 回滚方式 | 操作 |
|----------|------|
| git revert | `git revert <commit-hash>`，将 3 个文件恢复到改造前状态 |
| REQUIREMENTS 单独回退 | 删除 REQ-030/REQ-031 两行，回退 frontmatter 到 v6.2，删除修订记录 v7.0 行 |

**回退影响**：
- 回退后 STORY-010-02 和 STORY-010-05 中的新框架描述失去需求追溯
- STORY-010-07（grep 验证）将检测到文档与需求版本不一致

---

## 8. tier（复杂度）

**tier = S**

判定依据：
- 文件数：3 个
- 变更行数：合计约 +70 行
- 变更类型：文本更新 + 需求条目新增
- 风险：低（纯文档变更，无逻辑实现）

---

## 9. shared_fragments（共享片段引用）

| 片段 | 来源 | 用途 |
|------|------|------|
| 三阶段框架文本 | `agents/ptm-tde.md`（STORY-010-02 产物） | agents/README.md ptm-tde 描述 |
| Gate 编号与类型 | `docs/ptm-tde/gate-spec.md` | REQ-030/REQ-031 需求描述 |
| CP↔Gate 映射 | `docs/ptm-tde/gate-spec.md` | skills/README.md 上下文 |
| CR-010 批准时间 | `process/changes/CR-010-ptm-tde三阶段框架改造.md` frontmatter | REQUIREMENTS v7.0 修订记录 |

---

## 10. open_items（待确认项）

| ID | 问题 | 状态 | 说明 |
|----|------|------|------|
| O-06-01 | `skills/README.md` 中 `## ptm-tde Cross-Stage Contracts` 的路径引用是否需要更新 `analysis/` 下其他路径（如 `analysis/plan/` → `process/plan/`）？ | OPEN | 当前 Cross-Stage Contracts 仅涉及 `confirmed-scenarios.md` 路径，暂无其他旧路径引用。若后续 CR 修改了 Skill 输出路径，此处需要同步更新。 |
| O-06-02 | `process/REQUIREMENTS-ptm-tde.md` 中 RA-07/RA-08 等风险描述是否受框架改造影响需要更新？ | OPEN | 风险描述与 Skill 行为相关，不受框架改造影响——不需更新。但 `confirmed-scenarios.md` 路径引用如出现则需同步。当前检查无旧路径。 |

---

## 11. 验证 checklist

- [ ] `skills/README.md` 使用说明中 "11 步" 替换为 "三阶段框架"
- [ ] `skills/README.md` 使用说明中 "CP02/CP09/CP11" 替换为 "GATE-2/GATE-3/GATE-4"
- [ ] `skills/README.md` Cross-Stage Contracts 中 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md`
- [ ] `agents/README.md` ptm-tde 章节包含三阶段 + Gate 描述
- [ ] `process/REQUIREMENTS-ptm-tde.md` frontmatter: `version` = `"7.0"`, `total_requirements` = `31`, `source_inputs` 包含 CR-010 路径
- [ ] REQ-030 包含：三阶段名称、5 个 Gate 编号和类型、人工确认规则
- [ ] REQ-031 包含：GATE-3 检查范围、上下游 Warning 为非阻断、人工确认稿区分规则
- [ ] 修订记录包含 v7.0 行，描述正确

---

## 12. 依赖与门控

| 依赖项 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| STORY-010-02 | contract | pending | 主 Agent 框架重写完成后，REQ-030/REQ-031 的需求描述和 agents/README.md 的描述才能与主 Agent 保持一致 |
| STORY-010-05 | runtime | pending | 核心文档更新完成后，skills/README.md 和 agents/README.md 的路径引用才能对应用户可见的文档 |
| STORY-010-01 | contract | done | `gate-spec.md` Gate 编号和命名已冻结，REQ-030/REQ-031 引用遵循 |

---

## 13. DEV-LOG 预留

实现时在此记录：
- REQ-030/REQ-031 最终文本
- 跨文件一致性验证结果
- 前置 Story 完成状态确认

---

## 14. Gotchas

1. **`total_requirements` 字段遗漏更新**：frontmatter 中的 `total_requirements: 29` 需改为 `total_requirements: 31`。该值与需求表格行数通过 CP 验证脚本校验，不一致会导致后续 CR 的需求追溯出问题。

2. **REQ-030 的归因来源**：REQ-030 影响 KYM（GATE-1/2）、MFQ（GATE-3）、PPDCS（GATE-4/5）以及交付（GATE-5），因此来源标注为 `CR-010 / UC-02 至 UC-06`，覆盖全部 5 个 Use Case。

3. **REQ-031 的归因来源**：REQ-031 仅影响 MFQ 阶段和 GATE-3，来源标注为 `CR-010 / UC-04`。

4. **`skills/README.md` 的 Skill Index 不修改**：本节只改变使用说明和 Cross-Stage Contracts，Skill Index 中 19 个 Skill 的职责描述保持不变——Skill 的运行逻辑未变，只是阶段归属变了（由 STORY-010-02 的 `agents/ptm-tde.md` 和 STORY-010-05 的 `skill-references.md` 承载）。

5. **`agents/README.md` 中的 ngfw-factory-installer 章节不修改**：该章节与 CR-010 无关，保留原样。

---

## 补充章节：Requirements（Functional / Non-Functional）

> 本部分补全 meta-dev LLD 规范要求的章节，内容来自 CR-010 与 HLD-CR-010。

### Functional Requirements

| # | 需求 | 来源 |
|---|------|------|
| FR-06-01 | `skills/README.md` 使用说明中「11 步主流程」→「三阶段框架」，「CP02/CP09/CP11」→「GATE-2/GATE-3/GATE-4」；Cross-Stage Contracts 中 `analysis/scenarios/confirmed-scenarios.md` → `kym/scenarios/confirmed-scenarios.md` | CR-010 §目录结构迁移 |
| FR-06-02 | `agents/README.md` ptm-tde 章节增加三阶段框架（KYM → MFQ → PPDCS）+ 5 Gate 门控描述 | CR-010 §三阶段框架 |
| FR-06-03 | `process/REQUIREMENTS-ptm-tde.md` frontmatter 更新：`version=7.0`、`total_requirements=31`、source_inputs 增加 CR-010 路径 | CR-010 §需求基线 |
| FR-06-04 | 新增 REQ-030（三阶段框架 + 5 Gate 门控体系）和 REQ-031（MFQ Exit Gate 自检+人工确认点） | CR-010 §新增 MFQ Exit Gate |
| FR-06-05 | 修订记录追加 v7.0 行，描述 CR-010 新增需求 | CR-010 §变更记录 |

### Non-Functional Requirements

- **需求追溯**：REQ-030/REQ-031 提供完整的 GIVEN/WHEN/THEN 验收条件，可被后续 CR-011/012/013 的需求追溯到
- **版本一致性**：REQUIREMENTS frontmatter 的 `total_requirements` 值与表格行数一致
- **文档一致性**：`skills/README.md` 和 `agents/README.md` 中的新框架描述与 `agents/ptm-tde.md` 保持一致

---

## 补充章节：模块拆分与职责

本 Story 修改 3 个文件，不涉及模块拆分：

| 文件 | 变更职责 |
|------|----------|
| `skills/README.md` | 2 处变更：使用说明文本（11 步→三阶段、CP→Gate）+ Cross-Stage Contracts 路径引用 |
| `agents/README.md` | 1 处变更：ptm-tde 章节增加三阶段框架描述 |
| `process/REQUIREMENTS-ptm-tde.md` | 3 处变更：frontmatter 更新 + 新增 REQ-030/REQ-031 + 修订记录追加 |

---

## 补充章节：数据模型与持久化设计

本 Story 为纯文档/需求声明更新，不涉及数据模型或持久化存储。

---

## 补充章节：技术设计细节

- **需求条目格式**：REQ-030/REQ-031 遵循 `process/REQUIREMENTS-ptm-tde.md` 现有表格格式（编号/类型/功能描述/优先级/验收条件/来源），不使用新格式
- **frontmatter 更新**：`version` 从 `"6.2"` 升级到 `"7.0"`（主版本号升级，因 CR-010 引入了结构性框架变更）；`total_requirements` 从 29 增至 31
- **修订记录**：按时间降序排列，v7.0 插入在 v6.2 之前

---

## 补充章节：安全与性能设计

本 Story 为纯文档/需求声明更新，不涉及运行时代码变更，无安全风险或性能影响。

---

## 补充章节：实施步骤

| 步骤 | 操作 | 验证方式 |
|------|------|----------|
| 1 | 更新 `skills/README.md`：使用说明 + Cross-Stage Contracts | `grep "11 步\|CP02\|CP09\|CP11" skills/README.md` 返回 0（除历史记录外） |
| 2 | 更新 `agents/README.md`：ptm-tde 章节描述 | `grep "三阶段框架\|KYM\|MFQ\|PPDCS\|GATE" agents/README.md` 匹配到新描述 |
| 3 | 更新 `process/REQUIREMENTS-ptm-tde.md` frontmatter | `grep "version:" process/REQUIREMENTS-ptm-tde.md` 输出 `"7.0"` |
| 4 | 新增 REQ-030 和 REQ-031 | 检查 REQ-030 含三阶段+5 Gate，REQ-031 含 GATE-3 Checklist+Warning |
| 5 | 追加修订记录 v7.0 行 | `grep "7.0" process/REQUIREMENTS-ptm-tde.md` 匹配到修订记录行 |

---

## 补充章节：风险、难点与预研建议

| 风险 / 难点 | 影响 | 缓解措施 |
|-------------|------|----------|
| `total_requirements` 遗漏更新 | 中 — 若 frontmatter 值未更新，CP 验证脚本检测到与表格行数不一致 | 实施步骤 3 验证脚本逐行计数 |
| REQ-030/REQ-031 描述不完整 | 低 — 若验收条件不完整，后续 CR 追溯困难 | 参照现有 REQ 格式填写完整的 GIVEN/WHEN/THEN |
| Cross-Stage Contracts 遗漏其他旧路径 | 低 — 当前仅涉及 `confirmed-scenarios.md` 路径 | grep 扫描 `analysis/` 确认无其他残留 |
