import json
from typing import Dict, Optional, Tuple, List, Any

def schema_to_create_table_sql(table_name: str, schema: Dict) -> str:
    """
    Generate SQL for creating a table based on its schema.

    Args:
        table_name: The name of the table to create.
        schema: The schema definition of the table.
    Returns:
        A string containing the SQL create table statement.
    """
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
        
        if schema.get("auto_increment") == field:
            parts.append("AUTOINCREMENT")

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

def _format_sql_value(value: Any) -> str:
    """Get the input value as a string formatted for SQL insertion.

    Args:
        value (Any[str, int, bool, Dict]): The value to format.

    Returns:
        str: The formatted value as a string.
    """
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return f"{value}"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (dict, list)):
        return f"{json.dumps(value)}"
    return str(value)

def schema_to_insert_sql(table_name: str, schema: Dict, **values) -> Optional[Tuple[str, Tuple]]:
    """
    Generate SQL for inserting a new row into a table based on its schema.

    Args:
        table_name: The name of the table to insert into.
        schema: The schema definition of the table.
        **values: The values to insert, as keyword arguments.

    Returns:
        A tuple containing the SQL insert statement and a tuple of values to insert, or None if no values are provided.

    Raises:
        ValueError: If any provided field is not defined in the schema.
    """
    if not values:
        return None

    all_fields = set(schema.get("fields", []))
    for field in values.keys():
        if field not in all_fields:
            raise ValueError(f"Field '{field}' is not defined in the schema for table '{table_name}'")

    fields = ", ".join(values.keys())
    placeholders = ", ".join(["?"] * len(values))

    insert_str = f"""
    INSERT INTO {table_name} ({fields})
    VALUES ({placeholders});
    """

    data_values = tuple(_format_sql_value(v) for v in values.values())

    return insert_str.strip(), data_values

def schema_to_update_sql(table_name: str, schema: Dict, where_clause: str, where_values: Tuple, **values) -> Optional[Tuple[str, Tuple]]:
    """
    Generate SQL for updating rows in a table based on its schema.

    Args:
        table_name: The name of the table to update.
        schema: The schema definition of the table.
        where_clause: The WHERE clause to specify which rows to update (without the 'WHERE' keyword).
        where_values: A tuple of values for the WHERE clause.
        **values: The values to update, as keyword arguments.

    Returns:
        A tuple containing the SQL update statement and a tuple of values to update, or None if no values are provided.

    Raises:
        ValueError: If any provided field is not defined in the schema.
    """
    if not values:
        return None

    all_fields = set(schema.get("fields", []))
    for field in values.keys():
        if field not in all_fields:
            raise ValueError(f"Field '{field}' is not defined in the schema for table '{table_name}'")

    set_clauses = ", ".join([f"{field} = ?" for field in values.keys()])
    update_str = f"""
    UPDATE {table_name}
    SET {set_clauses}
    WHERE {where_clause};
    """

    data_values = tuple(_format_sql_value(v) for v in values.values()) + where_values

    return update_str.strip(), data_values