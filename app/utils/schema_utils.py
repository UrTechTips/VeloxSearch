import json
from typing import Dict, Optional

def schema_to_create_table_sql(table_name: str, schema: Dict) -> str:
    primary_key = schema.get("primary_key")
    required = set(schema.get("required_fields", []))
    unique = set(schema.get("unique_fields", []))
    foreign_keys = schema.get("foreign_keys", [])
    types = schema.get("types", {})
    fields = schema.get("fields", [])

    column_defs = []

    for field in fields:
        parts = [field, types.get(field, "TEXT")]

        if field == primary_key:
            parts.append("PRIMARY KEY")

        if field in required:
            parts.append("NOT NULL")

        if field in unique and field != primary_key:
            parts.append("UNIQUE")

        column_defs.append(" ".join(parts))

    fk_defs = [
        f"FOREIGN KEY ({fk['field']}) REFERENCES {fk['reference_table']}({fk['reference_field']})"
        for fk in foreign_keys
    ]

    all_defs = column_defs + fk_defs

    create_str = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {", ".join(all_defs)}
    );
    """

    return create_str.strip()

def format_sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return f"'{value}'"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (dict, list)):
        return f"'{json.dumps(value)}'"
    return str(value)

def schema_to_insert_sql(table_name: str, schema: Dict, **values) -> Optional[str]:
    if not values:
        return None

    fields = []
    formatted_values = []

    for field, value in values.items():
        fields.append(field)
        formatted_values.append(format_sql_value(value))

    insert_str = f"""
    INSERT INTO {table_name} ({", ".join(fields)})
    VALUES ({", ".join(formatted_values)});
    """

    return insert_str.strip()