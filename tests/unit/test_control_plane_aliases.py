"""Unit tests for the control-plane ergonomic aliases.

Each resource accessor (``keys``, ``users``, ``budgets``, ``pricing``,
``usage``) exposes short aliases (``create``, ``get``, ``list``, ...) that
delegate to the generator-derived methods on the underlying generated API,
which stays reachable via ``raw``. These tests stub ``raw`` and assert each
alias forwards to the right generated method with the right arguments, without
needing a live gateway.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from otari._client.api.budgets_api import BudgetsApi
from otari._client.api.keys_api import KeysApi
from otari._client.api.pricing_api import PricingApi
from otari._client.api.usage_api import UsageApi
from otari._client.api.users_api import UsersApi
from otari._client.exceptions import ApiException
from otari.control_plane import ControlPlane
from otari.errors import AuthenticationError

# (resource, alias, alias_args, generated_method, expected_forwarded_args)
CASES: list[tuple[str, str, tuple[Any, ...], str, tuple[Any, ...]]] = [
    ("keys", "create", ("req",), "create_key_v1_keys_post", ("req",)),
    ("keys", "get", ("k1",), "get_key_v1_keys_key_id_get", ("k1",)),
    ("keys", "list", (1, 2), "list_keys_v1_keys_get", (1, 2)),
    ("keys", "update", ("k1", "req"), "update_key_v1_keys_key_id_patch", ("k1", "req")),
    ("keys", "delete", ("k1",), "delete_key_v1_keys_key_id_delete", ("k1",)),
    ("users", "create", ("req",), "create_user_v1_users_post", ("req",)),
    ("users", "get", ("u1",), "get_user_v1_users_user_id_get", ("u1",)),
    ("users", "list", (3, 4), "list_users_v1_users_get", (3, 4)),
    ("users", "update", ("u1", "req"), "update_user_v1_users_user_id_patch", ("u1", "req")),
    ("users", "delete", ("u1",), "delete_user_v1_users_user_id_delete", ("u1",)),
    ("users", "get_usage", ("u1",), "get_user_usage_v1_users_user_id_usage_get", ("u1",)),
    ("budgets", "create", ("req",), "create_budget_v1_budgets_post", ("req",)),
    ("budgets", "get", ("b1",), "get_budget_v1_budgets_budget_id_get", ("b1",)),
    ("budgets", "list", (5, 6), "list_budgets_v1_budgets_get", (5, 6)),
    ("budgets", "update", ("b1", "req"), "update_budget_v1_budgets_budget_id_patch", ("b1", "req")),
    ("budgets", "delete", ("b1",), "delete_budget_v1_budgets_budget_id_delete", ("b1",)),
    ("pricing", "list", (7, 8), "list_pricing_v1_pricing_get", (7, 8)),
    ("pricing", "get", ("m1",), "get_pricing_v1_pricing_model_key_get", ("m1",)),
    ("pricing", "set", ("req",), "set_pricing_v1_pricing_post", ("req",)),
    ("pricing", "delete", ("m1",), "delete_pricing_v1_pricing_model_key_delete", ("m1",)),
    ("pricing", "get_history", ("m1",), "get_pricing_history_v1_pricing_model_key_history_get", ("m1",)),
]


@pytest.fixture
def control_plane() -> ControlPlane:
    return ControlPlane("http://localhost:8000", "master")


@pytest.mark.parametrize(("resource", "alias", "alias_args", "generated_method", "forwarded"), CASES)
def test_alias_delegates_to_generated_method(
    control_plane: ControlPlane,
    resource: str,
    alias: str,
    alias_args: tuple[Any, ...],
    generated_method: str,
    forwarded: tuple[Any, ...],
) -> None:
    res = getattr(control_plane, resource)
    res.raw = MagicMock()
    sentinel = object()
    getattr(res.raw, generated_method).return_value = sentinel

    result = getattr(res, alias)(*alias_args)

    getattr(res.raw, generated_method).assert_called_once_with(*forwarded)
    # ``delete`` aliases return ``None``; the rest return the generated result.
    assert result is (None if alias == "delete" else sentinel)


def test_usage_list_forwards_by_keyword(control_plane: ControlPlane) -> None:
    """usage.list must delegate by keyword.

    The generated signature grows query-filter params between ``user_id`` and
    ``skip``, so positional forwarding silently binds ``skip`` to a filter.
    """
    control_plane.usage.raw = MagicMock()
    control_plane.usage.list(None, None, "u1", 0, 10)
    control_plane.usage.raw.list_usage_v1_usage_get.assert_called_once_with(
        start_date=None, end_date=None, user_id="u1", skip=0, limit=10
    )


def test_alias_forwards_request_options_as_kwargs(control_plane: ControlPlane) -> None:
    control_plane.keys.raw = MagicMock()
    control_plane.keys.get("k1", _request_timeout=5.0, _headers={"X": "Y"})
    control_plane.keys.raw.get_key_v1_keys_key_id_get.assert_called_once_with(
        "k1", _request_timeout=5.0, _headers={"X": "Y"}
    )


def test_raw_exposes_generated_api(control_plane: ControlPlane) -> None:
    assert isinstance(control_plane.keys.raw, KeysApi)
    assert isinstance(control_plane.users.raw, UsersApi)
    assert isinstance(control_plane.budgets.raw, BudgetsApi)
    assert isinstance(control_plane.pricing.raw, PricingApi)
    assert isinstance(control_plane.usage.raw, UsageApi)
    control_plane.close()


# (resource, alias, generated_method, alias_args) covering every alias shape.
MAP_CASES: list[tuple[str, str, str, tuple[Any, ...]]] = [
    ("keys", "list", "list_keys_v1_keys_get", ()),
    ("users", "get", "get_user_v1_users_user_id_get", ("u1",)),
    ("budgets", "create", "create_budget_v1_budgets_post", ("req",)),
    ("pricing", "delete", "delete_pricing_v1_pricing_model_key_delete", ("m1",)),
    ("usage", "list", "list_usage_v1_usage_get", ()),
]


@pytest.mark.parametrize(("resource", "alias", "generated_method", "alias_args"), MAP_CASES)
def test_alias_maps_api_exception_to_typed_error(
    control_plane: ControlPlane,
    resource: str,
    alias: str,
    generated_method: str,
    alias_args: tuple[Any, ...],
) -> None:
    """Control-plane aliases surface a generated ``ApiException`` as a typed ``OtariError``.

    Mirrors the inference path (``client.py`` maps ``ApiException`` already), so
    a bad master key yields a clean ``AuthenticationError`` instead of leaking
    the raw generated exception (and a CLI traceback).
    """
    res = getattr(control_plane, resource)
    res.raw = MagicMock()
    getattr(res.raw, generated_method).side_effect = ApiException(
        status=401, reason="Unauthorized", body='{"detail":"Invalid master key"}'
    )

    with pytest.raises(AuthenticationError) as excinfo:
        getattr(res, alias)(*alias_args)

    assert not isinstance(excinfo.value, ApiException)
    assert excinfo.value.status_code == 401
    assert "Invalid master key" in str(excinfo.value)
