"""Endpoint-coverage manifest checks.

``sdk-endpoints.txt`` records which gateway endpoints this SDK surfaces
(``[covered]``) and which it deliberately does not (``[excluded]``). The file is
a generated artifact: the gateway's codegen workflow pushes it here alongside
the generated core, from the canonical copy at
``scripts/sdk_codegen/sdk-endpoints.txt`` in ``mozilla-ai/otari``.

The drift gate itself lives in the gateway, where the manifest is validated
against ``docs/public/openapi.json`` from the same commit. It used to live here
and fetch the spec from ``main`` over the network at test time, which made the
result depend on when the test ran rather than on what the commit contained: an
unchanged commit passed one day and failed the next, and because CI only runs on
push and pull_request, ``main`` sat red unnoticed for over two weeks
(mozilla-ai/otari#438). What remains here is offline and deterministic.
"""

from __future__ import annotations

from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[2] / "sdk-endpoints.txt"
HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


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


def test_manifest_sections_are_non_empty() -> None:
    covered, excluded = parse_manifest(MANIFEST.read_text())
    assert covered, "manifest [covered] section is empty"
    assert excluded, "manifest [excluded] section is empty"


def test_manifest_sections_are_disjoint() -> None:
    covered, excluded = parse_manifest(MANIFEST.read_text())
    both = sorted(covered & excluded)
    assert not both, f"endpoints in both [covered] and [excluded]: {both}"


def test_manifest_entries_are_well_formed() -> None:
    covered, excluded = parse_manifest(MANIFEST.read_text())
    malformed = sorted(
        entry
        for entry in covered | excluded
        if entry.split(" ", 1)[0] not in HTTP_METHODS or not entry.split(" ", 1)[1].startswith("/")
    )
    assert not malformed, f'manifest entries are not "METHOD /path": {malformed}'
