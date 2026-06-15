import redis
from app.core.redis_config import REDIS_HOST, REDIS_PORT
from app.core.apikey_config import RATE_LIMIT, QUOTA_LIMIT

# def is_rate_limited(redis_client: redis.Redis, apikey: str, rate_limit: int = RATE_LIMIT) -> bool:
#     """Checks if the given API key has exceeded the rate limit.

#     Args:
#         redis_client (redis.Redis): The Redis client.
#         api_key (str): The API key to check.
#         rate_limit (int): The maximum number of requests allowed per minute.
    
#     Returns:
#         bool: True if the API key is rate limited, False otherwise.
#     """
#     key = f"rate_limit:{apikey}"
#     count = redis_client.get(key)
#     if count is None:
#         redis_client.set(key, 1, ex=60)
#         return False
#     elif int(count) < rate_limit:
#         redis_client.incr(key)
#         return False
#     else:
#         return True

import time

def is_rate_limited(redis_client: redis.Redis, apikey: str, rate_limit: int = RATE_LIMIT, window: int = 60):
    key = f"rate_limit:{apikey}"
    now = time.time()
    
    pipe = redis_client.pipeline()
    
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}": now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)
    
    results = pipe.execute()
    current_count = results[2]

    remaining_requests = rate_limit - current_count
    
    if current_count > rate_limit:
        return True, remaining_requests
    return False, remaining_requests

def is_quota_exceeded(redis_client: redis.Redis, api_key: str, quota_limit: int = QUOTA_LIMIT, window: int = 86400) -> bool:
    """Checks if the given API key has exceeded the quota limit.

    Args:
        redis_client (redis.Redis): The Redis client.   
        api_key (str): The API key to check.
        quota_limit (int): The maximum number of requests allowed per day.
        window (int): The time window in seconds for the quota limit.

    Returns:
        bool: True if the API key has exceeded the quota, False otherwise. 
    """
    key = f"quota_limit:{api_key}"
    now = time.time()

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}": now})
    pipe.zcard(key)
    pipe.expire(key, window + 1)

    results = pipe.execute()
    current_count = results[2]

    # Remaining quota can be calculated as quota_limit - current_count if needed
    remaining_quota = quota_limit - current_count

    if current_count > quota_limit:
        return True, remaining_quota
    return False, remaining_quota