# 因子库候选回流区

项目运行期间发现的新因子、值域扩展、样本扩展或约束扩展，先由 `ptm-tde` 写入特性项目：

```text
analysis/factor-usage/candidate-factor-proposals.yaml
```

公共库维护者评审后，才将候选提案回流到本目录并合并进 `resource/factor-libraries/<library_id>/`。

## 回流流程

1. 收集项目候选提案。
2. 按 `factor_id / factor_name / aliases / owner_object / factor_group` 去重。
3. 判定处理方式：`reuse / extend / new_factor / new_group / reject / defer`。
4. 更新目标公共库、change log、index 版本和 checksum。
5. 必要时生成 `snapshots/<snapshot_id>/`。
