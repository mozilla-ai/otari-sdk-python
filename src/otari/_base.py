"""Shared logic for the sync and async otari gateway clients.

Holds everything that does not depend on whether the underlying transport is
synchronous or asynchronous: auth-mode resolution, base-URL normalization,
header building, and error mapping. The concrete clients
(:class:`~otari.client.OtariClient` and
:class:`~otari.async_client.AsyncOtariClient`) construct their own generated
``_client`` and httpx clients and implement the I/O methods on top of this base.

Option C: the inference path is a thin shell over the OpenAPI-generated core in
:mod:`otari._client` (typed models + per-endpoint API classes). The generated
``ApiException`` is the single error type all generated calls raise; this module
maps it to the typed otari exception hierarchy in :mod:`otari.errors`.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast

from otari._client.exceptions import ApiException
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
# Admin/master credential for the control-plane (management) endpoints.
_ENV_ADMIN_KEY = "GATEWAY_ADMIN_KEY"


class _BaseOtariClient:
    """Transport-agnostic base for the otari gateway clients.

    Subclasses are responsible for constructing the generated ``_client``
    ``ApiClient`` (seeded with the default headers assembled here) and an httpx
    client (``httpx.Client`` or ``httpx.AsyncClient``) for the SSE streaming
    shim, using the resolved configuration attributes set up here.
    """

    platform_mode: bool
    """Whether the client is operating in platform mode."""

    def __init__(
        self,
        api_base: str | None = None,
        *,
        api_key: str | None = None,
        platform_token: str | None = None,
        admin_key: str | None = None,
        default_headers: dict[str, str] | None = None,
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
        # The generated core's operation paths already include the ``/v1``
        # prefix, so the generated ``Configuration.host`` is the gateway root.
        self._gateway_root_url = api_base_url.removesuffix("/v1")

        headers: dict[str, str] = {**(default_headers or {})}

        # Auth resolution (same logic as TS SDK / Python GatewayProvider):
        # 1. Explicit platform_token -> platform mode (Bearer Authorization)
        # 2. OTARI_AI_TOKEN (or legacy GATEWAY_PLATFORM_TOKEN) env + no api_key
        #    option -> platform mode
        # 3. Otherwise -> non-platform mode (Otari-Key header)
        if resolved_platform_token and not api_key:
            self.platform_mode = True
            self._platform_token: str | None = resolved_platform_token
            self._api_key: str | None = None
            headers["Authorization"] = f"Bearer {resolved_platform_token}"
        else:
            self.platform_mode = False
            self._platform_token = None
            self._api_key = resolved_api_key or None
            if resolved_api_key:
                headers[GATEWAY_HEADER_NAME] = f"Bearer {resolved_api_key}"

        # Default headers fed into the generated ApiClient and the streaming
        # shim's httpx requests. Includes the auth header for the active mode.
        self._default_headers: dict[str, str] = headers

        # Control-plane (management) auth. Those endpoints expect
        # ``Authorization: Bearer <admin/master key>``, distinct from the
        # ``Otari-Key`` virtual key used for inference. In platform mode the
        # platform token already serves as that bearer; for a self-hosted
        # gateway the caller passes the master key as ``admin_key`` (or via
        # ``GATEWAY_ADMIN_KEY``).
        self._admin_token: str | None = (
            admin_key or os.environ.get(_ENV_ADMIN_KEY) or resolved_platform_token
        )

    # -- Error handling -----------------------------------------------------

    def _map_api_exception(self, error: ApiException) -> OtariError:
        """Map a generated ``ApiException`` to a typed otari exception.

        ``ApiException`` carries ``.status`` (int) and ``.body`` (the raw JSON
        string the gateway returned) plus ``.headers``. The gateway encodes the
        human-readable reason under the ``detail`` key (FastAPI convention).

        Most status mappings only apply in platform mode; in non-platform mode
        the generic :class:`OtariError` is raised so the caller still gets a
        single SDK exception type. The one cross-mode case is
        :class:`UnsupportedCapabilityError`, surfaced in both modes.
        """
        status = error.status if isinstance(error.status, int) else 0
        headers = error.headers or {}
        detail = self._extract_detail(error)
        correlation_id = _header_get(headers, "x-correlation-id")
        retry_after = _header_get(headers, "retry-after")

        full = f"{detail} (correlation_id={correlation_id})" if correlation_id else detail

        # Unsupported-capability is surfaced regardless of mode.
        if status == 400 and _UNSUPPORTED_MODERATION_RE.search(detail):
            provider = _parse_unsupported_provider(detail)
            capability = "multimodal_moderation" if "multimodal" in detail else "moderation"
            return UnsupportedCapabilityError(
                full,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
                provider=provider,
                capability=capability,
            )

        if status in (401, 403):
            return AuthenticationError(
                full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
            )
        if status == 402:
            return InsufficientFundsError(
                full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
            )
        if status == 404:
            return ModelNotFoundError(
                full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
            )
        if status == 409:
            return BatchNotCompleteError(
                full,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
                batch_id=_extract_batch_id(detail),
                batch_status=_extract_status(detail),
            )
        if status == 429:
            return RateLimitError(
                full,
                status_code=status,
                original_error=error,
                provider_name=PROVIDER_NAME,
                retry_after=retry_after,
            )
        if status == 504:
            return GatewayTimeoutError(
                full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
            )
        # 502 and any other 5xx are upstream-provider failures.
        if status == 502 or 500 <= status < 600:
            return UpstreamProviderError(
                full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
            )

        return OtariError(
            full, status_code=status, original_error=error, provider_name=PROVIDER_NAME
        )

    @staticmethod
    def _extract_detail(error: ApiException) -> str:
        """Pull the gateway's human-readable detail from an ``ApiException`` body."""
        body = error.body
        if isinstance(body, (bytes, bytearray)):
            body = body.decode("utf-8", "replace")
        if isinstance(body, str) and body:
            try:
                parsed = json.loads(body)
            except (ValueError, TypeError):
                return body
            if isinstance(parsed, dict):
                detail = parsed.get("detail") or parsed.get("message") or parsed.get("error")
                if isinstance(detail, str):
                    return detail
                if detail is not None:
                    return str(detail)
            return body
        return error.reason or "An error occurred"

    def _map_streaming_response(self, response: httpx.Response, body: bytes) -> OtariError:
        """Map a failed raw streaming response to a typed otari exception.

        The SSE shim issues raw httpx requests, so it never goes through the
        generated client and never raises ``ApiException``. To keep one mapping
        path, adapt the failed response into an ``ApiException`` and reuse
        :meth:`_map_api_exception`.
        """
        exc = ApiException(
            status=response.status_code,
            reason=response.reason_phrase,
            body=body.decode("utf-8", "replace"),
        )
        exc.headers = dict(response.headers)
        return self._map_api_exception(exc)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class _FromDict(Protocol):
    """Structural type for the generated request models' ``from_dict`` classmethod."""

    @classmethod
    def from_dict(cls, obj: dict[str, Any] | None) -> Any: ...


_M = TypeVar("_M", bound=_FromDict)


def build_request(model: type[_M], body: dict[str, Any]) -> _M:
    """Build a generated request model from ``body``, narrowing the ``Optional``.

    The generated ``from_dict`` is typed ``-> Optional[Self]`` (it returns ``None``
    only for ``None`` input); we always pass a real dict, so the result is never
    ``None``. This wrapper keeps that fact in one place instead of scattering
    ``# type: ignore`` across every ergonomic method.
    """
    return cast("_M", model.from_dict(body))


def _header_get(headers: Any, name: str) -> str | None:
    """Case-insensitively read a header from a dict or HTTPHeaderDict."""
    if headers is None:
        return None
    getter = getattr(headers, "get", None)
    if getter is not None:
        value = getter(name)
        if value is not None:
            return str(value)
    lowered = name.lower()
    try:
        for key, value in dict(headers).items():
            if str(key).lower() == lowered:
                return str(value)
    except (TypeError, ValueError):
        return None
    return None


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
