---
story_id: "STORY-01"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T13:43:26+08:00"
author: "meta-dev"
tier: "platform"
shared_fragments:
  - "installer-projection"
open_items:
  - "无 blocker；user scope 合并移交 STORY-02"
depends_on: []
---

# STORY-01 LLD：Installer 基线 — Claude/Codex project scope 投影

## 1. 目标

把安装器的正式支持范围收敛为 Claude Code / Codex，并稳定 `project scope` 的目录投影、规则文件写入和 dry-run 输出。该 Story 需要**明确列出实际写入目录与文件**，以便开发时不会把平台投影写错。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-001 | 仅支持 Claude Code / Codex，且安装器统一托管 |
| HLD §9 | 平台投影与 project scope 路径 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `parse_args` | 接收平台、scope、project-dir、dry-run 参数 |
| `resolve_target_root` | 解析 project scope 根目录 |
| `install_rules` | 生成平台无关规则文件（如项目根 `AGENTS.md`、Claude 的 `CLAUDE.md`） |
| `install_agents` | 生成平台 Agent 投影 |
| `install_skills` | 生成平台 Skill 投影 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `scripts/install.py` | 收缩平台口径，补强 project scope dry-run，并明确写入路径 |
| `rules/CLAUDE.md` | 作为 Claude Code 的规则源文件 |
| `rules/AGENTS.md` 或项目根 `AGENTS.md` | 作为项目级通用规则源文件（若存在） |

### project scope 写入目录（必须落盘）

#### Claude Code

```text
<project-root>/
  AGENTS.md                         # 若源规则存在则写入
  .claude/
    CLAUDE.md
    agents/
      ptm-tde.md
    skills/
      <skill-name>/SKILL.md
```

#### Codex

```text
<project-root>/
  AGENTS.md                         # 若源规则存在则写入
  .codex/
    agents/
      ptm-tde.toml
    skills/
      <skill-name>.md
```

## 5. 数据模型与持久化设计

- 无新增业务持久化模型。
- 新增**安装结果清单视图**，至少要能表达：

| 字段 | 含义 |
|---|---|
| `platform` | 目标平台 |
| `scope` | 固定为 `project` |
| `target_root` | 目标项目根目录 |
| `writes` | 将写入的绝对/相对路径列表 |
| `content_type` | `rules / agents / skills` |

- dry-run 只输出安装结果清单，不落盘业务数据。

## 6. API / Interface 设计

| 参数 | 约束 |
|---|---|
| `--platform` | `claude-code / codex` |
| `--scope` | `project` |
| `--project-dir` | 必填；指向安装目标项目根目录 |
| `--content` | `all / rules / agents / skills` |
| `--dry-run` | 必须显示写入列表 |

### 输出约定

- Claude Code：写入 `.claude/CLAUDE.md`、`.claude/agents/*.md`、`.claude/skills/<name>/SKILL.md`
- Codex：写入 `.codex/agents/*.toml`、`.agents/skills/<name>/SKILL.md`
- 若存在通用规则源：写入 `<project-root>/AGENTS.md`

## 7. 核心处理流程

1. 解析 `platform / scope / project-dir / content / dry-run`；
2. 校验平台仅允许 `claude-code / codex`；
3. 校验 scope 必须为 `project`；
4. 解析 `<project-root>`；
5. 计算将写入的目标目录：
   - Claude：`AGENTS.md`、`.claude/CLAUDE.md`、`.claude/agents/`、`.claude/skills/`
   - Codex：`AGENTS.md`、`.codex/agents/`、`.agents/skills/`
6. 若 `dry-run=true`，输出完整写入清单；
7. 若 `dry-run=false`，按 `rules → agents → skills` 顺序执行写入；
8. 输出安装结果摘要。

## 8. 技术设计细节

### 8.1 目录生成规则

- Claude Code：
  - `<project-root>/.claude/CLAUDE.md`
  - `<project-root>/.claude/agents/ptm-tde.md`
  - `<project-root>/.claude/skills/<skill-name>/SKILL.md`
- Codex：
  - `<project-root>/.codex/agents/ptm-tde.toml`
  - `<project-root>/.agents/skills/<skill-name>/SKILL.md`
- 通用规则：
  - `<project-root>/AGENTS.md`（仅在源文件存在时写入）

### 8.2 写入顺序

1. 规则文件
2. Agent 文件
3. Skill 文件

### 8.3 dry-run 最小内容

- platform
- scope
- project root
- 每个即将写入的目录和文件
- 每个文件的来源类别（rules / agent / skill）

## 9. 安全与性能设计

- 禁止默认落到非 project scope。
- 禁止保留已淘汰平台的误导性默认值。
- 禁止在 dry-run 中省略写入目录，否则开发时无法校验平台结构。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| Claude Code project dry-run | 检查 `.claude/CLAUDE.md`、`.claude/agents/ptm-tde.md`、`.claude/skills/...` 是否都出现在输出中 |
| Codex project dry-run | 检查 `.codex/agents/ptm-tde.toml`、`.agents/skills/...` 是否都出现在输出中 |
| AGENTS 规则写入 | 检查 `<project-root>/AGENTS.md` 是否按存在性进入输出 |
| 旧平台拒绝 | 参数校验 |

## 11. 实施步骤

1. 收缩平台枚举与帮助文案；
2. 固化 Claude/Codex 的 project scope 目录规则；
3. 在 `install_rules` 中明确 `<project-root>/AGENTS.md` 与 `.claude/CLAUDE.md` 的写入条件；
4. 在 `install_agents` 中明确 `.claude/agents/*.md` 与 `.codex/agents/*.toml` 的输出；
5. 在 `install_skills` 中明确 `.claude/skills/<name>/SKILL.md` 与 `.agents/skills/<name>/SKILL.md` 及其同树模板资产输出；
6. 重写 dry-run 输出，显示完整目录/文件清单；
7. 输出安装结果摘要。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 历史多平台文案残留 | 统一在 install.py 与规则文件中收口 |
| Codex 投影差异 | 保持由 installer 托管，不把布局写死到 Agent |
| 写入目录不透明 | dry-run 强制列出所有目录与文件 |

## 13. 回滚与发布策略

- 回滚范围：`scripts/install.py` 与相关规则文件；
- 若安装失败，仅保留 dry-run，不执行写入；
- 项目级安装失败时，允许按 `rules / agents / skills` 三类分别清理已写目录。

## 14. Definition of Done

- [ ] 仅支持 Claude Code / Codex
- [ ] project scope dry-run 输出完整
- [ ] Claude Code 写入目录明确到 `.claude/CLAUDE.md`、`.claude/agents/`、`.claude/skills/`
- [ ] Codex 写入目录明确到 `.codex/agents/`、`.agents/skills/`
- [ ] 路径符合 `process/PLATFORM-INSTALL-SPEC.md`
