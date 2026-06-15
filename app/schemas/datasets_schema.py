schema = {
    "fields": [
        "id",
        "owner_id",
        "name",
        "description",
        "length",
        "index_status",
        "plan",
        "created_at",
        "updated_at"
    ],
    "types": {
        "id": "TEXT",
        "owner_id": "TEXT",
        "name": "TEXT",
        "description": "TEXT",
        "length": "INTEGER",
        "index_status": "TEXT",
        "plan": "TEXT",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP"
    },
    "primary_key": "id",
    "required_fields": ["id", "owner_id", "name", "length", "index_status", "plan", "created_at", "updated_at"],
    "optional_fields": ["description"],
    "unique_fields": ["id", "name"],
    "auto_increment": "",
    "foreign_keys": [
        {
            "field": "owner_id",
            "reference_table": "users",
            "reference_field": "id"
        }
    ]
}