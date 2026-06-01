import uuid
import random
from app.db.database import DatabaseService
from app.db.manager import DatabaseManager
from app.core.database_config import DATABASE_NAME
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT

from app.utils.hash_utils import apihash

def generate_key(owner_id: str, dataset_id: str) -> str:
    """Generates an API key for a given owner and secret.

    Args:
        owner_id (str): The ID of the owner for whom the API key is being generated.
        dataset_id (str): The ID of the dataset to which the API key belongs.

    Returns:
        str: The generated API key.
    """
    api_key = uuid.uuid4().hex
    # Get random 10 character string for API key ID
    random_hex = uuid.uuid4().hex
    start_id = random.randint(0, len(random_hex) - 10)
    apikey_id = random_hex[start_id:start_id + 10]
    hash = apihash(api_key)

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    db.insert_apikey(apikey_id, owner_id, dataset_id, True, hash, RATE_LIMIT, QUOTA_LIMIT)
    return api_key

def validate_key(api_key: str) -> bool:
    """Validates an API key against the stored hash in the database.

    Args:
        api_key (str): The API key to validate.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    hash = apihash(api_key)

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.validate_apikey(hash)

def deactivate_key(api_key: str, owner_id: str) -> bool:
    """Deactivates an API key in the database.

    Args:
        api_key (str): The API key to deactivate.
        owner_id (str): The ID of the owner of the API key.

    Returns:
        bool: True if the API key was successfully deactivated, False otherwise.
    """
    hash = apihash(api_key)

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.deactivate_apikey(hash, owner_id)

def get_dataset_id_from_apikey(api_key: str) -> str:
    """Retrieves the dataset ID associated with a given API key. The function handles the hashing of API key.

    Args:
        api_key (str): The API key for which to retrieve the dataset ID.

    Returns:
        str: The dataset ID associated with the API key, or None if not found.
    """
    hash = apihash(api_key)

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.get_dataset_id_from_apikey(hash)

def get_dataset_id_from_apikey_hash(api_key_hash: str) -> str:
    """Retrieves the dataset ID associated with a given API key hash.

    Args:
        api_key_hash (str): The hash of the API key for which to retrieve the dataset ID.

    Returns:
        str: The dataset ID associated with the API key hash, or None if not found.
    """
    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    return db.get_dataset_id_from_apikey_hash(api_key_hash)