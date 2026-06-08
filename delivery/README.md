# PTM Team 交付目录

本目录包含 `ptm-team install` 命令的安装交付物。

## 目录结构

```
delivery/
├── README.md           # 本文件
├── doc/                # 交付文档
│   └── USER-MANUAL.md  # 用户手册
├── agents/             # Agent 定义文件
│   ├── ptm-tde.md      # ✅ 已交付
│   ├── ptm-tm.md       # ⬜ 待开发
│   ├── ptm-tse.md      # ⬜ 待开发
│   ├── ptm-te.md       # ⬜ 待开发
│   ├── ptm-tae.md      # ⬜ 待开发
│   └── ptm-qa.md       # ⬜ 待开发
├── skills/             # Skill 定义文件（30+ 个）
├── rules/              # 规则文件
└── scripts/            # 安装/卸载脚本
```

## 当前交付状态

| Agent | 版本 | 状态 | 安装命令 |
|---|---|---|---|
| ptm-tde | v1.0 | ✅ 已交付 | `ptm-team install ptm-tde` |
| ptm-tm | — | ⬜ 未开始 | — |
| ptm-tse | — | ⬜ 未开始 | — |
| ptm-te | — | ⬜ 未开始 | — |
| ptm-tae | — | 🔄 Step 1 进行中 | — |
| ptm-qa | — | ⬜ 未开始 | — |

## ptm-tde 安装内容

`ptm-team install ptm-tde` 会安装以下内容到目标项目：

- `agents/ptm-tde.md` — 主 Agent 定义（12 步流程 + 5 个人工检查点）
- `skills/` 下全部 ptm-tde 专属 Skill（30+ 个）
- `resource/` 因子库资源文件
- 目标项目 `CLAUDE.md` 追加 ptm-tde 引用
- 目标项目 `skills/README.md` 更新 Skill 索引

## 相关文档

- 蓝图：`docs/ptm-team-blueprint.md`
- ptm-tde 用户手册：`docs/ptm-tde/USER-MANUAL.md`
- ptm-tde 发布说明：`docs/ptm-tde/RELEASE-NOTES.md`
- 部署检查清单：`docs/release/DEPLOY-CHECKLIST.md`
