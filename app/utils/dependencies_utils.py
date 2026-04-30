import jwt
from fastapi import Header, HTTPException, Request
from app.core import JWT_SECRET, JWT_ALGORITHM
from app.utils.api_utils import validate_key, get_dataset_id_from_apikey
from app.utils.rate_limiter import is_rate_limited, is_quota_exceeded

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
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    
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
    print(request.app.state)
    redis_client = request.app.state.redis_client
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid API key")
    
    apikey = authorization.split(" ")[1]
    if is_rate_limited(redis_client, apikey):
        raise HTTPException(429, "Rate limit exceeded")
    if is_quota_exceeded(redis_client, apikey):
        raise HTTPException(403, "Quota exceeded")
    if not validate_key(apikey):
        raise HTTPException(401, "Invalid API key")
    if not apikey:
        raise HTTPException(401, "API key missing")
    return apikey