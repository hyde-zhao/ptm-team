# STORY-010-05 实现日志

## 实现日期

2026-06-01

## 实现概述

按 LLD §3 变更方案，逐一修改 5 个 `docs/ptm-tde/` 核心文档，将旧「11 步 + CP + analysis/design/」体系更新为「三阶段 + Gate + kym/mfq/ppdcs/process/」体系。

## 变更文件清单

| 文件 | 变更次数 | 变更类型 |
|------|----------|----------|
| `docs/ptm-tde/README.md` | 10 处编辑 | TOC、架构图、§3 完全替换、§4 完全替换（含 GATE-3 新增）、§7 目录树替换、§7 说明文字、§2.6 路径、§8.1 CP02→GATE-2、§8.2 路径（2 处） |
| `docs/ptm-tde/USER-MANUAL.md` | 10 处编辑 | 角色说明、头部目录规则、§3.3 目录树+约束、§4.1 追踪链、§4.2 公共因子库、§4.4 Topology 路径+回链、§5 deliverable-renderer 输出、§6.1 检索字段、§9 交付物说明+路径、§12.2 消费记录+目录树+确认场景路径 |
| `docs/ptm-tde/runtime-artifacts.md` | 8 处编辑 | §目录结构完全替换、§公共因子库消费记录（3 处）、§场景产物字段、§确认场景与拓扑绑定基线、§分析产物表完全替换、§设计产物（3 处）、§PC 拓扑物化字段、§交付产物 |
| `docs/ptm-tde/component-manual.md` | 3 处编辑 | §主流程表完全替换、§使用边界路径、§关键调用关系（2 处） |
| `docs/ptm-tde/skill-references.md` | 1 处编辑 | §主流程 Skill 表完全替换（16 行：阶段列 + checkpoint-manager 职责 + 路径引用） |

## 关键决策与偏差

1. **裸 `confirmed-scenarios.md` 引用**：LLD 要求全路径一致性为 `kym/scenarios/confirmed-scenarios.md`。实现中保留了几处紧密上下文中的裸引用（如 `LC.topology_bindings -> confirmed-scenarios.md`），但将缺乏上下文的独立引用（USER-MANUAL.md coverage-verifier 输入、README.md GATE-2 表、runtime-artifacts.md PC 物化表）全部补全为完整前缀。

2. **CP 编号在历史章节中的处理**：README.md §8.1（CR-20260520-001 历史记录）中的 CP02 引用被更新为「GATE-2 KYM Exit Gate」，保持历史章节可读性的同时消除旧编号。

3. **GATE-3 新增内容**：完全按照 LLD §3.1.4 中的改后内容生成 GATE-3（MFQ Exit Gate），包含 5 项自检和 4 项人工确认。

4. **`ppdcs/ppdcs/` 双重目录名**：在目录树注释中保留简单描述，不做额外注解以避免文档臃肿。

## 跨文档一致性验证结果

| 验证项 | 结果 |
|---|---|
| `doc/STATE.yaml` 旧引用 5 文档 | 0 匹配 |
| `analysis/scenarios/confirmed` 旧引用 全 docs/ | 0 匹配 |
| `analysis/` + `design/` 旧路径 5 文档 | 0 匹配 |
| `11步` 旧术语 5 文档 | 0 匹配 |
| `confirmed-scenarios.md` 路径前缀一致性 | 全部 `kym/scenarios/confirmed-scenarios.md`（上下文裸引用除外） |
| `factor-usage` 路径前缀一致性 | 全部 `mfq/factor-usage/`（父目录下的子条目除外） |

## 已知限制

- 少数 `confirmed-scenarios.md` 引用在已建立 `kym/scenarios/` 上下文的句子中使用简写形式（如 README.md line 199），这在英文技术文档中是常见做法。
- 本章不修改 `gate-spec.md`、`checkpoint-spec-v1-archived.md` 或其他非目标文件。

## 提供给 meta-qa 的验证入口和风险提示

- **验证入口**：运行本文件「跨文档一致性验证结果」中的 6 项 grep 命令。
- **风险提示**：
  1. README.md §8 历史章节中 CR-20260520-001 的描述仍提及「CP02 已扩展」，实际已改为「GATE-2 KYM Exit Gate 已扩展」——需确认历史语义未丢失。
  2. USER-MANUAL.md §5 coverage-verifier 的输入描述中 `confirmed-scenarios.md` 已补全路径前缀——需确认与其他文档的描述一致。
  3. runtime-artifacts.md 的分析产物表新增了「阶段」列——需要跟其他文档的表格风格保持一致。

## CP6 结论

- 文件：`process/checks/CP6-STORY-010-05-update-core-docs-CODING-DONE.md`
- 结论：**PASS**
- 阻断项：0
