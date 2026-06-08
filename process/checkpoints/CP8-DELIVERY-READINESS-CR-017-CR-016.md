---
checkpoint: "CP8-manual"
type: "auto_precheck_then_manual"
status: "approved"
approved_by: "user"
approved_at: "2026-06-06T00:00:00+08:00"
cr_ids: ["CR-017-factor-library-discovery-gap", "CR-016-atomic-ops-consumption-gap"]
created_at: "2026-06-06T00:00:00+08:00"
owner: "meta-po（po-zhao）"
---

# CP8：CR-017 + CR-016 联合交付就绪人工终验

## 自动预检摘要

| CR | 预检结果 | 详情 |
|----|:--:|------|
| CR-017 | **PASS 12/12** | `process/checks/CP8-DELIVERY-READINESS-CR-017.md` |
| CR-016 | **PASS 14/14** | `process/checks/CP8-DELIVERY-READINESS-CR-016.md` |

---

## Decision Brief

### 变更总览

| CR | 问题 | 修复 | 提交 | 文件 | 行数 |
|----|------|------|------|:--:|:--:|
| CR-017 | 9 个因子库只扫 2 个，18/35 假阳性 | Step 1.5 因子库清单加载 + match_confidence 分级 | `befeeb3` | 3 | +113/-13 |
| CR-016 | 原子操作无 CLI 查询，3 个误标候选 | Step 1.6 CLI 查询 + L1-L4 五维语义匹配（atomic-ops aliases） | `24c0a0b` `44e8aa1` `f3e7a73` | 5 | +216/-48 |

### 修复效果

```
修复前                              修复后
─────────────────────────────────────────────
因子库扫描: 2/9 (22%)               9/9 (100%)
因子假阳性: 18/35 (51%)             0
原子操作: fw_config_subinterface    → fw_config_interface (L3-weak, score=3.8)
          fw_config_trunk_interface  → fw_config_interface (L3-weak, score=3.8)
          fw_config_lag_interface    → fw_config_interface (L3-weak, score=3.8)
```

### 基础设施新增

```
mfq/
├── factor-usage/              # CR-017
│   └── factor-library-lock.yaml
└── atomic-op-usage/           # CR-016
    ├── atomic-op-lock.yaml
    ├── atomic-op-bindings.yaml
    └── atomic-op-resolution-report.md
```

### 关键设计决策

| 决策 | 结论 |
|------|------|
| 因子库发现方式 | index.yaml 驱动，全量遍历（不再用路径回退） |
| candidate 因子策略 | match_confidence=medium，可匹配但需下游确认 |
| 语义匹配算法 | 五维加权分词重叠：op_id 3.0 + desc 1.0 + tags 2.0 + aliases 1.5 + params 1.5 |
| 别名数据来源 | atomic-ops list --format json → aliases 字段（32/79 ops） |
| CLI 降级行为 | WARNING + 回退 L1 精确匹配，不阻断 |
| 同义词维护 | 零 ptm-team 维护，全部由 atomic-ops 仓库定义 |

---

## 待人工决策

| 决策 ID | 类型 | 问题 | 推荐 | 备选 |
|---------|------|------|------|------|
| **CP8-DQ-01** | scope | CR-017 交付就绪确认 | **approve**：确认交付，关闭 CR-017 | 修改 / reject |
| **CP8-DQ-02** | scope | CR-016 交付就绪确认 | **approve**：确认交付，关闭 CR-016 | 修改 / reject |
| **CP8-DQ-03** | follow_up_tracking | CR-016 aliases 补齐：atomic-ops 剩余 47 个无歧义 op 按需补充 aliases（规则：新增 op 有子类型参数→必须写 aliases） | **确认进入台账** | 立即创建正式 CR / 丢弃 |

---

## 不授权项

- 不授权在未完成 atomic-ops aliases 规范落地前关闭 CR-016 台账 T-01
- 不授权删除或降级 CR-017 的 Step 1.5 和 CR-016 的 Step 1.6
- 不授权修改 mfq/factor-usage/ 和 mfq/atomic-op-usage/ 目录结构

---

## 回复选项

- **`approve`** — 接受全部推荐方案，CR-017 + CR-016 确认交付
- **`修改: <决策ID>=<具体修改点>`** — 调整单项
- **`reject`** — 驳回

---

## 人工审查结果

| 决策 ID | 用户结论 | 备注 |
|---|---|---|
| CP8-DQ-01（CR-017 交付） | `approved` | — |
| CP8-DQ-02（CR-016 交付） | `approved` | — |
| CP8-DQ-03（aliases 台账） | `approved` | 进入台账跟踪 |

| 字段 | 值 |
|---|---|
| 审查人 | user |
| 审查时间 | 2026-06-06 |
| 最终结论 | **APPROVED** — CR-017 + CR-016 交付就绪，全部关闭 |
