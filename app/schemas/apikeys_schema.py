schema = {
    "fields": [
        "id",
        "owner_id",
        "hashed_key",
        "scopes",
        "rate_limit",
        "expires_at",
        "created_at",
    ],
    "types": {
        "id": "TEXT",
        "owner_id": "TEXT",
        "hashed_key": "TEXT",
        "scopes": "TEXT", # TODO: Change to JSON when switching database
        "rate_limit": "INTEGER",
        "expires_at": "TIMESTAMP",
        "created_at": "TIMESTAMP",
    },
    "primary_key": "id",
    "required_fields": ["id", "owner_id", "hashed_key", "scopes", "rate_limit", "expires_at", "created_at"],
    "optional_fields": [],
    "unique_fields": ["id"],
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "id"
        }
    ]
}