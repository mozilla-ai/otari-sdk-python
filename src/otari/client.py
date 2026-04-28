"""OtariClient: Python client for the otari gateway.

Wraps the OpenAI Python SDK (``AsyncOpenAI``), adding gateway-specific
auth handling and error mapping for platform mode. Extracted from the
``GatewayProvider`` in `any-llm <https://github.com/mozilla-ai/any-llm>`_.

Example::

    from otari import OtariClient

    client = OtariClient(
        api_base="http://localhost:8000",
        platform_token="tk_xxx",
    )

    response = await client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)
"""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import TYPE_CHECKING, Any, overload

import httpx
import openai
from openai import AsyncOpenAI

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
    from openai import AsyncStream
    from openai.types import CreateEmbeddingResponse, Model
    from openai.types.chat import (
        ChatCompletion,
        ChatCompletionChunk,
    )
    from openai.types.responses import (
        Response,
        ResponseStreamEvent,
    )

    from otari.types import (
        BatchResult,
        CreateBatchParams,
        ListBatchesOptions,
    )

PROVIDER_NAME = "gateway"
GATEWAY_HEADER_NAME = "Otari-Key"

# Locked phrasing used by the gateway to signal that the selected
# provider does not support a moderation request.
_UNSUPPORTED_MODERATION_RE = re.compile(r"does not support (?:multimodal )?moderation")

_ENV_API_BASE = "GATEWAY_API_BASE"
_ENV_API_KEY = "GATEWAY_API_KEY"
_ENV_PLATFORM_TOKEN = "GATEWAY_PLATFORM_TOKEN"  # noqa: S105

_STATUS_TO_ERROR: dict[int, type[AuthenticationError] | type[ModelNotFoundError]] = {
    401: AuthenticationError,
    403: AuthenticationError,
    404: ModelNotFoundError,
}


class OtariClient:
    """Client for the otari gateway.

    Supports two authentication modes (mirroring the TypeScript SDK and
    the Python ``GatewayProvider``):

    - **Platform mode**: A Bearer token is sent in the standard Authorization
      header. Errors are mapped to typed otari exceptions.
    - **Non-platform mode**: An API key is sent via a custom ``Otari-Key``
      header. Errors from the OpenAI SDK pass through unmodified.

    Args:
        api_base: Base URL of the gateway (e.g. ``"http://localhost:8000"``).
            Falls back to the ``GATEWAY_API_BASE`` environment variable.
        api_key: API key for non-platform mode.
            Falls back to ``GATEWAY_API_KEY`` env var.
        platform_token: Platform token for platform mode.
            Falls back to ``GATEWAY_PLATFORM_TOKEN`` env var.
        default_headers: Additional default headers to send with every request.
        openai_options: Extra keyword arguments forwarded to the underlying
            ``AsyncOpenAI`` constructor.

    Example::

        client = OtariClient(
            api_base="http://localhost:8000",
            platform_token="tk_xxx",
        )

        response = await client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)
    """

    openai: AsyncOpenAI
    """The underlying OpenAI client instance."""

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
        raw_base = api_base or os.environ.get(_ENV_API_BASE)

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

        resolved_platform_token = platform_token or os.environ.get(_ENV_PLATFORM_TOKEN)
        resolved_api_key = api_key or os.environ.get(_ENV_API_KEY, "")

        headers: dict[str, str] = {**(default_headers or {})}
        extra_kwargs: dict[str, Any] = {**(openai_options or {})}

        # Auth resolution (same logic as TS SDK / Python GatewayProvider):
        # 1. Explicit platform_token -> platform mode
        # 2. GATEWAY_PLATFORM_TOKEN env + no api_key option -> platform mode
        # 3. Otherwise -> non-platform mode
        if resolved_platform_token and not api_key:
            self.platform_mode = True
            self._platform_token: str | None = resolved_platform_token
            self._api_key: str | None = None
            self.openai = AsyncOpenAI(
                api_key=resolved_platform_token,
                base_url=api_base_url,
                default_headers=headers or None,
                **extra_kwargs,
            )
        else:
            self.platform_mode = False
            self._platform_token = None
            self._api_key = resolved_api_key or None
            if resolved_api_key:
                headers[GATEWAY_HEADER_NAME] = f"Bearer {resolved_api_key}"
            # In non-platform mode we still need to pass *some* API key to the
            # OpenAI client (it validates the field).
            self.openai = AsyncOpenAI(
                api_key=resolved_api_key or "unused",
                base_url=api_base_url,
                default_headers=headers or None,
                **extra_kwargs,
            )

        # Store auth headers for batch/raw HTTP calls.
        self._auth_headers: dict[str, str] = {}
        if resolved_platform_token and not api_key:
            self._auth_headers["Authorization"] = f"Bearer {resolved_platform_token}"
        elif resolved_api_key:
            self._auth_headers[GATEWAY_HEADER_NAME] = f"Bearer {resolved_api_key}"
        if default_headers:
            self._auth_headers.update(default_headers)

        # httpx client for raw HTTP calls (batch, etc.)
        self._http = httpx.AsyncClient()

    # -- Chat completions ---------------------------------------------------

    @overload
    async def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: None = ...,
        **kwargs: Any,
    ) -> ChatCompletion: ...

    @overload
    async def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool = ...,
        **kwargs: Any,
    ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]: ...

    async def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a chat completion.

        When ``stream=True`` is set, returns an async iterable of chunks.

        Args:
            model: Model identifier (e.g. ``"openai:gpt-4o-mini"``).
            messages: List of message dicts with ``role`` and ``content``.
            stream: Whether to stream the response.
            **kwargs: Additional parameters forwarded to the OpenAI API.

        Returns:
            A ``ChatCompletion`` or an async stream of ``ChatCompletionChunk``.
        """
        try:
            params: dict[str, Any] = {"model": model, "messages": messages, **kwargs}
            if stream is not None:
                params["stream"] = stream
            return await self.openai.chat.completions.create(**params)
        except Exception as exc:
            self._handle_error(exc)
            raise

    # -- Responses API ------------------------------------------------------

    async def response(
        self,
        *,
        model: str,
        input: Any,  # noqa: A002
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Response | AsyncStream[ResponseStreamEvent]:
        """Create a response using the OpenAI Responses API.

        Args:
            model: Model identifier (e.g. ``"openai:gpt-4o-mini"``).
            input: The input for the response.
            stream: Whether to stream the response.
            **kwargs: Additional parameters forwarded to the OpenAI API.

        Returns:
            A ``Response`` or an async stream of ``ResponseStreamEvent``.
        """
        try:
            params: dict[str, Any] = {"model": model, "input": input, **kwargs}
            if stream is not None:
                params["stream"] = stream
            return await self.openai.responses.create(**params)
        except Exception as exc:
            self._handle_error(exc)
            raise

    # -- Embeddings ---------------------------------------------------------

    async def embedding(
        self,
        *,
        model: str,
        input: str | list[str],  # noqa: A002
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        """Create embeddings for the given input.

        Args:
            model: Model identifier (e.g. ``"openai:text-embedding-3-small"``).
            input: Text or list of texts to embed.
            **kwargs: Additional parameters forwarded to the OpenAI API.

        Returns:
            An ``CreateEmbeddingResponse``.
        """
        try:
            return await self.openai.embeddings.create(model=model, input=input, **kwargs)
        except Exception as exc:
            self._handle_error(exc)
            raise

    # -- Models -------------------------------------------------------------

    async def list_models(self) -> list[Model]:
        """List available models from the gateway.

        Returns:
            A list of ``Model`` objects.
        """
        try:
            page = await self.openai.models.list()
        except Exception as exc:
            self._handle_error(exc)
            raise
        else:
            return [model async for model in page]

    # -- Batch operations ---------------------------------------------------

    async def create_batch(self, params: CreateBatchParams) -> dict[str, Any]:
        """Create a batch job.

        Args:
            params: Batch creation parameters including model and requests array.

        Returns:
            The created batch object.
        """
        return await self._batch_request("POST", "/batches", body=dict(params))

    async def retrieve_batch(self, batch_id: str, provider: str) -> dict[str, Any]:
        """Retrieve the status of a batch job.

        Args:
            batch_id: The ID of the batch to retrieve.
            provider: The provider name (e.g. ``"openai"``).

        Returns:
            The batch object with current status.
        """
        encoded_id = httpx.URL(f"/batches/{batch_id}").raw_path.decode()
        return await self._batch_request(
            "GET",
            f"{encoded_id}?provider={_url_encode(provider)}",
        )

    async def cancel_batch(self, batch_id: str, provider: str) -> dict[str, Any]:
        """Cancel a batch job.

        Args:
            batch_id: The ID of the batch to cancel.
            provider: The provider name (e.g. ``"openai"``).

        Returns:
            The batch object with updated status.
        """
        encoded_id = httpx.URL(f"/batches/{batch_id}").raw_path.decode()
        return await self._batch_request(
            "POST",
            f"{encoded_id}/cancel?provider={_url_encode(provider)}",
        )

    async def list_batches(
        self,
        provider: str,
        options: ListBatchesOptions | None = None,
    ) -> list[dict[str, Any]]:
        """List batch jobs for a provider.

        Args:
            provider: The provider name (e.g. ``"openai"``).
            options: Optional pagination parameters.

        Returns:
            List of batch objects.
        """
        params_parts = [f"provider={_url_encode(provider)}"]
        if options:
            if "after" in options:
                params_parts.append(f"after={_url_encode(options['after'])}")
            if "limit" in options:
                params_parts.append(f"limit={options['limit']}")
        query = "&".join(params_parts)
        response = await self._batch_request("GET", f"/batches?{query}")
        data: list[dict[str, Any]] = response.get("data", [])
        return data

    async def retrieve_batch_results(
        self,
        batch_id: str,
        provider: str,
    ) -> BatchResult:
        """Retrieve the results of a completed batch job.

        Args:
            batch_id: The ID of the batch.
            provider: The provider name (e.g. ``"openai"``).

        Returns:
            The batch results containing per-request outcomes.

        Raises:
            BatchNotCompleteError: If the batch is not yet complete.
        """
        from otari.types import BatchResult as BatchResultType  # noqa: PLC0415
        from otari.types import BatchResultItem  # noqa: PLC0415

        encoded_id = httpx.URL(f"/batches/{batch_id}").raw_path.decode()
        data = await self._batch_request(
            "GET",
            f"{encoded_id}/results?provider={_url_encode(provider)}",
        )
        items = [
            BatchResultItem(
                custom_id=entry["custom_id"],
                result=entry.get("result"),
                error=entry.get("error"),
            )
            for entry in data.get("results", [])
        ]
        return BatchResultType(results=items)

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

    # -- Batch HTTP helpers -------------------------------------------------

    async def _batch_request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a direct HTTP request for batch operations.

        Unlike completion/embedding which use ``self.openai``, batch methods
        use direct HTTP because the gateway batch API has a custom JSON format.
        """
        url = f"{self._base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            **self._auth_headers,
        }

        response = await self._http.request(
            method,
            url,
            headers=headers,
            json=body if body is not None else None,
        )

        if not response.is_success:
            await self._handle_batch_error(response)

        return response.json()

    async def _handle_batch_error(self, response: httpx.Response) -> None:
        """Map batch HTTP errors to typed SDK errors."""
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

    # -- Cleanup ------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP clients."""
        await self._http.aclose()
        await self.openai.close()

    async def __aenter__(self) -> OtariClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


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
