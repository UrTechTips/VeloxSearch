import sqlite3
from typing import Optional, Dict

from app.db.manager import DatabaseManager

class DatasetService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_metadata(self, dataset_id: str) -> Optional[Dict]:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE dataset_id = ?", (dataset_id,))
            result = cursor.fetchone()
            return {"metadata": result[0]} if result else None