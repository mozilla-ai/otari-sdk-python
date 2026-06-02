"""Quick smoke test for the otari Python SDK (synchronous client).

Reads credentials from the SDK's documented environment variables:
``GATEWAY_API_BASE`` (optional; defaults to the hosted gateway in platform
mode) and ``OTARI_AI_TOKEN`` (or the legacy ``GATEWAY_PLATFORM_TOKEN``).
"""

from otari import OtariClient, OtariError


def main() -> None:
    # Credentials are picked up from GATEWAY_API_BASE / OTARI_AI_TOKEN.
    client = OtariClient()

    with client:
        # -- Chat completion --
        print("=== Chat Completion ===")
        response = client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in three languages, one per line."}],
        )
        print(response.choices[0].message.content)
        print()

        # -- Streaming --
        print("=== Streaming ===")
        stream = client.completion(
            model="openai:gpt-4o-mini",
            messages=[{"role": "user", "content": "Count from 1 to 5."}],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end="", flush=True)
        print("\n")

        # -- Embeddings --
        print("=== Embeddings ===")
        try:
            emb = client.embedding(
                model="openai:text-embedding-3-small",
                input="The quick brown fox jumps over the lazy dog.",
            )
            vec = emb.data[0].embedding
            print(f"Dimension: {len(vec)}, first 5 values: {vec[:5]}")
        except OtariError as e:
            print(f"Skipped ({e.message})")
        print()

        # -- List models --
        print("=== Models ===")
        try:
            models = client.list_models()
            for m in models[:10]:
                print(f"  {m.id}")
            if len(models) > 10:
                print(f"  ... and {len(models) - 10} more")
        except OtariError as e:
            print(f"Skipped ({e.message})")
        print()

        # -- Responses API --
        print("=== Responses API ===")
        try:
            resp = client.response(
                model="openai:gpt-4o-mini",
                input="What is 2 + 2? Answer with just the number.",
            )
            print(resp.output_text)
        except OtariError as e:
            print(f"Skipped ({e.message})")

    print("\nDone.")


if __name__ == "__main__":
    main()
