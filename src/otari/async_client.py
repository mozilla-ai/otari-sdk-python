"""AsyncOtariClient: asynchronous Python client for the otari gateway.

A thin async shell over the OpenAPI-generated core in
:mod:`otari._client`. The generated core is synchronous (urllib3-based), so
non-streaming calls are dispatched to a worker thread via ``asyncio.to_thread``;
streaming is natively async over ``httpx.AsyncClient`` and the SSE shim in
:mod:`otari._streaming`. Generated ``ApiException``\\s are mapped to the typed
errors in :mod:`otari.errors`.

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

import asyncio
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, overload

import httpx

from otari._base import _BaseOtariClient, build_request
from otari._client import ApiClient, Configuration
from otari._client.api.batches_api import BatchesApi
from otari._client.api.chat_api import ChatApi
from otari._client.api.embeddings_api import EmbeddingsApi
from otari._client.api.messages_api import MessagesApi
from otari._client.api.models_api import ModelsApi
from otari._client.api.moderations_api import ModerationsApi
from otari._client.api.rerank_api import RerankApi
from otari._client.api.responses_api import ResponsesApi
from otari._client.exceptions import ApiException
from otari._client.models.chat_completion_request import ChatCompletionRequest
from otari._client.models.count_tokens_request import CountTokensRequest
from otari._client.models.create_batch_request import CreateBatchRequest
from otari._client.models.embedding_request import EmbeddingRequest
from otari._client.models.messages_request import MessagesRequest
from otari._client.models.moderation_request import ModerationRequest
from otari._client.models.rerank_request import RerankRequest
from otari._streaming import aiter_sse
from otari.control_plane import ControlPlane
from otari.errors import OtariError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from otari._client.models.chat_completion import ChatCompletion
    from otari._client.models.chat_completion_chunk import ChatCompletionChunk
    from otari._client.models.count_tokens_response import CountTokensResponse
    from otari._client.models.create_embedding_response import CreateEmbeddingResponse
    from otari._client.models.model_object import ModelObject
    from otari._client.models.moderation_response import ModerationResponse
    from otari._client.models.rerank_response import RerankResponse
    from otari.types import (
        BatchResult,
        CreateBatchParams,
        ListBatchesOptions,
    )


class AsyncOtariClient(_BaseOtariClient):
    """Asynchronous client for the otari gateway.

    Supports the same two authentication modes as
    :class:`~otari.client.OtariClient`:

    - **Platform mode**: Bearer token in the ``Authorization`` header.
    - **Non-platform mode**: API key in the custom ``Otari-Key`` header.

    The generated core is synchronous; non-streaming calls run in a worker
    thread (``asyncio.to_thread``) while streaming is natively async.

    Args:
        api_base: Base URL of the gateway. Falls back to ``GATEWAY_API_BASE``;
            in platform mode defaults to ``https://api.otari.ai``.
        api_key: API key for non-platform mode (``GATEWAY_API_KEY``).
        platform_token: Platform token (``OTARI_AI_TOKEN`` / legacy
            ``GATEWAY_PLATFORM_TOKEN``).
        admin_key: Master/admin key for the control-plane (``GATEWAY_ADMIN_KEY``).
        default_headers: Additional default headers sent with every request.
        timeout: Per-request timeout (seconds) for the streaming shim.
    """

    def __init__(
        self,
        api_base: str | None = None,
        *,
        api_key: str | None = None,
        platform_token: str | None = None,
        admin_key: str | None = None,
        default_headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(
            api_base,
            api_key=api_key,
            platform_token=platform_token,
            admin_key=admin_key,
            default_headers=default_headers,
        )
        self._timeout = timeout
        config = Configuration(host=self._gateway_root_url)
        self._api = ApiClient(config)
        # set_default_header is generated (untyped); seed the per-mode auth header.
        api_any = cast("Any", self._api)
        for name, value in self._default_headers.items():
            api_any.set_default_header(name, value)
        self._http = httpx.AsyncClient(timeout=timeout)

        self._chat = ChatApi(self._api)
        self._responses = ResponsesApi(self._api)
        self._embeddings = EmbeddingsApi(self._api)
        self._moderations = ModerationsApi(self._api)
        self._rerank = RerankApi(self._api)
        self._messages = MessagesApi(self._api)
        self._models = ModelsApi(self._api)
        self._batches = BatchesApi(self._api)

    @cached_property
    def control_plane(self) -> ControlPlane:
        """Typed client for the management endpoints (keys, users, budgets, pricing, usage).

        Requires an admin credential: pass ``admin_key`` (the gateway master key),
        set ``GATEWAY_ADMIN_KEY``, or use ``platform_token``.
        """
        if not self._admin_token:
            msg = (
                "control-plane management requires an admin credential; pass "
                "admin_key=... (the gateway master key) or use platform_token=..."
            )
            raise OtariError(msg)
        return ControlPlane(self._gateway_root_url, self._admin_token)

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
        stream: bool,
        **kwargs: Any,
    ) -> ChatCompletion | AsyncIterator[ChatCompletionChunk]: ...

    async def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a chat completion.

        When ``stream=True``, returns an async iterator of typed
        ``ChatCompletionChunk``; otherwise a typed ``ChatCompletion``.
        """
        body = {"model": model, "messages": messages, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/chat/completions", body, "chat")
        request = build_request(ChatCompletionRequest, body)
        return await self._call(
            lambda: self._chat.chat_completions_v1_chat_completions_post(request)
        )

    # -- Responses API ------------------------------------------------------

    async def response(
        self,
        *,
        model: str,
        input: Any,  # noqa: A002
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a response via the OpenAI-style Responses API.

        When ``stream=True``, returns an async iterator of raw event dicts;
        otherwise the parsed response object.
        """
        body = {"model": model, "input": input, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/responses", body, "responses")
        return await self._call(
            lambda: self._responses.create_response_v1_responses_post(body)  # type: ignore[arg-type]
        )

    # -- Messages API (Anthropic-shaped /messages) --------------------------

    async def message(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create an Anthropic-style message via the gateway ``/messages`` endpoint.

        When ``stream=True``, returns an async iterator of raw event dicts;
        otherwise a typed ``MessageResponse``.
        """
        body = {"model": model, "messages": messages, "max_tokens": max_tokens, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/messages", body, "messages")
        request = build_request(MessagesRequest, body)
        return await self._call(lambda: self._messages.create_message_v1_messages_post(request))

    async def count_tokens(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> CountTokensResponse:
        """Count input tokens for an Anthropic-style message request.

        Calls the gateway ``/v1/messages/count_tokens`` endpoint, which counts
        the tokens a ``/messages`` request would consume without generating a
        response. Returns a typed ``CountTokensResponse``.
        """
        request = build_request(CountTokensRequest, {"model": model, "messages": messages, **kwargs})
        result = await self._call(
            lambda: self._messages.count_message_tokens_v1_messages_count_tokens_post(request)
        )
        return cast("CountTokensResponse", result)

    # -- Embeddings ---------------------------------------------------------

    async def embedding(
        self,
        *,
        model: str,
        input: str | list[str],  # noqa: A002
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        """Create embeddings for the given input."""
        request = build_request(EmbeddingRequest, {"model": model, "input": input, **kwargs})
        result = await self._call(
            lambda: self._embeddings.create_embedding_v1_embeddings_post(request)
        )
        return cast("CreateEmbeddingResponse", result)

    # -- Moderations --------------------------------------------------------

    async def moderation(
        self,
        *,
        model: str,
        input: str | list[str],  # noqa: A002
        **kwargs: Any,
    ) -> ModerationResponse:
        """Classify text against the gateway moderation endpoint."""
        request = build_request(ModerationRequest, {"model": model, "input": input, **kwargs})
        result = await self._call(
            lambda: self._moderations.create_moderation_v1_moderations_post(request)
        )
        return cast("ModerationResponse", result)

    # -- Rerank -------------------------------------------------------------

    async def rerank(
        self,
        *,
        model: str,
        query: str,
        documents: list[str],
        **kwargs: Any,
    ) -> RerankResponse:
        """Rerank ``documents`` by relevance to ``query``."""
        request = build_request(
            RerankRequest, {"model": model, "query": query, "documents": documents, **kwargs}
        )
        result = await self._call(lambda: self._rerank.create_rerank_v1_rerank_post(request))
        return cast("RerankResponse", result)

    # -- Models -------------------------------------------------------------

    async def list_models(self) -> list[ModelObject]:
        """List available models from the gateway."""
        result = await self._call(self._models.list_models_v1_models_get)
        return list(result.data)

    # -- Batch operations ---------------------------------------------------

    async def create_batch(self, params: CreateBatchParams) -> Any:
        """Create a batch job."""
        request = build_request(CreateBatchRequest, dict(params))
        return await self._call(lambda: self._batches.create_batch_v1_batches_post(request))

    async def retrieve_batch(self, batch_id: str, provider: str) -> Any:
        """Retrieve the status of a batch job."""
        return await self._call(
            lambda: self._batches.retrieve_batch_v1_batches_batch_id_get(batch_id, provider)
        )

    async def cancel_batch(self, batch_id: str, provider: str) -> Any:
        """Cancel a batch job."""
        return await self._call(
            lambda: self._batches.cancel_batch_v1_batches_batch_id_cancel_post(batch_id, provider)
        )

    async def list_batches(
        self,
        provider: str,
        options: ListBatchesOptions | None = None,
    ) -> list[Any]:
        """List batch jobs for a provider."""
        options = options or {}
        result = await self._call(
            lambda: self._batches.list_batches_v1_batches_get(
                provider,
                after=options.get("after"),
                limit=options.get("limit"),
            )
        )
        data = result.get("data", []) if isinstance(result, dict) else []
        return list(data)

    async def retrieve_batch_results(self, batch_id: str, provider: str) -> BatchResult:
        """Retrieve the results of a completed batch job.

        Raises:
            BatchNotCompleteError: If the batch is not yet complete (HTTP 409).
        """
        from otari.types import BatchResult as BatchResultType  # noqa: PLC0415
        from otari.types import BatchResultItem  # noqa: PLC0415

        data = await self._call(
            lambda: self._batches.retrieve_batch_results_v1_batches_batch_id_results_get(
                batch_id, provider
            )
        )
        results = data.get("results", []) if isinstance(data, dict) else []
        items = [
            BatchResultItem(
                custom_id=entry["custom_id"],
                result=entry.get("result"),
                error=entry.get("error"),
            )
            for entry in results
        ]
        return BatchResultType(results=items)

    # -- Internal helpers ---------------------------------------------------

    async def _call(self, fn: Callable[[], Any]) -> Any:
        """Run a synchronous generated call off-thread, mapping its errors."""
        try:
            return await asyncio.to_thread(fn)
        except ApiException as exc:
            raise self._map_api_exception(exc) from exc

    async def _stream(self, path: str, body: dict[str, Any], kind: Any) -> AsyncIterator[Any]:
        """Open a raw async streaming POST and yield parsed SSE chunks."""
        url = f"{self._base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            **self._default_headers,
        }
        async with self._http.stream("POST", url, json=body, headers=headers) as response:
            if response.status_code >= 400:
                raw = await response.aread()
                raise self._map_streaming_response(response, raw)
            async for chunk in aiter_sse(response, kind):
                yield chunk

    # -- Cleanup ------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP clients."""
        await self._http.aclose()
        await asyncio.to_thread(cast("Any", self._api).__exit__, None, None, None)

    async def __aenter__(self) -> AsyncOtariClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
