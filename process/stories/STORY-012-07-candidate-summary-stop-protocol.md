---
story_id: STORY-012-07
story_name: 候选汇总 + skill-references 更新 + STOP 协议落地
workflow_id: WF-PTM-TEAM-20260520-001
change_id: CR-012-ptm-tde-mfq-phase
tier: M
wave: D
depends_on: [STORY-012-06]
blocks: [STORY-012-08]
status: ready-for-verification
file_ownership:
  - skills/test-point-integrator/SKILL.md
  - skills/README.md
  - docs/ptm-tde/skill-references.md
parallel_safe: false
---

# STORY-012-07：候选汇总 + skill-references 更新 + STOP 协议落地

## 1. 目标

在 `test-point-integrator` 中内嵌候选汇总与用户批量确认功能（设计文档 §6），更新 `skill-references.md` 反映 MFQ 阶段 v3.0 的 Skill 能力变化，并将 HLD §11 的 STOP-01~05 执行协议落地到 MFQ 阶段各 Skill 的操作章节中。

## 2. 范围

- **修改文件**：3 个
- **改动量**：~50 行（候选汇总 ~30 行 + skill-references ~10 行 + STOP-01~05 引用 ~10 行）
- **新建文件**：0 个（候选汇总不独立建 Skill）

### 候选汇总功能（内嵌到 test-point-integrator）

| 功能点 | 说明 |
|--------|------|
| 三源候选归集 | 从 M/F/Q 分析器产出的候选列表（`mfq/m-analysis/candidate-*.yaml`、`mfq/f-analysis/` 耦合因子候选、`mfq/q-analysis/` 质量因子候选）汇总 |
| 去重合并 | 以 factor_id / candidate_op_name 为 key，合并同 key 的多源候选，标注多来源 |
| 优先级判定 | 高（M 分析高关联度对象）/ 中（F 分析关键耦合或 Q 分析强相关维度）/ 低（中关联度或弱相关维度） |
| 用户批量确认 | 展示因子候选汇总表 + 原子操作候选汇总表，使用 STOP-05 的 `( )` 单选标记选项；禁止自行判定 |
| 确认后回写 | 确认的候选因子→因子库候选；确认的原子操作→待开发清单；丢弃的候选→记录在候选汇总表保留决定 |

### 确认选项格式（STOP-05 落地）

```markdown
选项：
( ) 全部确认 — 所有候选转为已确认
( ) 逐项确认 — 逐项标记确认/拒绝/修改
( ) 批量修改 — 提供修改意见，统一调整后确认
( ) 全部拒绝 — 所有候选丢弃
```

### skill-references 更新

在 `docs/ptm-tde/skill-references.md` 中：
1. MFQ 阶段的 m-analyzer / f-analyzer / q-analyzer 的职责描述更新为 v3.0 版本
2. test-point-integrator 的职责描述增加「候选汇总与用户确认」
3. 新增「候选汇总」说明段落，描述 output 路径 `mfq/candidates/`

## 3. 验收标准

- [ ] **AC01**：`skills/test-point-integrator/SKILL.md` 包含「候选汇总」或「candidate.*汇总」或「candidate.*summary」章节
- [ ] **AC02**：候选汇总章节包含去重合并逻辑描述（`去重` 或 `dedup` 或 `合并.*factor_id`）
- [ ] **AC03**：候选汇总章节包含用户确认选项（至少 2 个可选选项，使用 `( )` 单选标记）
- [ ] **AC04**：`docs/ptm-tde/skill-references.md` 中 m-analyzer 描述包含 `v3.0` 或 `场景步骤驱动` 或 `覆盖矩阵`
- [ ] **AC05**：`docs/ptm-tde/skill-references.md` 中 test-point-integrator 描述包含 `候选汇总` 或 `candidate`
- [ ] **AC06**：`docs/ptm-tde/skill-references.md` 包含 `mfq/candidates/` 路径引用
- [ ] **AC07**：`grep -rn "STOP-0[1-5]" skills/m-analyzer/SKILL.md skills/f-analyzer/SKILL.md skills/q-analyzer/SKILL.md skills/test-point-integrator/SKILL.md skills/design-planner/SKILL.md` 返回 > 0 或各 Skill 有等价的行为约束描述
- [ ] **AC08**：`grep "⛔ HARD-STOP\|HARD.STOP\|禁止.*自行" skills/test-point-integrator/SKILL.md` 返回 > 0（候选汇总确认步骤中）

## 4. 文件清单

| 文件 | 变更类型 | 改动说明 |
|------|----------|----------|
| `skills/test-point-integrator/SKILL.md` | 修改 | 在 LC 生成步骤之后新增「候选汇总与用户确认」步骤。内容：三源去重合并 → 优先级判定 → 用户批量确认交互 → 确认后回写。贯穿 STOP-02（禁止自行判定候选全部确认）和 STOP-05（选项视觉区分） |
| `docs/ptm-tde/skill-references.md` | 修改 | MFQ 阶段 m-analyzer/f-analyzer/q-analyzer 职责描述更新为 v3.0；test-point-integrator 增加候选汇总职责；新增 `mfq/candidates/` 路径说明段落 |
| `skills/README.md` | 检查 | 确认 MFQ 阶段 Skill 注册表无变化（无新增 Skill），无需修改 |

## 5. 依赖关系

- **上游**：STORY-012-06（test-point-integrator 已适配，消费 M/F/Q 候选列表）
- **下游**：STORY-012-08（文档更新需引用 skill-references 的最新状态）

## 6. 实施注意事项

### 候选汇总内嵌边界
- 候选汇总作为 test-point-integrator 的一个独立步骤（在 LC 生成之后，输出产物之前），不作为独立 Skill
- 如果 M/F/Q 分析尚未完成（对应候选列表文件不存在），跳过候选汇总步骤，不阻断 LC 生成
- 候选汇总失败（如候选列表格式不一致）降级为 Warning，不影响 test-point-integrator 的主流程

### STOP 协议落地清单
检查 MFQ 阶段各 Skill 是否已包含对应 STOP 规则：
- STOP-01（GATE-3 硬停止）：由 STORY-012-02 在 gate-spec.md 中实现，本 Story 在各 Skill 的「完成」步骤中引用「通过 GATE-3 人工确认后方可进入 PPDCS 阶段」
- STOP-02（候选确认硬停止）：本 Story 在 test-point-integrator 候选汇总步骤中实现
- STOP-03（禁止绕过 Skill）：各 Skill 的前置条件中强化「必须通过本 Skill 调用执行，不得直接生成产物」
- STOP-04（路径写入校验）：各 Skill 的写入步骤中增加「校验目标父目录存在且为目录」
- STOP-05（选项视觉区分）：本 Story 在候选汇总确认界面中实现 `( )` 单选标记

### skill-references 更新要点
- 不新增 Skill 行，只更新现有 MFQ 阶段 Skill 的职责描述
- m-analyzer 描述更新示例：`执行 M 分析 v3.0（场景步骤驱动）：逐场景步骤发现测试对象/因子/原子操作，产出 TSP + Scenario-TSP 覆盖矩阵 + 场景步骤标签 + CAE 测试点 + 候选列表`
- 新增「MFQ 候选汇总」段落：
  ```markdown
  ### MFQ 候选汇总
  test-point-integrator 在整合 M/F/Q 测试点后，将三源候选列表去重合并，
  提交给用户批量确认。确认后的候选因子和原子操作存放在 `mfq/candidates/` 目录。
  ```
