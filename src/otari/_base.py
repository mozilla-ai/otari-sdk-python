"""Shared logic for the sync and async otari gateway clients.

Holds everything that does not depend on whether the underlying transport is
synchronous or asynchronous: auth-mode resolution, base-URL normalization,
header building, and error mapping. The concrete clients
(:class:`~otari.client.OtariClient` and
:class:`~otari.async_client.AsyncOtariClient`) construct their own OpenAI and
httpx clients and implement the I/O methods on top of this base.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import TYPE_CHECKING, Any

import openai

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

if TYPE_CHECKING:
    import httpx

PROVIDER_NAME = "gateway"
GATEWAY_HEADER_NAME = "Otari-Key"

# Locked phrasing used by the gateway to signal that the selected
# provider does not support a moderation request.
_UNSUPPORTED_MODERATION_RE = re.compile(r"does not support (?:multimodal )?moderation")

_DEFAULT_PLATFORM_API_BASE = "https://api.otari.ai"

_ENV_API_BASE = "GATEWAY_API_BASE"
_ENV_API_KEY = "GATEWAY_API_KEY"
# Matches the gateway server's own alias chain (OTARI_AI_TOKEN preferred).
_ENV_PLATFORM_TOKEN = "OTARI_AI_TOKEN"  # noqa: S105
_ENV_PLATFORM_TOKEN_LEGACY = "GATEWAY_PLATFORM_TOKEN"  # noqa: S105

_STATUS_TO_ERROR: dict[int, type[AuthenticationError] | type[ModelNotFoundError]] = {
    401: AuthenticationError,
    403: AuthenticationError,
    404: ModelNotFoundError,
}


class _BaseOtariClient:
    """Transport-agnostic base for the otari gateway clients.

    Subclasses are responsible for constructing the underlying OpenAI client
    (``OpenAI`` or ``AsyncOpenAI``) and the httpx client (``httpx.Client`` or
    ``httpx.AsyncClient``) using the resolved configuration attributes set up
    here.
    """

    platform_mode: bool
    """Whether the client is operating in platform mode."""

    def __init__(
        self,
        api_base: str | None = None,
        *,
        api_key: str | None = None,
        platform_token: str | None = None,
        default_headers: dict[str, str] | None = None,
        openai_options: dict[str, Any] | None = None,
    ) -> None:
        # Canonical OTARI_AI_TOKEN wins over the legacy GATEWAY_PLATFORM_TOKEN.
        resolved_platform_token = (
            platform_token
            or os.environ.get(_ENV_PLATFORM_TOKEN)
            or os.environ.get(_ENV_PLATFORM_TOKEN_LEGACY)
        )
        resolved_api_key = api_key or os.environ.get(_ENV_API_KEY, "")

        # Platform mode activates when a platform token is available and the
        # caller hasn't explicitly passed an api_key (which forces non-platform
        # mode). Mirrors the TS SDK's `!options.apiKey` check.
        will_use_platform_mode = bool(resolved_platform_token) and not api_key

        # In platform mode, fall back to the hosted otari.ai gateway so that
        # ``OtariClient(platform_token=...)`` works with no further setup. For
        # self-hosted gateways the caller must supply api_base — we have no way
        # to know where they've hosted it.
        raw_base = (
            api_base
            or os.environ.get(_ENV_API_BASE)
            or (_DEFAULT_PLATFORM_API_BASE if will_use_platform_mode else None)
        )

        if not raw_base:
            msg = (
                "api_base is required for the gateway client. "
                f"Pass it as api_base or set the {_ENV_API_BASE} environment variable."
            )
            raise ValueError(msg)

        # Ensure the base URL includes /v1 since the gateway expects
        # OpenAI-compatible paths like /v1/chat/completions.
        cleaned = raw_base.rstrip("/")
        api_base_url = cleaned if cleaned.endswith("/v1") else f"{cleaned}/v1"

        self._base_url = api_base_url

        headers: dict[str, str] = {**(default_headers or {})}

        # Auth resolution (same logic as TS SDK / Python GatewayProvider):
        # 1. Explicit platform_token -> platform mode
        # 2. OTARI_AI_TOKEN (or legacy GATEWAY_PLATFORM_TOKEN) env + no api_key
        #    option -> platform mode
        # 3. Otherwise -> non-platform mode
        if resolved_platform_token and not api_key:
            self.platform_mode = True
            self._platform_token: str | None = resolved_platform_token
            self._api_key: str | None = None
            # In platform mode the OpenAI client carries the Bearer token.
            self._openai_api_key = resolved_platform_token
        else:
            self.platform_mode = False
            self._platform_token = None
            self._api_key = resolved_api_key or None
            if resolved_api_key:
                headers[GATEWAY_HEADER_NAME] = f"Bearer {resolved_api_key}"
            # In non-platform mode we still need to pass *some* API key to the
            # OpenAI client (it validates the field).
            self._openai_api_key = resolved_api_key or "unused"

        # Configuration the concrete client uses to build its OpenAI client.
        self._openai_base_url = api_base_url
        self._openai_default_headers = headers or None
        self._openai_extra_kwargs: dict[str, Any] = {**(openai_options or {})}

        # Store auth headers for batch/raw HTTP calls.
        self._auth_headers: dict[str, str] = {}
        if resolved_platform_token and not api_key:
            self._auth_headers["Authorization"] = f"Bearer {resolved_platform_token}"
        elif resolved_api_key:
            self._auth_headers[GATEWAY_HEADER_NAME] = f"Bearer {resolved_api_key}"
        if default_headers:
            self._auth_headers.update(default_headers)

    # -- Error handling -----------------------------------------------------

    def _handle_error(self, error: Exception) -> None:
        """Convert ``openai.APIStatusError`` to typed otari exceptions.

        Most mappings only apply in platform mode; in non-platform mode the
        original error propagates unchanged. The one exception is
        :class:`UnsupportedCapabilityError`, which surfaces in both modes.
        """
        if not isinstance(error, openai.APIStatusError):
            return

        status = error.status_code
        headers = error.response.headers
        correlation_id = headers.get("x-correlation-id")
        retry_after = headers.get("retry-after")

        detail = str(getattr(error, "message", str(error)))
        if correlation_id:
            detail = f"{detail} (correlation_id={correlation_id})"

        # Unsupported-capability is surfaced regardless of mode.
        if status == 400 and _UNSUPPORTED_MODERATION_RE.search(detail):
            provider = _parse_unsupported_provider(detail)
            capability = "multimodal_moderation" if "multimodal" in detail else "moderation"
            raise UnsupportedCapabilityError(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
                provider=provider,
                capability=capability,
            ) from error

        # The rest of the mappings only apply in platform mode.
        if not self.platform_mode:
            return

        if (error_cls := _STATUS_TO_ERROR.get(status)) is not None:
            raise error_cls(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
            ) from error

        if status == 402:
            raise InsufficientFundsError(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
            ) from error

        if status == 429:
            raise RateLimitError(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
                retry_after=retry_after,
            ) from error

        if status == 502:
            raise UpstreamProviderError(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
            ) from error

        if status == 504:
            raise GatewayTimeoutError(
                detail,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
            ) from error

        # Unrecognized status: let the original error propagate.

    def _build_batch_headers(self) -> dict[str, str]:
        """Build the headers used for raw batch HTTP requests."""
        return {
            "Content-Type": "application/json",
            **self._auth_headers,
        }

    def _map_batch_error(self, response: httpx.Response) -> None:
        """Map a failed batch HTTP response to a typed SDK error.

        ``response.json()`` is read synchronously, so this works for both the
        sync and async clients (the async client has already received the full
        body by the time it calls this).
        """
        try:
            data = response.json()
            detail = data.get("detail", response.reason_phrase)
        except Exception:
            detail = response.reason_phrase or ""

        message = detail if isinstance(detail, str) else (response.reason_phrase or "")
        correlation_id = response.headers.get("x-correlation-id")
        full_message = f"{message} (correlation_id={correlation_id})" if correlation_id else message

        status = response.status_code

        if status in (401, 403):
            raise AuthenticationError(
                full_message,
                status_code=status,
                provider_name=PROVIDER_NAME,
            )

        if status == 404:
            msg = (
                full_message
                if "not found" in full_message.lower()
                else f"This gateway does not support batch operations. Upgrade your gateway. ({full_message})"
            )
            raise OtariError(msg, status_code=404, provider_name=PROVIDER_NAME)

        if status == 409:
            raise BatchNotCompleteError(
                full_message,
                status_code=409,
                provider_name=PROVIDER_NAME,
                batch_id=_extract_batch_id(message),
                batch_status=_extract_status(message),
            )

        if status == 422:
            raise OtariError(full_message, status_code=422, provider_name=PROVIDER_NAME)

        if status == 429:
            raise RateLimitError(
                full_message,
                status_code=429,
                provider_name=PROVIDER_NAME,
                retry_after=response.headers.get("retry-after"),
            )

        if status == 502:
            raise UpstreamProviderError(
                full_message,
                status_code=502,
                provider_name=PROVIDER_NAME,
            )

        if status == 504:
            raise GatewayTimeoutError(
                full_message,
                status_code=504,
                provider_name=PROVIDER_NAME,
            )

        raise OtariError(full_message, status_code=status, provider_name=PROVIDER_NAME)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _parse_unsupported_provider(detail: str) -> str:
    """Parse the provider name from a gateway 400 detail string.

    Example: ``"Provider anthropic does not support moderation"``
    """
    match = re.search(r"Provider\s+(\S+)\s+does not", detail)
    return match.group(1) if match else "unknown"


def _extract_batch_id(message: str) -> str | None:
    match = re.search(r"Batch '([^']+)'", message)
    return match.group(1) if match else None


def _extract_status(message: str) -> str | None:
    match = re.search(r"status: (\w+)", message)
    return match.group(1) if match else None


def _url_encode(value: str) -> str:
    """Percent-encode a single URL component."""
    return urllib.parse.quote(value, safe="")
