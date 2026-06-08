# CP5 自动预检：STORY-012-04 — F 分析器 v3.0 重写

| 字段 | 值 |
|------|-----|
| Story ID | STORY-012-04 |
| LLD 路径 | `process/stories/STORY-012-04-f-analyzer-v3-rewrite-LLD.md` |
| Story 卡片 | `process/stories/STORY-012-04-f-analyzer-v3-rewrite.md` |
| 检查时间 | 2026-06-02T23:30:00+08:00 |
| 检查人 | meta-dev（Agent C） |
| HLD | `process/HLD-CR-012.md` (v1.1, confirmed) |
| 依赖状态 | STORY-012-01（lld-ready-for-review）+ STORY-012-03（lld-ready-for-review） |

---

## Entry Criteria

| # | 条件 | 状态 | 证据 |
|---|---|---|---|
| 1 | Story status 为 `lld-ready-for-review` | ✅ PASS | Story frontmatter `status: lld-ready-for-review` |
| 2 | LLD 文件存在且非空 | ✅ PASS | `process/stories/STORY-012-04-f-analyzer-v3-rewrite-LLD.md`（~28KB） |
| 3 | HLD 已确认 | ✅ PASS | `process/HLD-CR-012.md` `confirmed: true` |
| 4 | CP3 HLD 人工确认通过 | ✅ PASS | `checkpoints/CP3-HLD-REVIEW-CR-012.md` `approved` |

---

## Checklist

### 1. LLD 覆盖 Story 验收标准

| AC | 对应 LLD 章节 | 状态 |
|---|---|---|
| AC01（grep TSP >= 5） | §7.2 步骤 2 + §11 TASK-012-04-05/06/10/13 | ✅ |
| AC02（[F→] 标签消费） | §7.2 步骤 2 子步骤 A + §8.1 F 线索索引 | ✅ |
| AC03（覆盖矩阵引用） | §5.1 消费数据 + §6.1 输入契约 | ✅ |
| AC04（输出路径 mfq/f-analysis/） | §5.2 生产数据 + §11 TASK-012-04-11/12/14 | ✅ |
| AC05（耦合对象发现） | §7.2 步骤 2 子步骤 B + §11 TASK-012-04-06 | ✅ |
| AC06（耦合因子候选） | §7.4 降级规则 + §11 TASK-012-04-13 | ✅ |
| AC07（discovery_source） | §8.1 关键算法 + §11 TASK-012-04-06/08 | ✅ |
| AC08（CAE 耦合约束） | §8.2 复用点 + §11 TASK-012-04-04/09/10 | ✅ |
| AC09（三源合并） | §7.3 三源合并规则 + §11 TASK-012-04-05/07/08 | ✅ |
| AC10（name 不变） | §4 文件影响范围 + §11 TASK-012-04-01 | ✅ |

**结论**：10/10 AC 全部覆盖 ✅

### 2. LLD 与 HLD / 设计文档一致性

| 检查项 | HLD / 设计文档依据 | LLD 章节 | 状态 |
|---|---|---|---|
| 9 步流程 | HLD §9（F 分析器 v3.0 9 步） | §7.1 主流程 | ✅ 一致 |
| 消费 TSP + 覆盖矩阵 + [F→] 标签 | HLD §9（F 分析器消费 M 分析的 TSP + F 线索） | §5.1 + §6.1 | ✅ 一致 |
| 逐 TSP 驱动 | 设计文档 §4 步骤 2 | §7.2 详细子流程 | ✅ 一致 |
| 耦合对象/因子发现 | 设计文档 §4 子步骤 B/C | §7.2 子步骤 B/C | ✅ 一致 |
| discovery_source 区分 | 设计文档 §4 子步骤 A（f-tag-seed / scenario-inference） | §8.1 discovery_source 聚合 | ✅ 一致 |
| 三源合并 | 设计文档 §4 步骤 4 | §7.3 三源合并规则 | ✅ 一致 |
| 耦合测试点按 TSP 组织 | 设计文档 §4 步骤 6 | §7.1 步骤 6 + §11 TASK-012-04-10 | ✅ 一致 |
| F 输出路径 mfq/f-analysis/ | HLD §9（F 分析器输出路径） | §5.2 + §11 TASK-012-04-14 | ✅ 一致 |
| 候选汇总 | HLD §9（F 分析器产出耦合因子候选列表） | §7.4 + §11 TASK-012-04-13 | ✅ 一致 |
| STOP 协议 | HLD §11 STOP-01~05 | §9 安全设计 + §12.1 | ✅ 一致 |

**结论**：10/10 一致性检查通过 ✅

### 3. 文件影响范围明确

| 检查项 | 状态 | 证据 |
|---|---|---|
| 文件清单完整 | ✅ | §4：1 个文件 `skills/f-analyzer/SKILL.md`（全量重写） |
| 不改动项明确 | ✅ | §4 末尾列出 6 项不改动内容 |
| 改动量可度量 | ✅ | 314 行→~450 行，净增 ~150 行 |

**结论**：通过 ✅

### 4. 接口契约完整

| 接口方向 | 条目数 | 状态 |
|---|---|---|
| 输入消费契约 | 6 条（TSP 列表、覆盖矩阵、测试对象表、因子表、场景、Excel 工具） | ✅ §6.1 |
| 输出生产契约 | 4 条（coupling-graph.yaml、coupling-test-points.md、tool-analysis.md、耦合因子候选列表） | ✅ §6.2 |
| 消费方标注 | 每条输出明确标注 test-point-integrator（STORY-012-06）或候选汇总（STORY-012-07） | ✅ §6.2 |
| 测试覆盖 | 每条接口在 §10 中有对应测试 | ✅ §10 → §6 交叉引用 |

**结论**：通过 ✅

### 5. 测试设计可执行

| 检查项 | 状态 | 证据 |
|---|---|---|
| AC 映射表完整 | ✅ | §10.1：10 AC 全部映射 |
| 关键流程测试 | ✅ | §10.2：5 个关键流程测试（TSP 驱动、F 线索缺失降级、全候选降级、HARD-STOP、路径校验） |
| 测试可验证 | ✅ | 全部使用 grep/人工审阅验证 |

**结论**：通过 ✅

### 6. LLD Clarification Queue 收敛

| ID | 问题 | blocks_lld | 状态 |
|---|---|---|---|
| LCQ-STORY-012-04-01 | object_role_in_coupling 枚举约束 | false | open — 等待 meta-po 收集后统一确认 |
| LCQ-STORY-012-04-02 | F 线索指向不存在 TSP 的处理策略 | false | open — 等待 meta-po 收集后统一确认 |

**结论**：2 项均不阻断 LLD（`blocks_lld=false`），可在 CP5 人工确认时一并决策 ✅

---

## Exit Criteria

| # | 条件 | 状态 |
|---|---|---|
| 1 | 6 项 checklist 全部完成 | ✅ PASS |
| 2 | 无 FAIL 项 | ✅ PASS |
| 3 | 0 项 `blocks_lld=true` | ✅ PASS |
| 4 | LLD 可提交人工审查 | ✅ PASS |

---

## 自动预检结论

**✅ PASS**（6/6 checklist 通过，2 项 non-blocking LCQ 待人工确认）

> 下一动作：meta-po 收齐全部 8 个目标 Story 的 CP5 自动预检后，生成 `checkpoints/CP5-ALL-STORIES-LLD-BATCH-CR-012.md`，发起统一人工确认。
