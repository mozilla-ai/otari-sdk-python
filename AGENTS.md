# AGENTS.md

Guidance for agentic coding tools working in this repository.
Scope: entire repo.

`CLAUDE.md` is a symlink to this file. Always edit `AGENTS.md` directly; never modify `CLAUDE.md`.

## Project Snapshot
- Project: `otari` (PyPI package name `otari`), the **Python client SDK** for the otari
  gateway / platform. `OtariClient` (sync) and `AsyncOtariClient` (async) talk to a running
  gateway over HTTP.
- Language/runtime: Python 3.11+ (CI matrix: 3.11, 3.12, 3.13).
- Package manager + task runner: `uv`.
- Source root: `src/otari` (imported as `otari`).
- Tests: `tests/unit` (mocked, offline) and `tests/integration` (real gateway).

## Architecture (Big Picture)
This SDK is a **thin, hand-written shell over an OpenAPI-generated typed core**. Read these
together before changing request behavior.

- **Generated core** (`src/otari/_client/`): produced by OpenAPI Generator from the gateway's
  OpenAPI spec. It is **generated, not hand-edited.** Regeneration happens upstream in the
  gateway repo (`.github/workflows/gateway-sdk-codegen.yml`), which opens a
  `sdk-codegen/client-core` PR here. The core is **excluded from ruff and mypy**
  (`pyproject.toml`: `extend-exclude` / mypy `exclude`). Do not edit it to fix a lint error;
  fix the shell or the upstream spec/generator instead.
- **Hand-written shell** (everything else under `src/otari/`):
  - `client.py` / `async_client.py`: ergonomic `OtariClient` / `AsyncOtariClient` with
    `completion`, `response`, `message`, `embedding`, `moderation`, `rerank`, `list_models`,
    batch operations, and a `control_plane` accessor.
  - `_base.py`: shared logic: auth-mode resolution, default headers, URL normalization, and
    the single seam where generated `ApiException` is caught and mapped to typed errors.
  - `_streaming.py`: hand-written SSE shim. The generated core buffers and **cannot stream**,
    so streaming endpoints use raw `httpx` + a line/event parser. Chat streaming yields typed
    `ChatCompletionChunk`; responses/messages streaming yields raw event `dict`s (no chunk
    model exists for those).
  - `errors.py`: typed error hierarchy (`OtariError` base + subclasses).
  - `types.py`: re-exports of generated models plus hand-written TypedDicts (batch/options).
  - `control_plane.py`: wrapper over the management endpoints (keys/users/budgets/pricing/usage).

### Two auth modes (must both keep working)
Resolved in `_base.py` from constructor args, then environment:
- **Platform** (`OTARI_AI_TOKEN` / `platform_token`): `Authorization: Bearer <token>`, base URL
  defaults to `https://api.otari.ai`.
- **Self-hosted** (`api_key` + `api_base`, env `GATEWAY_API_KEY` / `GATEWAY_API_BASE`):
  `Otari-Key` header; `api_base` is **required** in this mode.
Error mapping applies in both modes; do not regress one when changing the other.

### Endpoint-coverage drift gate
`tests/unit/test_endpoint_coverage.py` fetches the canonical gateway spec
(`https://raw.githubusercontent.com/mozilla-ai/otari/main/docs/public/openapi.json`) and
asserts every gateway endpoint is accounted for in `sdk-endpoints.txt` (`[covered]` or
`[excluded]` with a reason). A new gateway endpoint with no wrapper and no explicit exclusion
fails CI. When you add or intentionally skip an endpoint, update `sdk-endpoints.txt`.

## Setup Commands
- Install (dev): `uv sync --extra dev`

## Test Commands
- Full suite: `uv run pytest`
- Unit only: `uv run pytest tests/unit`
- Single test: `uv run pytest tests/unit/test_client.py::TestOtariClient::test_completion -v`
- Drift gate (needs network): `uv run pytest tests/unit/test_endpoint_coverage.py -v`
- Integration tests under `tests/integration/` spawn / require a real gateway and are skipped
  when one is not available.

## Lint / Typecheck / Build Commands
- Lint: `uv run ruff check .`
- Typecheck (mypy strict): `uv run mypy src/`
- Build: `uv build`

## Repository Conventions
- `from __future__ import annotations` at the top of modules; `TYPE_CHECKING` for type-only
  imports; import `Callable`/`Iterator` from `collections.abc`.
- mypy is `strict`; the generated `otari._client` is excluded. New/changed shell code must be
  fully typed. Use `@overload` for streaming polymorphism (`stream=True` vs not), as `client.py`
  already does.
- Public API is exported from `src/otari/__init__.py` (clients, errors, types); don't remove or
  rename exports without auditing callers.
- Unit tests mock at the transport seam (the generated core's REST client) and use `respx` for
  the raw-`httpx` streaming path. Test classes are `Test<Feature>`.

## Change Validation Checklist
- Touched request handling, auth, or errors → run `tests/unit` and confirm both auth modes still
  map errors correctly.
- Touched streaming → run the streaming tests; verify chat yields `ChatCompletionChunk` and
  responses/messages yield raw dicts.
- Added/removed an endpoint wrapper → update `sdk-endpoints.txt` and run the drift gate.
- Always run `uv run ruff check .` and `uv run mypy src/` before opening a PR.

## Writing style

- Avoid em dashes and double hyphens (`--`) used as separators in prose
  (README, docs, doc comments, commit messages, PR descriptions). Use commas,
  semicolons, colons, parentheses, or periods, or rephrase. This does not apply
  to code (for example CLI flags like `--all`) or en-dash numeric ranges like `3–4`.

## Notes for Agents
- Never hand-edit `src/otari/_client/`; it is regenerated from the gateway spec.
- Prefer minimal, targeted edits; match existing typing and import style in touched files.
- Preserve security-relevant behavior (header/auth handling, error-detail boundaries).
