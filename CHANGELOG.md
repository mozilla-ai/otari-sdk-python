# Changelog

## [0.5.0](https://github.com/mozilla-ai/otari-sdk-python/compare/otari-0.4.1...otari-0.5.0) (2026-10-07)


### Features

* regenerate SDK client core from Otari OpenAPI spec ([#106](https://github.com/mozilla-ai/otari-sdk-python/issues/106)) ([2117262](https://github.com/mozilla-ai/otari-sdk-python/commit/2117262c2a97ee0e0e06eedbaef8fa70754aea81))
* regenerate SDK client core from Otari OpenAPI spec ([#108](https://github.com/mozilla-ai/otari-sdk-python/issues/108)) ([4c77747](https://github.com/mozilla-ai/otari-sdk-python/commit/4c77747b1e08049a005bf8f5231e5370d1fc0c13))
* regenerate SDK client core from Otari OpenAPI spec ([#109](https://github.com/mozilla-ai/otari-sdk-python/issues/109)) ([340d725](https://github.com/mozilla-ai/otari-sdk-python/commit/340d725a8d8238bd32473e8c3bedfda586d932b3))
* regenerate SDK client core from Otari OpenAPI spec ([#110](https://github.com/mozilla-ai/otari-sdk-python/issues/110)) ([2bd8da6](https://github.com/mozilla-ai/otari-sdk-python/commit/2bd8da6179cc2be3524e2fb4ac0753980d2eae9e))
* regenerate SDK client core from Otari OpenAPI spec ([#111](https://github.com/mozilla-ai/otari-sdk-python/issues/111)) ([965a5cf](https://github.com/mozilla-ai/otari-sdk-python/commit/965a5cfd2f7805056337c84550816dc6f57a0536))
* regenerate SDK client core from Otari OpenAPI spec ([#112](https://github.com/mozilla-ai/otari-sdk-python/issues/112)) ([d7c5b8e](https://github.com/mozilla-ai/otari-sdk-python/commit/d7c5b8e4e771b4bdd02003c68ad1afab459e9300))
* regenerate SDK client core from Otari OpenAPI spec ([#113](https://github.com/mozilla-ai/otari-sdk-python/issues/113)) ([58e996b](https://github.com/mozilla-ai/otari-sdk-python/commit/58e996b4b1a4339a248f94a79da9cf3913a96c0a))
* regenerate SDK client core from Otari OpenAPI spec ([#114](https://github.com/mozilla-ai/otari-sdk-python/issues/114)) ([18e93e8](https://github.com/mozilla-ai/otari-sdk-python/commit/18e93e8dc9c19c24fb7fda2285ceb6e6618ac264))
* regenerate SDK client core from Otari OpenAPI spec ([#115](https://github.com/mozilla-ai/otari-sdk-python/issues/115)) ([4a9a297](https://github.com/mozilla-ai/otari-sdk-python/commit/4a9a297628c72b5d4c5c9dace0e7670ce3047be8))
* regenerate SDK client core from Otari OpenAPI spec ([#116](https://github.com/mozilla-ai/otari-sdk-python/issues/116)) ([2dbf11b](https://github.com/mozilla-ai/otari-sdk-python/commit/2dbf11bbdc99fec3f80c75faa737de264d0367d5))
* regenerate SDK client core from Otari OpenAPI spec ([#117](https://github.com/mozilla-ai/otari-sdk-python/issues/117)) ([b2972cc](https://github.com/mozilla-ai/otari-sdk-python/commit/b2972cc0580011a9967d69d73676638f25c9c8b3))
* regenerate SDK client core from Otari OpenAPI spec ([#118](https://github.com/mozilla-ai/otari-sdk-python/issues/118)) ([aaec3e0](https://github.com/mozilla-ai/otari-sdk-python/commit/aaec3e01d94b7f52a25452ab475e7b580214a744))
* regenerate SDK client core from Otari OpenAPI spec ([#120](https://github.com/mozilla-ai/otari-sdk-python/issues/120)) ([469d75a](https://github.com/mozilla-ai/otari-sdk-python/commit/469d75a570083a08da360f632c11ddbb1cbea3a4))

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
