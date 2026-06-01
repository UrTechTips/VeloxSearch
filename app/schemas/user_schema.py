schema = {
    "fields": [
        "id",
        "name",
        "email",
        "created_at",
        "datasets_count"
    ],
    "types": {
        "id": "TEXT",
        "name": "TEXT",
        "email": "TEXT",
        "created_at": "TIMESTAMP",
        "datasets_count": "INTEGER"
    },
    "primary_key": "id",
    "required_fields": ["id", "name", "email", "created_at", "datasets_count"],
    "optional_fields": [],
    "unique_fields": ["id", "email"],
    "auto_increment": "",
    "foreign_keys": []
}