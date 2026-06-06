# _proposals — 候选因子提案区

## 用途

存放从原始材料中提取的候选测试因子，等待进一步建模和评审。

候选因子的来源：
- `_inbox/` 中 Excel/CSV 提取的变量
- 需求分析中发现的遗漏因子
- 缺陷回溯中识别的缺失覆盖
- 从历史项目回流的新因子提案

## 候选因子最小信息集

每个候选因子提案件必须包含以下信息：

```yaml
# ── 必填 ──
factor_id: FAC-{DOMAIN}-{NAME}    # 提议的因子 ID
factor_name: "中文名称"            # 人读名称
description: "因子简要描述"         # 1-2 句说明这个因子是什么
source: "来源文件或出处"            # 从哪个 Excel/文档提取

# ── 初步建模（可留为 TODO 或写初步判断）──
owner_object: OBJ-???              # 所属被测对象
factor_kind: ???                   # data|control|constraint|state|oracle|condition
design_role: ???                   # driver|constraint|oracle
domain_model: ???                  # enum|range|ip_address|string_pattern|state
candidate_values: []               # 候选取值列表（从原始材料提取）
notes: "补充说明"                  # 不确定的地方、需要确认的事项

# ── 状态 ──
status: proposed                   # proposed|candidate|rejected|deferred
proposal_date: YYYY-MM-DD
```

## 文件格式

提案可以按来源组织为单个文件，或按领域聚合为一个文件：

```
_proposals/
├── README.md                                  # 本文件
├── from-tgfw-policy-routing.xlsx.yaml         # 从某个 Excel 提取的所有候选
├── from-defect-analysis.yaml                  # 从缺陷分析提取的候选
└── ngfw-dpi-candidates.yaml                   # 按领域聚合的候选
```

## 去重检查

提交候选因子前，必须执行以下去重检查：

1. **ID 去重**：`factor_id` 是否与发布区已有因子冲突
2. **语义去重**：通过 `factor_name` / `aliases` / `owner_object` 判定是否与已有因子重复
3. **分组查重**：该因子是否可以归入已有 `factor_group`

判定结果：

| 判定 | 条件 | 下一步 |
|------|------|--------|
| `reuse` | 发布区已有等价因子 | 无需新增，记录复用关系 |
| `extend` | 发布区已有但需扩展取值/样本/约束 | 记录扩展提案，评审后进入 `<library>/` |
| `new_factor` | 发布区和研究区均无等价因子 | 进入 `<library>/factor-library.yaml` |
| `new_group` | 多个 new_factor 形成新的覆盖组合 | 同时创建因子组定义 |
| `reject` | 不满足公共因子复用条件 | 记录拒绝原因 |
| `defer` | 信息不足，暂时搁置 | 记录待确认事项，后续补齐 |

## 审批后流程

1. 通过审批的候选因子，**迁移**到 `<library-name>/factor-library.yaml`
2. 在 `<library-name>/factor-change-log.md` 中记录新增
3. 在候选提案文件中标注 `status: candidate` 和迁移目标
4. 可选：删除已迁移的提案，或保留标记为 `DONE-` 前缀
