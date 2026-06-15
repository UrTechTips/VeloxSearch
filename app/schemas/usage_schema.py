schema = {
    "fields": [
        "id",
        "apikey_id",
        "endpoint",
        "latency",
        "query_hash",
        "created_at"
    ],
    "types": {
        "id": "INTEGER",
        "apikey_id": "TEXT",
        "endpoint": "TEXT",
        "latency": "REAL",
        "query_hash": "TEXT",
        "created_at": "TIMESTAMP"
    },
    "primary_key": "id",
    "required_fields": ["id", "apikey_id", "endpoint", "latency", "query_hash", "created_at"],
    "optional_fields": [],
    "unique_fields": ["id"],
    "auto_increment": "id",
    "foreign_keys": [
        {
            "field": "apikey_id",
            "reference_table": "apikeys",
            "reference_field": "id"
        }
    ]
}