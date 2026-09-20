import os
import sqlite3
from supabase import create_client, Client

class DatabaseManager:
    def __init__(self, db_name: str):
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def __enter__(self):
        """Allows use of 'with DatabaseManager(name) as conn:'"""
        return self.supabase

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass