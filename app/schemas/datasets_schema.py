schema = {
    "fields": [
        "dataset_id",
        "owner_id",
        "name",
        "description",
        "length",
        "index_status",
        "created_at",
        "updated_at"
    ],
    "types": {
        "dataset_id": "TEXT",
        "owner_id": "TEXT",
        "name": "TEXT",
        "description": "TEXT",
        "length": "INTEGER",
        "index_status": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP"
    },
    "primary_key": "dataset_id",
    "required_fields": ["dataset_id", "owner_id", "name", "description", "length", "index_status", "created_at", "updated_at"],
    "optional_fields": [],
    "unique_fields": ["dataset_id", "name"],
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "user_id"
        }
    ]
}