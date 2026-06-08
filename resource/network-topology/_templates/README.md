# 模板目录

本目录存放新增组网拓扑的标准模板。

## 模板规范

组网拓扑模板需包含两部分：

### 1. Mermaid 拓扑图

```mermaid
%%{init: {'flowchart': {'curve': 'linear', 'nodeSpacing': 60, 'rankSpacing': 80}}}%%
flowchart LR
    classDef dut fill:#ffe8cc,stroke:#c46a00,stroke-width:1px,color:#111;
    classDef tg fill:#dff3ff,stroke:#0077a8,stroke-width:1px,color:#111;
    classDef sw fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px,color:#111;
    classDef mock fill:#f3e8ff,stroke:#7b1fa2,stroke-width:1px,color:#111;
    classDef port fill:#f5f5f5,stroke:#999,stroke-width:1px,color:#111;
```

### 2. YAML 属性描述

参照 `topology-spec.md` 中的对象模型定义（DUT/TG/SW/Mock/link）。

## 命名约定

`node{N}_dut{X}_tg{Y}_sw{Z}_mock{W}_link{L}`

## 提交流程

1. 按规范编写 Mermaid + YAML
2. 追加到 `topology-collection.md`
3. 更新 `index.yaml` 添加新条目
