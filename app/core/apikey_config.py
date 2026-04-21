import dotenv
import os

dotenv.load_dotenv()

RATE_LIMIT = 1000 # TODO: Create a Rate limit dictionary for different user tiers
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "")