"""Typed client for the gateway control-plane (management) endpoints.

Wraps the OpenAPI-generated :mod:`otari._client` core (the same core that backs
the inference path). The control-plane endpoints (API keys,
users, budgets, pricing, usage) authenticate with
``Authorization: Bearer <admin/master key>``, which is distinct from the
``Otari-Key`` virtual key used for inference. Obtain an instance via
:attr:`otari.OtariClient.control_plane`.
"""

from __future__ import annotations

from functools import cached_property
from typing import Any, cast

from otari import _client as _cp
from otari._client.api.budgets_api import BudgetsApi
from otari._client.api.keys_api import KeysApi
from otari._client.api.pricing_api import PricingApi
from otari._client.api.usage_api import UsageApi
from otari._client.api.users_api import UsersApi


class ControlPlane:
    """Accessors for the gateway management endpoints, sharing one authenticated client.

    Method names on the underlying API objects are generator-derived (for
    example ``keys.create_key_v1_keys_post(...)``); friendlier aliases are a
    planned follow-up.
    """

    def __init__(self, base_url: str, bearer_token: str) -> None:
        config = _cp.Configuration(host=base_url)
        # The generated client is intentionally not type-checked here; treat it
        # as ``Any`` so strict mypy does not flag its untyped methods.
        self._api_client = cast("Any", _cp.ApiClient(config))
        self._api_client.set_default_header("Authorization", f"Bearer {bearer_token}")

    @cached_property
    def keys(self) -> KeysApi:
        return KeysApi(self._api_client)

    @cached_property
    def users(self) -> UsersApi:
        return UsersApi(self._api_client)

    @cached_property
    def budgets(self) -> BudgetsApi:
        return BudgetsApi(self._api_client)

    @cached_property
    def pricing(self) -> PricingApi:
        return PricingApi(self._api_client)

    @cached_property
    def usage(self) -> UsageApi:
        return UsageApi(self._api_client)

    def close(self) -> None:
        self._api_client.__exit__(None, None, None)
