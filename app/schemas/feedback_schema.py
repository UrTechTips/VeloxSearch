schema = {
    "fields": [
        "dataset_id",
        "query_hash",
        "clicked_doc_id",
        "position",
    ],
    "types": {
        "dataset_id": "TEXT",
        "query_hash": "TEXT",
        "clicked_doc_id": "TEXT",
        "position": "INTEGER",
    },
    "primary_key": "dataset_id",
    "required_fields": ["dataset_id", "query_hash", "clicked_doc_id", "position"],
    "optional_fields": [],
    "unique_fields": ["dataset_id", "query_hash", "clicked_doc_id"],
    "foreign_keys": [
        {
            "field": "dataset_id",
            "reference_table": "datasets",
            "reference_field": "dataset_id"
        }
    ]
}