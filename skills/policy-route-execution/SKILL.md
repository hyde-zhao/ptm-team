---
name: policy-route-execution
description: 通过 ptm-atomic CLI 执行策略路由原子操作（config/update/delete/verify/priority/reset-hitcount/verify-hitcount），含 op_id->子命令 + args->flag 双层映射、干跑/执行/verify 三阶段、STATE_INVALID 自动重连和 inverse_op 回滚清理
argument-hint: "<op_id> [--dry-run | --execute] | validate | map"
user-invokable: true
status: active
---

# policy-route-execution

## 目标

本 Skill 通过 `ptm-atomic` CLI 执行 NGFW 策略路由原子操作，为 ptm-te 测试执行工程师提供：

- **双层映射翻译**：op_id -> CLI 子命令（第一层）+ args -> CLI flag（第二层），centralize 三层命名翻译（ptm-tde PC args / op yaml params / CLI flag）
- **三阶段执行**：干跑（dry-run）-> 执行（execute，需授权）-> 验证（verify）
- **STATE_INVALID 自动重连**：session 失效时自动重新 auth login 并重试 1 次
- **inverse_op 回滚清理**：按 op 的 rollback 策略执行清理（inverse_op / restore_snapshot / irreversible 豁免 / none）

核心脚本：`scripts/op_mapper.py`（双层映射 + 执行 + 回滚 + 一致性校验）。

## 前置条件

1. **ptm-atomic 已安装且已 sync**：`ptm-atomic --version` 可执行，`ptm-atomic list | grep policy_route` 返回 7 个 policy-route op
2. **auth login 已完成**：session.json 可用（`ptm-atomic run --base-url <url> auth login --username admin --password-env FW_WEB_PASSWORD --session-file <path> --execute`）
3. **环境变量已设置**：`FW_WEB_PASSWORD` 等凭据环境变量已导出
4. **设备可达**：目标 NGFW 设备 Web 管理地址 HTTPS 可达

## 双层映射表

### 第一层：op_id -> CLI 子命令（8 个）

CLI 格式：`ptm-atomic run --base-url <url> [--session-file <path>] --format json <family> <action> [flags] [--execute]`

真相源：`run_policy_route.py` `build_subtree()` + `run_auth.py`

| op_id（ptm-tde PC） | family | action | side_effect | rollback（ptm-atomic list 实测） | idempotent |
|---|---|---|---|---|---|
| `fw_login_web_management` | `auth` | `login` | observation | （空，建立 session，只读） | true |
| `fw_config_policy_route` | `policy-route` | `config` | state_mutation | `inverse_op:fw_delete_policy_route` | true |
| `fw_update_policy_route` | `policy-route` | `update` | state_mutation | `restore_snapshot` | true |
| `fw_delete_policy_route` | `policy-route` | `delete` | destructive | `restore_snapshot` | false |
| `fw_verify_policy_route` | `policy-route` | `verify` | observation | （空，只读） | true |
| `fw_update_policy_route_priority` | `policy-route` | `priority` | （空） | （空，无 rollback 元数据） | true |
| `fw_reset_policy_route_hitcount` | `policy-route` | `reset-hitcount` | state_mutation | `irreversible` | true |
| `fw_verify_policy_route_hitcount` | `policy-route` | `verify-hitcount` | observation | （空，只读） | true |

### 第二层：args -> CLI flag（7 个 op + login）

真相源：`run_policy_route.py` `_add_*_args()` + op yaml `inputs.params` + `ptm-atomic run ... --help`

#### 三层命名不一致对照

| ptm-tde PC `args` | op yaml `inputs.params` | CLI flag | 三层是否一致 |
|---|---|---|---|
| `src_addr` | `source_network` | `--source-network` | 否（三层各不同） |
| `dst_addr` | `dst_network` | `--dst-network` | 否（第 1 层不同） |
| `next_hop` | `next_hop_ip` | `--next-hop-ip` | 否（第 1 层不同） |
| `in_interface` | `in_interface` | `--in-interface` | 否（第 3 层用连字符） |
| `type` | `type` | `--policy-route-type` | 否（第 3 层加前缀） |
| `id` | `id` | `--id` | 是 |
| `page` | - | `--page` | 是（CLI 分页参数） |
| `size` | - | `--size` | 是（CLI 分页参数） |
| `moveid` | - | `--moveid` | 是 |
| `targetid` | - | `--targetid` | 是 |
| `targetsite` | - | `--targetsite` | 是 |

#### 各 op 的 args -> flag 映射

**config / update**（`_add_common_args`）：

| args key | CLI flag | required | 说明 |
|---|---|---|---|
| `src_addr` | `--source-network` | 是 | 源地址对象或地址组名 |
| `dst_addr` | `--dst-network` | 否（默认 any） | 目的地址对象或地址组名 |
| `next_hop` | `--next-hop-ip` | 否 | 下一跳 IP |
| `in_interface` | `--in-interface` | 是 | 入接口 |
| `type` | `--policy-route-type` | 否（默认 ipv4） | 地址族（ipv4/ipv6） |
| `id` | `--id` | update 必需 | 策略路由 ID（优先从 config 响应 `data.policy_route_id` 取，verify 查询兜底） |

**delete / reset-hitcount**（`_add_delete_args`）：

| args key | CLI flag | required | 说明 |
|---|---|---|---|
| `id` | `--id` | 是 | 策略路由 ID |
| `type` | `--policy-route-type` | 否（默认 ipv4） | 地址族 |

**verify / verify-hitcount**（`_add_verify_args`）：

| args key | CLI flag | required | 说明 |
|---|---|---|---|
| `type` | `--policy-route-type` | 否（默认 ipv4） | 地址族 |
| `page` | `--page` | 否（默认 1） | 分页页码 |
| `size` | `--size` | 否（默认 40） | 分页大小 |

**priority**（`_add_priority_args`）：

| args key | CLI flag | required | 说明 |
|---|---|---|---|
| `type` | `--policy-route-type` | 否（默认 ipv4） | 地址族 |
| `moveid` | `--moveid` | 是 | 移动的路由 ID |
| `targetid` | `--targetid` | 是 | 目标路由 ID |
| `targetsite` | `--targetsite` | 是 | 目标位置（before/after/first/last） |

**login**（`run_auth.py`）：

| args key | CLI flag | required | 说明 |
|---|---|---|---|
| `username` | `--username` | 否 | 用户名 |
| `password_env` | `--password-env` | 否（默认 FW_WEB_PASSWORD） | 密码环境变量名 |

## 执行流程（干跑 -> 执行 -> verify）

ptm-te agent 对每条 state_mutation 类 op 的三阶段执行：

### 阶段 1：干跑（dry-run）

```python
envelope = execute_op(op_id, args, base_url, session_file, dry_run=True)
# 验证参数路由和 session 有效性
# envelope.status == "success" -> 进入阶段 2
# envelope.status == "error" -> 阻塞，不进入执行
```

### 阶段 2：执行（execute，需 authorized=True）

```python
envelope = execute_op(op_id, args, base_url, session_file, dry_run=False, authorized=True)
# 真实写操作，设备策略变更
# STATE_INVALID -> 自动重连重试（最多 1 次）
# envelope.status == "success" -> 进入阶段 3
# envelope.status == "error" -> 记录错误，准备回滚
```

### 阶段 3：验证（verify）

```python
envelope = execute_op("fw_verify_policy_route", {"type": "ipv4", "page": 1, "size": 40},
                      base_url, session_file, dry_run=False, authorized=True)
# 查询设备当前策略路由状态
# 与 expected_result 比对判定 Check 点
```

> observation 类 op（verify / verify-hitcount）和 login 只执行阶段 1 或直接 execute（只读无副作用）。

### 命令示例

**config dry-run**：
```bash
ptm-atomic run --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --format json \
  policy-route config \
  --source-network <IP_ADDRESS>/24 --dst-network any --next-hop-ip 18.18.2.2 \
  --in-interface GE0_12 --policy-route-type ipv4
```

**config execute**：
```bash
ptm-atomic run --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --format json \
  policy-route config \
  --source-network <IP_ADDRESS>/24 --dst-network any --next-hop-ip 18.18.2.2 \
  --in-interface GE0_12 --policy-route-type ipv4 --execute
```

**delete execute（inverse_op 清理）**：
```bash
ptm-atomic run --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --format json \
  policy-route delete --id 15 --policy-route-type ipv4 --execute
```

**auth login（重连）**：
```bash
ptm-atomic run --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --format json \
  auth login --username admin --password-env FW_WEB_PASSWORD --execute
```

## 回滚策略（inverse_op / restore_snapshot / irreversible 豁免 / none）

用例执行后，`handle_rollback` 按 op 的 rollback 策略清理：

| rollback 类型 | 策略 | 示例 op | 清理动作 |
|---|---|---|---|
| `inverse_op` | 执行 inverse_op 清理 | `fw_config_policy_route` | 执行 `fw_delete_policy_route`（id 经 `ptm-atomic show` 读 `rollback_strategy.id_source` 声明按 4 模式解析：response/args/query/placeholder） |
| `restore_snapshot` | 按 before 快照恢复 | `fw_update_policy_route` | 按 `pre_snapshot.full_config` 恢复原值 |
| `restore_snapshot`（as_cleanup_skip） | 作为清理动作时不触发回滚 | `fw_delete_policy_route` | 跳过（它本身就是清理动作） |
| `irreversible` | **不回滚**，豁免注明 | `fw_reset_policy_route_hitcount` | 返回 `rollback=waived`，用例设计者需接受副作用 |
| `none` | 不需回滚（只读或无元数据） | `fw_verify_policy_route` / `fw_verify_policy_route_hitcount` / `fw_login_web_management` / `fw_update_policy_route_priority` | 返回 `rollback=not_required` |

### irreversible 豁免说明

`fw_reset_policy_route_hitcount` 是 `irreversible`（命中计数清零不可恢复）。ptm-te **不强行回滚**此类步骤。用例设计者需：
- 接受该副作用，或
- 通过用例顺序规避（如 reset 放在用例末尾）

## 错误表

### error_type 取值表

| error_type | 含义 | op_mapper 处理 | 调用方（ptm-te）后续动作 |
|---|---|---|---|
| `NONE` | 成功 | 无错误 | 继续下一步 |
| `STATE_INVALID` | session 失效 | 自动重连 auth login + 重试 1 次 | 重连失败则终止用例 |
| `OP_NOT_FOUND` | op_id 未在映射表中 | 阻塞，返回错误 envelope | 阻塞该 step，反馈 ptm-tae 检查工具覆盖 |
| `EXEC_FAILED` | subprocess 执行失败 / 超时 / 未授权 | 返回错误 envelope | 记录错误，准备回滚或终止 |
| `VALIDATION_FAILED` | 参数校验失败（required flag 缺失等） | 返回错误 envelope | 阻塞，检查 PC args |
| `CONFIG_REJECTED` | 设备拒绝配置 | 返回错误 envelope | 见下方子错误码 |
| `DEVICE_UNREACHABLE` | 设备不可达 | 返回错误 envelope | 降级 dry-run-only 或终止 |
| `AUTH_FAILED` | 登录失败（重连时） | 终止，不重试 | 终止用例 |
| `UNKNOWN_ERROR` | 未知错误（输出无法解析等） | 返回错误 envelope | 记录错误，人工排查 |

### CONFIG_REJECTED 子错误码

| 子错误码 | 含义 | 处理方式 |
|---|---|---|
| `ePolicyRouteInIfModeError` | 入接口非路由模式 | 需人工 Web 修改接口为路由模式后重试。op_mapper 不自动修复。 |

## Gotchas

1. **CLI 名是 `ptm-atomic` 不是 `atomic-ops`**：Python 模块叫 `atomic_ops`，但命令名是 `ptm-atomic`。旧 SKILL 用 `atomic-ops run` 会报 command not found。op_mapper 硬编码 `ptm-atomic`。

2. **扁平格式硬报错**：`ptm-atomic run fw_config_policy_route` 报 `invalid choice`，无 deprecated warning。必须用嵌套子命令 `ptm-atomic run --base-url <url> policy-route config`。op_mapper 的 `build_command` 生成嵌套格式。

3. **三层命名不一致**：ptm-tde PC `src_addr` ≠ op yaml `source_network` ≠ CLI `--source-network`。op_mapper 的 `ARGS_TO_FLAGS` 承载全部翻译，不假设三层同名。漂移时单点修正 `ARGS_TO_FLAGS`。

4. **rollback 字段名是 `rollback` 不是 `rollback_strategy`**：`ptm-atomic list` 真实字段是 `side_effect` + `rollback`。`OP_METADATA` 使用 `rollback` 字段名。op yaml 中的 `rollback_strategy` 是 op 级声明，与 list 输出的 `rollback` 字段对应。

5. **reset-hitcount 是 irreversible**：`fw_reset_policy_route_hitcount` 命中计数清零不可恢复。`ROLLBACK_STRATEGY` type=irreversible，`handle_rollback` 返回 `rollback=waived`。用例设计者需接受该副作用或通过用例顺序规避（reset 放末尾）。

6. **session 由 --session-file 自动管理**：ptm-te 无需自铸 idempotency_key / state_ref / session_ref，CLI 层已展平。op_mapper 只传 `--session-file` 路径，session.json 由 ptm-atomic 自动管理。

7. **login 签名是 --password-env 不是 --password**：`auth login --username admin --password-env FW_WEB_PASSWORD`，禁止命令行明文密码。`ARGS_TO_FLAGS` login 映射 `password_env -> --password-env`，默认值 `FW_WEB_PASSWORD`。

8. **update/delete 的 --id 按声明驱动解析**：后续 step 的 `args.id` 建议用 `${STEP-N.id}` 占位符（由 op_mapper `resolve_step_refs` 按被引 op 的 `rollback_strategy.id_source` 声明自动解析，支持 response/args/query/placeholder 4 模式）；LLM 仍可手动传 id，但占位符写法避免手动提取错误。`handle_rollback` 同样通过 `ptm-atomic show` 读声明解析 id（声明优先；无声明回退旧 `_extract_inverse_id`）。config 创建后 `data.policy_route_id` 直接返回新建的 id（真相源 `atoms/fw/fw_config_policy_route.yaml returns`，id_source=response）。

9. **update --id 已注册可用**（原 O-08 风险已消除）：ptm-atomic 0.1.0 实测 `policy-route update --help` 已暴露 `--id ID`（required），`run_policy_route.py _run_update` 的 `_require_arg(args, "id")` 正常工作。原"update --id 未注册 / 抛 AttributeError"已过时，update runtime 验证可正常执行。

10. **入接口必须路由模式**：`ePolicyRouteInIfModeError` 表示 `in_interface` 非路由模式，需人工 Web 改接口模式后重试。op_mapper 不自动修复。SKILL 错误表明示此子错误码。

11. **delete 是 restore_snapshot 不是 observation**：`fw_delete_policy_route` 实测 rollback=restore_snapshot（destructive），不是只读。但 delete 作为 config 的清理动作时不触发回滚（它本身就是清理）。`ROLLBACK_STRATEGY` delete 标记 `as_cleanup_skip=True`。

12. **priority 无 rollback 元数据**：`fw_update_policy_route_priority` 的 side_effect 和 rollback 均为空，由用例设计决定是否恢复原优先级。`ROLLBACK_STRATEGY` priority: type=none。

13. **回滚类型必须以 ptm-atomic list 实测为准**：不要凭 op 名字推断 rollback 类型。`validate_mapping_consistency()` 校验 `ROLLBACK_STRATEGY.type` 与 `OP_METADATA.rollback` 交叉一致。

14. **4 种 id_source 模式（声明驱动）**：op yaml 的 `rollback_strategy.id_source` 声明了 id 的获取方式，经 `ptm-atomic show` 暴露给 ptm-te：
    - `response`（mode A）：id 来自 POST 响应（如 `policy_route_id`）— `fw_config_policy_route`
    - `args`（mode B）：id 即 args 字段值（如 `object_name`）— `fw_config_object`（待 op 覆盖扩展后端到端）
    - `query`（mode C）：需执行 verify GET 查询按 name 匹配获取 id — `fw_config_acl_policy`（待 op 覆盖扩展后端到端）
    - `placeholder`（mode D）：id 为固定占位（如 "1"），真正定位靠其他字段（如 `old_name`，rollback 时 new_name↔old_name 互换）— `fw_update_acl_policy_group`（待 op 覆盖扩展后端到端）
    `resolve_id` / `build_inverse_args` 按 `id_source` 分发，`handle_rollback` 声明优先（无声明回退旧 `_extract_inverse_id`）。

## 参数说明

### 共享参数（run 层级）

| 参数 | 必需 | 默认值 | 说明 |
|---|---|---|---|
| `--base-url` | 是 | - | 设备 Web 管理地址，如 `https://<IP_ADDRESS>` |
| `--session-file` | 否 | `~/.local/state/ptm-atomic/ngfw/session.json` | session.json 路径 |
| `--timeout` | 否 | 10 | HTTP 超时秒数 |
| `--verify-tls` | 否 | False（默认禁用） | TLS 证书验证 |
| `--format` | 否 | yaml | 输出格式（op_mapper 统一用 json） |
| `--execute` | 否 | False（默认 dry-run） | 执行真实写操作 |
| `--auth-header` | 否 | Authorization | 认证头类型 |

### op_mapper.py CLI 用法

```bash
# 映射表一致性校验
python scripts/op_mapper.py validate

# 打印映射结果（不执行）
python scripts/op_mapper.py map \
  --op-id fw_config_policy_route \
  --args '{"src_addr":"<IP_ADDRESS>/24","in_interface":"GE0_12","type":"ipv4"}'

# 执行单条 op（dry-run）
python scripts/op_mapper.py execute \
  --op-id fw_config_policy_route \
  --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --args '{"src_addr":"<IP_ADDRESS>/24","in_interface":"GE0_12"}' \
  --dry-run

# 执行单条 op（execute，需授权）
python scripts/op_mapper.py execute \
  --op-id fw_config_policy_route \
  --base-url https://<IP_ADDRESS> \
  --session-file ~/.local/state/ptm-atomic/ngfw/session.json \
  --args '{"src_addr":"<IP_ADDRESS>/24","in_interface":"GE0_12"}' \
  --execute --authorized
```

### envelope 结构

每条 op 执行结果封装为 envelope（JSON）：

```json
{
  "op_id": "fw_config_policy_route",
  "step_name": "配置策略路由",
  "status": "success",
  "data": {
    "policy_route_id": "<id>",
    "config_result": { "status": "succeeded", "config_domain": "policy_route" }
  },
  "error_type": "NONE",
  "diag_snapshot_ref": "runs/<run-id>/snapshot-before/<step>.json"
}
```

> `data.policy_route_id` 是 config 创建策略路由成功后返回的新建 id（真相源 `atoms/fw/fw_config_policy_route.yaml returns`），供后续 `update`/`delete`/`reset-hitcount` 的 `--id` 与 `handle_rollback` 回滚取用。

## 相邻对象边界

| 职责 | 归属 | 差异界定 |
|---|---|---|
| op_id/args 双层映射翻译 | **op_mapper.py**（本 Skill） | centralize 三层命名翻译，其他模块不重复映射逻辑 |
| 设备 SSH/Telnet 连接 | device-connection（STORY-024-02） | op_mapper 不建立 SSH/Telnet 连接，只调用 ptm-atomic CLI（Web HTTPS） |
| 设备清单管理 | device-management（STORY-024-02） | op_mapper 不维护 devices.yaml，base_url/session_file 由调用方传入 |
| 用例解析 | agents/ptm-te.md（STORY-024-01） | op_mapper 不解析 PC 文件，op_id/args 由调用方从 case_steps 提取后传入 |
| 执行门控 | agents/ptm-te.md（STORY-024-01） | op_mapper 不实现环境就绪/关键判定门控，只提供执行和回滚能力 |
| ptm-atomic CLI 本身 | ptm-atomic 仓库 | op_mapper 是 CLI 的消费者，不修改 ptm-atomic |

## 真相源锁定

映射表真相源锁定三处，`validate_mapping_consistency()` 校验一致性：

1. **`run_policy_route.py` `build_subtree()`** - 7 个 policy-route 子命令名（config/update/delete/verify/reset-hitcount/verify-hitcount/priority）
2. **op yaml `inputs.params`** - 参数名（source_network/dst_network/next_hop_ip/in_interface/type/id）
3. **`ptm-atomic run ... --help`** - CLI flag 名（--source-network 等）
4. **op yaml `returns.data`** - config 返回的 id 字段名（`policy_route_id`），供 inverse_op 回滚与 update/delete 取用
5. **`run_trex.py` `build_subtree()` + `atoms/tg/*.yaml`** - tg 族 6 op（v1.5）：命令树三层 `tg trex <action>`，action 名与 op_id 不同（如 `tg_config_interface`→`config-interface`）；`rollback_strategy.required_inputs`（mode E 回滚）；`side_effect=traffic_runtime`（新枚举）；`rollback_strategy.type=manual_required`（新回滚类型）

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|------|------|--------|---------|
| v1.0 | 2026-07-13 | host-orchestrator（CR-024） | policy-route-execution skill v1 初始交付（8 op 双层映射 + 执行 + 回滚） |
| v1.1 | 2026-07-13 | host-orchestrator（CR-028） | op_mapper 扩展至 15 op（5 族）；op 覆盖矩阵文档 |
| v1.2 | 2026-07-14 | host-orchestrator | Gotcha #8 刷新：id 来源优先 config 响应 `data.policy_route_id`（真相源 `fw_config_policy_route.yaml returns`），verify 查询仅兜底；Gotcha #9 刷新：update --id 已注册可用（ptm-atomic 0.1.0 修复，原 O-08 风险消除）；op_mapper `handle_rollback` 增加 `result_envelope` 参数从 config 响应提取 id；真相源锁定增加第 4 处 `returns.data`。注：CR-025 后 args key 对齐 op yaml params（source_network 等），但本 SKILL 映射表示例仍含旧 src_addr 命名，留 follow-up 同步。 |
| v1.3 | 2026-07-17 | host-orchestrator | op_mapper 扩展 tg 族 6 op（`EXPECTED_OP_COUNT` 15→21，v1.5 trex-traffic 接入）：命令树三层 `tg trex <action>`，`build_inverse_args` mode E（`required_inputs`），`manual_required` 回滚类型。真相源锁定增加第 5 处（`run_trex.py` + `atoms/tg/`）。 |
