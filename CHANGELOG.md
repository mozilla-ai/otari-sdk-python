# Changelog

## [0.4.1](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.4.0...otari-0.4.1) (2026-09-25)


### Bug Fixes

* read the renamed Otari-Request-ID and Otari-Attempt-ID response headers ([#100](https://github.com/mozilla-ai/otari-sdk-python/issues/100)) ([be1c262](https://github.com/mozilla-ai/otari-sdk-python/commit/be1c262759bff6d78dbcccc78a01ea2da250570a))

## [0.4.0](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.3.0...otari-0.4.0) (2026-09-16)


### ⚠ BREAKING CHANGES

* api_base must be the gateway origin with no path prefix, and requests now go to /api/v1 instead of /v1. Upgrade alongside an Otari gateway that serves the /api/v1 prefix.

### Features

* target the /api/v1 prefix + Regenerate SDK client core from Otari OpenAPI spec ([#78](https://github.com/mozilla-ai/otari-sdk-python/issues/78)) ([6119622](https://github.com/mozilla-ai/otari-sdk-python/commit/6119622f5864b9b50bb109f3544f39a7d36f29af))

## [0.3.0](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.2.0...otari-0.3.0) (2026-08-13)


### Features

* expose Otari request IDs ([#32](https://github.com/mozilla-ai/otari-sdk-python/issues/32)) ([ccee0f0](https://github.com/mozilla-ai/otari-sdk-python/commit/ccee0f03ea845660a22531d79a57ce708f43492d))


### Bug Fixes

* **ci:** make the endpoint-coverage check offline and deterministic ([#26](https://github.com/mozilla-ai/otari-sdk-python/issues/26)) ([af17bdd](https://github.com/mozilla-ai/otari-sdk-python/commit/af17bdd73c28b3c171c71898b824a86e296eb2f9))
* **control-plane:** forward usage.list arguments by keyword ([#24](https://github.com/mozilla-ai/otari-sdk-python/issues/24)) ([c7ac8eb](https://github.com/mozilla-ai/otari-sdk-python/commit/c7ac8ebe6dee4a32babe28efc8b0be56b297c80b))
* **control-plane:** map generated ApiException to typed OtariError ([#21](https://github.com/mozilla-ai/otari-sdk-python/issues/21)) ([47dd032](https://github.com/mozilla-ai/otari-sdk-python/commit/47dd032b3ca82a5514bac24366174b88c38deee7))

## [0.2.0](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.1.1...otari-0.2.0) (2026-06-16)


### Features

* add image generation and audio (speech/transcription) methods ([#16](https://github.com/mozilla-ai/otari-sdk-python/issues/16)) ([c558a03](https://github.com/mozilla-ai/otari-sdk-python/commit/c558a03afc192549f006717455fd64b9212bf393))

## [0.1.1](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.1.0...otari-0.1.1) (2026-06-12)


### Features

* independent release automation + surface gateway spec version ([#12](https://github.com/mozilla-ai/otari-sdk-python/issues/12)) ([21b9b5b](https://github.com/mozilla-ai/otari-sdk-python/commit/21b9b5b3dd61321371ff2df01fc0e5281f3c5228))
* wrap /v1/messages/count_tokens (regenerate core + ergonomic method) ([#10](https://github.com/mozilla-ai/otari-sdk-python/issues/10)) ([6704e56](https://github.com/mozilla-ai/otari-sdk-python/commit/6704e56c6107e270e08158311214111752b2f606))


### Bug Fixes

* regenerate SDK client core so message.reasoning is a string ([#14](https://github.com/mozilla-ai/otari-sdk-python/issues/14)) ([2cad75b](https://github.com/mozilla-ai/otari-sdk-python/commit/2cad75bc54754a225ab802bbfb247055692c9e73))


### Documentation

* add AGENTS.md/CLAUDE.md agent guide, refresh README ([#6](https://github.com/mozilla-ai/otari-sdk-python/issues/6)) ([56c3848](https://github.com/mozilla-ai/otari-sdk-python/commit/56c38483962952b042a69a2b9f3bc3f80bf54656))
