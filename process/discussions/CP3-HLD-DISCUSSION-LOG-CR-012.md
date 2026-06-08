# CP3 HLD 讨论日志 — CR-012 MFQ 阶段改造

> 状态：完成
> 恢复点：`process/checks/CP3-DISCUSSION-CHECKPOINT-CR-012.json`

---

## Round 1：架构灰区讨论（2026-06-02）

### AGA-01：候选汇总的实现方式

**讨论**：设计文档 §6.2 定义了候选汇总流程，需要确定是新建独立 Skill 还是内嵌到现有 Skill。

**Advisor 意见**：
- lane-architecture：候选汇总 ≤50 行，与测试点归集天然关联，推荐内嵌到 test-point-integrator
- lane-product：减少 Skill 数量降低用户认知负担，推荐内嵌

**决定**：内嵌到 test-point-integrator（方案 B）。触发独立 Skill 的条件：候选汇总逻辑 >50 行。

### AGA-02：M/F/Q 分析器重写策略

**讨论**：设计文档 v3.0 提供了逐步骤处理逻辑，需要决定是全量替换现有 SKILL.md 还是增量追加。

**Advisor 意见**：
- lane-architecture：全量重写保证方法论一致性，避免新旧混杂
- lane-quality：增量追加有新旧矛盾风险，长期维护成本高

**决定**：全量重写（方案 A）。前提：设计文档 v3.0 已覆盖旧版全部功能点。

### AGA-03：覆盖矩阵的存储格式

**决定**：独立 Markdown 文件 `mfq/m-analysis/scenario-tsp-coverage.md`。与现有产出格式一致，人类可读。

### AGA-04：步骤标签的传递方式

**决定**：嵌入覆盖矩阵末尾的 F/Q 线索汇总表。单一文件减少碎片。

### AGA-05：GATE-3 硬停止机制（v1.1 新增）

**讨论**：上一阶段测试发现 Agent 会在 GATE-2 自行放行（问题 #1）、kym Skill 自问自答（问题 #2）、目录漂移（问题 #5）。这些问题对 GATE-3 MFQ Exit Gate 同样适用。

**Advisor 意见**：
- lane-architecture：纯文档约束不足以阻止 AGI Agent，需要 checkpoint-manager 自检脚本增加人工确认回填校验
- lane-quality：双重防御 — SKILL.md 中的 ⛔ HARD-STOP 标记（文档层）+ 脚本校验人工确认回填（执行层）

**决定**：方案 A。在 gate-spec.md 和 checkpoint-manager SKILL.md 的 GATE-3 人工确认项中标注 `⛔ HARD-STOP`；在 checkpoint-manager 自检脚本中增加人工确认回填校验。新增执行协议 STOP-01~05。

**影响面**：
- §11 新增「执行协议：硬停止规则」小节（STOP-01~05）
- §12 NFR 新增「安全性：路径写入前置校验」和「门控强制」两个维度
- §13 新增 R5（HARD-STOP 被 Agent 忽略的风险）
- §14 新增 ADR-012-05（GATE-3 HARD-STOP 机制）

---

## Round 2：用户确认（CP3 人工门控）

待用户确认：
- Q1：候选汇总内嵌到 test-point-integrator
- Q2：全量重写策略
- Q3：F/Q 分析器步骤数（F=9步, Q=6步）

---

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.0 | 2026-06-02 | meta-po（代 hld-designer） | 初始讨论日志，覆盖 4 个 AGA 全部决议 |
| 1.1 | 2026-06-02 | meta-po（代 hld-designer） | 新增 AGA-05（GATE-3 硬停止机制），讨论日志补充 Round 1 AGA-05 决议和 Round 2 影响面 |
