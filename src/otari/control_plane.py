"""Typed client for the gateway control-plane (management) endpoints.

Wraps the OpenAPI-generated :mod:`otari._client` core (the same core that backs
the inference path). The control-plane endpoints (API keys,
users, budgets, pricing, usage) authenticate with
``Authorization: Bearer <admin/master key>``, which is distinct from the
``Otari-Key`` virtual key used for inference. Obtain an instance via
:attr:`otari.OtariClient.control_plane`.

Each resource accessor (``keys``, ``users``, ``budgets``, ``pricing``,
``usage``) exposes ergonomic aliases (``create``, ``get``, ``list``,
``update``, ``delete``, ...) that delegate to the generator-derived methods.
The raw generated API object stays reachable via the ``raw`` attribute on each
resource (for example
``client.control_plane.keys.raw.create_key_v1_keys_post(...)``), so the full
generated surface remains available as an escape hatch.
"""

from __future__ import annotations

from functools import cached_property, wraps
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

from otari import _client as _cp
from otari._base import map_api_exception
from otari._client.api.budgets_api import BudgetsApi
from otari._client.api.keys_api import KeysApi
from otari._client.api.pricing_api import PricingApi
from otari._client.api.usage_api import UsageApi
from otari._client.api.users_api import UsersApi
from otari._client.exceptions import ApiException

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from otari._client import (
        BudgetResponse,
        CreateBudgetRequest,
        CreateKeyRequest,
        CreateKeyResponse,
        CreateUserRequest,
        KeyInfo,
        PricingResponse,
        SetPricingRequest,
        UpdateBudgetRequest,
        UpdateKeyRequest,
        UpdateUserRequest,
        UsageEntry,
        UsageLogResponse,
        UserResponse,
    )


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _translate(fn: Callable[_P, _R]) -> Callable[_P, _R]:
    """Map a generated ``ApiException`` to a typed :class:`otari.errors.OtariError`.

    The inference client maps generated exceptions in ``client.py``; the
    control-plane ergonomic aliases get the same treatment here so callers see a
    single SDK error type instead of the raw generated ``ApiException``. The
    ``raw`` escape hatch is intentionally left unwrapped.
    """

    @wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return fn(*args, **kwargs)
        except ApiException as exc:
            raise map_api_exception(exc) from exc

    return wrapper


class KeysResource:
    """Ergonomic accessors for the API-keys management endpoints.

    Aliases delegate to the generated :class:`KeysApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: KeysApi) -> None:
        self.raw = api

    @_translate
    def create(self, request: CreateKeyRequest, **kwargs: Any) -> CreateKeyResponse:
        return self.raw.create_key_v1_keys_post(request, **kwargs)

    @_translate
    def get(self, key_id: str, **kwargs: Any) -> KeyInfo:
        return self.raw.get_key_v1_keys_key_id_get(key_id, **kwargs)

    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[KeyInfo]:
        return self.raw.list_keys_v1_keys_get(skip, limit, **kwargs)

    @_translate
    def update(self, key_id: str, request: UpdateKeyRequest, **kwargs: Any) -> KeyInfo:
        return self.raw.update_key_v1_keys_key_id_patch(key_id, request, **kwargs)

    @_translate
    def delete(self, key_id: str, **kwargs: Any) -> None:
        self.raw.delete_key_v1_keys_key_id_delete(key_id, **kwargs)


class UsersResource:
    """Ergonomic accessors for the users management endpoints.

    Aliases delegate to the generated :class:`UsersApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: UsersApi) -> None:
        self.raw = api

    @_translate
    def create(self, request: CreateUserRequest, **kwargs: Any) -> UserResponse:
        return self.raw.create_user_v1_users_post(request, **kwargs)

    @_translate
    def get(self, user_id: str, **kwargs: Any) -> UserResponse:
        return self.raw.get_user_v1_users_user_id_get(user_id, **kwargs)

    @_translate
    def update(self, user_id: str, request: UpdateUserRequest, **kwargs: Any) -> UserResponse:
        return self.raw.update_user_v1_users_user_id_patch(user_id, request, **kwargs)

    @_translate
    def delete(self, user_id: str, **kwargs: Any) -> None:
        self.raw.delete_user_v1_users_user_id_delete(user_id, **kwargs)

    @_translate
    def get_usage(self, user_id: str, **kwargs: Any) -> list[UsageLogResponse]:
        return self.raw.get_user_usage_v1_users_user_id_usage_get(user_id, **kwargs)

    # Defined last: a method named ``list`` shadows the ``list`` builtin for any
    # ``list[...]`` annotation that follows it in this class body.
    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[UserResponse]:
        return self.raw.list_users_v1_users_get(skip, limit, **kwargs)


class BudgetsResource:
    """Ergonomic accessors for the budgets management endpoints.

    Aliases delegate to the generated :class:`BudgetsApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: BudgetsApi) -> None:
        self.raw = api

    @_translate
    def create(self, request: CreateBudgetRequest, **kwargs: Any) -> BudgetResponse:
        return self.raw.create_budget_v1_budgets_post(request, **kwargs)

    @_translate
    def get(self, budget_id: str, **kwargs: Any) -> BudgetResponse:
        return self.raw.get_budget_v1_budgets_budget_id_get(budget_id, **kwargs)

    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[BudgetResponse]:
        return self.raw.list_budgets_v1_budgets_get(skip, limit, **kwargs)

    @_translate
    def update(self, budget_id: str, request: UpdateBudgetRequest, **kwargs: Any) -> BudgetResponse:
        return self.raw.update_budget_v1_budgets_budget_id_patch(budget_id, request, **kwargs)

    @_translate
    def delete(self, budget_id: str, **kwargs: Any) -> None:
        self.raw.delete_budget_v1_budgets_budget_id_delete(budget_id, **kwargs)


class PricingResource:
    """Ergonomic accessors for the model-pricing management endpoints.

    Aliases delegate to the generated :class:`PricingApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: PricingApi) -> None:
        self.raw = api

    @_translate
    def get(self, model_key: str, **kwargs: Any) -> PricingResponse:
        return self.raw.get_pricing_v1_pricing_model_key_get(model_key, **kwargs)

    @_translate
    def set(self, request: SetPricingRequest, **kwargs: Any) -> PricingResponse:
        return self.raw.set_pricing_v1_pricing_post(request, **kwargs)

    @_translate
    def delete(self, model_key: str, **kwargs: Any) -> None:
        self.raw.delete_pricing_v1_pricing_model_key_delete(model_key, **kwargs)

    @_translate
    def get_history(self, model_key: str, **kwargs: Any) -> list[PricingResponse]:
        return self.raw.get_pricing_history_v1_pricing_model_key_history_get(model_key, **kwargs)

    # Defined last: a method named ``list`` shadows the ``list`` builtin for any
    # ``list[...]`` annotation that follows it in this class body.
    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[PricingResponse]:
        return self.raw.list_pricing_v1_pricing_get(skip, limit, **kwargs)


class UsageResource:
    """Ergonomic accessors for the usage-log management endpoints.

    Aliases delegate to the generated :class:`UsageApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: UsageApi) -> None:
        self.raw = api

    @_translate
    def list(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> list[UsageEntry]:
        # Passed by keyword: the generated signature grows query-filter params
        # between user_id and skip as the gateway adds them.
        return self.raw.list_usage_v1_usage_get(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            skip=skip,
            limit=limit,
            **kwargs,
        )


class ControlPlane:
    """Accessors for the gateway management endpoints, sharing one authenticated client.

    Each accessor returns a resource wrapper exposing ergonomic aliases (for
    example ``keys.create(...)``, ``users.list(...)``, ``budgets.get(...)``).
    The generator-derived methods stay reachable via the ``raw`` attribute on
    each resource (for example ``keys.raw.create_key_v1_keys_post(...)``).
    """

    def __init__(self, base_url: str, bearer_token: str) -> None:
        config = _cp.Configuration(host=base_url)
        # The generated client is intentionally not type-checked here; treat it
        # as ``Any`` so strict mypy does not flag its untyped methods.
        self._api_client = cast("Any", _cp.ApiClient(config))
        self._api_client.set_default_header("Authorization", f"Bearer {bearer_token}")

    @cached_property
    def keys(self) -> KeysResource:
        return KeysResource(KeysApi(self._api_client))

    @cached_property
    def users(self) -> UsersResource:
        return UsersResource(UsersApi(self._api_client))

    @cached_property
    def budgets(self) -> BudgetsResource:
        return BudgetsResource(BudgetsApi(self._api_client))

    @cached_property
    def pricing(self) -> PricingResource:
        return PricingResource(PricingApi(self._api_client))

    @cached_property
    def usage(self) -> UsageResource:
        return UsageResource(UsageApi(self._api_client))

    def close(self) -> None:
        self._api_client.__exit__(None, None, None)
