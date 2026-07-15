# ptm-te · 测试执行工程师

> 状态：✅ v1 交付（CR-024，2026-07-10）· 所属项目：ptm-team · 设备管理 + 策略路由用例执行

## 角色定位

**ptm-tde 下游执行器**。消费 ptm-tde 产出的物理用例（PC），在真实设备上执行原子操作，编排用例解析、设备准备、login、逐条 op 执行、结果判定、用例清理和结果回写。采用与 ptm-tde 一致的编排器模式。

## v1 能力范围

| 能力 | 说明 | 状态 |
|------|------|------|
| 设备管理（精简核心） | 设备清单（devices.yaml）+ 型号映射 + SSH/Telnet 双轨连接 + 系统快照采集 | ✅ |
| 策略路由用例执行 | 基于 `ptm-atomic` CLI 消费 `fw_*` 原子操作（15 op_id / 5 族双层映射，CR-028 扩展后） | ✅ |
| 运行时验证 | hg3250-51 端到端 | ⏳ follow-up（T-01，需设备 + --execute 授权） |

## 编排流程

```
[1] 用例解析（cases/upload/<特性名>特性测试用例.md，提取 case_steps）
  -> [2] 设备准备（device-management 加载 devices.yaml + device-connection 连接探测 + 快照 before）
    -> [3] login 一次（ptm-atomic auth login，持久化 session.json，后续复用）
      -> [4] 逐条原子操作执行（op_mapper：op_id->子命令 + args->flag；干跑->执行->verify）
        -> [5] 结果判定（envelope: status + Check 点 vs expected_result）
          -> [6] 执行日志（结构化 JSONL）
            -> [7] 用例清理（inverse_op 回滚：config->delete；irreversible 类不回滚）
              -> [8] 快照 after + 结果回写（result.json + report.md）
```

## 专属 Skill

| Skill | 职责 | 脚本 |
|-------|------|------|
| `device-management` | 设备清单（devices.yaml）+ 型号映射查表（纯元数据，不含连接） | 无 |
| `device-connection` | SSH/Telnet 双轨连接 + 回退 + 系统快照采集（before/after） | ssh_exec.py / collect_sysinfo.py |
| `policy-route-execution` | op_id->子命令 + args->flag 双层映射 + 干跑/执行/verify + inverse_op 清理 | op_mapper.py |

## 安装

```shell
# 安装 ptm-te agent 及其 3 个 skill 到 Claude Code
ptm-team install claude --agent ptm-te

# 安装到 Codex / Qoder
ptm-team install codex --agent ptm-te
ptm-team install qoder --agent ptm-te

# 预览安装内容（不实际修改文件）
ptm-team install claude --agent ptm-te --dry-run
```

> 安装前需先安装 `ptm-atomic` CLI（`uv tool install git+ssh://...ptm-atomic.git` + `ptm-atomic sync`）。

## 使用

### 1. 配置设备清单

复制模板并填入设备信息（凭据用 `${ENV_VAR}` 占位，不入库明文）：

```shell
cp skills/device-management/templates/devices.yaml.example devices.yaml
cp .env.example .env  # 填入 FW_WEB_PASSWORD 等环境变量
```

### 2. 上传用例

将待执行的 PC 上传到 `cases/upload/`（ptm-te 执行入口，手写最小 PC 或复制 ptm-tde 产出 PC 到此）：

```
cases/upload/<特性名>特性测试用例.md
```

PC 需含结构化 `case_steps[].atomic_op.op_id` + `args` + `expected_result`（CR-019 契约）。

### 3. 执行用例

ptm-te agent 按编排流程 [1]-[8] 执行，产物写入 `runs/<run-id>/`：

```
runs/<run-id>/
  ├── parse-result.json     # 用例解析结果
  ├── snapshot-before/      # 设备快照 before
  ├── exec-log.jsonl        # 逐条 op 执行日志
  ├── snapshot-after/       # 设备快照 after
  ├── result.json           # 用例结果（机器可读）
  └── report.md             # 测试报告（人类可读）
```

### dry-run 默认门

首期默认 `--dry-run`（不真实修改设备）；`--execute` 写操作需单次授权（CP2 DQ-01）。

## 关键设计

| 设计 | 说明 |
|------|------|
| op_mapper 双层映射 | op_id->子命令（8 个）+ args->flag（7 op），三层命名翻译 centralize |
| login-once-reuse-session | auth login 一次，session.json 复用，STATE_INVALID 自动重连 |
| inverse_op 回滚 | config->delete 清理；update->restore_snapshot；reset-hitcount irreversible 不回滚 |
| 凭据管理 | devices.yaml 不入库明文，${ENV_VAR} 占位，--password-env 传 Web 密码 |

## 依赖

- 上游：ptm-tde（PC 产出，`ppdcs/delivery/`，用户复制到 `cases/upload/`）
- 外部：ptm-atomic CLI（`ptm-atomic run` 嵌套子命令）
- 下游：ptm-tae（未识别 op_id 反馈工具缺失）

## 演进路线

| Step | 能力 | 状态 |
|------|------|------|
| Step 1 v1 | 设备管理 + 策略路由用例执行（ptm-atomic CLI 版） | ✅ 交付（CR-024） |
| Step 1 v1.1 | runtime 端到端验证（hg3250-51 + --execute） | ⏳ T-01 follow-up |
| Step 2 | 真实消费 ptm-tde 产出 PC | ⏳ T-01 candidate |
| Step 3 | 进程管理 / 串口初始化 | ⏳ T-04 candidate |
| Step 4 | batch policy-route package 级编排 | ⏳ T-05 candidate |

## 相关文档

- Agent 定义：`agents/ptm-te.md`
- HLD：`process/HLD-CR-024.md`（v1.1）
- LLD：`process/stories/STORY-024-0*-LLD.md`
- 蓝图：`docs/ptm-team-blueprint.md`（v1.1）
- CR-024：`process/changes/CR-024-ptm-te-agent.md`
