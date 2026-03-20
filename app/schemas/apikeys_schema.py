schema = {
    "fields": [
        "apikey_id",
        "owner_id",
        "key_id",
        "hashed_key",
        "scopes",
        "rate_limit",
        "expires_at",
        "created_at",
    ],
    "types": {
        "apikey_id": "TEXT",
        "owner_id": "TEXT",
        "key_id": "TEXT",
        "hashed_key": "TEXT",
        "scopes": "TEXT", # TODO: Change to JSON when switching database
        "rate_limit": "INTEGER",
        "expires_at": "TIMESTAMP",
        "created_at": "TIMESTAMP",
    },
    "primary_key": "apikey_id",
    "required_fields": ["apikey_id", "owner_id", "key_id", "hashed_key", "scopes", "rate_limit", "expires_at", "created_at"],
    "optional_fields": [],
    "unique_fields": ["apikey_id", "key_id"],
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "user_id"
        }
    ]
}