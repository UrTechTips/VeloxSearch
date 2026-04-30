from fastapi.testclient import TestClient
from app.main import app
from tqdm import tqdm
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT

api_key = "5c2d7abfa0f74597bafdf04262c29b4b"

# def test_rate_limiting():
#     with TestClient(app) as client:
#         for i in range(RATE_LIMIT):
#             response = client.post(
#                 "/search/query", 
#                 params={"query": f"test query {i}"}, 
#                 headers={"Authorization": f"Bearer {api_key}"}
#             )
#             assert response.status_code == 200

#         response = client.post(
#             "/search/query", 
#             params={"query": "test query exceeding limit"}, 
#             headers={"Authorization": f"Bearer {api_key}"}
#         )
#         assert response.status_code == 429

def test_quota_limiting():
    with TestClient(app) as client:
        for i in range(QUOTA_LIMIT): # Assuming QUOTA_LIMIT is 1000
            response = client.post(
                "/search/query", 
                params={"query": f"test query {i}"}, 
                headers={"Authorization": f"Bearer {api_key}"}
            )
            assert response.status_code == 200

        response = client.post(
            "/search/query", 
            params={"query": "test query exceeding quota"}, 
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code == 403