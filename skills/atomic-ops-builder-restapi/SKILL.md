---
name: atomic-ops-builder-restapi
description: 将浏览器 F12 或 DevTools 抓到的防火墙 REST API 请求转换为 atomic-ops 仓库中的 atomic operation specs、adapter profile mappings、atomic-ops run runner、CLI 参数、测试和发布缓存刷新步骤。Use when the user provides endpoint/method/payload/query/response/auth details from firewall APIs, asks to implement OSPFv2, OSPFv3, BFD or similar firewall operations, or needs method-level atomic ops generated from F12 captures.
---

# Atomic Ops Builder REST API

## Overview

Use this skill to turn F12 / DevTools REST API evidence into runnable atomic-ops operations. The default output is a method-level atomic operation set, an adapter profile mapping, runner/CLI support, tests, validation commands, and a clear note about global command cache refresh.

## First Steps

1. Read current repository facts before designing or editing. Check `atoms/`, `adapters/`, `schemas/`, `src/atomic_ops/commands/run.py`, `src/atomic_ops/runner/`, `packages/`, and `tests/` if they exist.
2. Read [references/f12-api-extraction.md](references/f12-api-extraction.md) when parsing raw browser capture data.
3. Read [references/atomic-ops-workflow.md](references/atomic-ops-workflow.md) before creating specs, adapter mappings, packages, runner dispatch, or validation steps.
4. Read [references/runner-gotchas.md](references/runner-gotchas.md) before implementing live execution, auth/session handling, DELETE behavior, error classification, cache refresh, or smoke tests.
5. If the repository structure differs from this skill, follow the repository. Do not invent missing paths without first explaining the mismatch and choosing the smallest compatible implementation.

## Hard Rules

- Split each HTTP method into a separate atomic operation. Do not combine `GET`, `POST`, `PUT`, and `DELETE` for the same endpoint into one multi-action atom unless the user explicitly asks to change the atomic schema.
- Use stable `op_id` forms such as `fw_get_<domain>_<object>`, `fw_create_<domain>_<object>`, `fw_update_<domain>_<object>`, `fw_delete_<domain>_<object>`, `fw_config_<domain>`, and `fw_verify_<domain>_<object>`.
- Allow protocol names containing digits, such as `ospfv2` and `ospfv3`. If the repository schema rejects digits, update the schema and tests together.
- Make adapter mappings one actual API call per operation, including method, path, query template, payload template, response handling, timeout, TLS policy, and auth header strategy as supported by the repo.
- Never send a JSON body for `GET`. If schema requires a payload field, keep an empty template in YAML only; ensure the runner does not send a body.
- Implement `DELETE` exactly from F12 evidence. Query deletion uses query parameters and no body; body deletion sends JSON only when the capture proves it; path deletion uses the captured path parameter.
- Keep runner default behavior as dry-run. Only `--execute` may call the device.
- Return the fixed runner envelope: `op_id`, `status`, `data`, `error_type`, `diag_snapshot_ref`. Put success details under `data`.
- Keep credentials out of atoms, adapter YAML, docs, tests, and fixtures. Use environment variables, runtime input, or session files.
- Classify login expiry, TLS warning, non-standard success, HTTP errors, and JSON parse failures into explicit `error_type` values.
- Verify every live change with a follow-up `GET`. Treat device `{"msg":"success"}` as insufficient proof when the target state does not change.

## Workflow

1. Parse F12 input into endpoint, method, payload, query, response, primary key, pagination, auth/session, and observed device behavior.
2. Classify each interface as query, verify, config, create, update, or delete. Assign risk: `GET` is low, `PUT` and `POST` are medium, `DELETE` is high.
3. Generate an atomic operation list. Define one `op_id` per method with inputs, required fields, defaults, idempotency, preconditions, risk, and verification.
4. Write atomic specs using existing YAML style and schema. Include `device_type`, `idempotent`, `description`, `inputs`, `outputs`, `risk`, and `adapter_contract_ref` if those fields exist in the repo.
5. Write adapter profile operation mappings from F12 facts only. Do not infer path, query/body deletion style, or payload field types from similar endpoints.
6. Implement runner and CLI dispatch in the repository's existing style. Support dry-run previews and execute mode without leaking auth/session material.
7. Add tests for dry-run rendering, method/path/query/payload, GET-without-body, DELETE query/body/path differences, CLI args, output envelope, error classification, schema validation, and adapter validation.
8. Run repository validation commands. Prefer existing test and guardrail entry points over new scripts.
9. For live smoke tests, start with GET, then idempotent PUT, then POST/DELETE only on explicit test objects. Verify each change with GET.
10. If `atomic-ops list` cannot see new operations after code changes, check package membership, global sync cache, and command reinstall/cache refresh.

## Implementation Notes

- Preserve captured field types unless the device contract proves normalization is required. F12 may show string numbers, integers, and booleans that the device accepts differently.
- For `PUT`, prefer idempotent config semantics. For `POST`, require a unique key or returned identifier. For `DELETE`, document whether repeat deletion is genuinely idempotent or only returns a misleading success.
- Add CLI parameters from captured fields, such as `--id`, `--interface`, `--network`, `--area`, `--metric`, `--page`, `--size`, and `--json-payload`, only when the operation needs them.
- Keep adapter payload templates to business fields. Authentication belongs in runtime session/auth handling.
- Update the package or registry surface that feeds `atomic-ops list`; repository files alone may not update the global synced cache.
- When publishing the global command, force reinstall and refresh caches according to the repo's packaging flow. Do not assume `uv tool install . --force` always uses the newest build.

## Required Final Report

End with:

- New or modified atomic ops
- Adapter operations
- Runner and CLI changes
- Tests and validation results
- Live smoke test results, or why not run
- Problems found and how they were handled
- Whether global command reinstall and sync cache refresh are needed
