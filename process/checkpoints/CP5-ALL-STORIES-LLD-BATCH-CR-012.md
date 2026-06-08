# CP5 全量 Story LLD 人工确认 — CR-012 MFQ 阶段改造

| 字段 | 值 |
|------|-----|
| 批次 ID | CR-012-all-stories |
| 目标 Story 数 | 8 |
| 自动预检通过率 | 8/8（100%） |
| 创建时间 | 2026-06-02T22:30:00+08:00 |
| 创建者 | meta-po |
| 状态 | ✅ approved（2026-06-02） |

---

## 自动预检汇总

| # | Story ID | 名称 | tier | Wave | CP5 结果 | 文件 |
|---|----------|------|------|------|----------|------|
| 1 | STORY-012-01 | MFQ 路径迁移 | S | A | ✅ PASS | `CP5-STORY-012-01-*-IMPLEMENTABILITY.md` |
| 2 | STORY-012-02 | MFQ Exit Gate 增强 | S | A | ✅ PASS | `CP5-STORY-012-02-*-IMPLEMENTABILITY.md` |
| 3 | STORY-012-03 | M 分析器 v3.0 重写 | M | B | ✅ PASS | `CP5-STORY-012-03-*-IMPLEMENTABILITY.md` |
| 4 | STORY-012-04 | F 分析器 v3.0 重写 | M | C | ✅ PASS | `CP5-STORY-012-04-*-IMPLEMENTABILITY.md` |
| 5 | STORY-012-05 | Q 分析器 v3.0 重写 | M | C | ✅ PASS | `CP5-STORY-012-05-*-IMPLEMENTABILITY.md` |
| 6 | STORY-012-06 | 上下游适配 | M | D | ✅ PASS | `CP5-STORY-012-06-*-IMPLEMENTABILITY.md` |
| 7 | STORY-012-07 | 候选汇总 + STOP 协议 | M | D | ✅ PASS | `CP5-012-07-*-IMPLEMENTABILITY.md` |
| 8 | STORY-012-08 | 文档更新 | S | D | ✅ PASS | `CP5-STORY-012-08-*-IMPLEMENTABILITY.md` |

**自动预检总计**：96/96 项 PASS（12 项 × 8 Story），0 FAIL，0 BLOCKED。

---

## 文件所有权矩阵

| 文件 | 012-01 | 012-02 | 012-03 | 012-04 | 012-05 | 012-06 | 012-07 | 012-08 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `skills/m-analyzer/SKILL.md` | ✅ | | ✅ | | | | ✅ | |
| `skills/f-analyzer/SKILL.md` | ✅ | | | ✅ | | | ✅ | |
| `skills/q-analyzer/SKILL.md` | ✅ | | | | ✅ | | ✅ | |
| `skills/test-point-integrator/SKILL.md` | ✅ | | | | | ✅ | ✅ | |
| `skills/design-planner/SKILL.md` | ✅ | | | | | ✅ | | |
| `docs/ptm-tde/gate-spec.md` | | ✅ | | | | | | |
| `skills/checkpoint-manager/SKILL.md` | | ✅ | | | | | | |
| `docs/ptm-tde/skill-references.md` | | | | | | | ✅ | |
| `skills/README.md` | | | | | | | ✅ | |
| `process/changes/CR-INDEX.yaml` | | | | | | | | ✅ |
| `process/STATE.md` | | | | | | | | ✅ |
| `agents/ptm-tde.md` | | | | | | | | ✅ |
| `process/changes/CR-012-ptm-tde-mfq-phase.md` | | | | | | | | ✅ |

**结论**：0 文件冲突。`skills/m-analyzer/SKILL.md` 被 3 个 Story 修改，通过 Wave 顺序隔离（A→B→D）。`skills/test-point-integrator/SKILL.md` 同理（A→D→D）。

---

## Clarification Queue（6 项，均不阻断 LLD）

| ID | Story | 问题 | 推荐方案 | blocks_lld |
|----|-------|------|---------|:---:|
| LCQ-03-01 | 012-03 | 覆盖矩阵视角 A/B 一致性检查：手动 vs 脚本 | 方案 A：手动校验（CP7 不一致率高时引入脚本） | false |
| LCQ-03-02 | 012-03 | 因子库搜索路径：三层回退 vs 单一 | 方案 A：沿用三层回退（CR-013 统一时同步） | false |
| LCQ-04-01 | 012-04 | `object_role_in_coupling` 枚举约束 | 方案 A：枚举（触发方/受影响方/共享资源） | false |
| LCQ-04-02 | 012-04 | F 线索指向不存在 TSP 的处理 | 方案 A：记录 gap + 警告不阻断 | false |
| LCQ-05-01 | 012-05 | `generation_basis` 枚举范围 | 方案 A：保持 3 类（行业标准/经验推断/需求推断） | false |
| LCQ-05-02 | 012-05 | OPEN 标记项汇总确认策略 | 方案 A：单次展示等待确认 | false |

> 所有 LCQ 均不阻断 LLD，可在 CP5 人工确认后、实施阶段按推荐方案处理。

---

## 待人工决策清单

| 决策 ID | 类型 | 待确认问题 | 推荐方案 | 备选方案 | 影响 |
|---|---|---|---|---|---|
| **CP5-DQ-01** | implementation | 是否批准全部 8 Story LLD 作为实现输入 | **approve 全部** | 修改 / 仅批准 Wave A+B（前 3 Story） | 全部 5 Skill + 3 文档进入实施 |
| CP5-DQ-02 | risk_acceptance | 6 项 LCQ 均按推荐方案处理 | 接受全部推荐方案 | 逐项调整 | LLD 中已标注推荐方案，CP7 验证时确认 |
| CP5-DQ-03 | risk_acceptance | `skills/m-analyzer/SKILL.md` 被 3 个 Story 修改，Wave B→D 串行风险 | 按 Wave 顺序实施，每 Wave 完成后验证再推进 | 合并为一个 Story | 实施周期可能延长，但文件冲突风险为零 |

### 推荐 / 备选优劣

**CP5-DQ-01**：
- 推荐（全部批准）：✅ 8 Story 全部 CP5 PASS ✅ LLD 14 章节完整 ✅ 0 文件冲突；⚠️ 8 Story 实施需 4 轮 Wave
- 备选（仅 Wave A+B）：✅ 先交付路径迁移和 M 分析器；❌ F/Q 分析器落后于 M，适配 Story 无法启动

**CP5-DQ-02**：
- 推荐（接受全部）：✅ 所有 LCQ 已有明确推荐方案；⚠️ 实施中如发现推荐方案不可行需回到 LLD
- 备选（逐项调整）：✅ 更精确控制；❌ 延迟实施

**CP5-DQ-03**：
- 推荐（按 Wave 实施）：✅ 零文件冲突 ✅ 每 Wave 独立可验证；⚠️ 实施周期较长
- 备选（合并）：❌ 3 个 Story 合并会导致 ~230 行改动集中在一个文件中，review 负担大

### 不授权项

> ⚠️ 本确认不代表授权：
> - PPDCS 阶段任何修改（CR-013 范围）
> - Python 脚本或 MCP 服务开发
> - 公共因子库内容写入
> - KYM 阶段 Skill 修改

### 后续 CR 候选

| ID | 内容 | 状态 |
|----|------|------|
| T-03 | 覆盖矩阵自动化校验脚本（LCQ-03-01 触发条件满足时） | candidate |
| T-04 | 因子库搜索路径统一管理（LCQ-03-02 留待 CR-013） | candidate |

---

## 回复选项

| 回复 | 含义 |
|------|------|
| **`approve`** | 批准全部 8 Story LLD，接受全部 6 项 LCQ 推荐方案，进入 story-execution（Wave A 启动） |
| **`修改: <决策ID>=<修改点>`** | 逐项调整 |
| **`reject`** | 不通过，需重新设计 |

> 📂 LLD 文件：`process/stories/STORY-012-0*-LLD.md`（8 个）
> 📂 CP5 预检：`process/checks/CP5-STORY-012-0*-IMPLEMENTABILITY.md`（8 个）
> 📂 人工审查稿：本文件
