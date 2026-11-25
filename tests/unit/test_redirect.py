"""The SDK never follows a redirect.

The request carries credentials, and a redirect may name another host. These
tests run the real transports (urllib3 for the generated core, httpx for the raw
paths) against two loopback servers, because a mocked transport cannot show
whether the library under it would have followed the redirect.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any

import pytest

from otari import AsyncOtariClient, OtariClient, RedirectError
from otari.control_plane import ControlPlane

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

MESSAGES = [{"role": "user", "content": "hi"}]


@dataclass
class Gateway:
    """A gateway that redirects every request to ``other``, which counts what reaches it."""

    url: str
    other_url: str
    hits: list[str] = field(default_factory=list)


def _serve(handler: type[BaseHTTPRequestHandler]) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, args=(0.01,), daemon=True).start()
    return server


@pytest.fixture
def gateway() -> Iterator[Gateway]:
    hits: list[str] = []

    class Other(BaseHTTPRequestHandler):
        def _answer(self) -> None:
            hits.append(self.path)
            self.rfile.read(int(self.headers.get("content-length") or 0))
            body = b'{"object": "list", "data": []}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_POST = _answer  # noqa: N815

        def log_message(self, *args: Any) -> None:
            pass

    other = _serve(Other)
    other_url = f"http://127.0.0.1:{other.server_port}"

    class Redirecting(BaseHTTPRequestHandler):
        def _answer(self) -> None:
            self.rfile.read(int(self.headers.get("content-length") or 0))
            self.send_response(307)
            self.send_header("Location", other_url + self.path)
            self.send_header("Content-Length", "0")
            self.end_headers()

        do_GET = do_POST = _answer  # noqa: N815

        def log_message(self, *args: Any) -> None:
            pass

    redirecting = _serve(Redirecting)
    try:
        yield Gateway(f"http://127.0.0.1:{redirecting.server_port}", other_url, hits)
    finally:
        for server in (redirecting, other):
            server.shutdown()
            server.server_close()


def _assert_refused(error: RedirectError, gateway: Gateway) -> None:
    assert error.status_code == 307
    assert error.location is not None
    assert error.location.startswith(gateway.other_url)
    assert gateway.hits == []


SYNC_CALLS: dict[str, Callable[[OtariClient], Any]] = {
    "generated core GET": lambda c: c.list_models(),
    "generated core POST": lambda c: c.embedding(model="openai:x", input="hi"),
    "streaming POST": lambda c: list(c.completion(model="openai:x", messages=MESSAGES, stream=True)),
    "raw POST": lambda c: c.speech(model="openai:tts-1", input="hi", voice="alloy"),
    "control plane": lambda c: c.control_plane.keys.list(),
}


async def _drain_stream(client: AsyncOtariClient) -> None:
    stream = await client.completion(model="openai:x", messages=MESSAGES, stream=True)
    async for _ in stream:
        pass


class TestRedirectIsRefused:
    @pytest.mark.parametrize("call", SYNC_CALLS.values(), ids=SYNC_CALLS.keys())
    def test_sync_client(self, gateway: Gateway, call: Callable[[OtariClient], Any]) -> None:
        client = OtariClient(gateway.url, api_key="vk", admin_key="master")

        with pytest.raises(RedirectError) as excinfo:
            call(client)

        _assert_refused(excinfo.value, gateway)

    def test_control_plane_built_directly(self, gateway: Gateway) -> None:
        control_plane = ControlPlane(gateway.url, "master")

        with pytest.raises(RedirectError) as excinfo:
            control_plane.keys.list()

        _assert_refused(excinfo.value, gateway)

    async def test_async_generated_core(self, gateway: Gateway) -> None:
        client = AsyncOtariClient(gateway.url, api_key="vk")

        with pytest.raises(RedirectError) as excinfo:
            await client.list_models()

        _assert_refused(excinfo.value, gateway)

    async def test_async_streaming(self, gateway: Gateway) -> None:
        client = AsyncOtariClient(gateway.url, api_key="vk")

        with pytest.raises(RedirectError) as excinfo:
            await _drain_stream(client)

        _assert_refused(excinfo.value, gateway)

    async def test_async_raw_post(self, gateway: Gateway) -> None:
        client = AsyncOtariClient(gateway.url, api_key="vk")

        with pytest.raises(RedirectError) as excinfo:
            await client.speech(model="openai:tts-1", input="hi", voice="alloy")

        _assert_refused(excinfo.value, gateway)
