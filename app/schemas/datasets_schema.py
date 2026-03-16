schema = {
    "fields": [
        "dataset_id",
        "user_id",
        "name",
        "description",
        "length",
        "created_at",
        "updated_at"
    ],
    "types": {
        "dataset_id": "TEXT",
        "user_id": "TEXT",
        "name": "TEXT",
        "description": "TEXT",
        "length": "INTEGER",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP"
    },
    "primary_key": "dataset_id",
    "required_fields": ["dataset_id", "user_id", "name", "description", "length", "created_at", "updated_at"],
    "optional_fields": [],
    "unique_fields": ["dataset_id", "name"],
    "foreign_keys": ["user_id"]
}