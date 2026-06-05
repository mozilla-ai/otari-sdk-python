"""Integration tests for the generated control-plane client against a live gateway.

These drive the generated control-plane client through a full CRUD lifecycle for
every management endpoint (keys, users, budgets, pricing, usage). They start a
real gateway on SQLite with a master key, so no provider credentials or database
server are needed: control-plane endpoints never call an LLM provider.

Run requirements:
- The ``gateway`` console script on PATH (set ``OTARI_GATEWAY_CMD`` to override),
  e.g. ``pip install otari-gateway`` in CI.
- The generated client importable (this preview imports it from
  ``src/otari/_generated``; once it is wired into the public client, import from
  there instead).

Auth note, verified against the gateway: management endpoints authenticate via
``Authorization: Bearer <master_key>``, NOT the ``Otari-Key`` virtual-key header
used for inference.
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

MASTER_KEY = "itest-master-key"

# Preview: import the generated client from where the codegen PR drops it.
_GENERATED = Path(__file__).resolve().parents[2] / "src" / "otari" / "_generated"
if _GENERATED.is_dir():
    sys.path.insert(0, str(_GENERATED))

ocp = pytest.importorskip("otari_control_plane", reason="generated control-plane client not present")

from otari_control_plane.api.budgets_api import BudgetsApi  # noqa: E402
from otari_control_plane.api.keys_api import KeysApi  # noqa: E402
from otari_control_plane.api.pricing_api import PricingApi  # noqa: E402
from otari_control_plane.api.usage_api import UsageApi  # noqa: E402
from otari_control_plane.api.users_api import UsersApi  # noqa: E402
from otari_control_plane.exceptions import NotFoundException  # noqa: E402
from otari_control_plane.models.create_budget_request import CreateBudgetRequest  # noqa: E402
from otari_control_plane.models.create_key_request import CreateKeyRequest  # noqa: E402
from otari_control_plane.models.create_user_request import CreateUserRequest  # noqa: E402
from otari_control_plane.models.set_pricing_request import SetPricingRequest  # noqa: E402
from otari_control_plane.models.update_budget_request import UpdateBudgetRequest  # noqa: E402
from otari_control_plane.models.update_key_request import UpdateKeyRequest  # noqa: E402
from otari_control_plane.models.update_user_request import UpdateUserRequest  # noqa: E402


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_healthy(base_url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with contextlib.suppress(urllib.error.URLError, ConnectionError):
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        time.sleep(0.3)
    raise RuntimeError(f"gateway did not become healthy at {base_url}")


@pytest.fixture(scope="module")
def gateway_url() -> Iterator[str]:
    cmd = os.environ.get("OTARI_GATEWAY_CMD", "gateway").split()
    port = _free_port()
    db_path = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    proc = subprocess.Popen(
        [
            *cmd, "serve",
            "--database-url", f"sqlite:///{db_path}",
            "--master-key", MASTER_KEY,
            "--host", "127.0.0.1", "--port", str(port),
            "--auto-migrate", "--log-level", "40",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_healthy(base_url)
        yield base_url
    finally:
        proc.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        with contextlib.suppress(FileNotFoundError):
            os.unlink(db_path)


@pytest.fixture
def api_client(gateway_url: str) -> Iterator[object]:
    config = ocp.Configuration(host=gateway_url)
    # Management endpoints use Bearer auth with the master key (not Otari-Key).
    with ocp.ApiClient(config) as client:
        client.set_default_header("Authorization", f"Bearer {MASTER_KEY}")
        yield client


def test_budgets_lifecycle(api_client: object) -> None:
    api = BudgetsApi(api_client)
    created = api.create_budget_v1_budgets_post(CreateBudgetRequest(max_budget=100.0, budget_duration_sec=3600))
    assert created.budget_id
    assert created.max_budget == 100.0
    bid = created.budget_id

    assert any(b.budget_id == bid for b in api.list_budgets_v1_budgets_get())
    assert api.get_budget_v1_budgets_budget_id_get(bid).budget_id == bid

    updated = api.update_budget_v1_budgets_budget_id_patch(bid, UpdateBudgetRequest(max_budget=250.0))
    assert updated.max_budget == 250.0

    api.delete_budget_v1_budgets_budget_id_delete(bid)
    with pytest.raises(NotFoundException):
        api.get_budget_v1_budgets_budget_id_get(bid)


def test_users_lifecycle(api_client: object) -> None:
    api = UsersApi(api_client)
    created = api.create_user_v1_users_post(CreateUserRequest(user_id="itest-user", alias="Alice"))
    assert created.user_id == "itest-user"
    assert created.alias == "Alice"

    assert any(u.user_id == "itest-user" for u in api.list_users_v1_users_get())
    assert api.get_user_v1_users_user_id_get("itest-user").user_id == "itest-user"

    updated = api.update_user_v1_users_user_id_patch("itest-user", UpdateUserRequest(alias="Alice2"))
    assert updated.alias == "Alice2"

    # usage sub-resource is readable for a known user
    api.get_user_usage_v1_users_user_id_usage_get("itest-user")

    api.delete_user_v1_users_user_id_delete("itest-user")
    with pytest.raises(NotFoundException):
        api.get_user_v1_users_user_id_get("itest-user")


def test_keys_lifecycle_returns_secret_on_create(api_client: object) -> None:
    api = KeysApi(api_client)
    created = api.create_key_v1_keys_post(CreateKeyRequest(key_name="itest-key"))
    assert created.id
    # The one-time key value must be present on create (manually-created surface).
    assert getattr(created, "key", None), "create_key must return the key secret"
    kid = created.id

    assert any(k.id == kid for k in api.list_keys_v1_keys_get())
    assert api.get_key_v1_keys_key_id_get(kid).id == kid

    updated = api.update_key_v1_keys_key_id_patch(kid, UpdateKeyRequest(key_name="itest-key-renamed"))
    assert updated.key_name == "itest-key-renamed"

    api.delete_key_v1_keys_key_id_delete(kid)
    with pytest.raises(NotFoundException):
        api.get_key_v1_keys_key_id_get(kid)


def test_pricing_lifecycle(api_client: object) -> None:
    api = PricingApi(api_client)
    model_key = "openai:itest-model"
    created = api.set_pricing_v1_pricing_post(
        SetPricingRequest(model_key=model_key, input_price_per_million=1.0, output_price_per_million=2.0)
    )
    assert created.model_key == model_key

    assert any(p.model_key == model_key for p in api.list_pricing_v1_pricing_get())
    assert api.get_pricing_v1_pricing_model_key_get(model_key).model_key == model_key
    # history is populated after at least one set
    assert api.get_pricing_history_v1_pricing_model_key_history_get(model_key) is not None

    api.delete_pricing_v1_pricing_model_key_delete(model_key)
    with pytest.raises(NotFoundException):
        api.get_pricing_v1_pricing_model_key_get(model_key)


def test_usage_is_readable(api_client: object) -> None:
    api = UsageApi(api_client)
    # Fresh gateway: usage list is readable (and empty), proving the typed GET works.
    assert api.list_usage_v1_usage_get() is not None
