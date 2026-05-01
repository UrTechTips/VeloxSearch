import time
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT


@pytest.fixture(autouse=True)
def setup_cleanup():
    global api_key
    with open("test_api_key.txt", "r") as f:
        api_key = f.read().strip()
    with TestClient(app) as client:
        yield client, api_key
    # Cleanup after tests
    app.state.redis_client.delete(f"rate_limit:{api_key}")
    app.state.redis_client.delete(f"quota_limit:{api_key}")

def test_rate_limiting(setup_cleanup):
    client, api_key = setup_cleanup
    for i in range(RATE_LIMIT):
        response = client.post(
            "/search/query", 
            params={"query": f"test query {i}"}, 
                headers={"Authorization": f"Bearer {api_key}"}
            )
        assert response.status_code == 200

    response = client.post(
        "/search/query", 
        params={"query": "test query exceeding limit"}, 
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 429

def test_quota_limiting(setup_cleanup):
    client, api_key = setup_cleanup
    for i in range(QUOTA_LIMIT):
        response = client.post(
            "/search/query", 
            params={"query": f"test query {i}"}, 
                headers={"Authorization": f"Bearer {api_key}"}
            )
        time.sleep(5)  # Sleep to avoid hitting rate limit before quota limit
        assert response.status_code == 200

    response = client.post(
        "/search/query", 
        params={"query": "test query exceeding quota"}, 
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 403