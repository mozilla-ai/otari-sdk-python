"""AsyncOtariClient: asynchronous Python client for the otari gateway.

Wraps the OpenAI Python SDK (``AsyncOpenAI``), adding gateway-specific auth
handling and error mapping for platform mode. Extracted from the
``GatewayProvider`` in `any-llm <https://github.com/mozilla-ai/any-llm>`_.

Example::

    from otari import AsyncOtariClient

    client = AsyncOtariClient(
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

from typing import TYPE_CHECKING, Any, overload

import httpx
from openai import AsyncOpenAI

from otari._base import _BaseOtariClient, _url_encode

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


class AsyncOtariClient(_BaseOtariClient):
    """Asynchronous client for the otari gateway.

    Supports two authentication modes (mirroring the TypeScript SDK and
    the Python ``GatewayProvider``):

    - **Platform mode**: A Bearer token is sent in the standard Authorization
      header. Errors are mapped to typed otari exceptions.
    - **Non-platform mode**: An API key is sent via a custom ``Otari-Key``
      header. Errors from the OpenAI SDK pass through unmodified.

    Args:
        api_base: Base URL of the gateway (e.g. ``"http://localhost:8000"``).
            Falls back to the ``GATEWAY_API_BASE`` environment variable. In
            platform mode it defaults to the hosted gateway at
            ``https://api.otari.ai`` when neither is supplied.
        api_key: API key for non-platform mode.
            Falls back to ``GATEWAY_API_KEY`` env var.
        platform_token: Platform token for platform mode.
            Falls back to the canonical ``OTARI_AI_TOKEN`` env var (or the
            legacy ``GATEWAY_PLATFORM_TOKEN`` alias).
        default_headers: Additional default headers to send with every request.
        openai_options: Extra keyword arguments forwarded to the underlying
            ``AsyncOpenAI`` constructor.

    Example::

        client = AsyncOtariClient(
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

    def __init__(
        self,
        api_base: str | None = None,
        *,
        api_key: str | None = None,
        platform_token: str | None = None,
        default_headers: dict[str, str] | None = None,
        openai_options: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            api_base,
            api_key=api_key,
            platform_token=platform_token,
            default_headers=default_headers,
            openai_options=openai_options,
        )
        self.openai = AsyncOpenAI(
            api_key=self._openai_api_key,
            base_url=self._openai_base_url,
            default_headers=self._openai_default_headers,
            **self._openai_extra_kwargs,
        )
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
            result: Response | AsyncStream[ResponseStreamEvent] = await self.openai.responses.create(**params)
        except Exception as exc:
            self._handle_error(exc)
            raise
        else:
            return result

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
        response = await self._http.request(
            method,
            url,
            headers=self._build_batch_headers(),
            json=body if body is not None else None,
        )

        if not response.is_success:
            self._map_batch_error(response)

        result: dict[str, Any] = response.json()
        return result

    # -- Cleanup ------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP clients."""
        await self._http.aclose()
        await self.openai.close()

    async def __aenter__(self) -> AsyncOtariClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
