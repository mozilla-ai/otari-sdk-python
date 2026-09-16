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
    ("keys", "create", ("req",), "keys_create_key", ("req",)),
    ("keys", "get", ("k1",), "keys_get_key", ("k1",)),
    ("keys", "list", (1, 2), "keys_list_keys", (1, 2)),
    ("keys", "update", ("k1", "req"), "keys_update_key", ("k1", "req")),
    ("keys", "delete", ("k1",), "keys_delete_key", ("k1",)),
    ("users", "create", ("req",), "users_create_user", ("req",)),
    ("users", "get", ("u1",), "users_get_user", ("u1",)),
    ("users", "list", (3, 4), "users_list_users", (3, 4)),
    ("users", "update", ("u1", "req"), "users_update_user", ("u1", "req")),
    ("users", "delete", ("u1",), "users_delete_user", ("u1",)),
    ("users", "get_usage", ("u1",), "users_get_user_usage", ("u1",)),
    ("budgets", "create", ("req",), "budgets_create_budget", ("req",)),
    ("budgets", "get", ("b1",), "budgets_get_budget", ("b1",)),
    ("budgets", "list", (5, 6), "budgets_list_budgets", (5, 6)),
    ("budgets", "update", ("b1", "req"), "budgets_update_budget", ("b1", "req")),
    ("budgets", "delete", ("b1",), "budgets_delete_budget", ("b1",)),
    ("pricing", "list", (7, 8), "pricing_list_pricing", (7, 8)),
    ("pricing", "get", ("m1",), "pricing_get_pricing", ("m1",)),
    ("pricing", "set", ("req",), "pricing_set_pricing", ("req",)),
    ("pricing", "delete", ("m1",), "pricing_delete_pricing", ("m1",)),
    ("pricing", "get_history", ("m1",), "pricing_get_pricing_history", ("m1",)),
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
    control_plane.usage.raw.usage_list_usage.assert_called_once_with(
        start_date=None, end_date=None, user_id=["u1"], skip=0, limit=10
    )


def test_usage_list_wraps_user_id_for_the_repeatable_query_param(
    control_plane: ControlPlane,
) -> None:
    """user_id is repeatable upstream, so the single-user alias must wrap it."""
    control_plane.usage.raw = MagicMock()
    control_plane.usage.list(user_id="u1")
    kwargs = control_plane.usage.raw.usage_list_usage.call_args.kwargs
    assert kwargs["user_id"] == ["u1"]


def test_usage_list_leaves_user_id_none_unwrapped(control_plane: ControlPlane) -> None:
    """None must stay None; [None] would filter on a literal missing user."""
    control_plane.usage.raw = MagicMock()
    control_plane.usage.list()
    kwargs = control_plane.usage.raw.usage_list_usage.call_args.kwargs
    assert kwargs["user_id"] is None


def test_alias_forwards_request_options_as_kwargs(control_plane: ControlPlane) -> None:
    control_plane.keys.raw = MagicMock()
    control_plane.keys.get("k1", _request_timeout=5.0, _headers={"X": "Y"})
    control_plane.keys.raw.keys_get_key.assert_called_once_with("k1", _request_timeout=5.0, _headers={"X": "Y"})


def test_raw_exposes_generated_api(control_plane: ControlPlane) -> None:
    assert isinstance(control_plane.keys.raw, KeysApi)
    assert isinstance(control_plane.users.raw, UsersApi)
    assert isinstance(control_plane.budgets.raw, BudgetsApi)
    assert isinstance(control_plane.pricing.raw, PricingApi)
    assert isinstance(control_plane.usage.raw, UsageApi)
    control_plane.close()


# (resource, alias, generated_method, alias_args) covering every alias shape.
MAP_CASES: list[tuple[str, str, str, tuple[Any, ...]]] = [
    ("keys", "list", "keys_list_keys", ()),
    ("users", "get", "users_get_user", ("u1",)),
    ("budgets", "create", "budgets_create_budget", ("req",)),
    ("pricing", "delete", "pricing_delete_pricing", ("m1",)),
    ("usage", "list", "usage_list_usage", ()),
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
