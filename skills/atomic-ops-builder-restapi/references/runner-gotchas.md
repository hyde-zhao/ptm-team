# Runner Gotchas

Use this reference before implementing execution, auth/session behavior, error handling, publication, or live smoke tests.

## Auth And Secrets

Keep secrets out of versioned artifacts:

- No password, token, cookie, authorization value, CSRF secret, or real session content in YAML.
- No real session material in docs or tests.
- Use environment variables, runtime prompts, or session files according to repository patterns.
- Redact auth and cookie headers from dry-run and error output.

Handle login/session failures explicitly. Useful `error_type` examples:

- `auth_session_missing`
- `auth_session_expired`
- `auth_token_parse_failed`
- `http_error`
- `tls_warning`
- `json_parse_error`
- `device_nonstandard_success`
- `device_state_mismatch`
- `validation_error`

Use existing repository names if they already define an error taxonomy.

## Request Semantics

GET:

- Do not send JSON body.
- Allow empty payload templates in YAML only if schema requires them.
- Tests should assert that the HTTP client receives no body.

DELETE:

- Implement query, body, or path identity exactly as captured.
- Do not use another endpoint as analogy.
- Tests should cover the captured deletion transport.

PUT:

- Treat as desired-state config when the same payload reliably converges to the same state.
- Include pre-check or post-check when the device returns weak success markers.

POST:

- Require unique key, returned id, or explicit user-provided test object.
- Avoid making POST smoke tests part of default validation.

## Output Envelope

Keep top-level output stable:

```json
{
  "op_id": "fw_update_ospfv2_interface",
  "status": "dry_run",
  "data": {},
  "error_type": null,
  "diag_snapshot_ref": null
}
```

Common statuses are repository-specific, but dry-run, success, and failed states should not change the envelope shape.

## Cache And Global Command

`atomic-ops list` may read a synced/global cache instead of the current working tree. When new operations do not appear:

1. Confirm the atom was added to the correct package or registry.
2. Confirm schema and adapter validation pass.
3. Refresh the sync cache using repository tooling.
4. Reinstall the global command and clear stale build artifacts if needed.
5. Re-run `atomic-ops list` and an operation dry-run through the same command the user will run.

Do not assume `uv tool install . --force` always uses the newest package contents.

## Live Smoke Test Order

Use this order for real devices:

1. GET query to verify session and API reachability.
2. Idempotent PUT against a safe target.
3. POST only with a known disposable object and clear cleanup plan.
4. DELETE only with a known disposable object or explicit user approval.
5. GET after each change to prove actual device state.

If the device returns `{"msg":"success"}` but GET shows no state change, treat the operation as failed or unverified and re-check F12 evidence.
