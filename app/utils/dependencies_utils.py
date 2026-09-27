import os
from jwt import PyJWKClient, decode as jwt_decode, PyJWTError
import time
from dotenv import load_dotenv
from fastapi import Header, HTTPException, Request
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT
from app.core import JWT_SECRET, JWT_ALGORITHM
from app.utils.api_utils import validate_key, get_dataset_id_from_apikey, get_dataset_id_from_apikey_hash
from app.utils.rate_limiter import is_rate_limited, is_quota_exceeded
from app.utils.hash_utils import apihash
from supabase import create_client, Client
from app.db import service as database_service

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
jwk_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")  

def get_current_user(authorization: str = Header(...)):
    """Verifies the JWT token from the Authorization header and returns the user ID.

    Args:
        authorization (str, optional): _description_. Defaults to Header(...).

    Raises:
        HTTPException: 401 if the token is invalid or expired
        HTTPException: 401 if the token is invalid
        HTTPException: 401 if the token is expired

    Returns:
        str: The user ID extracted from the JWT token.
    """
    if not authorization.startswith("Bearer "):
        print(f"Invalid token format: {authorization}", flush=True)
        raise HTTPException(401, "Invalid token")

    token = authorization.split(" ")[1]
    # print(f"Verifying token: {token}", flush=True) #TODO: Remove debug print
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decoded_token = jwt_decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
        return decoded_token["sub"]
    except PyJWTError as e:
        print(f"JWT verify failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
def get_apikey(authorization: str = Header(...), request: Request = None):
    """Extracts the API key from the Authorization header.

    Args:
        authorization (str, optional): _description_. Defaults to Header(...).
        request (Request, optional): _description_. Defaults to None.

    Raises:
        HTTPException: 401 if the API key is missing or invalid
        HTTPException: 401 if the API key is invalid
        HTTPException: 429 if the rate limit is exceeded
        HTTPException: 403 if the quota is exceeded
    
    Returns:
        str: The API key extracted from the Authorization header.
    """
    redis_client = request.app.state.redis_client
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid API key")
    
    apikey = authorization.split(" ")[1]
    if database_service.is_apikey_deactivated(apihash(apikey)):
        raise HTTPException(401, "API key is deactivated")
    is_rate_limit, remaining_requests = is_rate_limited(redis_client, apikey)
    if is_rate_limit:
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": 60, "X-RateLimit-Limit": RATE_LIMIT, "X-RateLimit-Remaining": remaining_requests})
    is_quota_exceed, remaining_quota = is_quota_exceeded(redis_client, apikey)
    if is_quota_exceed:
        raise HTTPException(429, "Quota exceeded", headers={"Retry-After": 86400, "X-Quota-Limit": QUOTA_LIMIT, "X-Quota-Remaining": remaining_quota})
    if not validate_key(apikey):
        raise HTTPException(401, "Invalid API key")
    if not apikey:
        raise HTTPException(401, "API key missing")
    return apikey, get_dataset_id_from_apikey(apikey)

def validate_jwt(authorization: str = Header(...)):
    """Validates the JWT token from the Authorization header.

    Args:
        authorization (str, optional): _description_. Defaults to Header(...).
    
    Raises:
        HTTPException: 401 if the token is invalid or expired
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        decoded_token = jwt_decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Token")