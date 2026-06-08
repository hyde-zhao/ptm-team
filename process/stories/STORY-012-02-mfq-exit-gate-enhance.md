---
story_id: STORY-012-02
story_name: MFQ Exit Gate 增强（编号规范化 + HARD-STOP 机制）
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: S
wave: A
depends_on: []
blocks: []
status: ready-for-verification
file_ownership:
  - docs/ptm-tde/gate-spec.md
  - skills/checkpoint-manager/SKILL.md
parallel_safe: true
---

# STORY-012-02：MFQ Exit Gate 增强（编号规范化 + HARD-STOP 机制）

## 1. 目标

将 `gate-spec.md` 和 `checkpoint-manager/SKILL.md` 中 GATE-3 MFQ Exit Gate 的 Checklist 自检项编号统一为 M1-M7 + W1-W2 前缀，注入 HLD §11 定义的 STOP-01~05 执行协议硬停止规则，并增加人工确认项的 `⛔ HARD-STOP` 标记。

## 2. 范围

- **修改文件**：2 个
- **改动量**：~30 行（编号重命名 + HARD-STOP 标记新增）
- **不改动**：GATE-1/GATE-2/GATE-4/GATE-5 的内容、checkpoint-manager 的检查执行框架代码

## 3. 验收标准

- [ ] **AC01**：`grep -c "M[1-7]\|W[1-2]" docs/ptm-tde/gate-spec.md` 输出 >= 9（M1-M7 共 7 行 + W1-W2 共 2 行）
- [ ] **AC02**：`grep -c "M[1-7]\|W[1-2]" skills/checkpoint-manager/SKILL.md` 输出 >= 9
- [ ] **AC03**：`grep "⛔ HARD-STOP" docs/ptm-tde/gate-spec.md` 存在且位于 GATE-3 人工确认项章节
- [ ] **AC04**：`grep "⛔ HARD-STOP" skills/checkpoint-manager/SKILL.md` 存在且位于 GATE-3 人工确认项章节
- [ ] **AC05**：gate-spec.md GATE-3 的 Checklist 表中 `#` 列不再使用纯数字（1-8），全部使用 M1-M7 + W1-W2 前缀
- [ ] **AC06**：gate-spec.md GATE-3 的「上下游 Warning」表 `#` 列使用 W1-W2 前缀（与 Checklist 区分）
- [ ] **AC07**：checkpoint-manager SKILL.md GATE-3 的「Checklist 概要」表和「上下游 Warning」表编号与 gate-spec.md 完全一致
- [ ] **AC08**：grep `STOP-0[1-5]` 在 gate-spec.md 和 checkpoint-manager SKILL.md 中至少出现于 GATE-3 相关章节（或 GATE-3 引用遵守 STOP 协议）

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `docs/ptm-tde/gate-spec.md` | 修改 | GATE-3 章节：Checklist #1-8 → M1-M7；上下游 Warning → W1-W2；人工确认项增加 HARD-STOP 标记；末尾增加「执行协议引用」（引用 HLD §11 STOP-01 ~ STOP-05） |
| `skills/checkpoint-manager/SKILL.md` | 修改 | GATE-3 章节：Checklist 概要 #1-8 → M1-M7；上下游 Warning → W1-W2；人工确认项增加 HARD-STOP 标记；末尾增加「执行协议引用」 |

### 编号映射

| 旧编号 | 新编号 | 检查项内容 |
|--------|--------|----------|
| #1 | M1 | M 分析输出完整 |
| #2 | M2 | F 分析输出完整 |
| #3 | M3 | Q 分析输出完整 |
| #4 | M4 | 测试点整合完整 |
| #5 | M5 | LC topology_bindings 一致 |
| #6 | M6 | 设计计划存在 |
| #7 | M7 | 公共因子库 lock 有效 |
| #8 | 合并到 M5 | plan 存在性和格式（与 M6 合并） |
| W1 | W1 | KYM 场景下游可消费（不变） |
| W2 | W2 | PPDCS 可消费 plan（不变） |

## 5. 依赖关系

- **上游**：无（Wave A 并行）
- **下游**：无（Gate 增强被所有后续 Story 间接使用，但无直接文件依赖）

## 6. 实施注意事项

- **HARD-STOP 标记位置**：在 gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3「人工确认项」章节中，每个确认项的描述前增加 `⛔ HARD-STOP：禁止 Agent 自行判定通过。必须等待用户回复 approve/修改/reject。`
- **STOP-01~05 引用方式**：在 GATE-3 章节末尾增加 `### 执行协议` 小节，列出 STOP-01~05 规则摘要（从 HLD §11 复制），而非在每个 Checklist 项中重复。引用原文：
  - STOP-01：GATE-3 人工确认禁止自答
  - STOP-02：候选汇总确认禁止自行判定
  - STOP-03：禁止绕过 Skill 直接生成产物
  - STOP-04：路径写入前必须校验父目录
  - STOP-05：确认选项必须使用 `( )` / `[ ]` / `>>>` 标记
- **双向同步**：gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3 内容必须逐项一致。先修改 gate-spec.md（作为真相源），再将改动同步到 checkpoint-manager。
- **不要改动其他 Gate**：只修改 GATE-3 章节。GATE-1/GATE-2 的编号体系（#1-N）保持不变。
- **修订记录**：在 gate-spec.md 头部修订记录追加一行 `v1.4 | 2026-06-02 | meta-dev | [CR-012] GATE-3 Checklist 编号统一为 M1-M7+W1-W2，增加人工确认 HARD-STOP 标记和 STOP-01~05 执行协议引用`
- **并行安全**：本 Story 与 STORY-012-01 无文件冲突，可并行执行。
