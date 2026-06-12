from typing import Optional, Dict, List

from starlette.exceptions import HTTPException
from app.db.manager import DatabaseManager
from app.schemas import user_schema, dataset_schema, apikey_schema, usage_schema, feedback_schema
from app.utils.schema_utils import schema_to_insert_sql, schema_to_update_sql

# TODO: Add update and delete functions as well, and consider moving to separate file if this gets too large
# TODO: Modify all insert functions to validate kwargs or hardcode fields with respect to the schema

class DatabaseService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict]:
        """Get metadata for a specific dataset.

        Args:
            dataset_id (str): The ID of the dataset.

        Returns:
            Optional[Dict]: The metadata for the dataset, or None if not found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
            result = cursor.fetchone()
            result = zip(dataset_schema['fields'], result) if result else None
            return {"metadata": dict(result)} if result else None

    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        """Get metadata for a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            Optional[Dict]: The metadata for the user, or None if not found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            result = zip(user_schema['fields'], result) if result else None
            return {"metadata": dict(result)} if result else None

    def list_datasets(self, user_id: str) -> List[Dict]:
        """List all datasets for a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            List[Dict]: A list of dictionaries describing the datasets owned by the user.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE owner_id = ?", (user_id,))
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def list_apikeys(self, dataset_id: str, owner_id: str) -> List[Dict]:
        """List all API keys for a specific dataset and owner.

        Args:
            dataset_id (str): The ID of the dataset.
            owner_id (str): The ID of the owner.

        Returns:
            List[Dict]: A list of dictionaries describing the API keys for the dataset and owner.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM apikeys WHERE dataset_id = ? AND owner_id = ?", (dataset_id, owner_id))
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def validate_apikey(self, api_hashed_key: str) -> bool:
        # TODO: Do i need to add user_id to check as security??
        """Validates an API key for a specific user.

        Args:
            api_hashed_key (str): The hashed API key to validate.

        Returns:
            bool: True if the API key is valid for the user, False otherwise.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM apikeys WHERE hashed_key = ?", (api_hashed_key,))
            result = cursor.fetchone()
            return bool(result)

    def validate_dataset_id(self, dataset_id: str, user_id: str) -> bool:
        """Validates a dataset ID for a specific user.

        Args:
            dataset_id (str): The ID of the dataset to validate.
            user_id (str): The ID of the user to check ownership against.
            
        Returns:
            bool: True if the dataset ID is valid and owned by the user, False otherwise.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM datasets WHERE id = ? AND owner_id = ?", (dataset_id, user_id))
            result = cursor.fetchone()

            if not result:
                print(f"Validation failed for dataset_id: {dataset_id} and user_id: {user_id}")
                cursor.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
                dataset_exists = cursor.fetchone()
                if dataset_exists:
                    raise HTTPException(status_code=403, detail={"message": "You do not have permission to access this dataset!"})
                else:
                    raise HTTPException(status_code=404, detail={"message": "Invalid dataset ID!"})
            return bool(result)

    def get_dataset_useagerate(self, dataset_id: str) -> Optional[int]:
        """Get the usage rate for a specific dataset. Number of requests in the last minute.

        Args:
            dataset_id (str): The ID of the dataset to check usage for.

        Returns:
            Optional[int]: The usage rate for the dataset, or None if no usage found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            query = """
                SELECT COUNT(u.id) 
                FROM usage u
                JOIN apikeys a ON u.apikey_id = a.id
                WHERE a.dataset_id = ? 
                AND u.created_at >= datetime('now', '-1 minute')
            """
            cursor.execute(query, (dataset_id,))
            result = cursor.fetchone()
            
            # Note: COUNT() returns 0 if no rows match. 
            return int(result[0]) if result and result[0] > 0 else None

    def get_dataset_usagequota(self, dataset_id: str) -> Optional[int]:
        """Get the usage quota for a specific dataset. Number of requests in the last 24 hours.

        Args:
            dataset_id (str): The ID of the dataset to check usage for.

        Returns:
            Optional[int]: The usage quota for the dataset, or None if no usage found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            query = """
                SELECT COUNT(u.id) 
                FROM usage u
                JOIN apikeys a ON u.apikey_id = a.id
                WHERE a.dataset_id = ? 
                AND u.created_at >= datetime('now', 'start of day')
            """
            cursor.execute(query, (dataset_id,))
            result = cursor.fetchone()
            
            return int(result[0]) if result and result[0] > 0 else None
    
    def get_apikey_usagerate(self, api_hashed_key: str) -> Optional[int]:
        """Get the usage rate for a specific API key. Number of requests in the last minute.

        Args:
            api_hashed_key (str): The hashed API key to check usage for.

        Returns:
            Optional[int]: The usage rate for the API key, or None if no usage found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM apikeys WHERE hashed_key = ?", (api_hashed_key,))
            apikey = cursor.fetchone()
            if not apikey:
                return None
            apikey_id = apikey[0]

            cursor.execute("SELECT COUNT(*) FROM usage WHERE apikey_id = ? AND created_at >= datetime('now', '-1 minute')", (apikey_id,))
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] is not None else None

    def get_apikey_usagequota(self, api_hashed_key: str) -> Optional[int]:
        """Get the usage quota for a specific API key. Number of requests in the last 24 hours.

        Args:
            api_hashed_key (str): The hashed API key to check usage for.

        Returns:
            Optional[int]: The usage quota for the API key, or None if no usage found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM apikeys WHERE hashed_key = ?", (api_hashed_key,))
            apikey = cursor.fetchone()
            if not apikey:
                return None
            apikey_id = apikey[0]

            cursor.execute("SELECT COUNT(*) FROM usage WHERE apikey_id = ? AND created_at >= datetime('now', 'start of day')", (apikey_id,))
            result = cursor.fetchone()
            return int(result[0]) if result and result[0] is not None else None
        
    def get_dataset_id_from_apikey(self, api_hashed_key: str) -> Optional[str]:
        """Get the dataset ID associated with a specific API key.

        Args:
            api_hashed_key (str): The hashed API key to check.

        Returns:
            Optional[str]: The dataset ID associated with the API key, or None if not found.
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM apikeys WHERE hashed_key = ?", (api_hashed_key,))
            apikey = cursor.fetchone()
            if not apikey:
                return None
            dataset_id = apikey[2]
            return dataset_id

    # ID's are omitted as they are generated using AUTO_INCREMENT.
    
    def insert_dataset(self, dataset_id: str, owner_id: str, name: str, description: str = None, length: int = None, plan: str = "basic", index_status: str = "None") -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                created_at = cursor.execute("SELECT datetime('now')").fetchone()[0]
                cursor.execute(*schema_to_insert_sql("datasets", dataset_schema, id=dataset_id, owner_id=owner_id, name=name, description=description, length=length, plan=plan, index_status=index_status, created_at=created_at, updated_at=created_at))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting dataset: {e}")
                return False

    def insert_user(self, user_id: str, name: str, email: str) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                created_at = cursor.execute("SELECT datetime('now')").fetchone()[0]
                cursor.execute(*schema_to_insert_sql("users", user_schema, id=user_id, name=name, email=email, created_at=created_at, datasets_count=0))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting user: {e}")
                return False

    def insert_apikey(self, apikey_id: str, owner_id: str, dataset_id: str, name: str, is_active: bool, hashed_key: str, encrypted_key: str, rate_limit: int, quota_limit: int) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                created_at = cursor.execute("SELECT datetime('now')").fetchone()[0]
                cursor.execute(*schema_to_insert_sql("apikeys", apikey_schema, id=apikey_id, owner_id=owner_id, name=name, dataset_id=dataset_id, is_active=is_active, hashed_key=hashed_key, encrypted_key=encrypted_key, rate_limit=rate_limit, quota_limit=quota_limit, created_at=created_at))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting apikey: {e}")
                return False

    def deactivate_apikey(self, apikey_hash: str, owner_id: str) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE apikeys SET is_active = FALSE WHERE hashed_key = ? AND owner_id = ?", (apikey_hash, owner_id))
                conn.commit()
                return True
            except Exception as e:
                raise HTTPException(status_code=400, detail={"message": f"Error deactivating API key: {e}"})
            
    def insert_usage(self, apikey_hash: str, endpoint: str, latency: float, query_hash: str) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                created_at = cursor.execute("SELECT datetime('now')").fetchone()[0]
                apikey_id = cursor.execute("SELECT id FROM apikeys WHERE hashed_key = ?", (apikey_hash,)).fetchone()
                if not apikey_id:
                    print(f"Error inserting usage: No apikey found for hash {apikey_hash}")
                    return False
                apikey_id = apikey_id[0]
                cursor.execute(*schema_to_insert_sql("usage", usage_schema, apikey_id=apikey_id, endpoint=endpoint, latency=latency, query_hash=query_hash, created_at=created_at))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting usage: {e}")
                return False

    def insert_feedback(self, dataset_id: str, **kwargs) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(*schema_to_insert_sql("feedback", feedback_schema, dataset_id=dataset_id, **kwargs))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error inserting feedback: {e}")
                return False

    # Update Functions
    def update_dataset(self, dataset_id: str, owner_id: str, **kwargs) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            current_time = cursor.execute("SELECT datetime('now')").fetchone()[0]
            cursor.execute(*schema_to_update_sql("datasets", dataset_schema, "id = ? AND owner_id = ?", (dataset_id, owner_id), updated_at=current_time, **kwargs))
            conn.commit()

    # Deleting Function

    def delete_dataset(self, dataset_id: str, owner_id: str) -> bool:
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM datasets WHERE id = ? AND owner_id = ?", (dataset_id, owner_id))
            conn.commit()

            cursor.execute("DELETE FROM apikeys WHERE dataset_id = ? AND owner_id = ?", (dataset_id, owner_id))
            conn.commit()
            return True
            