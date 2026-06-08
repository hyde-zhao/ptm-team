---
change_id: CR-017-factor-library-discovery-gap
workflow_id: WF-PTM-TEAM-20260520-001
created_at: "2026-06-05T00:00:00+08:00"
created_by: meta-po（po-zhao）
status: closed
approved_at: "2026-06-06T00:00:00+08:00"
closed_at: "2026-06-06T00:00:00+08:00"
impact_level: medium
complexity: standard
rollback_to: story-planning
approval_source: user-request
depends_on:
  - CR-011 (closed, committed)
  - CR-015 (closed, committed)
commits:
  - "befeeb3: 初始实现（3 文件 +113/-13）"
cp3_approved: "2026-06-06 (CP3-DQ-01/02/03 all approved)"
cp5_approved: "2026-06-06 (CP5-DQ-01 approved)"
cp6: "process/checks/CP6-STORY-017-01-factor-library-discovery-CODING-DONE.md (10/10 PASS)"
cp7: "process/checks/CP7-CR-017-global-VERIFICATION-DONE.md (18/18 PASS)"
cross_references:
  - CR-016-atomic-ops-consumption-gap (同类问题，共享 Step 1.5 资源发现设计模式。CR-017 先启动，CR-016 在此基础上追加 atomic-ops 发现)
---

# CR-017 — m-analyzer 因子库发现缺口修复

## 变更请求摘要

m-analyzer 的因子库消费契约声明"提取测试因子前必须读取公共库"，但实际只扫描了 9 个已安装库中的 **2 个**（`ngfw-policy-routing` + `ngfw-interface`），漏掉其余 7 个。导致 35 个候选因子中有 **18 个与已有库重复**：

| 候选 | 期望目标库 | 实际已有因子 |
|------|-----------|------------|
| FAC-CAND-001, 003 | `ngfw-ipv4-route` | FAC-RT-NEXT-HOP, FAC-L3-FAIL-DETECT-METHOD |
| FAC-CAND-005, 015 | `ngfw-interface` / `ngfw-ipv4-route` | FAC-L3-OUTIF-TYPE, FAC-L3-NH-IF-TYPE |
| FAC-CAND-009-012 | `ngfw-dfx` | FAC-DFX-CAPACITY-*, FAC-COUNTER-*, FAC-LOG-* |
| FAC-CAND-002 | `ngfw-load-balance` | FAC-LB-INTERFACE-WEIGHT |

## 背景与根因

### 四层根因分析

1. **无库发现机制**（规范层）：m-analyzer SKILL.md 全文零次提到 `index.yaml`。Agent 被指向 `resource/factor-libraries/` 目录，但从未被告知要读取这个文件来发现有哪些库
2. **lock 文件缺失无回退流程**（架构层）：契约说"读取 `factor-library-lock.yaml` 或从公共 resource 目录选择库"，但"选择库"三个字无任何定义——选几个？选哪些？按什么标准？
3. **子目录枚举缺失**（实现层）：查找路径指向 `factor-libraries/` 目录而非具体文件，但未指令遍历所有子目录加载 `factor-library.yaml`
4. **`candidate` 状态因子被隐性排除**（语义层）：匹配规则只有"命中 `active` 因子时复用"。8 个库共 115 个因子均为 `candidate` 状态，按字面规则即使扫描了也不会命中

### 与 CR-016 的同源性

两个 CR 是同一根因的平行表现：

```
m-analyzer 消费表声明"消费 X"，但未提供发现/查询 X 的机制
    ├── X = 公共因子库 → 9 个库只扫了 2 个（CR-017）
    └── X = atomic-ops  → 74 个 op 一个都没查（CR-016）
```

修复模式一致：在现有 Step 2 之前增加「资源清单加载」步骤（Step 1.5），构建内存索引，再在 Step 2 的子步骤中进行语义匹配。

### 关键发现

- `resource/component-resource-links.yaml` 明确写了 `library_id: all`、`install_policy: required`，意图是全量消费所有 9 个库
- `resource/factor-libraries/README.md` 第 147 行描述了正确的初始化流程："读取 `index.yaml` 和目标库主文件，生成 lock 文件"，但 m-analyzer 从未被要求执行此步骤
- `factor-libraries/README.md` 第 212 行明确说 `candidate` 状态"可用于分析草稿"，说明候选库不应当被跳过
- GATE-3 审查时看到"扫描 2 个库，命中率 52%"未触发追问，编排器层面也缺少"因子库扫描完整性"自检项

## atomic-ops CLI 前置依赖

**本 CR 无外部依赖**。因子库是本地静态 YAML 文件，`index.yaml` 和各库的 `factor-library.yaml` 均已就位。CR-017 可立即启动，不等待任何外部改动。

## 五维度影响分析

### 1. 需求影响

| 维度 | 影响 |
|------|------|
| 现有需求 | 不变。m-analyzer 的功能定位不变 |
| 新增需求 | 隐式新增：m-analyzer 须能发现并遍历全部已注册因子库 |
| 需求冲突 | 无 |

### 2. 设计影响

| 维度 | 影响 |
|------|------|
| 架构决策 | 新增 Step 1.5（资源清单加载），与 CR-016 共享设计模式。candidate 状态因子允许匹配但标记 `match_confidence=medium` |
| HLD 影响 | 不改变 HLD（M/F/Q 分析的职责边界不变） |
| ADR 影响 | 新增设计决策：candidate 状态因子的复用策略（可匹配但降低置信度，下游需显式确认） |

### 3. Story/实现影响

| 维度 | 影响 |
|------|------|
| 受影响文件 | 3 个（详见下方） |
| Story 拆解 | 1 Story（M tier），1 Wave。修改集中在 m-analyzer SKILL.md，test-point-integrator 和 gate-spec 小改 |
| 实现复杂度 | 低。核心改动是在 SKILL.md 中增加库发现和遍历指令，不涉及算法设计 |

### 4. 安全/权限影响

| 维度 | 影响 |
|------|------|
| 文件读取 | 新增读取 `index.yaml` 和各库 `factor-library.yaml`，均为本地只读操作 |
| 目录创建 | 可能写入 `mfq/factor-usage/factor-library-lock.yaml`（如不存在），与现有 mfq/ 权限一致 |
| 风险 | 零。纯本地文件 I/O |

### 5. 交付影响

| 维度 | 影响 |
|------|------|
| 安装器 | 不变 |
| 文档 | 更新 gate-spec.md（GATE-3 新增因子库扫描完整性检查项） |
| 向后兼容 | 完全兼容。新逻辑是对旧逻辑的超集（多扫 7 个库），不会产生新问题 |

## 修改文件清单

| 优先级 | 文件 | 变更范围 | 预计行数 |
|--------|------|---------|:---:|
| P0 | `skills/m-analyzer/SKILL.md` | 新增 Step 1.5 因子库发现 + 修改 Step 2B（candidate 状态可匹配）+ 修改消费表 + Gotchas/验收标准更新 | ~60 行 |
| P1 | `skills/test-point-integrator/SKILL.md` | GATE-3 候选因子交叉验证：去重后回查全部公共库做反查 + Gotchas 更新 | ~25 行 |
| P2 | `docs/ptm-tde/gate-spec.md` | GATE-3 新增检查项：因子库扫描完整性（扫描库数 = 已安装库数） | ~8 行 |

### 文档处理决策

| 受影响文档 | 决策 | 说明 |
|-----------|------|------|
| `skills/m-analyzer/SKILL.md` | 原文档增量更新 | 保留现有 v3.0 结构，在 Step 1 和 Step 2 之间插入 Step 1.5，修改 Step 2B 匹配规则 |
| `skills/test-point-integrator/SKILL.md` | 原文档增量更新 | Step 7.5 候选汇总中增加因子库反查子步骤 |
| `docs/ptm-tde/gate-spec.md` | 原文档增量更新 | GATE-3 checklist 追加一项 |

## 复杂度判定

**判定：standard**（与 CR-016 相同级别）。

不满足 fast-lane 条件：
- 涉及 3 个产品文件
- 引入新机制（库发现遍历 + candidate 状态因子匹配 + 置信度分级）
- 跨 Skill 协调（m-analyzer + test-point-integrator）
- 修改 gate-spec.md（GATE-3 检查项）

## 文件所有权冲突分析

| CR | 状态 | 与 CR-017 重叠文件 |
|----|------|-------------------|
| CR-011 | closed，待 CP8 人工终验 + commit | `docs/ptm-tde/gate-spec.md` |
| CR-015 | active，fast-lane，待 CP8 人工终验 + commit | `skills/test-point-integrator/SKILL.md` |
| CR-016 | draft，待 atomic-ops P0+P1 + CP8 终验 | 无直接重叠（CR-016 改 m-analyzer Step 2C，CR-017 改 Step 1.5 + 2B） |

CR-016 和 CR-017 修改同一文件（`skills/m-analyzer/SKILL.md`）但**修改不同区域**：
- CR-016：Step 2C（原子操作支撑检查）+ Pre-2C（atomic-ops 清单加载）
- CR-017：Step 1.5（因子库发现）+ Step 2B（candidate 状态匹配规则）

建议实施顺序：**CR-017 先 → CR-016 后**。CR-017 建立的 Step 1.5 资源发现模式恰好是 CR-016 atomic-ops 发现步骤的前半部分（因子库发现）。CR-016 在 Step 1.5 中追加 atomic-ops 发现即可。

**推荐策略**：先完成 CR-011 + CR-015 CP8 终验和 commit，再依次推进 CR-017 → CR-016。

## 执行时间线

| 步骤 | 动作 | 阻塞条件 |
|------|------|---------|
| 0 | 用户完成 CR-011 + CR-015 CP8 人工终验，commit 基线 | ⛔ CR-017 启动前提 |
| 1 | 启动 CR-017：Phase 2 HLD 设计（meta-se） | |
| 2 | HLD 通过后：Story 拆解（预计 1 Story）+ CP4 自动预检 | |
| 3 | LLD 设计 + CP5 自动预检 + 人工确认 | |
| 4 | 实施 + CP6 + CP7 | |
| 5 | CR-016 在此基础上追加 atomic-ops 发现（等 atomic-ops P0+P1 完成） | ⛔ 等待 atomic-ops |
| 6 | 交付文档更新 + CP8 | |

## 改进方案详述

### Step 1.5（新增）：因子库清单加载

在现有 Step 1（加载 KYM 输入）和 Step 2（逐场景步骤分析）之间插入：

```
【Step 1.5：因子库清单加载】

1. 读取库索引
   a. 读取 resource/factor-libraries/index.yaml → 获取全部已注册库的 library_id / status / path
   b. 确认 component-resource-links.yaml 声明 library_id=all（验证意图）

2. 遍历加载
   a. 对索引中的每个库（无论 status=active 还是 candidate）：
      - 进入子目录，加载 factor-library.yaml
      - 解析所有 factor（含 factor_id / factor_name / aliases / owner_object / factor_group / status）
   b. 构建内存索引：factor_id → {library_id, library_status, factor_status, factor_group, ...}

3. ⚠️ candidate 状态处理
   - library_status=candidate 的库：照常加载和匹配，标记 match_confidence=medium
   - factor_status=candidate 的因子：照常匹配，标记 match_confidence=medium
   - factor_status=active 的因子：正常匹配，标记 match_confidence=high
   - 区分逻辑：candidate 不是"跳过"，而是"可匹配但下游需确认"

4. 输出锁文件
   - 若 mfq/factor-usage/factor-library-lock.yaml 不存在 → 创建之，锁定当前库版本
   - 若已存在 → 校验一致性，不一致时输出 WARNING

5. 扫描完整性校验
   - 记录扫描库数 N_scanned，与 index.yaml 注册库数 N_registered 对比
   - N_scanned < N_registered → 硬错误，阻断后续匹配
```

### Step 2B（修改）：因子匹配规则更新

```
【子步骤 B：发现/匹配测试因子】（修改部分）

2. 在公共因子库中检索每个候选因子：
   查找顺序：已加载的内存索引（Step 1.5 构建）
   按 factor_id / factor_name / aliases / owner_object 检索
   - 命中 → 标记为"已有因子"（source=public-library），记录 match_confidence
     · factor_status=active → match_confidence=high，直接复用
     · factor_status=candidate → match_confidence=medium，复用但下游需确认
     · 如值域/样本/约束不足 → 记录扩展建议
   - 未命中 → 标记为"因子候选"（source=new-candidate），加入候选列表
```

---

## Decision Brief（CR intake）

### 待人工决策清单

| 决策 ID | 决策类型 | 待确认问题 | 推荐方案 | 备选方案 | 优劣摘要 | 影响 / 风险 |
|---|---|---|---|---|---|---|
| CR017-DQ-01 | scope | 是否批准启动 CR-017（standard 模式，3 文件，1 Story） | **approve**：批准启动。推荐先完成 CR-011 + CR-015 CP8 终验和 commit | 备选 A：基于当前 working tree 直接启动 / 备选 B：与 CR-016 合并为一个 CR | 推荐方案文件所有权清晰。备选 A 需处理 gate-spec.md 和 test-point-integrator 的未提交冲突。备选 B 引入 atomic-ops 外部依赖会阻塞因子库修复 | 推荐：等待成本低（两个 CP8 终验）。合并方案风险高（被 atomic-ops 阻塞） |
| CR017-DQ-02 | architecture | candidate 状态因子的复用策略 | **match_confidence 分级**：active→high，candidate→medium，均匹配但区分置信度 | 备选 A：candidate 状态照常匹配不区分 / 备选 B：candidate 状态不匹配，仅作为候选回退提示 | 推荐方案在"可发现"与"需确认"之间取得平衡，candidate 因子用于减少假阳性但保留人工确认窗口。备选 A 可能让未成熟因子静默进入正式测试点。备选 B 实际退回当前行为 | 推荐：下游 test-point-integrator 和 PC 生成需感知 match_confidence |
| CR017-DQ-03 | follow_up_tracking | CR-016 和 CR-017 的实施顺序 | **CR-017 先于 CR-016**：CR-017 无外部依赖可立即启动；CR-016 等 atomic-ops P0+P1 | 并行推进 | 推荐：CR-017 建立的 Step 1.5 模式恰好是 CR-016 的前半部分，顺序推进减少重复设计 | CR-016 的 m-analyzer 改动与 CR-017 修改同一文件不同区域，无合并冲突 |

### 不授权项

- 不授权修改现有因子库文件（`resource/factor-libraries/*/factor-library.yaml`）
- 不授权修改 `candidate-factor-proposals.yaml` 的外部消费格式
- 不授权删除或降级任何现有 candidate 状态因子
- 不授权修改 `resource/factor-libraries/index.yaml` 中的库状态

### 风险与回退

| 风险 | 等级 | 缓解 | 回退路径 |
|------|------|------|---------|
| candidate 因子未经充分验证被大规模复用 | 中 | match_confidence=medium 标记 + 下游显式确认 | 提升匹配阈值或改为仅 active 可匹配 |
| 全量加载 9 个库影响分析性能 | 低 | 纯内存索引，9 个库合计 <200 因子，可忽略 | 按 domain 按需过滤 |
| 与 CR-016 m-analyzer 同一文件修改冲突 | 低 | 修改不同区域（Step 1.5+2B vs Step 2C），顺序推进 | 合并冲突由第二个 CR 承担适配成本 |

### 后续 CR 候选

| 编号 | 描述 | 优先级 | 状态 |
|------|------|--------|------|
| T-01 | 因子库定期同步机制（类似 atomic-ops sync），当前库为静态快照 | P2 | candidate |
| T-02 | match_confidence 在下游 test-point-integrator / PC 生成中的显式处理 | P2 | candidate |
| T-03 | 因子库 index.yaml 中 candidate→active 的升级流程规范化 | P3 | candidate |

---

## 验证方法

1. 创建测试项目，场景涉及 IPv4 路由、DFX、负载均衡、HA 等多个域的因子
2. 运行 m-analyzer，验证：
   - `factor-resolution-report.md` 显示扫描库数 = 9（与 `index.yaml` 一致）
   - `ngfw-ipv4-route` 库中的 FAC-RT-NEXT-HOP、FAC-L3-FAIL-DETECT-METHOD 等被标记为 `source=public-library, match_confidence=medium`
   - 不再生成 FAC-CAND-001（下一跳类型）等 18 个重复候选
   - 真正的新候选（库中确实没有的）仍正常生成
3. 验证 `factor-library-lock.yaml` 不存在时自动创建
4. 验证 GATE-3 因子库扫描完整性自检通过

---

## 参考

- 关联 CR：CR-016（atomic-ops 消费缺口，共享 Step 1.5 设计模式）
- 关键文件：`skills/m-analyzer/SKILL.md` Step 2B（第 171-184 行）、公共因子库补充契约（第 496-505 行）
- 依赖资源：`resource/factor-libraries/index.yaml`、`resource/component-resource-links.yaml`
- 问题工作流：WF-PTM-TEAM-20260520-001
