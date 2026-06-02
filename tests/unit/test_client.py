"""Tests for the synchronous OtariClient.

Mirrors the TypeScript SDK's ``client.test.ts`` covering constructor,
auth modes, error mapping, and method delegation.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import openai
import pytest

from otari.client import OtariClient
from otari.errors import (
    AuthenticationError,
    BatchNotCompleteError,
    GatewayTimeoutError,
    InsufficientFundsError,
    ModelNotFoundError,
    OtariError,
    RateLimitError,
    UnsupportedCapabilityError,
    UpstreamProviderError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_api_error(
    status: int,
    message: str,
    headers: dict[str, str] | None = None,
) -> openai.APIStatusError:
    """Build a fake ``openai.APIStatusError`` for testing error mapping."""
    resp_headers = httpx.Headers(headers or {})
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    response = httpx.Response(status_code=status, headers=resp_headers, request=request)
    return openai.APIStatusError(
        message=message,
        response=response,
        body={"message": message},
    )


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


class TestConstructor:
    def test_throws_when_api_base_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GATEWAY_API_BASE", raising=False)
        with pytest.raises(ValueError, match="api_base is required"):
            OtariClient()

    def test_uses_api_base_from_options(self) -> None:
        client = OtariClient(api_base="http://localhost:8000")
        assert str(client.openai.base_url).rstrip("/") == "http://localhost:8000/v1"

    def test_does_not_double_append_v1(self) -> None:
        client = OtariClient(api_base="http://localhost:8000/v1")
        assert str(client.openai.base_url).rstrip("/") == "http://localhost:8000/v1"

    def test_strips_trailing_slash(self) -> None:
        client = OtariClient(api_base="http://localhost:8000/")
        assert str(client.openai.base_url).rstrip("/") == "http://localhost:8000/v1"

    def test_falls_back_to_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_API_BASE", "http://env-gateway:9000")
        client = OtariClient()
        assert str(client.openai.base_url).rstrip("/") == "http://env-gateway:9000/v1"


class TestPlatformMode:
    def test_activates_with_explicit_token(self) -> None:
        client = OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_test123",  # noqa: S106
        )
        assert client.platform_mode is True
        assert client.openai.api_key == "tk_test123"

    def test_activates_via_env_when_no_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_PLATFORM_TOKEN", "tk_env_token")
        client = OtariClient(api_base="http://localhost:8000")
        assert client.platform_mode is True
        assert client.openai.api_key == "tk_env_token"

    def test_does_not_activate_when_api_key_provided(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_PLATFORM_TOKEN", "tk_env_token")
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        assert client.platform_mode is False


class TestHostedDefault:
    """Hosted-gateway default + OTARI_AI_TOKEN precedence (parity with TS SDK)."""

    @staticmethod
    def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
        for name in ("GATEWAY_API_BASE", "OTARI_AI_TOKEN", "GATEWAY_PLATFORM_TOKEN"):
            monkeypatch.delenv(name, raising=False)

    def test_platform_token_uses_hosted_default_base(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        client = OtariClient(platform_token="tk_x")  # noqa: S106
        assert client.platform_mode is True
        assert str(client.openai.base_url).rstrip("/") == "https://api.otari.ai/v1"

    def test_otari_ai_token_env_uses_hosted_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        monkeypatch.setenv("OTARI_AI_TOKEN", "tk_env")
        client = OtariClient()
        assert client.platform_mode is True
        assert str(client.openai.base_url).rstrip("/") == "https://api.otari.ai/v1"

    def test_api_key_only_no_base_still_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        with pytest.raises(ValueError, match="api_base is required"):
            OtariClient(api_key="k")

    def test_legacy_platform_token_env_uses_hosted_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        monkeypatch.setenv("GATEWAY_PLATFORM_TOKEN", "tk_legacy")
        client = OtariClient()
        assert client.platform_mode is True
        assert str(client.openai.base_url).rstrip("/") == "https://api.otari.ai/v1"

    def test_canonical_token_takes_precedence_over_legacy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        monkeypatch.setenv("OTARI_AI_TOKEN", "tk_canonical")
        monkeypatch.setenv("GATEWAY_PLATFORM_TOKEN", "tk_legacy")
        client = OtariClient()
        assert client.platform_mode is True
        assert client.openai.api_key == "tk_canonical"
        assert client._auth_headers["Authorization"] == "Bearer tk_canonical"

    def test_explicit_api_base_overrides_hosted_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear_env(monkeypatch)
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk_x")  # noqa: S106
        assert client.platform_mode is True
        assert str(client.openai.base_url).rstrip("/") == "http://localhost:8000/v1"


class TestNonPlatformMode:
    def test_is_default_without_platform_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GATEWAY_PLATFORM_TOKEN", raising=False)
        client = OtariClient(api_base="http://localhost:8000")
        assert client.platform_mode is False

    def test_falls_back_to_api_key_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GATEWAY_API_KEY", "env-key")
        monkeypatch.delenv("GATEWAY_PLATFORM_TOKEN", raising=False)
        client = OtariClient(api_base="http://localhost:8000")
        assert client.platform_mode is False

    def test_forwards_default_headers(self) -> None:
        client = OtariClient(
            api_base="http://localhost:8000",
            default_headers={"X-Custom": "value"},
        )
        assert client is not None


# ---------------------------------------------------------------------------
# Error handling (platform mode)
# ---------------------------------------------------------------------------


class TestErrorHandlingPlatformMode:
    @pytest.fixture
    def client(self) -> OtariClient:
        return OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_test",  # noqa: S106
        )

    def test_maps_401_to_authentication_error(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(401, "Unauthorized"),
        )
        with pytest.raises(AuthenticationError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_maps_403_to_authentication_error(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(403, "Forbidden"),
        )
        with pytest.raises(AuthenticationError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_maps_404_to_model_not_found(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(404, "Not Found"),
        )
        with pytest.raises(ModelNotFoundError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_maps_402_to_insufficient_funds(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(402, "Payment Required"),
        )
        with pytest.raises(InsufficientFundsError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_maps_429_to_rate_limit_with_retry_after(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(429, "Too Many Requests", {"retry-after": "60"}),
        )
        with pytest.raises(RateLimitError) as exc_info:
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc_info.value.retry_after == "60"

    def test_maps_502_to_upstream_provider_error(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(502, "Bad Gateway"),
        )
        with pytest.raises(UpstreamProviderError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_maps_504_to_gateway_timeout(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(504, "Gateway Timeout"),
        )
        with pytest.raises(GatewayTimeoutError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_includes_correlation_id_in_message(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(401, "Unauthorized", {"x-correlation-id": "abc-123"}),
        )
        with pytest.raises(AuthenticationError, match="correlation_id=abc-123"):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_passes_through_unrecognized_status(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(418, "I'm a teapot"),
        )
        with pytest.raises(openai.APIStatusError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_passes_through_non_api_error(self, client: OtariClient) -> None:
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=TypeError("network failure"),
        )
        with pytest.raises(TypeError, match="network failure"):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_stores_original_error(self, client: OtariClient) -> None:
        api_err = _make_api_error(401, "Unauthorized")
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=api_err,
        )
        with pytest.raises(AuthenticationError) as exc_info:
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc_info.value.original_error is api_err
        assert exc_info.value.provider_name == "gateway"
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Error handling (non-platform mode)
# ---------------------------------------------------------------------------


class TestErrorHandlingNonPlatformMode:
    def test_does_not_map_errors(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(401, "Unauthorized"),
        )
        # In non-platform mode, the raw APIStatusError should pass through.
        with pytest.raises(openai.APIStatusError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )

    def test_error_is_not_otari_error(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(401, "Unauthorized"),
        )
        with pytest.raises(openai.APIStatusError) as exc_info:
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert not isinstance(exc_info.value, OtariError)


# ---------------------------------------------------------------------------
# Unsupported capability error (both modes)
# ---------------------------------------------------------------------------


class TestUnsupportedCapabilityError:
    def test_surfaces_in_platform_mode(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk_test")  # noqa: S106
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(400, "Provider anthropic does not support moderation"),
        )
        with pytest.raises(UnsupportedCapabilityError) as exc_info:
            client.completion(
                model="anthropic:claude-3",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc_info.value.capability == "moderation"
        assert exc_info.value.provider == "anthropic"

    def test_surfaces_in_non_platform_mode(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(400, "Provider anthropic does not support moderation"),
        )
        with pytest.raises(UnsupportedCapabilityError) as exc_info:
            client.completion(
                model="anthropic:claude-3",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc_info.value.capability == "moderation"

    def test_multimodal_moderation(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk_test")  # noqa: S106
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(
                400, "Provider openai does not support multimodal moderation for this model"
            ),
        )
        with pytest.raises(UnsupportedCapabilityError) as exc_info:
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )
        assert exc_info.value.capability == "multimodal_moderation"

    def test_unrelated_400_passes_through_in_non_platform(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        client.openai.chat.completions.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(400, "Invalid request parameters"),
        )
        with pytest.raises(openai.APIStatusError):
            client.completion(
                model="openai:gpt-4o-mini",
                messages=[{"role": "user", "content": "hi"}],
            )


# ---------------------------------------------------------------------------
# Method delegation
# ---------------------------------------------------------------------------


class TestMethodDelegation:
    @pytest.fixture
    def client(self) -> OtariClient:
        return OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_test",  # noqa: S106
        )

    def test_completion_delegates(self, client: OtariClient) -> None:
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.choices = []
        client.openai.chat.completions.create = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert result is mock_response
        client.openai.chat.completions.create.assert_called_once_with(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "hi"}],
        )

    def test_embedding_delegates(self, client: OtariClient) -> None:
        mock_response = MagicMock()
        client.openai.embeddings.create = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.embedding(
            model="openai:text-embedding-3-small",
            input="hello",
        )
        assert result is mock_response
        client.openai.embeddings.create.assert_called_once_with(
            model="openai:text-embedding-3-small",
            input="hello",
        )

    def test_response_delegates(self, client: OtariClient) -> None:
        mock_response = MagicMock()
        client.openai.responses.create = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.response(
            model="openai:gpt-4o-mini",
            input="hello",
        )
        assert result is mock_response

    def test_list_models_delegates(self, client: OtariClient) -> None:
        mock_models = [
            MagicMock(id="model-1"),
            MagicMock(id="model-2"),
        ]

        mock_page = MagicMock()
        mock_page.__iter__.return_value = iter(mock_models)
        client.openai.models.list = MagicMock(return_value=mock_page)  # type: ignore[method-assign]

        result = client.list_models()
        assert result == mock_models

    def test_error_mapping_on_embedding(self, client: OtariClient) -> None:
        client.openai.embeddings.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(401, "Unauthorized"),
        )
        with pytest.raises(AuthenticationError):
            client.embedding(model="openai:text-embedding-3-small", input="hello")

    def test_error_mapping_on_response(self, client: OtariClient) -> None:
        client.openai.responses.create = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(429, "Rate limited"),
        )
        with pytest.raises(RateLimitError):
            client.response(model="openai:gpt-4o-mini", input="hello")

    def test_error_mapping_on_list_models(self, client: OtariClient) -> None:
        client.openai.models.list = MagicMock(  # type: ignore[method-assign]
            side_effect=_make_api_error(502, "Bad Gateway"),
        )
        with pytest.raises(UpstreamProviderError):
            client.list_models()


# ---------------------------------------------------------------------------
# Batch operations
# ---------------------------------------------------------------------------


class TestBatchOperations:
    @pytest.fixture
    def client(self) -> OtariClient:
        return OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_test",  # noqa: S106
        )

    def test_create_batch(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            200,
            json={"id": "batch-123", "status": "created", "provider": "openai"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.create_batch({
            "model": "openai:gpt-4o-mini",
            "requests": [{"custom_id": "r1", "body": {"messages": []}}],
        })
        assert result["id"] == "batch-123"

    def test_retrieve_batch(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            200,
            json={"id": "batch-123", "status": "completed"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.retrieve_batch("batch-123", "openai")
        assert result["status"] == "completed"

    def test_cancel_batch(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            200,
            json={"id": "batch-123", "status": "cancelled"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.cancel_batch("batch-123", "openai")
        assert result["status"] == "cancelled"

    def test_list_batches(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            200,
            json={"data": [{"id": "b1"}, {"id": "b2"}]},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.list_batches("openai")
        assert len(result) == 2

    def test_retrieve_batch_results(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            200,
            json={
                "results": [
                    {"custom_id": "r1", "result": {"id": "cmpl-1", "choices": []}},
                    {"custom_id": "r2", "error": {"code": "err", "message": "failed"}},
                ]
            },
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        result = client.retrieve_batch_results("batch-123", "openai")
        assert len(result.results) == 2
        assert result.results[0].custom_id == "r1"
        assert result.results[1].error is not None


class TestBatchErrorHandling:
    @pytest.fixture
    def client(self) -> OtariClient:
        return OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_test",  # noqa: S106
        )

    def test_409_maps_to_batch_not_complete(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            409,
            json={"detail": "Batch 'batch-123' is not complete (status: in_progress)"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(BatchNotCompleteError) as exc_info:
            client.retrieve_batch_results("batch-123", "openai")
        assert exc_info.value.batch_id == "batch-123"
        assert exc_info.value.batch_status == "in_progress"

    def test_404_suggests_upgrade(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            404,
            json={"detail": "Not supported"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(OtariError, match="Upgrade your gateway"):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })

    def test_404_passes_through_not_found(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            404,
            json={"detail": "Batch not found"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(OtariError, match="not found"):
            client.retrieve_batch("batch-xyz", "openai")

    def test_401_maps_to_authentication_error(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            401,
            json={"detail": "Invalid key"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(AuthenticationError):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })

    def test_429_maps_to_rate_limit(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            429,
            headers={"retry-after": "30"},
            json={"detail": "Rate limited"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(RateLimitError) as exc_info:
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })
        assert exc_info.value.retry_after == "30"

    def test_502_maps_to_upstream_error(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            502,
            json={"detail": "Bad Gateway"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(UpstreamProviderError):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })

    def test_504_maps_to_gateway_timeout(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            504,
            json={"detail": "Gateway Timeout"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(GatewayTimeoutError):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })

    def test_correlation_id_in_batch_error(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            401,
            headers={"x-correlation-id": "corr-456"},
            json={"detail": "Invalid key"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(AuthenticationError, match="correlation_id=corr-456"):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })

    def test_unknown_status_maps_to_otari_error(self, client: OtariClient) -> None:
        mock_response = httpx.Response(
            418,
            json={"detail": "I'm a teapot"},
        )
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        with pytest.raises(OtariError):
            client.create_batch({
                "model": "openai:gpt-4o-mini",
                "requests": [],
            })


# ---------------------------------------------------------------------------
# Batch auth modes
# ---------------------------------------------------------------------------


class TestBatchAuthModes:
    def test_non_platform_sends_otari_key(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", api_key="my-key")
        mock_response = httpx.Response(200, json={"id": "b1", "provider": "openai"})
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        client.create_batch({
            "model": "openai:gpt-4o-mini",
            "requests": [],
        })
        call_kwargs = client._http.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers.get("Otari-Key") == "Bearer my-key"
        assert "Authorization" not in headers

    def test_platform_sends_authorization(self) -> None:
        client = OtariClient(api_base="http://localhost:8000", platform_token="tk_123")  # noqa: S106
        mock_response = httpx.Response(200, json={"id": "b1", "provider": "openai"})
        client._http.request = MagicMock(return_value=mock_response)  # type: ignore[method-assign]

        client.create_batch({
            "model": "openai:gpt-4o-mini",
            "requests": [],
        })
        call_kwargs = client._http.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers.get("Authorization") == "Bearer tk_123"
        assert "Otari-Key" not in headers


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_context_manager(self) -> None:
        with OtariClient(api_base="http://localhost:8000") as client:
            assert client.platform_mode is False
