# 测试组网图

## 定位

本目录是 `ptm-team` 公共测试组网资源的 canonical source。组网图是仓库级 `resource`，供 `ptm-tde`（测试设计）和 `ptm-te`（测试执行）在场景设计和环境准备阶段消费。

## 目录

```
resource/network-topology/
├── README.md                        # 本文件
├── index.yaml                       # 组网拓扑索引
├── topology-spec.md                 # TGFW 产品测试组网方案和规范 v1.0-draft
├── topology-collection.md           # TGFW 测试组网图集合（Mermaid + YAML）
│
├── _templates/                      # 新增组网拓扑模板
│   └── README.md
└── _inbox/                          # 待入库的组网文件
    └── README.md
```

## 数据说明

### topology-spec.md

组网描述规范，定义测试组网的对象模型、描述格式和设计规范：

- 对象类型：DUT（被测设备）、TG（流量仪）、SW（交换机）、Mock（模拟对象）
- 描述格式：Mermaid 图 + YAML 属性描述
- 接口规范：统一 `port<N>` 命名，禁止使用 `eth0`/`eth1` 等

### topology-collection.md

覆盖全部测试场景的标准化逻辑 Topo 模板集合（node2 ~ node8），含：

- Mermaid 拓扑图（带样式）
- YAML 属性描述（节点、接口、链路）
- 适用场景说明

**命名约定**：`node{N}_dut{X}_tg{Y}_sw{Z}_mock{W}_link{L}`

## 使用方式

### 安装

安装 `ptm-tde` 或 `ptm-te` agent 时，安装器会将组网图资源同步安装到用户级公共资源目录：

```text
~/.ptm-team/resource/network-topology/
```

也可通过 `PTM_TEAM_RESOURCE_HOME` 指向团队共享资源目录。

## 维护

- 新增拓扑模板：参照 `topology-spec.md` 规范编写 Mermaid + YAML，追加到 `topology-collection.md`
- 修改规范：更新 `topology-spec.md` 并同步修正已有模板
- 待入库的原始文件放入 `_inbox/`

## 兼容消费者

| 消费者 | 资源 | 用途 |
|--------|------|------|
| ptm-tde | 组网图集合 | 场景设计中组网拓扑匹配与引用 |
| ptm-te | 组网图集合 + 规范 | 测试执行时的环境准备和拓扑映射 |
