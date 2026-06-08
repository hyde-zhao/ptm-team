---
checkpoint: CP6
cr_id: CR-015-ptm-tde-ask-user-question-interaction
workflow_mode: fast-lane
created_at: "2026-06-04"
status: PASS
---

# CP6-CR-015 — AskUserQuestion 编码完成检查

## Entry Criteria

| 条目 | 状态 |
|------|:----:|
| CR 文档已创建 | ✅ `process/changes/CR-015-ptm-tde-ask-user-question-interaction.md` |
| 实施计划已批准 | ✅ 用户 approve |

## Checklist

| # | 检查项 | 状态 | 证据 |
|---|--------|:----:|------|
| 1 | `agents/ptm-tde.md` 新增用户交互层小节 | ✅ | L336-L376：决策树 + 参数约束 + Gate 映射 + STOP-05 关系 |
| 2 | `test-point-integrator/SKILL.md` 步骤 4.5.3 追加 AskUserQuestion | ✅ | 4 选项单选，label 对应 Confirm all / Item by item / Batch modify / Reject all |
| 3 | `f-analyzer/SKILL.md` 步骤 5 追加 AskUserQuestion | ✅ | 3 选项单选，label 对应 Confirm all / Partial / Reject all |
| 4 | `f-analyzer/SKILL.md` 步骤 8 追加 AskUserQuestion | ✅ | 2 选项单选，label 对应 Write back / Skip |
| 5 | `q-analyzer/SKILL.md` 步骤 1 末尾追加 AskUserQuestion | ✅ | 4 选项单选，label 对应 Accept all / Skip all / Item by item / Defer |
| 6 | `design-planner/SKILL.md` 步骤 5 升级为规范 AskUserQuestion | ✅ | 3 选项单选，label 对应 Confirm all / Modify method / Merge/split |
| 7 | `kym/SKILL.md` 阶段一追加 AskUserQuestion | ✅ | 3 选项单选（Early req / Mid dev / Late test） |
| 8 | `kym/SKILL.md` 阶段三追加交互模式选择 + 选项拆分规则 | ✅ | 决策树 + C-Customers/S-Schedule/D-Deliverables 拆分策略 |
| 9 | `kym/SKILL.md` 阶段四追加 AskUserQuestion | ✅ | 3 选项 Gate 映射（Approve / Modify / Reject） |
| 10 | `checkpoint-manager/SKILL.md` 追加 STOP-06 + 人工确认交互方式 | ✅ | STOP-06 降级规则 + GATE-2/3/4 AskUserQuestion 模板 |

## 回退基线验证

| # | 检查项 | 状态 |
|---|--------|:----:|
| R1 | 所有交互点保留 STOP-05 文本回退 | ✅ |
| R2 | "若 AskUserQuestion 不可用" 回退提示存在 | ✅ |
| R3 | HARD-STOP 协议语义保持不变 | ✅ |

## Exit Criteria

| 条目 | 状态 |
|------|:----:|
| 7 个产品文件全部修改 | ✅ PASS |
| 每个交互点含 AskUserQuestion 优先 + 文本回退 | ✅ PASS |
| 无破坏原有逻辑 | ✅ PASS |

## 结论

**PASS** — 10/10 检查项通过，3/3 回退验证通过。进入 CP7 验证。
