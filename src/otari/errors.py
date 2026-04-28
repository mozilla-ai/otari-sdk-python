"""Exception hierarchy for otari gateway errors.

Mirrors the TypeScript SDK's exception classes. In platform mode,
OpenAI ``APIStatusError`` status codes are mapped to these typed errors
so callers can handle specific failure modes.
"""

from __future__ import annotations


class OtariError(Exception):
    """Base exception for all otari errors.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code from the gateway, if available.
        original_error: The original SDK exception that triggered this error.
        provider_name: Name of the provider that raised the error.
    """

    default_message: str = "An error occurred"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        original_error: Exception | None = None,
        provider_name: str | None = None,
    ) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
        self.status_code = status_code
        self.original_error = original_error
        self.provider_name = provider_name

    def __str__(self) -> str:
        if self.provider_name:
            return f"[{self.provider_name}] {self.message}"
        return self.message


class AuthenticationError(OtariError):
    """Raised when authentication with the gateway fails (HTTP 401, 403)."""

    default_message = "Authentication failed"


class ModelNotFoundError(OtariError):
    """Raised when the requested model is not found (HTTP 404)."""

    default_message = "Model not found"


class InsufficientFundsError(OtariError):
    """Raised when the user's budget or credits are exhausted (HTTP 402)."""

    default_message = "Insufficient funds or budget exceeded"


class RateLimitError(OtariError):
    """Raised when the API rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Value of the ``Retry-After`` header, when the server
            provides one. May be a number of seconds or an HTTP-date string.
    """

    default_message = "Rate limit exceeded"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        original_error: Exception | None = None,
        provider_name: str | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            original_error=original_error,
            provider_name=provider_name,
        )
        self.retry_after = retry_after


class UpstreamProviderError(OtariError):
    """Raised when the upstream provider is unreachable or errors (HTTP 502)."""

    default_message = "Upstream provider error"


class GatewayTimeoutError(OtariError):
    """Raised when the gateway times out waiting for the upstream provider (HTTP 504)."""

    default_message = "Gateway timeout waiting for upstream provider"


class BatchNotCompleteError(OtariError):
    """Raised when attempting to retrieve results for a batch that is not yet complete (HTTP 409).

    Attributes:
        batch_id: The ID of the batch.
        batch_status: The current status of the batch.
    """

    default_message = "Batch is not yet complete"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        original_error: Exception | None = None,
        provider_name: str | None = None,
        batch_id: str | None = None,
        batch_status: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            original_error=original_error,
            provider_name=provider_name,
        )
        self.batch_id = batch_id
        self.batch_status = batch_status


class UnsupportedCapabilityError(OtariError):
    """Raised when the gateway reports that the selected provider does not
    support a requested capability (e.g. moderation).

    Attributes:
        capability: Capability that was requested (e.g. ``"moderation"``).
        provider: Provider name reported by the gateway (e.g. ``"anthropic"``).
    """

    default_message = "The selected provider does not support this capability"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        original_error: Exception | None = None,
        provider_name: str | None = None,
        capability: str = "",
        provider: str = "",
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            original_error=original_error,
            provider_name=provider_name,
        )
        self.capability = capability
        self.provider = provider
