"""otari - Python client for the otari gateway.

Example::

    from otari import OtariClient

    client = OtariClient(
        api_base="http://localhost:8000",
        platform_token="your-token-here",
    )

    response = client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)
"""

from importlib.metadata import PackageNotFoundError, version

from otari.async_client import AsyncOtariClient
from otari.client import OtariClient
from otari.control_plane import ControlPlane
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
    BatchRequestItem,
    BatchResult,
    BatchResultError,
    BatchResultItem,
    ChatCompletion,
    ChatCompletionChunk,
    CreateBatchParams,
    CreateEmbeddingResponse,
    ListBatchesOptions,
    MessageResponse,
    ModelObject,
    ModerationResponse,
    OtariClientOptions,
    RerankResponse,
)

try:
    __version__ = version("otari")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"


__all__ = [
    "AsyncOtariClient",
    "AuthenticationError",
    "BatchNotCompleteError",
    "BatchRequestItem",
    "BatchResult",
    "BatchResultError",
    "BatchResultItem",
    "ChatCompletion",
    "ChatCompletionChunk",
    "ControlPlane",
    "CreateBatchParams",
    "CreateEmbeddingResponse",
    "GatewayTimeoutError",
    "InsufficientFundsError",
    "ListBatchesOptions",
    "MessageResponse",
    "ModelNotFoundError",
    "ModelObject",
    "ModerationResponse",
    "OtariClient",
    "OtariClientOptions",
    "OtariError",
    "RateLimitError",
    "RerankResponse",
    "UnsupportedCapabilityError",
    "UpstreamProviderError",
]
