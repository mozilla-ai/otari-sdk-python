"""Integration tests for the control-plane surface against a live gateway.

These drive ``OtariClient.control_plane`` through a full CRUD lifecycle for every
management endpoint (keys, users, budgets, pricing, usage), exercising the manual
wiring (Bearer auth + the generated client) end to end via the ergonomic aliases
(``keys.create(...)`` etc.), plus the ``raw`` escape hatch. They start a real
gateway on SQLite with a master key, so no provider credentials or database
server are needed: control-plane endpoints never call an LLM provider.

Run requirements:
- The ``gateway`` console script on PATH (set ``OTARI_GATEWAY_CMD`` to override),
  e.g. ``pip install otari-gateway`` in CI.

Auth note, verified against the gateway: management endpoints authenticate via
``Authorization: Bearer <master_key>``, NOT the ``Otari-Key`` virtual-key header
used for inference. ``OtariClient`` sends the former when given ``admin_key``.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from otari import OtariClient
from otari._client.exceptions import NotFoundException
from otari._client.models.create_budget_request import CreateBudgetRequest
from otari._client.models.create_key_request import CreateKeyRequest
from otari._client.models.create_user_request import CreateUserRequest
from otari._client.models.set_pricing_request import SetPricingRequest
from otari._client.models.update_budget_request import UpdateBudgetRequest
from otari._client.models.update_key_request import UpdateKeyRequest
from otari._client.models.update_user_request import UpdateUserRequest

pytestmark = pytest.mark.integration

MASTER_KEY = "itest-master-key"


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
    if shutil.which(cmd[0]) is None:
        pytest.skip(f"gateway command '{cmd[0]}' not found; set OTARI_GATEWAY_CMD (e.g. pip install the gateway)")
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
def client(gateway_url: str) -> Iterator[OtariClient]:
    otari = OtariClient(api_base=gateway_url, admin_key=MASTER_KEY)
    try:
        yield otari
    finally:
        otari.control_plane.close()


def test_budgets_lifecycle(client: OtariClient) -> None:
    budgets = client.control_plane.budgets
    created = budgets.create(CreateBudgetRequest(max_budget=100.0, budget_duration_sec=3600))
    assert created.budget_id
    assert created.max_budget == 100.0
    bid = created.budget_id

    assert any(b.budget_id == bid for b in budgets.list())
    assert budgets.get(bid).budget_id == bid

    updated = budgets.update(bid, UpdateBudgetRequest(max_budget=250.0))
    assert updated.max_budget == 250.0

    budgets.delete(bid)
    with pytest.raises(NotFoundException):
        budgets.get(bid)


def test_users_lifecycle(client: OtariClient) -> None:
    users = client.control_plane.users
    created = users.create(CreateUserRequest(user_id="itest-user", alias="Alice"))
    assert created.user_id == "itest-user"
    assert created.alias == "Alice"

    assert any(u.user_id == "itest-user" for u in users.list())
    assert users.get("itest-user").user_id == "itest-user"

    updated = users.update("itest-user", UpdateUserRequest(alias="Alice2"))
    assert updated.alias == "Alice2"

    users.get_usage("itest-user")

    users.delete("itest-user")
    with pytest.raises(NotFoundException):
        users.get("itest-user")


def test_keys_lifecycle_returns_secret_on_create(client: OtariClient) -> None:
    keys = client.control_plane.keys
    created = keys.create(CreateKeyRequest(key_name="itest-key"))
    assert created.id
    # The one-time key value must be present on create (manually-created surface).
    assert getattr(created, "key", None), "create_key must return the key secret"
    kid = created.id

    assert any(k.id == kid for k in keys.list())
    assert keys.get(kid).id == kid

    updated = keys.update(kid, UpdateKeyRequest(key_name="itest-key-renamed"))
    assert updated.key_name == "itest-key-renamed"

    keys.delete(kid)
    with pytest.raises(NotFoundException):
        keys.get(kid)


def test_pricing_lifecycle(client: OtariClient) -> None:
    pricing = client.control_plane.pricing
    model_key = "openai:itest-model"
    created = pricing.set(
        SetPricingRequest(model_key=model_key, input_price_per_million=1.0, output_price_per_million=2.0)
    )
    assert created.model_key == model_key

    assert any(p.model_key == model_key for p in pricing.list())
    assert pricing.get(model_key).model_key == model_key
    assert pricing.get_history(model_key) is not None

    pricing.delete(model_key)
    with pytest.raises(NotFoundException):
        pricing.get(model_key)


def test_usage_is_readable(client: OtariClient) -> None:
    # Fresh gateway: usage list is readable, proving the typed GET works through the client.
    assert client.control_plane.usage.list() is not None


def test_raw_escape_hatch_reaches_generated_methods(client: OtariClient) -> None:
    # The generator-derived methods stay reachable via ``raw`` as an escape hatch.
    keys = client.control_plane.keys
    created = keys.raw.create_key_v1_keys_post(CreateKeyRequest(key_name="itest-raw-key"))
    assert created.id
    assert any(k.id == created.id for k in keys.raw.list_keys_v1_keys_get())
    keys.raw.delete_key_v1_keys_key_id_delete(created.id)


def test_control_plane_requires_admin_credential(gateway_url: str) -> None:
    from otari import OtariError

    no_admin = OtariClient(api_base=gateway_url, api_key="some-virtual-key")
    with pytest.raises(OtariError):
        _ = no_admin.control_plane
