import os
import uuid
import random

from dotenv import load_dotenv
from app.db.database import DatabaseService
from app.db.manager import DatabaseManager
from app.core.database_config import DATABASE_NAME
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT
from cryptography.fernet import Fernet

from app.utils.hash_utils import apihash

load_dotenv()
encryption_key = os.getenv("API_KEY_ENCRYPTION_KEY").encode('utf-8')
fernet = Fernet(encryption_key)

def generate_key(owner_id: str, dataset_id: str, name: str) -> str:
    """Generates an API key for a given owner and secret.

    Args:
        owner_id (str): The ID of the owner for whom the API key is being generated.
        dataset_id (str): The ID of the dataset to which the API key belongs.
        name (str): The name of the API key.

    Returns:
        str: The generated API key.
    """
    api_key = uuid.uuid4().hex
    # Get random 10 character string for API key ID
    random_hex = uuid.uuid4().hex
    start_id = random.randint(0, len(random_hex) - 10)
    apikey_id = random_hex[start_id:start_id + 10]
    hash = apihash(api_key)

    encrypted_key = fernet.encrypt(api_key.encode('utf-8')).decode()

    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    db.insert_apikey(apikey_id, owner_id, dataset_id, name, True, hash, encrypted_key, RATE_LIMIT, QUOTA_LIMIT)
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

def list_keys(dataset_id: str, owner_id: str):
    """Lists all API keys for a given dataset and owner.

    Args:
        dataset_id (str): The ID of the dataset for which to list API keys.
        owner_id (str): The ID of the owner for whom to list API keys.
    
    Returns:
        list: A list of API keys associated with the given dataset and owner.
    """
    db = DatabaseService(DatabaseManager(DATABASE_NAME))
    keys = db.list_apikeys(dataset_id, owner_id)
    print(f"Retrieved keys from database: {keys}")
    decrypted_keys = []
    for key in keys:
        decrypted_key = fernet.decrypt(key['encrypted_key'].encode('utf-8')).decode()
        decrypted_keys.append({
            "name": key['name'],
            "id": key['id'],
            "dataset_id": key['dataset_id'],
            "is_active": key['is_active'],
            "created_at": key['created_at'],
            "api_key": decrypted_key
        })
    print(f"Decrypted keys: {decrypted_keys}")
    return decrypted_keys