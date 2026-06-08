---
status: active
current_round: 15
total_rounds: 15
ready_for_design: false
source: ".meta-workflow/process/CLARIFICATION-LOG.md"
---

---

## 调研发现（2026-05-09）——防火墙测试原子操作规范需求

> 本段为 meta-pm 阶段零快速调研，服务于"防火墙测试原子操作描述规范"新需求。

### 现有可复用资源

| 来源 | 调研发现 | 对本需求的价值 |
|------|---------|---------------|
| **Robot Framework** | Keyword 是最成熟的原子操作封装形式：具备名称、参数列表（含类型和默认值）、Return Type、Tags、Documentation 五字段；Tags 用于分类和过滤；文档格式同时支持纯文本和 HTML | Keyword 的 metadata 模型可直接作为原子操作元数据字段集的参考基线 |
| **Ansible Task/Module** | 幂等性（idempotency）是 Ansible 最核心的设计原则：模块在目标已达到期望状态时应直接退出；非幂等操作（如 shell/command）通过 `changed_when`、`creates`、`when` 条件手动引入幂等语义 | 直接支持"失败/重试/幂等性"这一用户关键决策点 |
| **Cisco XDR Atomic Actions** | 定义：小型、自包含的工作流，类似编程语言中的函数；可接收输入、执行动作并返回输出；400+ 系统原子动作，覆盖主流安全厂商（含防火墙类） | 证明"原子操作 = 输入→执行→输出"是行业共识；系统原子动作与自定义原子动作的两层模型值得借鉴 |
| **Keyword-Driven 测试框架** | 测试数据与脚本逻辑分离；关键字（原子操作）存入外部库，每个 Keyword 对应库中的具体实现；高度可复用，可被非编码人员使用 | 支持"规范描述 vs 具体实现"的边界划分讨论 |
| **pyATS / TRex** | 业界成熟的网络测试自动化框架；TRex 支持有状态/无状态流量生成，适用于防火墙压力测试；pyATS 与流量生成器的组合验证是主流模式 | 验证"TG 流量操作"是防火墙测试中的成熟原子能力；TRex 这类工具的调用方式可作为原子操作边界参考 |

### 平台能力约束

| 约束项 | 说明 |
|--------|------|
| 目标平台未在此需求中声明 | 用户尚未说明原子操作规范最终运行在哪种编排引擎上（Python 脚本 / YAML / LLM Agent / CI），需在场景发现中澄清 |
| REST API 直用 vs CLI 包装 | 用户已标记为关键决策点；行业趋势是提供 CLI/SDK 包装层（如 Ansible module 封装 API）以获得幂等性、参数验证和错误标准化能力，但增加维护成本 |
| 多设备协同 | 防火墙 + TG + Linux Mock + 交换机四类设备的原子操作规范需要统一抽象，避免碎片化；是否需要统一元数据 schema 是关键设计决策 |

### 对需求的初步影响

1. **Keyword 模型（Robot Framework）是最接近本需求的现有方案**：五字段结构（名称、参数、返回类型、标签、文档）可直接作为原子操作元数据 schema 的参考起点。
2. **幂等性必须显式纳入规范**：基于 Ansible 实践，对防火墙配置类操作（create/delete/update policy）幂等性描述是基本要求，TG 发流类操作需要区分是否幂等。
3. **"规范层 vs 实现层"是最先需要与用户对齐的边界问题**：本次需求是产出元数据描述规范（如何定义一个原子操作的 schema），还是同时产出具体的防火墙操作 Python 实现？
4. **REST API vs CLI 决策不可替用户做**：已知利弊见未决问题表，等待用户确认后再进入规范设计。

### 未决问题（待场景发现澄清）

| ID | 优先级 | 问题 | 利弊摘要 |
|----|--------|------|---------|
| Q-00 | **RESOLVED** (2026-05-09) | 工作目录定位：本需求是在 ptm-tde 仓库下新建子项目，还是需要在独立仓库中开发原子操作规范？ | **用户回答**：当前需求在 ptm-tde 仓库的 SCOPE-Pack 流程下完成规范设计工作（process/ 走澄清→HLD→Story→实现流程）；用户拿到 `delivery/` 交付物后会自行新建独立仓库落地实现。`scenario_subject_type=target-artifact`，场景主体是"防火墙测试原子操作规范"这个产物，不是 ptm-tde 仓库本身。 |
| Q-01 | **TRENDING-RESOLVED** (2026-05-09) | 产出范围：仅输出"原子操作描述规范（metadata schema + 设计原则文档）"，还是同时包含具体原子操作的 Python/YAML 实现？ | **已确认**：规范 + 实现代码骨架；**补充**：用户在 Q-02 中描述阶段二"测试工程师把原子操作实现为 CLI 工具"，间接印证 CLI 包装模式是主要实现形式；等待用户在 Q-03 正式确认后标记为 RESOLVED。 |
| Q-02 | **RESOLVED** (2026-05-09) | 调度方式：原子操作最终被谁调度？ | **用户回答**：三阶段演进模型。阶段一（用例设计）：测试工程师读取原子操作清单、为新功能设计新的原子操作；阶段二（执行阶段）：测试工程师把原子操作实现为 CLI 工具，人工/半自动执行；阶段三（自动化阶段）：全部工具实现后由 LLM 推理调度，需保证执行效率和易用易维护。LLM 调度面对的是结构化 CLI 工具集 + 规范元数据，而非裸 REST API。 |
| Q-03 | **TRENDING-RESOLVED** (2026-05-09) | REST API vs CLI 包装：继续直用防火墙 REST API，还是开发 CLI 工具封装 REST API？ | **Q-02 间接印证**：用户阶段二选择"实现为 CLI 工具"，强烈倾向 CLI 封装模式；但尚未作为独立问题被用户显式确认，等待正式拍板。 |
| Q-04 | **RESOLVED** (2026-05-09) | 设备多样性：防火墙厂商型号？ | **用户回答**：单厂商 TGFW（不是华为），无需多厂商抽象层。 |
| Q-05 | REQUIRED | 覆盖边界：4 类设备（防火墙、TG、Linux Mock、交换机）的原子操作规范，是统一一套 schema，还是各自独立规范？ | 统一 schema：复用性高但需找最小公约数；各自独立：灵活但碎片化 |
| Q-06 | OPTIONAL | 幂等性要求：是否需要对每个原子操作显式声明幂等性级别？（强幂等 / 弱幂等 / 非幂等）| 影响规范字段集复杂度 |
| Q-07 | **RESOLVED** (2026-05-09) | 使用者角色：规范主要服务于"手工编写测试用例的测试工程师"，还是"LLM Agent 自动生成执行编排"？ | **用户回答**：两者都是——工程师手工编写 + Agent 辅助/自动调度，规范需要同时人机可读。 |
| Q-08 | **OPEN / BLOCKING-for-HLD** (2026-05-09) | 测试用例 vs 原子操作边界：测试用例的粒度和原子操作的粒度如何划定？哪些逻辑放在测试用例层，哪些下沉到原子操作层？ | 见本轮澄清记录详细分析与三候选方案；此边界未定时，原子操作 schema 的 `scope` 字段、`pre_condition` 设计方式和 CLI 命名粒度均无法确定；标记为 HLD 前必须关闭的阻断项。 |

---

## 澄清历史

### 第 1 轮澄清（2026-04-09 — 初始需求与边界）

- 已确认：产物为独立工具包，而非嵌入式插件。
- 已确认：首版试点领域为华为网络防火墙。
- 已确认：目标平台覆盖 GitHub Copilot CLI、Claude Code、OpenClaw；当前实现已扩展到 Codex。
- 已确认：MFQ 中 M/F/Q 分别指模块/功能点分析、功能交互/耦合分析、质量属性分析。
- 已确认：核心交付物为 Markdown 格式的测试方案与测试用例文档。

### 第 2 轮澄清（2026-04-09 — 技术细节与规则）

- 已确认：需求字段模型、HTSM 参考范围、设计方法选择原则与覆盖判定规则。
- 已确认：F 分析首版采用 Excel 基线 + 内存图模型。
- 已确认：Excel 为耦合分析最低基线，新耦合点必须经用户确认后方可回写。
- 已确认：MCP 首版仅做查询，不做知识入库和索引维护。
- 已确认：输出字段需保留优先级和测试类型。

### 第 3 轮澄清（2026-04-09 — 场景拆分补齐）

- 已确认：应用场景输入可来自表格或 Markdown。
- 已确认：设计方法需要拆分为独立用户场景。
- 已确认：需求变更影响分析与问题单分析都属于正式支持场景。
- 已确认：每个逻辑用例的设计过程需要作为交付物一部分保留。

### 第 4 轮澄清（2026-04-22 — 新规范迁移中的场景重确认）

- 目标：按新规范把旧版场景迁移到 `process/USE-CASES.md`，并基于已实施项目能力重新确认。
- 迁移来源：`.meta-workflow/checkpoints/USE-CASES.md`、`README.md`、`doc/HLD.md`、`doc/USER-MANUAL.md`。
- 结果：已生成 `process/USE-CASES.md` v1.1，并完成更新模式下的确认。
- 说明：本轮在 autonomous mode 下执行，保留旧版已确认的 7 类核心流程，并补入“安装并初始化工作流包”场景作为新增正式场景。

### 第 5 轮澄清（2026-04-23 — 全局重设计场景重建）

- 修正结论：本轮 `USE-CASES` 应描述“用户如何使用 ptm-tde Agent 完成测试分析与设计”，而不是“如何整改本项目自身流程”。
- Phase 1A 判定：目标交付类型修正为 `agent`，治理模式修正为 `conditional`，评审强度修正为 `light`。
- Phase 1B 基线：场景围绕 ptm-tde 的真实能力重建，覆盖安装初始化、导入特性材料、目录与场景确认、MFQ 分析、设计计划确认、交付输出、需求变更处理、问题单盲区分析共 8 个场景。
- Phase 2 扫描：8 维覆盖已补齐多平台安装、`.input/` / `.output/` 约束、关键确认点、变更回退与外部依赖协同等维度。
- 当前结果：已按用户纠正意见重写 `process/USE-CASES.md` v2.0（draft），作为后续需求提取的正确场景基线。

### 第 6 轮澄清（2026-04-23 — 用户场景确认与需求提取）

- 用户已明确确认：`process/USE-CASES.md` 应作为“使用 ptm-tde Agent 的终端用户场景”正式基线继续推进。
- 已将 `process/USE-CASES.md` v2.0 标记为 `confirmed`。
- 已基于该场景基线和 `process/REQUEST.md` 提取 `process/REQUIREMENTS.md` v2.0（draft）。
- 当前需求聚焦 21 条 `REQ-NNN` 条目，覆盖安装初始化、输入导入、场景确认、M/F/Q 分析、设计计划、五种设计方法、覆盖验证、交付输出、变更影响分析和问题单盲区分析。
- 下一步：等待用户确认 `REQUIREMENTS.md`，以完成检查点①并推进到 `solution-design`。

### 第 7 轮澄清（2026-04-23 — 需求收敛与进入 HLD）

- 用户新增要求：平台仅保留 Claude Code 和 Codex；应用场景必须升级为可直接指导逻辑用例写作的“原子操作 - 观察点 - 逻辑链”模板。
- 用户新增要求：PPDCS 设计阶段必须输出完整分析过程（流程图、状态图、数据取值范围、组合策略等），并新增用例检索能力。
- 已据此重写 `process/REQUIREMENTS.md` 为 v3.0，并将其标记为 `confirmed`。
- 检查点①已完成：`USE-CASES.md confirmed=true` 且 `REQUIREMENTS.md confirmed=true`。
- 已进入 `solution-design`，并输出 `process/HLD.md` v4.0 与 `checkpoints/CHECKPOINT-HLD.md` 供检查点②确认。

### 第 8 轮澄清（2026-04-23 — 知识库与 MCP 设计补充）

- 用户新增要求：需要实现知识入库和索引维护，并与当前已搭建的知识库联合实现 MCP 开发。
- 设计补充点：场景发现需要先查询防火墙主应用场景，再查询特性应用场景、特性主功能，作为场景逻辑链设计参考。
- 已受理 CR-004，并将该变更判定为影响需求与 HLD 的高影响设计变更。
- 已重写 `process/REQUIREMENTS.md` 为 v4.0，新增知识入库、索引维护、分阶段知识查询和 MCP 联合开发相关需求。
- 已补充 `process/HLD.md` 为 v5.0，加入知识治理架构、MCP Gateway、`knowledge-index.yaml`、`knowledge-index-manager.py` 和 staged query 流程。
- 当前仍停留在 `solution-design`，等待更新后的 HLD 检查点②确认。

### 第 9 轮澄清（2026-04-23 — HLD 细化约束收敛）

- 用户明确 M1：REST API 由用户提供配置；测试工具由用户提供已有能力和接口说明，且工具需按 CLI 方式抽象；若工具当前不支持特性测试，Agent 需要协助输出工具接口抽象和待实现功能描述。
- 用户明确 M2：Claude Code / Codex 安装均由 `install.py` 托管，并需要纳入 `project scope / user scope` 两种安装范围；user scope 需要规则文件合并策略，允许按分阶段落地先完成 project scope。
- 用户明确 M3：用例检索收敛为按需求、逻辑用例和功能分类标签检索，不再扩展复杂排序与全文检索。
- 用户明确 M4：知识库当前仅需只读查询，不承担知识入库、远端索引维护或写回。
- 已受理 `CR-005`，并将该变更判定为影响需求与 HLD 的高影响设计变更。
- 已重写 `process/REQUIREMENTS.md` 为 v5.0，补入双 scope 安装、动作源契约和工具抽象需求，并收缩检索与知识治理边界。
- 已补充 `process/HLD.md` 为 v6.0，删除知识入库链路，改为只读 MCP staged query，并加入 user scope 合并策略与动作源建模设计。
- 当前仍停留在 `solution-design`，等待更新后的 HLD v6 检查点②确认。

### 第 10 轮澄清（2026-04-23 — HLD 确认并进入 Story/LLD 设计）

- 用户已明确确认 `process/HLD.md` v6.0。
- 用户直接要求继续完成 Story 分解，并在同一轮中完成全部 Story 的 LLD 设计。
- 本轮据此视为：检查点②通过，且检查点③在用户授权下同步通过。
- 已生成 `process/STORY-BACKLOG.md`、`process/DEVELOPMENT-PLAN.yaml`、`process/STORY-STATUS.md`。
- 已为全部 Story 起草 `process/stories/story-*.md` 与 `process/stories/story-*-lld.md`。
- 当前阶段已推进到 `story-execution`，所有 Story 状态停在 `ready-for-lld-review`，等待用户确认 LLD 后再进入开发。

### 第 11 轮澄清（2026-04-24 — 首轮 LLD 评审反馈修订）

- 用户指出 `STORY-01` 缺少明确写入目录，需要把 project scope 的实际目标路径细化到文件级。
- 用户指出 `STORY-03` 需要强化“场景分析必须准确正确、未知即询问用户”的原则，并把场景预置条件及其原子操作写入 LLD。
- 用户指出 `STORY-04` 需要补入测试对象 / 测试因子提取，以及工具满足性评估与 CLI/API 抽象设计。
- 用户指出 `STORY-06` 需要细化流程图生成、覆盖路径生成、测试数据分析与叠加，以及状态图、迁移路径和数据叠加方法。
- 用户指出 `STORY-07` 需要先做因子提取，再做因子级数据分析，再判定组合策略，最后把多条数据叠加到逻辑用例生成物理用例。
- 已据此重写 `story-01-lld.md`、`story-03-lld.md`、`story-04-lld.md`、`story-06-lld.md`、`story-07-lld.md`，并同步补强 `story-05-lld.md`、`story-09-lld.md` 的 factor / tool gap 消费说明。
- 当前仍停留在 `story-execution`，继续等待用户确认修订后的 LLD。

### 第 12 轮澄清（2026-04-24 — 工具分析表交付需求补充）

- 用户新增正式交付要求：在最终交付件中增加**工具分析表**。
- 工具分析表必须区分两类对象：
  - 已使用工具 / 动作源：给出工具名称、主要用法、用途和已使用场景；
  - 待实现工具 / 工具抽象：给出 API/CLI 接口、功能描述、不同输入输出条件下的处理逻辑、输出内容和适用场景。
- 已受理 `CR-006`，并将该变更判定为影响需求、HLD、相关 LLD 和交付模型的高影响设计变更。
- 已将 `process/REQUIREMENTS.md` 升级为 v6.0（confirmed），并细化 `REQ-026`、新增 `REQ-027`。
- 已将 `process/HLD.md` 升级为 v7.0（ready-for-review），补入工具分析模型、交付流程和输出路径。
- 已同步补强 `story-03-lld.md`、`story-04-lld.md`、`story-08-lld.md`、`story-09-lld.md`。
- 当前流程已从 `story-execution` 回退到 `solution-design`，等待更新后的 HLD v7 检查点②确认。

### 第 13 轮澄清（2026-04-24 — meta-flow 文档格式与 Story 命名同步）

- 用户指出 meta-flow 已更新，要求同步检查并更新 `process/REQUEST.md` 与 `process/USE-CASES.md` 的文档格式。
- 用户要求检查 Story 文档的命名/命令规范，并统一修改 Story 文件名。
- 已受理 `CR-007`，判定为中影响治理变更：不改变需求与 HLD 边界，但会影响上游治理文档和 Story 文件路径引用。
- 已将 `process/REQUEST.md` 升级为 v2.0，补齐上下文字段、范围/排除结构和交付表格式。
- 已将 `process/USE-CASES.md` 升级为 v2.1，补齐上下文字段并收缩平台口径到 Claude Code / Codex。
- 已将 `process/stories/` 下全部 Story 文件统一改为 kebab-case，并同步更新 `STORY-STATUS`、变更单和历史引用路径。
- 当前阶段仍保持 `solution-design`，主待办不变：继续等待 HLD v7 检查点②确认。

### 第 14 轮澄清（2026-05-09 — 防火墙原子操作规范：三阶段模型 + 边界问题分析）

> 本轮服务于"防火墙测试原子操作规范"新需求，与 ptm-tde Agent 主流程独立记录。

#### 本轮用户回答摘要

**Q-07（RESOLVED）— 使用者角色**
- 两者都是：测试工程师手工编写 + Agent 辅助/自动调度。
- 规范必须同时满足人机可读需求。

**Q-02（RESOLVED）— 调度方式：三阶段演进模型**
- 阶段一（用例设计阶段）：测试工程师读取已有原子操作清单，为该特性的新功能设计新的原子操作，输出原子操作 schema 描述文件。
- 阶段二（执行阶段）：测试工程师把原子操作实现为 CLI 工具，通常使用 CLI 操作，人工/半自动执行。
- 阶段三（自动化执行阶段）：所有工具实现后，由 LLM 推理调度，需保证执行效率和易用易维护。LLM 调度面对的是结构化 CLI 工具集 + 规范元数据，而非裸 REST API。
- 关键推论：原子操作规范是设计语言（Schema），CLI 是其实现产物；两者需要保持结构对应。

**Q-03（TRENDING-RESOLVED）— CLI 包装倾向**
- Q-02 阶段二描述"测试工程师把原子操作实现为 CLI 工具"，间接印证了 CLI 封装模式；但尚未作为独立问题被用户正式确认，保持 TRENDING-RESOLVED 状态。

**Q-04（RESOLVED）— 防火墙厂商**
- 单厂商 TGFW，无需多厂商抽象层。

#### 本轮重点：测试用例 vs 原子操作边界调研与分析

**背景**：用户反问"测试用例和原子操作的边界是什么？"，希望产品经理给出建议。

**调研来源**：
- [Robot Framework User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html)（Test Case vs Keyword 分层）
- [Cisco XDR Atomic Actions](https://docs.xdr.security.cisco.com/Content/Automate/atomic-actions.htm)（Atomic Action vs Workflow）
- [Cucumber Step Organization](https://cucumber.io/docs/gherkin/step-organization/)（Scenario vs Step Definition）
- [Spirent 高性能防火墙测试](https://www.spirent.com/blogs/2012-02-16_structuring_real_world_test_high_performance_firewalls)（Test Method 粒度参考）

**调研结论（业界共识）**：

| 框架/平台 | 测试用例等价层 | 原子操作等价层 | 边界判定原则 |
|---------|------------|------------|-----------|
| Robot Framework | Test Case | Keyword | 单 Keyword 不跨多个独立目标状态；Test Case 描述"什么场景通过" |
| Cisco XDR | Workflow | Atomic Action | Atomic Action = 函数（接收输入、执行动作、返回输出），无业务判断；Workflow = 编排多个 Atomic Action 的脚本 |
| Cucumber/BDD | Scenario | Step Definition | Step = 单个动作或断言（不含 "and"）；Scenario = 一个完整的可验证意图 |
| Spirent 防火墙测试 | Test Suite / Test Case | Test Method / Procedure | Test Method 描述如何配置和执行单一测试操作；Test Case 描述哪个条件下预期什么结果 |

**三候选边界定义**：

---

**候选 A：以"单设备 API 调用"为原子操作粒度**

- 边界判定：凡是对单个设备（防火墙/TG/Switch/Mock）调用单次 API 或 CLI 命令的操作，即为一个原子操作；测试用例由若干原子操作 + 断言组合而成。
- TGFW 示例（"ACL 阻断流量验证"）：
  - 原子操作层：`fw_create_acl_rule`、`tg_send_packet`、`fw_query_policy_hit_count`、`fw_delete_acl_rule`
  - 测试用例层：Given 空 ACL；When 创建阻断规则 + 发流；Then 查询命中计数 > 0 且流量被阻断；清理。
- 优点：粒度最细、最易复用、调度时每步可独立重试、CLI 命名直观；与 Cisco XDR Atomic Action 完全对齐。
- 缺点：测试用例代码量显著增加（一个简单场景可能需要 10+ 条原子操作）；工程师手写时认知负担较高；同一功能不同调用方式（幂等/非幂等）需要拆成不同原子操作。

---

**候选 B：以"单一可观察状态变更"为原子操作粒度**

- 边界判定：原子操作 = 完成一个可独立验证的最小状态变更（含必要的等待/轮询逻辑，但不含跨目标的断言）；测试用例 = 描述一个完整的"触发条件 → 预期状态"验证场景，由多个原子操作 + 一个或多个断言组成。
- TGFW 示例（"ACL 阻断流量验证"）：
  - 原子操作层：`fw_ensure_acl_rule_exists`（含创建+等待生效）、`tg_send_and_capture_traffic`（含发流+统计采集）、`fw_teardown_acl_rule`
  - 测试用例层：Given 防火墙策略基线已建立；When 执行 `fw_ensure_acl_rule_exists` + `tg_send_and_capture_traffic`；Then 断言流量被阻断（捕获包数=0）+ 命中计数 > 0；Cleanup `fw_teardown_acl_rule`。
- 优点：每个原子操作的语义完整（自我含义明确），工程师设计和阅读效率高；LLM 调度时上下文窗口消耗小（操作数量少）；幂等性容易在原子操作内部实现。
- 缺点：原子操作内部的复合逻辑（等待+重试+验证）使调试变复杂；不同测试场景的复用粒度不如候选 A 细。
- **这是调研中最接近业界主流的方案**（对齐 Robot Framework Keyword 粒度 + Ansible Task 粒度）。

---

**候选 C：以"完整测试阶段（Setup/Action/Verify/Cleanup）"为原子操作粒度**

- 边界判定：将原子操作定义为四个测试阶段之一（类似 Gherkin 的 Given/When/Then/After），整个防火墙测试由 Setup 原子操作集 + Action 原子操作集 + Verify 原子操作集 + Cleanup 原子操作集编排完成；测试用例 = 对上述四个阶段的编排配置。
- TGFW 示例（"ACL 阻断流量验证"）：
  - 原子操作层：`setup_acl_test_baseline`、`action_send_blocked_traffic`、`verify_acl_block_result`、`cleanup_acl_policy`
  - 测试用例层：配置引用以上 4 个原子操作，并给出具体参数（规则 ID、流量参数、预期命中阈值）。
- 优点：与 BDD Scenario 结构直接对应，工程师设计时认知摩擦最低；LLM 调度可以直接按阶段生成编排序列。
- 缺点：粒度太粗，多个测试用例共享的 setup/cleanup 逻辑无法复用；同一阶段下如有多个独立变体，需要重写整个原子操作；维护成本最高。

---

**推荐：候选 B**

理由：
1. **三阶段模型适配**：阶段一（设计）时，以"状态变更"为粒度的原子操作与测试用例的"验证场景"形成清晰分工，工程师写用例时思维负担最低；阶段二（实现为 CLI）时，"单一状态变更"恰好对应一个语义完整的 CLI 子命令；阶段三（LLM 调度）时，操作数量适中，上下文消耗可控，且每个原子操作的输入/输出语义清晰，有利于 LLM 推理。
2. **TGFW 单厂商约束**：不需要 adapter 层，候选 B 的内部实现复杂度不会因多厂商而急剧膨胀。
3. **人机双读可行**：原子操作名称使用 `动词_目标_状态` 格式（如 `fw_ensure_acl_rule_active`），工程师可直接阅读理解；LLM 可通过名称 + schema 元数据推理用法。
4. **业界对齐**：与 Robot Framework Keyword 和 Ansible Task 均属同一粒度层，有成熟的实践参考。

候选 A 适合对调试精度要求极高且已有完整工具链的场景（如 Spirent 压测场景）；候选 C 适合 BDD 驱动的接受度测试。在本需求的防火墙功能测试场景下，候选 B 是最均衡的选择。

#### 新增未决问题

| ID | 优先级 | 问题 | 候选选项 |
|----|--------|------|---------|
| Q-08 | **BLOCKING-for-HLD** | 测试用例 vs 原子操作边界：采用哪种粒度定义原子操作？ | A：单设备 API 调用；B：单一可观察状态变更（推荐）；C：完整测试阶段（SAVC）；D：其他（用户自定义描述） |

#### 本轮 USE-CASES.md 同步更新

- 新增"三阶段调度模型"段落，记录设计→实现→自动化的演进路径。
- 新增 TGFW 单厂商约束到平台约束段落。
- 更新用户角色段落，将 Agent 调度者作为新用户画像 P-05 登记（待 Q-08 确认后补充场景细节）。
- 在 OPEN-ITEMS 段落登记 Q-08，标记 BLOCKING-for-HLD。

#### 当前阻断项状态

| ID | 状态 | 说明 |
|----|------|------|
| Q-05 | OPEN / REQUIRED | 统一 schema vs 各设备独立规范 |
| Q-06 | OPEN / OPTIONAL | 幂等性字段是否显式声明 |
| Q-08 | **RESOLVED (2026-05-09)** | 用户选择候选 B：单一可观察状态变更粒度 |

---

### 第 15 轮澄清（2026-05-09 — Q-08 RESOLVED + 继续 8 维扫描：异常路径 / 幂等性 / 跨设备编排）

#### Q-08 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-08 |
| **状态** | **RESOLVED（2026-05-09）** |
| **用户选择** | 候选 B：以"单一可观察状态变更"为原子操作粒度 |
| **正式规则（写入 USE-CASES.md 边界规则章节）** | 1. 原子操作 = 单一可观察状态变更，内部可含必要等待/重试，但不含跨目标断言；2. 测试用例 = "触发条件 → 预期状态" + 多个原子操作 + 独立断言；3. 命名规范：`设备_动词_目标`（如 `fw_ensure_acl_rule_exists`），与 Robot Framework Keyword / Ansible Task 粒度对齐；4. 认可示例：TGFW "ACL 阻断验证" = `fw_ensure_acl_rule_exists` + `tg_send_and_capture_traffic` + `fw_teardown_acl_rule` 三个原子操作。 |

#### 本轮新增问题（8 维扫描续 — 异常路径 / 幂等性 / 跨设备编排）

| ID | 维度 | 问题描述 | 阻断等级 | 状态 |
|----|------|---------|---------|------|
| Q-09 | 异常维度（D7） | 原子操作执行失败时的标准行为：抛出异常终止 / 返回结构化错误码 / 内部自动重试 / 降级继续？ | BLOCKING-for-HLD | OPEN |
| Q-10 | 幂等性约束 | 候选 B 已隐含"内部含等待/重试"，是否要求所有原子操作必须是幂等？还是支持非幂等但需显式标记？ | REQUIRED | OPEN |
| Q-11 | 跨设备编排粒度 | 候选 B 倾向单设备状态变更，但"防火墙下发策略后 TG 立即抓包"这类跨设备联动是否合并为一个原子操作？ | REQUIRED | OPEN |

#### 当前阻断项状态（第 15 轮末）

| ID | 状态 | 说明 |
|----|------|------|
| Q-05 | OPEN / REQUIRED | 统一 schema vs 各设备独立规范 |
| Q-06 | OPEN / OPTIONAL | 幂等性字段是否显式声明（与 Q-10 关联） |
| Q-08 | **RESOLVED (2026-05-09)** | 候选 B 已确认 |
| Q-09 | **OPEN / BLOCKING-for-HLD** | 异常行为标准：等待用户选择 |
| Q-10 | OPEN / REQUIRED | 幂等性约束范围：等待用户确认 |
| Q-11 | OPEN / REQUIRED | 跨设备联动是否合并为原子操作：等待用户确认 |

---

### 第 16 轮澄清（2026-05-09 — Q-09 / Q-10 / Q-11 RESOLVED + 8 维扫描第二轮问题准备）

#### 用户决策摘要（全部接受推荐）

| ID | 决策 | 正式规则 |
|----|------|---------|
| **Q-09** | **RESOLVED (2026-05-09) — 选 B2** | 失败时返回结构化错误码 `{status: failed, error_type, detail}`，调用方决策；原子操作内部不做自动重试，重试由编排层控制 |
| **Q-10** | **RESOLVED (2026-05-09) — 选 I2** | 默认鼓励幂等；非幂等操作必须在 schema 中显式标记 `idempotent: false`，并填写 `side_effects` 字段说明副作用 |
| **Q-11** | **RESOLVED (2026-05-09) — 选 E2** | 保持单设备原子操作；跨设备联动（如防火墙下发策略后 TG 立即抓包）保持为独立原子操作，在测试用例层通过 `tight_sequence` 字段描述时序依赖 |

#### Q-09 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-09 |
| **维度** | 异常维度（D7）|
| **状态** | **RESOLVED（2026-05-09）** |
| **用户选择** | B2：返回结构化错误码，调用方决策 |
| **正式规则** | 1. 原子操作失败时返回 `{status: "failed", error_type: "<类型>", detail: "<说明>"}` 结构；2. 原子操作内部不做自动重试；3. 重试策略由编排层（测试用例执行器 / LLM Agent）控制；4. schema 中新增必填字段 `on_failure` 枚举（`fail_fast` / `return_error` / `retry_by_caller`），默认 `return_error` |

#### Q-10 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-10 |
| **维度** | 幂等性约束 |
| **状态** | **RESOLVED（2026-05-09）** |
| **用户选择** | I2：默认幂等，非幂等显式标记 |
| **正式规则** | 1. 所有原子操作默认应实现为幂等；2. 非幂等操作必须在 schema 中显式声明 `idempotent: false`；3. 声明非幂等时必须同时填写 `side_effects: "<副作用描述>"`，说明对系统状态的持久影响；4. Q-06 随之关闭：幂等性字段设计采用 I2 模型（`idempotent: bool`，默认 `true`；`side_effects: string`，仅非幂等时必填）|

#### Q-11 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-11 |
| **维度** | 跨设备编排粒度 |
| **状态** | **RESOLVED（2026-05-09）** |
| **用户选择** | E2：保持单设备原子操作，跨设备时序依赖用测试用例层 `tight_sequence` 字段描述 |
| **正式规则** | 1. 原子操作始终以单设备为操作主体（`device` 字段为单值）；2. 跨设备联动不合并为复合原子操作；3. 测试用例 schema 新增 `tight_sequence: [op_id_1, op_id_2, ...]` 字段，用于声明需要紧密顺序执行的原子操作组；4. `tight_sequence` 不改变原子操作本身的设计，只在用例层标记执行约束 |

#### 同步更新 USE-CASES.md OPEN-ITEMS 状态

- Q-09 → RESOLVED (B2)
- Q-10 → RESOLVED (I2)，同时关闭 Q-06
- Q-11 → RESOLVED (E2)

#### 当前阻断项状态（第 16 轮末）

| ID | 状态 | 说明 |
|----|------|------|
| Q-05 | OPEN / REQUIRED | 统一 schema vs 各设备独立规范；尚未阻断当前扫描 |
| Q-06 | **RESOLVED (2026-05-09)** | 随 Q-10/I2 关闭；幂等性字段采用 `idempotent: bool` + `side_effects: string` |
| Q-08 | **RESOLVED (2026-05-09)** | 候选 B 已确认 |
| Q-09 | **RESOLVED (2026-05-09)** | B2：返回结构化错误码，调用方决策 |
| Q-10 | **RESOLVED (2026-05-09)** | I2：默认幂等，非幂等必须显式标记 |
| Q-11 | **RESOLVED (2026-05-09)** | E2：保持单设备；用例层 `tight_sequence` 描述时序依赖 |
| Q-12 | **RESOLVED (2026-05-09) — P1** | 参数化：强类型字段列表，每参数声明 name/type/required/default/description |
| Q-13 | **RESOLVED (2026-05-09) — R1** | 返回值：统一顶层 `{status, result, metadata: {duration_ms, device, timestamp}}` + 各操作自定 `output_schema` |
| Q-14 | **RESOLVED (2026-05-09) — V1** | 版本演进：原子操作级 `schema_version` + `deprecated/since/reason` 字段 |
| Q-15 ~ Q-16 | OPEN / 待确认 | 超时与时序、可观测性；第二批问题（本轮抛出）|

---

### 第 17 轮澄清（2026-05-09 — Q-12/13/14 RESOLVED + Q-15/16 抛出）

#### Q-12 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-12 |
| **维度** | 参数化与变量注入 |
| **状态** | **RESOLVED（2026-05-09）— P1** |
| **用户选择** | P1：强类型字段列表，每参数独立声明 |
| **正式规则** | 1. 原子操作 `parameters` 字段为数组，每项包含：`name`（必填字符串）、`type`（必填，枚举：string / int / float / bool / json / list）、`required`（必填布尔）、`default`（可选，类型随 `type` 字段）、`description`（必填字符串，人机双可读）；2. 无默认值的必填参数必须在 schema 中将 `required: true` 且不填 `default`；3. 参数类型为 `json` 时，可附带 `schema_ref` 字段指向复合对象定义 |

#### Q-13 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-13 |
| **维度** | 结果与返回值规范 |
| **状态** | **RESOLVED（2026-05-09）— R1** |
| **用户选择** | R1：统一顶层结构 + 各操作自定义 `output_schema` |
| **正式规则** | 1. 所有原子操作返回值必须包含统一顶层字段：`status`（枚举：success / failed / timeout / skipped）、`result`（操作级自定义输出对象，见 `output_schema`）、`metadata`（固定三字段：`duration_ms: int`、`device: string`、`timestamp: ISO8601 string`）；2. 各操作在 schema 中通过 `output_schema` 字段声明 `result` 对象的内部结构；3. 失败时 `result` 中必须含 `error_type` 和 `detail` 字段（与 B2 规则对齐）；4. `metadata.device` 与操作级 `device` 字段保持一致，供编排层做路由和日志归因 |

#### Q-14 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-14 |
| **维度** | 版本与演进 |
| **状态** | **RESOLVED（2026-05-09）— V1** |
| **用户选择** | V1：原子操作级版本 + `deprecated` 标记 |
| **正式规则** | 1. 每个原子操作 schema 携带 `schema_version: semver`（如 `"1.0.0"`），独立于整体规范版本演进；2. 废弃操作必须在 schema 中声明 `deprecated: true`、`since: semver`（废弃起始版本）、`reason: string`（废弃原因）和可选 `replaced_by: <op_id>`；3. 废弃操作不立即删除，保留至少一个大版本周期；4. 整体原子操作库维护 `CHANGELOG.md`，每次新增/修改/废弃操作必须追加条目 |

#### 当前阻断项状态（第 17 轮末）

| ID | 状态 | 说明 |
|----|------|------|
| Q-05 | OPEN / REQUIRED | 统一 schema vs 各设备独立规范 |
| Q-06 | **RESOLVED (2026-05-09)** | 随 Q-10/I2 关闭 |
| Q-08 | **RESOLVED (2026-05-09)** | 候选 B |
| Q-09 | **RESOLVED (2026-05-09)** | B2 |
| Q-10 | **RESOLVED (2026-05-09)** | I2 |
| Q-11 | **RESOLVED (2026-05-09)** | E2 |
| Q-12 | **RESOLVED (2026-05-09)** | P1 |
| Q-13 | **RESOLVED (2026-05-09)** | R1 |
| Q-14 | **RESOLVED (2026-05-09)** | V1 |
| Q-15 | **OPEN / REQUIRED** | 超时与时序；本轮第一个问题 |
| Q-16 | **OPEN / REQUIRED** | 可观测性；本轮第二个问题 |

---

### 第 18 轮澄清（2026-05-09 — Q-15/Q-16 RESOLVED + Q-01 正式固化 + REQUIREMENTS.md 生成）

#### Q-01 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-01 |
| **维度** | 产出范围 |
| **状态** | **RESOLVED（2026-05-09）** |
| **用户决策** | 由 Q-02 三阶段演进模型间接确认，本轮正式固化为 IN-SCOPE |
| **正式规则** | 1. 交付物包含两类：规范文档（schema 定义、设计原则、命名规范、错误码规范、诊断快照枚举）+ 代码骨架（4 类设备原子操作模板、测试用例层 tight_sequence 模板、YAML/Python 示例）；2. 阶段二实现形式为 CLI 工具包装，作为既定前提写入 REQUIREMENTS；3. 代码骨架为可直接调用的占位桩函数，返回合规的 R1 结构，不是完整端到端实现 |

#### Q-15 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-15 |
| **维度** | 超时与时序 |
| **状态** | **RESOLVED（2026-05-09）— T1** |
| **用户选择** | T1：schema 声明 `default_timeout_s: int` + `poll_interval_s: float` 元数据字段；调用方通过 CLI 参数覆盖 |
| **正式规则** | 1. 每个原子操作 schema 可声明 `default_timeout_s: int`（默认超时秒数，必填）和 `poll_interval_s: float`（轮询间隔秒数，可选，仅需要等待稳态的操作填写）；2. 调用方（CLI 工具或 LLM Agent）可通过 CLI 参数覆盖这两个值；3. 超时时返回 `{status: "timeout"}`，与 B2/R1 结构对齐（`result` 中含 `error_type: "timeout"` 和 `detail`）；4. `wait_for_steady_state` 语义通过 `poll_interval_s` 字段存在与否隐式表达：有 `poll_interval_s` 的操作即为"需要等待稳态"的操作 |

#### Q-16 正式关闭记录

| 字段 | 内容 |
|------|------|
| **ID** | Q-16 |
| **维度** | 可观测性 |
| **状态** | **RESOLVED（2026-05-09）— O1** |
| **用户选择** | O1：schema 新增 `diagnostic_snapshot` 数组字段，每项含 `device / snapshot_type / description`；采集由代码骨架辅助函数提供，不侵入原子操作主逻辑 |
| **正式规则** | 1. 每个原子操作 schema 可声明 `diagnostic_snapshot` 数组，每项包含：`device`（采集目标设备 ID）、`snapshot_type`（枚举：`config_dump` / `counter` / `route_table` / `log_tail`）、`description`（说明采集目的，人机双可读）；2. 诊断快照采集由代码骨架中的辅助函数（helper）提供，不侵入原子操作主逻辑；3. 快照数据作为可选附加信息写入 `metadata` 的 `diagnostics` 子字段，不影响 `status` / `result` 的主结构；4. 若操作不需要诊断快照，`diagnostic_snapshot` 字段可省略 |

#### 全量问题状态汇总（第 18 轮末 — 全部关闭）

| ID | 状态 | 决策摘要 |
|----|------|---------|
| Q-00 | **RESOLVED (2026-05-09)** | 在 ptm-tde 仓库完成规范设计，用户新建独立仓库落地实现 |
| Q-01 | **RESOLVED (2026-05-09)** | 规范文档 + 代码骨架双交付；阶段二为 CLI 工具包装 |
| Q-02 | **RESOLVED (2026-05-09)** | 三阶段演进：设计 → CLI 实现 → LLM 调度 |
| Q-03 | **RESOLVED (2026-05-09)** | CLI 包装模式（由 Q-02 确认） |
| Q-04 | **RESOLVED (2026-05-09)** | 单厂商 TGFW |
| Q-05 | **RESOLVED (2026-05-09)** | 统一 schema（由 REQUIREMENTS 中 FR-1 覆盖 4 类设备） |
| Q-06 | **RESOLVED (2026-05-09)** | 随 Q-10/I2 关闭；`idempotent: bool` + `side_effects: string` |
| Q-07 | **RESOLVED (2026-05-09)** | 工程师 + LLM Agent 双使用者 |
| Q-08 | **RESOLVED (2026-05-09)** | 候选 B：单一可观察状态变更粒度 |
| Q-09 | **RESOLVED (2026-05-09)** | B2：结构化错误码，调用方决策 |
| Q-10 | **RESOLVED (2026-05-09)** | I2：默认幂等，非幂等显式标记 |
| Q-11 | **RESOLVED (2026-05-09)** | E2：单设备 + 用例层 `tight_sequence` |
| Q-12 | **RESOLVED (2026-05-09)** | P1：强类型字段列表 |
| Q-13 | **RESOLVED (2026-05-09)** | R1：统一顶层 + 自由 `result` + `metadata` |
| Q-14 | **RESOLVED (2026-05-09)** | V1：原子操作级 `schema_version` + `deprecated` |
| Q-15 | **RESOLVED (2026-05-09)** | T1：`default_timeout_s` + `poll_interval_s`；超时返回 `{status: "timeout"}` |
| Q-16 | **RESOLVED (2026-05-09)** | O1：`diagnostic_snapshot` 数组 + 枚举；辅助函数采集，不侵入主逻辑 |

> 所有 BLOCKING / REQUIRED / OPTIONAL 问题已全部关闭。REQUIREMENTS.md 已生成，进入需求确认人工检查点。
