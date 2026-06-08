"""Tests for the synchronous OtariClient (Option C: generated-core shell).

Covers constructor / auth-mode wiring, request shaping, typed response parsing,
generated ``ApiException`` -> typed error mapping, and the hand-written SSE
streaming shim. Non-streaming calls are mocked at the generated transport
(``RESTClientObject.request``, see ``conftest.py``); streaming is mocked with
``respx`` over the httpx layer the shim uses.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from otari._client.models.chat_completion import ChatCompletion
from otari._client.models.chat_completion_chunk import ChatCompletionChunk
from otari.client import OtariClient
from otari.errors import (
    AuthenticationError,
    GatewayTimeoutError,
    InsufficientFundsError,
    ModelNotFoundError,
    OtariError,
    RateLimitError,
    UnsupportedCapabilityError,
    UpstreamProviderError,
)

# ---------------------------------------------------------------------------
# Response fixtures (validated against the generated models)
# ---------------------------------------------------------------------------

CHAT_RESPONSE: dict[str, Any] = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "openai:gpt-4o-mini",
    "choices": [
        {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "Hi"}}
    ],
}

EMBEDDING_RESPONSE: dict[str, Any] = {
    "object": "list",
    "model": "openai:text-embedding-3-small",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
    "usage": {"prompt_tokens": 1, "total_tokens": 1},
}

RERANK_RESPONSE: dict[str, Any] = {
    "id": "rerank-1",
    "results": [{"index": 0, "relevance_score": 0.9}],
}

MESSAGE_RESPONSE: dict[str, Any] = {
    "id": "msg-1",
    "type": "message",
    "role": "assistant",
    "model": "anthropic:claude-3-5-sonnet",
    "content": [{"type": "text", "text": "Hi"}],
    "usage": {"input_tokens": 1, "output_tokens": 1},
}

MODERATION_RESPONSE: dict[str, Any] = {
    "id": "modr-1",
    "model": "openai:omni-moderation-latest",
    "results": [{"flagged": False, "categories": {}, "category_scores": {}}],
}

MODELS_RESPONSE: dict[str, Any] = {
    "object": "list",
    "data": [{"id": "openai:gpt-4o", "object": "model", "created": 1, "owned_by": "openai"}],
}


def _sse(*events: str) -> bytes:
    """Build a ``text/event-stream`` body from JSON event strings + the DONE sentinel."""
    body = "".join(f"data: {e}\n\n" for e in events)
    return (body + "data: [DONE]\n\n").encode()


# ---------------------------------------------------------------------------
# Constructor / auth-mode wiring
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_throws_when_api_base_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("GATEWAY_API_BASE", "OTARI_AI_TOKEN", "GATEWAY_PLATFORM_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        with pytest.raises(ValueError, match="api_base is required"):
            OtariClient()

    def test_uses_api_base_from_options(self) -> None:
        client = OtariClient(api_base="http://localhost:8000")
        assert client._base_url == "http://localhost:8000/v1"
        assert client._gateway_root_url == "http://localhost:8000"

    def test_does_not_double_append_v1(self) -> None:
        client = OtariClient(api_base="http://localhost:8000/v1")
        assert client._base_url == "http://localhost:8000/v1"

    def test_strips_trailing_slash(self) -> None:
        client = OtariClient(api_base="http://localhost:8000/")
        assert client._base_url == "http://localhost:8000/v1"

    def test_falls_back_to_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_API_BASE", "http://env-gateway:9000")
        client = OtariClient()
        assert client._base_url == "http://env-gateway:9000/v1"


class TestAuthModes:
    def test_platform_mode_sets_bearer_header(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk_test")  # noqa: S106
        assert client.platform_mode is True
        assert client._default_headers["Authorization"] == "Bearer tk_test"
        assert "Otari-Key" not in client._default_headers
        # The header is fed into the generated ApiClient default headers.
        assert client._api.default_headers["Authorization"] == "Bearer tk_test"

    def test_platform_mode_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OTARI_AI_TOKEN", "tk_env")
        client = OtariClient(api_base="http://localhost:8000")
        assert client.platform_mode is True
        assert client._default_headers["Authorization"] == "Bearer tk_env"

    def test_non_platform_mode_sets_otari_key_header(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="vk_123")
        assert client.platform_mode is False
        assert client._default_headers["Otari-Key"] == "Bearer vk_123"
        assert "Authorization" not in client._default_headers
        assert client._api.default_headers["Otari-Key"] == "Bearer vk_123"

    def test_api_key_overrides_platform_token_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_PLATFORM_TOKEN", "tk_env")
        client = OtariClient(api_base="http://localhost:8000", api_key="vk_123")
        assert client.platform_mode is False

    def test_hosted_default_base_in_platform_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("GATEWAY_API_BASE", "OTARI_AI_TOKEN", "GATEWAY_PLATFORM_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        client = OtariClient(platform_token="tk_x")  # noqa: S106
        assert client._base_url == "https://api.otari.ai/v1"


# ---------------------------------------------------------------------------
# Request shaping + typed response parsing
# ---------------------------------------------------------------------------


class TestCompletion:
    def test_returns_typed_chat_completion(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=CHAT_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        result = client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.5,
        )
        assert isinstance(result, ChatCompletion)
        assert result.choices[0].message.content == "Hi"
        # Request shaping: correct path + body, with the Otari-Key auth header.
        assert mock.last.method == "POST"
        assert mock.last.url.endswith("/v1/chat/completions")
        body = mock.last.json_body
        assert body["model"] == "openai:gpt-4o-mini"
        assert body["temperature"] == 0.5
        assert mock.last.headers.get("Otari-Key") == "Bearer vk"

    def test_platform_mode_sends_bearer(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=CHAT_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk")  # noqa: S106
        client.completion(model="m", messages=[{"role": "user", "content": "Hi"}])
        assert mock.last.headers.get("Authorization") == "Bearer tk"


class TestEmbedding:
    def test_returns_typed_embedding(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=EMBEDDING_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        result = client.embedding(model="openai:text-embedding-3-small", input="hello")
        assert result.data[0].embedding == [0.1, 0.2]
        assert mock.last.url.endswith("/v1/embeddings")
        assert mock.last.json_body["input"] == "hello"


class TestRerank:
    def test_returns_typed_rerank(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=RERANK_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        result = client.rerank(model="m", query="q", documents=["a", "b"])
        assert result.results[0].relevance_score == 0.9
        assert mock.last.url.endswith("/v1/rerank")
        assert mock.last.json_body["documents"] == ["a", "b"]


class TestMessage:
    def test_returns_typed_message_response(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=MESSAGE_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        result = client.message(
            model="anthropic:claude-3-5-sonnet",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=64,
        )
        assert result.id == "msg-1"
        assert mock.last.url.endswith("/v1/messages")
        body = mock.last.json_body
        assert body["max_tokens"] == 64
        assert body["model"] == "anthropic:claude-3-5-sonnet"


class TestModeration:
    def test_returns_typed_moderation(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=MODERATION_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        result = client.moderation(model="m", input="text")
        assert result.results[0].flagged is False
        assert mock.last.url.endswith("/v1/moderations")


class TestListModels:
    def test_returns_typed_models(self, mock_rest: Any) -> None:
        mock = mock_rest(status=200, body=MODELS_RESPONSE)
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        models = client.list_models()
        assert models[0].id == "openai:gpt-4o"
        assert mock.last.url.endswith("/v1/models")


# ---------------------------------------------------------------------------
# Error mapping (generated ApiException -> typed otari errors)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (403, AuthenticationError),
        (402, InsufficientFundsError),
        (404, ModelNotFoundError),
        (429, RateLimitError),
        (502, UpstreamProviderError),
        (503, UpstreamProviderError),
        (504, GatewayTimeoutError),
        (418, OtariError),
    ],
)
class TestErrorMapping:
    def test_status_maps_to_error(
        self, mock_rest: Any, status: int, expected: type[OtariError]
    ) -> None:
        mock_rest(status=status, body={"detail": "boom"}, reason="err")
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(expected) as exc_info:
            client.completion(model="m", messages=[{"role": "user", "content": "Hi"}])
        assert exc_info.value.status_code == status
        assert "boom" in str(exc_info.value)


class TestErrorDetails:
    def test_rate_limit_carries_retry_after(self, mock_rest: Any) -> None:
        mock_rest(status=429, body={"detail": "slow down"}, headers={"retry-after": "30"})
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(RateLimitError) as exc_info:
            client.completion(model="m", messages=[{"role": "user", "content": "Hi"}])
        assert exc_info.value.retry_after == "30"

    def test_correlation_id_in_message(self, mock_rest: Any) -> None:
        mock_rest(status=402, body={"detail": "no funds"}, headers={"x-correlation-id": "abc-123"})
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(InsufficientFundsError) as exc_info:
            client.completion(model="m", messages=[{"role": "user", "content": "Hi"}])
        assert "abc-123" in str(exc_info.value)

    def test_unsupported_moderation_maps_in_any_mode(self, mock_rest: Any) -> None:
        mock_rest(
            status=400, body={"detail": "Provider anthropic does not support moderation"}
        )
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(UnsupportedCapabilityError) as exc_info:
            client.moderation(model="anthropic:claude", input="text")
        assert exc_info.value.provider == "anthropic"
        assert exc_info.value.capability == "moderation"


# ---------------------------------------------------------------------------
# SSE streaming shim (chat = must-have)
# ---------------------------------------------------------------------------


class TestChatStreaming:
    @respx.mock
    def test_yields_typed_chunks_and_stops_on_done(self) -> None:
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
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        stream = client.completion(
            model="m", messages=[{"role": "user", "content": "Hi"}], stream=True
        )
        chunks = list(stream)
        assert all(isinstance(c, ChatCompletionChunk) for c in chunks)
        assert [c.choices[0].delta.content for c in chunks] == ["He", "llo"]
        # The streaming request set the SSE Accept + auth header and stream flag.
        request = route.calls.last.request
        assert request.headers["accept"] == "text/event-stream"
        assert request.headers["otari-key"] == "Bearer vk"

    @respx.mock
    def test_streaming_error_maps_to_typed_error(self) -> None:
        respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(429, json={"detail": "rate limited"})
        )
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(RateLimitError):
            list(
                client.completion(
                    model="m", messages=[{"role": "user", "content": "Hi"}], stream=True
                )
            )

    @respx.mock
    def test_platform_mode_streaming_sends_bearer(self) -> None:
        chunk = (
            '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
            '"choices":[{"index":0,"delta":{"content":"x"}}]}'
        )
        route = respx.post("http://localhost:8000/v1/chat/completions").mock(
            return_value=httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=_sse(chunk)
            )
        )
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk")  # noqa: S106
        list(
            client.completion(
                model="m", messages=[{"role": "user", "content": "Hi"}], stream=True
            )
        )
        assert route.calls.last.request.headers["authorization"] == "Bearer tk"


# ---------------------------------------------------------------------------
# Control-plane accessor
# ---------------------------------------------------------------------------


class TestControlPlane:
    def test_requires_admin_credential(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="vk")
        with pytest.raises(OtariError, match="admin credential"):
            _ = client.control_plane

    def test_available_with_admin_key(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", admin_key="master")
        cp = client.control_plane
        assert cp.keys is not None
        assert cp._api_client.default_headers["Authorization"] == "Bearer master"
        cp.close()
