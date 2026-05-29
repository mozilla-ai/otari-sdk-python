<p align="center">
  <img src="assets/otari-logo.svg" width="320" alt="otari logo"/>
</p>

<div align="center">

# otari (Python)

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/otari)](https://pypi.org/project/otari/)
<a href="https://discord.gg/4gf3zXrQUc">
    <img src="https://img.shields.io/static/v1?label=Chat%20on&message=Discord&color=blue&logo=Discord&style=flat-square" alt="Discord">
</a>

**Python client for [otari-gateway](https://github.com/mozilla-ai/otari).**
Communicate with any LLM provider through the gateway using a single, typed interface.

[TypeScript SDK](https://github.com/mozilla-ai/otari-sdk-ts) | [Documentation](https://mozilla-ai.github.io/otari/) | [Platform (Beta)](https://otari.ai/)

</div>

## Quickstart

```python
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
```

**That's it!** Change the model string to switch between LLM providers through the gateway.

## Installation

### Requirements

- Python 3.11 or newer
- A running [otari-gateway](https://mozilla-ai.github.io/otari/gateway/overview/) instance

### Install

```bash
pip install otari
```

### Setting Up Credentials

Set environment variables for your gateway:

```bash
export GATEWAY_API_BASE="http://localhost:8000"
export GATEWAY_PLATFORM_TOKEN="your-token-here"
# or for non-platform mode:
export GATEWAY_API_KEY="your-key-here"
```

Alternatively, pass credentials directly when creating the client (see [Usage](#usage) examples).

## otari-gateway

This Python SDK is a client for [otari-gateway](https://github.com/mozilla-ai/otari), an **optional** FastAPI-based proxy server that adds enterprise-grade features on top of the core library:

- **Budget Management** - Enforce spending limits with automatic daily, weekly, or monthly resets
- **API Key Management** - Issue, revoke, and monitor virtual API keys without exposing provider credentials
- **Usage Analytics** - Track every request with full token counts, costs, and metadata
- **Multi-tenant Support** - Manage access and budgets across users and teams

The gateway sits between your applications and LLM providers, exposing an OpenAI-compatible API that works with any supported provider.

### Quick Start

```bash
docker run \
  -e GATEWAY_MASTER_KEY="your-secure-master-key" \
  -e OPENAI_API_KEY="your-api-key" \
  -p 8000:8000 \
  ghcr.io/mozilla-ai/otari/gateway:latest
```

> **Note:** You can use a specific release version instead of `latest` (e.g., `1.2.0`). See [available versions](https://github.com/orgs/mozilla-ai/packages/container/package/otari%2Fgateway).

### Managed Platform (Beta)

Prefer a hosted experience? The [otari platform](https://otari.ai/) provides a managed control plane for keys, usage tracking, and cost visibility across providers, while still building on the same `otari` interfaces.

## Usage

### Authentication Modes

The client supports two authentication modes, matching the TypeScript SDK:

#### Platform Mode (Recommended)

Uses a Bearer token in the standard Authorization header. On the hosted platform, generate an API token at [otari.ai/organization-settings/api-tokens](https://otari.ai/organization-settings/api-tokens) and add a provider key (e.g. OpenAI) at [otari.ai/organization-settings/provider-keys](https://otari.ai/organization-settings/provider-keys) so the gateway can route requests to that provider:

```python
client = OtariClient(
    api_base="http://localhost:8000",
    platform_token="tk_your_api_token",
)
```

#### Non-Platform Mode

Sends the API key via a custom `Otari-Key` header:

```python
client = OtariClient(
    api_base="http://localhost:8000",
    api_key="your-api-key",
)
```

#### Auto-Detection from Environment Variables

When no explicit credentials are provided, the client reads from environment variables:

```python
# Uses GATEWAY_API_BASE, GATEWAY_PLATFORM_TOKEN, or GATEWAY_API_KEY
client = OtariClient()
```

### Chat Completions

```python
response = await client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.choices[0].message.content)
```

### Streaming

```python
stream = await client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True,
)

async for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### Responses API

```python
response = await client.response(
    model="openai:gpt-4o-mini",
    input="Summarize this in one sentence.",
)

print(response.output_text)
```

### Embeddings

```python
result = await client.embedding(
    model="openai:text-embedding-3-small",
    input="Hello world",
)

print(result.data[0].embedding)
```

### Listing Models

```python
models = await client.list_models()
for model in models:
    print(model.id)
```

### Error Handling

In platform mode, HTTP errors are mapped to typed exceptions:

```python
from otari import OtariClient, AuthenticationError, RateLimitError

try:
    response = await client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
except AuthenticationError as e:
    print(f"Invalid credentials: {e.message}")
except RateLimitError as e:
    print(f"Rate limited, retry after: {e.retry_after}")
```

| HTTP Status | Error Class | Description |
|------------|-------------|-------------|
| 400 (capability) | `UnsupportedCapabilityError` | Selected provider does not support the requested capability |
| 401, 403 | `AuthenticationError` | Invalid or missing credentials |
| 402 | `InsufficientFundsError` | Budget or credits exhausted |
| 404 | `ModelNotFoundError` | Model not found, or no provider key configured for the requested provider. The exception's `message` carries the gateway's detail. |
| 429 | `RateLimitError` | Rate limit exceeded (includes `retry_after`) |
| 502 | `UpstreamProviderError` | Upstream provider unreachable |
| 504 | `GatewayTimeoutError` | Gateway timed out waiting for provider |

`UnsupportedCapabilityError` surfaces in both platform and non-platform modes; the other mappings are platform-mode only.

### Context Manager

The client supports async context manager for automatic cleanup:

```python
async with OtariClient(api_base="http://localhost:8000") as client:
    response = await client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
```

## Why choose `otari`?

- **Simple, unified interface** - Single client for all providers through the gateway, switch models with just a string change
- **Developer friendly** - Full type hints for better IDE support and clear, actionable error messages
- **Leverages the OpenAI SDK** - Built on the official OpenAI Python SDK for maximum compatibility
- **Async-first** - Built on `AsyncOpenAI` for modern async Python applications
- **Stays framework-agnostic** so it can be used across different projects and use cases
- **Battle-tested** - Powers our own production tools ([any-agent](https://github.com/mozilla-ai/any-agent))

## Development

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/

# Lint
ruff check src/ tests/

# Type-check
mypy src/
```

## Documentation

- **[Full Documentation](https://mozilla-ai.github.io/otari/)** - Complete guides and API reference
- **[Supported Providers](https://mozilla-ai.github.io/otari/providers/)** - List of all supported LLM providers
- **[Gateway Documentation](https://mozilla-ai.github.io/otari/gateway/overview/)** - Gateway setup and deployment
- **[TypeScript SDK](https://github.com/mozilla-ai/otari-sdk-ts)** - The TypeScript SDK for Node.js applications
- **[otari Platform (Beta)](https://otari.ai/)** - Hosted control plane for key management, usage tracking, and cost visibility

## Contributing

We welcome contributions from developers of all skill levels! Please see the [Contributing Guide](https://github.com/mozilla-ai/otari/blob/main/CONTRIBUTING.md) or open an issue to discuss changes.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
