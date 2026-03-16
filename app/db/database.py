from typing import Optional, Dict
from app.db.manager import DatabaseManager
from app.schemas.datasets_schema import schema as dataset_schema
from app.schemas.user_schema import schema as user_schema

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
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                fields = ", ".join(dataset_schema['fields'])
                placeholders = ", ".join(["?"] * len(dataset_schema['fields']))
                values = [dataset_id, user_id] + [kwargs.get(field) for field in dataset_schema['fields'] if field not in ["dataset_id", "user_id"]]
                cursor.execute(
                    f"INSERT INTO datasets ({fields}) VALUES ({placeholders})",
                    tuple(values)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting dataset: {e}")
                return False
            
    def insert_user(self, user_id: str, **kwargs) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                fields = ", ".join(user_schema['fields'])
                placeholders = ", ".join(["?"] * len(user_schema['fields']))
                values = [user_id] + [kwargs.get(field) for field in user_schema['fields'] if field != "user_id"]
                cursor.execute(
                    f"INSERT INTO users ({fields}) VALUES ({placeholders})",
                    tuple(values)
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting user: {e}")
                return False