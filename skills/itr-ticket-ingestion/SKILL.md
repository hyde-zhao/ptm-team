---
name: itr-ticket-ingestion
description: 从 ITR（问题单系统）安全、受控地拉取现网问题单，保存原始快照到受限数据区，生成批次清单并写入版本化 SQLite 数据库。后续由清洗、变更检测和失败保护模块扩展。
argument-hint: "<ITR URL> [--product <name>] [--time-range <start> <end>] [--page <n>] [--page-size <n>]"
user-invokable: true
status: active
shared: true
shared_writers:
  - ST-RA-05.1-INGEST（§1-§5：HTTP 摄取、快照保存、批次清单、数据库写入）
  - ST-RA-05.2-CLEAN（§6-§7：字段映射、清洗与质量报告）
  - ST-NRA-03（§8：失败保护，已实现）
  - ST-RA-06.1-DETECT（§9：变更检测与版本历史，已实现）
version: "1.2"
source_cr: "CR-030, CR-031"
source_feature: "FEAT-RA-INGESTION"
---

# itr-ticket-ingestion

## 目标

从用户指定的 ITR 来源安全、受控地获取现网问题单，经过 allowlist 白名单校验后发起 HTTP GET 请求，将原始响应保存为受权限保护的快照文件，生成批次清单，并将结构化数据写入版本化 SQLite 数据库。

**安全原则**：deny-by-default。任何不在白名单的 URL、方法、参数和 header 一律拒绝。不推断认证凭据，不向 ITR 发出写操作。

**依赖**：`data/dao.py`（ST-RA-INGEST-DB 提供的公共 DAO 接口）—— 只调用公共函数，不直接执行 SQL，不修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore`。

## 运行数据治理契约

本 Skill 只在**安装后的 `ptm-tse` 项目**内运行。调用方先解析 `runtime_root`：默认当前安装项目根；用户覆盖值必须被验证为该项目根。`data_root` 固定为 `<runtime-root>/data/`。本文其余所有 `data/...` 路径均以此为基准，绝不解析到 `ptm-team` 源码根、全局用户目录或任意当前工作目录。

| 类别 | 路径 / 范围 | 规则 |
|---|---|---|
| 敏感运行数据 | `ptm-tse.db`、`-wal`、`-shm`、`-journal`、`snapshots/`、原始快照、批次/质量/冲突清单 | `data/` 与敏感子目录为 `0700`；敏感文件为 `0600`；新建时硬断言。 |
| support | `dao.py`、`schema.sql`、`.gitignore` | 不是问题单运行数据，不适用自动清理；不得因摄取失败或保留策略删除、迁移或重写。 |
| 预检 | `RuntimeDataGovernanceReport` | 必须由 ptm-tse Agent 在摄取前产生并为 `compliant`，至少核验运行根、路径分类、权限和 git 排除。 |

若报告为 `blocked` 或 `needs-user-authorization`，本 Skill 必须停止，既不发出 HTTP GET，也不创建 batch、快照、清单或数据库写入。它可以返回修复建议，但不能自行修复已存在的权限、执行迁移/导出/清理，或改变保留状态；这些动作只能由安装项目的 Agent 在用户明确本地运行授权后执行。失败处理中删除的仅限本次调用尚未提交的临时文件，不得作为生命周期清理。

## 前置条件

1. ptm-tse Agent 已提供状态为 `compliant` 的 `RuntimeDataGovernanceReport`；`runtime_root` 已解析，且 `data_root=<runtime-root>/data/`
2. `data/dao.py` 中的 `init_storage()` 已执行，确保 `data/` 和 `data/snapshots/` 目录存在且权限为 `0700`
3. ITR 服务 `http://<IP_ADDRESS>/itr/v1/itrs` 网络可达
4. Python 标准库可用（`json`、`hashlib`、`os`、`shutil`、`pathlib`、`sqlite3`、`datetime`）
5. `<runtime-root>/data/dao.py` 可导入（`from data.dao import ...` 或等价方式）

---

## §1 触发条件与输入契约

### 触发条件

用户显式请求从 ITR 拉取问题单时触发本 Skill。典型触发语句：

- "请从 ITR 拉取 product=TGFW 最近 30 天的问题单"
- "拉取 ITR 问题单，产品 TGFW，时间范围 2026-06-01 到 2026-07-01"

### 输入契约

| 参数 | 必需 | 类型 | 约束 | 说明 |
|---|---|---|---|---|
| `url` | 是 | `str` | 必须匹配 allowlist pattern | ITR 接口地址 |
| `product` | 是 | `str` | 必须在参数白名单 | 产品名称 |
| `time_range_start` | 否 | `str` | ISO 8601 格式 | 时间范围起始 |
| `time_range_end` | 否 | `str` | ISO 8601 格式 | 时间范围结束 |
| `page` | 否 | `int` | >= 1 | 分页页码，默认 1 |
| `page_size` | 否 | `int` | <= max_page_size（100） | 每页条数，默认 50 |

任何不在白名单的额外参数将被拒绝。

### 平台差异

本 Skill 使用 Python 标准库（`open()`、`json`、`hashlib`、`shutil`、`os`、`sqlite3`），不依赖特定 HTTP 库。各 Agent 平台使用其内置 HTTP 能力发起 GET 请求：

- **标准 Python 运行时**：使用 `requests` 或 `httpx` 库
- **Agent 内置 HTTP 工具**：使用平台提供的 HTTP 请求能力
- 无论何种 HTTP 实现，均须遵守相同的 allowlist 校验规则

---

## §2 受控 HTTP GET 摄取

### 2.1 Allowlist 白名单配置

本 Skill 使用 `skills/itr-ticket-ingestion/templates/allowlist-config.yaml` 作为 allowlist 配置真相源。配置结构：

```yaml
# skills/itr-ticket-ingestion/templates/allowlist-config.yaml
# ITR 受控摄取 allowlist 白名单配置
# 任何不在本白名单的 URL、方法、参数和 header 将被拒绝（deny-by-default）

allowlist:
  - pattern: "http://<IP_ADDRESS>/itr/v1/itrs"
    description: "TGFW ITR 问题单接口"
    allowed_params:
      - product
      - time_range_start
      - time_range_end
      - page
      - page_size
    max_page_size: 100
    allow_redirects: false
```

### 2.2 Allowlist 校验算法

执行任何 HTTP 请求前，必须按以下顺序完成全部校验。任一校验失败立即终止，不发起 HTTP 请求。

```
1. 方法白名单校验
   IF method != "GET":
     → 拒绝，抛出 HTTPMethodDeniedError
     原因："仅允许 GET 方法，检测到: {method}"

2. 认证头拒绝校验
   拒绝的 header 名称（case-insensitive 匹配）：
     - authorization
     - x-auth-token
     - cookie
     - x-api-key
   IF any header key in 拒绝列表:
     → 拒绝，抛出 CredentialDeniedError
     原因："禁止携带认证凭据，检测到 header: {key}"

3. URL pattern 匹配
   FOR each pattern in allowlist:
     IF url 完全匹配 pattern.pattern:
       matched_pattern = pattern; BREAK
   IF matched_pattern IS None:
     → 拒绝，抛出 AllowlistDeniedError
     原因："URL 不在白名单中: {url}"

4. 参数白名单校验
   FOR each key in user_params:
     IF key NOT IN matched_pattern.allowed_params:
       → 拒绝，抛出 AllowlistDeniedError
       原因："参数 '{key}' 不在白名单中"

5. 分页上限校验
   IF user_params.page_size > matched_pattern.max_page_size:
     → 拒绝，抛出 AllowlistDeniedError
     原因："分页大小 {page_size} 超过上限 {max_page_size}"

6. 通过
   → 返回 (url, user_params, matched_pattern)
```

### 2.3 HTTP GET 请求执行

通过 allowlist 校验后，发起 HTTP GET 请求：

```
1. 构造请求
   - 方法: GET
   - URL: 校验通过的 url + query params
   - headers: 不含任何认证头（Authorization、Cookie 等）
   - timeout: 30 秒（DEFAULT_TIMEOUT 常量）
   - allow_redirects: false（3xx 视为错误）

2. 发起请求并记录元数据
   - request_time: ISO 8601 时间戳（请求发起时刻）
   - elapsed_ms: 请求耗时（毫秒）

3. 响应处理
   - HTTP 2xx:
     → 成功，记录 http_status、body、headers、content_length
   - HTTP 4xx/5xx:
     → 失败，抛出 HTTPFetchError（recoverable=False）
     原因："ITR 返回错误状态 {http_status}"
   - 连接超时:
     → 失败，抛出 HTTPFetchError（recoverable=True）
     原因："ITR 连接超时（>30s）"
   - 响应体为空:
     → 失败，抛出 HTTPFetchError（recoverable=False）
     原因："ITR 响应体为空"
   - HTTP 3xx（重定向）:
     → 失败，抛出 HTTPFetchError（recoverable=False）
     原因："不允许 HTTP 重定向"

4. 不自动重试
   所有 HTTP 层面的失败均不自动重试。外部系统重试策略需用户明确指定。
```

### 2.4 分页摄取

当需要拉取多页数据时，按以下流程自动分页：

```
function fetch_all_pages(url, base_params):
    all_tickets = []
    page = 1
    max_page_size = matched_pattern.max_page_size

    WHILE True:
        params = base_params + {page: page, page_size: max_page_size}
        response = fetch_page(url, params)    # 走完整 allowlist 校验 → HTTP GET
        tickets = parse_ticket_array(response.body)

        IF tickets IS EMPTY:
            BREAK  # 无更多数据

        all_tickets.extend(tickets)
        page += 1

        IF len(tickets) < max_page_size:
            BREAK  # 最后一页（不足一页）

    RETURN all_tickets
```

**分页中断处理**：若某页请求失败，已成功拉取的前几页保留（快照和 batch 创建），batch 标记 partial，失败页码和原因记录在 errors 中。失败页可单独重试。

---

## §3 原始快照保存

### 3.1 存储策略

| 属性 | 值 |
|---|---|
| 根目录 | `data/snapshots/` |
| 目录权限 | `0700`（由 `data/dao.py` 的 `init_storage()` 保证） |
| 文件命名 | `batch-{batch_id}-raw.json` |
| 文件权限 | `0600`（写入后硬断言） |
| Git 排除 | `data/snapshots/` 已在 `data/.gitignore` 中排除 |
| 临时文件 | 先写 `.tmp` 后缀临时文件，权限校验通过后原子替换 |
| 磁盘空间 | 写入前检查可用空间 >= 100MB |

### 3.2 快照文件结构

```json
{
  "snapshot_metadata": {
    "batch_id": "batch-20260716-001",
    "request_url": "http://<IP_ADDRESS>/itr/v1/itrs",
    "request_params": {
      "product": "TGFW",
      "time_range_start": "2026-06-01",
      "page": 1,
      "page_size": 50
    },
    "request_time": "2026-07-16T10:30:00Z",
    "http_status": 200,
    "response_hash": "sha256:abc123def456...",
    "response_size_bytes": 45678,
    "elapsed_ms": 1234
  },
  "raw_response": "<ITR 原始 JSON 响应体，原样保存，不做任何转换>"
}
```

### 3.3 保存算法

```
function save_raw_snapshot(response_body, request_url, params,
                            http_status, headers, batch_id):
    # 0. 前置检查：磁盘空间
    available = shutil.disk_usage("data/").free
    IF available < 100 * 1024 * 1024:  # 100MB
      → 抛出 SnapshotSaveError(recoverable=False)
      原因："磁盘空间不足，可用 {available} bytes，需要 >= 100MB"

    # 1. 计算响应 hash
    response_hash = "sha256:" + hashlib.sha256(response_body.encode()).hexdigest()

    # 2. 确定文件路径
    snapshot_path = Path(f"data/snapshots/batch-{batch_id}-raw.json")
    tmp_path = Path(f"data/snapshots/batch-{batch_id}-raw.json.tmp")

    # 3. 组装快照结构
    snapshot = {
        "snapshot_metadata": {
            "batch_id": batch_id,
            "request_url": request_url,
            "request_params": params,
            "request_time": datetime.utcnow().isoformat() + "Z",
            "http_status": http_status,
            "response_hash": response_hash,
            "response_size_bytes": len(response_body.encode()),
            "elapsed_ms": elapsed_ms  # 从 HTTP 请求记录获取
        },
        "raw_response": response_body  # 原样保存，不做任何转换
    }

    # 4. 写入临时文件
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 5. 权限硬断言：设置 0600 并验证
    os.chmod(tmp_path, 0o600)
    actual_mode = stat.S_IMODE(os.stat(tmp_path).st_mode)
    IF actual_mode != 0o600:
      # 权限不满足 → 删除临时文件和本批次所有未提交数据 → 停止
      tmp_path.unlink(missing_ok=True)
      IF snapshot_path.exists():
        snapshot_path.unlink(missing_ok=True)
      → 抛出 SnapshotSaveError(recoverable=False)
      原因："快照权限设置失败: 期望 0o600, 实际 {oct(actual_mode)}"

    # 6. 原子替换：临时文件 → 正式文件
    os.replace(tmp_path, snapshot_path)

    # 7. 最终校验：正式文件是否存在且权限正确
    IF NOT snapshot_path.exists():
      → 抛出 SnapshotSaveError(recoverable=False)
      原因："原子替换失败，目标文件不存在"
    final_mode = stat.S_IMODE(os.stat(snapshot_path).st_mode)
    IF final_mode != 0o600:
      → 抛出 SnapshotSaveError(recoverable=False)
      原因："快照权限异常: 期望 0o600, 实际 {oct(final_mode)}"

    # 8. 返回结果
    RETURN {
        "snapshot_ref": str(snapshot_path),
        "response_hash": response_hash,
        "saved_at": snapshot["snapshot_metadata"]["request_time"],
        "file_size_bytes": snapshot["snapshot_metadata"]["response_size_bytes"]
    }
```

### 3.4 失败清理规则

快照保存过程中任一校验失败（权限、磁盘空间、原子替换），立即：
1. 删除本批次产生的临时文件（`.tmp`）
2. 删除本批次已写入但未完成校验的快照文件
3. 不创建 `ingestion_batch` 数据库记录
4. 停止本批次摄取

---

## §4 批次清单生成

### 4.1 Batch Manifest 结构

每次成功保存快照后，生成批次清单 YAML 文件：`data/snapshots/batch-{batch_id}-manifest.yaml`

```yaml
# batch-manifest.yaml — ITR 摄取批次清单
# 模板文件: skills/itr-ticket-ingestion/templates/batch-manifest.yaml
# 本文件由 itr-ticket-ingestion Skill 在每次成功摄取后自动生成

batch_id: "batch-20260716-001"
request:
  url: "http://<IP_ADDRESS>/itr/v1/itrs"
  params:
    product: "TGFW"
    time_range_start: "2026-06-01"
    time_range_end: "2026-07-01"
  timestamp: "2026-07-16T10:30:00Z"
http_status: 200
response_hash: "sha256:abc123def456..."
snapshot:
  ref: "data/snapshots/batch-20260716-001-raw.json"
  saved_at: "2026-07-16T10:30:00Z"
schema_version: "1.0"
ingestion_result:
  total_fetched: 0
  total_new: 0
  total_updated: 0
  total_unchanged: 0
  total_conflict: 0
  total_cleaned: 0
  total_failed: 0
quality_report_ref: "skills/itr-ticket-ingestion/templates/quality-report.yaml"
errors: []
```

**字段说明**：

| 字段 | 填充时机 | 说明 |
|---|---|---|
| `batch_id` | 摄取开始时 | `batch-{YYYYMMDD}-{seq}` 格式 |
| `request.*` | HTTP 请求完成后 | 请求 URL、参数和时间戳 |
| `http_status` | HTTP 响应后 | 响应状态码 |
| `response_hash` | 快照保存后 | sha256 哈希 |
| `snapshot.*` | 快照保存后 | 快照文件路径和时间 |
| `ingestion_result.total_fetched` | 本 Story | HTTP 响应中解析出的 ticket 总数 |
| `ingestion_result.total_new/updated/unchanged/conflict` | ST-RA-06.1-DETECT | 变更检测结果（后续 Story 填充） |
| `ingestion_result.total_cleaned/failed` | ST-RA-05.2-CLEAN | 清洗结果（后续 Story 填充） |
| `quality_report_ref` | ST-RA-05.2-CLEAN | 质量报告路径（后续 Story 追加） |

### 4.2 生成流程

```
function generate_batch_manifest(batch_id, request_url, params, http_status,
                                  response_hash, snapshot_ref, saved_at,
                                  total_fetched):
    manifest = {
        "batch_id": batch_id,
        "request": {
            "url": request_url,
            "params": params,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "http_status": http_status,
        "response_hash": response_hash,
        "snapshot": {
            "ref": snapshot_ref,
            "saved_at": saved_at
        },
        "schema_version": "1.0",
        "ingestion_result": {
            "total_fetched": total_fetched,
            "total_new": 0,
            "total_updated": 0,
            "total_unchanged": 0,
            "total_conflict": 0,
            "total_cleaned": 0,
            "total_failed": 0
        },
        "quality_report_ref": "skills/itr-ticket-ingestion/templates/quality-report.yaml",
        "errors": []
    }

    manifest_path = f"data/snapshots/batch-{batch_id}-manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)

    RETURN manifest_path
```

---

## §5 数据库写入

### 5.1 DAO 调用约束

本 Skill 只调用 `data/dao.py` 中的公共函数接口，不直接执行 SQL。可调用的接口：

| 函数 | 用途 | 调用阶段 |
|---|---|---|
| `get_connection()` | 创建数据库连接 | 写入前 |
| `begin_transaction(conn)` | 开始事务 | 写入前 |
| `commit(conn)` | 提交事务 | 写入成功后 |
| `rollback(conn)` | 回滚事务 | 写入失败时 |
| `insert_ingestion_batch(conn, batch)` | 插入批次记录 | §5.3 |
| `get_ticket_by_source_id(conn, source_id)` | 查询 ticket 是否存在 | S2 变更检测（后续） |
| `insert_ticket(conn, ticket)` | 插入新 ticket | S1 首次摄取 |
| `upsert_ticket(conn, ticket, field_diffs)` | 插入或更新 ticket | S2 增量摄取（后续） |
| `insert_ticket_version(conn, ...)` | 插入版本历史 | S1/S2 |
| `get_next_version(conn, ticket_id)` | 获取下一版本号 | S1/S2 |
| `insert_change_history(conn, ...)` | 插入变更历史 | S1/S2 |

**禁止操作**：
- 不直接执行 `conn.execute(...)` SQL 语句
- 不修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore`
- 不绕过 DAO 校验函数（`validate_ticket()`、`validate_change_type()` 等）

### 5.2 数据库连接管理

```
# 获取数据库连接
conn = get_connection()  # 使用默认路径 data/ptm-tse.db

# 写入前确保存储已初始化
init_storage()  # 确保 data/ 和 data/snapshots/ 目录存在且权限 0700
```

### 5.3 本 Story 写入范围（S1 首次摄取）

在 §5.3 中，本 Story 只负责 S1 首次摄取的数据库写入：

```
function write_ingestion_result(conn, batch_id, request_url, params,
                                 http_status, response_hash, snapshot_ref,
                                 tickets):
    begin_transaction(conn)

    TRY:
        # 1. 插入 ingestion_batch 记录
        batch_record = {
            "batch_id": batch_id,
            "request_url": request_url,
            "request_params": json.dumps(params),
            "http_status": http_status,
            "response_hash": response_hash,
            "snapshot_ref": snapshot_ref,
            "schema_version": "1.0",
            "total_fetched": len(tickets)
        }
        batch_db_id = insert_ingestion_batch(conn, batch_record)

        # 2. 遍历 tickets，写入 ticket + ticket_version + change_history
        for ticket in tickets:
            # 2a. 检查 source_ticket_id 是否已存在
            existing = get_ticket_by_source_id(conn, ticket["source_ticket_id"])

            IF existing is None:
                # 新 ticket → insert
                ticket_id = insert_ticket(conn, ticket)
                change_type = "new"
            ELSE:
                # 已存在 → skip（S1 首次摄取不处理变更）
                # 变更检测由 ST-RA-06.1-DETECT 在 S2 处理
                CONTINUE

            # 2b. 插入 ticket_version（version=1）
            next_ver = get_next_version(conn, ticket_id)
            previous_status = None  # 首次无上一版本
            field_diffs = json.dumps({})  # 首次无差异
            insert_ticket_version(
                conn, ticket_id, next_ver, previous_status,
                field_diffs, batch_id
            )

            # 2c. 插入 change_history（type='new'）
            insert_change_history(
                conn, ticket_id, batch_id, change_type="new"
            )

        commit(conn)
        RETURN {"batch_db_id": batch_db_id, "total_inserted": len(tickets)}

    EXCEPT Exception as e:
        rollback(conn)
        → 记录错误并抛出
        # 快照文件已保存，batch manifest 已生成
        # 数据库回滚意味着本批次数据不在 DB 中，但快照可用于重试
```

### 5.4 错误处理

| 场景 | 处理 |
|---|---|
| DAO 调用抛出 `ValueError` | 记录校验失败信息，回滚事务 |
| DAO 调用抛出 `sqlite3.IntegrityError` | 记录冲突信息（如 source_ticket_id 重复），回滚事务 |
| 事务写入中途失败 | 回滚事务，快照文件和 manifest 保留 |
| 数据库文件不可访问 | 抛出异常，不创建任何数据 |

---

## §6 字段映射与清洗

> **本章节由 ST-RA-05.2-CLEAN 实现。**
>
> 清洗管线接收 ST-RA-05.1-INGEST 从 ITR HTTP 响应解析出的原始 ticket 数组，
> 按 `field-mapping.yaml` 配置将 ITR 字段映射为 `ticket` 表列，执行空值/异常/重复检测，
> 设置 `quality_flag`，并生成 `IngestionQualityReport`。
>
> **设计依据**: ST-RA-05.2-CLEAN LLD §1-§5 + §2.3.1（severity/pri 标准化映射）。
> **依赖**: `data/dao.py`（公共 DAO 接口，只调用，不修改），
> `skills/itr-ticket-ingestion/templates/field-mapping.yaml`（映射配置真相源）。

### 6.1 清洗管线入口

```
── 输入 ──
raw_tickets: list[dict]  (来自 ST-RA-05.1 的 HTTP 响应解析)
batch_id: str
          │
          ▼
┌─ Step 1. 加载映射配置 ────────────────────────────────────┐
│  mapping = load_field_mapping("field-mapping.yaml")        │
│  校验 schema_version，不匹配则拒绝                          │
└────────────────────────────────────────────────────────────┘
          │
          ▼
┌─ Step 2. 逐条清洗 ────────────────────────────────────────┐
│  FOR each raw_ticket:                                      │
│    a. map_fields(raw, mapping) → 按 source→target 映射    │
│       未在 mapping 中定义的字段 → 保留在 raw_json,          │
│       记录到 unclassified_fields[]                          │
│    b. validate_required(cleaned) → 校验必填字段             │
│       source_ticket_id / product / source_updated_at       │
│       缺失 → FailedRecord('missing_required')             │
│    c. validate_enums(cleaned, mapping) → 校验枚举字段       │
│       不在 valid_values → quality_flag='anomaly'           │
│    d. detect_nulls(cleaned) → 空值检测                      │
│       非必填字段空值 → quality_flag='incomplete'            │
│    e. detect_duplicate(cleaned, seen_ids) → 重复检测        │
│       同批次内 source_ticket_id 重复 → duplicate_count++    │
│       首批保留，后续标记为重复（不进 cleaned 列表）          │
│    f. classify_fields(cleaned, classification_dict)         │
│       未分类字段 → 记录到 issues，不进 cleaned 字典          │
│    g. set_quality_flag(cleaned, issues)                     │
│       按优先级: blocked > anomaly > incomplete > clean      │
│    h. 追加 raw_json（完整原始 ITR 记录）、first_seen_at、   │
│       last_seen_at、source_updated_at                        │
└────────────────────────────────────────────────────────────┘
```

### 6.2 字段映射表

> 完整映射配置源：`skills/itr-ticket-ingestion/templates/field-mapping.yaml`

| ITR 源字段 | ticket 目标列 | 类型 | 必填 | 校验规则 |
|---|---|---|---|---|
| `id` | `source_ticket_id` | `string` | **是** | 非空，长度 ≤ 256 |
| `product` | `product` | `string` | **是** | 非空 |
| `pri` | `priority` | `enum` | 否 | ∈ {P1, P2, P3, P4}，否则 anomaly |
| `severity` | `severity` | `enum` | 否 | ∈ {致命, 严重, 一般, 提示}，否则 anomaly |
| `module` | `module` | `string` | 否 | — |
| `status` | `status` | `string` | 否 | — |
| `title` | `title` | `string` | 否 | — |
| `description` | `description` | `string` | 否 | — |
| `root_cause` | `root_cause` | `string` | 否 | — |
| `test_missed_analysis` | `test_missed_analysis` | `string` | 否 | — |
| `test_missed_phase` | `test_missed_phase` | `string` | 否 | — |
| `improvement_measures` | `improvement_measures` | `string` | 否 | — |
| `openeddate` | `openeddate` | `string` | 否 | — |
| `resolveddate` | `resolveddate` | `string` | 否 | — |
| `source_updated_at` | `source_updated_at` | `datetime` | **是** | ISO 8601 格式 |

**不在本表中的 ITR 字段**：
1. 不映射到 ticket 表列
2. 保留在 `raw_json` 中（完整原始响应始终保存）
3. 在 `quality_report.issues` 中记录 `type='unclassified'`
4. **不静默丢弃**

### 6.3 清洗规则

#### 6.3.1 空值处理

| 场景 | 字段类型 | 处理 | quality_flag |
|---|---|---|---|
| source_ticket_id 为空 | 必填 | FailedRecord，不进 cleaned 列表 | (记录丢弃) |
| product 为空 | 必填 | FailedRecord，不进 cleaned 列表 | (记录丢弃) |
| source_updated_at 为空 | 必填 | FailedRecord，不进 cleaned 列表 | (记录丢弃) |
| 任意非必填字段为空 | 可选 | 字段值设为 None，记录 null issue | `incomplete` |

**空值判定算法**：
```
function detect_nulls(cleaned_record, mapping_config):
    issues = []
    FOR each field in mapping_config:
        IF field.required AND (cleaned_record[field.target] IS NULL OR EMPTY):
            → 如果 field.target ∈ {source_ticket_id, product, source_updated_at}:
              → FailedRecord（阻断，不进 cleaned 列表）
            → 否则:
              → cleaned_record[field.target] = None
              → issues.append({field: field.target, type: 'null'})
    RETURN issues
```

#### 6.3.2 枚举校验

| 枚举字段 | 有效值 | 异常处理 |
|---|---|---|
| `priority` | P1, P2, P3, P4 | 保留原值，quality_flag='anomaly' |
| `severity` | 致命, 严重, 一般, 提示 | 保留原值，quality_flag='anomaly' |

**枚举校验算法**：
```
function validate_enums(cleaned_record, mapping_config):
    issues = []
    FOR each field in mapping_config WHERE field.type == 'enum':
        value = cleaned_record.get(field.target)
        IF value IS NOT NULL AND value NOT IN field.valid_values:
            → 保留原值（不清空）
            → issues.append({field: field.target, type: 'anomaly',
                              value: value, expected: field.valid_values})
    RETURN issues
```

#### 6.3.3 severity / pri 映射与高严重度判定

> 来源: ST-RA-05.2-CLEAN LLD §2.3.1（CP5 Round 2 评审整改）

**pri ↔ severity 映射关系**：

| pri 值 | 典型 severity | 高严重度判定 | 说明 |
|---|---|---|---|
| P1 | 致命 或 严重 | **是** | P1 问题总是高严重度，无论 severity 字段是否有值 |
| P2 | 严重 或 一般 | **是**（如果 severity ∈ {致命, 严重}） | P2 且 severity 为致命/严重时，视为高严重度 |
| P3 | 一般 | 否 | P3/P4 不做高严重度门控 |
| P4 | 提示 | 否 | — |

**高严重度判定函数**：
```python
def is_high_severity(ticket: dict) -> bool:
    """判定是否触发 QCOMB-01 / QCOMB-02 高严重度质量门控"""
    pri = ticket.get('priority', '')
    severity = ticket.get('severity', '')

    # P1 总是高严重度
    if pri == 'P1':
        return True
    # P2 且 severity 为致命或严重
    if pri == 'P2' and severity in ('致命', '严重'):
        return True
    return False
```

**映射失败处理**：

| 场景 | 处理 | quality_flag |
|---|---|---|
| `pri` 不在 {P1, P2, P3, P4} | 记录原始值，标注 anomaly | `anomaly` |
| `severity` 不在 {致命, 严重, 一般, 提示} | 记录原始值，标注 anomaly | `anomaly` |
| `pri` 缺失 | 不影响清洗，但 QCOMB-01/02 不触发 | 不影响 quality_flag |
| `severity` 缺失 | 不影响清洗，但 QCOMB-02 仅基于 pri 判定 | 不影响 quality_flag |
| `pri` 和 `severity` 同时缺失 | 该记录不参与高严重度门控 | 不影响 quality_flag（除非其他字段异常） |

#### 6.3.4 重复检测

```
function detect_duplicates(cleaned_record, seen_ids):
    source_id = cleaned_record['source_ticket_id']
    IF source_id IN seen_ids:
        → duplicate_count++
        → 返回 None（不进 cleaned 列表）
    ELSE:
        seen_ids.add(source_id)
        → 返回 cleaned_record
```

> 重复处理策略: 同批次内首次出现的 source_ticket_id 保留，后续重复记录只增加计数，不写入 ticket 表。
> 跨批次的去重/变更检测由 ST-RA-06.1-DETECT 处理。

#### 6.3.5 未知字段处理

```
function handle_unknown_fields(raw_record, mapping_config):
    known_sources = {m.source for m in mapping_config}
    unknown = []
    FOR each key in raw_record:
        IF key NOT IN known_sources:
            → unknown.append(key)
            → 不映射到 cleaned 字典
            → 字段保留在 raw_json 中
    RETURN unknown
```

> **阻断规则**：未分类字段不导致记录阻断，但：
> 1. 未知字段不出现在 cleaned 字典中
> 2. 在 `quality_report.issues` 中记录 `type='unclassified'`
> 3. 保留在 `raw_json` 中供追溯

### 6.4 quality_flag 设置

> 来源: ST-RA-05.2-CLEAN LLD §3.1

| quality_flag | 判定条件 | 对分析的影响 |
|---|---|---|
| `clean` | 必填字段全部有效，无可疑值，无冲突 | 可直接分析 |
| `incomplete` | 非 source_ticket_id/product 的必填字段有空值 | 可分析但标注数据不完整 |
| `anomaly` | 字段值格式/范围异常（如枚举不在有效值内） | 可分析但标注异常字段 |
| `blocked` | source_ticket_id 或 product 缺失 | 不可分析 |

**判定优先级**: `blocked` > `anomaly` > `incomplete` > `clean`

```python
def set_quality_flag(record: dict, issues: list[dict]) -> str:
    """按优先级判定 quality_flag"""
    issue_types = {i['type'] for i in issues}

    if 'blocked_critical' in issue_types:
        return 'blocked'
    if 'anomaly' in issue_types:
        return 'anomaly'
    if 'null_value' in issue_types:
        # 检查是否影响必填关键字段
        for i in issues:
            if i['type'] == 'null_value' and i.get('required'):
                if i['field'] in ('source_ticket_id', 'product', 'source_updated_at'):
                    return 'blocked'
        return 'incomplete'
    return 'clean'
```

### 6.5 敏感字段分类

> 来源: ST-RA-05.2-CLEAN LLD §3.2 + FEAT-RA-INGESTION DESIGN §5（安全约束）

| 分类 | 定义 | 字段示例 | 存储策略 | 使用策略 |
|---|---|---|---|---|
| `raw` | 原始数据，不可直接暴露 | `raw_json`（完整原始响应） | 仅存储在 SQLite `ticket.raw_json` | 不进 LLM/报告正文 |
| `cleaned` | 映射清洗后，可安全分析 | `title`, `description`, `root_cause` | 存储在对应字段 | 可进入分析流程 |
| `report` | 聚合/脱敏后，可对外展示 | severity 分布、产品质量统计 | 存储在分析报告 | 可出现在报告中 |

**分类词典**: 定义在 `field-mapping.yaml` 的 `field_classification` 节点中。所有未在词典中注册的字段视为 `unclassified`，保留在 `raw_json` 中。

### 6.6 清洗主流程伪代码

```python
def clean_tickets(raw_tickets: list[dict], batch_id: str,
                  mapping_path: str = "skills/itr-ticket-ingestion/templates/field-mapping.yaml") -> dict:
    """清洗管线主入口"""
    mapping = load_field_mapping(mapping_path)
    classification = mapping.get('field_classification', {})

    cleaned_records = []
    failed_records = []
    stats = CleaningStats()

    for idx, raw in enumerate(raw_tickets):
        # 1. 字段映射
        cleaned = map_fields(raw, mapping['mappings'], raw_ticket=raw)

        # 2. 未知字段检测
        unknown = handle_unknown_fields(raw, mapping['mappings'])
        stats.unclassified_fields += len(unknown)

        # 3. 必填字段校验
        missing = validate_required_fields(cleaned, mapping['mappings'])
        if any(f in ('source_ticket_id', 'product', 'source_updated_at') for f in missing):
            failed_records.append(FailedRecord(
                index=idx,
                source_ticket_id=raw.get('id'),
                reason='missing_required',
                fields=missing
            ))
            stats.total_failed += 1
            continue

        # 4. 枚举校验 + 空值检测 + 重复检测
        issues = []
        issues.extend(validate_enums(cleaned, mapping['mappings']))
        issues.extend(detect_nulls_non_required(cleaned, mapping['mappings']))

        # 5. 重复检测
        if cleaned['source_ticket_id'] in seen_ids:
            stats.duplicate_count += 1
            continue
        seen_ids.add(cleaned['source_ticket_id'])

        # 6. 设置 quality_flag
        cleaned['quality_flag'] = set_quality_flag(cleaned, issues)

        # 7. 追加 raw_json 和时间戳
        cleaned['raw_json'] = json.dumps(raw, ensure_ascii=False)
        cleaned['first_seen_at'] = now_iso
        cleaned['last_seen_at'] = now_iso

        cleaned_records.append(cleaned)

    # 8. 计算统计
    stats = compute_stats(raw_tickets, cleaned_records, failed_records, stats)

    return {
        "cleaned": cleaned_records,
        "failed": failed_records,
        "stats": stats
    }
```

### 6.7 清洗的错误处理

| 错误场景 | 处理策略 | 降级行为 |
|---|---|---|
| 必填字段缺失（source_ticket_id） | FailedRecord，不进 cleaned 列表 | 该条记录不写入 ticket 表 |
| 必填字段缺失（product） | 同上 | 同上 |
| 必填字段缺失（source_updated_at） | 同上 | 同上 |
| 非必填字段空值 | 字段值设为 None，quality_flag='incomplete' | 记录可继续分析 |
| 枚举字段值不在 valid_values 内 | 保留原值，quality_flag='anomaly' | 记录可继续分析 |
| 未知字段 | 保留在 raw_json 中，记录到 issues | 记录可继续分析 |
| 批次内 source_ticket_id 重复 | 保留第一条，后续标记为重复 | 只保留第一条的 cleaned 版本 |
| field-mapping.yaml 不存在或 schema_version 不匹配 | 拒绝整个批次，不执行清洗 | 批次 blocked |

**降级原则**：
- 不静默丢弃记录（除非 source_ticket_id 或 product 缺失——无法建立唯一标识）
- 不静默删除字段（未知字段保留在 raw_json）
- 不静默吞下映射错误（映射失败记录在 quality_report 中）

---

## §7 质量报告生成

> **本章节由 ST-RA-05.2-CLEAN 实现。**
>
> 清洗完成后，根据统计结果和阈值配置生成 `IngestionQualityReport`，
> 执行单字段阈值判定和 QCOMB-01~05 组合规则检查，输出批次级 overall_status。
> `quality_report_ref` 回写 `ingestion_batch` 表和 `batch-manifest.yaml`。
>
> **设计依据**: ST-RA-05.2-CLEAN LLD §2.4-§2.6 + §5（状态机）。
> **模板源**: `skills/itr-ticket-ingestion/templates/quality-report.yaml`

### 7.1 报告生成入口

```python
def generate_quality_report(clean_result: dict, batch_id: str,
                            request_url: str, http_status: int,
                            response_hash: str, schema_version: str) -> dict:
    """生成 IngestionQualityReport"""
    stats = clean_result['stats']
    cleaned = clean_result['cleaned']
    failed = clean_result['failed']
    issues = collect_all_issues(cleaned, failed)

    report = load_template("quality-report.yaml")
    report['batch_id'] = batch_id
    report['schema_version'] = schema_version
    report['generated_at'] = datetime.utcnow().isoformat() + "Z"

    # 输入摘要
    report['input_summary']['total_fetched'] = stats.total_input
    report['input_summary']['http_status'] = http_status
    report['input_summary']['response_hash'] = response_hash

    # 质量摘要
    report['quality_summary']['total_clean'] = count_by_flag(cleaned, 'clean')
    report['quality_summary']['total_flagged'] = count_by_flag(cleaned, ('incomplete', 'anomaly'))
    report['quality_summary']['total_failed'] = len(failed)
    report['quality_summary']['total_blocked'] = count_by_flag(cleaned, 'blocked')
    report['quality_summary']['null_rate'] = stats.null_count / max(stats.total_input, 1)
    report['quality_summary']['anomaly_rate'] = stats.anomaly_count / max(stats.total_input, 1)
    report['quality_summary']['duplicate_rate'] = stats.duplicate_count / max(stats.total_input, 1)
    report['quality_summary']['conflict_count'] = stats.conflict_count
    report['quality_summary']['unclassified_fields'] = stats.unclassified_fields

    # 单字段阈值判定
    report = evaluate_thresholds(report, stats)

    # 组合规则判定（QCOMB-01 ~ QCOMB-05）
    report = evaluate_combined_rules(report, stats, cleaned)

    # 整体判定
    report['analyzable_ratio'] = compute_analyzable_ratio(cleaned, failed, stats)
    report['is_analyzable'] = report['analyzable_ratio'] >= 0.5
    report['overall_status'] = determine_overall_status(report)
    report['issues'] = format_issues(issues)

    return report
```

### 7.2 统计指标计算公式

| 指标 | 公式 | 说明 |
|---|---|---|
| `null_rate` | `null_count / total_fetched` | 含空值（非必填字段）的条数占比 |
| `anomaly_rate` | `anomaly_count / total_fetched` | 枚举值异常或格式异常的条数占比 |
| `duplicate_rate` | `duplicate_count / total_fetched` | 同批次内 source_ticket_id 重复的条数占比 |
| `analyzable_ratio` | `(total_clean + total_incomplete_or_anomaly) / total_fetched` | 可分析记录占比（quality_flag ∈ {clean, incomplete, anomaly} 的记录数 / total_fetched） |

**analyzable_ratio 计算**:
```python
def compute_analyzable_ratio(cleaned, failed, stats):
    analyzable = sum(1 for c in cleaned if c['quality_flag'] != 'blocked')
    return analyzable / max(stats.total_input, 1)
```

### 7.3 单字段阈值判定

> 来源: ST-RA-05.2-CLEAN LLD §2.5（质量阈值默认值）

| 参数 | 默认值 | 说明 | 超阈值行为 |
|---|---|---|---|
| `null_rate_threshold` | 0.30 (30%) | 必填字段空值占比上限 | 结合 QCOMB-03 判定 |
| `anomaly_rate_threshold` | 0.10 (10%) | 异常值占比上限 | → overall_status='flagged'（未阻断时） |
| `duplicate_rate_threshold` | 0.50 (50%) | source_ticket_id 重复率上限 | → overall_status='blocked' |
| `min_analyzable_ratio` | 0.50 (50%) | 可分析记录占比下限 | 结合 QCOMB-03 判定 |
| `max_conflict_count` | 50 | 单批次冲突数上限 | 结合 QCOMB-05 判定 |

```python
def evaluate_thresholds(report: dict, stats: CleaningStats) -> dict:
    """逐项判定单字段阈值"""
    t = report['thresholds']

    # null_rate
    t['null_rate']['actual'] = stats.null_count / max(stats.total_input, 1)
    t['null_rate']['passed'] = t['null_rate']['actual'] <= t['null_rate']['threshold']

    # anomaly_rate
    t['anomaly_rate']['actual'] = stats.anomaly_count / max(stats.total_input, 1)
    t['anomaly_rate']['passed'] = t['anomaly_rate']['actual'] <= t['anomaly_rate']['threshold']

    # duplicate_rate
    dup_rate = stats.duplicate_count / max(stats.total_input, 1)
    t['duplicate_rate']['actual'] = dup_rate
    t['duplicate_rate']['passed'] = dup_rate <= t['duplicate_rate']['threshold']

    # analyzable_ratio
    t['min_analyzable_ratio']['actual'] = report['analyzable_ratio']
    t['min_analyzable_ratio']['passed'] = report['analyzable_ratio'] >= t['min_analyzable_ratio']['threshold']

    # conflict_count
    t['max_conflict_count']['actual'] = stats.conflict_count
    t['max_conflict_count']['passed'] = stats.conflict_count <= t['max_conflict_count']['threshold']

    return report
```

### 7.4 组合风险规则（QCOMB-01 ~ QCOMB-05）

> 来源: ST-RA-05.2-CLEAN LLD §2.6（CP5 评审 H4 整改）
>
> 判定顺序: QCOMB-01 → QCOMB-02 → QCOMB-03 → QCOMB-04 → QCOMB-05
> 任一条触发 blocked → overall_status='blocked'
> QCOMB-04 不阻断，仅标注 analysis_confidence='degraded'

#### QCOMB-01: 最小关键字段完整率

| 属性 | 值 |
|---|---|
| 触发条件 | 高严重度记录（P1 或 P2+致命/严重）的 `root_cause` 字段 null_rate > 40% |
| 判定结果 | `overall_status = blocked` |
| 优先级 | 高于单字段 null_rate 阈值 |
| 原因 | P1/P2 问题单若无根因字段，分析没有价值 |

```python
def evaluate_qcomb_01(cleaned: list[dict], report: dict) -> bool:
    """QCOMB-01: 高严重度记录的 root_cause 完整率"""
    high_sev = [c for c in cleaned if is_high_severity(c)]
    if not high_sev:
        return False  # 无高严重度记录，不触发

    rc_null = sum(1 for c in high_sev if not c.get('root_cause'))
    rc_null_rate = rc_null / len(high_sev)

    cr = report['combined_rules']['QCOMB-01']
    cr['severity_high_count'] = len(high_sev)
    cr['root_cause_null_count'] = rc_null
    cr['root_cause_null_rate'] = rc_null_rate
    cr['triggered'] = rc_null_rate > 0.40
    return cr['triggered']
```

#### QCOMB-02: 高严重度记录质量不得 flagged

| 属性 | 值 |
|---|---|
| 触发条件 | severity=致命的记录中 quality_flag='blocked' 的数量 > 0 |
| 判定结果 | `overall_status = blocked` |
| 优先级 | 高于 analyzable_ratio |
| 原因 | 致命级问题单必须全部可分析，不允许任何一条被阻断 |

> **严重度判定依据**: `is_high_severity()` 函数（见 §6.3.3）：
> - P1 → 总是高严重度
> - P2 + severity ∈ {致命, 严重} → 高严重度

```python
def evaluate_qcomb_02(cleaned: list[dict], report: dict) -> bool:
    """QCOMB-02: 致命级记录中是否有被 blocked 的"""
    fatal = [c for c in cleaned if c.get('severity') == '致命']
    fatal_blocked = [c for c in fatal if c.get('quality_flag') == 'blocked']

    cr = report['combined_rules']['QCOMB-02']
    cr['fatal_count'] = len(fatal)
    cr['fatal_blocked_count'] = len(fatal_blocked)
    cr['triggered'] = len(fatal_blocked) > 0
    return cr['triggered']
```

#### QCOMB-03: 双因子质量门控

| 属性 | 值 |
|---|---|
| 触发条件 | `analyzable_ratio < 0.5` **AND** `null_rate > 0.25` |
| 判定结果 | `overall_status = blocked` |
| 原因 | 当可分析比例低且空值率高时，无论单项阈值是否通过都阻断 |

```python
def evaluate_qcomb_03(report: dict, stats: CleaningStats) -> bool:
    """QCOMB-03: 双因子门控"""
    ar = report['analyzable_ratio']
    nr = stats.null_count / max(stats.total_input, 1)

    cr = report['combined_rules']['QCOMB-03']
    cr['analyzable_ratio'] = ar
    cr['null_rate'] = nr
    cr['triggered'] = (ar < 0.5) and (nr > 0.25)
    return cr['triggered']
```

#### QCOMB-04: 分析方法降级

| 属性 | 值 |
|---|---|
| 触发条件 | `analyzable_ratio < 0.7` |
| 判定结果 | 报告标注 `analysis_confidence = degraded`（informational） |
| **不阻断** | 仅输出数量/占比，趋势/同比可信度降低 |

```python
def evaluate_qcomb_04(report: dict) -> bool:
    """QCOMB-04: 分析方法降级（informational only）"""
    ar = report['analyzable_ratio']

    cr = report['combined_rules']['QCOMB-04']
    cr['analyzable_ratio'] = ar
    cr['triggered'] = ar < 0.7
    return cr['triggered']
```

#### QCOMB-05: 批量冲突上限

| 属性 | 值 |
|---|---|
| 触发条件 | 冲突数 > 20% 的总记录数 |
| 判定结果 | `overall_status = blocked` |
| 原因 | 冲突过多意味着 schema 或映射有系统性问题，不应硬合并 |

```python
def evaluate_qcomb_05(report: dict, stats: CleaningStats) -> bool:
    """QCOMB-05: 批量冲突上限"""
    conflict_rate = stats.conflict_count / max(stats.total_input, 1)

    cr = report['combined_rules']['QCOMB-05']
    cr['conflict_count'] = stats.conflict_count
    cr['total_fetched'] = stats.total_input
    cr['conflict_rate'] = conflict_rate
    cr['triggered'] = conflict_rate > 0.20
    return cr['triggered']
```

### 7.5 overall_status 综合判定

```python
def determine_overall_status(report: dict) -> str:
    """综合判定批次 overall_status。

    优先级: blocked > flagged > clean

    blocked 条件（任一满足）:
      - duplicate_rate > 50%
      - QCOMB-01 触发（高严重度 root_cause null > 40%）
      - QCOMB-02 触发（致命级记录存在 blocked）
      - QCOMB-03 触发（双因子门控）
      - QCOMB-05 触发（冲突 > 20%）
    """
    blocked_signals = [
        not report['thresholds']['duplicate_rate']['passed'],
        report['combined_rules']['QCOMB-01']['triggered'],
        report['combined_rules']['QCOMB-02']['triggered'],
        report['combined_rules']['QCOMB-03']['triggered'],
        report['combined_rules']['QCOMB-05']['triggered'],
    ]

    if any(blocked_signals):
        report['block_reason'] = build_block_reason(report)
        return 'blocked'

    # flagged 条件
    flagged_signals = [
        not report['thresholds']['anomaly_rate']['passed'],
        report['issues'],  # 有任何 issue
    ]
    if any(flagged_signals):
        return 'flagged'

    # QCOMB-04: 降级标注（不改变 overall_status）
    if report['combined_rules']['QCOMB-04']['triggered']:
        report['analysis_confidence'] = 'degraded'

    return 'clean'


def build_block_reason(report: dict) -> str:
    """构造阻断原因描述"""
    reasons = []
    cr = report['combined_rules']
    t = report['thresholds']

    if not t['duplicate_rate']['passed']:
        reasons.append(f"重复率 {t['duplicate_rate']['actual']:.1%} 超过阈值 {t['duplicate_rate']['threshold']:.0%}")
    if cr['QCOMB-01']['triggered']:
        reasons.append(f"高严重度记录 root_cause 空值率 {cr['QCOMB-01']['root_cause_null_rate']:.1%} > 40%")
    if cr['QCOMB-02']['triggered']:
        reasons.append(f"致命级记录中存在 {cr['QCOMB-02']['fatal_blocked_count']} 条 blocked")
    if cr['QCOMB-03']['triggered']:
        reasons.append(f"双因子门控触发: analyzable={cr['QCOMB-03']['analyzable_ratio']:.2f}, null_rate={cr['QCOMB-03']['null_rate']:.2f}")
    if cr['QCOMB-05']['triggered']:
        reasons.append(f"冲突率 {cr['QCOMB-05']['conflict_rate']:.1%} > 20%")
    return "; ".join(reasons)
```

### 7.6 overall_status 状态机

> 来源: ST-RA-05.2-CLEAN LLD §5

```
       ┌─────────────────────────────────────┐
       │                                     │
       ▼                                     │
   ┌───────┐  all thresholds passed  ┌───────┴──┐
   │ clean  │◄────────────────────────│ pending   │
   └───┬───┘                         └─────┬─────┘
       │                                   │
       │ some issues present               │ threshold exceeded / QCOMB triggered
       ▼                                   ▼
   ┌─────────┐                       ┌─────────┐
   │ flagged  │                       │ blocked  │
   └─────────┘                       └─────────┘
```

| 状态 | 含义 | 对 analysis_run 的影响 |
|---|---|---|
| `clean` | 所有指标通过阈值，无 QCOMB 阻断 | analysis_run 正常创建 |
| `flagged` | 有警告但未超过阻断阈值 | analysis_run 可创建，标注 `risk_warnings: [IngestionQualityReport flagged]` |
| `blocked` | 任一项超过阻断阈值 或 QCOMB 阻断规则触发 | **禁止创建 analysis_run** |

### 7.7 质量报告回写

> 清洗和质量判定完成后，将结果回写到数据库和批次清单。

**回写步骤**：

```
1. 保存质量报告 YAML 文件
   path = f"data/snapshots/batch-{batch_id}-quality-report.yaml"
   quality_report 写入 .yaml 文件

2. 回写 ingestion_batch 表
   DAO: insert_ingestion_batch() 或后续通过 DAO 更新批次记录
   字段: total_cleaned, total_failed, quality_report_ref

3. 回写 batch-manifest.yaml
   manifest['ingestion_result']['total_cleaned'] = stats.total_cleaned
   manifest['ingestion_result']['total_failed'] = stats.total_failed
   manifest['quality_report_ref'] = quality_report_path

4. 若 overall_status='blocked':
   - 不创建 analysis_run
   - 在 batch-manifest 的 errors 中记录 block_reason
   - 该批次 ticket 仍写入 DB（清洗完成的数据保留），但禁止下游分析
```

**DAO 调用约束**（同 §5.1）：
- 只调用 `data/dao.py` 公共函数
- 不直接执行 SQL
- 不修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore`

---

## §8 摄取失败保护

> **本章节由 ST-NRA-03 实现。**
>
> 本章节将 §2-§7 中分散定义的失败处理策略整合为统一的失败保护框架，涵盖 6 类失败场景的分类、逐类处理策略、事务边界保护、幂等性保护和组件降级策略。
> 失败保护的核心原则是**阻止错误传播**：任一步骤失败不污染已落盘数据、不覆盖历史快照、不产生残留部分数据。

### 8.1 失败分类

摄取管线中的失败场景按发生阶段和影响范围分为以下 6 类：

| 类别 | 发生阶段 | 影响范围 | 是否覆盖历史数据 | 详细定义位置 |
|---|---|---|---|---|
| 网络错误 | §2 HTTP GET | 当前批次 | 否 | §2.3 连接超时 |
| HTTP 非 2xx | §2 HTTP GET | 当前批次 | 否 | §2.3 4xx/5xx/3xx |
| 响应解析失败 | §2 → §6 清洗前 | 当前批次 | 否 | 本章 §8.2.3（新增） |
| 快照保存失败 | §3 快照保存 | 当前批次 | 否 | §3.4 失败清理规则 |
| 权限断言失败 | §3 快照保存 | 当前批次 | 否 | §3.3 步骤 5-7 |
| DB 写入失败 | §5 数据库写入 | 当前事务 | 否（回滚） | §5.4 错误处理 |

### 8.2 逐类失败处理策略

#### 8.2.1 网络错误

**触发条件**：DNS 解析失败、TCP 连接超时（>30s）、TLS 握手失败。

**处理**：
- 不创建 `ingestion_batch` 记录
- 不生成快照和 manifest
- 抛出 `HTTPFetchError(recoverable=True)`
- 错误输出：`{error_type: "HTTPFetchError", recoverable: true, reason: "连接超时（>30s）"}`

**设计依据**：§2.3 连接超时处理。不自动重试，由调用方决定重试策略。

#### 8.2.2 HTTP 非 2xx

**触发条件**：HTTP 4xx（客户端错误）、5xx（服务端错误）、3xx（重定向）。

**处理**：
- 不创建 `ingestion_batch` 记录
- 不生成快照和 manifest
- 抛出 `HTTPFetchError(recoverable=False)`
- 错误输出：`{error_type: "HTTPFetchError", recoverable: false, http_status: <code>, reason: "ITR 返回错误状态 {http_status}"}`

**设计依据**：§2.3 响应处理。4xx/5xx/3xx 均视为不可恢复错误。

#### 8.2.3 响应 JSON 解析失败

**触发条件**：HTTP 200 但响应体不是合法 JSON（截断、编码损坏、非 JSON 格式）。

> 本场景为本章节新增，§2-§7 未单独定义。

**处理**：
```
1. 将原始响应体保存到 data/snapshots/batch-{batch_id}-parse_error.raw
   - 文件权限 0600
   - 文件名以 .raw 结尾（区别于 .json 快照）
2. 记录 parse_error 元数据：
   - batch_id、request_url、http_status（200）、response_size_bytes
   - parse_error_type（如 "JSONDecodeError"）、error_position（行号/列号）
3. 不创建 ingestion_batch 数据库记录
4. 不进入清洗管线
5. 返回错误：
   {error_type: "ParseError", recoverable: false, reason: "ITR 响应 JSON 解析失败: {parse_error_detail}", raw_ref: "data/snapshots/batch-{batch_id}-parse_error.raw"}
```

**设计依据**：原始保存策略与 §3.2 一致（保留原始数据供追溯），但标记为 parse_error 以阻断后续处理。不创建 batch 记录，不进入清洗管线。

#### 8.2.4 快照保存失败

**触发条件**：磁盘空间不足（<100MB）、目录权限异常、原子替换失败。

**处理**（详见 §3.4）：
1. 删除本批次临时文件（`.tmp`）
2. 删除本批次已写入但未完成校验的快照文件
3. 不创建 `ingestion_batch` 数据库记录
4. 停止本批次摄取

**设计依据**：§3.3 保存算法步骤 0/5/7、§3.4 失败清理规则。

#### 8.2.5 权限断言失败

**触发条件**：快照文件权限 chmod 后实际权限 ≠ 0600，或最终校验时正式文件权限异常。

**处理**（详见 §3.3 步骤 5-7）：
- 删除临时文件和本批次所有未提交数据
- 停止摄取
- 抛出 `SnapshotSaveError(recoverable=False)`，原因包含期望权限与实际权限

**设计依据**：§3.3 步骤 5-7。权限失败的不可恢复性由 HLD REV-03 §可信分析治理约束决定。

#### 8.2.6 DB 写入失败

**触发条件**：`sqlite3.IntegrityError`（唯一性冲突）、`ValueError`（字段校验失败）、连接断开、磁盘 I/O 错误。

**处理**（详见 §5.4）：
- 事务回滚（`rollback(conn)`）
- 快照文件和 manifest 保留（可作为重试输入）
- 数据库不残留未完成数据

**设计依据**：§5.4 错误处理、§5.3 事务边界。

### 8.3 事务边界保护

摄取管线的写入操作按批次划分事务边界：

| 操作 | 事务边界 | 回滚范围 | 残留风险 |
|---|---|---|---|
| 插入 `ingestion_batch` | 一个 `BEGIN..COMMIT` | 整条 batch 记录 | 无 |
| 批量写入 ticket + ticket_version + change_history | 一个 `BEGIN..COMMIT` 包裹整批 | 本批次所有 ticket/ticket_version/change_history | 无 |

**事务保护规则**：
```
1. 单批次单事务：整个批次的 ticket、ticket_version、change_history 写入在同一个事务中
2. 任一步骤失败 → 调用 rollback(conn) → 整批回滚
3. 回滚后不残留部分数据：
   - ticket 表中的部分 INSERT 不留下
   - ticket_version 表中的部分版本记录不留下
   - change_history 表中的部分变更记录不留下
4. 快照和 manifest 在事务外保存（文件系统无事务），回滚后保留供重试
```

**设计依据**：§5.3 `write_ingestion_result()` 伪代码中 `begin_transaction(conn)` / `commit(conn)` / `rollback(conn)` 的包裹结构、§5.4 DB 写入失败处理。

### 8.4 幂等性保护

摄取管线的幂等性由两层机制保护：

#### 8.4.1 batch_id 去重

| 属性 | 值 |
|---|---|
| 触发条件 | `insert_ingestion_batch()` 时 batch_id 已存在 |
| 处理 | 由 DAO 层 `UNIQUE(batch_id)` 约束触发 `sqlite3.IntegrityError` → 事务回滚 |
| 用户可见行为 | 返回错误 `"batch_id 重复: {batch_id}"`，不覆盖已有 batch 数据 |

**设计依据**：`data/schema.sql` 中 `ingestion_batch.batch_id UNIQUE` 约束。

#### 8.4.2 source_ticket_id 去重

| 属性 | 值 |
|---|---|
| 触发条件 | S1 首次摄取时 `source_ticket_id` 已存在于 ticket 表 |
| 处理 | `get_ticket_by_source_id()` 返回已有记录 → 跳过不写入（S1 不处理变更） |
| S2 行为 | 走变更检测路径（`upsert_ticket` + 版本历史），由 ST-RA-06.1-DETECT 处理 |

**设计依据**：§5.3 步骤 2a-2b（existing != None → CONTINUE）。

#### 8.4.3 同批次内重复

| 属性 | 值 |
|---|---|
| 触发条件 | 同批次响应中同一条 `source_ticket_id` 出现多次 |
| 处理 | 清洗管线 `detect_duplicates()` 保留第一条，后续标记为重复 |
| 用户可见行为 | `quality_report.duplicate_count++`，不影响 overall_status（除非超阈值） |

**设计依据**：§6.3.4 重复检测。

### 8.5 降级策略

当摄取管线的某个组件失败时，降级行为遵循"不传播错误"原则：

| 组件 | 失败时降级行为 | 对下游的影响 | 恢复方式 |
|---|---|---|---|
| Allowlist 校验 | 停止，不发起 HTTP 请求 | 无（未产生任何数据） | 修正 URL/参数后重试 |
| HTTP GET | 停止，不创建 batch | 无（未产生任何数据） | 网络恢复后重试（需用户决定） |
| 响应解析 | 保存原始响应为 `.parse_error.raw`，停止 | batch 不创建 | 手工检查原始响应后修正 |
| 快照保存 | 删除本批次临时/未提交数据，停止 | batch 不创建 | 清理磁盘/修复权限后重试 |
| 字段清洗（非必填） | 记录为 `FailedRecord`，不影响其他记录 | 该条记录不写入 ticket | 修正 ITR 数据源后重试 |
| 字段清洗（必填缺失） | `quality_report.overall_status='blocked'`，整批不创建 analysis_run | ticket 已写入但禁止分析 | 修正 ITR 数据源后重试 |
| DB 写入 | 事务回滚，快照和 manifest 保留 | batch 数据不在 DB 中 | 从快照重放摄取 |
| 质量报告生成 | 报告文件写入失败，清洗数据已写入 DB | 缺少质量报告，但不影响数据 | 从已清洗数据重新生成报告 |

**降级优先级**：
1. **已有数据安全** > 新数据摄入
2. **可追溯性** > 完整性（快照保存失败才删除临时文件，DB 回滚才放弃写入）
3. **用户可见** > 静默处理（所有错误输出结构化错误信息）

**设计依据**：§2-§7 各章节的失败处理规则、FEAT-RA-INGESTION DESIGN §4.3 失败路径。

---

## §9 S2 变更检测与版本历史

> **本章节由 ST-RA-06.1-DETECT 实现。**
>
> S2 增量摄取阶段消费清洗后的新批次 ticket（来自 ST-RA-05.2-CLEAN），与数据库中已有记录逐条比对，计算字段级差异，判定语义冲突，执行自动合并或进入人工冲突队列，并写入版本历史和变更记录。
>
> **设计依据**: ST-RA-06.1-DETECT LLD v1.2 §2-§4、§6、§12。
> **依赖**: `data/dao.py`（公共 DAO 接口，只调用，不修改），`skills/itr-ticket-ingestion/templates/conflict-queue.yaml`（冲突队列模板）。

### 9.1 变更检测入口

S2 增量摄取时，在清洗管线完成（§6）和清洗结果写入数据库之后调用变更检测管线。

```
── 输入 ──
new_batch: list[dict]   (来自 ST-RA-05.2 的 CleanResult.cleaned)
batch_ref: str          (batch_id)
conn: sqlite3.Connection
          │
          ▼
┌─ S2 增量摄取主流程 ─────────────────────────────────────┐
│                                                          │
│  1. 加载已有数据                                          │
│     existing_map = {}                                     │
│     FOR each record in new_batch:                         │
│       sid = record['source_ticket_id']                    │
│       IF sid IS NOT None:                                 │
│         existing = get_ticket_by_source_id(conn, sid)     │
│         existing_map[sid] = existing                      │
│                                                          │
│  2. 逐条变更检测（见 §9.2-§9.3）                          │
│     对每条 record 执行：字段 diff → 冲突判定 → 分类       │
│     产出：new_list, modified_list, unchanged_list,        │
│            conflict_list                                  │
│                                                          │
│  3. 写入数据库（事务包裹，见 §9.5）                       │
│                                                          │
│  4. 生成冲突队列文件（见 §9.4）                           │
│     若 conflict_list 非空 → 写入 conflict-queue.yaml     │
│                                                          │
│  5. 返回 ChangeResult                                    │
│     {new, modified, unchanged, conflicts, stats}          │
└────────────────────────────────────────────────────────────┘
```

**ChangeResult 结构**：

```python
@dataclass
class ChangeResult:
    new: list[dict]                  # 新增 ticket 记录
    modified: list[ModifiedRecord]   # 已变更记录
    unchanged: list[str]             # 未变化的 source_ticket_id 列表
    conflicts: list[ConflictRecord]  # 冲突队列项
    stats: ChangeStats               # 统计信息

@dataclass
class ModifiedRecord:
    source_ticket_id: str
    ticket_id: int                   # 数据库中已有记录的 id
    previous_status: str | None
    field_diffs: dict                # {field_name: {old: value, new: value}}
    ticket_record: dict              # 清洗后的完整 record（用于 upsert）

@dataclass
class ConflictRecord:
    source_ticket_id: str | None     # None 表示无稳定 ID
    reason: str                      # 'missing_id' | 'semantic_conflict' | 'irreconcilable'
    new_record: dict                 # 新批次中的记录
    existing_record: dict | None     # 数据库中已有记录（如存在）
    suggested_resolution: str        # 'manual_review' | 'keep_existing' | 'keep_new'
    created_at: str                  # ISO8601

@dataclass
class ChangeStats:
    total_input: int
    count_new: int
    count_modified: int
    count_unchanged: int
    count_conflict: int
```

### 9.2 字段差异计算

#### 9.2.1 逐条匹配与分类

对 `new_batch` 中的每条记录执行以下判定：

```
FOR each record in new_batch:
    sid = record.get('source_ticket_id')

    a. 无稳定 ID:
       IF sid IS None OR sid == '':
         conflict_list.append(ConflictRecord(
           reason='missing_id', source_ticket_id=None,
           new_record=record, existing_record=None,
           suggested_resolution='manual_review'
         ))
         CONTINUE

    b. 匹配已有记录:
       existing = existing_map.get(sid)
       IF existing IS None:
         new_list.append(record)
         CONTINUE

    c. 计算字段 diff:
       diffs = compute_field_diff(existing, record)
       IF diffs IS EMPTY:
         unchanged_list.append(sid)
         CONTINUE

    d. 冲突判定:
       conflict_fields = check_semantic_conflict(diffs)
       IF conflict_fields IS NOT EMPTY:
         conflict_list.append(ConflictRecord(
           reason='semantic_conflict', source_ticket_id=sid,
           new_record=record, existing_record=existing,
           suggested_resolution='manual_review'
         ))
         CONTINUE

    e. 自动合并:
       modified_list.append(ModifiedRecord(
         ticket_id=existing['id'],
         previous_status=existing.get('status'),
         field_diffs=diffs,
         ticket_record=record
       ))
```

#### 9.2.2 compute_field_diff 算法

```python
def compute_field_diff(existing: dict, incoming: dict,
                       exclude_fields: set = None) -> dict:
    """
    逐字段比较已有记录与新记录。
    返回: {field_name: {old: value, new: value}}
    """
    exclude_fields = exclude_fields or {
        'first_seen_at',   # 由系统维护（仅首次 INSERT 写入）
        'created_at',      # 由数据库自动维护
        'last_seen_at',    # 在 upsert 时统一更新
        'quality_flag',    # 由清洗流程独立管理
        'raw_json'         # 每次拉取独立保存
    }
    diffs = {}
    for key in incoming:
        if key in exclude_fields:
            continue
        old_val = existing.get(key)
        new_val = incoming.get(key)
        if old_val != new_val:
            diffs[key] = {'old': old_val, 'new': new_val}
    return diffs
```

**排除字段说明**：

| 排除字段 | 排除原因 |
|---|---|
| `first_seen_at` | 只在首次 INSERT 时写入，后续不变（HLD 数据模型定义） |
| `created_at` | 数据库自动维护的时间戳 |
| `last_seen_at` | 在 upsert 时统一刷新，不作为语义变更 |
| `quality_flag` | 由 §6 清洗流程独立管理，变更检测不修改 |
| `raw_json` | 每次 ITR 拉取独立保存，不作为语义变更 |

### 9.3 语义字段冲突判定

#### 9.3.1 冲突判定规则

处理 `compute_field_diff()` 产出的 `field_diffs` 时，按以下规则判定是否进入人工冲突队列：

| 字段 | 判定 | 规则 |
|---|---|---|
| `status` | **冲突** | status 的任何非空变更都需人工判断（可能为合法工作流变更，也可能为 ITR 数据错误） |
| `severity` | **冲突** | 严重度升降级需人工确认是否为真实变化 |
| `product` | **冲突** | product 是核心归属字段，变更意味着问题被重新分类 |
| `module` | **冲突**（条件） | module 从非空变为空 → 信息丢失，需人工判断；从空变为非空或值变更 → 自动合并 |
| `title`, `description` | **自动合并** | 文本级 diff 保留在 field_diffs 中 |
| `openeddate`, `resolveddate` | **自动合并** | 时间字段变更可直接接受 |
| `root_cause`, `test_missed_analysis` | **自动合并** | 分析字段变更可直接接受 |
| `test_missed_phase`, `improvement_measures` | **自动合并** | 措施字段变更可直接接受 |

**冲突字段白名单**: `{status, severity, product}` — 这些字段的任何非空变更视为语义冲突。

#### 9.3.2 check_semantic_conflict 算法

```python
SEMANTIC_CONFLICT_FIELDS = {'status', 'severity', 'product'}

def check_semantic_conflict(field_diffs: dict) -> dict:
    """筛选出需要人工判断的冲突字段。

    返回: {field_name: {old: value, new: value}}  冲突字段子集。
    返回空 dict 表示无冲突，可自动合并。
    """
    conflicts = {}
    for field, diff in field_diffs.items():
        if field in SEMANTIC_CONFLICT_FIELDS:
            # status/severity/product 的任何非空变更都是语义冲突
            if diff['new'] is not None and diff['new'] != '':
                conflicts[field] = diff
        elif field == 'module':
            # module 从非空变为空 = 信息丢失 → 冲突
            if diff['old'] and not diff['new']:
                conflicts[field] = diff
    return conflicts
```

**变更类型枚举**：

| change_type | 含义 | 触发条件 | 版本行为 |
|---|---|---|---|
| `new` | 新的 source_ticket_id | 数据库中无匹配记录 | INSERT ticket(version=1) + ticket_version(1) + change_history |
| `modified` | 字段值有变更（可自动合并） | field_diffs 非空且无冲突 | upsert ticket + 新增 ticket_version(N+1) + change_history |
| `unchanged` | 已有记录无变化 | field_diffs 为空 | 不更新 ticket，不新增 ticket_version，仅 insert change_history |
| `conflict` | 无法自动合并 | 无稳定 ID 或语义冲突 | 进入 conflict_queue，不写入 ticket |

**冲突解决枚举**：

| resolution | 含义 | 触发条件 | 后续动作 |
|---|---|---|---|
| `auto_merged` | 自动合并 | field_diffs 中无冲突字段 | 正常 upsert |
| `manual_queue` | 进入人工处理队列 | 无 source_ticket_id 或语义冲突 | 记录在 conflict-queue.yaml，等待人工 reviewer |
| `rejected` | 人工拒绝合并 | reviewer 决定保留旧版本 | 不写入新记录，change_history 标记 |

### 9.4 无稳定 ID 与冲突队列

#### 9.4.1 无稳定 ID 处理

当 `source_ticket_id` 为空或缺失时，该条记录**不写入 ticket 表**，而是进入冲突队列供人工处理。

**处理流程**：

```
1. 创建 ConflictRecord:
   - source_ticket_id: None
   - reason: 'missing_id'
   - new_record: 完整的清洗后记录
   - existing_record: None
   - suggested_resolution: 'manual_review'
   - created_at: ISO8601 时间戳

2. 写入冲突队列文件（见 §9.4.2）获取 conflict_ref

3. 写入 change_history:
   - ticket_id: None（无稳定 ID）
   - batch_ref: 当前批次 ID
   - change_type: 'conflict'
   - affected_fields: None
   - resolution: 'manual_queue'
   - conflict_ref: 冲突队列文件中的引用

   调用: insert_change_history(conn, None, batch_ref, 'conflict',
                                None, 'manual_queue', conflict_ref)
```

**安全约束**：
- 不自动生成 ID（不伪造 source_ticket_id）
- 不静默丢弃记录（所有冲突均有 change_history 和 conflict-queue.yaml 留痕）
- DAO 层校验：`ticket_id` 为 None 时 `conflict_ref` 必填；缺失则 DAO 抛出 `ValueError`

#### 9.4.2 冲突队列文件

冲突队列模板路径：`skills/itr-ticket-ingestion/templates/conflict-queue.yaml`

生成时写入实际输出目录（如 `data/snapshots/batch-{batch_id}-conflicts.yaml`）。

```yaml
# conflict-queue.yaml — ITR 摄取冲突队列
# 模板文件: skills/itr-ticket-ingestion/templates/conflict-queue.yaml
# 本文件由 itr-ticket-ingestion Skill 在 S2 变更检测后自动生成
# 人工 reviewer 需逐条填写 reviewer_decision 和 resolution_timestamp

batch_ref: "string"
generated_at: "ISO8601"
conflicts:
  - index: 0
    source_ticket_id: null | "string"
    reason: "missing_id | semantic_conflict | irreconcilable"
    new_record_summary:
      product: "string"
      title: "string"
      severity: "string"
    existing_record_summary:
      source_ticket_id: "string"
      first_seen_at: "string"
      last_seen_at: "string"
      status: "string"
    field_conflicts:
      - field: "status"
        existing: "已关闭"
        new: "重新打开"
    suggested_resolution: "manual_review | keep_existing | keep_new"
    reviewer_decision: ""         # 人工回填: 'keep_existing' | 'keep_new' | 'rejected'
    resolution_timestamp: ""      # 人工回填: ISO8601
```

**冲突队列生成流程**：

```
function write_conflict_queue(conflict_list, batch_id, output_dir):
    IF conflict_list IS EMPTY:
      RETURN (None, 0)  # 无冲突，不生成文件

    # 按 conflict-queue.yaml 模板组装记录
    queue = {
        "batch_ref": batch_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "conflicts": []
    }

    FOR idx, conflict in enumerate(conflict_list):
        entry = {
            "index": idx,
            "source_ticket_id": conflict.source_ticket_id,
            "reason": conflict.reason,
            "new_record_summary": {
                "product": conflict.new_record.get("product"),
                "title": conflict.new_record.get("title"),
                "severity": conflict.new_record.get("severity"),
            },
            "existing_record_summary": (
                {
                    "source_ticket_id": conflict.existing_record.get("source_ticket_id"),
                    "first_seen_at": conflict.existing_record.get("first_seen_at"),
                    "last_seen_at": conflict.existing_record.get("last_seen_at"),
                    "status": conflict.existing_record.get("status"),
                }
                if conflict.existing_record else None
            ),
            "field_conflicts": _extract_field_conflicts(conflict),
            "suggested_resolution": conflict.suggested_resolution,
            "reviewer_decision": "",
            "resolution_timestamp": "",
        }
        queue["conflicts"].append(entry)

    # 写入文件
    output_path = f"{output_dir}/batch-{batch_id}-conflicts.yaml"
    with open(output_path, "w") as f:
        yaml.dump(queue, f, default_flow_style=False, allow_unicode=True)

    RETURN (output_path, len(conflict_list))
```

**冲突队列写入失败处理**：
- 若冲突队列 YAML 文件写入失败（磁盘满、权限错误等），终止该批次事务并保留错误摘要
- 不得在无 `conflict_ref` 的情况下提交 `change_history` 记录——避免产生无法定位的冲突记录
- 整个批次事务回滚；快照文件和 manifest 保留供重试（同 §8.3 事务边界保护）

### 9.5 版本历史写入

#### 9.5.1 数据库写入流程（事务包裹）

```
function write_s2_results(conn, new_list, modified_list, unchanged_list,
                           conflict_list, batch_ref):
    begin_transaction(conn)

    TRY:
        # 1. 新增 ticket
        FOR each record in new_list:
            ticket_id = insert_ticket(conn, record)
            # version=1，首次无上一版本
            insert_ticket_version(conn, ticket_id, 1,
              None, "{}", batch_ref)
            insert_change_history(conn, ticket_id, batch_ref,
              change_type='new', resolution='auto_merged')

        # 2. 未变化 ticket
        FOR each sid in unchanged_list:
            existing = get_ticket_by_source_id(conn, sid)
            insert_change_history(conn, existing['id'], batch_ref,
              change_type='unchanged')
            # 不更新 ticket，不新增 ticket_version

        # 3. 自动合并 ticket
        FOR each mod in modified_list:
            diff_str = json.dumps(mod.field_diffs, ensure_ascii=False)
            affected = json.dumps(list(mod.field_diffs.keys()), ensure_ascii=False)

            # 更新 ticket 主表
            upsert_ticket(conn, mod.ticket_record, mod.field_diffs)

            # 新增版本记录
            version = get_next_version(conn, mod.ticket_id)
            insert_ticket_version(conn, mod.ticket_id, version,
              mod.previous_status, diff_str, batch_ref)

            # 变更历史
            insert_change_history(conn, mod.ticket_id, batch_ref,
              change_type='modified', affected_fields=affected,
              resolution='auto_merged')

        # 4. 冲突记录（先写队列文件获取 ref，再写 change_history）
        FOR each conflict in conflict_list:
            conflict_ref = _write_conflict_queue_entry(conflict, batch_ref)
            ticket_id = (
                get_ticket_by_source_id(conn, conflict.source_ticket_id)['id']
                if conflict.source_ticket_id else None
            )
            insert_change_history(conn, ticket_id, batch_ref,
              change_type='conflict', resolution='manual_queue',
              conflict_ref=conflict_ref)
            # 冲突不写入 ticket 表，不变更 ticket_version

        commit(conn)
        RETURN ChangeResult(...)

    EXCEPT Exception as e:
        rollback(conn)
        # 快照和 manifest 保留供重试
        → 记录错误并抛出
```

**关键 DAO 调用**：

| 操作 | DAO 方法 | 说明 |
|---|---|---|
| 插入新 ticket | `insert_ticket(conn, ticket)` | 首次插入，source_ticket_id 自动校验 |
| 更新已有 ticket | `upsert_ticket(conn, ticket, field_diffs)` | 只更新有变化的字段 + last_seen_at |
| 插入版本记录 | `insert_ticket_version(conn, ticket_id, version, previous_status, field_diffs, batch_ref)` | version 号通过 `get_next_version()` 获取 |
| 插入变更记录 | `insert_change_history(conn, ticket_id, batch_ref, change_type, affected_fields, resolution, conflict_ref)` | conflict_ref 用于无稳定 ID 场景 |
| 查询已有 ticket | `get_ticket_by_source_id(conn, source_ticket_id)` | 按 source_ticket_id 匹配 |
| 事务管理 | `begin_transaction(conn)` / `commit(conn)` / `rollback(conn)` | 整个批次在单个事务中 |

#### 9.5.2 ticket_version 写入规范

```python
def build_version_record(ticket_id: int, existing_record: dict,
                         field_diffs: dict, batch_ref: str,
                         conn: sqlite3.Connection) -> dict:
    """
    构建 ticket_version 写入字典。
    version 号由 get_next_version() 获取。
    field_diffs 序列化为 JSON string。
    previous_status 从 existing_record 中提取。
    返回: 可供 DAO insert_ticket_version() 调用的参数字典。
    """
    return {
        'ticket_id': ticket_id,
        'version': get_next_version(conn, ticket_id),
        'previous_status': existing_record.get('status'),
        'field_diffs': json.dumps(field_diffs, ensure_ascii=False),
        'batch_ref': batch_ref
    }
```

**field_diffs JSON 格式**：

```json
{
  "title": {"old": "旧标题", "new": "新标题"},
  "status": {"old": "已关闭", "new": "重新打开"},
  "severity": {"old": "一般", "new": "致命"}
}
```

#### 9.5.3 change_history 写入规范

| change_type | ticket_id | resolution | affected_fields | conflict_ref | 说明 |
|---|---|---|---|---|---|
| `new` | 有效 ID | `auto_merged` | None | None | 首次摄取创建 |
| `modified` | 有效 ID | `auto_merged` | JSON array | None | 自动合并的字段变更 |
| `unchanged` | 有效 ID | None | None | None | 每批次记录无变化事实 |
| `conflict`（有 ID） | 有效 ID | `manual_queue` | None | 有效引用 | 语义冲突，等待 reviewer |
| `conflict`（无 ID） | **None** | `manual_queue` | None | 有效引用 | 无稳定 ID，等待 reviewer |

**无稳定 ID 场景调用示例**：

```python
# source_ticket_id 缺失时的 change_history 调用
conflict_ref = "data/snapshots/batch-20260716-001-conflicts.yaml#conflicts[0]"
insert_change_history(
    conn,
    ticket_id=None,          # 无稳定 ID
    batch_ref=batch_ref,
    change_type='conflict',
    affected_fields=None,
    resolution='manual_queue',
    conflict_ref=conflict_ref  # 必填，指向冲突队列条目
)
```

### 9.6 变更摘要生成

#### 9.6.1 ChangeResult 回写

变更检测完成后，将统计结果回写到 `batch-manifest.yaml` 的 `ingestion_result` 字段：

```yaml
ingestion_result:
  total_fetched: 150       # 来自清洗管线
  total_new: 12            # 新增 ticket 数
  total_updated: 8         # 自动合并（modified）数
  total_unchanged: 120     # 无变化数
  total_conflict: 10       # 冲突数
  total_cleaned: 150       # 来自清洗管线（已填充）
  total_failed: 0          # 来自清洗管线（已填充）
```

**变更摘要输出格式**：

```json
{
  "batch_id": "batch-20260716-002",
  "change_result": {
    "total_input": 150,
    "count_new": 12,
    "count_modified": 8,
    "count_unchanged": 120,
    "count_conflict": 10
  },
  "conflict_queue_ref": "data/snapshots/batch-20260716-002-conflicts.yaml",
  "has_conflicts": true,
  "errors": []
}
```

#### 9.6.2 对下游的交付契约

| 数据 | 格式 | 消费对象 | 说明 |
|---|---|---|---|
| `ChangeResult` | `new` + `modified` + `unchanged` + `conflicts` + `stats` | ST-RA-06.2-REFRESH（FEAT-RA-ANALYSIS） | 决定哪些 ticket 需要增量重算 |
| `ticket_version` 历史 | 通过 DAO `get_ticket_versions()` 查询 | 环比/同比分析 | 消费版本链 |
| `conflict-queue.yaml` | 模板格式 YAML | 人工 reviewer | 逐条处理冲突 |

### 9.7 错误处理

| 错误场景 | 处理策略 | 降级行为 |
|---|---|---|
| source_ticket_id 缺失 | 进入 conflict_queue（reason='missing_id'），写入 change_history（ticket_id=None, conflict_ref 必填） | 该条记录不写入 ticket，批次中其他记录正常处理 |
| status/severity/product 变更 | 进入 conflict_queue（reason='semantic_conflict'） | 该条记录不更新，保留旧版本 |
| module 字段从有值变为空 | 进入 conflict_queue | 该条记录不更新 |
| 数据库查询异常（已有 ticket 查询失败） | 记录错误 → 该条按 `new` 处理（首次） | 可能导致重复 ticket，但 source_ticket_id UNIQUE 约束会捕获 |
| ticket_version 写入 UNIQUE 冲突 | 事务回滚 | 批次不保存，检查 version 号生成逻辑 |
| 事务提交失败（磁盘满等） | 事务回滚 | 批次全部不保存，已有数据安全 |
| 冲突队列文件写入失败 | 终止该批次事务并保留错误摘要；不得声称已持久化冲突 | 无审计 `conflict_ref` 时不得提交 change_history |

**降级原则**：
- 不静默合并冲突项
- 无稳定 ID 是阻断条件，不自动生成 ID
- 其余记录独立处理：一条记录的冲突不影响其他记录的正常写入
- 同一批次内所有写入（ticket、ticket_version、change_history）在同一事务中完成或全部回滚

### 9.8 变更记录生命周期

```
新批次到来
    │
    ├─ 无 source_ticket_id ──► conflict (manual_queue)
    │                         change_history(ticket_id=None, conflict_ref=...)
    │                         ──► reviewer 决策 ──┬─► rejected
    │                                             └─► 手工创建 ticket
    │
    ├─ 首次出现 ──► new (auto_merged)
    │              insert_ticket + ticket_version(1) + change_history
    │
    ├─ 无变化 ──► unchanged
    │             ticket 不变，仅 change_history 记录
    │
    ├─ 字段变更 + 语义冲突 ──► conflict (manual_queue)
    │                         change_history(ticket_id=..., conflict_ref=...)
    │                         ──► reviewer 决策 ──┬─► auto_merged（批准合并）
    │                                             └─► rejected（拒绝变更）
    │
    └─ 字段变更 + 无冲突 ──► modified (auto_merged)
                             upsert_ticket + ticket_version(N+1) + change_history
```

### 9.9 与相邻模块的集成契约

#### 9.9.1 对 ST-RA-05.2-CLEAN（上游）的输入约定

| 输入 | 格式 | 要求 |
|---|---|---|
| `new_batch` | `list[dict]` | CleanResult.cleaned：清洗后、已映射、含 quality_flag 的 ticket 字典 |
| `batch_ref` | `str` | 批次唯一标识 |

#### 9.9.2 对 ST-RA-INGEST-DB 的 DAO 调用

本 Skill 只调用 `data/dao.py` 中的公共函数，不直接执行 SQL。可调用的接口：

| 函数 | 用途 | 调用阶段 |
|---|---|---|
| `get_connection()` | 创建数据库连接 | 写入前 |
| `begin_transaction(conn)` | 开始事务 | 写入前 |
| `commit(conn)` | 提交事务 | 写入成功后 |
| `rollback(conn)` | 回滚事务 | 写入失败时 |
| `get_ticket_by_source_id(conn, source_id)` | 查询 ticket 是否存在 | S2 匹配已有记录 |
| `insert_ticket(conn, ticket)` | 插入新 ticket | new 记录 |
| `upsert_ticket(conn, ticket, field_diffs)` | 插入或更新 ticket | modified 记录 |
| `insert_ticket_version(conn, ...)` | 插入版本历史 | new / modified |
| `get_next_version(conn, ticket_id)` | 获取下一版本号 | new / modified |
| `insert_change_history(conn, ...)` | 插入变更历史 | 所有变更类型 |

**禁止操作**：
- 不直接执行 `conn.execute(...)` SQL 语句
- 不修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore`
- 不绕过 DAO 校验函数（`validate_ticket()`、`validate_change_type()`、`validate_resolution()` 等）

#### 9.9.3 对人工 reviewer 的契约

| 承诺 | 实现 |
|---|---|
| 冲突可见 | `conflict-queue.yaml` 列出每个冲突的源、现有记录、差异字段和建议方案 |
| 决策可追溯 | reviewer 回填 `reviewer_decision` + `resolution_timestamp` |
| 不自动覆盖 | 冲突项在 reviewer 决策前不写入 ticket 表 |
| 无 ID 记录可定位 | `conflict_ref` 指向冲突队列条目 + change_history 留痕 |

### 9.10 开放项与假设

#### 开放项

| ID | 描述 | 状态 | 影响 |
|---|---|---|---|
| O-DET-01 | 冲突字段白名单 `{status, severity, product}` 是否完整 | OPEN | 可能需要追加更多语义冲突字段 |
| O-DET-02 | 大规模批次（>1000 条）的变更检测性能 | OPEN（延后至性能 CR） | 可能需要批量查询优化 |

#### 假设

| ID | 假设 | 依据 | 风险 |
|---|---|---|---|
| A-DET-01 | source_ticket_id 在不同批次间保持稳定 | ITR 工单 ID 是持久化唯一标识 | 低 |
| A-DET-02 | 同批次内不会有同一 source_ticket_id 出现两次（已在 ST-RA-05.2 去重） | 清洗流程的批次内去重 | 低 |
| A-DET-03 | 自动合并的字段变更不会导致语义不一致 | 非冲突字段是可安全合并的文本/元数据 | 中（需持续观察） |
| A-DET-04 | `first_seen_at` 只在首次 INSERT 时写入，后续不变 | HLD 数据模型定义 | 低 |
| A-DET-05 | `quality_flag` 由清洗流程独立管理，变更检测不修改 | ST-RA-05.2-CLEAN 的职责 | 低 |

### 9.11 不适用边界（S2 变更检测）

本 §9 **不负责**以下事项：

- 不执行 HTTP 请求或 ITR 数据拉取（由 §1-§5 负责）
- 不执行字段映射、清洗或质量报告生成（由 §6-§7 负责）
- 不处理冲突队列中 reviewer 决策后的回写逻辑（属于人工工作流或后续 Story）
- 不执行分析计算或环比/同比聚合（由 FEAT-RA-ANALYSIS 负责）
- 不修改 `data/dao.py`、`data/schema.sql`、`data/.gitignore`

---

## 输出格式

成功执行后，本 Skill 返回结构化摘要：

```json
{
  "batch_id": "batch-20260716-001",
  "snapshot_ref": "data/snapshots/batch-20260716-001-raw.json",
  "manifest_ref": "data/snapshots/batch-20260716-001-manifest.yaml",
  "response_hash": "sha256:abc123def456...",
  "total_fetched": 150,
  "total_inserted": 120,
  "http_status": 200,
  "errors": []
}
```

**字段说明**：

| 字段 | 说明 |
|---|---|
| `batch_id` | 批次唯一标识 |
| `snapshot_ref` | 原始快照文件路径 |
| `manifest_ref` | 批次清单文件路径 |
| `response_hash` | 响应体 sha256 哈希 |
| `total_fetched` | ITR 返回的 ticket 总数 |
| `total_inserted` | 成功写入数据库的新 ticket 数 |
| `http_status` | HTTP 响应状态码 |
| `errors` | 错误列表（空数组表示完全成功） |

---

## 失败处理

### 错误类型与降级

| 错误类型 | recoverable | 降级行为 | 对下游影响 |
|---|---|---|---|
| `HTTPMethodDeniedError` | false | 不发起请求 | 批次不创建 |
| `AllowlistDeniedError` | false | 不发起请求 | 批次不创建 |
| `CredentialDeniedError` | false | 不发起请求 | 批次不创建 |
| `HTTPFetchError`（超时） | true | 不创建 batch，不写快照 | 批次失败 |
| `HTTPFetchError`（4xx/5xx） | false | 不创建 batch，不写快照 | 批次失败 |
| `SnapshotSaveError` | false | 删除本批次临时/未提交数据，停止 | 批次失败 |
| DAO 写入异常 | false | 事务回滚，快照保留 | 批次数据不在 DB 中 |

### 错误信息格式

所有错误返回包含人类可读的 `error_reason`、`recoverable` 标记和结构化 `details`：

```json
{
  "error": "AllowlistDeniedError",
  "error_reason": "URL 不在白名单中: http://evil.example.com/api",
  "recoverable": false,
  "details": {
    "url": "http://evil.example.com/api",
    "allowlist_entries": ["http://<IP_ADDRESS>/itr/v1/itrs"]
  }
}
```

### 降级原则

- 不自动重试 HTTP 请求（外部系统，重试策略需用户明确）
- 失败不覆盖任何历史快照或 batch 记录
- 分页成功部分保留（已保存的快照不变，batch 标记 partial），失败页可单独重试
- 每种错误输出 `error_reason` + `recoverable` + `details`

---

## 停止条件

以下任一条件满足时，摄取流程立即停止：

1. Allowlist 校验失败（方法、URL、参数、认证头任一不通过）
2. `RuntimeDataGovernanceReport.status != "compliant"`
3. HTTP GET 返回非 2xx
4. HTTP GET 超时（>30s）
5. 磁盘空间不足（<100MB）
6. 快照权限设置/校验失败（非 0600）
7. 数据库事务写入异常
8. 分页过程中某一页失败（已成功页的快照保留）
9. 用户主动中断

---

## 不适用边界

本 Skill **不负责**以下事项：

- 不连接 ITR 以外的外部系统（TAC、日志、工单、知识库）
- 不推断或读取认证凭据（Keychain、.netrc、环境变量等）
- 不向 ITR 发出写操作（POST/PUT/PATCH/DELETE 一律拒绝）
- 不将原始数据写入 Git 或 process 目录（`data/snapshots/` 已 git-ignored）
- 不处理 HTTPS（首版只支持 HTTP，由 allowlist 限定内网地址）
- 不处理 HTTP 重定向（3xx 视为错误）
- 不自动生成 URL（URL 必须由用户显式提供并通过 allowlist 校验）
- 不执行变更检测和冲突处理（由 ST-RA-06.1-DETECT 负责）
- 不把 `ptm-team/data/`、全局用户目录或调用时 CWD 当作数据根
- 不对已有运行文件自动 `chmod`、删除、迁移、导出或执行保留清理；仅在已授权摄取中创建本次新文件和清理未提交临时文件

---

## 配置引用

- Allowlist 配置：`skills/itr-ticket-ingestion/templates/allowlist-config.yaml`
- 字段映射配置：`skills/itr-ticket-ingestion/templates/field-mapping.yaml`
- 质量报告模板：`skills/itr-ticket-ingestion/templates/quality-report.yaml`
- Batch Manifest 模板：`skills/itr-ticket-ingestion/templates/batch-manifest.yaml`
- 冲突队列模板：`skills/itr-ticket-ingestion/templates/conflict-queue.yaml`
- 数据库 DAO：`data/dao.py`
- 数据库 Schema：`data/schema.sql`
- 受限存储排除：`data/.gitignore`

---

## §10 Gotchas

> 本节记录 itr-ticket-ingestion Skill 的常见误用、陷阱和必须注意的边界行为。每一条均来自设计契约中的显式约束或已知踩坑记录。

### G-ING-01: Allowlist 遗漏导致拒绝所有请求

**现象**：所有 URL 请求被 `AllowlistDeniedError` 拒绝，即使 URL 指向合法的 ITR 服务。

**原因**：`skills/itr-ticket-ingestion/templates/allowlist-config.yaml` 中未注册目标 ITR endpoint 的 pattern。allowlist 是 deny-by-default——未注册即拒绝。

**规避**：
1. 部署前确认 `allowlist-config.yaml` 包含所有目标 ITR 的 `pattern`、`allowed_params` 和 `max_page_size`
2. 新增 ITR 数据源时必须先更新 allowlist 配置，再发起摄取
3. URL 必须**精确匹配** pattern——不允许子路径通配、IP 范围或正则

**检测信号**：错误输出中出现 `"URL 不在白名单中"` 且 `allowlist_entries` 列表不包含目标 URL。

---

### G-ING-02: 快照临时文件残留（权限断言失败后未清理）

**现象**：`data/snapshots/` 目录下出现 `batch-*-raw.json.tmp` 残留文件。

**原因**：快照保存流程（§3.3）在权限断言失败时会调用 `tmp_path.unlink()` 清理临时文件，但以下场景可能导致残留：
- 进程在 `os.chmod()` 与 `unlink()` 之间被 SIGKILL 终止
- 磁盘写满导致 `chmod` 成功但后续 `unlink` 失败
- 异步文件系统延迟刷盘

**规避**：
1. 摄取前检查 `data/snapshots/` 中是否有 `.tmp` 残留文件，手动清理后重试
2. 在 cron/定时摄取脚本中加入 `.tmp` 文件存活时间检查（超过 1 小时的 `.tmp` 视为残留）
3. 权限断言失败后的清理逻辑（§3.4）已覆盖正常路径，但进程异常终止无法覆盖

**影响**：残留 `.tmp` 不会影响后续批次（文件名不含冲突），但可能占用磁盘空间。

---

### G-ING-03: WAL 模式 -shm/-wal 文件被 Git 跟踪

**现象**：`git status` 显示 `data/ptm-tse.db-shm` 和 `data/ptm-tse.db-wal` 为未跟踪文件。

**原因**：SQLite 在 WAL 模式下会在数据库文件同目录创建 `-shm`（共享内存）和 `-wal`（预写日志）文件。这些文件是 SQLite 运行时自动管理的，不应纳入版本控制。如果 `data/.gitignore` 只忽略了 `*.db`，这些文件会被 Git 发现。

**规避**：
1. 确保 `data/.gitignore` 包含以下规则：
   ```
   *.db
   *.db-shm
   *.db-wal
   *.db-journal
   ```
2. 不要手动删除 WAL 文件——可能导致未提交事务丢失
3. 关闭所有数据库连接后，WAL 文件会被自动合并和清理

**影响**：误提交 WAL 文件不会破坏数据库，但会污染 Git 历史并可能在不同机器间产生不必要的冲突。

---

### G-ING-04: 事务未提交导致数据丢失

**现象**：`ingestion_batch` 和 `ticket` 表中没有本批次的任何记录，但快照文件存在。

**原因**：数据库写入使用显式事务（`begin_transaction` / `commit`）。以下场景会导致事务未提交：
- 写入循环中异常被捕获，但 `rollback` 后没有重新抛出，调用方以为成功
- `commit(conn)` 后连接被意外关闭（WAL 模式下 checkpoint 未完成）
- 使用 `get_connection()` 创建的连接在 `commit` 前被垃圾回收

**规避**：
1. 始终在 `try/finally` 中关闭连接：`conn.close()` 应在 finally 块中执行
2. 事务写入完成后立即 `commit`，然后才更新 manifest
3. 验证方法：写入后立即用 `get_ticket_by_source_id()` 查询确认数据已落盘
4. 不要依赖"连接关闭时自动回滚"作为预期行为

**检测信号**：快照和 manifest 文件存在，但 `ingestion_batch` 表中无对应记录。

---

### G-ING-05: batch_id 重用导致幂等跳过

**现象**：重试失败批次时，数据库写入被静默跳过，`total_inserted = 0`。

**原因**：`insert_ingestion_batch()` 依赖 `ingestion_batch.batch_id` 的 UNIQUE 约束实现幂等保护（§8.4.1）。如果使用相同的 `batch_id` 重试，DAO 层会触发 `sqlite3.IntegrityError`，事务回滚，不会覆盖已有数据。这**是设计行为而非 bug**，但调用方可能误以为第二次执行成功。

**规避**：
1. 重试失败批次前，先生成**新的** `batch_id`（如 `batch-20260716-002` 替代 `batch-20260716-001`）
2. 待重试的原始快照文件可以通过旧 batch_id 定位，新 batch 使用新 batch_id 重新写入
3. 不要试图删除旧 `ingestion_batch` 记录以"重用" batch_id——这会破坏审计追溯
4. 文档中明确：`batch_id` 是**一次性**标识符，不支持重用

**检测信号**：返回错误 `"batch_id 重复: {batch_id}"`，或事务回滚后 `total_inserted = 0`。

---

### G-ING-06: 字段映射缺失导致 unclassified_fields

**现象**：`quality_report` 的 `unclassified_fields` 计数持续增长，但清洗后的 ticket 表缺少这些字段的值。

**原因**：ITR 响应中的字段如果不在 `field-mapping.yaml` 的映射表中，按 §6.3.5 规则会保留在 `raw_json` 中并记录为 `type='unclassified'`，但**不会**出现在 `cleaned` 字典中。这意味着下游分析无法使用这些字段，即使它们可能包含有价值的信息（如 `assignee`、`component` 等 ITR 扩展字段）。

**规避**：
1. 每次 ITR 响应 schema 变更后，对比实际返回字段与 `field-mapping.yaml`，补全新字段映射
2. 定期检查 `quality_report.issues` 中 `type='unclassified'` 的条目，评估是否需要新增映射
3. 对于明确不需要的 ITR 字段，在 `field-mapping.yaml` 中显式标记 `ignored: true` 以消除告警
4. 不要假设"未知字段不重要"——它们可能在下游分析中被需要

**检测信号**：`quality_report.issues[]` 中出现 `type='unclassified'` 条目，或 `stats.unclassified_fields > 0`。

---

### G-ING-07: QCOMB-02 致命级阻断范围过大（一个致命记录阻断整批）

**现象**：整批 150 条 ticket 中只有 1 条 `severity=致命` 且 `quality_flag='blocked'`，导致整批 `overall_status='blocked'`，所有 150 条都无法进入下游分析。

**原因**：QCOMB-02 规则（§7.4）规定：`severity=致命` 的记录中存在任何 `quality_flag='blocked'` 即阻断整批。这来自设计决策"致命级问题单必须全部可分析"，但在实际运行中可能过度阻断。

**规避**：
1. 在清洗管线中优先检查致命级记录的 source_ticket_id 和 product 是否完整，提前修复后再执行 QCOMB 判定
2. 如果需要，可在 `quality-report.yaml` 中将 QCOMB-02 的阻断条件改为 `fatal_blocked_count / fatal_count > 0.5`（致命记录半数以上 blocked 才阻断）
3. 当前行为是**设计契约**而非 bug，修改 QCOMB-02 阈值需通过 CR 变更设计基线
4. 运维建议：在触发 QCOMB-02 阻断时，单独定位那条 blocked 致命记录，修复后重跑清洗

**检测信号**：`combined_rules.QCOMB-02.triggered = true`，且 `fatal_blocked_count = 1`，`fatal_count` 远大于 1。

---

### G-ING-08: severity/pri 不在枚举值时设为 anomaly 但不清洗数据

**现象**：ticket 的 `priority` 值不是 P1/P2/P3/P4（如 "紧急"、"Critical"），清洗管线将其 `quality_flag` 设为 `anomaly`，但**保留原值**写入 ticket 表。

**原因**：按 §6.3.2 枚举校验规则，`priority` 和 `severity` 的枚举异常处理策略是"保留原值，quality_flag='anomaly'"——不清空、不转换、不阻断。下游分析模块（reverse-analysis Skill）的资格检查（§1.2 Step 4）会将非 P1/P2/P3/P4 的 severity 视为空处理（默认拒绝分析），导致该 ticket 被静默排除。

**规避**：
1. 在上游 ITR 数据录入环节强制枚举约束，确保 `pri` 只取 P1-P4，`severity` 只取致命/严重/一般/提示
2. 如有跨系统映射需求（如 Jira "Blocker" → P1），应在 ST-RA-05.2-CLEAN 的映射配置中增加标准化规则
3. 不要在清洗管线中做隐式转换——当前设计选择"保留原值"而非"猜测映射"
4. 下游分析前，检查 ticket 表中 `quality_flag='anomaly'` 且 `severity` 非标准的记录，人工确认后决定是否纳入分析

**检测信号**：`quality_report.issues[]` 中出现 `type='anomaly'` 且 `field='severity'` 或 `field='priority'`，`value` 不在有效枚举值列表中。

---

### G-ING-09: 分页中断时 partial batch 的 errors 记录不完整

**现象**：分页摄取过程中第 3 页失败，batch manifest 的 `errors` 字段记录了失败页码，但没有记录已成功拉取的 ticket 清单。

**原因**：§2.4 分页中断处理规定"已成功拉取的前几页保留"，但 `errors` 字段只记录失败页码和原因，不输出成功部分的 ticket ID 清单。如果调用方需要精确知道"哪些 ticket 已在快照中，哪些缺失"，必须解析原始快照文件。

**规避**：
1. 分页成功部分的 ticket 在快照文件中完整保留，解析 `raw_response` 即可获取
2. 如需精确的"成功/失败 ticket 对照"，在调用方消费 manifest 后解析快照并比对 expected page
3. 后续版本可在 manifest 中增加 `partial_success_ticket_ids[]` 字段（OPEN）

**检测信号**：`batch-manifest.yaml` 的 `errors` 非空但 `total_fetched > 0`，说明是 partial batch。

---

### G-ING-10: conflict-queue.yaml 写入失败导致 change_history 缺失

**现象**：S2 变更检测中产生了冲突记录，但 `change_history` 表和 `conflict-queue.yaml` 中都没有对应条目。

**原因**：§9.5.1 步骤 4 要求"先写队列文件获取 ref，再写 change_history"。如果冲突队列 YAML 写入失败（磁盘满、权限错误），按 §9.7 规则"不得在无 conflict_ref 的情况下提交 change_history"，整批事务回滚。但如果开发实现时未正确包裹事务，可能出现部分 change_history 已提交但 conflict-queue 写入失败的不一致状态。

**规避**：
1. 确保冲突队列写入和 change_history 在同一事务边界内保持一致性
2. 推荐实现顺序：先写 conflict-queue.yaml（文件系统），成功后再在事务中写入 change_history（带 conflict_ref）；conflict-queue 写入失败则不开启事务
3. 监控 `data/snapshots/` 目录的磁盘空间，避免写入中途空间耗尽

**检测信号**：`change_history` 中有 `change_type='conflict'` 但 `conflict_ref` 指向的文件不存在；或反过来，`conflict-queue.yaml` 存在但 change_history 中无对应记录。

---

## 修订记录

| 版本 | 日期 | 修订人 | 变更要点 |
|---|---|---|---|
| 1.1 | 2026-07-16 | meta-dev | CR-030：受控 ITR GET、快照/清洗/质量、失败保护与 S2 变更检测。 |
| 1.2 | 2026-07-17 | host-orchestrator | CR-031：增加安装项目 `runtime_root`/`data_root` 解析、敏感运行数据分类和预检门控；禁止本 Skill 未授权修复既有运行数据。 |
