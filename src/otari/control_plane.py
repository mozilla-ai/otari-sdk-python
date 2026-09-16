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
``client.control_plane.keys.raw.keys_create_key(...)``), so the full
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
        return self.raw.keys_create_key(request, **kwargs)

    @_translate
    def get(self, key_id: str, **kwargs: Any) -> KeyInfo:
        return self.raw.keys_get_key(key_id, **kwargs)

    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[KeyInfo]:
        return self.raw.keys_list_keys(skip, limit, **kwargs)

    @_translate
    def update(self, key_id: str, request: UpdateKeyRequest, **kwargs: Any) -> KeyInfo:
        return self.raw.keys_update_key(key_id, request, **kwargs)

    @_translate
    def delete(self, key_id: str, **kwargs: Any) -> None:
        self.raw.keys_delete_key(key_id, **kwargs)


class UsersResource:
    """Ergonomic accessors for the users management endpoints.

    Aliases delegate to the generated :class:`UsersApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: UsersApi) -> None:
        self.raw = api

    @_translate
    def create(self, request: CreateUserRequest, **kwargs: Any) -> UserResponse:
        return self.raw.users_create_user(request, **kwargs)

    @_translate
    def get(self, user_id: str, **kwargs: Any) -> UserResponse:
        return self.raw.users_get_user(user_id, **kwargs)

    @_translate
    def update(self, user_id: str, request: UpdateUserRequest, **kwargs: Any) -> UserResponse:
        return self.raw.users_update_user(user_id, request, **kwargs)

    @_translate
    def delete(self, user_id: str, **kwargs: Any) -> None:
        self.raw.users_delete_user(user_id, **kwargs)

    @_translate
    def get_usage(self, user_id: str, **kwargs: Any) -> list[UsageLogResponse]:
        return self.raw.users_get_user_usage(user_id, **kwargs)

    # Defined last: a method named ``list`` shadows the ``list`` builtin for any
    # ``list[...]`` annotation that follows it in this class body.
    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[UserResponse]:
        return self.raw.users_list_users(skip, limit, **kwargs)


class BudgetsResource:
    """Ergonomic accessors for the budgets management endpoints.

    Aliases delegate to the generated :class:`BudgetsApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: BudgetsApi) -> None:
        self.raw = api

    @_translate
    def create(self, request: CreateBudgetRequest, **kwargs: Any) -> BudgetResponse:
        return self.raw.budgets_create_budget(request, **kwargs)

    @_translate
    def get(self, budget_id: str, **kwargs: Any) -> BudgetResponse:
        return self.raw.budgets_get_budget(budget_id, **kwargs)

    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[BudgetResponse]:
        return self.raw.budgets_list_budgets(skip, limit, **kwargs)

    @_translate
    def update(self, budget_id: str, request: UpdateBudgetRequest, **kwargs: Any) -> BudgetResponse:
        return self.raw.budgets_update_budget(budget_id, request, **kwargs)

    @_translate
    def delete(self, budget_id: str, **kwargs: Any) -> None:
        self.raw.budgets_delete_budget(budget_id, **kwargs)


class PricingResource:
    """Ergonomic accessors for the model-pricing management endpoints.

    Aliases delegate to the generated :class:`PricingApi`, which stays reachable
    via :attr:`raw` for the full generated surface.
    """

    def __init__(self, api: PricingApi) -> None:
        self.raw = api

    @_translate
    def get(self, model_key: str, **kwargs: Any) -> PricingResponse:
        return self.raw.pricing_get_pricing(model_key, **kwargs)

    @_translate
    def set(self, request: SetPricingRequest, **kwargs: Any) -> PricingResponse:
        return self.raw.pricing_set_pricing(request, **kwargs)

    @_translate
    def delete(self, model_key: str, **kwargs: Any) -> None:
        self.raw.pricing_delete_pricing(model_key, **kwargs)

    @_translate
    def get_history(self, model_key: str, **kwargs: Any) -> list[PricingResponse]:
        return self.raw.pricing_get_pricing_history(model_key, **kwargs)

    # Defined last: a method named ``list`` shadows the ``list`` builtin for any
    # ``list[...]`` annotation that follows it in this class body.
    @_translate
    def list(self, skip: int | None = None, limit: int | None = None, **kwargs: Any) -> list[PricingResponse]:
        return self.raw.pricing_list_pricing(skip, limit, **kwargs)


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
        #
        # user_id is repeatable upstream (user_id=a&user_id=b, max 50). This alias
        # keeps its single-user signature and wraps, so the public API is
        # unchanged; multi-user filtering is reachable via `raw`.
        return self.raw.usage_list_usage(
            start_date=start_date,
            end_date=end_date,
            user_id=None if user_id is None else [user_id],
            skip=skip,
            limit=limit,
            **kwargs,
        )


class ControlPlane:
    """Accessors for the gateway management endpoints, sharing one authenticated client.

    Each accessor returns a resource wrapper exposing ergonomic aliases (for
    example ``keys.create(...)``, ``users.list(...)``, ``budgets.get(...)``).
    The generator-derived methods stay reachable via the ``raw`` attribute on
    each resource (for example ``keys.raw.keys_create_key(...)``).
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
