schema = {
    "fields": [
        "id",
        "owner_id",
        "dataset_id",
        "hashed_key",
        "scopes",
        "rate_limit",
        "is_active",
        "expires_at",
        "created_at",
    ],
    "types": {
        "id": "TEXT",
        "owner_id": "TEXT",
        "dataset_id": "TEXT",
        "hashed_key": "TEXT",
        "scopes": "TEXT", # TODO: Change to JSON when switching database
        "is_active": "BOOLEAN",
        "rate_limit": "INTEGER",
        "expires_at": "TIMESTAMP",
        "created_at": "TIMESTAMP",
    },
    "primary_key": "id",
    "required_fields": ["id", "owner_id", "dataset_id", "hashed_key", "rate_limit", "is_active", "created_at"],
    "optional_fields": ["scopes", "expires_at"],
    "unique_fields": ["id"],
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "id"
        },
        {
            "field": "dataset_id",
            "reference_table": "datasets",
            "reference_field": "id"
        }
    ]
}