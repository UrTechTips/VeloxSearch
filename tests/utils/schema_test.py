import re
import pytest
from app.utils.schema_utils import schema_to_create_table_sql, schema_to_insert_sql, schema_to_update_sql

schema = {
    "fields": ["api_key_id", "owner_id", "key_id", "rate_limit"],
    "types": {
        "api_key_id": "TEXT",
        "owner_id": "TEXT",
        "key_id": "TEXT",
        "rate_limit": "INTEGER",
    },
    "primary_key": "api_key_id",
    "required_fields": ["api_key_id", "owner_id"],
    "unique_fields": ["key_id"],
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "id"
        }
    ]
}

def normalize_whitespace(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def test_schema_to_create_table_sql():
    expected_sql = """CREATE TABLE IF NOT EXISTS api_keys (
        api_key_id TEXT PRIMARY KEY AUTOINCREMENT NOT NULL, owner_id TEXT NOT NULL, key_id TEXT UNIQUE, rate_limit INTEGER, FOREIGN KEY (owner_id) REFERENCES users(id)
    );
    """
    assert normalize_whitespace(schema_to_create_table_sql("api_keys", schema)) == normalize_whitespace(expected_sql)

def test_empty_schema():
    empty_schema = {
        "fields": [],
        "types": {},
        "primary_key": None,
        "required_fields": [],
        "optional_fields": [],
        "unique_fields": [],
        "foreign_keys": []
    }
    expected_sql = 'CREATE TABLE IF NOT EXISTS empty_table (\n        \n    );'
    assert normalize_whitespace(schema_to_create_table_sql("empty_table", empty_schema)) == normalize_whitespace(expected_sql)

def test_schema_with_only_required_fields():
    required_schema = {
        "fields": ["id", "name"],
        "types": {"id": "TEXT", "name": "TEXT"},
        "primary_key": "id",
        "required_fields": ["id", "name"],
        "optional_fields": [],
        "unique_fields": ["id"],
        "foreign_keys": []
    }
    expected_sql = """CREATE TABLE IF NOT EXISTS required_table (
        id TEXT PRIMARY KEY AUTOINCREMENT NOT NULL, name TEXT NOT NULL
    );
    """
    assert normalize_whitespace(schema_to_create_table_sql("required_table", required_schema)) == normalize_whitespace(expected_sql)

def test_schema_to_insert_sql():
    expected_sql = """INSERT INTO api_keys (api_key_id, owner_id, key_id, rate_limit)
    VALUES (?, ?, ?, ?);
"""
    expected_values = ('ak_1', 'user_1', 'key_123', '100')
    actual_sql, actual_params = schema_to_insert_sql("api_keys", schema, api_key_id='ak_1', owner_id='user_1', key_id='key_123', rate_limit=100)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == expected_values
    
def test_insert_sql_with_json():
    expected_sql = """INSERT INTO api_keys (api_key_id, owner_id, key_id, rate_limit)
    VALUES (?, ?, ?, ?);
"""
    expected_values = ('ak_2', 'user_2', 'key_456', '500')
    actual_sql, actual_params = schema_to_insert_sql("api_keys", schema, api_key_id='ak_2', owner_id='user_2', key_id='key_456', rate_limit=500)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == expected_values

def test_insert_with_null():
    expected_sql = """INSERT INTO api_keys (api_key_id, owner_id, rate_limit)
    VALUES (?, ?, ?);
"""
    expected_values = ('ak_3', 'NULL', '200')
    actual_sql, actual_params = schema_to_insert_sql("api_keys", schema, api_key_id='ak_3', owner_id=None, rate_limit=200)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == expected_values

# Update sql tests
def test_schema_to_update_sql():
    expected_sql = """UPDATE api_keys SET owner_id = ?, key_id = ?, rate_limit = ? WHERE api_key_id = ?;
"""
    actual_sql, actual_params = schema_to_update_sql("api_keys", schema, "api_key_id = ?", ('ak_1',), owner_id='user_3', key_id='key_789', rate_limit=300)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == ('user_3', 'key_789', '300', 'ak_1')

def test_update_sql_with_json():
    expected_sql = """UPDATE api_keys SET owner_id = ?, key_id = ?, rate_limit = ? WHERE api_key_id = ?;
"""
    actual_sql, actual_params = schema_to_update_sql("api_keys", schema, "api_key_id = ?", ('ak_2',), owner_id='user_4', key_id='key_101', rate_limit=400)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == ('user_4', 'key_101', '400', 'ak_2')

def test_update_with_null():
    expected_sql = """UPDATE api_keys SET owner_id = ?, key_id = ?, rate_limit = ? WHERE api_key_id = ?;
"""
    actual_sql, actual_params = schema_to_update_sql("api_keys", schema, "api_key_id = ?", ('ak_3',), owner_id=None, key_id='key_102', rate_limit=500)
    assert normalize_whitespace(actual_sql) == normalize_whitespace(expected_sql)
    assert actual_params == ('NULL', 'key_102', '500', 'ak_3')