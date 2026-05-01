import dotenv
import os

dotenv.load_dotenv()

RATE_LIMIT = 20 # TODO: Create a Rate limit dictionary for different user tiers
QUOTA_LIMIT = 100 # TODO: Create a Quota limit dictionary for different user tiers
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "")