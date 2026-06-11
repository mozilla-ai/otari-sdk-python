"""The gateway/spec version is surfaced on the public package.

The gateway codegen stamps the spec version into the generated core
(``otari._client._spec_version``); the package re-exports it as
``otari.__spec_version__`` so callers can tell which gateway spec this SDK
targets. This guards the wiring (a stale literal in ``__init__`` would diverge
from the generated marker).
"""

from __future__ import annotations

import otari
from otari._client._spec_version import __spec_version__ as marker


def test_spec_version_is_surfaced() -> None:
    assert otari.__spec_version__ == marker
    assert isinstance(otari.__spec_version__, str)
    assert otari.__spec_version__
