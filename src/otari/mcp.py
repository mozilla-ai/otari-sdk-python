"""Caller-controlled MCP, using generated models but a single-attempt transport.

The generated urllib3 client inherits connection retries unless overridden.
Use the client's HTTPX transport instead: zero connection retries, no status
retries, no redirects, and no inference error mapping (a 409 here is not a
batch error). The owning Otari client closes this shared transport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import httpx

from otari._base import build_request
from otari.errors import MCPError, MCPOutcomeUnknownError
from otari.types import CallToolResult, McpErrorBody, McpExecuteRequest, McpToolsResponse

if TYPE_CHECKING:
    from otari.async_client import AsyncOtariClient
    from otari.client import OtariClient


def _unknown_response(response: httpx.Response | None = None) -> MCPOutcomeUnknownError:
    # Never include raw response/exception text, which may contain call data.
    return MCPOutcomeUnknownError(
        "MCP execution outcome is unknown; the remote tool may already have run",
        execution_state="outcome_unknown",
        status_code=response.status_code if response is not None else None,
        request_id=response.headers.get("X-Otari-Request-ID") if response is not None else None,
    )


def _check_response(response: httpx.Response, *, executing: bool) -> None:
    if response.status_code == 200:
        return
    try:
        body = McpErrorBody.model_validate(response.json())
    except ValueError:
        if executing:
            raise _unknown_response(response) from None
        raise MCPError(
            "MCP discovery failed without a typed gateway response",
            execution_state="not_started",
            status_code=response.status_code,
            request_id=response.headers.get("X-Otari-Request-ID"),
        ) from None
    error_type = MCPOutcomeUnknownError if body.execution_state == "outcome_unknown" else MCPError
    raise error_type(
        body.detail,
        code=body.code,
        execution_state=body.execution_state.value,
        request_id=body.request_id,
        status_code=response.status_code,
        retry_after=response.headers.get("Retry-After"),
    )


def _execution_body(
    mcp_server_id: str | UUID,
    tool_name: str,
    arguments: dict[str, Any],
    server_revision: str,
    client_execution_id: str | UUID,
) -> dict[str, Any]:
    request = build_request(McpExecuteRequest, {
        "mcp_server_id": mcp_server_id,
        "tool_name": tool_name,
        "arguments": arguments,
        "server_revision": server_revision,
        "client_execution_id": client_execution_id,
    })
    # JSON mode serializes UUIDs; do not exclude None recursively, since null
    # values inside authorized arguments must survive unchanged.
    return request.model_dump(mode="json", by_alias=True, exclude={"additional_properties"})


def _execution_result(response: httpx.Response) -> CallToolResult:
    _check_response(response, executing=True)
    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise TypeError("Expected an MCP result object")  # noqa: TRY301
        return build_request(CallToolResult, payload)
    except (ValueError, TypeError, KeyError):
        # A malformed success cannot establish that execution did not happen.
        raise _unknown_response(response) from None


class MCP:
    """Stored-server MCP discovery and caller-authorized execution."""

    def __init__(self, client: OtariClient) -> None:
        self._client = client

    def list_tools(self, mcp_server_id: str | UUID) -> McpToolsResponse:
        """Discover the authorized catalog and the stored-server revision.

        Tool annotations are untrusted metadata, not authorization decisions.
        """
        server_id = UUID(str(mcp_server_id))
        try:
            response = self._client._http.get(
                f"{self._client._base_url}/mcp/servers/{server_id}/tools",
                headers=self._client._default_headers,
                follow_redirects=False,
            )
        except httpx.RequestError:
            raise MCPError("MCP discovery transport failed", execution_state="not_started") from None
        _check_response(response, executing=False)
        return McpToolsResponse.model_validate(response.json())

    def execute(
        self,
        *,
        mcp_server_id: str | UUID,
        tool_name: str,
        arguments: dict[str, Any],
        server_revision: str,
        client_execution_id: str | UUID,
    ) -> CallToolResult:
        """Execute exactly the caller-authorized call with one HTTP attempt.

        The application owns approval, edited arguments, rejection and
        cancellation. ``client_execution_id`` is correlation, NOT idempotency.
        Persist discovery's ``server_revision`` with the authorized call.
        Network failures and untyped responses are outcome-unknown; never
        retry automatically or fall back to direct MCP execution.
        A native result with ``is_error=True`` is a definitive result.
        """
        body = _execution_body(mcp_server_id, tool_name, arguments, server_revision, client_execution_id)
        try:
            response = self._client._http.post(
                f"{self._client._base_url}/mcp/execute",
                json=body,
                headers=self._client._default_headers,
                follow_redirects=False,
            )
        except httpx.RequestError:
            raise _unknown_response() from None
        return _execution_result(response)


class AsyncMCP:
    """Async counterpart of :class:`MCP`, with the same execution safety contract."""

    def __init__(self, client: AsyncOtariClient) -> None:
        self._client = client

    async def list_tools(self, mcp_server_id: str | UUID) -> McpToolsResponse:
        """Discover the authorized catalog and stored-server revision."""
        server_id = UUID(str(mcp_server_id))
        try:
            response = await self._client._http.get(
                f"{self._client._base_url}/mcp/servers/{server_id}/tools",
                headers=self._client._default_headers,
                follow_redirects=False,
            )
        except httpx.RequestError:
            raise MCPError("MCP discovery transport failed", execution_state="not_started") from None
        _check_response(response, executing=False)
        return McpToolsResponse.model_validate(response.json())

    async def execute(
        self,
        *,
        mcp_server_id: str | UUID,
        tool_name: str,
        arguments: dict[str, Any],
        server_revision: str,
        client_execution_id: str | UUID,
    ) -> CallToolResult:
        """Execute one authorized call, without retries; see :meth:`MCP.execute`.

        Task cancellation propagates normally. Cancellation after starting the
        request does not establish whether the remote tool ran.
        """
        body = _execution_body(mcp_server_id, tool_name, arguments, server_revision, client_execution_id)
        try:
            response = await self._client._http.post(
                f"{self._client._base_url}/mcp/execute",
                json=body,
                headers=self._client._default_headers,
                follow_redirects=False,
            )
        except httpx.RequestError:
            raise _unknown_response() from None
        return _execution_result(response)
