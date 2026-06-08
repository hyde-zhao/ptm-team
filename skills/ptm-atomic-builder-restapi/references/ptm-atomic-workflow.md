# Atomic Ops Workflow

Use this reference when creating or updating atomic specs, adapter profiles, packages, runner dispatch, tests, and validation.

## Repository Discovery

Start by reading the actual repository layout. Prefer existing patterns over this reference if they differ.

Check:

- `atoms/`
- `adapters/`
- `schemas/`
- `src/ptm_atomic/commands/run.py`
- `src/ptm_atomic/runner/`
- `packages/`
- `tests/`

Find nearby operations in the same domain and copy their style for YAML shape, test naming, runner helpers, CLI parser style, and validation commands.

## Operation Modeling

Create one atomic operation per method-level API call.

Use stable names:

- `fw_get_<domain>_<object>`
- `fw_create_<domain>_<object>`
- `fw_update_<domain>_<object>`
- `fw_delete_<domain>_<object>`
- `fw_config_<domain>`
- `fw_verify_<domain>_<object>`

Allow digits in protocol/domain segments, such as `ospfv2`, `ospfv3`, and `bfd4`, if the device domain naturally contains digits. If schema validation rejects these names, update the schema and add a regression test.

## Atomic Spec Content

Follow existing YAML conventions. When the repository supports these fields, include:

- `device_type`
- `idempotent`
- `description`
- `inputs`
- `outputs`
- `risk`
- `preconditions`
- `execution_semantics`
- `rollback`
- `verification`
- `adapter_contract_ref`

Set idempotency from behavior:

- `GET`: normally `true`
- `PUT`: normally `true` for desired-state config
- `POST`: only `true` when the device de-duplicates by unique key or the runner checks existence first
- `DELETE`: depends on device behavior; if repeat delete returns success while object is absent, document the practical semantics

## Adapter Profile Mapping

Add one operation mapping per `op_id`. Each mapping should describe exactly one HTTP call.

Include what the repository supports:

- `method`
- `path`
- `query_template`
- `payload_template`
- `headers` or auth strategy reference
- `timeout`
- TLS behavior
- response handling

Rules:

- Paths, methods, query templates, and payload templates must come from F12 or existing verified docs.
- `GET` must not send a body from the runner.
- `DELETE` must match query/body/path identity exactly.
- Payload templates contain business fields only.
- Do not store password, token, cookie, authorization header value, CSRF secret, or session content.

## Runner And CLI

Implement in the repository's existing runner structure, usually under `src/ptm_atomic/runner/`, and wire dispatch in `src/ptm_atomic/commands/run.py`.

Runner requirements:

- Default dry-run.
- Require explicit `--execute` for device calls.
- Dry-run output includes method, path, query, and sanitized payload preview.
- Execute mode uses runtime auth/session inputs only.
- Output envelope contains only `op_id`, `status`, `data`, `error_type`, and `diag_snapshot_ref` at top level.
- Success details stay under `data`.

CLI requirements:

- Add only operation-specific arguments required by captured fields.
- Support raw JSON payload input only when existing CLI patterns allow it, such as `--json-payload`.
- Avoid requiring secrets as CLI flags if environment variables or session files are the established pattern.

## Tests

Add focused tests for:

- Dry-run method/path/query/payload rendering for every new op
- GET sends no body
- DELETE query/body/path differences
- CLI argument parsing and dispatch
- Fixed output envelope
- Error classification
- Schema validation
- Adapter profile validation
- Package/list visibility if the repository has package fixtures or registry tests

Keep live device calls out of unit tests unless the repository already has a gated integration-test pattern.

## Validation And Publication

Run repository-native commands. Typical checks include:

- Runner unit tests
- Atomic spec schema validation
- Adapter profile validation
- Layout/security guardrails
- `ptm-atomic list` visibility check
- Dry-run through the installed or global command

If the global command does not show the new operation, inspect package membership and sync cache. Reinstall or refresh global command/cache according to repository instructions instead of assuming current workspace files are enough.
