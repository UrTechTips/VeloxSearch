import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.apikeyRouter import (
    deactivate_apikey,
    generate_apikey,
    router,
)
from app.utils.dependencies_utils import get_current_user


@pytest.fixture()
def test_app():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    return app


@pytest.fixture()
def client(test_app):
    with TestClient(test_app) as test_client:
        yield test_client


def test_router_has_expected_prefix_and_tag():
    assert router.prefix == "/apikey"
    assert "apikey" in router.tags


def test_generate_apikey_direct_call_returns_created_response(monkeypatch):
    calls = {}

    def fake_generate_key(user_id, dataset_id):
        calls["user_id"] = user_id
        calls["dataset_id"] = dataset_id
        return "apikey-abc123"

    monkeypatch.setattr("app.routers.apikeyRouter.generate_key", fake_generate_key)

    response = generate_apikey(dataset_id="dataset-1", user_id="user-42")

    assert response.status_code == 201
    assert response.body == b"apikey-abc123"
    assert response.media_type == "text/plain"
    assert calls == {"user_id": "user-42", "dataset_id": "dataset-1"}


def test_deactivate_apikey_direct_call_returns_ok_on_success(monkeypatch):
    calls = {}

    def fake_deactivate_key(api_key):
        calls["api_key"] = api_key
        return True

    monkeypatch.setattr("app.routers.apikeyRouter.deactivate_key", fake_deactivate_key)

    response = deactivate_apikey(api_key="key-xyz", user_id="user-42")

    assert response.status_code == 200
    assert response.body == b"API key deactivated successfully!"
    assert response.media_type == "text/plain"
    assert calls == {"api_key": "key-xyz"}


def test_deactivate_apikey_direct_call_returns_bad_request_on_failure(monkeypatch):
    def fake_deactivate_key(api_key):
        return False

    monkeypatch.setattr("app.routers.apikeyRouter.deactivate_key", fake_deactivate_key)

    response = deactivate_apikey(api_key="key-xyz", user_id="user-42")

    assert response.status_code == 400
    assert response.body == b"Failed to deactivate API key!"
    assert response.media_type == "text/plain"


def test_generate_apikey_endpoint_returns_created_and_plain_text(client, monkeypatch):
    calls = {}

    def fake_generate_key(user_id, dataset_id):
        calls["user_id"] = user_id
        calls["dataset_id"] = dataset_id
        return "generated-key-001"

    monkeypatch.setattr("app.routers.apikeyRouter.generate_key", fake_generate_key)

    response = client.post("/apikey/generate", params={"dataset_id": "dataset-1"})

    assert response.status_code == 201
    assert response.text == "generated-key-001"
    assert response.headers["content-type"].startswith("text/plain")
    assert calls == {"user_id": "user-123", "dataset_id": "dataset-1"}


def test_deactivate_apikey_endpoint_returns_ok_when_successful(client, monkeypatch):
    calls = {}

    def fake_deactivate_key(api_key):
        calls["api_key"] = api_key
        return True

    monkeypatch.setattr("app.routers.apikeyRouter.deactivate_key", fake_deactivate_key)

    response = client.post("/apikey/deactivate", params={"api_key": "key-123"})

    assert response.status_code == 200
    assert response.text == "API key deactivated successfully!"
    assert response.headers["content-type"].startswith("text/plain")
    assert calls == {"api_key": "key-123"}


def test_deactivate_apikey_endpoint_returns_bad_request_when_failed(client, monkeypatch):
    def fake_deactivate_key(api_key):
        return False

    monkeypatch.setattr("app.routers.apikeyRouter.deactivate_key", fake_deactivate_key)

    response = client.post("/apikey/deactivate", params={"api_key": "key-123"})

    assert response.status_code == 400
    assert response.text == "Failed to deactivate API key!"
    assert response.headers["content-type"].startswith("text/plain")


def test_generate_apikey_endpoint_uses_query_parameter(client, monkeypatch):
    received = {}

    def fake_generate_key(user_id, dataset_id):
        received["user_id"] = user_id
        received["dataset_id"] = dataset_id
        return "ok"

    monkeypatch.setattr("app.routers.apikeyRouter.generate_key", fake_generate_key)

    response = client.post("/apikey/generate", params={"dataset_id": "ds-query-test"})

    assert response.status_code == 201
    assert received["dataset_id"] == "ds-query-test"
    assert received["user_id"] == "user-123"


def test_deactivate_apikey_endpoint_uses_query_parameter(client, monkeypatch):
    received = {}

    def fake_deactivate_key(api_key):
        received["api_key"] = api_key
        return True

    monkeypatch.setattr("app.routers.apikeyRouter.deactivate_key", fake_deactivate_key)

    response = client.post("/apikey/deactivate", params={"api_key": "query-key"})

    assert response.status_code == 200
    assert received["api_key"] == "query-key"