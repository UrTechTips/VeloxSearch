import jwt
import time
from fastapi import Header, HTTPException, Request
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT
from app.core import JWT_SECRET, JWT_ALGORITHM
from app.utils.api_utils import validate_key, get_dataset_id_from_apikey, get_dataset_id_from_apikey_hash
from app.utils.rate_limiter import is_rate_limited, is_quota_exceeded
from firebase_admin import auth

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
        raise HTTPException(401, "Invalid token")
    
    token = authorization.split(" ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception:
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
        auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Token")