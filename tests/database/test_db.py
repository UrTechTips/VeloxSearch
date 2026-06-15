import sqlite3

import pytest

from app.db.database import DatabaseService
from app.db.manager import DatabaseManager

from app import schemas
from app.utils.schema_utils import schema_to_create_table_sql

@pytest.fixture()
def db_service(tmp_path):
    db_path = tmp_path / "db_service_test.sqlite3"
    db_manager = DatabaseManager(str(db_path))

    with db_manager as conn:
        cursor = conn.cursor()
        cursor.execute(schema_to_create_table_sql("users", schemas.user_schema))
        cursor.execute(schema_to_create_table_sql("datasets", schemas.dataset_schema))
        cursor.execute(schema_to_create_table_sql("apikeys", schemas.apikey_schema))
        cursor.execute(schema_to_create_table_sql("usage", schemas.usage_schema))
        cursor.execute(schema_to_create_table_sql("feedback", schemas.feedback_schema))
    return DatabaseService(db_manager)


def test_insert_and_get_user_metadata(db_service):
    inserted = db_service.insert_user(
        "user_1",
        name="Alice",
        email="alice@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=0,
    )

    assert inserted is True

    metadata = db_service.get_user_metadata("user_1")
    assert metadata == {
        "metadata": {
            "id": "user_1",
            "name": "Alice",
            "email": "alice@example.com",
            "created_at": "2026-01-01 10:00:00",
            "datasets_count": 0,
        }
    }


def test_get_nonexistent_user_metadata_returns_none(db_service):
    assert db_service.get_user_metadata("missing-user") is None


def test_insert_and_get_dataset_metadata(db_service):
    db_service.insert_user(
        "owner_1",
        name="Owner",
        email="owner@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=1,
    )

    inserted = db_service.insert_dataset(
        "dataset_1",
        "owner_1",
        name="Dataset One",
        description="Test dataset",
        length=123,
        index_status="ready",
        created_at="2026-01-01 10:01:00",
        updated_at="2026-01-01 10:01:00",
    )

    assert inserted is True

    metadata = db_service.get_dataset_metadata("dataset_1")
    assert metadata == {
        "metadata": {
            "id": "dataset_1",
            "owner_id": "owner_1",
            "name": "Dataset One",
            "description": "Test dataset",
            "length": 123,
            "index_status": "ready",
            "created_at": "2026-01-01 10:01:00",
            "updated_at": "2026-01-01 10:01:00",
        }
    }


def test_get_nonexistent_dataset_metadata_returns_none(db_service):
    assert db_service.get_dataset_metadata("missing-dataset") is None


def test_insert_duplicate_dataset_returns_false(db_service):
    db_service.insert_user(
        "owner_2",
        name="Owner 2",
        email="owner2@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=1,
    )

    first = db_service.insert_dataset(
        "dup_dataset",
        "owner_2",
        name="Duplicate",
        description="first insert",
        length=1,
        index_status="ready",
        created_at="2026-01-01 10:01:00",
        updated_at="2026-01-01 10:01:00",
    )
    second = db_service.insert_dataset(
        "dup_dataset",
        "owner_2",
        name="Duplicate",
        description="second insert",
        length=2,
        index_status="ready",
        created_at="2026-01-01 10:02:00",
        updated_at="2026-01-01 10:02:00",
    )

    assert first is True
    assert second is False


def test_insert_and_validate_apikey(db_service):
    db_service.insert_user(
        "api_owner",
        name="API Owner",
        email="apiowner@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=0,
    )

    inserted = db_service.insert_apikey(
        "key_1",
        "api_owner",
        hashed_key="hashed-1",
        scopes="search:read",
        rate_limit=60,
        expires_at="2027-01-01 00:00:00",
        created_at="2026-01-01 10:00:00",
    )

    assert inserted is True
    assert db_service.validate_apikey("api_owner", "hashed-1") is True
    assert db_service.validate_apikey("api_owner", "missing-hash") is False


def test_insert_usage_success_and_missing_hash(db_service):
    db_service.insert_user(
        "usage_owner",
        name="Usage Owner",
        email="usageowner@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=0,
    )
    db_service.insert_apikey(
        "key_usage",
        "usage_owner",
        hashed_key="usage-hash",
        scopes="search:read",
        rate_limit=100,
        expires_at="2027-01-01 00:00:00",
        created_at="2026-01-01 10:00:00",
    )

    ok = db_service.insert_usage(
        "usage_1",
        "usage-hash",
        endpoint="/api/v1/search",
        latency=12.5,
        query_hash="q1",
        created_at="2026-01-01 10:00:05",
    )
    missing = db_service.insert_usage(
        "usage_2",
        "unknown-hash",
        endpoint="/api/v1/search",
        latency=10.0,
        query_hash="q2",
        created_at="2026-01-01 10:00:06",
    )

    assert ok is True
    assert missing is False


def test_get_apikey_usage_rate_and_quota(db_service):
    db_service.insert_user(
        "quota_owner",
        name="Quota Owner",
        email="quotaowner@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=0,
    )
    db_service.insert_apikey(
        "key_quota",
        "quota_owner",
        hashed_key="quota-hash",
        scopes="search:read",
        rate_limit=100,
        expires_at="2027-01-01 00:00:00",
        created_at="2026-01-01 10:00:00",
    )

    manager = db_service.db_manager
    with manager as conn:
        cursor = conn.cursor()
        apikey_id = cursor.execute(
            "SELECT id FROM apikeys WHERE hashed_key = ?",
            ("quota-hash",),
        ).fetchone()[0]

        cursor.execute(
            """
            INSERT INTO usage (id, apikey_id, endpoint, latency, query_hash, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            ("rate_now_1", apikey_id, "/api/v1/search", 8.2, "qn1"),
        )
        cursor.execute(
            """
            INSERT INTO usage (id, apikey_id, endpoint, latency, query_hash, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-30 seconds'))
            """,
            ("rate_now_2", apikey_id, "/api/v1/search", 7.9, "qn2"),
        )
        cursor.execute(
            """
            INSERT INTO usage (id, apikey_id, endpoint, latency, query_hash, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '-2 minutes'))
            """,
            ("rate_old_1", apikey_id, "/api/v1/search", 15.0, "qo1"),
        )
        conn.commit()

    rate = db_service.get_apikey_usagerate("quota-hash")
    quota = db_service.get_apikey_usagequota("quota-hash")

    assert rate == 2
    assert quota == 3


def test_get_apikey_usage_rate_and_quota_return_none_for_unknown_hash(db_service):
    assert db_service.get_apikey_usagerate("missing-hash") is None
    assert db_service.get_apikey_usagequota("missing-hash") is None


def test_insert_feedback(db_service):
    db_service.insert_user(
        "feedback_owner",
        name="Feedback Owner",
        email="feedback@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=1,
    )
    db_service.insert_dataset(
        "feedback_dataset",
        "feedback_owner",
        name="Feedback Dataset",
        description="for feedback",
        length=50,
        index_status="ready",
        created_at="2026-01-01 10:00:00",
        updated_at="2026-01-01 10:00:00",
    )

    inserted = db_service.insert_feedback(
        "feedback_1",
        "feedback_dataset",
        query_hash="q-feedback",
        clicked_doc_id="doc-1",
        position=1,
    )

    assert inserted is True

    with db_service.db_manager as conn:
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT id, dataset_id, query_hash, clicked_doc_id, position FROM feedback WHERE id = ?",
            ("feedback_1",),
        ).fetchone()

    assert dict(row) == {
        "id": "feedback_1",
        "dataset_id": "feedback_dataset",
        "query_hash": "q-feedback",
        "clicked_doc_id": "doc-1",
        "position": 1,
    }


# @pytest.mark.xfail(
#     raises=ValueError,
#     reason="DatabaseService.list_datasets uses dict(row) on tuple rows; requires sqlite3.Row row_factory or explicit mapping",
# )
def test_list_datasets_for_user_returns_items(db_service):
    db_service.insert_user(
        "list_owner",
        name="List Owner",
        email="listowner@example.com",
        created_at="2026-01-01 10:00:00",
        datasets_count=2,
    )
    db_service.insert_dataset(
        "list_ds_1",
        "list_owner",
        name="List One",
        description="first",
        length=10,
        index_status="ready",
        created_at="2026-01-01 10:00:00",
        updated_at="2026-01-01 10:00:00",
    )
    db_service.insert_dataset(
        "list_ds_2",
        "list_owner",
        name="List Two",
        description="second",
        length=20,
        index_status="ready",
        created_at="2026-01-01 10:01:00",
        updated_at="2026-01-01 10:01:00",
    )

    result = db_service.list_datasets("list_owner")

    assert "datasets" in result
    assert len(result["datasets"]) == 2
    dataset_ids = {row["id"] for row in result["datasets"]}
    assert dataset_ids == {"list_ds_1", "list_ds_2"}

def test_update_dataset_index_status(db_service):
    db_service.insert_user(
        "update_owner",
        name="Update Owner",
        email="updateowner@example.com",
    )
    db_service.insert_dataset(
        "update_ds",
        "update_owner",
        name="Update Dataset",
        description="for update test",
        length=5,
        index_status="pending",
    )
    db_service.update_dataset_index_status("update_ds", "update_owner", "ready")
    metadata = db_service.get_dataset_metadata("update_ds")
    assert metadata["metadata"]["index_status"] == "ready"