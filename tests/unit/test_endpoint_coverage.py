"""Endpoint-coverage drift gate.

Fetches the canonical otari gateway OpenAPI spec and asserts that every API
endpoint it exposes is accounted for in ``sdk-endpoints.txt`` -- either wrapped
by this SDK's public surface (``[covered]``) or deliberately deferred
(``[excluded]``). A new gateway endpoint in neither section fails this test,
so a future endpoint (as ``/messages`` once was) cannot silently go unsurfaced.

The fetch uses :mod:`urllib.request` (stdlib) so the test runs in the normal
suite. It is skipped offline (network error / ``OTARI_SKIP_NETWORK_TESTS=1``)
but runs in CI, where the network is available.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

SPEC_URL = "https://raw.githubusercontent.com/mozilla-ai/otari/main/docs/public/openapi.json"
MANIFEST = Path(__file__).resolve().parents[2] / "sdk-endpoints.txt"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def parse_manifest(text: str) -> tuple[set[str], set[str]]:
    """Return (covered, excluded) endpoint sets from manifest text.

    Format: ``[covered]`` / ``[excluded]`` sections; each entry is
    ``METHOD /path`` with an optional ``# reason`` trailer; ``#`` lines and
    blank lines are ignored.
    """
    covered: set[str] = set()
    excluded: set[str] = set()
    section: set[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[covered]":
            section = covered
            continue
        if line == "[excluded]":
            section = excluded
            continue
        entry = line.split("#", 1)[0].strip()
        if not entry or section is None:
            continue
        method, path = entry.split(None, 1)
        section.add(f"{method.upper()} {path.strip()}")
    return covered, excluded


def spec_endpoints(spec: dict) -> set[str]:
    """Extract ``METHOD /path`` pairs from an OpenAPI doc, dropping meta routes."""
    eps: set[str] = set()
    for path, methods in spec.get("paths", {}).items():
        if path == "/health" or path.startswith("/health/"):
            continue
        for method in methods:
            if method.lower() in HTTP_METHODS:
                eps.add(f"{method.upper()} {path}")
    return eps


def fetch_spec() -> dict:
    if os.environ.get("OTARI_SKIP_NETWORK_TESTS") == "1":
        pytest.skip("OTARI_SKIP_NETWORK_TESTS=1")
    try:
        with urllib.request.urlopen(SPEC_URL, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"could not fetch otari OpenAPI spec from {SPEC_URL}: {exc}")


def test_manifest_parses() -> None:
    covered, excluded = parse_manifest(MANIFEST.read_text())
    assert covered, "manifest [covered] section is empty"
    assert not (covered & excluded), f"endpoints in both sections: {sorted(covered & excluded)}"


def test_spec_endpoints_are_accounted_for() -> None:
    covered, excluded = parse_manifest(MANIFEST.read_text())
    spec = spec_endpoints(fetch_spec())
    accounted = covered | excluded
    unaccounted = sorted(spec - accounted)
    assert not unaccounted, (
        "Gateway OpenAPI exposes endpoint(s) the SDK does not account for: "
        f"{unaccounted}. Add a public wrapper and list under [covered], or "
        "defer it under [excluded] with a reason, in sdk-endpoints.txt."
    )


def test_manifest_has_no_stale_entries() -> None:
    """Warn (not fail) if a manifest entry no longer exists in the spec."""
    covered, excluded = parse_manifest(MANIFEST.read_text())
    spec = spec_endpoints(fetch_spec())
    stale = sorted((covered | excluded) - spec)
    if stale:
        pytest.skip(f"manifest entries not present in current spec (review): {stale}")
