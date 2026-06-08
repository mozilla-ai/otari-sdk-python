# Control-plane integration tests

Strategy for verifying each control-plane endpoint (keys, users, budgets,
pricing, usage) end to end against a real gateway. `test_control_plane_generated.py`
is the Python reference; the same shape applies to the TS / Go / Rust SDKs.

## Why this works without Docker or provider keys

Control-plane endpoints are pure gateway + DB operations; they never call an LLM
provider. So a test can run the gateway on **SQLite** with just a **master key**:
no Postgres, no provider credentials. The fixture starts `gateway serve
--database-url sqlite:///... --master-key ... --auto-migrate`, waits for
`/health`, and tears it down.

## Auth (verified)

Management endpoints authenticate with `Authorization: Bearer <master_key>`.
The `Otari-Key` header is for the virtual API keys used on inference endpoints
and returns 401 here. The integrated client must send Bearer for control-plane
calls.

## Per-endpoint coverage

Each resource is exercised through its full lifecycle, with extra attention on
the create/POST operations (the manually-integrated surface):

| Resource | create | get | list | update | delete | extra |
|----------|--------|-----|------|--------|--------|-------|
| budgets  | ✓ (asserts `budget_id`, `max_budget`) | ✓ | ✓ | ✓ | ✓ → 404 | |
| users    | ✓ | ✓ | ✓ | ✓ | ✓ → 404 | `GET .../usage` |
| keys     | ✓ (asserts the one-time `key` secret is returned) | ✓ | ✓ | ✓ | ✓ → 404 | |
| pricing  | ✓ | ✓ | ✓ | — | ✓ → 404 | `GET .../history` |
| usage    | — | — | ✓ | — | — | |

Identifier fields differ per resource (gateway convention): `id` (keys),
`user_id` (users), `budget_id` (budgets), `model_key` (pricing).

## Other languages (same pattern)

- **TypeScript** (vitest): a `beforeAll` spawns the gateway via `child_process`,
  polls `/health`; tests use the generated fetch client with an `Authorization`
  header; `afterAll` kills it.
- **Go** (`testing`): `TestMain` starts the gateway with `os/exec`, waits on
  `/health`; table-driven lifecycle tests per resource; defer cleanup.
- **Rust** (`tokio::test` + a shared harness): spawn the gateway with
  `std::process::Command`, await `/health`; reqwest-based generated client.

## Running

```bash
# gateway must be importable as a console script (or set OTARI_GATEWAY_CMD)
OTARI_GATEWAY_CMD="gateway" pytest tests/integration/test_control_plane_generated.py -v
```

These tests target the generated client at `src/otari/_generated` for now. Once
it is wired into the public client, point the imports at the public surface so
the tests also cover the manual integration layer.
