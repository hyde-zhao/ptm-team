# _templates — 因子库标准模板

## 用途

创建新的因子库时，从此目录复制模板到 `<library-name>/`，去除文件名中的 `.tmpl` 后缀。

## 使用方式

```bash
# 假设要创建 ngfw-dpi 因子库
cp _templates/factor-library.yaml.tmpl ngfw-dpi/factor-library.yaml
cp _templates/factor-library.md.tmpl ngfw-dpi/factor-library.md
cp _templates/factor-groups.md.tmpl ngfw-dpi/factor-groups.md
cp _templates/factor-change-log.md.tmpl ngfw-dpi/factor-change-log.md
```

## 模板说明

| 模板文件 | 用途 | 消费方 |
|----------|------|--------|
| `factor-library.yaml.tmpl` | 机器可读因子主库，含完整字段注释 | 安装器、ptm-tde、其他 Agent |
| `factor-library.md.tmpl` | 人读说明文件，因子总览表格 | 人工评审、横向对比 |
| `factor-groups.md.tmpl` | 因子组和覆盖策略 | 测试设计阶段的组合参考 |
| `factor-change-log.md.tmpl` | 变更记录 | 追溯和审计 |

## 注意事项

- `.tmpl` 文件中的注释标记 `# --- 注释 ---` 是指导性说明，创建实例时应删除或替换为实际内容
- `factor-library.yaml` 和 `factor-library.md` 必须保持内容一致
- 模板中的示例因子仅作格式参考，创建新库时替换为实际因子
