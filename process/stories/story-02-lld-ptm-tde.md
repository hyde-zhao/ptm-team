---
story_id: "STORY-02"
lld_version: "1.0"
status: "lld-approved"
confirmed: true
confirmed_by: "user"
confirmed_at: "2026-04-24T13:43:26+08:00"
author: "meta-dev"
tier: "platform"
shared_fragments:
  - "installer-projection"
  - "marker-merge"
open_items:
  - "marker section 命名以 `ptm-tde managed block` 为默认候选，实施时可细化"
depends_on:
  - "STORY-01"
---

# STORY-02 LLD：Installer 用户级安装 — `CLAUDE.md` / `AGENTS.md` 合并

## 1. 目标

在 `user scope` 安装场景下，引入 marker section 合并策略和 merge report，避免覆盖用户已有全局规则文件。

## 2. 需求映射

| 需求 | 说明 |
|---|---|
| REQ-001 | user scope 需显式合并，不得静默覆盖 |
| HLD §8.5 / §10.6 | 安装与合并流程 |

## 3. 模块拆分与职责

| 模块 | 职责 |
|---|---|
| `resolve_target_root` | 解析 `~/.claude` / `~/.codex` |
| `install_rules` | 检测已有规则文件并决定 merge 模式 |
| `merge reporter` | 输出 merge report 或 blocked 原因 |

## 4. 代码结构与文件影响范围

| 文件 | 变更 |
|---|---|
| `scripts/install.py` | 新增 marker merge 流程 |
| `rules/CLAUDE.md` | 作为被合并内容源 |
| `process/PLATFORM-INSTALL-SPEC.md` | 引用规范，不强制改动 |

## 5. 数据模型与持久化设计

| 对象 | 字段 |
|---|---|
| merge report | `target_file / mode / inserted_blocks / conflicts / blocked_reason` |

## 6. API / Interface 设计

| 参数 | 约束 |
|---|---|
| `--scope user` | 进入 user scope 路径 |
| dry-run | 必须显示 merge mode |

## 7. 核心处理流程

1. 解析 user scope 根路径；
2. 检测既有 `CLAUDE.md` / `AGENTS.md`；
3. 选择 `direct-write / marker-merge / blocked`；
4. 生成 merge report；
5. 成功后再写入。

## 8. 技术设计细节

- marker section 采用固定起止标记；
- 若未找到合法插入点，则 blocked；
- Codex 仍由 installer 托管用户根目录，不额外扩散规则写入行为。

## 9. 安全与性能设计

- 规则文件先 diff 再写入；
- 合并失败必须终止，不得产生半写入状态。

## 10. 测试设计

| 测试项 | 方式 |
|---|---|
| 空文件首次写入 | dry-run + 实装 |
| 既有文件 marker merge | diff |
| 冲突文件 blocked | 失败路径 |

## 11. 实施步骤

1. 增加规则文件检测；
2. 增加 marker merge；
3. 增加 merge report；
4. 增加 blocked 分支；
5. 对齐 dry-run 展示。

## 12. 风险、难点与预研建议

| 风险 | 应对 |
|---|---|
| 用户文件格式复杂 | 以 marker section 为最小可控边界 |
| 合并逻辑误判 | 先以 dry-run 明示，再允许写入 |

## 13. 回滚与发布策略

- merge 前读取原文件内容；
- 失败时不写入；
- 回滚以原文件备份或未写入为主。

## 14. Definition of Done

- [ ] user scope 支持 marker merge
- [ ] 存在 merge report
- [ ] 冲突时 blocked
