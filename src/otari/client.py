"""OtariClient: synchronous Python client for the otari gateway.

A thin, ergonomic shell over the OpenAPI-generated core in
:mod:`otari._client`. Non-streaming calls go through the generated typed API
classes (returning typed models such as ``ChatCompletion``); streaming calls go
through the hand-written SSE shim in :mod:`otari._streaming`; generated
``ApiException``\\s are mapped to the typed errors in :mod:`otari.errors`.

For an asynchronous client, see :class:`~otari.async_client.AsyncOtariClient`.

Example::

    from otari import OtariClient

    client = OtariClient(
        api_base="http://localhost:8000",
        platform_token="tk_xxx",
    )

    response = client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, overload

import httpx

from otari._base import _BaseOtariClient, build_request
from otari._client import ApiClient, Configuration
from otari._client.api.batches_api import BatchesApi
from otari._client.api.chat_api import ChatApi
from otari._client.api.embeddings_api import EmbeddingsApi
from otari._client.api.images_api import ImagesApi
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
from otari._client.models.image_generation_request import ImageGenerationRequest
from otari._client.models.messages_request import MessagesRequest
from otari._client.models.moderation_request import ModerationRequest
from otari._client.models.rerank_request import RerankRequest
from otari._streaming import iter_sse
from otari.control_plane import ControlPlane
from otari.errors import OtariError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

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


class OtariClient(_BaseOtariClient):
    """Synchronous client for the otari gateway.

    Supports two authentication modes (mirroring the TypeScript SDK and the
    Python ``GatewayProvider``):

    - **Platform mode**: a Bearer token is sent in the standard ``Authorization``
      header (activated by ``platform_token`` / ``OTARI_AI_TOKEN``).
    - **Non-platform mode**: an API key is sent via the custom ``Otari-Key``
      header (``api_key`` / ``GATEWAY_API_KEY``).

    In both modes, gateway errors are mapped to the typed exceptions in
    :mod:`otari.errors`.

    Args:
        api_base: Base URL of the gateway (e.g. ``"http://localhost:8000"``).
            Falls back to ``GATEWAY_API_BASE``. In platform mode it defaults to
            the hosted gateway at ``https://api.otari.ai`` when neither is set.
        api_key: API key for non-platform mode. Falls back to ``GATEWAY_API_KEY``.
        platform_token: Platform token for platform mode. Falls back to the
            canonical ``OTARI_AI_TOKEN`` (or legacy ``GATEWAY_PLATFORM_TOKEN``).
        admin_key: Master/admin key for the control-plane endpoints. Falls back
            to ``GATEWAY_ADMIN_KEY`` (or the platform token in platform mode).
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
        # Raw httpx client used only for the SSE streaming shim (the generated
        # core buffers and cannot stream).
        self._http = httpx.Client(timeout=timeout)

        self._chat = ChatApi(self._api)
        self._responses = ResponsesApi(self._api)
        self._embeddings = EmbeddingsApi(self._api)
        self._moderations = ModerationsApi(self._api)
        self._rerank = RerankApi(self._api)
        self._messages = MessagesApi(self._api)
        self._models = ModelsApi(self._api)
        self._images = ImagesApi(self._api)
        self._batches = BatchesApi(self._api)

    @cached_property
    def control_plane(self) -> ControlPlane:
        """Typed client for the management endpoints (keys, users, budgets, pricing, usage).

        Requires an admin credential: pass ``admin_key`` (the gateway master key),
        set ``GATEWAY_ADMIN_KEY``, or use ``platform_token`` (which doubles as the
        control-plane bearer in platform mode).
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
    def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: None = ...,
        **kwargs: Any,
    ) -> ChatCompletion: ...

    @overload
    def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool,
        **kwargs: Any,
    ) -> ChatCompletion | Iterator[ChatCompletionChunk]: ...

    def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a chat completion.

        When ``stream=True``, returns an iterator of typed
        :class:`~otari._client.models.chat_completion_chunk.ChatCompletionChunk`.
        Otherwise returns a typed
        :class:`~otari._client.models.chat_completion.ChatCompletion`.

        Args:
            model: Model identifier (e.g. ``"openai:gpt-4o-mini"``).
            messages: List of message dicts with ``role`` and ``content``.
            stream: Whether to stream the response.
            **kwargs: Additional parameters modeled by the gateway chat schema
                (e.g. ``temperature``, ``tools``, ``guardrails``).
        """
        body = {"model": model, "messages": messages, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/chat/completions", body, "chat")
        request = build_request(ChatCompletionRequest, body)
        return self._call(lambda: self._chat.chat_completions_v1_chat_completions_post(request))

    # -- Responses API ------------------------------------------------------

    def response(
        self,
        *,
        model: str,
        input: Any,  # noqa: A002
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a response via the OpenAI-style Responses API.

        When ``stream=True``, returns an iterator of raw response-stream event
        dicts (the gateway's responses event stream has no single typed chunk
        model). Otherwise returns the parsed response object.
        """
        body = {"model": model, "input": input, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/responses", body, "responses")
        return self._call(lambda: self._responses.create_response_v1_responses_post(body))  # type: ignore[arg-type]

    # -- Messages API (Anthropic-shaped /messages) --------------------------

    def message(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        stream: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create an Anthropic-style message via the gateway ``/messages`` endpoint.

        This endpoint has no OpenAI-SDK seam and was previously missing from the
        SDK. When ``stream=True``, returns an iterator of raw message-stream
        event dicts (no single typed chunk model exists). Otherwise returns a
        typed :class:`~otari._client.models.message_response.MessageResponse`.

        Args:
            model: Model identifier (e.g. ``"anthropic:claude-3-5-sonnet"``).
            messages: Anthropic-style message list.
            max_tokens: Maximum tokens to generate (required by ``/messages``).
            stream: Whether to stream the response.
            **kwargs: Additional ``/messages`` parameters (``system``,
                ``temperature``, ``tools``, ``thinking``, ...).
        """
        body = {"model": model, "messages": messages, "max_tokens": max_tokens, **kwargs}
        if stream:
            body["stream"] = True
            return self._stream("/messages", body, "messages")
        request = build_request(MessagesRequest, body)
        return self._call(lambda: self._messages.create_message_v1_messages_post(request))

    def count_tokens(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> CountTokensResponse:
        """Count input tokens for an Anthropic-style message request.

        Calls the gateway ``/v1/messages/count_tokens`` endpoint, which counts
        the tokens a ``/messages`` request would consume without generating a
        response. Returns a typed
        :class:`~otari._client.models.count_tokens_response.CountTokensResponse`.

        Args:
            model: Model identifier (e.g. ``"anthropic:claude-3-5-sonnet"``).
            messages: Anthropic-style message list.
            **kwargs: Additional count-tokens parameters (``system``, ``tools``,
                ``tool_choice``, ``thinking``, ...).
        """
        request = build_request(CountTokensRequest, {"model": model, "messages": messages, **kwargs})
        result = self._call(
            lambda: self._messages.count_message_tokens_v1_messages_count_tokens_post(request),
        )
        return cast("CountTokensResponse", result)

    # -- Embeddings ---------------------------------------------------------

    def embedding(
        self,
        *,
        model: str,
        input: str | list[str],  # noqa: A002
        **kwargs: Any,
    ) -> CreateEmbeddingResponse:
        """Create embeddings for the given input."""
        request = build_request(EmbeddingRequest, {"model": model, "input": input, **kwargs})
        result = self._call(lambda: self._embeddings.create_embedding_v1_embeddings_post(request))
        return cast("CreateEmbeddingResponse", result)

    # -- Moderations --------------------------------------------------------

    def moderation(
        self,
        *,
        model: str,
        input: str | list[str],  # noqa: A002
        **kwargs: Any,
    ) -> ModerationResponse:
        """Classify text against the gateway moderation endpoint."""
        request = build_request(ModerationRequest, {"model": model, "input": input, **kwargs})
        result = self._call(lambda: self._moderations.create_moderation_v1_moderations_post(request))
        return cast("ModerationResponse", result)

    # -- Rerank -------------------------------------------------------------

    def rerank(
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
        result = self._call(lambda: self._rerank.create_rerank_v1_rerank_post(request))
        return cast("RerankResponse", result)

    # -- Images -------------------------------------------------------------

    def image_generation(
        self,
        *,
        model: str,
        prompt: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate images from a text prompt.

        Returns the gateway's OpenAI-compatible image payload as a dict
        (``{"created": ..., "data": [...]}``). The generated core models this
        response as an opaque object, so the parsed JSON is returned unchanged.

        Args:
            model: Model identifier (e.g. ``"openai:dall-e-3"``).
            prompt: Text prompt describing the desired image(s).
            **kwargs: Additional parameters (``n``, ``size``, ``quality``,
                ``response_format``, ``style``, ``user``).
        """
        request = build_request(
            ImageGenerationRequest, {"model": model, "prompt": prompt, **kwargs}
        )
        result = self._call(lambda: self._images.create_image_v1_images_generations_post(request))
        return cast("dict[str, Any]", result)

    # -- Audio --------------------------------------------------------------

    def speech(
        self,
        *,
        model: str,
        input: str,  # noqa: A002
        voice: str,
        **kwargs: Any,
    ) -> bytes:
        """Synthesize speech (text-to-speech), returning raw audio bytes.

        The gateway returns binary audio (``audio/mpeg`` by default) with no
        JSON response model, so this posts over httpx and returns the raw
        ``bytes``.

        Args:
            model: Model identifier (e.g. ``"openai:tts-1"``).
            input: Text to synthesize.
            voice: Voice to use (e.g. ``"alloy"``).
            **kwargs: Additional parameters (``response_format``, ``speed``,
                ``instructions``, ``user``).
        """
        body = {"model": model, "input": input, "voice": voice, **kwargs}
        response = self._post("/audio/speech", json=body)
        return response.content

    def transcription(
        self,
        *,
        model: str,
        file: bytes,
        filename: str = "audio",
        **kwargs: Any,
    ) -> Any:
        """Transcribe audio to text.

        ``file`` is the raw audio bytes uploaded as multipart form data. Returns
        the parsed JSON (a dict) for JSON response formats, or the raw text for
        ``text`` / ``srt`` / ``vtt`` formats.

        Args:
            model: Model identifier (e.g. ``"openai:whisper-1"``).
            file: Raw audio bytes to transcribe.
            filename: Filename for the multipart upload (some providers infer
                the audio format from its extension).
            **kwargs: Additional parameters (``language``, ``prompt``,
                ``response_format``, ``temperature``, ``user``).
        """
        data = {"model": model, **{key: str(value) for key, value in kwargs.items()}}
        files = {"file": (filename, file)}
        response = self._post("/audio/transcriptions", data=data, files=files)
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return response.text

    # -- Models -------------------------------------------------------------

    def list_models(self) -> list[ModelObject]:
        """List available models from the gateway."""
        result = self._call(self._models.list_models_v1_models_get)
        return list(result.data)

    # -- Batch operations ---------------------------------------------------

    def create_batch(self, params: CreateBatchParams) -> Any:
        """Create a batch job."""
        request = build_request(CreateBatchRequest, dict(params))
        return self._call(lambda: self._batches.create_batch_v1_batches_post(request))

    def retrieve_batch(self, batch_id: str, provider: str) -> Any:
        """Retrieve the status of a batch job."""
        return self._call(
            lambda: self._batches.retrieve_batch_v1_batches_batch_id_get(batch_id, provider)
        )

    def cancel_batch(self, batch_id: str, provider: str) -> Any:
        """Cancel a batch job."""
        return self._call(
            lambda: self._batches.cancel_batch_v1_batches_batch_id_cancel_post(batch_id, provider)
        )

    def list_batches(
        self,
        provider: str,
        options: ListBatchesOptions | None = None,
    ) -> list[Any]:
        """List batch jobs for a provider."""
        options = options or {}
        result = self._call(
            lambda: self._batches.list_batches_v1_batches_get(
                provider,
                after=options.get("after"),
                limit=options.get("limit"),
            )
        )
        data = result.get("data", []) if isinstance(result, dict) else []
        return list(data)

    def retrieve_batch_results(self, batch_id: str, provider: str) -> BatchResult:
        """Retrieve the results of a completed batch job.

        Raises:
            BatchNotCompleteError: If the batch is not yet complete (HTTP 409).
        """
        from otari.types import BatchResult as BatchResultType  # noqa: PLC0415
        from otari.types import BatchResultItem  # noqa: PLC0415

        data = self._call(
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

    def _call(self, fn: Callable[[], Any]) -> Any:
        """Run a generated call, mapping its ``ApiException`` to a typed error."""
        try:
            return fn()
        except ApiException as exc:
            raise self._map_api_exception(exc) from exc

    def _post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Issue a non-streaming raw httpx POST, mapping error responses.

        Audio endpoints (binary speech, multipart transcription) do not fit the
        generated JSON core, so they post directly over httpx and reuse the same
        error mapping as the streaming shim.
        """
        url = f"{self._base_url}{path}"
        response = self._http.post(
            url, headers=self._default_headers, json=json, data=data, files=files
        )
        if response.status_code >= 400:
            raise self._map_streaming_response(response, response.content)
        return response

    def _stream(self, path: str, body: dict[str, Any], kind: Any) -> Iterator[Any]:
        """Open a raw streaming POST and yield parsed SSE chunks.

        The generated core buffers responses, so streaming is hand-written here:
        a raw httpx streaming request parsed by :mod:`otari._streaming`.
        """
        url = f"{self._base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            **self._default_headers,
        }
        with self._http.stream("POST", url, json=body, headers=headers) as response:
            if response.status_code >= 400:
                raw = response.read()
                raise self._map_streaming_response(response, raw)
            yield from iter_sse(response, kind)

    # -- Cleanup ------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP clients."""
        self._http.close()
        cast("Any", self._api).__exit__(None, None, None)

    def __enter__(self) -> OtariClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
