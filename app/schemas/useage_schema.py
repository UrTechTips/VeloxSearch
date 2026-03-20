schema = {
    "fields": [
        "id",
        "apikey_id",
        "endpoint",
        "latency",
        "query_hash"
    ],
    "types": {
        "id": "TEXT",
        "apikey_id": "TEXT",
        "endpoint": "TEXT",
        "latency": "REAL",
        "query_hash": "TEXT"
    },
    "primary_key": "id",
    "required_fields": ["id", "apikey_id", "endpoint", "latency", "query_hash"],
    "optional_fields": [],
    "unique_fields": ["id"],
    "foreign_keys": [
        {
            "field": "apikey_id",
            "reference_table": "apikeys",
            "reference_field": "apikey_id"
        }
    ]
}