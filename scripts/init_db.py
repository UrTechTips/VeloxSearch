from app.db.manager import DatabaseManager
from app.utils.schema_utils import schema_to_create_table_sql
from app.schemas.user_schema import schema as user_schema
from app.schemas.usage_schema import schema as usage_schema
from app.schemas.apikeys_schema import schema as apikeys_schema
from app.schemas.datasets_schema import schema as dataset_schema
from app.schemas.feedback_schema import schema as feedback_schema
from app.core import DATABASE_NAME

def init_db():
    db_manager = DatabaseManager(DATABASE_NAME)
    with db_manager as conn:
        cursor = conn.cursor()
        cursor.execute(schema_to_create_table_sql("users", user_schema))
        cursor.execute(schema_to_create_table_sql("datasets", dataset_schema))
        cursor.execute(schema_to_create_table_sql("apikeys", apikeys_schema))
        cursor.execute(schema_to_create_table_sql("feedback", feedback_schema))
        cursor.execute(schema_to_create_table_sql("usage", usage_schema))
        conn.commit()

if __name__ == "__main__":
    init_db()