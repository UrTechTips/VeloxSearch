from datetime import datetime, timedelta, timezone
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
        with self.db_manager as db:
            result = db.table("datasets").select("*").eq("id", dataset_id).execute().data
            result = zip(dataset_schema['fields'], result) if result else None
            print(f"Retrieved metadata for dataset_id {dataset_id}: {result}")  # Debugging line
            return {"metadata": dict(result)} if result else None

    def get_user_metadata(self, user_id: str) -> Optional[Dict]:
        """Get metadata for a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            Optional[Dict]: The metadata for the user, or None if not found.
        """
        with self.db_manager as db:
            result = db.table("users").select("*").eq("id", user_id).execute().data
            result = zip(user_schema['fields'], result) if result else None
            return {"metadata": dict(result)} if result else None

    def list_datasets(self, user_id: str) -> List[Dict]:
        """List all datasets for a specific user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            List[Dict]: A list of dictionaries describing the datasets owned by the user.
        """
        with self.db_manager as db:
            results = db.table("datasets").select("*").eq("owner_id", user_id).execute()
            print("Results from list_datasets:", results)  # Debugging line
            return results.data if results else []

    def list_apikeys(self, dataset_id: str, owner_id: str) -> List[Dict]:
        """List all API keys for a specific dataset and owner.

        Args:
            dataset_id (str): The ID of the dataset.
            owner_id (str): The ID of the owner.

        Returns:
            List[Dict]: A list of dictionaries describing the API keys for the dataset and owner.
        """
        with self.db_manager as db:
            results = db.table("api_keys").select("*").eq("dataset_id", dataset_id).eq("owner_id", owner_id).execute()
            print("Results from list_apikeys:", results)  # Debugging line
            return results.data if results else []

    def validate_apikey(self, api_hashed_key: str) -> bool:
        # TODO: Do i need to add user_id to check as security??
        """Validates an API key for a specific user.

        Args:
            api_hashed_key (str): The hashed API key to validate.

        Returns:
            bool: True if the API key is valid for the user, False otherwise.
        """
        with self.db_manager as db:
            result = db.table("api_keys").select("*").eq("hashed_key", api_hashed_key).execute()
            return bool(result)

    def is_apikey_deactivated(self, api_hashed_key: str) -> bool:
        """Checks if an API key is deactivated.

        Args:
            api_hashed_key (str): The hashed API key to check.
        
        Returns:
            bool: True if the API key is deactivated, False otherwise.
        """
        with self.db_manager as db:
            print(f"Checking if API key is deactivated for hash: {api_hashed_key}")  # TODO: Remove this debug
            result = db.table("api_keys").select("is_active").eq("hashed_key", api_hashed_key).execute()
            if not result or len(result.data) == 0:
                print(f"No API key found for hash: {api_hashed_key}")
                return True  # If the API key doesn't exist, treat it as deactivated
            is_active = result.data[0]["is_active"]
            return not is_active

    def validate_dataset_id(self, dataset_id: str, user_id: str) -> bool:
        """Validates a dataset ID for a specific user.

        Args:
            dataset_id (str): The ID of the dataset to validate.
            user_id (str): The ID of the user to check ownership against.
            
        Returns:
            bool: True if the dataset ID is valid and owned by the user, False otherwise.
        """
        with self.db_manager as db:
            result = db.table("datasets").select("*").eq("id", dataset_id).eq("owner_id", user_id).execute()

            if not result:
                print(f"Validation failed for dataset_id: {dataset_id} and user_id: {user_id}")
                dataset_exists = db.table("datasets").select("*").eq("id", dataset_id).execute()
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
        with self.db_manager as db:
            one_minute_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
            result = (
                db.table("usage")
                .select("id", "api_keys!inner(dataset_id)", count="exact")
                .eq("api_keys.dataset_id", dataset_id)
                .gte("created_at", one_minute_ago)
                .execute()
            )
            total_count = result.count            
            # Note: COUNT() returns 0 if no rows match. 
            return total_count if total_count > 0 else None

    def get_dataset_usagequota(self, dataset_id: str) -> Optional[int]:
        """Get the usage quota for a specific dataset. Number of requests in the last 24 hours.

        Args:
            dataset_id (str): The ID of the dataset to check usage for.

        Returns:
            Optional[int]: The usage quota for the dataset, or None if no usage found.
        """
        with self.db_manager as db:
            one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            result = (
                db.table("usage")
                .select("id", "api_keys!inner(dataset_id)", count="exact")
                .eq("api_keys.dataset_id", dataset_id)
                .gte("created_at", one_day_ago)
                .execute()
            )
            total_count = result.count
            return int(total_count) if total_count > 0 else None

    def get_apikey_usagerate(self, api_hashed_key: str) -> Optional[int]:
        """Get the usage rate for a specific API key. Number of requests in the last minute.

        Args:
            api_hashed_key (str): The hashed API key to check usage for.

        Returns:
            Optional[int]: The usage rate for the API key, or None if no usage found.
        """
        with self.db_manager as db:
            result = db.table("api_keys").select("id").eq("hashed_key", api_hashed_key).execute()

            if not result:
                return None
            apikey_id = result[0]

            result = db.table("usage").select("id").eq("apikey_id", apikey_id).gte("created_at", (datetime.now(timezone.utc) - timedelta(minutes=1))).execute()
            return int(result.count) if result.count > 0 else None

    def get_apikey_usagequota(self, api_hashed_key: str) -> Optional[int]:
        """Get the usage quota for a specific API key. Number of requests in the last 24 hours.

        Args:
            api_hashed_key (str): The hashed API key to check usage for.

        Returns:
            Optional[int]: The usage quota for the API key, or None if no usage found.
        """
        with self.db_manager as db:
            result = db.table("api_keys").select("id").eq("hashed_key", api_hashed_key).execute()

            if not result:
                return None
            apikey_id = result[0]

            result = db.table("usage").select("id").eq("apikey_id", apikey_id).gte("created_at", (datetime.now(timezone.utc) - timedelta(days=1))).execute()
            return int(result.count) if result.count > 0 else None

    def get_dataset_id_from_apikey(self, api_hashed_key: str) -> Optional[str]:
        """Get the dataset ID associated with a specific API key.

        Args:
            api_hashed_key (str): The hashed API key to check.

        Returns:
            Optional[str]: The dataset ID associated with the API key, or None if not found.
        """
        with self.db_manager as db:
            result = db.table("api_keys").select("dataset_id").eq("hashed_key", api_hashed_key).execute()
            if not result:
                return None
            return result.data[0]["dataset_id"]  # Return the dataset_id

    # ID's are omitted as they are generated using AUTO_INCREMENT.
    
    def insert_dataset(self, dataset_id: str, owner_id: str, name: str, description: str = None, length: int = None, plan: str = "basic", index_status: str = "None") -> bool:
        with self.db_manager as db:
            try:
                created_at = datetime.now(timezone.utc).isoformat()
                db.table("datasets").insert({
                    "id": dataset_id,
                    "owner_id": owner_id,
                    "name": name,
                    "description": description,
                    "length": length if length is not None else 0,
                    "plan": plan,
                    "index_status": index_status,
                }).execute()
                return True
            except Exception as e:
                print(f"Error inserting dataset: {e}")
                return False

    def insert_user(self, user_id: str, name: str, email: str) -> bool:
        with self.db_manager as db:
            try:
                created_at = datetime.now(timezone.utc)
                db.table("users").insert({
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "datasets_count": 0
                }).execute()
                return True
            except Exception as e:
                print(f"Error inserting user: {e}")
                return False

    def insert_apikey(self, apikey_id: str, owner_id: str, dataset_id: str, name: str, is_active: bool, hashed_key: str, encrypted_key: str, rate_limit: int, quota_limit: int) -> bool:
        with self.db_manager as db:
            try:
                created_at = datetime.now(timezone.utc)
                db.table("api_keys").insert({
                    "id": apikey_id,
                    "owner_id": owner_id,
                    "name": name,
                    "dataset_id": dataset_id,
                    "is_active": is_active,
                    "hashed_key": hashed_key,
                    "encrypted_key": encrypted_key,
                    "rate_limit": rate_limit,
                    "quota_limit": quota_limit,
                }).execute()
                return True
            except Exception as e:
                print(f"Error inserting apikey: {e}")
                return False

    def deactivate_apikey(self, apikey_id: str, owner_id: str) -> bool:
        with self.db_manager as db:
            try:
                print("Deactivating API key with hash:", apikey_id, "for owner_id:", owner_id)  # TODO: Remove this debug
                db.table("api_keys").update({"is_active": False}).eq("id", apikey_id).eq("owner_id", owner_id).execute()
                return True
            except Exception as e:
                print(f"Error deactivating API key: {e}")
                raise HTTPException(status_code=400, detail={"message": f"Error deactivating API key: {e}"})
            
    def insert_usage(self, apikey_hash: str, endpoint: str, latency: float, query_hash: str) -> bool:
        with self.db_manager as db:
            try:
                created_at = datetime.now(timezone.utc)
                apikey_id = db.table("api_keys").select("id").eq("hashed_key", apikey_hash).execute()
                if not apikey_id:
                    print(f"Error inserting usage: No apikey found for hash {apikey_hash}")
                    return False
                apikey_id = apikey_id.data[0]["id"]
                db.table("usage").insert({
                    "apikey_id": apikey_id,
                    "endpoint": endpoint,
                    "latency": latency,
                    "query_hash": query_hash,
                }).execute()
                return True
            except Exception as e:
                print(f"Error inserting usage: {e}")
                return False

    def insert_feedback(self, dataset_id: str, **kwargs) -> bool:
        with self.db_manager as db:
            try:
                db.table("feedback").insert({
                    "dataset_id": dataset_id,
                    **kwargs
                }).execute()
                return True
            except Exception as e:
                print(f"Error inserting feedback: {e}")
                return False

    # Update Functions
    def update_dataset(self, dataset_id: str, owner_id: str, **kwargs) -> bool:
        with self.db_manager as db:
            try:
                updated_at = datetime.now(timezone.utc).isoformat()
                update_data = {**kwargs, "updated_at": updated_at}
                print(f"Updating dataset {dataset_id} for owner {owner_id} with data: {update_data}")  # Debugging line
                db.table("datasets").update(update_data).eq("id", dataset_id).eq("owner_id", owner_id).execute()
                return True
            except Exception as e:
                print(f"Error updating dataset: {e}")
                return False

    # Deleting Function

    def delete_dataset(self, dataset_id: str, owner_id: str) -> bool:
        """Delete from datasets and api_keys tables. This is a cascading delete, so all API keys associated with the dataset will also be deleted."""
        with self.db_manager as db:
            try:
                db.table("datasets").delete().eq("id", dataset_id).eq("owner_id", owner_id).execute()
                db.table("api_keys").delete().eq("dataset_id", dataset_id).execute()
                return True
            except Exception as e:
                print(f"Error deleting dataset: {e}")
                return False            