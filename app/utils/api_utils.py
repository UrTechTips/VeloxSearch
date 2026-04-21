import uuid
from hashlib import sha1
from app.db.database import DatabaseService
from app.db.manager import DatabaseManager
from app.core.database_config import DATABASE_NAME
from app.core.apikey_config import API_KEY_SECRET, RATE_LIMIT

def generate_key(owner_id: str, dataset_id: str) -> str:
    """Generates an API key for a given owner and secret.

    Args:
        owner_id (str): The ID of the owner for whom the API key is being generated.
        dataset_id (str): The ID of the dataset to which the API key belongs.

    Returns:
        str: The generated API key.
    """
    apikey_id = uuid.uuid4().hex
    api_key = uuid.uuid4().hex
    hash = sha1((api_key + API_KEY_SECRET).encode()).hexdigest()

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    db.insert_apikey(apikey_id, owner_id, dataset_id, True, hash, RATE_LIMIT)
    print("Generated API key:", api_key)  # Debugging statement
    return api_key

def validate_key(api_key: str) -> bool:
    """Validates an API key against the stored hash in the database.

    Args:
        api_key (str): The API key to validate.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    hash = sha1((api_key + API_KEY_SECRET).encode()).hexdigest()

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.validate_apikey(hash)

def deactivate_key(api_key: str) -> bool:
    """Deactivates an API key in the database.

    Args:
        api_key (str): The API key to deactivate.

    Returns:
        bool: True if the API key was successfully deactivated, False otherwise.
    """
    hash = sha1((api_key + API_KEY_SECRET).encode()).hexdigest()

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.deactivate_apikey(hash)

def get_dataset_id_from_apikey(api_key: str) -> str:
    """Retrieves the dataset ID associated with a given API key. The function handles the hashing of API key.

    Args:
        api_key (str): The API key for which to retrieve the dataset ID.

    Returns:
        str: The dataset ID associated with the API key, or None if not found.
    """
    hash = sha1((api_key + API_KEY_SECRET).encode()).hexdigest()

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.get_dataset_id_from_apikey(hash)