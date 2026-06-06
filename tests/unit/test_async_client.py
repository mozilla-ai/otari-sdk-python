"""Tests for the asynchronous AsyncOtariClient (Option C: generated-core shell).

The async client dispatches the (synchronous) generated calls off-thread via
``asyncio.to_thread`` and streams natively over ``httpx.AsyncClient``. Non-
streaming calls reuse the ``mock_rest`` fixture (it patches the same generated
``RESTClientObject.request``); streaming uses ``respx``.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from otari._client.models.chat_completion import ChatCompletion
from otari._client.models.chat_completion_chunk import ChatCompletionChunk
from otari.async_client import AsyncOtariClient
from otari.errors import (
    AuthenticationError,
    GatewayTimeoutError,
    InsufficientFundsError,
    ModelNotFoundError,
    OtariError,
    RateLimitError,
    UpstreamProviderError,
)
from tests.unit.test_client import (
    CHAT_RESPONSE,
    EMBEDDING_RESPONSE,
    MESSAGE_RESPONSE,
    MODELS_RESPONSE,
    RERANK_RESPONSE,
    _sse,
)


class TestConstructor:
    def test_throws_when_api_base_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("GATEWAY_API_BASE", "OTARI_AI_TOKEN", "GATEWAY_PLATFORM_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        with pytest.raises(ValueError, match="api_base is required"):
            AsyncOtariClient()

    def test_platform_mode_sets_bearer(self) -> None:
        client = AsyncOtariClient(api_base="http://localhost:8000", platform_token="tk")  # noqa: S106
        assert client.platform_mode is True
        assert client._api.default_headers["Authorization"] == "Bearer tk"

    def test_non_platform_mode_sets_otari_key(self) -> None:
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        assert client.platform_mode is False
        assert client._api.default_headers["Otari-Key"] == "Bearer vk"


class TestInference:
    async def test_completion_returns_typed(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=CHAT_RESPONSE)
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        result = await client.completion(
            model="openai:gpt-4o-mini", messages=[{"role": "user", "content": "Hi"}]
        )
        assert isinstance(result, ChatCompletion)
        assert result.choices[0].message.content == "Hi"
        assert mock.last.url.endswith("/v1/chat/completions")
        assert mock.last.headers.get("Otari-Key") == "Bearer vk"

    async def test_embedding_returns_typed(self, mock_rest: Any) -> None:
        mock_rest(status=200, body=EMBEDDING_RESPONSE)
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        result = await client.embedding(model="m", input="hi")
        assert result.data[0].embedding == [0.1, 0.2]

    async def test_rerank_returns_typed(self, mock_rest: Any) -> None:
        mock_rest(status=200, body=RERANK_RESPONSE)
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        result = await client.rerank(model="m", query="q", documents=["a"])
        assert result.results[0].relevance_score == 0.9

    async def test_message_returns_typed(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=MESSAGE_RESPONSE)
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        result = await client.message(
            model="anthropic:claude", messages=[{"role": "user", "content": "Hi"}], max_tokens=8
        )
        assert result.id == "msg-1"
        assert mock.last.url.endswith("/v1/messages")

    async def test_list_models_returns_typed(self, mock_rest: Any) -> None:
        mock_rest(status=200, body=MODELS_RESPONSE)
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        models = await client.list_models()
        assert models[0].id == "openai:gpt-4o"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (402, InsufficientFundsError),
        (404, ModelNotFoundError),
        (429, RateLimitError),
        (502, UpstreamProviderError),
        (504, GatewayTimeoutError),
        (418, OtariError),
    ],
)
class TestErrorMapping:
    async def test_status_maps(
        self, mock_rest: Any, status: int, expected: type[OtariError]
    ) -> None:
        mock_rest(status=status, body={"detail": "boom"}, reason="err")
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(expected) as exc_info:
            await client.completion(model="m", messages=[{"role": "user", "content": "Hi"}])
        assert exc_info.value.status_code == status


class TestStreaming:
    @respx.mock
    async def test_yields_typed_chunks_and_stops_on_done(self) -> None:
        chunk1 = (
            '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
            '"choices":[{"index":0,"delta":{"role":"assistant","content":"He"}}]}'
        )
        chunk2 = (
            '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
            '"choices":[{"index":0,"delta":{"content":"llo"}}]}'
        )
        route = respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=_sse(chunk1, chunk2),
            )
        )
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        stream = await client.completion(
            model="m", messages=[{"role": "user", "content": "Hi"}], stream=True
        )
        chunks = [chunk async for chunk in stream]
        assert all(isinstance(c, ChatCompletionChunk) for c in chunks)
        assert [c.choices[0].delta.content for c in chunks] == ["He", "llo"]
        assert route.calls.last.request.headers["accept"] == "text/event-stream"
        assert route.calls.last.request.headers["otari-key"] == "Bearer vk"

    @respx.mock
    async def test_streaming_error_maps(self) -> None:
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(429, json={"detail": "rate limited"})
        )
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        stream = await client.completion(
            model="m", messages=[{"role": "user", "content": "Hi"}], stream=True
        )
        with pytest.raises(RateLimitError):
            _ = [chunk async for chunk in stream]


class TestControlPlane:
    def test_requires_admin_credential(self) -> None:
        client = AsyncOtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(OtariError, match="admin credential"):
            _ = client.control_plane
