schema = {
    "fields": [
        "id",
        "dataset_id",
        "query_hash",
        "clicked_doc_id",
        "position",
    ],
    "types": {
        "id": "INTEGER",
        "dataset_id": "TEXT",
        "query_hash": "TEXT",
        "clicked_doc_id": "TEXT",
        "position": "INTEGER",
    },
    "primary_key": "id",
    "required_fields": ["id", "dataset_id", "query_hash", "clicked_doc_id", "position"],
    "optional_fields": [],
    "unique_fields": ["id", "dataset_id", "query_hash", "clicked_doc_id"],
    "auto_increment": "id",
    "foreign_keys": [
        {
            "field": "dataset_id",
            "reference_table": "datasets",
            "reference_field": "id"
        }
    ]
}