"""Offline MCP contract and single-attempt transport regression tests."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import httpcore
import httpx
import pytest
import respx

from otari import (
    AsyncOtariClient,
    CallToolResult,
    MCPError,
    MCPOutcomeUnknownError,
    McpToolsResponse,
    OtariClient,
)

BASE = "https://gateway.example.test"
SERVER = "2c948a61-dc96-4cd8-96bb-8e1434bf424e"
EXECUTION = "6e51b3bc-6f48-4c68-a61e-0786bc80cd67"
PARAMS = {
    "mcp_server_id": SERVER,
    "tool_name": "create_issue",
    "arguments": {"title": "Approved edit", "nested": {"null": None, "array": [1, False, "é"]}},
    "server_revision": "revision:1",
    "client_execution_id": EXECUTION,
}
CATALOG = {
    "server_id": SERVER,
    "server_revision": "revision:1",
    "tools": [{
        "name": "create_issue",
        "description": "Untrusted description",
        "input_schema": {"type": "object", "vendor:keyword": {"x": 1}},
        "annotations": {"readOnlyHint": False},
    }],
    "warnings": [{"tool_name": "omitted", "code": "mcp_tool_schema_unsupported"}],
}
RESULT = {
    "content": [{"type": "text", "text": "Created issue #42"}],
    "structuredContent": {"issue_number": 42},
    "isError": False,
    "_meta": {"trace": "native"},
    "vendor": {"untouched": True},
}


@pytest.fixture(params=["sync", "async"])
async def client(request, auth_mode, monkeypatch):
    for name in (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy",
        "OTARI_AI_TOKEN", "GATEWAY_PLATFORM_TOKEN", "GATEWAY_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    kwargs = {auth_mode: "test-secret"}
    cls = OtariClient if request.param == "sync" else AsyncOtariClient
    instance = cls(api_base=BASE, timeout=0.5, default_headers={"App-Context": "test"}, **kwargs)
    yield instance
    if isinstance(instance, AsyncOtariClient):
        await instance.close()
    else:
        instance.close()
    assert instance._http.is_closed


@pytest.fixture(params=["api_key", "platform_token"])
def auth_mode(request):
    return request.param


async def execute(client, **overrides):
    params = {**PARAMS, **overrides}
    if isinstance(client, AsyncOtariClient):
        return await client.mcp.execute(**params)
    return client.mcp.execute(**params)


async def discover(client):
    if isinstance(client, AsyncOtariClient):
        return await client.mcp.list_tools(UUID(SERVER))
    return client.mcp.list_tools(UUID(SERVER))


def assert_auth(request, auth_mode):
    expected = "Authorization" if auth_mode == "platform_token" else "Otari-Key"
    absent = "Otari-Key" if auth_mode == "platform_token" else "Authorization"
    assert request.headers[expected] == "Bearer test-secret"
    assert absent not in request.headers
    assert request.headers["App-Context"] == "test"


class TestMCP:
    async def test_discovery(self, client, auth_mode):
        with respx.mock as router:
            route = router.get(f"{BASE}/api/v1/mcp/servers/{SERVER}/tools").respond(200, json=CATALOG)
            result = await discover(client)
        assert isinstance(result, McpToolsResponse)
        assert result.to_dict() == {**CATALOG, "server_id": UUID(SERVER)}
        assert route.call_count == 1
        assert_auth(route.calls[0].request, auth_mode)
        assert client.mcp is client.mcp

    @pytest.mark.parametrize("is_error", [False, True])
    async def test_native_result_and_exact_arguments(self, client, auth_mode, is_error):
        native = {**RESULT, "isError": is_error}
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(200, json=native)
            result = await execute(client, mcp_server_id=UUID(SERVER), client_execution_id=UUID(EXECUTION))
        assert isinstance(result, CallToolResult)
        # Generated content models materialize absent nullable metadata as None.
        expected_content = [{**native["content"][0], "annotations": None, "_meta": None}]
        assert result.to_dict() == {**native, "content": expected_content}
        assert result.is_error is is_error
        assert route.call_count == 1
        request = route.calls[0].request
        assert json.loads(request.content) == PARAMS
        assert_auth(request, auth_mode)
        assert request.extensions["timeout"]["read"] == 0.5

    @pytest.mark.parametrize("content", [
        {"type": "image", "data": "YWJj", "mimeType": "image/png"},
        {"type": "audio", "data": "YWJj", "mimeType": "audio/wav"},
        {"type": "resource_link", "uri": "https://example.com/a", "name": "a"},
        {"type": "resource", "resource": {"uri": "https://example.com/a", "text": "native"}},
    ])
    async def test_native_content_variants(self, client, content):
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(200, json={"content": [content]})
            result = await execute(client, arguments={})
        actual = result.content[0].to_dict()
        for key, value in content.items():
            if key == "resource":
                for resource_key, resource_value in value.items():
                    assert actual[key][resource_key] == resource_value
            else:
                assert actual[key] == value
        assert route.call_count == 1
        assert json.loads(route.calls[0].request.content)["arguments"] == {}

    @pytest.mark.parametrize(("status", "code", "state"), [
        (401, "authentication_failed", "not_started"),
        (403, "mcp_tool_not_allowed", "not_started"),
        (404, "mcp_server_not_found", "not_started"),
        (409, "mcp_server_changed", "not_started"),
        (422, "invalid_request", "not_started"),
        (429, "rate_limit_exceeded", "not_started"),
        (502, "mcp_connection_failed", "not_started"),
        (503, "mcp_capacity_unavailable", "not_started"),
        (504, "mcp_outcome_unknown", "outcome_unknown"),
        (502, "mcp_result_too_large", "outcome_unknown"),
    ])
    async def test_typed_errors(self, client, status, code, state):
        body = {"detail": "Safe gateway message", "code": code, "execution_state": state, "request_id": "req_body"}
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(
                status, json=body, headers={"Retry-After": "2", "X-Otari-Request-ID": "req_header"},
            )
            with pytest.raises(MCPError) as caught:
                await execute(client)
        error = caught.value
        assert error.code == code
        assert error.execution_state == state
        assert error.request_id == "req_body"
        assert error.status_code == status
        assert error.retry_after == "2"
        assert error.message == body["detail"]
        assert isinstance(error, MCPOutcomeUnknownError) == (state == "outcome_unknown")
        assert route.call_count == 1

    async def test_discovery_typed_error(self, client):
        with respx.mock as router:
            route = router.get(f"{BASE}/api/v1/mcp/servers/{SERVER}/tools").respond(404, json={
                "detail": "MCP server not found", "code": "mcp_server_not_found",
                "execution_state": "not_started", "request_id": "req_discovery",
            })
            with pytest.raises(MCPError) as caught:
                await discover(client)
        assert caught.value.code == "mcp_server_not_found"
        assert caught.value.request_id == "req_discovery"
        assert caught.value.execution_state == "not_started"
        assert route.call_count == 1

    @pytest.mark.parametrize("failure", [
        httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout,
        httpx.ConnectError, httpx.ReadError, httpx.WriteError, httpx.RemoteProtocolError,
    ])
    async def test_transport_failure_is_unknown(self, client, failure, caplog):
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").mock(side_effect=failure("SECRET arguments"))
            with pytest.raises(MCPOutcomeUnknownError) as caught:
                await execute(client)
        assert route.call_count == 1
        assert caught.value.execution_state == "outcome_unknown"
        assert caught.value.code is None
        assert caught.value.request_id is None
        assert caught.value.status_code is None
        assert "SECRET" not in str(caught.value)
        assert "SECRET" not in caplog.text
        assert caught.value.original_error is None
        assert caught.value.__suppress_context__

    @pytest.mark.parametrize(("status", "body"), [
        (502, "proxy failure SECRET"), (504, "timeout"), (200, "invalid JSON"),
        (200, "{}"), (200, "null"), (200, '{"content": "invalid"}'),
        (429, '{"detail":"untyped"}'),
        (500, '{"execution_state":"not_started"}'),
    ])
    async def test_untyped_response_is_unknown(self, client, status, body):
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(
                status, text=body, headers={"X-Otari-Request-ID": "req_header"},
            )
            with pytest.raises(MCPOutcomeUnknownError) as caught:
                await execute(client)
        assert route.call_count == 1
        assert caught.value.request_id == "req_header"
        assert caught.value.code is None
        assert "SECRET" not in str(caught.value)

    @pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
    async def test_no_redirect(self, client, status):
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(
                status, headers={"Location": f"{BASE}/redirected"},
            )
            redirected = router.route(url=f"{BASE}/redirected").respond(200, json=RESULT)
            with pytest.raises(MCPOutcomeUnknownError):
                await execute(client)
        assert route.call_count == 1
        assert redirected.call_count == 0

    async def test_correlation_is_not_deduplication(self, client):
        with respx.mock as router:
            route = router.post(f"{BASE}/api/v1/mcp/execute").respond(200, json=RESULT)
            await execute(client)
            await execute(client)
        assert route.call_count == 2

    async def test_invalid_request_never_sent(self, client):
        with respx.mock as router:
            with pytest.raises(ValueError, match="server_revision"):
                await execute(client, server_revision="")
            assert router.calls.call_count == 0

    @pytest.mark.parametrize("failure", [httpcore.ConnectError, httpcore.ConnectTimeout])
    async def test_actual_transport_does_not_retry_connection(self, client, failure, monkeypatch):
        # Below HTTPX and httpcore's retry loop, unlike respx or a mocked .post.
        # No real socket is opened. A regression enabling connection retries
        # increases this counter even though the wrapper calls .post only once.
        backend = client._http._transport._pool._network_backend
        mock_type = AsyncMock if isinstance(client, AsyncOtariClient) else Mock
        connect = mock_type(side_effect=failure("mock connection failure"))
        monkeypatch.setattr(backend, "connect_tcp", connect)
        with pytest.raises(MCPOutcomeUnknownError):
            await execute(client)
        assert connect.call_count == 1

    async def test_environment_proxy_transport_has_no_retries(self, client, monkeypatch):
        monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example.test:8080")
        cls = type(client)
        proxied = cls(api_base=BASE, api_key="test-secret")
        try:
            transport = proxied._http._transport_for_url(httpx.URL(BASE))
            assert transport._pool._retries == 0
            backend = transport._pool._network_backend
            mock_type = AsyncMock if isinstance(proxied, AsyncOtariClient) else Mock
            connect = mock_type(side_effect=httpcore.ConnectError("mock proxy failure"))
            monkeypatch.setattr(backend, "connect_tcp", connect)
            with pytest.raises(MCPOutcomeUnknownError):
                await execute(proxied)
            assert connect.call_count == 1
            assert connect.call_args.kwargs["host"] == "proxy.example.test"
        finally:
            if isinstance(proxied, AsyncOtariClient):
                await proxied.close()
            else:
                proxied.close()

    async def test_async_cancellation_does_not_retry(self, client):
        if not isinstance(client, AsyncOtariClient):
            return

        # respx does not record BaseException failures such as CancelledError.
        # Count at the callback itself, before cancellation unwinds the stack.
        attempts = Mock()

        def cancel(request):
            attempts(request)
            raise asyncio.CancelledError

        with respx.mock as router:
            router.post(f"{BASE}/api/v1/mcp/execute").mock(side_effect=cancel)
            with pytest.raises(asyncio.CancelledError):
                await execute(client)
        assert attempts.call_count == 1
