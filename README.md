<p align="center">
  <img src="assets/otari-logo.svg" width="320" alt="otari logo"/>
</p>

<div align="center">

# Otari Python Client SDK

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/otari)](https://pypi.org/project/otari/)
<a href="https://discord.gg/4gf3zXrQUc">
    <img src="https://img.shields.io/static/v1?label=Chat%20on&message=Discord&color=blue&logo=Discord&style=flat-square" alt="Discord">
</a>

**Python client for [otari](https://github.com/mozilla-ai/otari), the open-source core that powers [otari.ai](https://otari.ai).**
Communicate with any LLM provider through otari using a single, typed interface.

[TypeScript SDK](https://github.com/mozilla-ai/otari-sdk-ts) | [Documentation](https://mozilla-ai.github.io/otari/) | [Platform (Beta)](https://otari.ai/)

</div>

> New to otari? The [otari repo](https://github.com/mozilla-ai/otari) explains what it is and why you’d use it.

## Quickstart

```bash
pip install otari
```

Generate an API token at [otari.ai/organization-settings/api-tokens](https://otari.ai/organization-settings/api-tokens), then add a provider key (e.g. OpenAI) at [otari.ai/organization-settings/provider-keys](https://otari.ai/organization-settings/provider-keys) so the gateway can route requests to that provider. Then use the client:

```python
from otari import OtariClient

client = OtariClient(
    platform_token="tk_your_api_token",
)

response = client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.choices[0].message.content)
```

With no `api_base`, the client defaults to the hosted gateway at `https://api.otari.ai`. Change the model string to switch between LLM providers through the gateway.

## Installation

### Requirements

- Python 3.11 or newer
- A running [otari](https://mozilla-ai.github.io/otari/gateway/overview/) instance (or the hosted gateway at [otari.ai](https://otari.ai/))

### Install

```bash
pip install otari
```

### Setting up credentials

For the hosted gateway, set your platform token (no `api_base` needed, it defaults to `https://api.otari.ai`):

```bash
export OTARI_AI_TOKEN="tk_your_api_token"
```

`GATEWAY_PLATFORM_TOKEN` is kept as a legacy alias for `OTARI_AI_TOKEN`; the canonical name takes precedence when both are set.

For a self-hosted gateway, set the base URL and an API key instead:

```bash
export GATEWAY_API_BASE="http://localhost:8000"
export GATEWAY_API_KEY="your-key-here"
```

Alternatively, pass credentials directly when creating the client (see [Authentication](#authentication)).

## Authentication

The client supports two authentication modes, matching the TypeScript SDK. When no explicit credentials are passed, the client auto-detects the mode from environment variables.

**Platform mode (hosted)**

Targets the hosted platform at [otari.ai](https://otari.ai/). The platform token is sent as a Bearer token in the standard `Authorization` header. Generate an API token at [otari.ai/organization-settings/api-tokens](https://otari.ai/organization-settings/api-tokens) and add a provider key (e.g. OpenAI) at [otari.ai/organization-settings/provider-keys](https://otari.ai/organization-settings/provider-keys) so the gateway can route requests to that provider. With no `api_base`, the client defaults to the hosted gateway at `https://api.otari.ai`:

```python
from otari import OtariClient

client = OtariClient(
    platform_token="tk_your_api_token",
)
```

Set `OTARI_AI_TOKEN` (or the legacy alias `GATEWAY_PLATFORM_TOKEN`) and `OtariClient()` picks up the token automatically.

**Self-hosted mode**

Targets a gateway you run yourself. The API key is sent via the custom `Otari-Key` header, and an explicit `api_base` is required. Follow the setup in the [otari repo](https://github.com/mozilla-ai/otari), then point the SDK at your gateway:

```python
from otari import OtariClient

client = OtariClient(
    api_base="http://localhost:8000",  # or wherever you host the gateway
    api_key="your-gateway-api-key",
)
```

Set `GATEWAY_API_BASE` and `GATEWAY_API_KEY` and `OtariClient()` picks them up automatically. Make sure your gateway has provider keys configured (e.g. OpenAI) so it can route requests upstream; see the [otari repo](https://github.com/mozilla-ai/otari) for setup.

**Environment variable quick reference**

| Variable | Mode | Purpose |
|----------|------|---------|
| `OTARI_AI_TOKEN` | Platform | Platform token, sent as `Authorization: Bearer …`. |
| `GATEWAY_PLATFORM_TOKEN` | Platform | Legacy alias for `OTARI_AI_TOKEN` (lower precedence). |
| `GATEWAY_API_BASE` | Self-hosted | Base URL of the gateway (required in self-hosted mode). |
| `GATEWAY_API_KEY` | Self-hosted | API key, sent via the `Otari-Key` header. |
| `GATEWAY_ADMIN_KEY` | Either | Admin/master key for the control-plane endpoints. |

When no explicit credentials are provided, the client reads from these variables:

```python
from otari import OtariClient

# Platform mode: OTARI_AI_TOKEN (or legacy GATEWAY_PLATFORM_TOKEN),
# defaulting to the hosted gateway.
# Self-hosted: GATEWAY_API_BASE + GATEWAY_API_KEY.
client = OtariClient()
```

## Usage

> **Migrating from a previous version?** `OtariClient` is now synchronous, call its methods directly (no `await`). For asynchronous code, switch to `AsyncOtariClient`, which keeps the previous `await`-based API. See [Async usage](#async-usage).

### Chat completions

```python
response = client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.completion(
    model="openai:gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True,
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### Responses API

```python
response = client.response(
    model="openai:gpt-4o-mini",
    input="Summarize this in one sentence.",
)

print(response.output_text)
```

### Messages API

The gateway's `/messages` endpoint (Anthropic message shape) is exposed via `message(...)`. `max_tokens` is required. Set `stream=True` to iterate raw message-stream event dicts.

```python
message = client.message(
    model="anthropic:claude-3-5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=256,
)

print(message.content)
```

### Response metadata

Use `with_response_metadata` to access the gateway's `X-Otari-Request-ID`:

```python
result = client.with_response_metadata.message(
    model="anthropic:claude-3-5-sonnet",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=256,
)
print(result.request_id, result.data.content)
```

For sync and async streams, `stream.request_id` is populated when iteration
starts, before the first event is yielded.

### Embeddings

```python
result = client.embedding(
    model="openai:text-embedding-3-small",
    input="Hello world",
)

print(result.data[0].embedding)
```

### Listing models

```python
models = client.list_models()
for model in models:
    print(model.id)
```

### Moderation

```python
result = client.moderation(
    model="openai:omni-moderation-latest",
    input="Some text to classify.",
)

print(result.results[0].flagged)
```

### Reranking

```python
result = client.rerank(
    model="cohere:rerank-v3.5",
    query="What is the capital of France?",
    documents=["Paris is the capital of France.", "Berlin is in Germany."],
)

for item in result.results:
    print(item.index, item.relevance_score)
```

### Image generation

```python
result = client.image_generation(
    model="openai:dall-e-3",
    prompt="A watercolor fox in a misty forest",
)

print(result.data[0].url)
```

The gateway returns a typed OpenAI-compatible `ImagesResponse`.

### Audio

Text to speech returns the raw audio bytes:

```python
audio = client.speech(
    model="openai:tts-1",
    input="Hello from otari.",
    voice="alloy",
)
Path("speech.mp3").write_bytes(audio)
```

Transcription uploads audio bytes and returns the parsed response:

```python
result = client.transcription(
    model="openai:whisper-1",
    file=Path("speech.mp3").read_bytes(),
)
print(result.json["text"])
```

### Batch operations

Submit many requests as a single batch job, poll for status, then fetch results once the batch completes. Batch endpoints are scoped to a `provider`.

```python
batch = client.create_batch(
    {
        "model": "openai:gpt-4o-mini",
        "requests": [
            {
                "custom_id": "req-1",
                "body": {
                    "model": "openai:gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Hello!"}],
                },
            },
        ],
        "completion_window": "24h",
    }
)

# Poll for status.
status = client.retrieve_batch(batch.id, provider="openai")

# List batches for a provider.
batches = client.list_batches("openai", {"limit": 20})

# Fetch results once complete (raises BatchNotCompleteError on HTTP 409).
results = client.retrieve_batch_results(batch.id, provider="openai")
for item in results.results:
    print(item.custom_id, item.result)

# Cancel a running batch.
client.cancel_batch(batch.id, provider="openai")
```

### Error handling

In platform mode, HTTP errors are mapped to typed exceptions:

```python
from otari import OtariClient, AuthenticationError, RateLimitError

try:
    response = client.completion(
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
| 409 | `BatchNotCompleteError` | Batch results requested before the batch finished |
| 429 | `RateLimitError` | Rate limit exceeded (includes `retry_after`) |
| 502 | `UpstreamProviderError` | Upstream provider unreachable |
| 504 | `GatewayTimeoutError` | Gateway timed out waiting for provider |

`UnsupportedCapabilityError` surfaces in both platform and non-platform modes; the other mappings are platform-mode only.

### Async usage

Every method on `OtariClient` has an asynchronous counterpart on `AsyncOtariClient`. It accepts the same constructor arguments and exposes the same methods, but they are coroutines you `await` (and streams are async iterables):

```python
import asyncio

from otari import AsyncOtariClient


async def main() -> None:
    async with AsyncOtariClient(platform_token="tk_your_api_token") as client:
        response = await client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response.choices[0].message.content)

        stream = await client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Tell me a story."}],
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)


asyncio.run(main())
```

### Context manager

The client supports a context manager for automatic cleanup:

```python
with OtariClient(api_base="http://localhost:8000") as client:
    response = client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
```

`AsyncOtariClient` supports the async equivalent:

```python
async with AsyncOtariClient(api_base="http://localhost:8000") as client:
    response = await client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
    )
```

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
