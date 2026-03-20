import sqlite3

class DatabaseManager:
    def __init__(self, db_name: str):
        if not db_name:
            raise ValueError("Database name cannot be empty")
        self.db_name = db_name

    def __enter__(self):
        """Allows use of 'with DatabaseManager(name) as conn:'"""
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access to rows
            return self.connection
        except sqlite3.Error as e:
            raise ConnectionError(f"Database connection failed: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'connection'):
            self.connection.close()