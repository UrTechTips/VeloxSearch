schema = {
    "fields": [
        "user_id",
        "name",
        "email",
        "created_at",
        "datasets_count"
    ],
    "types": {
        "user_id": "TEXT",
        "name": "TEXT",
        "email": "TEXT",
        "created_at": "TIMESTAMP",
        "datasets_count": "INTEGER"
    },
    "primary_key": "user_id",
    "required_fields": ["user_id", "name", "email", "created_at", "datasets_count"],
    "optional_fields": [],
    "unique_fields": ["user_id", "email"],
    "foreign_keys": []
}