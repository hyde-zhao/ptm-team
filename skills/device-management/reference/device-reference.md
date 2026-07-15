# 设备型号对照表

硬件系列到 TGFW 型号的完整映射，用于添加设备时确定 `device_type`。

> 来源：迁移自 manaul `reference/device-reference.md`，补充型号特征（CPU 平台 / 内存 / 硬盘）用于消歧。
> 本表是只读参考，不执行任何操作。

## 完整对照表

| 硬件系列 | 硬件等价类 | CPU 平台 | 操作系统 | TLS 型号 | IPS 型号 | SM 型号 | 渠道型号 | 型号特征（消歧用） | 备注 |
|----------|-----------|----------|----------|----------|----------|--------|----------|-------------------|------|
| nxp1043 | nxp1043-4g-无盘 | ARM | ubuntu | DAS-TGFW-160 | | | | 4G 内存 / 无盘 | 无盘 |
| nxp1043 | nxp1043-8g | ARM | ubuntu | DAS-TGFW-160-PRO | | | | 8G 内存 / 有 msata | 有 msata 的 160 |
| nxp1043 | nxp1043-8g | ARM | ubuntu | DAS-TGFW-290 | | DAS-TGFW-200-BM | 8G 内存 / 有 msata 无硬盘 | 安恒防火墙（千兆） |
| nxp1043 | nxp1043-8g | ARM | ubuntu | DAS-TGFW-490 | | | 8G 内存 / 有硬盘 | 通用 1043，有硬盘 |
| nxp1043 | nxp1043-8g | ARM | ubuntu | DAS-TGFW-690 | | DAS-TGFW-600-BM | 8G 内存 / 有硬盘 | 安恒防火墙（千兆） |
| nxp1046 | nxp1046-16g | ARM | ubuntu | DAS-TGFW-890 | | | 16G 内存 | |
| nxp1046 | nxp1046-16g | ARM | ubuntu | DAS-TGFW-1900 | | | 16G 内存 | 项目已有 nxp1046-95 |
| nxp1046 | nxp1046-16g | ARM | ubuntu | DAS-TGFW-1950 | | | 16G 内存 | |
| nxp1046 | nxp1046-16g | ARM | ubuntu | DAS-TGFW-2900 | | DAS-TGFW-2000-BM | 16G 内存 | 老 NXP1046-2U，安恒防火墙（万兆） |
| C3758R | C3758 | X86 | Centos, Das-os-x86 | DAS-TGFW-2900 | | | X86 / das-os 用 HG 包 | das-os 使用 HG 安装包 |
| C3758R | C3758 | X86 | Centos, Das-os-x86 | DAS-TGFW-2950 | | | X86 / das-os 用 HG 包 | das-os 使用 HG 安装包 |
| C3758R | C3758 | X86 | Centos, Das-os-x86 | DAS-TGFW-3900 | | | X86 / das-os 用 HG 包 | das-os 使用 HG 安装包 |
| C3758R | C3758 | X86 | Centos, Das-os-x86 | DAS-TGFW-3950 | | | X86 / das-os 用 HG 包 | das-os 使用 HG 安装包 |
| C3758R | C3758 | X86 | Centos, Das-os-x86 | DAS-TGFW-4900 | | | X86 / das-os 用 HG 包 | das-os 使用 HG 安装包 |
| C236 | C236 | X86 | Centos | DAS-TGFW-5900 | | | X86 | |
| C236 | C236 | X86 | Centos | DAS-TGFW-6900 | | | X86 | |
| EP | EP | X86 | Centos | DAS-TGFW-8900 | | | X86 | |
| EP | EP | X86 | Centos | DAS-TGFW-10900 | | | X86 | |
| EP | EP | X86 | Centos | DAS-TGFW-12900 | | DAS-TGFW-12000-BM | X86 | 安恒防火墙（万兆） |
| 华电飞腾 | HD-D2000 | 飞腾（FT） | Das-os-arm | DAS-TGFW-A1200-FU | | DAS-TGFW-A1000-BM | 飞腾 / 无硬盘 | 老飞腾，安恒防火墙（千兆） |
| 华电飞腾 | HD-D2000 | 飞腾（FT） | Das-os-arm | DAS-TGFW-A1280-FU | | DAS-TGFW-A2000-BM | 飞腾 / 无硬盘 | 老飞腾，安恒防火墙（千兆） |
| 杰伦海光 | JL-HG | 海光（HG） | Das-os-x86 | DAS-TGFW-A1500-HU | | DAS-TGFW-A4000-BM | 海光 / 有硬盘 | 老海光，安恒防火墙（万兆） |
| 乐研E2000Q | E2000Q | 飞腾（FT） | Das-os-arm | DAS-TGFW-A100-FU | | DAS-TGFW-A100-BM | DAS-TGFW-A160-FU | 飞腾 / 无盘 | 安恒防火墙（千兆） |
| 乐研E2000Q | E2000Q | 飞腾（FT） | Das-os-arm | DAS-TGFW-A200-FU | DAS-IPS-G500-FU | DAS-TGFW-A200-BM | DAS-TGFW-A260-FU | 飞腾 / 8G | 安恒防火墙（千兆） |
| 乐研E2000Q | E2000Q | 飞腾（FT） | Das-os-arm | DAS-TGFW-A400-FU | | DAS-TGFW-A400-BM | DAS-TGFW-A460-FU | 飞腾 / 8G | 安恒防火墙（千兆） |
| 乐研E2000Q | E2000Q | 飞腾（FT） | Das-os-arm | DAS-TGFW-A600-FU | DAS-IPS-G1000-FU | | DAS-TGFW-A660-FU | 飞腾 / 8G | |
| 乐研E2000Q | E2000Q | 飞腾（FT） | Das-os-arm | DAS-TGFW-A800-FU | | DAS-TGFW-A800-BM | DAS-TGFW-A860-FU | 飞腾 / 16G | 安恒防火墙（千兆） |
| 乐研D2000 | D2000 | 飞腾（FT） | Das-os-arm | DAS-TGFW-A1200-FU | DAS-IPS-G3000-FU / DAS-IPS-G5000-FU | | | 飞腾 | |
| 乐研D2000 | D2000 | 飞腾（FT） | Das-os-arm | DAS-TGFW-A1280-FU | DAS-IPS-G8000-FU | | | 飞腾 | |
| 乐研海光3250 | HG3250 | 海光（HG） | Das-os-x86 | DAS-TGFW-A1300-HU | | | | 海光 3250-40G | 项目已有 hg3250-51/52 |
| 乐研海光3250 | HG3250 | 海光（HG） | Das-os-x86 | DAS-TGFW-A1500-HU | DAS-IPS-G10000-HU | | | 海光 3250-40G | |
| 乐研海光3250 | HG3250 | 海光（HG） | Das-os-x86 | DAS-TGFW-A1580-HU | | | | 海光 3250-60G | |
| 乐研海光3250 | HG3250 | 海光（HG） | Das-os-x86 | DAS-TGFW-A1600-HU | | | | 海光 3250-60G | |
| 乐研海光5380 | HG5380 | 海光（HG） | Das-os-x86 | DAS-TGFW-A1800-HU | DAS-IPS-G20000-HU / DAS-IPS-G30000-HU | | | 海光 5380 | |
| 乐研海光5380 | HG5380 | 海光（HG） | Das-os-x86 | DAS-TGFW-A2200-HU | DAS-IPS-G40000-HU | | | 海光 5380 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFWV4000 | | | | X86 / C00SPC512 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S100-GZ | | | | X86 / C00SPC657 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S200-GZ | | | | X86 / C00SPC657 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S400-GZ | | | | X86 / C00SPC657 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S600-GZ | | | | X86 / C00SPC657 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S800-GZ | | | | X86 / C00SPC657 | |
| 天池云 | 天池云 | X86 | Centos | DAS-TGFW-S1000-GZ | | | | X86 / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S100-KU-GZ | | | | ARM / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S200-KU-GZ | | | | ARM / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S400-KU-GZ | | | | ARM / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S600-KU-GZ | | | | ARM / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S800-KU-GZ | | | | ARM / C00SPC657 | |
| 华为鲲鹏 | 华为鲲鹏 | ARM | ubuntu | DAS-TGFW-S1000-KU-GZ | | | | ARM / C00SPC657 | |

## 硬件系列 -> device_type 快速索引

| 硬件系列 | 可选 TGFW 型号 |
|----------|---------------|
| nxp1043 | DAS-TGFW-160, DAS-TGFW-160-PRO, DAS-TGFW-290, DAS-TGFW-490, DAS-TGFW-690 |
| nxp1046 | DAS-TGFW-890, DAS-TGFW-1900, DAS-TGFW-1950, DAS-TGFW-2900 |
| C3758R | DAS-TGFW-2900, DAS-TGFW-2950, DAS-TGFW-3900, DAS-TGFW-3950, DAS-TGFW-4900 |
| C236 | DAS-TGFW-5900, DAS-TGFW-6900 |
| EP | DAS-TGFW-8900, DAS-TGFW-10900, DAS-TGFW-12900 |
| 华电飞腾 | DAS-TGFW-A1200-FU, DAS-TGFW-A1280-FU |
| 杰伦海光 | DAS-TGFW-A1500-HU |
| 乐研E2000Q | DAS-TGFW-A100-FU, DAS-TGFW-A200-FU, DAS-TGFW-A400-FU, DAS-TGFW-A600-FU, DAS-TGFW-A800-FU |
| 乐研D2000 | DAS-TGFW-A1200-FU, DAS-TGFW-A1280-FU |
| 乐研海光3250 | DAS-TGFW-A1300-HU, DAS-TGFW-A1500-HU, DAS-TGFW-A1580-HU, DAS-TGFW-A1600-HU |
| 乐研海光5380 | DAS-TGFW-A1800-HU, DAS-TGFW-A2200-HU |
| 天池云 | DAS-TGFWV4000, DAS-TGFW-S100-GZ ~ DAS-TGFW-S1000-GZ |
| 华为鲲鹏 | DAS-TGFW-S100-KU-GZ ~ DAS-TGFW-S1000-KU-GZ |

## manaul 现有设备型号覆盖（DoD-12 校验基线）

| manaul 设备名 | 硬件系列 | device_type | 是否覆盖 |
|--------------|----------|-------------|:--------:|
| hg3250-51 | 乐研海光3250 | DAS-TGFW-A1300-HU | 是 |
| hg3250-52 | 乐研海光3250 | DAS-TGFW-A1300-HU | 是 |
| nxp1046-95 | nxp1046 | DAS-TGFW-1900 | 是 |
| 160pro-32 | nxp1043 | DAS-TGFW-160-PRO | 是 |
| 160-31 | nxp1043 | DAS-TGFW-160 | 是 |
| nxp290-171 | nxp1043 | DAS-TGFW-290 | 是 |
| nxp290-172 | nxp1043 | DAS-TGFW-290 | 是 |
| TG-C236 | C236 | trex-236 | 是（流量仪，非 TGFW 型号） |
| TG-J1900 | EP | （待补充） | 待补充 |

## 默认匹配规则

当用户只提供硬件系列但未说明具体型号时：

- **nxp1043** -> `DAS-TGFW-160-PRO`（最常用，有 msata）
- **nxp1046** -> `DAS-TGFW-1900`（项目已有 nxp1046-95）
- **乐研海光3250** -> `DAS-TGFW-A1300-HU`（项目已有 hg3250-51/52）
- **天池云** -> `DAS-TGFW-S400-GZ`（中间型号）
- **华为鲲鹏** -> `DAS-TGFW-S400-KU-GZ`（中间型号）
- **其他** -> 取该系列第一个型号

## 型号冲突说明

以下 TLS 型号对应多个硬件系列，需根据型号特征列区分：

- `DAS-TGFW-2900`：nxp1046（ARM/16G）和 C3758R（X86/das-os）都有
- `DAS-TGFW-A1200-FU`：华电飞腾 和 乐研D2000 都有
- `DAS-TGFW-A1280-FU`：华电飞腾 和 乐研D2000 都有
- `DAS-TGFW-A1500-HU`：杰伦海光 和 乐研海光3250 都有

## 添加新设备时的查表说明

1. 先按硬件系列在"快速索引"中定位候选型号列表
2. 若候选唯一，直接取该型号
3. 若候选多个，按"型号特征"列（CPU 平台 / 内存 / 硬盘 / 接口速率）与实际设备匹配
4. 仍无法确定时询问用户提供 CPU 平台或内存信息
5. 确定后写入 `devices.yaml` 的 `device_type` 字段
