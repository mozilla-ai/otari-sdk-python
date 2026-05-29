"""Configuration and type re-exports for the otari gateway client.

Re-exports OpenAI SDK types so consumers don't need to import ``openai`` directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

# ---------------------------------------------------------------------------
# Re-export OpenAI types that callers interact with directly.
# These use explicit `as` aliases to make the re-exports public per PEP 484.
# The TC002 / PLC0414 warnings are intentionally suppressed because these
# imports exist solely for re-export.
# ---------------------------------------------------------------------------
from openai import Stream as Stream  # noqa: PLC0414
from openai.types import CreateEmbeddingResponse as CreateEmbeddingResponse  # noqa: PLC0414
from openai.types import EmbeddingCreateParams as EmbeddingCreateParams  # noqa: PLC0414
from openai.types import Model as Model  # noqa: PLC0414
from openai.types.chat import ChatCompletion as ChatCompletion  # noqa: PLC0414, TC002
from openai.types.chat import ChatCompletionChunk as ChatCompletionChunk  # noqa: PLC0414
from openai.types.chat import ChatCompletionMessageParam as ChatCompletionMessageParam  # noqa: PLC0414
from openai.types.responses import Response as Response  # noqa: PLC0414
from openai.types.responses import ResponseStreamEvent as ResponseStreamEvent  # noqa: PLC0414

# ---------------------------------------------------------------------------
# Client options
# ---------------------------------------------------------------------------


class OtariClientOptions(TypedDict, total=False):
    """Options for constructing an :class:`~otari.client.OtariClient`.

    Auth resolution order (mirrors the TypeScript SDK / Python GatewayProvider):
      1. Explicit ``platform_token`` -> platform mode (Bearer token in Authorization header)
      2. ``OTARI_AI_TOKEN`` (or legacy ``GATEWAY_PLATFORM_TOKEN``) env var
         (when no ``api_key``) -> platform mode
      3. ``api_key`` or ``GATEWAY_API_KEY`` env var -> non-platform mode (``Otari-Key`` header)
      4. No credentials -> non-platform mode, no auth header

    In platform mode, ``api_base`` defaults to the hosted gateway at
    ``https://api.otari.ai`` when neither the option nor ``GATEWAY_API_BASE``
    is set.
    """

    api_base: str
    """Base URL of the gateway (e.g. ``"http://localhost:8000"``).

    Defaults to ``https://api.otari.ai`` in platform mode."""

    api_key: str
    """API key for non-platform mode. Sent via ``Otari-Key: Bearer <key>``."""

    platform_token: str
    """Platform token for platform mode. Sent as Bearer in the Authorization header.

    Falls back to ``OTARI_AI_TOKEN`` (or legacy ``GATEWAY_PLATFORM_TOKEN``)."""

    default_headers: dict[str, str]
    """Additional default headers to send with every request."""

    openai_options: dict[str, Any]
    """Extra options forwarded to the underlying ``AsyncOpenAI`` constructor."""


# ---------------------------------------------------------------------------
# Batch types
# ---------------------------------------------------------------------------


class BatchRequestItem(TypedDict):
    """A single request within a batch."""

    custom_id: str
    body: dict[str, Any]


class CreateBatchParams(TypedDict, total=False):
    """Parameters for creating a batch job."""

    model: str
    requests: list[BatchRequestItem]
    completion_window: str
    metadata: dict[str, str]


class ListBatchesOptions(TypedDict, total=False):
    """Pagination options for listing batches."""

    after: str
    limit: int


class BatchResultError(TypedDict):
    """Error information for a failed batch request."""

    code: str
    message: str


@dataclass
class BatchResultItem:
    """Result of a single request within a batch."""

    custom_id: str
    result: ChatCompletion | None = None
    error: BatchResultError | None = None


@dataclass
class BatchResult:
    """Aggregated results of a completed batch job."""

    results: list[BatchResultItem] = field(default_factory=list)
