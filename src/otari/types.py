"""Configuration and type re-exports for the otari gateway client.

Re-exports the OpenAPI-generated response/chunk models from
:mod:`otari._client` so consumers can name them without reaching into the
generated package, plus the SDK's own batch/option types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

# ---------------------------------------------------------------------------
# Re-export the generated models that callers interact with directly.
# Explicit ``as`` aliases make these public re-exports per PEP 484.
# ---------------------------------------------------------------------------
from otari._client.models.chat_completion import ChatCompletion as ChatCompletion  # noqa: PLC0414
from otari._client.models.chat_completion_chunk import ChatCompletionChunk as ChatCompletionChunk  # noqa: PLC0414
from otari._client.models.create_embedding_response import (
    CreateEmbeddingResponse as CreateEmbeddingResponse,  # noqa: PLC0414
)
from otari._client.models.message_response import MessageResponse as MessageResponse  # noqa: PLC0414
from otari._client.models.model_object import ModelObject as ModelObject  # noqa: PLC0414
from otari._client.models.moderation_response import ModerationResponse as ModerationResponse  # noqa: PLC0414
from otari._client.models.rerank_response import RerankResponse as RerankResponse  # noqa: PLC0414

# ---------------------------------------------------------------------------
# Client options
# ---------------------------------------------------------------------------


class OtariClientOptions(TypedDict, total=False):
    """Options for constructing an :class:`~otari.client.OtariClient`.

    Auth resolution order (mirrors the TypeScript SDK / Python GatewayProvider):
      1. Explicit ``platform_token`` -> platform mode (Bearer in Authorization header)
      2. ``OTARI_AI_TOKEN`` (or legacy ``GATEWAY_PLATFORM_TOKEN``) env var
         (when no ``api_key``) -> platform mode
      3. ``api_key`` or ``GATEWAY_API_KEY`` env var -> non-platform mode (``Otari-Key`` header)
      4. No credentials -> non-platform mode, no auth header

    In platform mode, ``api_base`` defaults to the hosted gateway at
    ``https://api.otari.ai`` when neither the option nor ``GATEWAY_API_BASE``
    is set.
    """

    api_base: str
    """Base URL of the gateway (defaults to ``https://api.otari.ai`` in platform mode)."""

    api_key: str
    """API key for non-platform mode. Sent via ``Otari-Key: Bearer <key>``."""

    platform_token: str
    """Platform token for platform mode. Sent as Bearer in the Authorization header."""

    admin_key: str
    """Master/admin key for the control-plane endpoints."""

    default_headers: dict[str, str]
    """Additional default headers to send with every request."""


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
    result: dict[str, Any] | None = None
    error: BatchResultError | None = None


@dataclass
class BatchResult:
    """Aggregated results of a completed batch job."""

    results: list[BatchResultItem] = field(default_factory=list)
