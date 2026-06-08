# 模板目录

本目录存放新增耦合矩阵的标准模板。当需要提交新的耦合矩阵（如新版本、新产品线）时，请参照以下模板。

## 模板文件

> 模板文件待补充。当下游消费者（ptm-tde）的 F 分析流程稳定后，可从此处沉淀标准化模板。

## 提交流程

1. 将原始 Excel 放入 `_inbox/`
2. 参照 `tgfw-coupling-matrix.yaml` 的输出格式编写对应的 YAML
3. 更新 `index.yaml` 添加新条目
4. 更新 `component-resource-links.yaml` 声明新的消费关系
