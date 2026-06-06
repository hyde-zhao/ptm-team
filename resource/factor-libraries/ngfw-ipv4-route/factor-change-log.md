# {Domain Name}因子库变更记录

> 复制此文件到 `<library-name>/factor-change-log.md`，删除 `.tmpl` 后缀
> change_type 必须使用以下枚举值之一

## change_type 枚举

| change_type | 含义 | 适用场景 |
|-------------|------|----------|
| `new_factor` | 新增因子 | 在库中添加全新因子 |
| `extend_factor_values` | 扩展因子取值 | 在 enum/range 中增加新值 |
| `extend_factor_samples` | 扩展因子样本 | 增加新的 sample_definition |
| `extend_usage_profiles` | 扩展样本用途配置 | 修改 usage_profiles |
| `add_constraints` | 新增约束 | 添加新的 require/forbid/allowed_values |
| `new_factor_group` | 新增因子组 | 定义新的因子组合覆盖目标 |
| `extend_factor_group` | 扩展因子组 | 在已有组中增删因子 |
| `deprecate_factor` | 废弃因子 | 标记因子不再推荐使用 |
| `merge_factors` | 合并因子 | 多个因子合并为一个 |
| `split_factor` | 拆分因子 | 一个因子拆分为多个 |
| `split_responsibility` | 职责拆分 | 将混用的因子按职责分离（如配置字段/运行时输入分离） |
| `schema_change` | Schema 变更 | 修改因子库结构本身的定义 |

## 变更记录

| change_id | date | change_type | factor_id | summary | review_status |
|-----------|---|---|---|---|---|
| {FL-INIT-001} | {YYYY-MM-DD} | new_factor | {FAC-ID} | {变更摘要，说明什么变更、为什么、影响范围} | candidate |

---

## 变更详细说明（按需填写）

### {change_id}: {变更标题}

**变更前状态**：
- {变更前是什么样的}

**变更后状态**：
- {变更后是什么样的}

**原因**：
- {为什么要做这个变更}

**影响**：
- {哪些下游方法或消费方受影响}
- {是否需要更新 factor_bindings 或 factor_groups}

**迁移指南**（如涉及废弃或拆分）：
- {旧因子 → 新因子的迁移路径}
