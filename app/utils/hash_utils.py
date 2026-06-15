from hashlib import sha256
from app.core.apikey_config import API_KEY_SECRET
from fastapi import Request
from xxhash import xxh64

def apihash(api_key: str) -> str:
    """Generates a hash for the given API key.

    Args:
        api_key (str): The API key to hash.
    
    Returns:
        str: The SHA-256 hash of the API key combined with the secret.
    """
    return sha256((api_key + API_KEY_SECRET).encode()).hexdigest()

def queryHash(request: Request = None):
    """Generates a hash for the query in the request body.

    Args:
        request (Request): The incoming HTTP request containing the query.
    
    Returns:
        str: The SHA-256 hash of the query.
    """
    requires_hash = request.headers.get("X-Require-Hash", "false").lower() == "true"
    # if requires_hash:
    query = request.query_params.get("query", "")
    query_hash = xxh64(query.encode()).hexdigest()
    return query_hash
    # return None