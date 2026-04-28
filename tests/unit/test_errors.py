"""Tests for the otari error hierarchy.

Mirrors the TypeScript SDK's ``errors.test.ts``.
"""

from __future__ import annotations

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


class TestOtariError:
    def test_default_message(self) -> None:
        err = OtariError()
        assert str(err) == "An error occurred"
        assert err.message == "An error occurred"

    def test_custom_message(self) -> None:
        err = OtariError("custom message")
        assert err.message == "custom message"

    def test_status_code(self) -> None:
        err = OtariError("msg", status_code=500)
        assert err.status_code == 500

    def test_original_error(self) -> None:
        original = ValueError("original")
        err = OtariError("msg", original_error=original)
        assert err.original_error is original

    def test_provider_name_in_str(self) -> None:
        err = OtariError("msg", provider_name="gateway")
        assert str(err) == "[gateway] msg"

    def test_str_without_provider(self) -> None:
        err = OtariError("msg")
        assert str(err) == "msg"

    def test_is_exception(self) -> None:
        err = OtariError()
        assert isinstance(err, Exception)


class TestAuthenticationError:
    def test_default_message(self) -> None:
        err = AuthenticationError()
        assert err.message == "Authentication failed"

    def test_custom_message(self) -> None:
        err = AuthenticationError("custom")
        assert err.message == "custom"

    def test_isinstance_chain(self) -> None:
        err = AuthenticationError()
        assert isinstance(err, OtariError)
        assert isinstance(err, Exception)


class TestModelNotFoundError:
    def test_default_message(self) -> None:
        err = ModelNotFoundError()
        assert err.message == "Model not found"

    def test_isinstance_chain(self) -> None:
        err = ModelNotFoundError()
        assert isinstance(err, OtariError)


class TestInsufficientFundsError:
    def test_default_message(self) -> None:
        err = InsufficientFundsError()
        assert err.message == "Insufficient funds or budget exceeded"

    def test_isinstance_chain(self) -> None:
        err = InsufficientFundsError()
        assert isinstance(err, OtariError)


class TestRateLimitError:
    def test_default_message(self) -> None:
        err = RateLimitError()
        assert err.message == "Rate limit exceeded"

    def test_retry_after(self) -> None:
        err = RateLimitError("msg", retry_after="60")
        assert err.retry_after == "60"

    def test_retry_after_none_by_default(self) -> None:
        err = RateLimitError()
        assert err.retry_after is None

    def test_isinstance_chain(self) -> None:
        err = RateLimitError()
        assert isinstance(err, OtariError)
        assert isinstance(err, Exception)

    def test_str_with_provider(self) -> None:
        err = RateLimitError("rate limited", provider_name="gateway")
        assert str(err) == "[gateway] rate limited"


class TestUpstreamProviderError:
    def test_default_message(self) -> None:
        err = UpstreamProviderError()
        assert err.message == "Upstream provider error"

    def test_isinstance_chain(self) -> None:
        err = UpstreamProviderError()
        assert isinstance(err, OtariError)


class TestGatewayTimeoutError:
    def test_default_message(self) -> None:
        err = GatewayTimeoutError()
        assert err.message == "Gateway timeout waiting for upstream provider"

    def test_isinstance_chain(self) -> None:
        err = GatewayTimeoutError()
        assert isinstance(err, OtariError)


class TestBatchNotCompleteError:
    def test_default_message(self) -> None:
        err = BatchNotCompleteError()
        assert err.message == "Batch is not yet complete"

    def test_batch_id_and_status(self) -> None:
        err = BatchNotCompleteError(
            "Batch 'abc' is not complete (status: in_progress)",
            batch_id="abc",
            batch_status="in_progress",
        )
        assert err.batch_id == "abc"
        assert err.batch_status == "in_progress"

    def test_isinstance_chain(self) -> None:
        err = BatchNotCompleteError()
        assert isinstance(err, OtariError)
        assert isinstance(err, Exception)


class TestUnsupportedCapabilityError:
    def test_default_message(self) -> None:
        err = UnsupportedCapabilityError(capability="moderation", provider="anthropic")
        assert err.message == "The selected provider does not support this capability"

    def test_capability_and_provider(self) -> None:
        err = UnsupportedCapabilityError(
            "Provider anthropic does not support moderation",
            capability="moderation",
            provider="anthropic",
        )
        assert err.capability == "moderation"
        assert err.provider == "anthropic"

    def test_isinstance_chain(self) -> None:
        err = UnsupportedCapabilityError(capability="moderation", provider="x")
        assert isinstance(err, OtariError)
        assert isinstance(err, Exception)

    def test_str_with_provider_name(self) -> None:
        err = UnsupportedCapabilityError(
            "not supported",
            provider_name="gateway",
            capability="moderation",
            provider="anthropic",
        )
        assert str(err) == "[gateway] not supported"
