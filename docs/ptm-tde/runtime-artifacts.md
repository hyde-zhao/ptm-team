# ptm-tde 运行产物契约

## 目录结构

```text
<feature-project-root>/
├── input/
├── analysis/
│   ├── feature-input/
│   ├── scenarios/
│   ├── m-analysis/
│   ├── f-analysis/
│   ├── q-analysis/
│   ├── integration/
│   ├── plan/
│   └── coverage/
├── design/
│   ├── ppdcs/
│   └── pc/
├── checkpoints/
├── delivery/
└── doc/STATE.yaml
```

## 输入

`input/` 放置原始输入，ptm-tde 不修改该目录。

推荐输入：

- 特性需求文件；
- 防火墙 topo 文件；
- 耦合矩阵；
- 外部接口、CLI 或工具方法参考资料。

## 分析产物

| 目录 | 内容 |
|---|---|
| `analysis/feature-input/` | 结构化需求与三~五级目录 |
| `analysis/scenarios/` | Scenario Chain、Topology、Action Source、Knowledge Reference |
| `analysis/m-analysis/` | M 分析测试点、PPDCS 标注、对象与因子 |
| `analysis/f-analysis/` | 耦合图、耦合测试点 |
| `analysis/q-analysis/` | 质量属性测试点 |
| `analysis/integration/` | 全量测试点、逻辑用例、测试数据、设计计划输入 |
| `analysis/plan/` | PPDCS 推断 reasoning |
| `analysis/coverage/` | 需求层与测试点层覆盖报告 |

## 设计产物

每个逻辑用例使用同一个 basename 输出两份设计文件：

```text
design/ppdcs/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
design/pc/<三级目录>-<四级目录>-<五级目录>-<逻辑用例名>.md
```

命名规则：

- 四段均来自已确认目录结构和 LC 名称；
- 去除路径分隔符和控制字符；
- 同名冲突追加 `-<LC-ID>`；
- 不创建 `design/<module>/<sub-module>/` 深目录。

## 交付产物

`delivery/` 只输出：

```text
<特性名>特性测试方案.md
<特性名>特性测试用例.md
```

测试方案是分析过程总结；测试用例是所有测试用例总表。

