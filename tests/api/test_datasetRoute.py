import json
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def setup_cleanup():
    with TestClient(app) as client:
        yield client
    # Cleanup after tests
    # Delete from sqlite 
    from app.db import service as database_service
    database_service.delete_dataset("test_dataset_id", "test_user")

def test_read_dataset(setup_cleanup):
    client = setup_cleanup
    response = client.get("/dataset/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the dataset route!"}

def test_create_dataset(setup_cleanup):
    client = setup_cleanup
    payload = {
        "user_id": "test_user",
        "database_name": "test_db",
        "description": "Test dataset"
    }

    response = client.post("/dataset/create", json=payload)
    assert response.status_code == 200
    assert "dataset_id" in response.json()
    assert response.json()["message"] == "Dataset created successfully!"

def test_upload_dataset(setup_cleanup):
    client = setup_cleanup
    dataset_id = "test_dataset_id"
    file_content = {"data": "test data"}
    
    response = client.post(
        "/dataset/upload",
        data={"id": dataset_id},
        files={"file": ("test_file.json", json.dumps(file_content), "application/json")}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Dataset uploaded successfully!"

def test_upload_config(setup_cleanup):
    client = setup_cleanup
    dataset_id = "test_dataset_id"
    config = {
        "searchable_fields": ["field1", "field2"],
        "vector_terms": ["term1", "term2"],
        "length": 100,
        "id_field": "id"
    }
    
    response = client.post(
        "/dataset/config",
        json={"id": dataset_id, "config": json.dumps(config)}
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["message"] == "Config uploaded successfully!"