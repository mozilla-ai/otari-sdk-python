"""Shared test helpers for mocking the generated core's transport.

Option C wires the SDK over the OpenAPI-generated core (:mod:`otari._client`),
whose non-streaming calls go through ``RESTClientObject.request`` (urllib3) and
whose streaming path is a hand-written raw httpx request. These helpers mock both
seams without a live gateway:

- :func:`mock_rest` patches ``RESTClientObject.request`` to return a canned
  response, exercising the full generated deserialization + the shell's error
  mapping. It records the last request (method/url/headers/body) for assertions.
- streaming tests use ``respx`` to mock the httpx transport directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from otari._client.rest import RESTClientObject, RESTResponse


@dataclass
class _Urllib3Like:
    """Minimal stand-in for a urllib3 ``HTTPResponse`` that ``RESTResponse`` wraps."""

    status: int
    data: bytes
    headers: dict[str, str]
    reason: str = "OK"


@dataclass
class RecordedRequest:
    """The last request the generated core issued through the patched transport."""

    method: str = ""
    url: str = ""
    headers: dict[str, Any] = field(default_factory=dict)
    body: Any = None

    @property
    def json_body(self) -> dict[str, Any]:
        if isinstance(self.body, (bytes, bytearray)):
            return json.loads(self.body.decode())
        if isinstance(self.body, str):
            return json.loads(self.body)
        return self.body or {}


class RestMock:
    """Captures the request and serves a canned response for the generated core."""

    def __init__(
        self,
        *,
        status: int,
        body: Any,
        headers: dict[str, str] | None = None,
        reason: str = "OK",
    ) -> None:
        self.status = status
        self.reason = reason
        self.headers = headers or {}
        if isinstance(body, (dict, list)):
            self.payload = json.dumps(body).encode()
        elif isinstance(body, str):
            self.payload = body.encode()
        else:
            self.payload = body
        self.last = RecordedRequest()

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, Any] | None = None,
        body: Any = None,
        post_params: Any = None,  # noqa: ARG002
        _request_timeout: Any = None,
    ) -> RESTResponse:
        self.last = RecordedRequest(
            method=method, url=url, headers=dict(headers or {}), body=body
        )
        resp = _Urllib3Like(
            status=self.status, data=self.payload, headers=self.headers, reason=self.reason
        )
        return RESTResponse(resp)


@pytest.fixture
def mock_rest(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Return a factory that installs a :class:`RestMock` over the generated core."""

    def _install(
        *,
        status: int = 200,
        body: Any = None,
        headers: dict[str, str] | None = None,
        reason: str = "OK",
    ) -> RestMock:
        mock = RestMock(status=status, body=body, headers=headers, reason=reason)
        monkeypatch.setattr(RESTClientObject, "request", mock.request)
        return mock

    return _install
