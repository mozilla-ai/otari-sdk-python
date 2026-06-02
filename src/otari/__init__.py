"""otari - Python client for the otari gateway.

Example::

    from otari import OtariClient

    client = OtariClient(
        api_base="http://localhost:8000",
        platform_token="your-token-here",
    )

    response = await client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)
"""

from importlib.metadata import PackageNotFoundError, version

from otari.async_client import AsyncOtariClient
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
from otari.types import (
    AsyncStream,
    BatchRequestItem,
    BatchResult,
    BatchResultError,
    BatchResultItem,
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    CreateBatchParams,
    CreateEmbeddingResponse,
    EmbeddingCreateParams,
    ListBatchesOptions,
    Model,
    OtariClientOptions,
    Response,
    ResponseStreamEvent,
    Stream,
)

try:
    __version__ = version("otari")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"


__all__ = [
    "AsyncOtariClient",
    "AsyncStream",
    "AuthenticationError",
    "BatchNotCompleteError",
    "BatchRequestItem",
    "BatchResult",
    "BatchResultError",
    "BatchResultItem",
    "ChatCompletion",
    "ChatCompletionChunk",
    "ChatCompletionMessageParam",
    "CreateBatchParams",
    "CreateEmbeddingResponse",
    "EmbeddingCreateParams",
    "GatewayTimeoutError",
    "InsufficientFundsError",
    "ListBatchesOptions",
    "Model",
    "ModelNotFoundError",
    "OtariClient",
    "OtariClientOptions",
    "OtariError",
    "RateLimitError",
    "Response",
    "ResponseStreamEvent",
    "Stream",
    "UnsupportedCapabilityError",
    "UpstreamProviderError",
]
