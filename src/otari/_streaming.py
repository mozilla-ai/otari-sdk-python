"""Server-Sent-Events (SSE) streaming shim for the otari gateway clients.

The OpenAPI-generated core in :mod:`otari._client` buffers the full HTTP
response before deserializing, so it *cannot* stream. (This is a known upstream
OpenAPI Generator limitation.) For ``stream=True`` on chat, responses, and
messages, the SDK hand-writes the stream here: a raw streaming POST via
``httpx`` that parses ``text/event-stream`` framing and yields typed chunks.

Wire format (gateway emits the OpenAI / Anthropic SSE convention):

    data: {"id": "...", ...}\\n
    \\n
    data: {"id": "...", ...}\\n
    \\n
    data: [DONE]\\n
    \\n

Each event is ``data: <payload>``; a blank line terminates an event; the
sentinel ``data: [DONE]`` ends the stream. ``event:``/``id:``/``:``-comment
lines are ignored (the gateway does not use named events for chat).

``parse_chunk`` decides the yielded type per endpoint:

- chat -> typed :class:`otari._client.models.ChatCompletionChunk`
- responses / messages -> the parsed JSON ``dict`` (no single typed chunk model
  exists for these provider-shaped event streams; callers get the raw event).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

from otari._client.models.chat_completion_chunk import ChatCompletionChunk

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    import httpx

StreamKind = Literal["chat", "responses", "messages"]

_DONE = "[DONE]"
_DATA_PREFIX = "data:"


def parse_chunk(kind: StreamKind, payload: str) -> Any:
    """Parse one SSE ``data:`` payload into the chunk type for ``kind``.

    Chat yields a typed :class:`ChatCompletionChunk`; responses/messages yield
    the parsed JSON ``dict`` (their event streams have no single typed model).
    """
    if kind == "chat":
        chunk = ChatCompletionChunk.from_json(payload)
        if chunk is None:  # pragma: no cover - from_json only returns None for empty input
            msg = "received empty chat completion chunk payload"
            raise ValueError(msg)
        return chunk
    return json.loads(payload)


def _iter_data_lines(line: str) -> str | None:
    """Return the ``data:`` payload of an SSE line, or ``None`` to skip it.

    Returns the sentinel string ``"[DONE]"`` unchanged so the caller can stop.
    """
    stripped = line.rstrip("\n").rstrip("\r")
    if not stripped or stripped.startswith(":"):
        return None
    if not stripped.startswith(_DATA_PREFIX):
        # event:/id:/retry: framing lines carry no chunk data for our streams.
        return None
    return stripped[len(_DATA_PREFIX) :].strip()


def iter_sse(
    response: httpx.Response,
    kind: StreamKind,
) -> Iterator[Any]:
    """Yield parsed chunks from a *synchronous* streaming httpx response.

    Stops on the ``data: [DONE]`` sentinel and on end-of-stream.
    """
    for line in response.iter_lines():
        payload = _iter_data_lines(line)
        if payload is None:
            continue
        if payload == _DONE:
            return
        yield parse_chunk(kind, payload)


async def aiter_sse(
    response: httpx.Response,
    kind: StreamKind,
) -> AsyncIterator[Any]:
    """Yield parsed chunks from an *asynchronous* streaming httpx response.

    Stops on the ``data: [DONE]`` sentinel and on end-of-stream.
    """
    async for line in response.aiter_lines():
        payload = _iter_data_lines(line)
        if payload is None:
            continue
        if payload == _DONE:
            return
        yield parse_chunk(kind, payload)
