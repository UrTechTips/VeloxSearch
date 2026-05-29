from app.utils.dependencies_utils import get_apikey, get_current_user, get_dataset_id_from_apikey, get_dataset_id_from_apikey_hash
import pytest
from fastapi.testclient import TestClient
from app.main import app
import jwt
from app.core.jwt_config import JWT_ALGORITHM, JWT_SECRET

@pytest.fixture
def valid_apikey():
    with TestClient(app) as client:
        with open("test_api_key.txt", "r") as f:
            api_key = f.read().strip()
        yield client, api_key

def test_get_apikey(valid_apikey):
    # get_apikey takes a header and a request
    client, api_key = valid_apikey
    client.headers = {"authorization": f"Bearer {api_key}"}
    request = client.build_request("GET", "/search")
    assert get_apikey(client.headers["authorization"], request) == api_key


    # Test with an invalid API key
    invalid_apikey = "invalid_api_key"
    client.headers = {"authorization": f"Bearer {invalid_apikey}"}
    try:
        get_apikey(client.headers["authorization"], request)
        assert False, "Expected an exception for invalid API key"
    except Exception as e:
        assert str(e) == "Invalid API key"

def test_get_current_user(valid_apikey):
    client, _ = valid_apikey
    token = jwt.encode({"user_id": "SomeUserId"}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    client.headers = {"authorization": f"Bearer {token}"}
    user_id = get_current_user(client.headers["authorization"])
    assert user_id is not None
    assert user_id == "SomeUserId"

    # Test with an invalid API key
    invalid_apikey = "invalid_api_key"
    client.headers = {"authorization": f"Bearer {invalid_apikey}"}
    try:
        get_current_user(client.headers["authorization"])
        assert False, "Expected an exception for invalid API key"
    except Exception as e:
        assert str(e) == "401: Invalid token"