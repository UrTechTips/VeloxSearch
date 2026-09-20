import os

from dotenv import load_dotenv

load_dotenv()

REDIS_HOST: str = 'localhost'
REDIS_PORT: int = 6379
REDIS_DB: int = 0   
REDIS_URL: str = os.getenv("REDIS_URL")