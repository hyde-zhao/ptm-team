# F12 API Extraction

Use this reference when the user provides DevTools, HAR, curl, screenshots, copied request headers, request payloads, or response bodies.

## Capture Checklist

Extract these facts before designing operations:

- Endpoint path, including API prefix and path parameters
- HTTP method
- Query parameters and pagination parameters
- Request body payload, content type, and whether body is absent
- Response body shape, success marker, error marker, and pagination envelope
- Primary key field and uniqueness constraints
- Create/update/delete identity source: query, body, path, or response id
- Authentication mechanism: session file, cookie, bearer token, CSRF token, login endpoint, or device-specific session header
- TLS behavior and whether the device uses self-signed certificates
- Observed status code and any non-standard success response

Do not keep raw credentials. Replace secrets with placeholders such as `<runtime-session>` or `<env-token>` if an example is necessary.

## Method Classification

Classify each captured request:

- `GET`: query or verify; low risk; must not send a JSON body.
- `PUT`: config or update; medium risk; usually idempotent if the same payload creates the same final state.
- `POST`: create or action; medium risk; require a unique key or returned id before calling it safe to repeat.
- `DELETE`: delete; high risk; require exact identity transport from F12 evidence.

For the same endpoint with multiple methods, create separate operations. Example:

- `GET /api/v1/ospfinterface` -> `fw_get_ospfv2_interface`
- `POST /api/v1/ospfinterface` -> `fw_create_ospfv2_interface`
- `PUT /api/v1/ospfinterface` -> `fw_update_ospfv2_interface`
- `DELETE /api/v1/ospfinterface?id=<interface>` -> `fw_delete_ospfv2_interface`

## Field Handling

Preserve device-accepted types unless repository schemas or live evidence require normalization. F12 captures often mix string numbers, integers, and booleans.

Record for every field:

- Source: query, body, path, derived CLI arg, environment, or session
- Required or optional
- Default value, if device or existing CLI provides one
- Allowed values, if visible from UI or API response
- Whether it is safe to echo in dry-run output

## DELETE Identity Rules

Never infer deletion style from a similar endpoint.

- Captured `DELETE /path?id=xxx`: send query `id=xxx`, no JSON body.
- Captured `DELETE /path` plus JSON `{"id":"xxx"}`: send JSON body.
- Captured `DELETE /path/<id>`: render the path parameter, no separate id unless the capture includes one.

If the device returns success but GET shows no state change, treat the F12 extraction as suspect and re-check query/body/path details.

## Extraction Output

Before editing code, summarize:

- Interface table: endpoint, method, role, identity, risk
- Payload/query field table
- Response envelope and success criteria
- Auth/session preconditions
- Operation split and proposed `op_id` names
- Open questions that block safe execution
