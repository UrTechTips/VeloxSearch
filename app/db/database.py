from typing import Optional, Dict
from app.db.manager import DatabaseManager
from app.schemas.datasets_schema import schema as dataset_schema
from app.schemas.user_schema import schema as user_schema
from app.utils.schema_utils import schema_to_insert_sql

class DatabaseService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,))
            result = cursor.fetchone()
            result = zip(dataset_schema['fields'], result) if result else None
            return {"metadata": dict(result)} if result else None

    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            result = zip(user_schema['fields'], result) if result else None
            return {"metadata": dict(result)} if result else None

    def list_datasets(self, user_id: str) -> Dict:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE user_id = ?", (user_id,))
            results = cursor.fetchall()
            return {"datasets": [dict(row) for row in results]}
        
    def insert_dataset(self, dataset_id: str, user_id: str, **kwargs) -> bool:
        # TODO: Validate kwargs against dataset_schema before inserting either in this file or in utils/schema_utils.py
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(schema_to_insert_sql("datasets", dataset_schema, dataset_id=dataset_id, user_id=user_id, **kwargs))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting dataset: {e}")
                return False
            
    def insert_user(self, user_id: str, **kwargs) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(schema_to_insert_sql("users", user_schema, user_id=user_id, **kwargs))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting user: {e}")
                return False